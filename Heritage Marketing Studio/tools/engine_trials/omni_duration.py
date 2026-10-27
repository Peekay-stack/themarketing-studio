#!/usr/bin/env python
"""omni_duration.py -- does 'About N seconds.' steer Omni's clip length for the beats the studio uses (4, 6, 8)?
Scratch script; spends real credit (360p drafts, ~0.034 USD/s). Fires 4/6/8 s requests on one frame, prints the actual
clip length (ffprobe via imageio_ffmpeg) and the token count. Output: Downloads\\engine-trial\\step2\\dur_<N>.mp4"""
import base64, json, os, re, subprocess, sys, threading, time
API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
D = r"C:\Users\punie\Downloads\engine-trial"; S = os.path.join(D, "step2"); os.makedirs(S, exist_ok=True)
sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import httpx, imageio_ffmpeg
KEY = os.environ["GOOGLE_API_KEY"].strip(); exe = imageio_ffmpeg.get_ffmpeg_exe()
FRAME = os.path.join(D, "step1", "frame_s6.jpg")
BASE = ("Animate this frame as one continuous shot, no cuts. ACTION: the boy raises the steel glass to his lips with both hands, "
        "drinks, then lowers it. CAMERA: a slow gentle handheld push-in. KEEP IDENTICAL TO THE IMAGE: faces, outfits, pack, kitchen. "
        "Audio: quiet room sound only, no speech, no music. No on-screen text. ")
def run(n, phrase, out):
    t0 = time.time()
    body = {"model": "gemini-omni-1.1-flash",
            "input": [{"type": "image", "data": base64.b64encode(open(FRAME, "rb").read()).decode(), "mime_type": "image/jpeg"},
                      {"type": "text", "text": BASE + phrase}],
            "response_format": {"type": "video", "aspect_ratio": "16:9", "resolution": "360p"}}
    r = httpx.post("https://generativelanguage.googleapis.com/v1beta/interactions", params={"key": KEY}, json=body, timeout=900)
    if r.status_code >= 400: out[n] = f"HTTP {r.status_code} {r.text[:160]}"; return
    d = r.json(); vid = None
    for st in d.get("steps", []):
        for c in st.get("content", []) or []:
            if c.get("type") == "video": vid = c
    if not vid or not vid.get("data"): out[n] = "no inline video"; return
    p = os.path.join(S, f"dur_{n}.mp4"); open(p, "wb").write(base64.b64decode(vid["data"]))
    err = subprocess.run([exe, "-i", p], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err); secs = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3)) if m else -1
    out[n] = f"asked {n} -> got {secs:.2f}s in {time.time()-t0:.0f}s"
if __name__ == "__main__":
    jobs = {"4": "About 4 seconds.", "6": "About 6 seconds.", "8": "About 8 seconds.", "8b": "Exactly 8 seconds long.", "3": "About 3 seconds."}
    out = {}; ts = [threading.Thread(target=run, args=(n, ph, out)) for n, ph in jobs.items()]
    [t.start() for t in ts]; [t.join() for t in ts]
    for n in jobs: print(n, "|", out.get(n))
