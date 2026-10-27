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
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections import deque
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

# Video. Gemini Omni 1.1 Flash through the Interactions API. Google retired the Veo preview models from this
# API (HTTP 404 from 23 Oct 2026) and Omni is the video model left on it. ONE model, two resolutions, so the two
# studio tiers differ in sharpness and price and not in who draws the shot: Draft = 360p, Final = 720p.
# Billed by token, MEASURED on 27 Oct 2026: 9,655 video tokens per 5 s at 360p and 28,960 at 720p, at $17.50 per
# million -> about $0.034 and $0.101 per second. The keys stay "lite"/"standard" because the studio's tier names
# (and the saved films that carry them) are older than the engine.
OMNI_MODEL = "gemini-omni-1.1-flash"
VIDEO_MODELS = {"lite": OMNI_MODEL, "standard": OMNI_MODEL}
VIDEO_RESOLUTION = {"lite": "360p", "standard": "720p"}
# There is no duration parameter: the length is steered by the words "About N seconds." in the prompt. Measured
# 27 Oct: N = 3, 4, 5, 6, 7, 8 each came back within 0.05 s of N.
VIDEO_SECONDS = (3, 8)

# The API's own 429 says: "limit: 8 requests per minute on Tier 2". The limiter keeps every render in this
# process under that with one request to spare, so a six-shot film fires at once and a second film queues behind
# it instead of failing. Set OMNI_RPM higher after a tier upgrade.
OMNI_RPM = max(1, int(os.environ.get("OMNI_RPM") or 7))
_omni_stamps: deque = deque()
_omni_lock = threading.Lock()
_tls = threading.local()


def _omni_slot() -> None:
    """Block until this process may send one more Omni request without passing OMNI_RPM in any 60 s window."""
    while True:
        with _omni_lock:
            now = time.time()
            while _omni_stamps and now - _omni_stamps[0] >= 60.0:
                _omni_stamps.popleft()
            if len(_omni_stamps) < OMNI_RPM:
                _omni_stamps.append(now)
                return
            wait = 60.0 - (now - _omni_stamps[0]) + 0.25
        time.sleep(max(0.25, wait))


def video_error() -> str:
    """Why the last `video()` call on THIS thread returned None, in words fit to show a person. '' after a success."""
    return getattr(_tls, "error", "") or ""


# When Omni refuses on quota or billing, bench it briefly so the other shots of the SAME film skip straight to
# the fallback instead of each making a doomed call. The bench is deliberately SHORT: once credit is restored the
# very next render must be able to use it, so a long bench would keep a topped-up account on the fallback.
_QUOTA_SPENT: dict[str, float] = {}
QUOTA_COOLDOWN = 90.0


def quota_spent(tier: str = "") -> str:
    """A human reason if this tier is known to be out of quota or credit right now, else ''."""
    model = VIDEO_MODELS.get(tier) or tier
    until = _QUOTA_SPENT.get(model, 0.0)
    if until <= time.time():
        return ""
    mins = max(1, int((until - time.time()) / 60))
    return (f"{model} is out of quota or credit on this Google project. Not retrying it for another {mins} min. "
            f"Top up the Gemini API balance at https://ai.studio/projects, or switch the video engine to fal")

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


_TTS_MODEL = "gemini-2.5-flash-preview-tts"


def _pcm_to_wav(pcm: bytes, rate: int = 24000, bits: int = 16, ch: int = 1) -> bytes:
    """Gemini TTS returns raw little-endian PCM (audio/L16); wrap it in a WAV header so it plays and mixes."""
    import struct
    byte_rate = rate * ch * bits // 8
    block = ch * bits // 8
    return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
            + b"fmt " + struct.pack("<IHHIIHH", 16, 1, ch, rate, byte_rate, block, bits)
            + b"data" + struct.pack("<I", len(pcm)) + pcm)


