#!/usr/bin/env python
"""film_direct_real.py -- run the REAL director's read (one Claude call) on the owner's rejected 28 Oct film and compare the beat map with the answer key.

Answer key (VIDEO_CRAFT_FRAMEWORK.md section 11): scene 1 surprise (continuous); scenes 2+3 are ONE beat shown at two scales, a flashback, and the logline means time passing; scene 4
is the turn (the realisation as she lets the hem down); scene 5 the payoff; scene 6 the message carrier (the pack, "one glass at a time"). Nothing is saved.

Run:  api/.venv/Scripts/python.exe tools/engine_trials/film_direct_real.py [filmscript-id]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api"))
import main, filmdirect

fid = sys.argv[1] if len(sys.argv) > 1 else "063785d77c"
d = json.load(open(os.path.join("tenants", "default", "filmscripts", fid + ".json"), encoding="utf-8"))
rows = d["full_script"]; vc = d.get("video_concept") or {}
secs = []
for r in rows:
    a, _, b = str(r.get("tc") or "").replace("–", "-").replace("s", "").partition("-")
    try:
        secs.append(max(4, round(float(b) - float(a))))
    except ValueError:
        secs.append(4)
res = main.film_direct({"scenes": rows, "seconds": secs, "logline": vc.get("logline", ""), "message": vc.get("rationale", ""), "tone": " ".join(str(vc.get(k, "")) for k in ("name", "rationale", "logline"))[:300],
                        "characters": d.get("video_characters", ""), "hero": "the product pack", "film": True})
if not isinstance(res, dict):
    print("ERROR", res.status_code, res.body[:400]); sys.exit(1)
print("SUMMARY:", res["summary"])
print("turn", res["turn_scene"], "| carrier", res["carrier_scene"], "| time passing", res["time_passing"], "| hero", res["hero_object"])
for s in res["scenes"]:
    print(f"  scene {s['no']} [{s['beat']}] {s['time_mode']:13} intensity {s['intensity']}  {s['purpose']}" + (f"  (marker: {s['marker']})" if s["marker"] else "") + ("  [hero]" if s["hero"] else ""))
print("TRANSITIONS:", [(t["from"], t["to"], t["to_mode"], "marked" if t["marked"] else "UNMARKED") for t in res["transitions"]])
for f in res["findings"]:
    print("  finding:", f["note"])
for n in res["notes"]:
    print("  (system)", n)
print("NO-COVERAGE RULES:", filmdirect.no_coverage(res))
