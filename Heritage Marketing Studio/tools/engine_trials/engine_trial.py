#!/usr/bin/env python
"""engine_trial.py -- T1: does a reference-driven video engine hold the REAL Heritage pack, the cast and the location?

Two clips, same scene, same three references (the real pack photo + a mother frame + a boy-in-kitchen frame from the
owner's 30s film). 5 s, 720p, audio off. Output goes to Downloads\\engine-trial. Not part of the product; reads api/.env
only for FAL_KEY. Run from the api folder so the project's own helpers import.
"""
import base64, os, sys, threading, time, json, urllib.request

API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
OUT = r"C:\Users\punie\Downloads\engine-trial"
sys.path.insert(0, API)
os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import fal_client

def data_uri(name, mime):
    with open(os.path.join(OUT, name), "rb") as fh:
        return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()

PACK = data_uri("ref1_pack.png", "image/png")
MOTHER = data_uri("ref2_mother.jpg", "image/jpeg")
BOY = data_uri("ref3_boy_kitchen.jpg", "image/jpeg")

SCENE = ("Medium shot, handheld by a real operator with a gentle breathing sway, shallow depth of field, warm morning "
         "window light, natural film grain. The mother holds the milk pouch and pours milk from its torn corner into a "
         "steel vessel on the kitchen counter while her young son stands beside her, watching and smiling. "
         "No on-screen text, captions or subtitles.")

RUNS = {
    "seedance2": ("bytedance/seedance-2.0/reference-to-video", {
        "prompt": ("@Image1 is the EXACT milk pouch: keep its shape, orange colour, green Heritage logo and the words "
                   "'Happy Full Cream Milk' exactly as shown, front-facing, never redrawn or re-lettered. "
                   "@Image2 is the mother: keep her face, hair and saree. @Image3 is the boy and the kitchen: keep "
                   "the boy's face and the kitchen. " + SCENE),
        "image_urls": [PACK, MOTHER, BOY],
        "duration": "5", "resolution": "720p", "aspect_ratio": "16:9", "generate_audio": False}),
    "kling_o1": ("fal-ai/kling-video/o1/reference-to-video", {
        "prompt": ("@Element1 is the EXACT milk pouch: keep its shape, orange colour, green Heritage logo and the words "
                   "'Happy Full Cream Milk' exactly as shown, front-facing, never redrawn or re-lettered. "
                   "@Element2 is the mother: keep her face, hair and saree. @Image1 is the boy and the kitchen: keep "
                   "the boy's face and the kitchen. " + SCENE),
        "elements": [{"frontal_image_url": PACK, "reference_image_urls": [PACK]},
                     {"frontal_image_url": MOTHER, "reference_image_urls": [MOTHER]}],
        "image_urls": [BOY],
        "duration": "5", "aspect_ratio": "16:9"}),
}

def run(label):
    ep, args = RUNS[label]
    t0 = time.time()
    try:
        res = fal_client.subscribe(ep, arguments=args, with_logs=False)
        vid = (res.get("video") or {}) if isinstance(res, dict) else {}
        url = vid.get("url")
        if not url:
            print(f"[{label}] NO VIDEO. keys={list(res.keys()) if isinstance(res, dict) else res}", flush=True); return
        dest = os.path.join(OUT, f"trial_{label}.mp4")
        urllib.request.urlretrieve(url, dest)
        print(f"[{label}] OK in {time.time()-t0:.0f}s -> {dest} ({os.path.getsize(dest)} bytes) seed={res.get('seed')}", flush=True)
    except Exception as e:
        print(f"[{label}] ERROR after {time.time()-t0:.0f}s: {type(e).__name__}: {str(e)[:600]}", flush=True)

only = sys.argv[1:] or list(RUNS)
ts = [threading.Thread(target=run, args=(k,)) for k in only]
[t.start() for t in ts]; [t.join() for t in ts]
print("DONE", flush=True)
