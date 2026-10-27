#!/usr/bin/env python
"""scene_shots_real.py -- REAL model calls to POST /scene-shots (main.scene_shots) on a hand-written Heritage script, so the proposals can be read
by a person. Spends a few cents of Claude credit; no images, no video. Output: Downloads\\engine-trial\\coverage_step3\\proposals.json (+ printed)."""
import json, os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
OUT = r"C:\Users\punie\Downloads\engine-trial\coverage_step3"; os.makedirs(OUT, exist_ok=True)
import filmvoice, main

def vo(t): return {"kind": "vo", "text": t}
rows = [
 {"no": 1, "visual": "The mother stirs the steaming milk in the steel pot with a ladle while the boy steps closer, holding his glass.", "camera": "handheld drift",
  "audio": [vo("Mornings begin the same way.")]},
 {"no": 2, "visual": "A lab technician lowers a pipette into a steel cup of milk sample, draws the liquid up and lifts it to study the level.", "camera": "slow push-in"},
 {"no": 3, "visual": "A man presses a button on the instrument while a woman beside him writes notes on a clipboard.", "camera": "locked-off",
  "audio": [vo("Behind every glass, a test, and then another.")]},
 {"no": 4, "visual": "The boy takes the steel glass from the counter; his mother stands beside him holding the Heritage pouch.", "camera": "slow push-in", "shot_size": "medium",
  "audio": [vo("Every glass is tasted, tested and checked twice before it ever reaches your family's door."), vo("Because the people who drink it are the people we love.")]},
 {"no": 5, "visual": "The mother tilts the Heritage pouch and pours a steady stream of milk into the steel vessel.", "camera": "gentle drift"},
 {"no": 6, "visual": "The Heritage pouch on the counter, front-on, in warm morning light.", "audio": [vo("Heritage. Health and happiness.")]},
]
total, _ = filmvoice.retime(rows, target_total=30); per = filmvoice.scene_seconds(rows, target_total=30)
print("scene seconds:", per, "total", total)
ctx = dict(logline="A morning with Heritage: the milk a family trusts, and the testing behind every glass.",
           characters="Mother: late 30s, cream saree with a gold border, hair in a bun. Boy: 8 years old, white school shirt, grey shorts. Lab technicians: a woman and a man in white coats with green trim, blue gloves, hair tied back.",
           location_line="A bright middle-class Hyderabad kitchen: steel counter, a window on the left, a gas stove; and a clean milk-testing lab.",
           wardrobe="Mother: cream saree with gold border. Boy: white school shirt, grey shorts. Technicians: white lab coats with green trim and the Heritage logo, blue gloves.",
           camera_notes="Handheld with a gentle breathing sway, shallow depth of field, natural window light.", plate_locked=False)
results = []
for i, row in enumerate(rows):
    t0 = time.time()
    res = main.scene_shots({"scene": row, "scene_seconds": per[i], "is_signoff": i == len(rows) - 1,
                            "prev_visual": rows[i - 1]["visual"] if i else "", "next_visual": rows[i + 1]["visual"] if i < len(rows) - 1 else "", "brand_mode": "grounded", **ctx})
    body = res if isinstance(res, dict) else {"status": res.status_code, **json.loads(res.body)}
    results.append({"scene": row["no"], "seconds": per[i], "response": body})
    print(f"\n=== scene {row['no']} ({per[i]}s)  {time.time()-t0:.0f}s: {row['visual'][:70]}")
    if body.get("status"):
        print("  ERROR", body); continue
    if not body.get("shots"):
        print("  no shots:", body.get("reason")); continue
    print(f"  master keeps {body['master_secs']}s")
    for k, s in enumerate(body["shots"], start=2):
        print(f"  shot {k}  {s['secs']}s  [{s['shot_size']}] {s['camera']!r} ({s['movement_class'] or '-'})\n     {s['visual']}")
        for w in s["warnings"]: print("     WARNING:", w)
    for n in body["notes"]: print("  note:", n)
# the same talky scene when the location IS locked (does it now offer a wide?)
res = main.scene_shots({"scene": rows[3], "scene_seconds": per[3], "prev_visual": rows[2]["visual"], "next_visual": rows[4]["visual"], **{**ctx, "plate_locked": True}})
body = res if isinstance(res, dict) else json.loads(res.body)
print("\n=== scene 4 again with the location LOCKED:", [(s["shot_size"], s["secs"]) for s in body.get("shots", [])])
results.append({"scene": 4, "seconds": per[3], "plate_locked": True, "response": body})
json.dump(results, open(os.path.join(OUT, "proposals.json"), "w"), indent=1, ensure_ascii=False)
