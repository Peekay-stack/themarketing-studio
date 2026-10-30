#!/usr/bin/env python
"""test_film_concept_delivery.py -- offline checks for Phase 3 (FILM_CONSOLIDATED_PLAN.md C6, C7): the director's read now checks that the script kept what the concept PROMISED (hook, surprise, turn,
memorable moment, each beat) and flags a scene that is a RUN of different quick actions; the shot planner then covers such a scene with one shot per action. The model is stubbed: no network, no credit,
nothing written to the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_film_concept_delivery.py
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import filmdirect as fd, sceneshots as ss, main

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

CONCEPT = {"hook": "A drop of milk rolls down a slanted steel plate.", "surprise": "She is running a lifetime of home purity tests.", "turn": "Her daughter-in-law sets the plate down.",
           "memorable": "She laughs and drinks the milk straight.", "stake": "She loses the one test she has trusted for fifty years.",
           "scenes": [{"t": "0-6s", "title": "The verdict", "desc": "A drop on a steel plate; a grandmother watches it."},
                      {"t": "6-15s", "title": "The tests", "desc": "Quick cuts: she smells it, watches it boil, holds it to light"}]}
ROWS = [{"no": 1, "tc": "0-6s", "visual": "A drop rolls down a plate; a grandmother watches."}, {"no": 2, "tc": "6-15s", "visual": "She sips and smells the milk."},
        {"no": 3, "tc": "15-24s", "visual": "Her daughter-in-law lowers the plate."}]
SECS = [6, 9, 9]

# ---- promises ------------------------------------------------------------------------------------------------------------------------------
pr = fd.promises(CONCEPT)
check("promises: the four moments then each beat, with ids the page and the server share", [p["id"] for p in pr] == ["hook", "surprise", "turn", "memorable", "beat1", "beat2"], [p["id"] for p in pr])
check("promises: labels and texts come from the concept (the model never supplies them); a beat keeps its time and title", pr[0]["label"] == "Hook" and pr[3]["label"] == "Memorable moment"
      and pr[5]["label"] == "Beat 2 (6-15s)" and "Quick cuts" in pr[5]["text"] and pr[5]["text"].startswith("The tests"), pr[5])
check("promises: the stake is NOT a promise to film (it is what the film must make felt)", all(p["id"] != "stake" for p in pr))
check("promises: no concept, an older concept, junk -> only what exists, never raises", fd.promises(None) == [] and fd.promises("x") == [] and [p["id"] for p in fd.promises({"scenes": [{"title": "a", "desc": "b"}]})] == ["beat1"])

# ---- the prompt --------------------------------------------------------------------------------------------------------------------------
p0 = fd.build_prompt(rows=ROWS, seconds=SECS, logline="x")
p1 = fd.build_prompt(rows=ROWS, seconds=SECS, logline="x", concept=CONCEPT)
check("prompt with a concept: lists every promise by id and asks for a status per promise", "WHAT THE CONCEPT PROMISED" in p1 and "[hook]" in p1 and "[beat2] Beat 2 (6-15s)" in p1 and "11. `concept`" in p1
      and "`flattened`" in p1 and "`missing`" in p1 and '"concept":[{"id":"hook"' in p1)
check("prompt without a concept: no promise section, no item 11, no concept in the JSON shape", "WHAT THE CONCEPT PROMISED" not in p0 and "11. `concept`" not in p0 and '"concept":' not in p0)
check("prompt (both): asks for `sequence` and `actions`, tells a montage apart, and the JSON shape carries them", "10. `sequence` and `actions`" in p0 and "`montage`, not a sequence" in p0 and '"sequence":false,"actions":[]' in p0 and '"sequence":false,"actions":[]' in p1)
check("prompt: the original items 1-9 and the ENGAGEMENT paragraph are all still there", all(f"{i}. `" in p0 for i in range(1, 10)) and "ENGAGEMENT. A film must be ENTERTAINING" in p0 and p0.rstrip().endswith("}"))
try:
    json.loads(p0[p0.index('{"summary"'):]); json.loads(p1[p1.index('{"summary"'):])
    shape_ok = True
except ValueError as e:
    shape_ok = False
check("prompt: the JSON shape at the end is valid JSON, with and without a concept", shape_ok)

# ---- validate: concept delivery -----------------------------------------------------------------------------------------------------
def raw(**over):
    base = {"summary": "s", "turn_scene": 3, "carrier_scene": 3, "scenes": [
        {"no": 1, "purpose": "hook", "intensity": 1, "place": "kitchen", "energy": 2, "change": "learns", "beat": "a"},
        {"no": 2, "purpose": "tests", "intensity": 2, "place": "kitchen", "energy": 1, "change": "x", "beat": "b", "sequence": True, "actions": ["smells the milk", "watches it boil", "holds it to the light"]},
        {"no": 3, "purpose": "turn", "intensity": 3, "place": "kitchen", "energy": 2, "change": "y", "beat": "c"}]}
    base.update(over); return base
P = fd.promises(CONCEPT)
ans = [{"id": "hook", "status": "delivered", "scene": 1, "note": ""}, {"id": "surprise", "status": "missing", "scene": 2, "note": "only one test is shown"},
       {"id": "turn", "status": "delivered", "scene": 3}, {"id": "memorable", "status": "flattened", "scene": 3, "note": "she drinks but does not laugh"},
       {"id": "beat1", "status": "delivered", "scene": 1}, {"id": "beat2", "status": "flattened", "scene": 2, "note": "three actions shown as one still shot"},
       {"id": "nope", "status": "missing", "scene": 1}, {"id": "hook", "status": "missing", "scene": 1}]
v = fd.validate(raw(concept=ans), ROWS, {}, P)
d = {e["id"]: e for e in v["concept_delivery"]}
check("validate: one delivery entry per promise answered, in the concept's order, with the SERVER's label and text; unknown ids and a repeated id are ignored",
      [e["id"] for e in v["concept_delivery"]] == ["hook", "surprise", "turn", "memorable", "beat1", "beat2"] and d["beat2"]["label"] == "Beat 2 (6-15s)" and d["hook"]["status"] == "delivered", v["concept_delivery"])
check("validate: a missing promise has no scene even if the model named one; a flattened one keeps its scene and note", d["surprise"]["scene"] is None and d["beat2"]["scene"] == 2 and "one still shot" in d["beat2"]["note"])
kinds = [f["kind"] for f in v["findings"]]
check("validate: the concept findings come FIRST (flattened and missing), delivered ones make none", kinds[:3] == ["concept-missing", "concept-flattened", "concept-flattened"] and kinds.count("concept-flattened") + kinds.count("concept-missing") == 3, kinds)
check("validate: a finding names the promise in words and quotes it", "surprise" in v["findings"][0]["note"].lower() and "lifetime" in v["findings"][0]["note"] and "missing" in v["findings"][0]["note"], v["findings"][0]["note"])
check("validate: three concept findings make the film's risk HIGH", v["engagement"]["risk"] == "high", v["engagement"])
same = fd.validate(raw(concept=[{"id": "turn", "status": "flattened", "scene": 3, "note": "a"}, {"id": "memorable", "status": "flattened", "scene": 3, "note": "b"}, {"id": "beat3", "status": "flattened", "scene": 3, "note": "c"}]),
                   ROWS, {}, fd.promises({**CONCEPT, "scenes": CONCEPT["scenes"] + [{"title": "x", "desc": "y"}]}))
check("validate: three findings that all sit on the SAME scene (one root cause) are all listed but count once towards the risk (medium, not high)",
      sum(1 for f in same["findings"] if f["kind"].startswith("concept")) == 3 and same["engagement"]["risk"] == "medium", (same["engagement"], [f["kind"] for f in same["findings"]]))
one = fd.validate(raw(concept=[{"id": "turn", "status": "flattened", "scene": 3, "note": "n"}]), ROWS, {}, P)
check("validate: one flattened promise alone makes the risk MEDIUM, and the promises not answered are counted in a note", one["engagement"]["risk"] == "medium" and any("answered for 1 of the concept's 6" in n for n in one["notes"]), (one["engagement"], one["notes"]))
none = fd.validate(raw(concept=[{"id": "hook", "status": "delivered", "scene": 1}] * 1), ROWS, {}, P)
check("validate: nothing flattened or missing -> risk is whatever the engagement checks say (here low) and no concept finding", none["engagement"]["risk"] == "low" and not any(f["kind"].startswith("concept") for f in none["findings"]))
bad = fd.validate(raw(concept=[{"id": "hook", "status": "great", "scene": 1}, "junk", {"id": "turn"}, {"id": "memorable", "status": "MISSING", "scene": 99}]), ROWS, {}, P)
check("validate: an unreadable status is not a finding; a status in capitals still reads; a scene that does not exist becomes none", [e["id"] for e in bad["concept_delivery"]] == ["memorable"] and bad["concept_delivery"][0]["scene"] is None)
plain = fd.validate(raw(), ROWS, {})
check("validate without promises: no concept_delivery key and no concept finding (as before)", "concept_delivery" not in plain and not any(f["kind"].startswith("concept") for f in plain["findings"]))
check("validate: a model that sends no concept array for a film with promises says so and finds nothing", fd.validate(raw(), ROWS, {}, P)["concept_delivery"] == [] and any("answered for 0" in n for n in fd.validate(raw(), ROWS, {}, P)["notes"]))
check("validate: garbage never raises", fd.validate({"concept": "x"}, ROWS, {}, P)["concept_delivery"] == [] and fd.validate(None, ROWS, {}, P)["scenes"] != [])

# ---- validate: sequence -------------------------------------------------------------------------------------------------------------------
sc = {s["no"]: s for s in v["scenes"]}
check("sequence: a scene with two or more actions is a sequence and keeps them in order", sc[2]["sequence"] is True and sc[2]["actions"] == ["smells the milk", "watches it boil", "holds it to the light"], sc[2])
check("sequence: scenes the model did not flag are not sequences", sc[1]["sequence"] is False and sc[1]["actions"] == [])
one_act = fd.validate(raw(scenes=[{"no": 2, "sequence": True, "actions": ["only one"]}]), ROWS, {})
check("sequence: a 'run' of ONE action is not a run; flagged without actions is not a run", {s["no"]: s for s in one_act["scenes"]}[2]["sequence"] is False
      and {s["no"]: s for s in fd.validate(raw(scenes=[{"no": 2, "sequence": True}]), ROWS, {})["scenes"]}[2]["sequence"] is False)
mont = fd.validate(raw(scenes=[{"no": 2, "time_mode": "montage", "sequence": True, "actions": ["a", "b"]}]), ROWS, {})
check("sequence: a montage (time passing by repetition) is never a sequence", {s["no"]: s for s in mont["scenes"]}[2]["sequence"] is False)
many = fd.validate(raw(scenes=[{"no": 2, "sequence": True, "actions": ["a" * 200, "b", "c", "d", "e", ""]}]), ROWS, {})
check("sequence: at most four actions, each clipped", len({s["no"]: s for s in many["scenes"]}[2]["actions"]) == 4 and all(len(a) <= 61 for a in {s["no"]: s for s in many["scenes"]}[2]["actions"]))

# ---- sequences() and the text other prompts read ------------------------------------------------------------------------------------------
check("sequences(): {scene: actions} for sequence scenes only; none for a montage or a one-action scene", fd.sequences(v) == {2: ["smells the milk", "watches it boil", "holds it to the light"]} and fd.sequences(None) == {} and fd.sequences({"scenes": "x"}) == {})
check("read_text: a sequence scene is marked with its actions for the planner and the flow review", "A RUN OF QUICK ACTIONS: smells the milk; watches it boil; holds it to the light" in fd.read_text(v, 2) and "A RUN OF QUICK ACTIONS" not in fd.read_text(mont, 2))
check("no_coverage: a sequence scene is NOT held to one shot by the director's rules (only a montage or a closer view is)", 2 not in fd.no_coverage(v))

# ---- the planner ---------------------------------------------------------------------------------------------------------------------------
check("budget: 'sequence' is exempt from the pace minimum like the hook and the turn (a 4 s sequence scene may be covered at Calm pace; a 4 s ordinary scene may not)",
      ss.budget(4, "calm", "sequence") == 1 and ss.budget(5, "standard", "sequence") == 1 and ss.budget(5, "standard", "") == 0 and ss.budget(4, "standard", "build") == 0)
row = {"no": 2, "visual": "She sips and smells the milk.", "camera": "medium"}
sp = ss.build_prompt(row=row, secs=6, n_extras=2, sequence_actions=["smells the milk", "watches it boil", "holds it to the light"], role="sequence")
check("planner prompt: a sequence scene is told its actions in order, that an empty list is wrong, and to give each later action its own shot", "A RUN OF DIFFERENT QUICK ACTIONS, in this order: 1. smells the milk; 2. watches it boil; 3. holds it to the light" in sp
      and "an empty list is the WRONG answer" in sp and "Give each LATER action its own extra shot" in sp and "never the same action from a new angle" in sp
      and "a real `shot_size`" in sp and "never \"none\"" in sp and "`detail` or `close`" in sp, sp[sp.index("THE SCENE"):][:900])
check("planner prompt: the plain role word 'sequence' is not shown as the scene's job", "This scene's job in the film: sequence" not in sp)
sp0 = ss.build_prompt(row=row, secs=6, n_extras=2)
check("planner prompt without actions: exactly as before (no sequence block)", "A RUN OF DIFFERENT QUICK ACTIONS" not in sp0 and "FIRST DECIDE WHETHER THIS SCENE NEEDS ANY EXTRA SHOT" in sp0)

# ---- the routes, with a stubbed model ---------------------------------------------------------------------------------------------------------
seen = {}
def fake_complete(messages, **kw):
    seen["messages"], seen["kw"] = messages, kw
    return seen.get("reply", "")
main.completion.complete = fake_complete
main.completion.has_key = lambda: True
seen["reply"] = json.dumps(raw(concept=ans))
r = main.film_direct({"scenes": ROWS, "seconds": SECS, "logline": "A grandmother's tests.", "concept": CONCEPT, "house_id": "h1"})
r = r if isinstance(r, dict) else {"status": r.status_code, **json.loads(r.body)}
check("route /film-direct: the concept reaches the model prompt and the answer comes back checked", "WHAT THE CONCEPT PROMISED" in seen["messages"][0]["content"] and len(r.get("concept_delivery", [])) == 6 and r["engagement"]["risk"] == "high", str(r)[:300])
r2 = main.film_direct({"scenes": ROWS, "seconds": SECS, "logline": "x"})
check("route /film-direct: with no concept sent it behaves as before (no promise section, no concept_delivery)", "WHAT THE CONCEPT PROMISED" not in seen["messages"][0]["content"] and "concept_delivery" not in r2)
r3 = main.film_direct({"scenes": ROWS, "seconds": SECS, "concept": "not a dict"})
check("route /film-direct: a concept that is not an object is ignored, not an error", isinstance(r3, dict) and "concept_delivery" not in r3)

GOODSHOTS = {"needs_coverage": True, "why": "The scene is a run of three actions.", "shots": [
    {"job": "insert", "why": "the second action: she watches the milk boil", "camera_position": "A low camera beside the pot, looking up at the rising foam.", "action": "The milk climbs towards the rim of the pot.", "shot_size": "detail", "camera": "locked-off", "movement_class": "static", "secs": 2},
    {"job": "reveal", "why": "the third action: she holds it to the light", "camera_position": "Over her shoulder towards the window.", "action": "She lifts the glass to the window light and squints.", "shot_size": "over", "camera": "locked-off", "movement_class": "static", "secs": 2}]}
def call(**over):
    p = {"scene": dict(row), "scene_seconds": 6, "logline": "A grandmother's tests.", "house_id": "h1", "brand_mode": "grounded", "pace": "calm", **over}
    out = main.scene_shots(p)
    return out if isinstance(out, dict) else {"status": out.status_code, **json.loads(out.body)}
seen["reply"] = json.dumps(GOODSHOTS); seen["messages"] = None
held = call(scene_seconds=5)
check("route /scene-shots: at Calm pace a 5 s ordinary scene is held as one shot and the model is not called (as before)", held["shots"] == [] and seen["messages"] is None, str(held)[:200])
seen["messages"] = None
seq = call(scene_seconds=5, beat_map=v)
check("route /scene-shots: the same 5 s scene, read as a run of quick actions, IS planned: the model is called with the actions and the planner returns shots",
      seen["messages"] is not None and "A RUN OF DIFFERENT QUICK ACTIONS" in seen["messages"][0]["content"] and "holds it to the light" in seen["messages"][0]["content"] and len(seq["shots"]) >= 1 and seq["needs_coverage"] is True, str(seq)[:300])
check("route /scene-shots: the director's read text in the prompt marks the scene as a run too", "A RUN OF QUICK ACTIONS" in seen["messages"][0]["content"])
seen["messages"] = None
montage_map = {**v, "scenes": [{**s, "time_mode": "montage"} if s["no"] == 2 else s for s in v["scenes"]]}
mm = call(scene_seconds=5, beat_map=montage_map)
check("route /scene-shots: a montage scene still gets NO extra angles (the montage rule wins over a sequence flag)", mm["shots"] == [] and "montage" in (mm.get("reason") or "") and seen["messages"] is None, str(mm)[:200])
seen["messages"] = None
hook_seq = call(scene_seconds=5, role="hook", beat_map=v)
check("route /scene-shots: a hook scene that is also a sequence is still planned (the role stays hook; the actions still reach the prompt)", seen["messages"] is not None and "A RUN OF DIFFERENT QUICK ACTIONS" in seen["messages"][0]["content"]
      and "This scene's job in the film: hook" in seen["messages"][0]["content"], str(hook_seq)[:200])

# ---- the flow review must not cut the cover the proposer made for a run of quick actions ----------------------------------------------------------
import flowreview as fr
FR_ROWS = [{"no": 1, "tc": "0-6s", "visual": "A drop rolls down a plate."},
           {"no": 2, "tc": "6-11s", "visual": "She smells the milk, watches it boil, holds it to light.", "shots": [{"visual": "The milk climbs the pot.", "secs": 2, "job": "insert", "why": "the boil", "shot_size": "detail"}]},
           {"no": 3, "tc": "11-17s", "visual": "Her daughter lowers the plate."}, {"no": 4, "tc": "17-23s", "visual": "She laughs and drinks."}, {"no": 5, "tc": "23-29s", "visual": "The pack stands on the counter."}]
FR_SECS = [6, 5, 6, 6, 6]       # scene 2 is a plain middle scene here (its plan role is `world`), so the pace minimum applies to it
SEQ = {2: ["smells", "boils", "light"]}
check("flowreview.budgets: a 5 s scene at Standard pace has no budget (as before) but a run-of-actions scene may carry one extra", fr.budgets(FR_ROWS, FR_SECS, "standard")[2] == 0 and fr.budgets(FR_ROWS, FR_SECS, "standard", seq=SEQ)[2] == 1)
check("flowreview.budgets: a hook or turn scene that is also a run keeps its own role (not changed)", fr.budgets(FR_ROWS, FR_SECS, "standard", roles={2: "hook"}, seq=SEQ)[2] == 1 and fr.budgets(FR_ROWS, FR_SECS, "standard", turn=2, seq=SEQ)[2] == 1)
check("flowreview.budgets: a montage / one-beat scene (no_cover) still gets none even when flagged as a run", fr.budgets(FR_ROWS, FR_SECS, "standard", no_cover={2: "montage"}, seq=SEQ)[2] == 0)
st_no = fr.stats(FR_ROWS, FR_SECS, "standard")
st_seq = fr.stats(FR_ROWS, FR_SECS, "standard", seq=SEQ)
check("flowreview.stats: WITHOUT the run flag the extra shot is reported over budget (the old behaviour); WITH it there is no over-budget finding", any(f["kind"] == "over-budget" and f["scene"] == 2 for f in st_no["findings"])
      and not any(f["kind"] == "over-budget" for f in st_seq["findings"]), [f["kind"] for f in st_seq["findings"]])
REVIEW = {"summary": "s", "turn_scene": 3, "carrier_scene": 3, "beats": [], "notes": [], "verdicts": [{"scene": 2, "shot": 2, "verdict": "keep", "reason": "the boil is a different action"}]}
seen["reply"] = json.dumps(REVIEW)
def review(**over):
    out = main.film_review({"scenes": FR_ROWS, "seconds": FR_SECS, "pace": "standard", "house_id": "h1", **over})
    return out if isinstance(out, dict) else {"status": out.status_code, **json.loads(out.body)}
r_plain = review()
r_seq = review(beat_map=v)
vd = lambda r: [x for x in r["verdicts"] if x["scene"] == 2][0]
check("route /film-review: with no run flag the pace rule cuts the extra shot on a 5 s Standard scene (as before)", vd(r_plain)["verdict"] == "cut" and vd(r_plain).get("by") == "pace", str(vd(r_plain)))
check("route /film-review: with the director's read marking scene 2 a run of quick actions the review KEEPS the shot the proposer made", vd(r_seq)["verdict"] == "keep" and not any(f["kind"] == "over-budget" for f in r_seq["stats"]["findings"]), str(vd(r_seq)) + str(r_seq["stats"]["findings"]))

# ---- the quiet opening that IS the concept's hook (G3) ---------------------------------------------------------------------------------------------
quiet = raw(scenes=[{"no": 1, "purpose": "hook", "intensity": 1, "place": "kitchen", "energy": 1, "change": "learns", "beat": "a"}, {"no": 2, "purpose": "tests", "intensity": 2, "place": "lab", "energy": 2, "change": "x", "beat": "b"},
                    {"no": 3, "purpose": "turn", "intensity": 3, "place": "street", "energy": 2, "change": "y", "beat": "c"}])
hook_ok = fd.validate({**quiet, "concept": [{"id": "hook", "status": "delivered", "scene": 1}]}, ROWS, {}, P)
sh = [f for f in hook_ok["findings"] if f["kind"] == "slow-hook"]
check("slow-hook: when the concept's hook is delivered in scene 1 the finding says the quiet opening is a choice, names the hook, keeps the finding and flags it by design",
      len(sh) == 1 and sh[0].get("by_design") is True and "chosen hook" in sh[0]["note"] and "drop of milk" in sh[0]["note"] and "a choice, not a miss" in sh[0]["note"], sh)
check("slow-hook by design still counts toward the risk: the risk is exactly what the same read gives with no promises at all (only the wording changed)", hook_ok["engagement"]["risk"] == fd.validate(quiet, ROWS, {})["engagement"]["risk"] and hook_ok["engagement"]["risk"] != "low", hook_ok["engagement"])
hook_late = fd.validate({**quiet, "concept": [{"id": "hook", "status": "delivered", "scene": 2}]}, ROWS, {}, P)
hook_flat = fd.validate({**quiet, "concept": [{"id": "hook", "status": "flattened", "scene": 1, "note": "weaker"}]}, ROWS, {}, P)
hook_none = fd.validate(quiet, ROWS, {})
plain_note = [f for f in hook_none["findings"] if f["kind"] == "slow-hook"][0]["note"]
check("slow-hook: the generic warning stays when the hook is delivered in another scene, flattened, or when there are no promises at all",
      all("by_design" not in f and "a choice, not a miss" not in f["note"] for r_ in (hook_late, hook_flat, hook_none) for f in r_["findings"] if f["kind"] == "slow-hook") and "must earn the next five" in plain_note, plain_note)
# ---- the director's read is told a scene's own place ----------------------------------------------------------------------------------------------------
pp = fd.build_prompt(rows=[{"no": 1, "tc": "0-6s", "visual": "A boy drinks."}, {"no": 2, "tc": "6-12s", "visual": "A technician reads a vial.", "place": "A dairy lab at dawn"}], seconds=[6, 6])
check("director's read prompt: a scene with its own place is given 'set in: <place>', a scene without one is not", "SCENE 2 (6 s): A technician reads a vial. | set in: A dairy lab at dawn" in pp and "SCENE 1 (6 s): A boy drinks.\n" in pp and "set in:" not in pp.split("SCENE 2")[0], pp[pp.index("THE SCRIPT"):][:300])
print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
