#!/usr/bin/env python
"""flow_trial_kling_elements.py -- TRIAL 2 of the "Flow / Higgsfield" research (28 Oct 2026): can Kling 3.0 on fal hold OUR cast across different shots from reference ELEMENTS (frontal image + tag @Element1)
-- Higgsfield's "Elements" / Flow's "Ingredients" -- with no storyboard frame to animate? Spends real credit; fal lists Kling 3.0 Pro with elements at a higher per-second rate than without, so clips are 3-4 s and
audio is off. Output: Downloads\\engine-trial\\flow_trials\\kling\\ (clips, the two reference crops, a contact sheet), and the endpoint's own error text if a call is refused.

  K1  text-to-video, elements [boy, mother]: both in one wide shot at the kitchen table
  K2  text-to-video, elements [mother]: a DIFFERENT composition (close-up of her hands and face at the table) -> same woman?
  K3  text-to-video, elements [boy]: a third composition (the boy from the side at the table) -> same boy?
Judged by eye against the reference crops; identity is the question, not beauty.
"""
import base64, io, json, os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import httpx, creative, imageio_ffmpeg, subprocess
from PIL import Image, ImageDraw
EXE = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(r"C:\Users\punie\Downloads\engine-trial", "flow_trials", "kling"); os.makedirs(OUT, exist_ok=True)
MEDIA = os.path.join(API, "tenants", "default", "media")
EP = sys.argv[1] if len(sys.argv) > 1 else "fal-ai/kling-video/v3/pro/text-to-video"


def crop(name, box, dest):
    im = Image.open(os.path.join(MEDIA, name)).convert("RGB"); w, h = im.size
    c = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    c.thumbnail((768, 768)); c.save(dest, quality=92); return dest


def data_uri(p): return "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()


BOY = crop("frame-3aa3378f04.jpg", (0.15, 0.0, 0.85, 1.0), os.path.join(OUT, "ref_boy.jpg"))          # the boy's face looking down, close
MOM = crop("frame-eb3b780b4f.jpg", (0.30, 0.0, 0.80, 0.90), os.path.join(OUT, "ref_mother.jpg"))      # the mother at the table
el_boy = {"frontal_image_url": data_uri(BOY)}
el_mom = {"frontal_image_url": data_uri(MOM)}

TRIALS = [
    ("K1_both", [el_boy, el_mom], "Wide shot of a warm sunlit Indian home kitchen in the morning, wooden table by a window. @Element1 is an eight year old boy sitting at the table drinking a glass of milk in slow gulps; "
     "@Element2 is his mother in a teal saree, standing beside him, watching him with a soft smile. Natural light, realistic, handheld feel.", 4),
    ("K2_mother_closeup", [el_mom], "Close-up of @Element2, a woman in a teal saree, seated at a wooden table in a warm sunlit kitchen, threading a needle and looking down at her work, then glancing up. Realistic, shallow depth of field.", 3),
    ("K3_boy_side", [el_boy], "Medium side view of @Element1, an eight year old boy in a cream t-shirt, sitting at a wooden kitchen table by a sunny window and putting down an empty glass, then looking at the camera. Realistic.", 3),
]
paths = {}
for name, elements, prompt, secs in TRIALS:
    args = {"prompt": prompt, "elements": elements, "duration": str(secs), "aspect_ratio": "16:9", "generate_audio": False}
    t0 = time.time()
    print(f"\n[{name}] {EP}  {secs}s  elements={len(elements)}", flush=True)
    url = creative.run_endpoint(EP, args)
    print(f"   -> {'OK ' + str(url)[:90] if url else 'NO VIDEO (see the fal error above)'}  ({time.time() - t0:.0f}s)", flush=True)
    if not url:
        continue
    p = os.path.join(OUT, name + ".mp4")
    r = httpx.get(url, timeout=180, follow_redirects=True); open(p, "wb").write(r.content); paths[name] = p
    print("   saved", p, len(r.content) // 1024, "KB")

# contact sheet: references, then 5 frames per clip
rows = [("REFERENCES given to Kling (boy, mother)", [BOY, MOM])]
for name, p in paths.items():
    fs = []
    for i in range(5):
        f = os.path.join(OUT, f"{name}_{i}.jpg"); subprocess.run([EXE, "-y", "-ss", f"{0.3 + i * 0.6:.2f}", "-i", p, "-frames:v", "1", "-vf", "scale=384:-1", f], capture_output=True); fs.append(f)
    rows.append((name, fs))
W, H = 384, 216
sh = Image.new("RGB", (5 * W, len(rows) * (H + 14)), "white"); dr = ImageDraw.Draw(sh)
for r, (lab, fs) in enumerate(rows):
    dr.text((3, r * (H + 14) + 1), lab, fill="black")
    for c, f in enumerate(fs):
        im = Image.open(f).convert("RGB"); im.thumbnail((W, H)); sh.paste(im, (c * W, r * (H + 14) + 14))
sh.save(os.path.join(OUT, "kling_sheet.jpg"), quality=85)
print("\nsheet ->", os.path.join(OUT, "kling_sheet.jpg"))
