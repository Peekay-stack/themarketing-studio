#!/usr/bin/env python
"""shot_render_real.py -- S1b check on the owner's re-directed Heritage film:
  1. FREE: the prompt, frame and seconds a single-shot render (`only_shot`) sends to the engine are IDENTICAL to what the full render sends for the same shot (generators stubbed, the real planner).
  2. REAL (about one Draft clip, 360p, $0.034 per output second measured): render that one shot for real through `only_shot`, report the clip record and play-test it (frame fingerprints, duration).
Run:  api/.venv/Scripts/python.exe tools/engine_trials/shot_render_real.py [shot key, default 2 = scene 3's master]
"""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import main, gemini, filmcut, filmvoice, imageio_ffmpeg
main._record_made = lambda *a, **k: None
KEY = sys.argv[1] if len(sys.argv) > 1 else "2"
plan = json.load(open(os.path.join(r"C:\Users\punie\Downloads\engine-trial", "heritage_redirect", "plan.json"), encoding="utf-8"))
rows = [dict(r) for r in plan["rows"]]
for i, r in enumerate(rows):
    if plan["frames"].get(str(i)): r["frame_url"] = plan["frames"][str(i)]
payload = {"scenes": rows, "aspect": "16:9", "duration": "30s", "engines": {"video": "google", "music": "google"}, "tier": "lite", "style": "real", "characters": plan["characters"], "brand_mode": "grounded",
           "script": {"logline": plan["common"]["logline"]}}

# ---- 1. free equivalence ----------------------------------------------------------------------------------------------------------------
seen = []
real_video = gemini.video
gemini.video = lambda prompt, **kw: (seen.append({"prompt": prompt, "image_ref": kw.get("image_ref"), "seconds": kw.get("seconds"), "tier": kw.get("tier")}), "/media/stub.mp4")[1]
filmcut.stitch = lambda urls, lengths=None: None
filmvoice.synth = lambda segs, *a, **k: (0, [])
main._music_bed = lambda *a, **k: ("", "")
full = main._produce_video_sync(dict(payload))
full_calls = list(seen); seen.clear()
one = main._produce_video_sync({**dict(payload), "only_shot": KEY})
only_calls = list(seen)
mine = [c for c in full_calls if c["image_ref"] == plan["frames"].get(str(int(KEY.split(".")[0])))] if "." not in KEY else []
print(f"full render made {len(full_calls)} engine calls; only_shot {KEY} made {len(only_calls)}")
same = bool(only_calls) and [json.dumps(c, sort_keys=True) for c in only_calls] == [json.dumps(c, sort_keys=True) for c in mine]
print("IDENTICAL prompt / frame / seconds / tier to the full render's call(s) for that shot:", same)
if not same:
    print(" only_shot:", only_calls); print(" full     :", mine); sys.exit(1)
print("record:", json.dumps({k: one[k] for k in ("shot", "ok", "tier", "model")}), "clips:", [(c["beat"], c["seconds"], c["ok"]) for c in one["clips"]])

# ---- 2. one real Draft clip -------------------------------------------------------------------------------------------------------------
gemini.video = real_video
res = main._produce_video_sync({**dict(payload), "only_shot": KEY})
print("\nREAL:", json.dumps({k: res.get(k) for k in ("shot", "ok", "tier", "model", "errors")}, ensure_ascii=False))
for c in res["clips"]:
    print("  beat", c["beat"], c["seconds"], "s", "ok" if c["ok"] else "FAILED", c["url"], c["provider"], "from_frame", c["from_frame"])
    if c["ok"]:
        p = os.path.join(API, "tenants", "default", "media", os.path.basename(c["url"]))
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        info = subprocess.run([exe, "-i", p], capture_output=True, text=True).stderr
        import re, hashlib
        print("   ", re.findall(r"Duration: [\d:.]+", info), os.path.getsize(p) // 1024, "KB")
        hs = []
        for t in (0.3, 1.2, 2.2, 3.2):
            r = subprocess.run([exe, "-y", "-ss", str(t), "-i", p, "-frames:v", "1", "-vf", "scale=64:36,format=gray", "-f", "rawvideo", "-"], capture_output=True)
            hs.append(hashlib.md5(r.stdout).hexdigest()[:5])
        print("    frame fingerprints (all different = it moves):", hs, "MOVES" if len(set(hs)) == len(hs) else "CHECK: some frames repeat")
