# -*- coding: utf-8 -*-
"""cloudtts.py -- Google Cloud Text-to-Speech (Chirp 3 HD) for Telugu and the other Indic languages the
fal ElevenLabs voices can't speak natively.

This is a DIFFERENT Google product from gemini.py: the Cloud TTS API (texttospeech.googleapis.com),
authenticated with its own GOOGLE_TTS_API_KEY -- NOT the AI-Studio / Gemini key, which Cloud TTS rejects.
The owner's ear chose Chirp 3 HD over both ElevenLabs and Gemini for Telugu diction. English stays on
ElevenLabs (its Indian voice artists carry the Indian accent; Cloud TTS has no en-IN Chirp 3 HD voice),
and child lines stay on ElevenLabs too. So this module is only ever reached for a Telugu/Indic adult line.
"""
from __future__ import annotations
import os
import sys
import base64

BASE = "https://texttospeech.googleapis.com/v1"

# 2-letter code -> BCP-47, for the Indic languages that actually have Chirp 3 HD voices (verified via the
# ListVoices API). Odia (or) and Assamese (as) have NO Chirp 3 HD, so they are deliberately absent and a
# line in them falls back to the fal path. Hindi/Tamil have Chirp 3 HD too but are routed to ElevenLabs
# upstream (it reads them with an Indian voice), so they only reach here if a Chirp voice is picked by hand.
_BCP47 = {"te": "te-IN", "kn": "kn-IN", "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN",
          "gu": "gu-IN", "pa": "pa-IN", "ur": "ur-IN", "hi": "hi-IN", "ta": "ta-IN"}


def _key() -> str:
    return (os.environ.get("GOOGLE_TTS_API_KEY") or "").strip()


def available() -> bool:
    return bool(_key())


def supports(lang_code: str) -> bool:
    """Whether a 2-letter language code has Chirp 3 HD voices we can address."""
    return (lang_code or "").strip().lower() in _BCP47


def synth(text: str, voice_short: str, lang_code: str) -> str | None:
    """Synthesise one line with a Chirp 3 HD voice and store it as a served /media mp3. Returns the path.

    `voice_short` is the bare Chirp voice name (e.g. "Achernar"); the full voice id is built per language
    ("te-IN-Chirp3-HD-Achernar"). Returns None on any failure so the caller can fall back to the fal path.
    """
    import httpx
    text = (text or "").strip()
    bcp = _BCP47.get((lang_code or "").strip().lower())
    if not text or not bcp or not available():
        return None
    body = {"input": {"text": text},
            "voice": {"languageCode": bcp, "name": f"{bcp}-Chirp3-HD-{voice_short}"},
            "audioConfig": {"audioEncoding": "MP3"}}
    try:
        r = httpx.post(f"{BASE}/text:synthesize?key={_key()}", json=body, timeout=180.0)
        if r.status_code >= 400:
            print(f"[cloudtts] {bcp}-{voice_short} HTTP {r.status_code}: {r.text[:200]}",
                  file=sys.stderr, flush=True)
            return None
        data = base64.b64decode(r.json()["audioContent"])
    except Exception as e:
        print(f"[cloudtts] {bcp}-{voice_short} failed: {e}", file=sys.stderr, flush=True)
        return None
    import gemini  # reuse the served media folder + /media path convention
    return gemini._store(data, ".mp3", "vo")
