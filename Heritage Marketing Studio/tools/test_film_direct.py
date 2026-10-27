#!/usr/bin/env python
"""test_film_direct.py -- offline checks for craft slice 4: filmdirect.py (the beat map: prompt, reader, backstops, the two no-coverage RULES) and how it reaches /film-direct,
/scene-shots and /film-review. The film is neutral and brand-free, shaped like the one the owner rejected (a memory shown at two scales that is really time passing, a turn, a
pack sign-off). No network, no credit, nothing written to the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_film_direct.py
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import filmdirect as fd, flowreview as fr, sceneshots as ss, filmscript, main

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

def S(visual, size, secs=2, job="reveal", why="adds something the master does not show", **k):
    return {"visual": visual, "shot_size": size, "secs": secs, "job": job, "why": why, **k}
ROWS = [
    {"no": 1, "visual": "A mother measures a boy's trousers at the hem.", "shot_size": "medium", "audio": [{"kind": "vo", "text": "Every day he grew."}]},
    {"no": 2, "visual": "Months earlier, the boy drinks a glass of milk at the counter.", "shot_size": "wide", "audio": [{"kind": "vo", "text": "Glass by glass."}],
     "shots": [S("Close on the boy's face.", "close", 2, "reaction", "his face shows the sip")]},
    {"no": 3, "visual": "Closer on the boy drinking, the glass lowering empty.", "shot_size": "close", "audio": [{"kind": "vo", "text": "Month after month."}],
     "shots": [S("His hand on the glass.", "detail", 2, "insert", "the glass is the object")]},
    {"no": 4, "visual": "The mother lets the hem down; it falls short again.", "shot_size": "medium", "audio": [{"kind": "vo", "text": "And one morning."}], "shots": [S("Her face.", "close", 2, "reaction", "the realisation")]},
    {"no": 5, "visual": "The boy stands tall in the trousers; they fit.", "shot_size": "wide", "audio": [{"kind": "vo", "text": "It fit."}]},
    {"no": 6, "visual": "The pack stands beside a glass on the counter.", "shot_size": "medium", "beat_role": "brand", "audio": [{"kind": "vo", "text": "One glass at a time."}]},
]
SECS = [6, 8, 6, 6, 6, 6]
ROLES = {1: "hook", 2: "world", 3: "mechanism", 4: "turn", 5: "turn", 6: "brand"}
KEY = {"summary": "A mother discovers that her son's growth was poured glass by glass.", "time_passing": True, "hero_object": "the pack", "turn_scene": 4, "carrier_scene": 6,
       "scenes": [
           {"no": 1, "purpose": "surprise at the short hem", "intensity": 1, "time_mode": "continuous", "marker": "", "beat": "a", "hero": False},
           {"no": 2, "purpose": "the memory, glass by glass", "intensity": 1, "time_mode": "flashback", "marker": "warmer light, a shorter boy", "beat": "b", "hero": False},
           {"no": 3, "purpose": "the memory again, closer", "intensity": 1, "time_mode": "flashback", "marker": "", "beat": "b", "hero": False},
           {"no": 4, "purpose": "the realisation as she lets the hem down", "intensity": 3, "time_mode": "continuous", "marker": "", "beat": "c", "hero": False},
           {"no": 5, "purpose": "it fits now", "intensity": 2, "time_mode": "continuous", "marker": "", "beat": "d", "hero": False},
           {"no": 6, "purpose": "the message lands on the pack", "intensity": 2, "time_mode": "continuous", "marker": "", "beat": "e", "hero": True}]}

# ---- prompt ----------------------------------------------------------------------------------------------------------------------------
pr = fd.build_prompt(rows=ROWS, seconds=SECS, logline="A mother lets a hem down, glass by glass.", message="One glass at a time.", tone="tender", characters="Mother, boy", hero="the pack", roles=ROLES)
check("prompt: carries the film's own words, the whole script with seconds and the planner's job", "glass by glass" in pr and "One glass at a time." in pr and "SCENE 2 (8 s, planned job: world)" in pr and pr.count("SCENE ") == 6)
check("prompt: asks for purpose, intensity, time mode, marker, beat group and hero per scene, plus the turn and the carrier",
      all(w in pr for w in ("`purpose`", "`intensity`", "`time_mode`", "`marker`", "`beat`", "`hero`", "`turn_scene`", "`carrier_scene`", "`time_passing`")))
check("prompt: montage = visibly different days; one beat shown twice shares an id; judged by meaning, any language", "VISIBLY DIFFERENT" in pr and "SAME id" in pr and "MEANING" in pr)
check("prompt: no brand word in the rules", "heritage" not in pr.lower() and "dairy" not in pr.lower())

# ---- parse / validate --------------------------------------------------------------------------------------------------------------------
check("parse: plain / fenced / garbage", fd.parse(json.dumps(KEY))["turn_scene"] == 4 and fd.parse("ok:\n```json\n" + json.dumps(KEY) + "\n```")["hero_object"] == "the pack" and fd.parse("nope") is None and fd.parse("[1]") is None)
v = fd.validate(KEY, ROWS, ROLES)
by = {s["no"]: s for s in v["scenes"]}
check("validate: one entry per script scene, in order, with the fields", [s["no"] for s in v["scenes"]] == [1, 2, 3, 4, 5, 6] and all(k in v["scenes"][0] for k in ("purpose", "intensity", "time_mode", "marker", "beat", "hero")))
check("validate: beats are renumbered and scenes 2+3 share one (neighbours)", by[2]["beat"] == by[3]["beat"] and len({s["beat"] for s in v["scenes"]}) == 5, str([s["beat"] for s in v["scenes"]]))
check("validate: the turn and the carrier are kept", v["turn_scene"] == 4 and v["carrier_scene"] == 6 and v["time_passing"] is True and v["hero_object"] == "the pack")
check("validate: transitions are listed, the marked one is marked, the unmarked return is a finding",
      [(t["from"], t["to"], t["marked"]) for t in v["transitions"]] == [(1, 2, True), (3, 4, False)] and any(f["kind"] == "unmarked-transition" and f["scene"] == 4 for f in v["findings"]), str(v["transitions"]))
check("validate: scenes 2+3 are reported as ONE beat", any(f["kind"] == "one-beat" and "2, 3" in f["note"] for f in v["findings"]))
check("validate: a good film has no 'flat' or 'weak turn' finding", not any(f["kind"] in ("flat", "weak-turn", "carrier-without-hero") for f in v["findings"]))
flat = fd.validate({**KEY, "scenes": [{**s, "intensity": 1} for s in KEY["scenes"]]}, ROWS, ROLES)
check("validate: every scene at the same intensity -> a 'flat' finding", any(f["kind"] == "flat" for f in flat["findings"]))
weak = fd.validate({**KEY, "scenes": [{**s, "intensity": 3 if s["no"] == 5 else 1} for s in KEY["scenes"]]}, ROWS, ROLES)
check("validate: a turn that is not the strongest scene is flagged", any(f["kind"] == "weak-turn" and f["scene"] == 4 for f in weak["findings"]))
nohero = fd.validate({**KEY, "scenes": [{**s, "hero": False} for s in KEY["scenes"]]}, ROWS, ROLES)
check("validate: a message carrier without the hero object is flagged", any(f["kind"] == "carrier-without-hero" and f["scene"] == 6 for f in nohero["findings"]))
odd = fd.validate({"turn_scene": 99, "carrier_scene": 99, "scenes": [{"no": 1, "intensity": 9, "time_mode": "Flash Back", "beat": "z"}, {"no": 1, "purpose": "duplicate"}, {"no": 2, "intensity": "x", "time_mode": "??", "beat": "z"},
                                                                    {"no": 77}, "junk", None]}, ROWS, ROLES)
ob = {s["no"]: s for s in odd["scenes"]}
check("validate: intensity is clamped 0-3, unknown time modes fall back, synonyms are read, junk entries are ignored", ob[1]["intensity"] == 3 and ob[1]["time_mode"] == "flashback" and ob[2]["intensity"] == 1 and ob[2]["time_mode"] == "flashback" and len(odd["scenes"]) == 6, str(odd["scenes"][:2]))
check("validate: scenes the review skipped get a plain default and a note", ob[4]["time_mode"] == "continuous" and any("Scene 4" in n for n in odd["notes"]))
check("validate: a turn or carrier that is not a real scene is replaced (carrier -> the sign-off) and says so", odd["carrier_scene"] == 6 and any("carrier" in n for n in odd["notes"]) and odd["turn_scene"] in (None, 1, 2, 3, 4, 5))
nb = fd.validate({"scenes": [{"no": 1, "beat": "a"}, {"no": 2, "beat": "b"}, {"no": 3, "beat": "a"}]}, ROWS[:3], ROLES)
check("validate: only NEIGHBOURING scenes may share a beat (a, b, a -> three beats)", len({s["beat"] for s in nb["scenes"]}) == 3)
check("validate: garbage never raises", fd.validate(None, ROWS)["scenes"] != [] and fd.validate({}, [])["scenes"] == [] and fd.validate({"scenes": "x"}, None)["scenes"] == [])
check("mode_of: synonyms and junk", [fd.mode_of(x) for x in ("memory", "Flash-forward", "time passing", "present", "banana", None)] == ["flashback", "flash-forward", "montage", "continuous", "", ""])

# ---- the two RULES (no model) -------------------------------------------------------------------------------------------------------------------
nc = fd.no_coverage(v)
check("rule D3: the second scene of a one-beat group may carry no extra angles; the first may", 3 in nc and 2 not in nc and "closer view" in nc[3], str(nc))
mont = fd.validate({**KEY, "scenes": [{**s, "time_mode": "montage"} if s["no"] in (2, 3) else s for s in KEY["scenes"]]}, ROWS, ROLES)
ncm = fd.no_coverage(mont)
check("rule D5: every scene inside a MONTAGE may carry no extra angles", 2 in ncm and 3 in ncm and "montage" in ncm[2] and 1 not in ncm and 4 not in ncm, str(ncm))
check("rules: no map / junk map -> no restrictions", fd.no_coverage(None) == {} and fd.no_coverage({}) == {} and fd.no_coverage({"scenes": "x"}) == {} and fd.no_coverage({"scenes": [None, {"no": "a"}]}) == {})
rt = fd.read_text(v, 3)
check("read_text: the director's read as lines, this scene marked, the turn and the carrier named", "Scene 3 (building, flashback)" in rt and "<== THIS SCENE" in rt and "THE TURN" in rt and "THE MESSAGE CARRIER" in rt and "given; do not redo it" in rt, rt)
check("read_text: no map -> empty", fd.read_text(None) == "" and fd.read_text({"scenes": []}) == "")

# ---- /film-direct, stubbed model -------------------------------------------------------------------------------------------------------------------
seen = {}
def fake_complete(messages, **kw):
    seen["messages"], seen["kw"], seen["n"] = messages, kw, seen.get("n", 0) + 1
    return seen.get("reply", "")
main.completion.complete = fake_complete
main.completion.has_key = lambda: True
def call_direct(**over):
    r = main.film_direct({"scenes": [dict(x) for x in ROWS], "seconds": SECS, "logline": "A mother lets a hem down.", "message": "One glass at a time.", "tone": "tender", "hero": "the pack", "house_id": "h1", "brand_mode": "grounded", **over})
    return r if isinstance(r, dict) else {"status": r.status_code, **json.loads(r.body)}
seen["reply"] = json.dumps(KEY)
r = call_direct()
check("route /film-direct: a good reply becomes a beat map with findings", r["model"] is True and len(r["scenes"]) == 6 and r["turn_scene"] == 4 and any(f["kind"] == "one-beat" for f in r["findings"]), str(r)[:300])
check("route /film-direct: called as a film call with the open house and brand mode; the planner's roles reach the prompt", seen["kw"].get("film") is True and seen["kw"].get("house_id") == "h1" and "planned job: hook" in seen["messages"][0]["content"] and "planned job: brand" in seen["messages"][0]["content"])
seen["reply"] = "Sure!\n```json\n" + json.dumps(KEY) + "\n```"
check("route /film-direct: a fenced reply works", call_direct()["turn_scene"] == 4)
seen["reply"] = "I cannot"
check("route /film-direct: an unreadable reply is a 502", call_direct().get("status") == 502 and "could not be understood" in call_direct()["detail"])
seen["reply"] = ""
check("route /film-direct: an empty reply is the same 502 every generator gives", call_direct().get("status") == 502)
main.completion.has_key = lambda: False
check("route /film-direct: no key is a 503", call_direct().get("status") == 503)
main.completion.has_key = lambda: True
check("route /film-direct: no scenes is a 400", call_direct(scenes=[]).get("status") == 400)

# ---- /scene-shots honours the rules and carries the director's read -------------------------------------------------------------------------------
GOODSHOTS = {"needs_coverage": True, "why": "A face is needed.", "shots": [{"job": "reaction", "why": "his face shows the sip landing", "camera_position": "Low at table height beside the glass.",
             "action": "The boy lifts the glass and looks into it.", "shot_size": "close", "camera": "slow push-in", "movement_class": "push-in", "secs": 2}]}
def call_shots(scene_no_, **over):
    row = dict(ROWS[scene_no_ - 1]); row.pop("shots", None)
    r = main.scene_shots({"scene": row, "scene_seconds": SECS[scene_no_ - 1], "pace": "fast", "beat_map": v, "house_id": "h1", **over})
    return r if isinstance(r, dict) else {"status": r.status_code, **json.loads(r.body)}
seen["reply"] = json.dumps(GOODSHOTS); seen["n"] = 0
r3 = call_shots(3)
check("rule D3 in /scene-shots: the closer view of a one-beat gets NO extra angles, and the model is not called", r3["shots"] == [] and r3["needs_coverage"] is False and "closer view" in r3["reason"] and seen["n"] == 0, str(r3))
r2 = call_shots(2)
check("/scene-shots: the first scene of that beat is proposed normally, and the model sees the director's read with THIS SCENE marked",
      len(r2["shots"]) == 1 and seen["n"] == 1 and "THE DIRECTOR'S READ OF THE FILM" in seen["messages"][0]["content"] and "<== THIS SCENE" in seen["messages"][0]["content"].split("DIRECTOR'S READ")[1], str(r2)[:200])
check("/scene-shots: with no beat map nothing changes (no director's read in the prompt, scene 3 is proposed)", len(call_shots(3, beat_map=None)["shots"]) == 1 and "DIRECTOR'S READ" not in seen["messages"][0]["content"])
rm = main.scene_shots({"scene": {k: x for k, x in ROWS[1].items() if k != "shots"}, "scene_seconds": 8, "pace": "fast", "beat_map": mont})
check("rule D5 in /scene-shots: a scene inside a montage returns none and says why", rm["shots"] == [] and "montage" in rm["reason"])

# ---- /film-review honours them too --------------------------------------------------------------------------------------------------------------------
ANS = {"summary": "ok", "time_passing": True, "turn_scene": 4, "carrier_scene": 6, "beats": [], "notes": [],
       "verdicts": [{"scene": 2, "shot": 2, "verdict": "keep", "reason": "the sip landing"}, {"scene": 3, "shot": 2, "verdict": "keep", "reason": "the glass is the object"}, {"scene": 4, "shot": 2, "verdict": "keep", "reason": "her face"}]}
seen["reply"] = json.dumps(ANS)
rr = main.film_review({"scenes": [dict(x) for x in ROWS], "seconds": SECS, "pace": "fast", "beat_map": v})
byv = {(x["scene"], x["shot"]): x for x in rr["verdicts"]}
check("rule D3 in /film-review: the extra shot on the second scene of a beat is cut with that reason even though the model kept it", byv[(3, 2)]["verdict"] == "cut" and byv[(3, 2)]["by"] == "pace" and "No extra angles here" in byv[(3, 2)]["reason"] and "closer view" in byv[(3, 2)]["reason"], str(byv[(3, 2)]))
check("... the first scene's shot and the turn's shot stay", byv[(2, 2)]["verdict"] == "keep" and byv[(4, 2)]["verdict"] == "keep")
check("... and the measured findings name it", any(f["kind"] == "no-coverage" and f["scene"] == 3 for f in rr["stats"]["findings"]), str(rr["stats"]["findings"]))
check("... and the model saw the director's read", "THE DIRECTOR'S READ OF THE FILM" in seen["messages"][0]["content"])
rr0 = main.film_review({"scenes": [dict(x) for x in ROWS], "seconds": SECS, "pace": "fast"})
check("/film-review with no beat map is unchanged (nothing cut by the rule)", all(x["verdict"] == "keep" for x in rr0["verdicts"]) and "DIRECTOR'S READ" not in seen["messages"][0]["content"])

# ---- the map is saved with the film ------------------------------------------------------------------------------------------------------------------
check("filmscript: video_beat_map is a saved field with an empty default", "video_beat_map" in filmscript.FIELDS and filmscript._blank("h")["video_beat_map"] is None)

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
