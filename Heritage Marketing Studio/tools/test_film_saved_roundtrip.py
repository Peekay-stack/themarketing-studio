#!/usr/bin/env python
"""test_film_saved_roundtrip.py -- every field added to a saved film on 29 Oct survives the film store, and a film saved BEFORE them still loads with the old shape (backwards and forwards):
the concept's `stake`, the director's read's `concept_delivery` / `sequence` / `actions`, and a frame's `parts` fingerprint. The store is pointed at a temp folder (never the real tenant).
Run:  api/.venv/Scripts/python.exe tools/test_film_saved_roundtrip.py
"""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import filmscript, takes, filmdirect as fd

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

tmp = tempfile.mkdtemp()
filmscript._path = lambda house_id: os.path.join(tmp, f"{house_id}.json")

concept = {"name": "R", "logline": "L", "vo": "v", "stake": "She loses the one test she trusted.", "hook": "h", "surprise": "s", "turn": "t", "memorable": "m", "scenes": [{"t": "0-5s", "title": "a", "desc": "b"}]}
rows = [{"no": 1, "tc": "0-6s", "visual": "A drop rolls."}, {"no": 2, "tc": "6-12s", "visual": "She smells it, watches it boil, holds it to light."}]
raw = {"summary": "s", "turn_scene": 2, "carrier_scene": 2, "scenes": [{"no": 1, "purpose": "p", "intensity": 1, "place": "kitchen", "energy": 1, "change": "c", "beat": "a"},
        {"no": 2, "purpose": "p", "intensity": 2, "place": "kitchen", "energy": 2, "change": "c", "beat": "b", "sequence": True, "actions": ["smells", "boils", "light"]}],
       "concept": [{"id": "hook", "status": "delivered", "scene": 1}, {"id": "beat1", "status": "flattened", "scene": 2, "note": "one still shot"}]}
bm = fd.validate(raw, rows, {}, fd.promises(concept)); bm["sig"] = "abc"
frame = {"id": "fr_1", "url": "/media/frame-1.jpg", "status": "done", "recipe": "r1", "parts": {"words": "aaaa", "dept": "bbbb", "loc": "cccc"}}
doc = {"frames": {"0": [frame]}, "frame_chosen": {"0": "fr_1"}}

filmscript.save("h1", {"video_concept": concept, "full_script": rows, "video_beat_map": bm, "video_builder": doc, "scene_frames": {"0": {"url": "/media/frame-1.jpg", "status": "done", "recipe": "r1", "parts": {"words": "aaaa"}}}})
back = filmscript.load("h1")
rows_p = [{"no": 1, "tc": "0-6s", "visual": "A boy drinks."}, {"no": 2, "tc": "6-12s", "visual": "A technician reads a vial.", "place": "A dairy lab at dawn"}]
filmscript.save("h3", {"full_script": rows_p})
check("a scene's own `place` survives the film store, and a row with none stays without the key", filmscript.load("h3")["full_script"][1]["place"] == "A dairy lab at dawn" and "place" not in filmscript.load("h3")["full_script"][0])
check("the concept's stake survives the store, with every other concept field", back["video_concept"] == concept, back["video_concept"])
check("the director's read survives whole: the promises, their statuses, a scene's sequence flag and its actions", back["video_beat_map"]["concept_delivery"] == bm["concept_delivery"]
      and back["video_beat_map"]["scenes"][1]["sequence"] is True and back["video_beat_map"]["scenes"][1]["actions"] == ["smells", "boils", "light"] and back["video_beat_map"]["sig"] == "abc", str(back["video_beat_map"])[:300])
check("the read's concept findings survive and are still first", [f["kind"] for f in back["video_beat_map"]["findings"]][:1] == ["concept-flattened"])
check("a chosen frame's `parts` fingerprint survives the builder's normaliser", back["video_builder"]["frames"]["0"][0]["parts"] == frame["parts"], back["video_builder"])
check("the saved page-state frame keeps its `parts` too", back["scene_frames"]["0"]["parts"] == {"words": "aaaa"})

# a film saved before these fields existed: loads, and the readers that use the new fields tolerate it
old = {"video_concept": {"name": "Old", "logline": "L", "vo": "v", "scenes": [{"t": "0-5s", "title": "a", "desc": "b"}]}, "full_script": rows,
       "video_beat_map": {"summary": "s", "turn_scene": 2, "carrier_scene": 2, "scenes": [{"no": 1, "purpose": "p", "intensity": 1, "time_mode": "continuous", "beat": "b1", "hero": False, "place": "kitchen", "energy": 1, "change": ""}],
                          "transitions": [], "findings": [], "notes": [], "engagement": {"risk": "low"}, "sig": "x"}}
filmscript.save("h2", old)
b2 = filmscript.load("h2")
check("an older film loads with no stake and no promise answers (nothing is invented)", "stake" not in b2["video_concept"] and "concept_delivery" not in b2["video_beat_map"])
check("the readers of the director's read tolerate an older read (no sequence field): no run, no cover change, text unchanged", fd.sequences(b2["video_beat_map"]) == {} and "A RUN OF QUICK ACTIONS" not in fd.read_text(b2["video_beat_map"]) and fd.no_coverage(b2["video_beat_map"]) == {})
check("an older frame with no `parts` is normalised with an empty fingerprint (the page then says only 'something changed')", takes.normalise({"frames": {"0": [{"id": "x", "url": "/media/a.jpg", "status": "done"}]}})["frames"]["0"][0]["parts"] == {})
print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
