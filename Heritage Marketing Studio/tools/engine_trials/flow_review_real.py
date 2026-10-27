#!/usr/bin/env python
"""flow_review_real.py -- run the REAL flow review (one Claude call) on the owner's rejected 28 Oct film and compare it with the answer key.

The film is read from the local dev tenant (api/tenants/default/filmscripts/<id>.json, not committed). Nothing is saved: the route only advises.
Answer key (VIDEO_CRAFT_FRAMEWORK.md section 11 and the owner's critique): scenes 2-3 are one beat shown twice (and the logline means time passing), the scene-5
shoulder shot adds nothing, a film this tender should not be cut every 2 s; it should land near 9 shots. Not every owner complaint is visible to a text review
(a hem with two legs of different length, a master frame that is a collage of a character sheet): those are the Frame check (slice 3).

Run:  api/.venv/Scripts/python.exe tools/engine_trials/flow_review_real.py [filmscript-id] [pace]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api"))
import main, flowreview, sceneshots

fid = sys.argv[1] if len(sys.argv) > 1 else "063785d77c"
pace = sys.argv[2] if len(sys.argv) > 2 else "calm"
d = json.load(open(os.path.join("tenants", "default", "filmscripts", fid + ".json"), encoding="utf-8"))
rows = d["full_script"]
vc = d.get("video_concept") or {}
secs = []
for r in rows:
    a, _, b = str(r.get("tc") or "").replace("–", "-").replace("s", "").partition("-")
    try:
        secs.append(max(4, round(float(b) - float(a))))
    except ValueError:
        secs.append(4)
payload = {"scenes": rows, "seconds": secs, "pace": pace, "logline": vc.get("logline", ""), "message": vc.get("rationale", ""), "tone": " ".join(str(vc.get(k, "")) for k in ("name", "rationale", "logline"))[:300],
           "characters": d.get("video_characters", ""), "film": True}
print(f"film {fid}: {len(rows)} scenes, seconds {secs}, pace {pace}, suggest_pace -> {sceneshots.suggest_pace(payload['tone'])}")
r = main.film_review(payload)
if not isinstance(r, dict):
    print("ERROR", r.status_code, r.body[:400]); sys.exit(1)
st = r["stats"]
print(f"\nMEASURED: {st['shots']} shots in {st['seconds']} s, {st['per10']} per 10 s (band {st['band']}), longest same-size run {st['longest_same_size_run']}")
for f in st["findings"]:
    print("  finding:", f["note"])
print("\nSUMMARY:", r["summary"])
print("turn scene", r["turn_scene"], "| message carrier", r["carrier_scene"], "| time passing", r["time_passing"])
for b in r["beats"]:
    print("  beat", b["scenes"], "repetition" if b["repetition"] else "", "-", b["purpose"])
print("\nVERDICTS")
for v in r["verdicts"]:
    print(f"  scene {v['scene']} shot {v['shot']} [{v['job'] or '-'}]: {v['verdict'].upper()}  {v['reason']}" + (f"  (merge with {v['merge_with']})" if v["merge_with"] else ""))
print("\nNOTES")
for n in r["notes"]:
    print("  scenes", n["scenes"], "-", n["note"], "->", n["suggestion"])
for n in r["notes_out"]:
    print("  (system)", n)
left = st["shots"] - len(r["skips"])
print(f"\nIf applied: {left} shots in the film ({len(r['skips'])} skipped).")
