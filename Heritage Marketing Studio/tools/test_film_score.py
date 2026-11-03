#!/usr/bin/env python
"""test_film_score.py -- offline checks for the CRAFT SCORECARD (api/filmscore.py + POST /film-score, FILM_CRAFT_LAYER_PLAN.md W0). The model is stubbed: no network, nothing saved.
Run:  api/.venv/Scripts/python.exe tools/test_film_score.py
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import filmscore, main

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

GOOD = {"tests": [{"id": i, "score": s, "reason": "r " + i} for i, s in zip(filmscore.IDS, (3, 2, 3, 1, 0, 2, 2))],
        "strongest": "message", "weakest": "device", "summary": "A warm, clear film.", "suggestion": "Give the grandmother a repeatable gesture."}

# --- pure functions ---
v = filmscore.validate(GOOD)
check("all seven tests appear once, in the server's order", [t["id"] for t in v["tests"]] == list(filmscore.IDS))
check("total and max add up (13 of 21)", v["total"] == 13 and v["max"] == 21 and v["scored"] == 7, (v["total"], v["max"]))
check("strongest and weakest are kept when the model's choice is valid", v["strongest"] == "message" and v["weakest"] == "device")
check("labels come from the server", v["tests"][0]["label"] == "One clear message")

w = filmscore.validate({"tests": [{"id": "hook", "score": 9, "reason": "x"}, {"id": "moment", "score": -4, "reason": "y"}, {"id": "bogus", "score": 3}, {"id": "hook", "score": 0}], "strongest": "nope", "weakest": "nope"})
check("scores are clamped to 0-3", w["tests"][1]["score"] == 3 and w["tests"][2]["score"] == 0)
check("an unknown id is ignored and a repeated id counts once (the first)", sum(1 for t in w["tests"] if t["id"] == "hook") == 1 and w["tests"][1]["score"] == 3)
check("a skipped test is None, not zero, and is left out of the total", w["tests"][0]["score"] is None and w["scored"] == 2 and w["max"] == 6 and len(w["notes"]) == 5, (w["scored"], w["max"], len(w["notes"])))
check("an invalid strongest/weakest falls back to the best/worst scored test", w["strongest"] == "hook" and w["weakest"] == "moment" or w["strongest"] in ("hook", "moment"))
e = filmscore.validate({})
check("an empty reply gives no scores and no crash", e["scored"] == 0 and e["max"] == 0 and e["strongest"] == "" and e["weakest"] == "")
check("a non-numeric score is treated as unscored", filmscore.validate({"tests": [{"id": "hook", "score": "high"}]})["tests"][1]["score"] is None)
check("parse reads fenced JSON and prose around it", filmscore.parse("```json\n" + json.dumps(GOOD) + "\n```")["weakest"] == "device" and filmscore.parse("Here: " + json.dumps(GOOD) + " done")["strongest"] == "message")
check("parse returns None for non-JSON and for a JSON list", filmscore.parse("no json here") is None and filmscore.parse("[1,2]") is None)

p = filmscore.build_prompt(concept={"logline": "A grandmother tests the milk.", "memorable": "She sniffs it and smiles.", "scenes": [{"t": "0-5", "title": "Fridge", "desc": "Opens it"}]},
                           rows=[{"no": 1, "visual": "Kitchen at dawn", "dialogue": "Pehle test, phir bharosa"}], seconds=[6], message="Pure milk", tone="warm", characters="Dadi")
check("the prompt carries the concept lines, beats, script rows, spoken line and all seven test ids",
      all(s in p for s in ("A grandmother tests the milk.", "She sniffs it and smiles.", "BEAT 0-5 Fridge", "SCENE 1 (6 s)", "Pehle test, phir bharosa", "Pure milk", "Dadi")) and all(f"`{i}`" in p for i in filmscore.IDS))
check("the prompt asks for JSON only and for honesty", "Return ONLY JSON" in p and "do not flatter" in p)

# --- the route, with the model stubbed ---
seen = {"n": 0}
def fake_complete(messages, **kw):
    seen["messages"], seen["kw"] = messages, kw
    seen["n"] += 1
    return seen.get("reply", "")
main.completion.complete = fake_complete
main.completion.has_key = lambda: True

def call(payload):
    r = main.film_score(payload)
    return (r.status_code, json.loads(r.body)) if hasattr(r, "status_code") else (200, r)

seen["reply"] = json.dumps(GOOD)
st, out = call({"concept": {"logline": "A grandmother tests the milk."}, "message": "Pure milk"})
check("a concept scores: 200, seven tests, model flag, one model call", st == 200 and len(out["tests"]) == 7 and out["model"] is True and seen["n"] == 1, (st, seen["n"]))
check("the model call is a film call and carries the concept text", "A grandmother tests the milk." in json.dumps(seen["messages"]))
st, out = call({"scenes": [{"no": 1, "visual": "Kitchen"}], "seconds": [5]})
check("a script alone also scores", st == 200 and out["total"] == 13)
n = seen["n"]
st, out = call({})
check("nothing to score: 400 and no model call", st == 400 and seen["n"] == n)
st, out = call({"concept": {}, "scenes": []})
check("an empty concept and no scenes: 400", st == 400)
seen["reply"] = "sorry, I cannot"
st, out = call({"concept": {"logline": "x"}})
check("an unreadable reply: 502, not a fake scorecard", st == 502 and "tests" not in out, (st, out))
seen["reply"] = json.dumps(GOOD)
main.completion.has_key = lambda: False
st, out = call({"concept": {"logline": "x"}})
check("no key configured: the model error is passed through (not 200)", st != 200, st)
main.completion.has_key = lambda: True

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
