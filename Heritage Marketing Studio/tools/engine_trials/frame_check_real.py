#!/usr/bin/env python
"""frame_check_real.py -- run the REAL frame check (one vision call per frame) on the frames of the owner's rejected 28 Oct film and print what it says beside the answer key.

Answer key (the owner's five pictures + the contact sheet): scene 5's master (frame key 4) is a collage of the cast sheet pasted beside a giant pair of legs -> must be flagged;
scene 1's low detail (frame 0.1) is a foot / leg shot with a doubtful body -> a body check is expected to look hard at it; the others are clean master and coverage frames -> should pass.
Nothing is saved: the route only advises. Tokens are printed so the cost can be priced from the model's own published rates.

Run:  api/.venv/Scripts/python.exe tools/engine_trials/frame_check_real.py [filmscript-id]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api"))
import main, framecheck

fid = sys.argv[1] if len(sys.argv) > 1 else "063785d77c"
d = json.load(open(os.path.join("tenants", "default", "filmscripts", fid + ".json"), encoding="utf-8"))
rows = d["full_script"]; frames = d["scene_frames"]
cast = d.get("video_characters", ""); ward = d.get("video_wardrobe", "")
print(f"model {framecheck.model_name()} | {len(frames)} frames | cast note {len(cast)} chars")
tot_in = tot_out = 0
KEY = {"4": "collage", "0.1": "anatomy?"}
for key in sorted(frames, key=lambda k: [int(x) for x in k.split(".")]):
    f = frames[key]
    if f.get("status") != "done":
        continue
    i, _, k = key.partition(".")
    row = rows[int(i)]
    desc = (row.get("shots") or [])[int(k) - 1].get("visual", "") if k else (row.get("visual") or "")
    res = main.frame_check({"frame_url": f["url"], "description": desc, "cast": cast, "wardrobe": ward, "pack_expected": "pack" in desc.lower() or "pouch" in desc.lower()})
    if not isinstance(res, dict):
        print(key, "ERROR", res.status_code, res.body[:200]); continue
    u = res["usage"]; tot_in += u["input_tokens"]; tot_out += u["output_tokens"]
    print(f"\n[{key}] {res['verdict'].upper():5} (key says: {KEY.get(key, 'clean')})  tokens in/out {u['input_tokens']}/{u['output_tokens']}")
    print("   sees:", res["seen"])
    for c in res["checks"]:
        print(f"   - {c['label']}: {c['note']}")
print(f"\nTOTAL tokens in {tot_in} / out {tot_out} over {len(frames)} frames")
