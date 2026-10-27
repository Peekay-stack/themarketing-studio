#!/usr/bin/env python
"""test_packqa.py -- offline checks for api/packqa.py (the advisory pack-proportion measure) on synthetic images, so they
do not depend on any brand's files. No network, no credit.
Run:  api/.venv/Scripts/python.exe tools/test_packqa.py
"""
import base64, io, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api"))
from PIL import Image, ImageDraw
import packqa

def png(img):
    b = io.BytesIO(); img.save(b, "PNG"); return b.getvalue()

def pack_photo(w, h, colour=(230, 120, 40), canvas=(600, 600)):
    """A pack-like photo: a coloured panel w x h centred on a white background (the usual library photo)."""
    im = Image.new("RGB", canvas, (255, 255, 255)); d = ImageDraw.Draw(im)
    x0, y0 = (canvas[0] - w) // 2, (canvas[1] - h) // 2
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=colour); return png(im)

def frame(rect, colour=(230, 120, 40), size=(1280, 720), rotate=0, bg=(120, 110, 100)):
    im = Image.new("RGB", size, bg); d = ImageDraw.Draw(im); d.rectangle(rect, fill=colour)
    if rotate: im = im.rotate(rotate, fillcolor=bg)
    return png(im)

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

REF = pack_photo(300, 300)          # a square pack, ratio 1.0
r = packqa.check(frame((500, 200, 800, 500)), REF)
check("same proportions (square in a 16:9 frame) -> ok", r["verdict"] == "ok" and 0.9 <= r["ratio"] <= 1.1, str(r))
r = packqa.check(frame((470, 150, 830, 450)), REF)       # 360 x 300 = 1.2x
check("a 1.2x longer pack -> ok (inside the tolerance)", r["verdict"] == "ok", str(r))
r = packqa.check(frame((450, 150, 850, 450)), REF)       # 400 x 300 = 1.33x
check("a 1.33x longer pack -> elongated (past the 1.25 line)", r["verdict"] == "elongated", str(r))
r = packqa.check(frame((400, 250, 880, 450)), REF)       # 480 x 200 = 2.4x
check("a 2.4x longer pack -> elongated, with a sentence", r["verdict"] == "elongated" and "longer and thinner" in r["note"], str(r))
check("elongated ratio is about 2.4", 2.1 <= r["ratio"] <= 2.7, str(r["ratio"]))
REF_TALL = pack_photo(200, 400)                          # ratio 2.0
r = packqa.check(frame((500, 250, 800, 450)), REF_TALL)  # 300 x 200 = 1.5 -> 0.75x
check("a squarer pack than the real one -> squashed", r["verdict"] == "squashed" and "squarer" in r["note"], str(r))
r = packqa.check(frame((500, 200, 800, 500), rotate=25), REF)
check("a tilted pack of the right shape is not called stretched", r["verdict"] in ("ok", "unclear"), str(r))
r = packqa.check(frame((900, 100, 1275, 400)), REF)
check("a pack cut off by the frame edge -> unclear, never a verdict", r["verdict"] == "unclear" and "edge" in r["note"], str(r))
r = packqa.check(frame((500, 200, 800, 500), colour=(40, 90, 200)), REF)
check("no pack-coloured blob in the frame -> unclear", r["verdict"] == "unclear", str(r))
r = packqa.check(frame((500, 200, 506, 206)), REF)
check("a speck of the colour is too small to measure -> unclear", r["verdict"] == "unclear", str(r))
r = packqa.check(frame((500, 200, 800, 500)), pack_photo(300, 300, colour=(235, 235, 235)))
check("a white/grey pack photo has no colour to key on -> unclear", r["verdict"] == "unclear", str(r))
GREEN = (30, 150, 70)
r = packqa.check(frame((400, 250, 880, 450), colour=GREEN), pack_photo(300, 300, colour=GREEN))
check("works for another brand's colour (green), not just orange", r["verdict"] == "elongated", str(r))
RED = (210, 30, 40)
r = packqa.check(frame((500, 200, 800, 500), colour=RED), pack_photo(300, 300, colour=RED))
check("works for a red pack (hue wraps around 0)", r["verdict"] == "ok", str(r))
img = Image.open(io.BytesIO(pack_photo(300, 300)));
check("garbage bytes never raise", packqa.check(b"not an image", REF)["verdict"] == "unclear")
check("the reference photo is measured at its own aspect (a non-16:9 canvas is not stretched)",
      abs(packqa.measure(pack_photo(300, 300, canvas=(400, 900)), packqa.colour_profile(pack_photo(300, 300, canvas=(400, 900))))["aspect"] - 1.0) < 0.1)

# the helper in main: stubbed loaders, never raises, None when either image cannot be read
os.environ["GOOGLE_API_KEY"] = "k"
import main, gemini
b64 = lambda raw: ("image/png", base64.b64encode(raw).decode())
gemini._as_base64 = lambda src: b64(REF) if src == "REF" else (b64(frame((400, 250, 880, 450))) if src == "FRAME" else None)
r = main._pack_shape_check("FRAME", "REF")
check("main helper returns the verdict dict", isinstance(r, dict) and r.get("verdict") == "elongated", str(r))
check("main helper returns None when the frame cannot be loaded", main._pack_shape_check("MISSING", "REF") is None)
check("main helper returns None when the pack photo cannot be loaded", main._pack_shape_check("FRAME", "MISSING") is None)
gemini._as_base64 = lambda src: (_ for _ in ()).throw(RuntimeError("boom"))
check("main helper swallows an unexpected error", main._pack_shape_check("FRAME", "REF") is None)

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
