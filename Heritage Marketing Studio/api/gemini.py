"""gemini.py — Google AI Studio provider: images, video and music.

Why this exists alongside creative.py/fal: the picture and music models we actually rely on are
Google's own (Imagen, Nano Banana, Veo, Lyria), so buying them direct is cheaper than through a
reseller — Veo 3.1 Lite is roughly half the price of the equivalent fal call, at the same speed.

Two API shapes are involved, which is why this module is not a one-liner:

  * images and music -> the Interactions API (`/v1beta/interactions`), a single POST that returns
    the asset as base64 INLINE DATA.
  * video           -> `:predictLongRunning`, which returns an operation to poll, then a URI to
    download with the key attached.

The important consequence: fal hands back hosted URLs, Google hands back bytes. Everything
downstream in this app passes URLs around, so each function here writes the bytes into the local
media store and returns a served path (`/media/...`). `local_path()` maps that back to disk for
ffmpeg.
"""
from __future__ import annotations

import base64
import ipaddress
import mimetypes
import os
import socket
import sys
import time
import uuid
from urllib.parse import urlparse

import library
import tenancy

BASE = "https://generativelanguage.googleapis.com/v1beta"
INTERACTIONS = f"{BASE}/interactions"


def _is_public_http_url(url: str) -> bool:
    """SECURITY — the audit's other finding on this same reference-fetch path: `_as_base64`'s
    `httpx.get(s, ...)` had no host/IP check at all, so a `reference_url` a caller supplies (from a
    real user-facing payload field) could point at `http://169.254.169.254/...` (the cloud metadata
    endpoint most SSRF exploits actually want) or any address on the server's own private network, and
    this would fetch it and hand the response back as if it were a picture. Resolves the hostname and
    refuses anything that isn't a genuine public address — loopback, link-local, private (RFC1918),
    and other reserved ranges are all blocked. Not bulletproof (a DNS answer can still change between
    this check and the real request — DNS rebinding), but a real, standard mitigation for the actual
    risk here, not just for the finding to exist and never be fixed.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        infos = socket.getaddrinfo(parsed.hostname, None)
    except (ValueError, OSError):
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True

# Images. Flash is the balanced default; lite is cheapest; pro for the hardest compositions.
IMAGE_MODEL = "gemini-3.1-flash-image"
IMAGE_MODEL_LITE = "gemini-3.1-flash-lite-image"
IMAGE_MODEL_PRO = "gemini-3-pro-image"

# The resolutions the Interactions API accepts for `image_size`. Clamped the same way the aspect ratio
# is, and for the same reason: an unrecognised value here is an HTTP 400 with the render lost, whereas a
# clamp is a known approximation. Every route was pinned at 1K because nothing passed the argument
# through — pro tier and anything above 1K were defined and unreachable.
IMAGE_SIZES = ("1K", "2K", "4K")

# Video. Lite is the draft tier — image-to-video capable, so the storyboard frames still drive it.
# TWO tiers, not three: the Gemini API documents only `veo-3.1-generate-preview` and the lite
# variant. A "fast" entry was here, and `veo-3.1-fast-generate-preview` is not a model Google
# publishes on this endpoint — every request for the middle tier 404'd and fell through to fal,
# which is why a film quoted at Veo's price arrived on fal's bill. Veo 3.1 Fast exists on Vertex AI;
# if it is ever exposed here, add it back with the id Google actually documents, not a guessed one.
VIDEO_MODELS = {
    "lite": "veo-3.1-lite-generate-preview",       # $0.05/s at 720p
    "standard": "veo-3.1-generate-preview",        # $0.40/s at 720p
}
VIDEO_BEATS = (4, 6, 8)   # Veo accepts only these clip lengths

# A model whose quota is spent stays spent — Veo's preview tiers have a daily allowance, not just a
# per-minute one. Remember that per model so six shots don't each sit through the full backoff
# ladder: one film burned eight minutes of waiting and still returned nothing.
_QUOTA_SPENT: dict[str, float] = {}
QUOTA_COOLDOWN = 900.0    # stop asking this model for 15 minutes


def quota_spent(tier: str = "") -> str:
    """A human reason if this tier is known to be out of quota right now, else ''."""
    model = VIDEO_MODELS.get(tier) or tier
    until = _QUOTA_SPENT.get(model, 0.0)
    if until <= time.time():
        return ""
    mins = max(1, int((until - time.time()) / 60))
    other = "Final (Veo 3.1 Standard)" if model != VIDEO_MODELS["standard"] else "fal"
    return (f"{model} is out of quota on this Google project. Not retrying it for another {mins} min. "
            f"Switch the video engine to fal (Veo 3.1 Fast), or the tier to {other}, or raise the "
            f"Veo limit at https://ai.dev/rate-limit")

# Music. The clip model always returns 30s, which comfortably covers a 10-30s film; pro is for
# longer cuts and takes its length from the prompt.
MUSIC_CLIP = "lyria-3-clip-preview"
MUSIC_PRO = "lyria-3-pro-preview"

# Tenant-scoped since the shared-directory leak was found: new files land under
# `api/tenants/<tenant>/media/`. Files written before that still live in the bare `api/media/`
# and are still SERVED from there, because their URLs are recorded inside stored documents —
# see `tenancy.asset_path`, which reads tenant-first then legacy. Bound at import, so this is
# one tenant per process; serving several from one process needs this to become a call.
MEDIA_DIR = tenancy.asset_dir("media")


def api_key() -> str:
    """Either name works — the Google SDKs accept both, so users set whichever they were given."""
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        v = (os.environ.get(name) or "").strip()
        if v:
            return v
    return ""


def available() -> bool:
    return bool(api_key())


def _headers() -> dict:
    return {"x-goog-api-key": api_key(), "Content-Type": "application/json"}


def _store(data: bytes, ext: str, prefix: str = "gem") -> str:
    """Write bytes into the served media folder and return the public path."""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    name = f"{prefix}-{uuid.uuid4().hex[:10]}{ext}"
    with open(os.path.join(MEDIA_DIR, name), "wb") as fh:
        fh.write(data)
    return f"/media/{name}"


def local_path(url_or_path: str) -> str | None:
    """Resolve a served '/media/...' or '/library-file/...' path (or a plain path) to a file on disk,
    else None.

    Real bug, found live: this only ever recognised `/media/...` (this module's own generated output).
    A signed-off LIBRARY reference — a real uploaded pack shot, cast photo, anything `library.get()`
    hands back a `/library-file/<kind>/<name>` URL for — matched none of this function's branches, so
    `_as_base64()` silently returned None for it (not an exception; nothing prints), which
    `image_from_reference()` reads as "no usable reference" and returns None with no error at all —
    the caller then falls through to fal, which fails loudly for an unrelated reason (fal needs a real
    http(s)/data: URL, which a relative path never is), and *that* error is the only one anyone sees.
    The actual fix belongs here: every real library asset has to resolve to real bytes for the
    identity/pack fidelity this whole reference mechanism exists for, not just generated media.
    """
    s = str(url_or_path or "")
    if s.startswith("/media/"):
        p = os.path.join(MEDIA_DIR, os.path.basename(s))
        return p if os.path.exists(p) else None
    if "/library-file/" in s:
        p = library.local_path(s.split("/library-file/", 1)[1])
        return p if p and os.path.exists(p) else None
    # SECURITY — real bug found in the backend audit: this used to accept ANY path that exists on
    # disk, unrestricted — `../../.env`, an absolute path to any file the server process can read,
    # anything. Reachable end to end: a caller can pass a plain path through `reference_url` (e.g.
    # `/cast-reference`, `/scene-still`) or through `_resolve_media`'s own fallback in main.py, and
    # whatever this returned got read as bytes and shipped to Google's API as an "image" reference —
    # an arbitrary-file-read-and-exfiltrate path. `library.local_path()` already refuses anything
    # outside its own root the same way; this fallback gets the same containment, scoped to the one
    # directory this module actually manages. Every legitimate caller already matches one of the two
    # branches above before reaching here, so this only ever denies paths nothing legitimate needed.
    root = os.path.normpath(MEDIA_DIR)
    full = os.path.normpath(os.path.join(MEDIA_DIR, s)) if not os.path.isabs(s) else os.path.normpath(s)
    if full.startswith(root + os.sep) and os.path.exists(full):
        return full
    return None


def for_api(mime: str, data: bytes) -> tuple[str, bytes]:
    """Turn an image the image API is not known to accept into one it does. Today that is AVIF only: the
    documented reference formats are PNG, JPEG, WebP and HEIC/HEIF, and a pack photo saved from a web page is
    often AVIF ("Heritage milk.avif"). A wrong guess here would mean the pack silently never attaches, so
    AVIF becomes PNG (transparency kept). Every other format is passed through exactly as before — this is
    deliberately not a general converter. If conversion fails the original goes through unchanged (no worse
    than before) and the reason is logged."""
    if str(mime).lower() != "image/avif":
        return mime, data
    try:
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img.load()
        buf = io.BytesIO()
        img.convert("RGBA" if "A" in img.getbands() else "RGB").save(buf, "PNG")
        return "image/png", buf.getvalue()
    except Exception as e:  # noqa: BLE001 -- any decode failure: fall back to the original bytes
        print(f"[gemini] could not convert an AVIF reference to PNG ({type(e).__name__}: {e}); sending as-is",
              file=sys.stderr, flush=True)
        return mime, data


def _as_base64(src: str) -> tuple[str, str] | None:
    """`_as_base64_raw`, with an AVIF reference converted to PNG first (see `for_api`)."""
    pair = _as_base64_raw(src)
    if not pair:
        return pair
    mime, b64 = pair
    if str(mime).lower() != "image/avif":
        return pair
    mime2, data2 = for_api(mime, base64.b64decode(b64))
    return mime2, base64.b64encode(data2).decode()


def _as_base64_raw(src: str) -> tuple[str, str] | None:
    """Any reference image — local media path, disk path, http URL or data URI — to (mime, base64)."""
    if not src:
        return None
    s = str(src)
    if s.startswith("data:"):
        head, _, b64 = s.partition(",")
        mime = head[5:].split(";")[0] or "image/png"
        return mime, b64
    p = local_path(s)
    if p:
        mime = mimetypes.guess_type(p)[0] or "image/png"
        with open(p, "rb") as fh:
            return mime, base64.b64encode(fh.read()).decode()
    if s.startswith(("http://", "https://")):
        # SECURITY — blind SSRF, found in the backend audit: this fetched whatever URL a caller
        # supplied with no host check at all, which is exactly the shape of a request that can reach
        # a cloud metadata endpoint or anything else on the server's own network. `follow_redirects`
        # is also off now on purpose — a URL that passes the check could still redirect to a private
        # address, and re-validating every hop is more machinery than a reference-image fetch needs;
        # refusing the redirect entirely closes that path instead.
        if not _is_public_http_url(s):
            print(f"[gemini] refused reference URL (not a public address): {s[:60]}",
                  file=sys.stderr, flush=True)
            return None
        import httpx
        try:
            r = httpx.get(s, timeout=120.0, follow_redirects=False)
            r.raise_for_status()
            mime = r.headers.get("content-type", "image/png").split(";")[0]
            return mime, base64.b64encode(r.content).decode()
        except Exception as e:
            print(f"[gemini] couldn't fetch reference {s[:60]}: {e}", file=sys.stderr, flush=True)
    return None


def _interaction(model: str, blocks: list, response_format: dict, timeout: float = 300.0):
    """One Interactions call. Returns the first inline asset as (mime, bytes), or None."""
    import httpx
    body = {"model": model, "input": blocks, "response_format": response_format}
    try:
        r = httpx.post(INTERACTIONS, headers=_headers(), json=body, timeout=timeout)
        if r.status_code >= 400:
            print(f"[gemini] {model} HTTP {r.status_code}: {r.text[:300]}",
                  file=sys.stderr, flush=True)
            return None
        data = r.json()
    except Exception as e:
        print(f"[gemini] {model} failed: {e}", file=sys.stderr, flush=True)
        return None
    return _dig_inline(data)


def _dig_inline(data) -> tuple[str, bytes] | None:
    """Pull base64 media out of an interaction response, whichever shape it arrives in."""
    if not isinstance(data, dict):
        return None
    inter = data.get("interaction") if isinstance(data.get("interaction"), dict) else data
    for key in ("output_image", "output_audio", "output_video"):
        blk = inter.get(key)
        if isinstance(blk, dict) and blk.get("data"):
            return blk.get("mime_type") or "application/octet-stream", base64.b64decode(blk["data"])
    for step in (inter.get("steps") or []):
        for block in (step.get("content") or []) if isinstance(step, dict) else []:
            if isinstance(block, dict) and block.get("data") and \
                    str(block.get("type")) in ("image", "audio", "video"):
                return (block.get("mime_type") or "application/octet-stream",
                        base64.b64decode(block["data"]))
    keys = list(inter.keys()) if isinstance(inter, dict) else type(inter).__name__
    print(f"[gemini] no inline media in response; keys={keys}", file=sys.stderr, flush=True)
    return None


def _ext_for(mime: str, fallback: str) -> str:
    return {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
            "audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav",
            "video/mp4": ".mp4"}.get((mime or "").lower(), fallback)


# --- images ---------------------------------------------------------------------------------
def image(prompt: str, ratio: str = "1:1", *, model: str | None = None,
          size: str = "1K") -> str | None:
    """Text-to-image. Returns a served '/media/...' path."""
    if not available():
        return None
    got = _interaction(model or IMAGE_MODEL, [{"type": "text", "text": prompt}],
                       {"type": "image", "mime_type": "image/jpeg",
                        "aspect_ratio": ratio if ratio in ("1:1", "16:9", "9:16", "4:3", "3:4") else "1:1",
                        "image_size": size if size in IMAGE_SIZES else "1K"})
    if not got:
        return None
    mime, data = got
    return _store(data, _ext_for(mime, ".jpg"), "still")


def image_from_reference(prompt: str, references: list, ratio: str = "16:9",
                         *, model: str | None = None, size: str = "1K") -> str | None:
    """A new shot that keeps the people from the reference image(s) identical.

    This is the character-lock path: identity travels as a picture, never as words.
    """
    if not available():
        return None
    blocks: list = [{"type": "text", "text": prompt}]
    for ref in (references or [])[:3]:
        pair = _as_base64(ref)
        if pair:
            blocks.append({"type": "image", "mime_type": pair[0], "data": pair[1]})
    if len(blocks) == 1:
        return None                     # no usable reference — caller should fall back
    got = _interaction(model or IMAGE_MODEL, blocks,
                       {"type": "image", "mime_type": "image/jpeg",
                        "aspect_ratio": ratio if ratio in ("1:1", "16:9", "9:16", "4:3", "3:4") else "16:9",
                        "image_size": size if size in IMAGE_SIZES else "1K"})
    if not got:
        return None
    mime, data = got
    return _store(data, _ext_for(mime, ".jpg"), "frame")


# --- music ----------------------------------------------------------------------------------
def music(prompt: str, seconds: int = 30) -> str | None:
    """One instrumental bed. The clip model returns a fixed 30s, which is then trimmed to the
    picture in the mix; longer films use the pro model and take their length from the prompt."""
    if not available():
        return None
    long_form = int(seconds or 30) > 30
    text = prompt if not long_form else f"{prompt} Compose roughly {int(seconds)} seconds."
    got = _interaction(MUSIC_PRO if long_form else MUSIC_CLIP,
                       [{"type": "text", "text": text}], {"type": "audio"}, timeout=420.0)
    if not got:
        return None
    mime, data = got
    return _store(data, _ext_for(mime, ".mp3"), "bed")


# --- video ----------------------------------------------------------------------------------
def video(prompt: str, *, image_ref: str = "", seconds: int = 8, ratio: str = "16:9",
          tier: str = "lite", poll_seconds: float = 10.0, timeout: float = 900.0) -> str | None:
    """Generate one shot. Animates `image_ref` when given, which is what keeps the cast identical.

    Veo is a long-running operation: submit, poll until done, then download the returned URI.
    """
    if not available():
        return None
    import httpx
    # An unknown tier resolves to the cheapest one on purpose: guessing upwards would bill 8x for a
    # typo, and the caller is told which model actually ran.
    model = VIDEO_MODELS.get(tier) or VIDEO_MODELS["lite"]
    inst: dict = {"prompt": prompt}
    ref = _as_base64(image_ref) if image_ref else None
    if ref:
        # `bytesBase64Encoded`, not `inlineData`. Google's own Gemini API example shows inlineData,
        # but that is the STANDARD model: Lite rejects it outright with "`inlineData` isn't supported
        # by this model", which silently cost us the character lock on every draft. Verified live
        # against veo-3.1-lite-generate-preview. If a model ever wants the documented shape instead,
        # _IMAGE_SHAPES retries with it rather than dropping to text-to-video and reinventing the cast.
        inst["image"] = {"bytesBase64Encoded": ref[1], "mimeType": ref[0]}
    elif image_ref:
        print("[gemini] reference frame unusable, falling back to text-to-video",
              file=sys.stderr, flush=True)
    # `durationSeconds` was missing, so every Google shot came back at Veo's default length however
    # long the beat was — the film would neither add up to the chosen duration nor stay in sync with
    # the soundtrack, which is placed on the planned timecodes. Snap to a beat Veo accepts.
    beat = min(VIDEO_BEATS, key=lambda b: (abs(b - int(seconds or 8)), b))
    params = {"aspectRatio": ratio if ratio in ("16:9", "9:16") else "16:9",
              "resolution": "720p", "durationSeconds": beat}
    # Two different retries, kept apart on purpose. Conflating them cost us two shots of a film:
    #   * a QUOTA error (429) is transient — Veo's per-minute allowance. Wait and ask again.
    #   * an "isn't supported" error is about the request shape — asking again is pointless, but the
    #     other image encoding is worth one try.
    # Previously any failure consumed the shape retry, so a 429 was followed by an inlineData attempt
    # that returned a misleading 400 and the shot was abandoned after ~2 seconds.
    if quota_spent(tier):
        print(f"[gemini] skipping {model}: {quota_spent(tier)}", file=sys.stderr, flush=True)
        return None
    alt = {**inst, "image": {"inlineData": {"mimeType": ref[0], "data": ref[1]}}} if ref else None
    # One short wait for a genuine burst, then stop. Riding out three long waits only helps when the
    # limit is per-minute; when the daily allowance is gone every wait is dead time.
    body, op, waits, quota_hits = inst, None, [20.0, 45.0], 0
    while True:
        try:
            r = httpx.post(f"{BASE}/models/{model}:predictLongRunning", headers=_headers(),
                           json={"instances": [body], "parameters": params}, timeout=180.0)
        except Exception as e:
            print(f"[gemini] {model} submit failed: {e}", file=sys.stderr, flush=True)
            return None
        if r.status_code < 400:
            op = (r.json() or {}).get("name")
            break
        text = r.text or ""
        print(f"[gemini] {model} HTTP {r.status_code}: {text[:300]}", file=sys.stderr, flush=True)
        if r.status_code == 429:
            quota_hits += 1
            # Twice in a row means the allowance is gone, not that we were briefly too quick.
            if quota_hits >= 2 or not waits:
                _QUOTA_SPENT[model] = time.time() + QUOTA_COOLDOWN
                print(f"[gemini] {model} is out of quota — giving up on it for "
                      f"{QUOTA_COOLDOWN / 60:.0f} min rather than waiting per shot",
                      file=sys.stderr, flush=True)
                return None
            pause = waits.pop(0)
            print(f"[gemini] rate limited — waiting {pause:.0f}s then retrying this shot once",
                  file=sys.stderr, flush=True)
            time.sleep(pause)
            continue
        if r.status_code in (500, 503) and waits:
            pause = waits.pop(0)
            print(f"[gemini] {r.status_code} — waiting {pause:.0f}s then retrying this shot",
                  file=sys.stderr, flush=True)
            time.sleep(pause)
            continue
        if alt is not None and "supported" in text:
            print("[gemini] retrying the reference frame in the other encoding",
                  file=sys.stderr, flush=True)
            body, alt = alt, None
            continue
        return None
    if not op:
        print(f"[gemini] {model} returned no operation name", file=sys.stderr, flush=True)
        return None

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(poll_seconds)
        try:
            s = httpx.get(f"{BASE}/{op}", headers=_headers(), timeout=90.0)
            done = s.json() if s.status_code < 400 else {}
        except Exception as e:
            print(f"[gemini] poll failed: {e}", file=sys.stderr, flush=True)
            continue
        if not done.get("done"):
            continue
        if done.get("error"):
            print(f"[gemini] {model} error: {str(done['error'])[:250]}", file=sys.stderr, flush=True)
            return None
        uri = ""
        try:
            samples = done["response"]["generateVideoResponse"]["generatedSamples"]
            uri = samples[0]["video"]["uri"]
        except Exception:
            print(f"[gemini] unexpected result shape: {str(done)[:250]}", file=sys.stderr, flush=True)
            return None
        try:
            v = httpx.get(uri, headers={"x-goog-api-key": api_key()}, timeout=600.0,
                          follow_redirects=True)
            v.raise_for_status()
            return _store(v.content, ".mp4", "shot")
        except Exception as e:
            print(f"[gemini] video download failed: {e}", file=sys.stderr, flush=True)
            return None
    print(f"[gemini] {model} timed out after {timeout:.0f}s", file=sys.stderr, flush=True)
    return None
