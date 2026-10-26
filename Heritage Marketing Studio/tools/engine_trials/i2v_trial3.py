#!/usr/bin/env python
"""i2v_trial3.py -- SCENE B: a harder frame (boy + hand holding the pouch front-on), same prompt for every engine.
Scratch script, not product code. Output: Downloads\\engine-trial\\i2v_B_<engine>.mp4. Prompt-rewriting switched OFF where the
API allows (Wan enable_prompt_expansion, MiniMax prompt_expansion_mode), so every engine reads the SAME words.
"""
import base64, json, os, sys, threading, time, urllib.request
API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
OUT = r"C:\Users\punie\Downloads\engine-trial"
sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import fal_client, httpx

B64 = base64.b64encode(open(os.path.join(OUT, "cand_B_28.5.jpg"), "rb").read()).decode()
DATA_URI = "data:image/jpeg;base64," + B64
PROMPT = ("Animate this frame. The boy takes the steel glass of milk from the counter and lifts it; the mother keeps "
          "holding the Heritage pouch steady, its front label facing the camera. Camera: a slow, gentle handheld push-in, "
          "shallow depth of field. Keep the pouch, its label and colours, the boy's face, his white shirt and grey shorts, "
          "and the kitchen exactly as in the image. No on-screen text, captions or subtitles.")

def fal_run(label, endpoint, args):
    t0 = time.time()
    try:
        res = fal_client.subscribe(endpoint, arguments=args, with_logs=False)
        url = ((res.get("video") or {}).get("url")) if isinstance(res, dict) else None
        if not url:
            print(f"[B_{label}] NO VIDEO keys={list(res.keys()) if isinstance(res, dict) else res}", flush=True); return
        dest = os.path.join(OUT, f"i2v_B_{label}.mp4"); urllib.request.urlretrieve(url, dest)
        print(f"[B_{label}] OK {time.time()-t0:.0f}s -> {dest} ({os.path.getsize(dest)} bytes)", flush=True)
    except Exception as e:
        print(f"[B_{label}] ERROR {time.time()-t0:.0f}s: {type(e).__name__}: {str(e)[:500]}", flush=True)

def omni():
    label, t0 = "omni", time.time()
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    body = {"model": "gemini-omni-1.1-flash",
            "input": [{"type": "image", "data": B64, "mime_type": "image/jpeg"}, {"type": "text", "text": PROMPT + " About 5 seconds."}],
            "response_format": {"type": "video", "aspect_ratio": "16:9", "resolution": "720p"}}
    try:
        r = httpx.post("https://generativelanguage.googleapis.com/v1beta/interactions", params={"key": key}, json=body, timeout=900)
        if r.status_code >= 400: print(f"[B_{label}] HTTP {r.status_code}: {r.text[:500]}", flush=True); return
        d = r.json(); vid = None
        for step in d.get("steps", []):
            for c in step.get("content", []) or []:
                if c.get("type") == "video": vid = c
        if not vid or not vid.get("data"): print(f"[B_{label}] no inline video; keys={list(d.keys())}", flush=True); return
        dest = os.path.join(OUT, "i2v_B_omni.mp4"); open(dest, "wb").write(base64.b64decode(vid["data"]))
        print(f"[B_{label}] OK {time.time()-t0:.0f}s -> {dest} ({os.path.getsize(dest)} bytes) video_tokens={[m for m in d.get('usage',{}).get('output_tokens_by_modality',[])]}", flush=True)
    except Exception as e:
        print(f"[B_{label}] ERROR {time.time()-t0:.0f}s: {type(e).__name__}: {str(e)[:500]}", flush=True)

JOBS = {
  "veo31_fast_control": lambda: fal_run("veo31_fast_control", "fal-ai/veo3.1/fast/image-to-video", {"prompt": PROMPT, "image_url": DATA_URI, "duration": "6s", "aspect_ratio": "16:9", "resolution": "720p", "generate_audio": False}),
  "kling30": lambda: fal_run("kling30", "fal-ai/kling-video/v3/standard/image-to-video", {"prompt": PROMPT, "start_image_url": DATA_URI, "duration": "5", "generate_audio": False}),
  "kling40": lambda: fal_run("kling40", "kling/v4/image-to-video", {"prompt": PROMPT, "start_image_url": DATA_URI, "duration": 5, "resolution": "720p"}),
  "minimax_h3max": lambda: fal_run("minimax_h3max", "minimax/h3-max/image-to-video", {"prompt": PROMPT, "image_url": DATA_URI, "duration": 5, "resolution": "768P", "prompt_expansion_mode": "disabled"}),
  "wan30": lambda: fal_run("wan30", "alibaba/wan-3.0/image-to-video", {"prompt": PROMPT, "start_image_url": DATA_URI, "duration": 5, "resolution": "720p", "aspect_ratio": "16:9", "audio": False, "enable_prompt_expansion": False}),
  "seedance20": lambda: fal_run("seedance20", "bytedance/seedance-2.0/image-to-video", {"prompt": PROMPT, "image_url": DATA_URI, "duration": "5", "resolution": "720p", "aspect_ratio": "16:9", "generate_audio": False}),
  "omni": omni,
}
only = sys.argv[1:] or list(JOBS)
ts = [threading.Thread(target=JOBS[k]) for k in only]
[t.start() for t in ts]; [t.join() for t in ts]
print("DONE", flush=True)
