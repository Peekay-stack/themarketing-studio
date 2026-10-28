#!/usr/bin/env python
"""flow_trial_omni_cost.py -- TRIAL 1b: what does an Omni EXTEND cost, and how does it compare with the chain we use today? (28 Oct 2026; spends about 12 s of 360p Draft output)
Runs clip 1 (4 s), then (a) EXTENDS it by 4 s via previous_interaction_id, and (b) the control: animates the LAST FRAME of clip 1 with the same continuation prompt. Prints each response's usage block, so the
cost of an extension (the new part only, or the whole video re-billed?) is read from the API's own token counts and compared with clip 1's (7,724 output tokens for 4.0 s on 28 Oct = about 1,930 tokens per second).
"""
import base64, json, os, re, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import httpx, gemini, imageio_ffmpeg
EXE = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(r"C:\Users\punie\Downloads\engine-trial", "flow_trials", "omni", "cost"); os.makedirs(OUT, exist_ok=True)
FRAME = os.path.join(API, "tenants", "default", "media", "frame-eb3b780b4f.jpg")


def call(name, blocks, prev=None):
    body = {"model": gemini.OMNI_MODEL, "input": blocks, "response_format": {"type": "video", "aspect_ratio": "16:9", "resolution": "360p"}}
    if prev: body["previous_interaction_id"] = prev
    gemini._omni_slot(); t0 = time.time()
    r = httpx.post(gemini.INTERACTIONS, headers=gemini._headers(), json=body, timeout=600)
    print(f"\n[{name}] HTTP {r.status_code} in {time.time() - t0:.0f}s", flush=True)
    if r.status_code >= 400: print("  error:", r.text[:300]); return None, None, None
    data = r.json(); vid = gemini._video_bytes(data)
    path = os.path.join(OUT, name + ".mp4"); open(path, "wb").write(vid)
    info = subprocess.run([EXE, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info); dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    u = data.get("usage") or {}
    print(f"  video {dur:.2f} s | usage: input {u.get('total_input_tokens')} (by modality {u.get('input_tokens_by_modality')}), output {u.get('total_output_tokens')} {u.get('output_tokens_by_modality')}, thought {u.get('total_thought_tokens')}, total {u.get('total_tokens')}")
    return data.get("id"), path, dur


ref = gemini._as_base64(FRAME)
P1 = ("Animate this frame as one continuous four-second shot, no cuts. ACTION: the woman keeps sewing, drawing the needle and thread through the grey cloth with her right hand, her eyes on the work. CAMERA: static. "
      "KEEP IDENTICAL TO THE IMAGE: her face, her teal saree with cream border, the grey cloth, the kitchen, the warm window light. No on-screen text. About 4 seconds.")
P2 = "she pulls the thread tight, lifts her eyes from the cloth and looks up with a quiet smile. Same kitchen, same light, same camera. About 4 seconds."
id1, v1, d1 = call("A1_clip1", [{"type": "image", "data": ref[1], "mime_type": ref[0]}, {"type": "text", "text": P1}])
id2, v2, d2 = call("A2_extend", [{"type": "text", "text": "Continue the same shot without a cut: " + P2}], prev=id1)
lf = os.path.join(OUT, "A1_last.jpg")
subprocess.run([EXE, "-y", "-ss", f"{d1 - 0.12:.2f}", "-i", v1, "-frames:v", "1", lf], capture_output=True)
lr = ("image/jpeg", base64.b64encode(open(lf, "rb").read()).decode())
id3, v3, d3 = call("A3_control_lastframe", [{"type": "image", "data": lr[1], "mime_type": lr[0]}, {"type": "text", "text": "Animate this frame as one continuous four-second shot: " + P2}])

from PIL import Image, ImageDraw
rows = []
for tag, p in (("A2 extension of A1 (new part = from 4 s)", v2), ("A3 control: last frame of A1, animated", v3)):
    if not p: continue
    info = subprocess.run([EXE, "-i", p], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info); dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    fs = []
    for t in ([3.2, 3.9, 4.1, 4.8, 6.0, 7.5] if "A2" in tag else [0.1, 0.6, 1.2, 2.0, 3.0, 3.8]):
        f = os.path.join(OUT, f"{tag[:2]}_{t}.jpg"); subprocess.run([EXE, "-y", "-ss", str(min(t, dur - 0.1)), "-i", p, "-frames:v", "1", "-vf", "scale=320:-1", f], capture_output=True); fs.append(f)
    rows.append((tag, fs))
sh = Image.new("RGB", (6 * 320, len(rows) * 194), "white"); dr = ImageDraw.Draw(sh)
for r, (tag, fs) in enumerate(rows):
    dr.text((3, r * 194 + 1), tag, fill="black")
    for c, f in enumerate(fs):
        im = Image.open(f).convert("RGB"); im.thumbnail((320, 180)); sh.paste(im, (c * 320, r * 194 + 14))
sh.save(os.path.join(OUT, "cost_sheet.jpg"), quality=85)
print("\nsheet ->", os.path.join(OUT, "cost_sheet.jpg"))
