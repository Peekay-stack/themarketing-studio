"""heygen.py — HeyGen avatar/presenter video provider.

Second video provider for the Video Studio, alongside the fal.ai cinematic gateway.
HeyGen renders a realistic human presenter speaking a script — ideal for product
explainers, recipe how-tos and multilingual (Hindi/Telugu/Tamil/English) versions.

If HEYGEN_API_KEY is set, real videos are generated via HeyGen's REST API (v2 generate +
status polling). Without a key, a MockProvider returns a placeholder so the app runs keyless.
Mirrors creative.py's provider pattern exactly.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request

API = "https://api.heygen.com"

# Curated fallback presenters/voices for the picker when no key is set (the demo/mock path).
# When a key IS set, list_avatars()/list_voices() fetch the real ones from the account.
DEFAULT_AVATARS = [
    {"id": "presenter_f_warm", "label": "Presenter — female, warm (default)", "avatar_id": "Daisy-inskirt-20220818", "ratio": "9:16"},
    {"id": "presenter_m_trust", "label": "Presenter — male, trustworthy", "avatar_id": "Tyler-incasualsuit-20220721", "ratio": "9:16"},
    {"id": "presenter_f_studio", "label": "Presenter — female, studio (16:9)", "avatar_id": "Anna_public_3_20240108", "ratio": "16:9"},
]
DEFAULT_VOICES = [
    {"id": "en_in_female", "label": "English (India) — warm female", "voice_id": "1bd001e7e50f421d891986aad5158bc8", "language": "English"},
    {"id": "hi_female", "label": "Hindi — female", "voice_id": "d7bbcdd6964c47bdaae26decade4a933", "language": "Hindi"},
    {"id": "te_female", "label": "Telugu — female", "voice_id": "te-IN-ShrutiNeural", "language": "Telugu"},
    {"id": "ta_female", "label": "Tamil — female", "voice_id": "ta-IN-PallaviNeural", "language": "Tamil"},
]
RATIOS = ["9:16", "16:9", "1:1"]
_DIM = {"9:16": (720, 1280), "16:9": (1280, 720), "1:1": (1080, 1080)}


def has_key() -> bool:
    return bool(os.environ.get("HEYGEN_API_KEY"))


def _get(path: str):
    req = urllib.request.Request(API + path, headers={"X-Api-Key": os.environ["HEYGEN_API_KEY"]})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _post(path: str, body: dict):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        API + path, data=data, method="POST",
        headers={"X-Api-Key": os.environ["HEYGEN_API_KEY"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def list_avatars() -> list[dict]:
    if not has_key():
        return DEFAULT_AVATARS
    try:
        data = _get("/v2/avatars").get("data", {})
        avatars = data.get("avatars", []) if isinstance(data, dict) else []
        out = []
        for a in avatars[:40]:
            out.append({"id": a.get("avatar_id"), "label": a.get("avatar_name") or a.get("avatar_id"),
                        "avatar_id": a.get("avatar_id"), "ratio": "9:16",
                        "preview": a.get("preview_image_url")})
        return out or DEFAULT_AVATARS
    except Exception:
        return DEFAULT_AVATARS


def list_voices() -> list[dict]:
    if not has_key():
        return DEFAULT_VOICES
    try:
        data = _get("/v2/voices").get("data", {})
        voices = data.get("voices", []) if isinstance(data, dict) else []
        out = []
        for v in voices[:80]:
            out.append({"id": v.get("voice_id"), "label": f'{v.get("language","")} — {v.get("name","")}'.strip(" —"),
                        "voice_id": v.get("voice_id"), "language": v.get("language", "")})
        return out or DEFAULT_VOICES
    except Exception:
        return DEFAULT_VOICES


class MockProvider:
    def generate(self, script: str, avatar_id: str, voice_id: str, ratio: str) -> dict:
        w, h = _DIM.get(ratio, _DIM["9:16"])
        return {"url": f"https://placehold.co/{w}x{h}/14331F/E8A93C.png?text=HeyGen+avatar+video",
                "provider": "mock", "kind": "avatar", "status": "mock",
                "avatar_id": avatar_id, "voice_id": voice_id, "ratio": ratio}


class HeyGenProvider:
    """Real avatar video via HeyGen v2 generate + status polling."""
    def generate(self, script: str, avatar_id: str, voice_id: str, ratio: str,
                 max_wait: int = 180) -> dict:
        w, h = _DIM.get(ratio, _DIM["9:16"])
        body = {
            "video_inputs": [{
                "character": {"type": "avatar", "avatar_id": avatar_id, "avatar_style": "normal"},
                "voice": {"type": "text", "input_text": script, "voice_id": voice_id},
            }],
            "dimension": {"width": w, "height": h},
        }
        resp = _post("/v2/video/generate", body)
        video_id = (resp.get("data") or {}).get("video_id")
        if not video_id:
            return {"url": None, "provider": "heygen", "kind": "avatar", "status": "error", "detail": resp}
        # poll for completion
        deadline = time.time() + max_wait
        while time.time() < deadline:
            st = _get(f"/v1/video_status.get?video_id={urllib.parse.quote(video_id)}").get("data", {})
            status = st.get("status")
            if status == "completed":
                return {"url": st.get("video_url"), "provider": "heygen", "kind": "avatar",
                        "status": "completed", "video_id": video_id, "ratio": ratio}
            if status in ("failed", "error"):
                return {"url": None, "provider": "heygen", "kind": "avatar", "status": "failed",
                        "video_id": video_id, "detail": st.get("error")}
            time.sleep(5)
        # still rendering — return the id so the UI can poll later
        return {"url": None, "provider": "heygen", "kind": "avatar", "status": "processing", "video_id": video_id}


def provider():
    return HeyGenProvider() if has_key() else MockProvider()


def generate_avatar_video(script: str, avatar_id: str, voice_id: str, ratio: str = "9:16") -> dict:
    return provider().generate(script, avatar_id, voice_id, ratio)
