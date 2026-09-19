"""creative.py — multi-provider creative gateway.

Image + cinematic video route through ONE integration (fal.ai). Avatar/presenter video
routes through HeyGen (heygen.py). If a provider's key is absent, a MockProvider returns
placeholder assets so the whole app runs with zero keys. Add models in CATALOG — one place.
"""
from __future__ import annotations

import base64
import hashlib
import mimetypes
import os
import sys
import urllib.parse
from dataclasses import dataclass

import gemini
import heygen


@dataclass
class CreativeModel:
    id: str          # what the UI sends
    label: str       # what the creative sees
    kind: str        # "image" | "video" | "avatar"
    provider: str    # "fal" | "heygen"
    ref: str         # provider-specific id (fal endpoint, or HeyGen avatar id)
    note: str


# The catalogue the front-end picker renders.
CATALOG: list[CreativeModel] = [
    # --- images (fal.ai) ---
    CreativeModel("ideogram-v3", "Ideogram v3 — best for text-in-image", "image",
                  "fal", "fal-ai/ideogram/v3", "Social cards with captions / brand line / CTA."),
    CreativeModel("imagen-4-ultra", "Imagen 4 Ultra — most photorealistic", "image",
                  "fal", "fal-ai/imagen4/preview/ultra", "Premium product & hero shots."),
    CreativeModel("nano-banana-2", "Nano Banana 2 — most consistent all-rounder", "image",
                  "fal", "fal-ai/nano-banana-2", "Versatile, good typography."),
    CreativeModel("flux-2", "FLUX.2 — open-weight photoreal", "image",
                  "fal", "fal-ai/flux-2", "Strong photoreal, cost-effective."),
    # --- cinematic video (fal.ai) ---
    CreativeModel("veo-3.1", "Veo 3.1 — premium video + native audio", "video",
                  "fal", "fal-ai/veo3.1", "Best cinematic default; great for YouTube."),
    CreativeModel("veo-3.1-fast", "Veo 3.1 Fast — same model, cheaper + quicker", "video",
                  "fal", "fal-ai/veo3.1/fast", "Drafts and iterations at lower cost."),
    CreativeModel("veo-3", "Veo 3 — previous generation", "video",
                  "fal", "fal-ai/veo3", "Fallback when 3.1 isn't enabled on the account."),
    CreativeModel("kling-3.0", "Kling 3.0 — cheapest premium, high-volume social", "video",
                  "fal", "fal-ai/kling-video/v3/standard/text-to-video",
                  "Short-form Reels at low cost."),
    # --- avatar / presenter video (HeyGen) ---
    CreativeModel("heygen-avatar", "HeyGen — avatar presenter (multilingual)", "avatar",
                  "heygen", "", "Talking-head explainers & recipes; Hindi/Telugu/Tamil/English."),
]
_BY_ID = {m.id: m for m in CATALOG}


def list_models(kind: str | None = None) -> list[dict]:
    return [m.__dict__ for m in CATALOG if kind is None or m.kind == kind]


def model_provider(model_id: str) -> str | None:
    m = _BY_ID.get(model_id)
    return m.provider if m else None


def _dig_url(result):
    """Pull a media URL out of any of the shapes fal endpoints return."""
    if not isinstance(result, dict):
        return None
    # image shapes
    if result.get("images"):
        first = result["images"][0]
        if isinstance(first, dict):
            return first.get("url")
        if isinstance(first, str):
            return first
    if isinstance(result.get("image"), dict) and result["image"].get("url"):
        return result["image"]["url"]
    # video shapes
    if isinstance(result.get("video"), dict) and result["video"].get("url"):
        return result["video"]["url"]
    if result.get("videos"):
        first = result["videos"][0]
        if isinstance(first, dict) and first.get("url"):
            return first["url"]
    if isinstance(result.get("output"), dict) and result["output"].get("url"):
        return result["output"]["url"]
    if isinstance(result.get("url"), str):
        return result["url"]
    return None


