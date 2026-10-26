#!/usr/bin/env python
"""analyze_i2v.py -- measure and package the image-to-video comparison.

For every clip: probe it, sample frames, isolate the orange pouch by colour, score how well the pouch's colour and size
hold against the START frame, crop the pouch for a close-up strip, and re-encode a web copy. Output goes to
scratchpad\\video_compare\\ (clips\\, img\\, metrics.json). Usage: analyze_i2v.py A|B
"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image
import imageio_ffmpeg
import scipy.ndimage as ndi

D = r"C:\Users\punie\Downloads\engine-trial"
SC = r"C:\Users\punie\AppData\Local\Temp\claude\C--Users-punie-Heritage-Marketing-Studio-OPUS\fcd137c0-c85a-447d-9d35-c10659cecac7\scratchpad"
OUT = os.path.join(SC, "video_compare"); os.makedirs(os.path.join(OUT, "clips"), exist_ok=True); os.makedirs(os.path.join(OUT, "img"), exist_ok=True)
exe = imageio_ffmpeg.get_ffmpeg_exe()
scene = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
START = {"A": "frame_first.jpg", "B": "cand_B_28.5.jpg"}[scene]
PREFIX = {"A": "i2v_", "B": "i2v_B_"}[scene]
ENGINES = ["veo31_fast_control", "kling30", "kling40", "omni", "minimax_h3max", "wan30", "seedance20"]
SAMPLES = [0.5, 1.5, 2.5, 3.5, 4.5]

def orange(a):
    a = a.astype(np.float32); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = np.maximum(mx - mn, 1e-6); v = mx / 255.0
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return (h >= 14) & (h <= 32) & (s > 0.62) & (v > 0.62)

def pouch(img):
    """(mean RGB, area, bbox) of the largest orange blob, or None."""
    a = np.asarray(img.convert("RGB").resize((1280, 720)))
    m = ndi.binary_closing(orange(a), iterations=3)
    lab, n = ndi.label(m)
    if n == 0: return None
    sizes = ndi.sum(m, lab, range(1, n + 1)); k = int(np.argmax(sizes)) + 1
    mk = lab == k; ys, xs = np.where(mk)
    return a[mk].mean(0), int(mk.sum()), (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), a

def probe(path):
    t = subprocess.run([exe, "-i", path], capture_output=True, text=True).stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", t); secs = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))
    v = re.search(r"Video: .*?, (\d+)x(\d+)", t); fps = re.search(r"(\d+(?:\.\d+)?) fps", t)
    return {"seconds": round(secs, 2), "size": f"{v.group(1)}x{v.group(2)}" if v else "?", "fps": float(fps.group(1)) if fps else None,
            "audio": "Audio:" in t, "mb": round(os.path.getsize(path) / 1e6, 2)}

def frame_at(path, t):
    out = os.path.join(SC, "_tmp_frame.png")
    subprocess.run([exe, "-y", "-ss", str(t), "-i", path, "-frames:v", "1", out], capture_output=True)
    return Image.open(out).convert("RGB") if os.path.exists(out) else None

start = Image.open(os.path.join(D, START)); sp = pouch(start)
s_rgb, s_area = sp[0], sp[1]
print(f"scene {scene}: start pouch mean RGB {s_rgb.round(0)} area {s_area}")
res = {"scene": scene, "start_rgb": [round(float(x), 1) for x in s_rgb], "start_area": s_area, "engines": {}}
for e in ENGINES:
    p = os.path.join(D, f"{PREFIX}{e}.mp4")
    if not os.path.exists(p): print("missing", e); continue
    info = probe(p); rows, crops, diffs, prev = [], [], [], None
    for t in [x for x in SAMPLES if x < info["seconds"] - 0.1]:
        fr = frame_at(p, t)
        if fr is None: continue
        g = np.asarray(fr.convert("L").resize((160, 90))).astype(np.float32)
        if prev is not None: diffs.append(float(np.abs(g - prev).mean()))
        prev = g
        q = pouch(fr)
        if q is None: rows.append({"t": t, "found": False}); continue
        rgb, area, bb, arr = q
        rows.append({"t": t, "found": True, "color_dist": float(np.linalg.norm(rgb - s_rgb)), "area_ratio": area / s_area})
        x0, y0, x1, y1 = bb; mw, mh = int((x1 - x0) * .2), int((y1 - y0) * .2)
        crop = Image.fromarray(arr[max(0, y0 - mh):y1 + mh, max(0, x0 - mw):x1 + mw]); crops.append(crop.resize((int(crop.width * 260 / crop.height), 260)))
    ok = [r for r in rows if r.get("found")]
    info.update({"samples": len(rows), "pouch_found": f"{len(ok)}/{len(rows)}",
                 "color_dist": round(float(np.mean([r["color_dist"] for r in ok])), 1) if ok else None,
                 "area_ratio": round(float(np.mean([r["area_ratio"] for r in ok])), 2) if ok else None,
                 "area_cv": round(float(np.std([r["area_ratio"] for r in ok]) / max(np.mean([r["area_ratio"] for r in ok]), 1e-6)), 2) if len(ok) > 1 else None,
                 "motion": round(float(np.mean(diffs)), 2) if diffs else None})
    if crops:                                                    # close-up strip of the pouch across the clip
        W = sum(c.width for c in crops) + 6 * (len(crops) - 1); strip = Image.new("RGB", (W, 260), "white"); x = 0
        for c in crops: strip.paste(c, (x, 0)); x += c.width + 6
        strip.save(os.path.join(OUT, "img", f"pouch_{scene}_{e}.jpg"), quality=88)
    web = os.path.join(OUT, "clips", f"{scene}_{e}.mp4")           # web copy: 720p, no audio, small
    subprocess.run([exe, "-y", "-i", p, "-an", "-vf", "scale=1280:-2", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", web], capture_output=True)
    info["web_mb"] = round(os.path.getsize(web) / 1e6, 2) if os.path.exists(web) else None
    res["engines"][e] = info
    print(f"{e:20s} {info['seconds']}s {info['size']:>9s} audio={info['audio']!s:5s} pouch={info['pouch_found']} "
          f"colourΔ={info['color_dist']} size×={info['area_ratio']} cv={info['area_cv']} motion={info['motion']} web={info['web_mb']}MB")
start.convert("RGB").save(os.path.join(OUT, "img", f"start_{scene}.jpg"), quality=90)
json.dump(res, open(os.path.join(OUT, f"metrics_{scene}.json"), "w"), indent=1)
print("saved metrics")
