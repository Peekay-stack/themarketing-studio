#!/usr/bin/env python
"""i2v_trial2.py -- round 2: MiniMax H3 Max, Wan 3.0 and Kling 4.0 image-to-video on the SAME frame and prompt as round 1.
Scratch script, not product code. Reads api/.env for FAL_KEY. Run from the api folder. Output: Downloads\\engine-trial\\i2v_<engine>.mp4
"""
import base64, os, sys, threading, time, urllib.request
API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
OUT = r"C:\Users\punie\Downloads\engine-trial"
sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import fal_client

DATA_URI = "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(OUT, "frame_first.jpg"), "rb").read()).decode()
PROMPT = ("Animate this frame. The mother keeps pouring the milk from the Heritage pouch into the steel vessel, the milk "
          "stream falling steadily; her head and hands move naturally. Camera: a slow, gentle handheld drift, shallow depth "
          "of field. Keep the pouch, its label and colours, her face, her saree and the kitchen exactly as in the image. "
          "No on-screen text, captions or subtitles.")

def run(label, endpoint, args):
    t0 = time.time()
    try:
        res = fal_client.subscribe(endpoint, arguments=args, with_logs=False)
        url = ((res.get("video") or {}).get("url")) if isinstance(res, dict) else None
        if not url:
            print(f"[{label}] NO VIDEO keys={list(res.keys()) if isinstance(res, dict) else res}", flush=True); return
        dest = os.path.join(OUT, f"i2v_{label}.mp4"); urllib.request.urlretrieve(url, dest)
        print(f"[{label}] OK {time.time()-t0:.0f}s -> {dest} ({os.path.getsize(dest)} bytes)", flush=True)
    except Exception as e:
        print(f"[{label}] ERROR {time.time()-t0:.0f}s: {type(e).__name__}: {str(e)[:600]}", flush=True)

JOBS = {
  "minimax_h3max": ("minimax/h3-max/image-to-video", {"prompt": PROMPT, "image_url": DATA_URI, "duration": 5, "resolution": "768P"}),
  "wan30": ("alibaba/wan-3.0/image-to-video", {"prompt": PROMPT, "start_image_url": DATA_URI, "duration": 5, "resolution": "720p", "aspect_ratio": "16:9", "audio": False}),
  "kling40": ("kling/v4/image-to-video", {"prompt": PROMPT, "start_image_url": DATA_URI, "duration": 5, "resolution": "720p"}),
}
only = sys.argv[1:] or list(JOBS)
ts = [threading.Thread(target=run, args=(k, *JOBS[k])) for k in only]
[t.start() for t in ts]; [t.join() for t in ts]
print("DONE", flush=True)
