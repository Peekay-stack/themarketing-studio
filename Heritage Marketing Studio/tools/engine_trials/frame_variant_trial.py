#!/usr/bin/env python
"""frame_variant_trial.py -- S1a question: do frame VARIANTS actually differ? The Shots step asks /scene-still for another frame of the same shot with its OWN seed (the film's fixed seed would repeat the
same picture). Does the image engine honour the seed? Renders the owner's re-directed scene-3 master three times (seed A, seed A again, seed B), then prints how different the pictures are
(mean absolute pixel difference on a 64x36 grey copy) and writes a contact sheet. Spends 3 image calls. Output: Downloads\\engine-trial\\flow_trials\\frame_variants\\
Run:  api/.venv/Scripts/python.exe tools/engine_trials/frame_variant_trial.py
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import numpy as np
from PIL import Image, ImageDraw
import main
main._record_made = lambda *a, **k: None
OUT = os.path.join(r"C:\Users\punie\Downloads\engine-trial", "flow_trials", "frame_variants"); os.makedirs(OUT, exist_ok=True)
plan = json.load(open(os.path.join(r"C:\Users\punie\Downloads\engine-trial", "heritage_redirect", "plan.json"), encoding="utf-8"))
row = plan["rows"][2]
body = {"scene_no": 3, "prompt": row["visual"] + " Camera: " + str(row.get("camera") or "") + ". Location: " + plan["location"], "ratio": "16:9", "style": "real", "engines": {"image": "google"}, "video_frame": True,
        "characters": plan["characters"], "use_cast": False, "use_plate": False, "brand_mode": "grounded", "reference_url": plan["cast"], "include_pack": False,
        "shot_size": row.get("shot_size") or ""}
runs = [("A (seed 111111)", 111111), ("A again (seed 111111)", 111111), ("B (seed 222222)", 222222)]
paths = []
for label, seed in runs:
    res = main.scene_still({**body, "seed": seed})
    if not isinstance(res, dict) or not res.get("image_url"):
        print(label, "FAILED", getattr(res, "body", res)); sys.exit(1)
    p = os.path.join(API, "tenants", "default", "media", os.path.basename(res["image_url"]))
    paths.append((label, p)); print(label, "->", os.path.basename(p), "provider", res.get("provider"))
def small(p): return np.asarray(Image.open(p).convert("L").resize((64, 36)), dtype="float32")
d = lambda a, b: float(np.abs(small(a) - small(b)).mean())
print(f"\nmean abs pixel difference (0-255): A vs A-again {d(paths[0][1], paths[1][1]):.1f} | A vs B {d(paths[0][1], paths[2][1]):.1f} | A-again vs B {d(paths[1][1], paths[2][1]):.1f}")
W, H = 460, 259
sh = Image.new("RGB", (3 * W, H + 16), "white"); dr = ImageDraw.Draw(sh)
for i, (label, p) in enumerate(paths):
    im = Image.open(p).convert("RGB"); im.thumbnail((W, H)); sh.paste(im, (i * W, 16)); dr.text((i * W + 4, 2), label, fill="black")
sh.save(os.path.join(OUT, "variants_sheet.jpg"), quality=88); print("sheet ->", os.path.join(OUT, "variants_sheet.jpg"))
