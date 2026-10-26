#!/usr/bin/env python
"""i2v_trial.py -- same first frame, same motion prompt, every reachable video engine. Image-to-video, ~5 s, 720p, no audio.

Frame = the opening shot of the owner's 30s Heritage film (mother pouring from the real pouch). The control is OUR
current path (Veo 3.1 Fast image-to-video on fal). Output: Downloads\\engine-trial\\i2v_<engine>.mp4. A scratch script, not
product code; reads api/.env for the keys. Run from the api folder.
"""
import base64, json, os, sys, threading, time, urllib.request

API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
OUT = r"C:\Users\punie\Downloads\engine-trial"
sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import fal_client, httpx

FRAME_PATH = os.path.join(OUT, "frame_first.jpg")
B64 = base64.b64encode(open(FRAME_PATH, "rb").read()).decode()
DATA_URI = "data:image/jpeg;base64," + B64

PROMPT = ("Animate this frame. The mother keeps pouring the milk from the Heritage pouch into the steel vessel, the milk "
          "stream falling steadily; her head and hands move naturally. Camera: a slow, gentle handheld drift, shallow depth "
          "of field. Keep the pouch, its label and colours, her face, her saree and the kitchen exactly as in the image. "
          "No on-screen text, captions or subtitles.")

def save(url, label):
    dest = os.path.join(OUT, f"i2v_{label}.mp4"); urllib.request.urlretrieve(url, dest); return dest

def fal_run(label, endpoint, args):
    t0 = time.time()
    try:
        res = fal_client.subscribe(endpoint, arguments=args, with_logs=False)
        url = ((res.get("video") or {}).get("url")) if isinstance(res, dict) else None
        if not url: print(f"[{label}] NO VIDEO keys={list(res.keys()) if isinstance(res, dict) else res}", flush=True); return
        d = save(url, label); print(f"[{label}] OK {time.time()-t0:.0f}s -> {d} ({os.path.getsize(d)} bytes)", flush=True)
    except Exception as e:
        print(f"[{label}] ERROR {time.time()-t0:.0f}s: {type(e).__name__}: {str(e)[:500]}", flush=True)

def omni():
    label, t0 = "omni", time.time()
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    body = {"model": "gemini-omni-1.1-flash",
            "input": [{"type": "image", "data": B64, "mime_type": "image/jpeg"},
                      {"type": "text", "text": PROMPT + " About 5 seconds."}],
            "response_format": {"type": "video", "aspect_ratio": "16:9", "resolution": "720p"}}
    try:
        r = httpx.post("https://generativelanguage.googleapis.com/v1beta/interactions", params={"key": key}, json=body, timeout=900)
        if r.status_code >= 400:
            print(f"[{label}] HTTP {r.status_code}: {r.text[:700]}", flush=True); return
        d = r.json()
        vid = None
        for step in d.get("steps", []):
            for c in step.get("content", []) or []:
                if c.get("type") == "video": vid = c
        if not vid:
            print(f"[{label}] no video in response; top keys={list(d.keys())}; sample={json.dumps(d)[:600]}", flush=True); return
        dest = os.path.join(OUT, "i2v_omni.mp4")
        if vid.get("data"):
            open(dest, "wb").write(base64.b64decode(vid["data"]))
        else:
            print(f"[{label}] video came back as a URI/other shape: { {k: (str(v)[:120]) for k, v in vid.items()} }", flush=True); return
        print(f"[{label}] OK {time.time()-t0:.0f}s -> {dest} ({os.path.getsize(dest)} bytes) usage={d.get('usage')}", flush=True)
    except Exception as e:
        print(f"[{label}] ERROR {time.time()-t0:.0f}s: {type(e).__name__}: {str(e)[:500]}", flush=True)

JOBS = {
  "veo31_fast_control": lambda: fal_run("veo31_fast_control", "fal-ai/veo3.1/fast/image-to-video",
        {"prompt": PROMPT, "image_url": DATA_URI, "duration": "6s", "aspect_ratio": "16:9", "resolution": "720p", "generate_audio": False}),
  "kling30": lambda: fal_run("kling30", "fal-ai/kling-video/v3/standard/image-to-video",
        {"prompt": PROMPT, "start_image_url": DATA_URI, "duration": "5", "generate_audio": False}),
  "seedance20": lambda: fal_run("seedance20", "bytedance/seedance-2.0/image-to-video",
        {"prompt": PROMPT, "image_url": DATA_URI, "duration": "5", "resolution": "720p", "aspect_ratio": "16:9", "generate_audio": False}),
  "omni": omni,
}
only = sys.argv[1:] or list(JOBS)
ts = [threading.Thread(target=JOBS[k]) for k in only]
[t.start() for t in ts]; [t.join() for t in ts]
print("DONE", flush=True)
