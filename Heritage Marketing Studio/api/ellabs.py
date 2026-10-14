# -*- coding: utf-8 -*-
"""ellabs.py -- DIRECT ElevenLabs TTS (the owner's own ElevenLabs account), NOT via fal.

Built but DORMANT on purpose (14 Oct): the studio's ElevenLabs voices are reached through fal today
(see filmaudio.run_fal), and the owner chose to keep Chirp primary with fal as the fallback. This module
is the ready path for a DIRECT account -- needed for a private voice CLONE (fal can't see voices in the
owner's own account) or to drop fal's margin later. It stays inert until BOTH are true:
  1. ELEVENLABS_API_KEY is set (available() is False without it, so nothing calls this), and
  2. a Voice with provider "el-direct" is cast (e.g. a cloned brand voice registered in filmvoice.VOICES).
Activating it then needs no code change -- just the key and the voice row. Fal remains the fallback.
"""
from __future__ import annotations
import os
import sys

BASE = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_multilingual_v2"   # swap to a v3 model id here if/when the account uses it


def _key() -> str:
    return (os.environ.get("ELEVENLABS_API_KEY") or "").strip()


def available() -> bool:
    return bool(_key())


def synth(text: str, voice_id: str, model: str = DEFAULT_MODEL,
          stability: float = 0.45, similarity: float = 0.8) -> str | None:
    """Synthesise one line with a DIRECT ElevenLabs voice (any voice in the account, incl. a clone) and
    store it as a served /media mp3. Returns the path, or None on any failure so the caller can fall back.
    """
    import httpx
    text = (text or "").strip()
    if not text or not voice_id or not available():
        return None
    try:
        r = httpx.post(f"{BASE}/text-to-speech/{voice_id}?output_format=mp3_44100_128",
                       headers={"xi-api-key": _key(), "Content-Type": "application/json",
                                "Accept": "audio/mpeg"},
                       json={"text": text, "model_id": model,
                             "voice_settings": {"stability": stability, "similarity_boost": similarity}},
                       timeout=180.0)
        if r.status_code >= 400:
            print(f"[ellabs] {voice_id} HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr, flush=True)
            return None
        data = r.content
    except Exception as e:
        print(f"[ellabs] {voice_id} failed: {e}", file=sys.stderr, flush=True)
        return None
    import gemini  # reuse the served media folder + /media path convention
    return gemini._store(data, ".mp3", "vo")
