#!/usr/bin/env python
"""coverage_golden.py -- a SNAPSHOT of what the planner and the video prompts produce for scenes that carry no `shots`.

Why: coverage (VIDEO_COVERAGE_PLAN.md) changes `filmcut.plan_by_scene` and the render's prompt wiring. The promise is that a film
with no `shots` is byte-for-byte what it was. This module computes the values; `tools/golden/coverage_golden.json` holds the values
as they were BEFORE the change (written once, from the unmodified code); `tools/test_coverage_plan.py` re-computes and compares.

    api/.venv/Scripts/python.exe tools/coverage_golden.py --write     # only ever run on the code you want to freeze
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "api")
GOLDEN = os.path.join(ROOT, "tools", "golden", "coverage_golden.json")


def _vo(text, speaker=""):
    return {"kind": "vo", "text": text, **({"speaker": speaker} if speaker else {})}


def corpus():
    """Eight film shapes. Rows use the fields the studio's rows really carry."""
    talk = "Every morning, two hundred thousand families pour a glass of Heritage, and every glass has been tested, tasted and checked twice over before it reaches the door."
    f1 = [{"no": i + 1, "tc": "", "visual": v, "camera": c, "audio": a}
          for i, (v, c, a) in enumerate([
              ("A mother pours milk into a steel vessel.", "slow push in", [_vo("Mornings begin the same way.")]),
              ("The boy steps closer with his glass.", "", []),
              ("A technician lowers a pipette into a sample.", "handheld", [_vo("Behind every glass, a test.")]),
              ("Two colleagues check a clipboard.", "", []),
              ("The boy drinks and smiles.", "", [_vo("Pure, every day.")]),
              ("The Heritage pouch, front-on, on the counter.", "", [_vo("Heritage. Health and happiness.")])])]
    f2 = [{"no": i + 1, "tc": "", "visual": f"Scene {i + 1} visual", "audio": [_vo(t)] if t else []}
          for i, t in enumerate(["Open on a village morning.", "", "The lab, the proof.", "Sign off."])]
    f3 = [{"no": 1, "tc": "", "visual": "Hook shot."}, {"no": 2, "tc": "", "visual": "Pack shot."}, {"no": 3, "tc": "", "visual": "Sign-off."}]
    f4 = [{"no": 1, "tc": "", "visual": "A long talking scene in the kitchen.", "audio": [_vo(talk), _vo(talk)]},
          {"no": 2, "tc": "", "visual": "A second talking scene.", "audio": [_vo(talk)]}]
    f5 = [{"no": 1, "tc": "", "visual": "Hook.", "beat_role": "hook"}, {"no": 2, "tc": "", "visual": "Mechanism A."},
          {"no": 3, "tc": "", "visual": "Sign-off in the middle.", "beat_role": "brand"}, {"no": 4, "tc": "", "visual": "Mechanism B."},
          {"no": 5, "tc": "", "visual": "A button after the sign-off.", "beat_role": "button"}]
    f6 = [{"no": 1, "tc": "", "visual": "Mother pours milk from the pouch into a steel glass.", "camera": "slow push in", "shot_size": "medium",
           "movement_class": "push-in", "beat_note": "tender, unhurried", "frame_url": "/media/f1.jpg", "dialogue": "VO: Mornings.", "title": ""},
          {"no": 2, "tc": "", "visual": "The boy drinks.", "desc": "Kitchen morning light.", "shot_size": "close", "frame_url": "/media/f2.jpg"},
          {"no": 3, "tc": "", "visual": "A lab technician studies the sample.", "camera": "handheld", "movement_class": "handheld", "frame_url": "/media/f3.jpg"},
          {"no": 4, "tc": "", "visual": "No frame on this one.", "camera": "static"},
          {"no": 5, "tc": "", "visual": "The pack, clean and front-facing.", "frame_url": "/media/f5.jpg"}]
    f7 = [{"no": 1, "tc": "", "visual": "One single scene film.", "audio": [_vo("Just one.")]}]
    f8 = [{"no": i + 1, "tc": "", "visual": f"Scene {i + 1}"} for i in range(7)]
    return {"f1_six_scenes": f1, "f2_four_scenes": f2, "f3_three_silent": f3, "f4_long_dialogue": f4, "f5_explicit_roles": f5,
            "f6_prompt_fields": f6, "f7_single": f7, "f8_overflow_seven": f8}


def _clean(o):
    return json.loads(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str))


def snapshot() -> dict:
    sys.path.insert(0, API)
    os.chdir(API)
    os.environ.setdefault("GOOGLE_API_KEY", "golden-test-key")
    import copy
    import filmcut, filmvoice
    out = {"plans": {}, "retime": {}, "prompts": {}, "turn_at": {}}
    for name, rows0 in corpus().items():
        for target in (0, 10, 20, 30):
            rows = copy.deepcopy(rows0)
            total, notes = filmvoice.retime(rows, target_total=target)
            per = filmvoice.scene_seconds(rows, target_total=target)
            segs = filmcut.plan_by_scene(rows, per)
            key = f"{name}@{target}"
            out["retime"][key] = {"total": total, "notes": notes, "tc": [r.get("tc") for r in rows]}
            out["plans"][key] = [{"index": s["index"], "seconds": s["seconds"], "no": (s["scenes"][0] if s["scenes"] else {}).get("no"),
                                  "continues": s.get("continues"), "role": s.get("role"), "role_what": s.get("role_what")} for s in segs]
    # prompts through the real render function, generators stubbed, nothing written
    import main, gemini, creative
    gemini.available = lambda: True
    for name in ("f6_prompt_fields", "f4_long_dialogue", "f1_six_scenes"):
        for tier, revise in (("lite", ""), ("standard", "make it warmer")):
            captured = []
            gemini.video = lambda prompt, **kw: (captured.append({"prompt": prompt, "seconds": kw.get("seconds"), "tier": kw.get("tier"),
                                                                   "frame": bool(kw.get("image_ref"))}), "/media/fake.mp4")[1]
            filmcut.stitch = lambda urls, lengths=None: None
            main._record_made = lambda *a, **k: None
            payload = {"scenes": copy.deepcopy(corpus()[name]), "aspect": "16:9", "duration": "30s", "engines": {"video": "google"},
                       "tier": tier, "camera_notes": "handheld, shallow depth of field" if name == "f6_prompt_fields" else "",
                       "wardrobe": "boy: white school shirt" if tier == "standard" else "", "note": revise, "script": {"logline": "A morning."}}
            try:
                main._produce_video_sync(payload)
            except Exception as e:                       # the stubbed stitch ends the route early; a raise after generation is fine
                captured.append({"raised": type(e).__name__})
            out["prompts"][f"{name}/{tier}"] = sorted(captured, key=lambda c: json.dumps(c, sort_keys=True))
    for name in ("f1_six_scenes", "f5_explicit_roles"):
        for on in (False, True):
            try:
                out["turn_at"][f"{name}/{on}"] = main._turn_at_from_rows(copy.deepcopy(corpus()[name]), "30s")
            except Exception as e:
                out["turn_at"][f"{name}/{on}"] = f"raised {type(e).__name__}"
    return _clean(out)


if __name__ == "__main__":
    snap = snapshot()
    if "--write" in sys.argv:
        os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
        with open(GOLDEN, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(snap, fh, indent=1, sort_keys=True, ensure_ascii=False)
        print("wrote", GOLDEN, "-", len(snap["plans"]), "plans,", len(snap["prompts"]), "prompt sets")
    else:
        print(json.dumps(snap)[:400])
