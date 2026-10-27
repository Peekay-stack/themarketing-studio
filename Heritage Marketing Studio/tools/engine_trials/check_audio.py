#!/usr/bin/env python
"""check_audio.py -- does an Omni clip contain human speech? Extracts each clip's audio track and asks a Gemini model to transcribe it
(audio-only is more reliable than asking about a video). Also reports loudness. Pennies. Scratch script."""
import base64, json, os, re, subprocess, sys
API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
D = r"C:\Users\punie\Downloads\engine-trial"; S = os.path.join(D, "step1")
sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import httpx, imageio_ffmpeg
exe = imageio_ffmpeg.get_ffmpeg_exe(); KEY = os.environ["GOOGLE_API_KEY"].strip(); MODEL = "gemini-3.5-flash"
CLIPS = {"OLD A 720p": os.path.join(D, "i2v_omni.mp4"), "OLD A 360p": os.path.join(D, "i2v_omni360.mp4"), "OLD B 720p": os.path.join(D, "i2v_B_omni.mp4"),
         "A_new_1": os.path.join(S, "A_new_1.mp4"), "A_new_2": os.path.join(S, "A_new_2.mp4"), "B_old_360": os.path.join(S, "B_old_360.mp4"),
         "B_new_1": os.path.join(S, "B_new_1.mp4"), "B_new_2": os.path.join(S, "B_new_2.mp4"),
         **{f"six_{k}": os.path.join(S, f"six_{k}.mp4") for k in ("s1", "s2", "s3", "s4", "s5", "s6")}}
Q = ("Listen to this audio carefully. Reply with ONLY compact JSON: "
     '{"human_voice": "yes" or "no" (any human voice at all, including murmurs, hums, singing, a few words, in ANY language), '
     '"words": "verbatim words in the original language and script, or NONE", '
     '"other_sounds": "short list of non-speech sounds you hear"}')
for name, path in CLIPS.items():
    mp3 = os.path.join(S, "_a.mp3")
    subprocess.run([exe, "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", mp3], capture_output=True)
    if not os.path.exists(mp3) or os.path.getsize(mp3) < 500:
        print(f"{name:12s} NO AUDIO TRACK"); continue
    lv = subprocess.run([exe, "-i", path, "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr
    mean = re.search(r"mean_volume: ([-\d.]+) dB", lv)
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(open(mp3, "rb").read()).decode()}}, {"text": Q}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent", params={"key": KEY}, json=body, timeout=200)
    try: ans = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    except Exception: ans = {"error": r.text[:200]}
    print(f"{name:12s} mean {mean.group(1) if mean else '?':>7s} dB | {json.dumps(ans, ensure_ascii=False)[:300]}", flush=True)