class MockProvider:
    """Deterministic placeholder assets so the app runs without any provider key."""
    def generate(self, model: CreativeModel, prompt: str, **kw) -> dict:
        seed = hashlib.md5(f"{model.id}:{prompt}".encode()).hexdigest()[:8]
        if model.kind == "image":
            text = urllib.parse.quote((prompt[:48] + "…") if len(prompt) > 48 else prompt)
            url = f"https://placehold.co/1080x1080/14331F/FBF6EA.png?text={text}"
        else:
            url = f"https://placehold.co/1280x720/14331F/E8A93C.png?text=VIDEO+{seed}"
        return {"url": url, "provider": "mock", "model": model.id, "kind": model.kind}


_IMAGE_SIZES = {"16:9": "landscape_16_9", "9:16": "portrait_16_9", "1:1": "square_hd",
                "4:3": "landscape_4_3", "3:4": "portrait_4_3"}


def _video_args(model: CreativeModel, prompt: str, ratio, duration, with_audio: bool) -> dict:
    """Video endpoints take different arg shapes than image ones (and reject `seed`/`image_size`)."""
    args = {"prompt": prompt}
    args["aspect_ratio"] = ratio if ratio in ("16:9", "9:16", "1:1") else "16:9"
    try:
        secs = int(float(str(duration).rstrip("s") or 8))
    except (TypeError, ValueError):
        secs = 8
    if model.ref.startswith("fal-ai/veo"):
        # Veo renders in fixed 4/6/8s beats and can score its own audio. We normally render
        # SILENT and lay one continuous track over the joined film (see filmaudio) — that also
        # costs about half as much per second.
        args["duration"] = f"{min(8, max(4, secs))}s"
        args["resolution"] = "720p"
        args["generate_audio"] = bool(with_audio)
    elif "kling" in model.ref:
        args["duration"] = "10" if secs > 7 else "5"
    return args


class FalProvider:
    """Real generation through fal.ai. Used automatically when FAL_KEY is set.

    Accepts an optional `seed` (used to keep characters/style consistent across a set of
    images) and `image_size`. Robustly parses the many result shapes fal endpoints use, and
    logs the raw result keys to stderr (-> render-log.txt) when no URL is found, so a
    misconfigured or gated endpoint is diagnosable instead of silently failing."""
    def __init__(self, key: str):
        self.key = key

    def generate(self, model: CreativeModel, prompt: str, *, seed=None, image_size=None,
                 ratio=None, duration=None, with_audio: bool = False) -> dict:
        import fal_client  # type: ignore
        os.environ.setdefault("FAL_KEY", self.key)
        if model.kind == "video":
            args = _video_args(model, prompt, ratio, duration, with_audio)
        else:
            args = {"prompt": prompt}
            if seed is not None:
                args["seed"] = int(seed)
            # Image endpoints size by `image_size`, not `aspect_ratio` — without this a 16:9
            # storyboard frame came back square and had to be letterboxed.
            args["image_size"] = image_size or _IMAGE_SIZES.get(ratio, "square_hd")
        try:
            if model.kind == "video":
                # A film takes minutes; go through the queue instead of a blocking sync call.
                result = fal_client.subscribe(model.ref, arguments=args, with_logs=False)
            else:
                result = fal_client.run(model.ref, arguments=args)
        except Exception as e:
            print(f"[creative] fal error on {model.ref}: {e}", file=sys.stderr, flush=True)
            raise
        url = _dig_url(result)
        if not url:
            keys = list(result.keys()) if isinstance(result, dict) else type(result).__name__
            print(f"[creative] fal returned no URL from {model.ref}; result keys={keys}",
                  file=sys.stderr, flush=True)
        return {"url": url, "provider": "fal", "model": model.id, "kind": model.kind}


# Text-to-image fallbacks, tried in order. A CHAIN rather than one hardcoded id, because the single
# id this app used — `fal-ai/imagen4/ultra` — was wrong (the real path carries `/preview/`) and had
# been wrong at all seven call sites for as long as they existed. fal answered every one of them with
# `Application "imagen4" not found`, the caller turned that into "both image providers refused it",
# and the fallback that exists precisely for when Google is down was itself dead. Nobody could see it
# because it only runs when the primary already failed.
#
# So: try each in turn, and return which one worked. A provider renaming a model degrades to the next
# candidate instead of silently removing the safety net.
TEXT2IMG_CHAIN = (
    "fal-ai/imagen4/preview/ultra",
    "fal-ai/nano-banana-2",
    "fal-ai/flux-2",
)


