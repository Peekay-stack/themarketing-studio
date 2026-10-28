#!/usr/bin/env python
"""flow_trial_omni_extend.py -- TRIAL 1 of the "Flow / Higgsfield" research (29 Oct 2026): can Gemini Omni EXTEND a clip (previous_interaction_id) the way Flow's Extend / Jump to do, and is it better
than our current chain (animate the last frame of clip 1)?  Spends real credit at 360p Draft (about $0.034 per output second, measured 27 Oct). Output: Downloads\\engine-trial\\flow_trials\\omni\\

  O1  clip 1 from a storyboard frame (the boy drinking), 4 s, stored (store=true is the default)
  O2  EXTEND O1 with previous_interaction_id: "continue the same shot" -> what comes back (the whole video or only the new part), its length, continuity at the seam
  O3  EXTEND O2 with a JUMP: "cut to a close-up of the mother watching" -> does an extension accept a cut to a different subject (Flow's Jump to)
  O4  CONTROL: the chain we use today: take the LAST frame of O1 and animate it with the same continuation prompt
Prints sizes, durations, response keys (never the data) and any usage block, so the cost per second is measured, not guessed.
"""
import base64, json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import httpx, gemini, imageio_ffmpeg
EXE = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(r"C:\Users\punie\Downloads\engine-trial", "flow_trials", "omni"); os.makedirs(OUT, exist_ok=True)
SUBJECT = sys.argv[1] if len(sys.argv) > 1 else "mother"
FRAME = os.path.join(API, "tenants", "default", "media", {"boy": "frame-878e75114f.jpg", "mother": "frame-eb3b780b4f.jpg"}[SUBJECT])      # the re-directed film's frames: boy drinking / the mother sewing
OUT = os.path.join(OUT, SUBJECT); os.makedirs(OUT, exist_ok=True)
RES = "360p"