def tts(text: str, voice_name: str, style: str = "", model: str = _TTS_MODEL) -> str | None:
    """Synthesise one line with Gemini TTS and store it as a served /media WAV. Returns the path, or None.

    Used by filmvoice for Telugu and the other Indic languages the fal ElevenLabs voices can't speak. It uses
    the same key as the rest of this module (GOOGLE_API_KEY / GEMINI_API_KEY). `style` is an optional
    natural-language delivery hint the model reads but never speaks. One retry: the TTS model occasionally
    returns no audio for a short or punctuation-heavy line.
    """
    import httpx
    text = (text or "").strip()
    if not text or not available():
        return None
    prompt = f"{style} {text}".strip() if style else text
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig":
                                                                  {"voiceName": voice_name}}}}}
    for attempt in (1, 2):
        try:
            r = httpx.post(f"{BASE}/models/{model}:generateContent", headers=_headers(),
                           json=body, timeout=180.0)
            if r.status_code >= 400:
                print(f"[gemini] tts {voice_name} HTTP {r.status_code}: {r.text[:200]}",
                      file=sys.stderr, flush=True)
                continue
            cand = (r.json().get("candidates") or [{}])[0]
            parts = (cand.get("content") or {}).get("parts") or []
            inline = next((p["inlineData"] for p in parts if "inlineData" in p), None)
            if not inline:
                print(f"[gemini] tts {voice_name}: no audio (finish={cand.get('finishReason', '?')}), "
                      f"attempt {attempt}", file=sys.stderr, flush=True)
                continue
            pcm = base64.b64decode(inline["data"])
            rate, mime = 24000, inline.get("mimeType", "")
            if "rate=" in mime:
                try:
                    rate = int(mime.split("rate=")[1].split(";")[0])
                except ValueError:
                    pass
            return _store(_pcm_to_wav(pcm, rate), ".wav", "vo")
        except Exception as e:
            print(f"[gemini] tts {voice_name} failed: {e}", file=sys.stderr, flush=True)
    return None


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
def _silent(data: bytes) -> bytes:
    """Omni's clip carries its own (very quiet) ambience track. The soundtrack is built separately and mixed over
    the whole cut, so the picture must stay SILENT, as the Veo shots were asked to be. Remux without audio; if
    ffmpeg is not available, the original bytes go through unchanged and the mix simply ignores that track."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return data
    tmp = tempfile.mkdtemp(prefix="omni-")
    try:
        src, dst = os.path.join(tmp, "in.mp4"), os.path.join(tmp, "out.mp4")
        with open(src, "wb") as fh:
            fh.write(data)
        res = subprocess.run([exe, "-y", "-i", src, "-an", "-c:v", "copy", "-movflags", "+faststart", dst],
                             capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0:
            with open(dst, "rb") as fh:
                return fh.read()
        print(f"[gemini] could not strip the clip's audio: {res.stderr[-200:]}", file=sys.stderr, flush=True)
        return data
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def _video_bytes(data) -> bytes | None:
    """The mp4 out of an Interactions response: inline base64 when small, otherwise a file URI to download."""
    inter = data.get("interaction") if isinstance(data, dict) and isinstance(data.get("interaction"), dict) else data
    blocks = []
    for step in (inter.get("steps") or []) if isinstance(inter, dict) else []:
        for block in (step.get("content") or []) if isinstance(step, dict) else []:
            if isinstance(block, dict) and str(block.get("type")) == "video":
                blocks.append(block)
    for block in blocks:
        if block.get("data"):
            return base64.b64decode(block["data"])
        uri = block.get("uri") or block.get("url") or block.get("file_uri")
        if uri:
            import httpx
            try:
                v = httpx.get(uri, headers={"x-goog-api-key": api_key()}, timeout=600.0, follow_redirects=True)
                v.raise_for_status()
                return v.content
            except Exception as e:
                print(f"[gemini] video download failed: {e}", file=sys.stderr, flush=True)
                return None
    keys = [list(b.keys()) for b in blocks] or (list(inter.keys()) if isinstance(inter, dict) else type(inter).__name__)
    print(f"[gemini] no video in the response; shape={keys}", file=sys.stderr, flush=True)
    return None


def video(prompt: str, *, image_ref: str = "", seconds: int = 8, ratio: str = "16:9",
          tier: str = "lite", poll_seconds: float = 10.0, timeout: float = 900.0) -> str | None:
    """Generate one SILENT shot with Gemini Omni. Animates `image_ref` when given, which is what keeps the cast
    and the pack identical to the approved frame. Returns a served '/media/...' path, or None.

    On None, `video_error()` says why. One synchronous call (Omni returns the clip in the response, ~20-60 s), so
    `poll_seconds` is kept only for the caller's signature. The length is steered by a closing "About N seconds."
    sentence that this function owns, so a prompt compiler must not write one.
    """
    _tls.error = ""
    if not available():
        _tls.error = "no Google API key is set"
        return None
    import httpx
    res = VIDEO_RESOLUTION.get(tier) or VIDEO_RESOLUTION["lite"]
    secs = max(VIDEO_SECONDS[0], min(VIDEO_SECONDS[1], int(round(float(seconds or 5)))))
    reason = quota_spent(tier)
    if reason:
        print(f"[gemini] skipping {OMNI_MODEL}: {reason}", file=sys.stderr, flush=True)
        _tls.error = reason
        return None
    blocks: list = []
    ref = _as_base64(image_ref) if image_ref else None
    if ref:
        blocks.append({"type": "image", "data": ref[1], "mime_type": ref[0]})
    elif image_ref:
        print("[gemini] reference frame unusable, falling back to text-to-video", file=sys.stderr, flush=True)
    text = re.sub(r"\s*About\s+\d+\s+seconds?\.?\s*$", "", str(prompt or "").strip(), flags=re.I)
    blocks.append({"type": "text", "text": f"{text} About {secs} seconds."})
    body = {"model": OMNI_MODEL, "input": blocks,
            "response_format": {"type": "video", "aspect_ratio": ratio if ratio in ("16:9", "9:16") else "16:9",
                                "resolution": res}}
    attempts, server_waits = 0, [10.0, 25.0]
    while True:
        attempts += 1
        _omni_slot()
        try:
            r = httpx.post(INTERACTIONS, headers=_headers(), json=body, timeout=timeout)
        except Exception as e:
            _tls.error = f"the request to Google failed: {type(e).__name__}"
            print(f"[gemini] {OMNI_MODEL} submit failed: {e}", file=sys.stderr, flush=True)
            return None
        if r.status_code < 400:
            break
        text_err = r.text or ""
        print(f"[gemini] {OMNI_MODEL} HTTP {r.status_code}: {text_err[:300]}", file=sys.stderr, flush=True)
        if r.status_code == 429:
            m = re.search(r"retry in (\d+)\s*s", text_err, re.I)
            if attempts <= 3:
                pause = min(70.0, float(m.group(1)) + 1.0 if m else 20.0)
                print(f"[gemini] rate limited, waiting {pause:.0f}s then retrying this shot",
                      file=sys.stderr, flush=True)
                time.sleep(pause)
                continue
            _QUOTA_SPENT[OMNI_MODEL] = time.time() + QUOTA_COOLDOWN
            _tls.error = "Google's per-minute video limit was still hit after waiting; try again in a minute"
            return None
        if r.status_code in (402, 403) and ("credit" in text_err.lower() or "billing" in text_err.lower()
                                            or "prepay" in text_err.lower() or r.status_code == 402):
            _QUOTA_SPENT[OMNI_MODEL] = time.time() + QUOTA_COOLDOWN
            _tls.error = ("the Gemini API prepayment credits are depleted: top up at https://ai.studio/projects "
                          "(out of credit)")
            return None
        if r.status_code == 400 and "safety" in text_err.lower():
            _tls.error = "Google's safety filter blocked this shot (no video returned)"
            return None
        if r.status_code in (500, 503) and server_waits:
            time.sleep(server_waits.pop(0))
            continue
        _tls.error = f"Google returned HTTP {r.status_code}"
        return None
    try:
        got = _video_bytes(r.json())
    except Exception as e:
        _tls.error = f"unreadable response from Google ({type(e).__name__})"
        return None
    if not got:
        _tls.error = "Google returned no video"
        return None
    return _store(_silent(got), ".mp4", "shot")