def text_to_image(prompt: str, *, ratio: str = "1:1", seed=None) -> dict:
    """First working text-to-image endpoint in `TEXT2IMG_CHAIN`. Never raises.

    Returns `{url, endpoint, errors}` — `errors` is kept even on success so a caller can report which
    provider actually served the image, and a support question ("why is this slow / why does this look
    different") has an answer that does not require reading a log file.
    """
    errors = []
    for ep in TEXT2IMG_CHAIN:
        args = {"prompt": prompt, "aspect_ratio": ratio}
        if seed is not None:
            args["seed"] = seed
        try:
            url = run_endpoint(ep, args)
        except Exception as e:
            errors.append(f"{ep}: {e}")
            continue
        if url:
            return {"url": url, "endpoint": ep, "errors": errors}
        errors.append(f"{ep}: no image returned")
    return {"url": "", "endpoint": "", "errors": errors}


def run_endpoint(ref: str, args: dict) -> str | None:
    """Call any fal endpoint directly and return the first media URL.

    The CATALOG covers the plain text-to-image / text-to-video models the picker offers. Reference
    driven work — character-consistent frames, image-to-video — needs endpoint-specific arguments
    (`image_urls`, `reference_image_urls`, `image_url`), so those callers compose their own args
    and come through here.
    """
    key = os.environ.get("FAL_KEY")
    if not key:
        return None
    import fal_client  # type: ignore
    os.environ.setdefault("FAL_KEY", key)
    try:
        result = fal_client.subscribe(ref, arguments=args, with_logs=False)
    except Exception as e:
        print(f"[creative] fal error on {ref}: {e}", file=sys.stderr, flush=True)
        return None
    url = _dig_url(result)
    if not url:
        keys = list(result.keys()) if isinstance(result, dict) else type(result).__name__
        print(f"[creative] {ref} returned no URL; keys={keys}", file=sys.stderr, flush=True)
    return url


# Reference-driven endpoints. Text-to-image reinvents people on every call no matter how detailed
# the description or how fixed the seed, so a character has to be carried as an IMAGE.
REF_IMAGE_MODEL = "fal-ai/nano-banana-2/edit"        # edits/regenerates from reference images
REF_CHARACTER_MODEL = "fal-ai/ideogram/character"    # purpose-built character reference (1 image)
I2V_MODELS = {"veo-3.1-fast": "fal-ai/veo3.1/fast/image-to-video",
              "veo-3.1": "fal-ai/veo3.1/image-to-video"}


def _fal_ref(url: str) -> str | None:
    """A reference into whatever fal's API can actually fetch — a real http(s) URL passed through
    unchanged, anything local (a generated `/media/...` still, a real `/library-file/...` asset)
    base64-encoded into a `data:` URI instead.

    Real bug, found live: this function didn't exist, and every reference was passed straight through
    as a bare string. fal's own servers do the fetching, and a relative path is meaningless off this
    machine — it failed with "Invalid URL scheme" for a library asset specifically, but a `/media/...`
    reference would have failed exactly the same way; fal happening to be tried is what surfaced it,
    not something specific to one path shape. `gemini.local_path` already resolves both prefixes
    correctly (fixed alongside this), so it is reused here rather than duplicating the prefix matching.
    """
    s = str(url or "")
    if s.startswith(("http://", "https://", "data:")):
        return s
    p = gemini.local_path(s)
    if not p:
        return None
    mime = mimetypes.guess_type(p)[0] or "image/png"
    with open(p, "rb") as fh:
        return f"data:{mime};base64,{base64.b64encode(fh.read()).decode()}"


