#!/usr/bin/env python
"""test_film_direct_craft.py -- offline checks for workstream W3 of FILM_CRAFT_LAYER_PLAN.md: the director's read in CRAFT MODE (request flag `craft: true` AND server switch CRAFT_BRIEF).
Adds two questions (one message, a memorable device), softens the "opens quietly" and "one place" findings to quiet notes that do not count towards the risk, and changes NOTHING when craft mode
is off. The model is stubbed; nothing is saved.
Run:  api/.venv/Scripts/python.exe tools/test_film_direct_craft.py
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import filmdirect, main

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

# a quiet film in ONE kitchen: scene 1 quiet (energy 1, intensity 1), four neighbouring scenes in the same place
ROWS = [{"no": i, "visual": f"Kitchen scene {i}", "dialogue": ""} for i in range(1, 7)]
def scene(n, place, energy, inten, change="x"):
    return {"no": n, "purpose": "p", "intensity": inten, "time_mode": "continuous", "marker": "", "beat": f"b{n}", "hero": n == 6, "place": place, "energy": energy, "change": change, "sequence": False, "actions": []}
RAW = {"summary": "s", "time_passing": False, "hero_object": "", "turn_scene": 4, "carrier_scene": 6,
       "scenes": [scene(1, "kitchen", 1, 1), scene(2, "kitchen", 2, 2), scene(3, "kitchen", 2, 2), scene(4, "kitchen", 3, 3), scene(5, "kitchen", 2, 2), scene(6, "street", 2, 3)],
       "one_message": {"clear": False, "message": "", "note": "it says three things"}, "device": {"present": False, "what": "", "note": "no repeatable line"}}

# --- pure functions ---
p_off, p_on = filmdirect.build_prompt(rows=ROWS, seconds=[5] * 6), filmdirect.build_prompt(rows=ROWS, seconds=[5] * 6, craft=True)
check("OFF: the prompt is exactly what it was (no craft section, no craft JSON)", "CRAFT." not in p_off and "one_message" not in p_off and "\"device\"" not in p_off)
check("ON: the prompt asks the two craft questions and the JSON shape carries them", "ONE MESSAGE" in p_on and "A MEMORABLE DEVICE" in p_on and "\"one_message\"" in p_on and "\"device\"" in p_on)
check("ON: the craft ask sits before the turn/carrier request and the rest of the prompt is unchanged", p_on.index("CRAFT.") < p_on.index("Then name the TURN") and p_on.replace(filmdirect.CRAFT_ASK, "").replace(filmdirect.CRAFT_JSON, "") == p_off)

off = filmdirect.validate(RAW, ROWS)
check("OFF: slow-hook and same-place are real findings, count towards the risk, and there is no craft block", {f["kind"] for f in off["findings"]} >= {"slow-hook", "same-place"}
      and not any(f.get("quiet") for f in off["findings"]) and "craft" not in off and off["engagement"]["risk"] == "medium", (off["engagement"], [f["kind"] for f in off["findings"]]))
on = filmdirect.validate(RAW, ROWS, craft=True)
kinds = {f["kind"]: f for f in on["findings"]}
check("ON: slow-hook and same-place are still listed, marked quiet", kinds["slow-hook"].get("quiet") is True and kinds["same-place"].get("quiet") is True)
check("ON: quiet notes do not count towards the risk (medium becomes low)", on["engagement"]["risk"] == "low", on["engagement"])
check("ON: the craft answers are returned cleaned", on["craft"]["message"] == {"clear": False, "message": "", "note": "it says three things"} and on["craft"]["device"]["present"] is False)
check("ON: no single message and no device become quiet, craft-tagged notes with no scene", kinds["no-message"]["quiet"] and kinds["no-message"]["craft"] and kinds["no-message"]["scene"] is None and kinds["no-device"]["quiet"] and "most remembered films" in kinds["no-device"]["note"])
check("ON: quiet notes are listed after the real findings", [bool(f.get("quiet")) for f in on["findings"]] == sorted(bool(f.get("quiet")) for f in on["findings"]))

good = dict(RAW, one_message={"clear": True, "message": "Test the milk", "note": ""}, device={"present": True, "what": "the sniff", "note": ""})
g = filmdirect.validate(good, ROWS, craft=True)
check("ON: a clear message and a present device raise no craft notes", not any(f["kind"] in ("no-message", "no-device") for f in g["findings"]) and g["craft"]["device"]["what"] == "the sniff")
m = filmdirect.validate({k: v for k, v in RAW.items() if k not in ("one_message", "device")}, ROWS, craft=True)
check("ON: answers the model did not give are unknown, never a finding", m["craft"] == {"message": None, "device": None} and not any(f["kind"] in ("no-message", "no-device") for f in m["findings"]))
b = filmdirect.validate(dict(RAW, one_message={"clear": "no"}, device="nope"), ROWS, craft=True)
check("ON: a malformed answer is unknown too", b["craft"] == {"message": None, "device": None})
three = filmdirect.validate(dict(RAW, scenes=[scene(i, "kitchen", 0, 0, "") for i in range(1, 7)]), ROWS, craft=True)
check("ON: real boredom findings still raise the risk (flat energy, no change are not quiet)", three["engagement"]["risk"] in ("medium", "high") and any(f["kind"] == "flat-energy" and not f.get("quiet") for f in three["findings"]), three["engagement"])

# --- the route, with the model stubbed ---
seen = {"n": 0}
def fake_complete(messages, **kw):
    seen["messages"] = messages; seen["n"] += 1
    return json.dumps(RAW)
main.completion.complete = fake_complete
main.completion.has_key = lambda: True
body = {"scenes": ROWS, "seconds": [5] * 6}

os.environ.pop("CRAFT_BRIEF", None)
r = main.film_direct({**body, "craft": True})
check("flag ON, server switch OFF: nothing changes (no craft prompt, no craft block, nothing quiet)", "CRAFT." not in seen["messages"][0]["content"] and "craft" not in r and not any(f.get("quiet") for f in r["findings"]))
os.environ["CRAFT_BRIEF"] = "1"
r = main.film_direct(dict(body))
check("flag OFF, server switch ON: nothing changes", "CRAFT." not in seen["messages"][0]["content"] and "craft" not in r)
r = main.film_direct({**body, "craft": True})
check("flag ON and server switch ON: the craft prompt goes out and the craft block comes back", "ONE MESSAGE" in seen["messages"][0]["content"] and r["craft"]["device"]["present"] is False and r["model"] is True, list(r))
os.environ.pop("CRAFT_BRIEF", None)

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