def strip(obj, depth=0):
    """The response shape with all bulk (base64) removed, so it can be printed."""
    if isinstance(obj, dict): return {k: strip(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, list): return [strip(v, depth + 1) for v in obj[:6]]
    if isinstance(obj, str) and len(obj) > 120: return f"<str {len(obj)} chars>"
    return obj


def call(name, blocks, prev=None, store=True):
    body = {"model": gemini.OMNI_MODEL, "input": blocks, "response_format": {"type": "video", "aspect_ratio": "16:9", "resolution": RES}}
    if prev: body["previous_interaction_id"] = prev
    if store is False: body["store"] = False
    gemini._omni_slot()
    t0 = time.time()
    r = httpx.post(gemini.INTERACTIONS, headers=gemini._headers(), json=body, timeout=600)
    took = time.time() - t0
    print(f"\n[{name}] HTTP {r.status_code} in {took:.0f}s", flush=True)
    if r.status_code >= 400:
        print("   error:", r.text[:600]); return None, None
    data = r.json()
    inter = data.get("interaction") if isinstance(data.get("interaction"), dict) else data
    iid = inter.get("id") or data.get("id")
    print("   id:", iid, "| response shape:", json.dumps(strip(data))[:900])
    vid = gemini._video_bytes(data)
    if not vid: print("   NO VIDEO in response"); return iid, None
    path = os.path.join(OUT, f"{name}.mp4"); open(path, "wb").write(vid)
    info = subprocess.run([EXE, "-i", path], capture_output=True, text=True).stderr
    import re
    print("   saved", path, len(vid) // 1024, "KB", re.findall(r"Duration: [\d:.]+", info), re.findall(r"(\d+x\d+)", info)[:1])
    return iid, path


def last_frame(path, dest):
    import re
    info = subprocess.run([EXE, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info); dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    subprocess.run([EXE, "-y", "-ss", f"{max(0.0, dur - 0.12):.2f}", "-i", path, "-frames:v", "1", dest], capture_output=True)
    return dest


def sheet(paths, dest, labels):
    from PIL import Image, ImageDraw
    W, H = 320, 180
    sh = Image.new("RGB", (len(paths[0]) * W, len(paths) * (H + 14)), "white"); dr = ImageDraw.Draw(sh)
    for r, (row, lab) in enumerate(zip(paths, labels)):
        dr.text((3, r * (H + 14) + 1), lab, fill="black")
        for c, p in enumerate(row):
            im = Image.open(p).convert("RGB"); im.thumbnail((W, H)); sh.paste(im, (c * W, r * (H + 14) + 14))
    sh.save(dest, quality=85)


def frames(path, tag, n=6):
    """n frames evenly across a clip."""
    info = subprocess.run([EXE, "-i", path], capture_output=True, text=True).stderr
    import re
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info); dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    out = []
    for i in range(n):
        p = os.path.join(OUT, f"{tag}_{i}.jpg"); subprocess.run([EXE, "-y", "-ss", f"{dur * (i + 0.5) / n:.2f}", "-i", path, "-frames:v", "1", "-vf", "scale=320:-1", p], capture_output=True); out.append(p)
    return out, dur


ref = gemini._as_base64(FRAME)
img = {"type": "image", "data": ref[1], "mime_type": ref[0]}
P1_BOY = ("Animate this frame as one continuous four-second shot, no cuts. ACTION: the boy keeps drinking the glass of milk in slow gulps, then lowers the glass a little. CAMERA: static, shallow depth of field. "
      "KEEP IDENTICAL TO THE IMAGE: the boy's face, his cream t-shirt, the kitchen, the warm window light. No on-screen text. About 4 seconds.")
P2_BOY = "Continue the same shot without a cut: the boy sets the glass down on the table and looks up. Same kitchen, same light, same camera. About 4 seconds."
P3_BOY = "Cut to a close-up of the boy's mother, standing in the kitchen doorway behind him, watching him with a soft smile. Same warm morning light. About 3 seconds."
P1_MOTHER = ("Animate this frame as one continuous four-second shot, no cuts. ACTION: the woman keeps sewing, drawing the needle and thread through the grey cloth with her right hand, her eyes on the work. CAMERA: static, shallow depth of field. "
             "KEEP IDENTICAL TO THE IMAGE: her face, her teal saree with cream border, the grey cloth, the kitchen, the warm window light. No on-screen text. About 4 seconds.")
P2_MOTHER = "Continue the same shot without a cut: she pulls the thread tight, lifts her eyes from the cloth and looks up with a quiet smile. Same kitchen, same light, same camera. About 4 seconds."
P3_MOTHER = "Cut to a close-up of the grey school trousers laid on the wooden table, her hand smoothing the new hem flat. Same warm morning light. About 3 seconds."
P1, P2, P3 = (P1_BOY, P2_BOY, P3_BOY) if SUBJECT == "boy" else (P1_MOTHER, P2_MOTHER, P3_MOTHER)

id1, v1 = call("O1_clip1", [img, {"type": "text", "text": P1}])
if not v1: sys.exit("O1 failed")
id2, v2 = call("O2_extend", [{"type": "text", "text": P2}], prev=id1) if id1 else (None, None)
id3, v3 = call("O3_jump", [{"type": "text", "text": P3}], prev=id2) if id2 else (None, None)
lf = last_frame(v1, os.path.join(OUT, "O1_last.jpg"))
lref = gemini._as_base64(lf)
id4, v4 = call("O4_control_lastframe", [{"type": "image", "data": lref[1], "mime_type": lref[0]}, {"type": "text", "text": P2.replace("Continue the same shot without a cut: ", "Animate this frame as one continuous four-second shot: ")}]) if lref else (None, None)

rows, labels, durs = [], [], {}
for tag, p, lab in (("O1", v1, "O1 clip 1 (4 s asked)"), ("O2", v2, "O2 EXTEND of O1 (what comes back)"), ("O3", v3, "O3 JUMP: cut to the mother"), ("O4", v4, "O4 control: last frame of O1 animated")):
    if p:
        fs, d = frames(p, tag, 6); rows.append(fs); labels.append(f"{lab}  [{d:.1f} s]"); durs[tag] = round(d, 2)
sheet(rows, os.path.join(OUT, "omni_sheet.jpg"), labels)
json.dump({"ids": [id1, id2, id3, id4], "durations": durs}, open(os.path.join(OUT, "run.json"), "w"), indent=1)
print("\nDURATIONS:", durs, "\nsheet ->", os.path.join(OUT, "omni_sheet.jpg"))