def image_from_reference(prompt: str, reference_urls: list[str], ratio: str = "16:9",
                         seed=None) -> str | None:
    """A new scene that keeps the people from the reference image(s) identical."""
    wanted = [u for u in (reference_urls or []) if u]
    refs = [r for r in (_fal_ref(u) for u in wanted) if r]
    if len(refs) < len(wanted):
        print(f"[creative] {len(wanted) - len(refs)} of {len(wanted)} reference(s) could not be "
              f"resolved to bytes — dropped rather than sent as an unusable path", file=sys.stderr,
              flush=True)
    if not refs:
        return None
    args = {"prompt": prompt, "image_urls": refs[:3],
            "aspect_ratio": ratio if ratio in ("16:9", "9:16", "1:1", "4:3", "3:4") else "16:9",
            "resolution": "1K", "num_images": 1}
    if seed is not None:
        args["seed"] = int(seed)
    url = run_endpoint(REF_IMAGE_MODEL, args)
    if url:
        return url
    # Fall back to the dedicated character model (takes a single reference).
    # Live-tested finding: this used to hardcode "landscape_16_9" regardless of what ratio the
    # caller actually asked for — a caller requesting a 1:1 social post that fell through to this
    # second-tier fallback silently got a 16:9 image back instead, which the frontend's square post
    # frame then force-cropped (`background-size:cover`), chopping the left/right edges off whatever
    # text or logo sat near them. `_IMAGE_SIZES` already has the real ratio->size mapping the primary
    # call above uses; this just needed to read from the same table instead of a fixed default.
    print("[creative] falling back to ideogram/character", file=sys.stderr, flush=True)
    return run_endpoint(REF_CHARACTER_MODEL, {
        "prompt": prompt, "reference_image_urls": refs[:1],
        "rendering_speed": "BALANCED", "image_size": _IMAGE_SIZES.get(ratio, "landscape_16_9"),
        **({"seed": int(seed)} if seed is not None else {})})


def video_from_image(model_id: str, prompt: str, image_url: str, *, seconds: int = 8,
                     ratio: str = "16:9") -> str | None:
    """Animate an approved storyboard frame, so the shot matches the board it was signed off from."""
    ref = I2V_MODELS.get(model_id) or I2V_MODELS["veo-3.1-fast"]
    secs = min(8, max(4, int(seconds)))
    return run_endpoint(ref, {
        "prompt": prompt, "image_url": image_url,
        "duration": f"{secs if secs in (4, 6, 8) else 8}s",
        "aspect_ratio": ratio if ratio in ("16:9", "9:16") else "16:9",
        "resolution": "720p", "generate_audio": False})


def _fal_provider():
    key = os.environ.get("FAL_KEY")
    return FalProvider(key) if key else MockProvider()


def generate_creative(model_id: str, prompt: str, *, avatar: str | None = None,
                      voice: str | None = None, ratio: str | None = None,
                      seed=None, image_size=None, duration=None,
                      with_audio: bool = False) -> dict:
    """Route by provider. For HeyGen avatar video, `prompt` is the script; `avatar`/`voice`
    select the presenter and voice. `seed` keeps a set of fal images visually consistent."""
    model = _BY_ID.get(model_id)
    if not model:
        raise ValueError(f"Unknown creative model '{model_id}'.")
    if model.provider == "heygen":
        avatars = heygen.list_avatars(); voices = heygen.list_voices()
        avatar_id = avatar or (avatars[0]["avatar_id"] if avatars else "")
        voice_id = voice or (voices[0]["voice_id"] if voices else "")
        res = heygen.generate_avatar_video(prompt, avatar_id, voice_id, ratio or "9:16")
        res["model"] = model.id
        return res
    prov = _fal_provider()
    if not isinstance(prov, FalProvider):
        return prov.generate(model, prompt)
    if model.kind != "video":
        return prov.generate(model, prompt, seed=seed, image_size=image_size)

    # fal enables video models per account, so the picked one may be absent even with a valid
    # key. Walk the video catalogue from the chosen model onwards rather than failing outright.
    chain = [model] + [m for m in CATALOG
                       if m.kind == "video" and m.provider == "fal" and m.id != model.id]
    last_error = None
    for candidate in chain:
        try:
            res = prov.generate(candidate, prompt, ratio=ratio, duration=duration,
                                with_audio=with_audio)
        except Exception as e:
            last_error = e
            continue
        if res.get("url"):
            if candidate.id != model.id:
                print(f"[creative] '{model.id}' unavailable; rendered with '{candidate.id}' instead.",
                      file=sys.stderr, flush=True)
            return res
    if last_error:
        raise last_error
    return {"url": None, "provider": "fal", "model": model.id, "kind": model.kind}
