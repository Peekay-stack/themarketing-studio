#!/usr/bin/env python
"""test_flow_review.py -- offline checks for craft slice 2: flowreview.py (facts, prompt, parsing, backstops) and POST /film-review with a stubbed model.
The film below is a neutral, brand-free six-scene family story shaped like the one the owner rejected on 28 Oct (a memory shown at two scales, a shoulder shot that
adds nothing, a run of drinking shots, 14 shots in 30 s, an opted-in pack sign-off). No network, no credit, nothing written to the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_flow_review.py
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import flowreview as fr, sceneshots as ss, filmcut, main

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

def S(visual, size, secs=2, job="reveal", why="adds something the master does not show", **k):
    return {"visual": visual, "shot_size": size, "secs": secs, "job": job, "why": why, **k}

def film():
    return [
        {"no": 1, "visual": "A mother measures a boy's trousers at the hem.", "shot_size": "medium", "audio": [{"kind": "vo", "text": "Every day he grew."}],
         "shots": [S("Detail of the hem pressed down.", "detail", 2, "insert", "the hem is the object the story turns on")]},
        {"no": 2, "visual": "Long ago, the boy drinks a glass of milk at the counter.", "shot_size": "wide", "audio": [{"kind": "vo", "text": "Glass by glass."}],
         "shots": [S("Close on the boy's face as he sips.", "close", 2, "reaction", "his face shows the sip landing"),
                   S("His hand around the steel glass.", "detail", 2, "insert", "the glass is the object"),
                   S("The boy drinks again from the other side.", "medium", 2, "reveal", "another angle")]},
        {"no": 3, "visual": "The boy drinks a glass of milk at the counter, closer.", "shot_size": "close", "audio": [{"kind": "vo", "text": "Month after month."}],
         "shots": [S("Over the shoulder as he drinks.", "over", 2, "reveal", "another angle on the drink"),
                   S("Tight on his hands and the glass.", "detail", 2, "insert", "the glass again")]},
        {"no": 4, "visual": "The mother lets the hem down and gasps; it still falls short.", "shot_size": "medium", "audio": [{"kind": "vo", "text": "And one morning."}],
         "shots": [S("Her face as she realises.", "close", 3, "reaction", "the realisation lands on her face")]},
        {"no": 5, "visual": "The boy stands tall in the trousers; they fit.", "shot_size": "wide", "audio": [{"kind": "vo", "text": "It fit."}],
         "shots": [S("Over the shoulder at the boy in the mirror.", "over", 2, "reveal", "another angle")]},
        {"no": 6, "visual": "The pack stands beside a glass on the counter.", "shot_size": "medium", "beat_role": "brand", "signoff_shots": True, "audio": [{"kind": "vo", "text": "One glass at a time."}],
         "shots": [S("A hand lifts the glass beside the pack.", "close", 2, "insert", "life around the pack"),
                   S("The pack, square to camera, clean.", "product", 2, "payoff-hold", "the message carrier")]},
    ]
SECS = [6, 8, 6, 6, 4, 6]; ROWS = film()
ROLES = {1: "hook", 2: "world", 3: "mechanism", 4: "turn", 5: "turn", 6: "brand"}

# ---- film_shots -----------------------------------------------------------------------------------------------------------------
sh = fr.film_shots(ROWS, SECS, ROLES)
check("film_shots: every scene's master plus its active extras (6 + 10 = 16)", len(sh) == 16 and sum(1 for s in sh if s["place"] is None) == 6, str(len(sh)))
check("film_shots: the masters keep what the extras leave; the film's seconds are unchanged", sum(s["secs"] for s in sh) == sum(SECS) == 36, str(sum(s["secs"] for s in sh)))
check("film_shots: board numbers are 1 for the master and 2.. for extras by place", [s["shot"] for s in sh if s["scene"] == 2] == [1, 2, 3, 4])
sk = film(); sk[1]["shots"][0]["skip"] = True
ssk = fr.film_shots(sk, SECS, ROLES)
check("film_shots: a SKIPPED shot is not in the cut and the others keep their board numbers (2 gone, 3 and 4 stay)", [s["shot"] for s in ssk if s["scene"] == 2] == [1, 3, 4] and len(ssk) == 15)
check("film_shots: nothing mutated", ROWS[1]["shots"][0].get("skip") is None)
check("film_shots: garbage rows never raise; only real rows count", fr.film_shots(None, None) == [] and len(fr.film_shots([None, "x", {"visual": "a"}], [3, 3, 3])) == 1)

# ---- stats / findings --------------------------------------------------------------------------------------------------------------
st = fr.stats(ROWS, SECS, "calm", ROLES)
kinds = [f["kind"] for f in st["findings"]]
check("stats: 16 shots in 36 s is flagged as too fast for Calm (4.4 per 10 s vs 2-2.5)", st["shots"] == 16 and st["per10"] == 4.4 and "cut-rate" in kinds, str(st))
check("stats: Fast pace does not flag that cut rate (4.4 is inside 3.5-5)", "cut-rate" not in [f["kind"] for f in fr.stats(ROWS, SECS, "fast", ROLES)["findings"]])
check("stats: scenes over their pace budget are named (Calm allows 1 extra: scene 2 has 3, scene 3 has 2)", sorted(f["scene"] for f in st["findings"] if f["kind"] == "over-budget") == [2, 3, 6], str(st["findings"]))
fit = fr.stats([{"no": 1, "visual": "a", "shots": [S("b", "close"), S("c", "detail"), S("d", "over")]}, {"no": 2, "visual": "end"}], [4, 4], "fast", {})
check("stats: 3 extras in a 4 s scene -> 'does not fit' (it holds 1)", any(f["kind"] == "does-not-fit" and f["scene"] == 1 for f in fit["findings"]), str(fit["findings"]))
run = fr.stats([{"no": i, "visual": "x", "shot_size": "medium"} for i in range(1, 5)], [4, 4, 4, 4], "standard", {})
check("stats: four same-size shots in a row are flagged as the same picture again", run["longest_same_size_run"] == 4 and any(f["kind"] == "same-size-run" for f in run["findings"]), str(run))
same = fr.stats([{"no": i, "visual": "x", "shot_size": s_} for i, s_ in zip(range(1, 7), ("wide", "close", "wide", "close", "wide", "close"))], [4] * 6, "standard", {})
check("stats: six shots of identical length are flagged (length should follow intensity)", any(f["kind"] == "same-length" for f in same["findings"]), str(same["findings"]))
nojob = film(); nojob[3]["shots"][0].pop("job")
check("stats: an extra shot with no job is flagged", any(f["kind"] == "no-job" and f["scene"] == 4 for f in fr.stats(nojob, SECS, "fast", ROLES)["findings"]))
badend = film(); badend[5]["shots"][1]["shot_size"] = "close"
check("stats: an opted-in sign-off whose last shot is not the product hero is flagged", any(f["kind"] == "signoff-last" for f in fr.stats(badend, SECS, "fast", ROLES)["findings"]))
check("stats: the good ending is not flagged", not any(f["kind"] == "signoff-last" for f in fr.stats(ROWS, SECS, "fast", ROLES)["findings"]))
clean = fr.stats([{"no": 1, "visual": "a", "shot_size": "wide"}, {"no": 2, "visual": "b", "shot_size": "close"}, {"no": 3, "visual": "c", "shot_size": "medium"}], [5, 6, 4], "calm", {})
check("stats: a short, calm, varied film has no findings", clean["findings"] == [], str(clean))
check("stats: empty film is safe", fr.stats([], [], "calm", {})["shots"] == 0 and fr.stats(None, None, "", None)["shots"] == 0)

# ---- build_prompt -----------------------------------------------------------------------------------------------------------------------
pr = fr.build_prompt(rows=ROWS, seconds=SECS, shots=sh, st=st, logline="A mother lets a hem down, glass by glass.", message="One glass at a time.", tone="tender, unhurried", pace="calm",
                     characters="Mother, boy", roles=ROLES)
check("prompt: carries the logline, the message, the tone and the pace", "glass by glass" in pr and "One glass at a time." in pr and "tender, unhurried" in pr and "ITS PACE: Calm" in pr)
check("prompt: lists EVERY shot in order with its scene, job, seconds and size", pr.count("  shot ") == 16 and "SCENE 2 (8 s" in pr and "[reaction, 2 s, close]" in pr and "[master, 4 s, medium]" in pr, pr[-1500:])
check("prompt: carries the measured facts", "16 shots in 36 s" in pr and "4.4 shots per 10 s" in pr)
check("prompt: asks for beats (repetition = one beat, time passing = variation), the turn and the carrier",
      "ONE beat shown at two scales" in pr and "`time_passing` is true" in pr and "MEANING" in pr and "TURN" in pr and "MESSAGE CARRIER" in pr)
check("prompt: asks for a verdict on EVERY extra shot with the 'what would the viewer lose' test and a protected closing shot",
      "VERDICT on EVERY extra shot" in pr and "what would the viewer lose" in pr and "Never cut the shot the film ends on" in pr)
check("prompt: the scene roles reach the model", "job in the film: turn" in pr and "job in the film: brand" in pr)
check("prompt: no brand word anywhere in the rules (the film's own data only)", "heritage" not in pr.lower() and "dairy" not in pr.lower() and "milk" in pr.lower())

# ---- parse -------------------------------------------------------------------------------------------------------------------------------
ANS = {"summary": "Scenes 2 and 3 are one moment twice; the film is over-cut for its tone.", "time_passing": True, "turn_scene": 4, "carrier_scene": 6,
       "beats": [{"scenes": [2, 3], "purpose": "the memory, glass by glass", "repetition": True}, {"scenes": [4], "purpose": "the realisation", "repetition": False}],
       "verdicts": [{"scene": 1, "shot": 2, "verdict": "keep", "reason": "the hem detail carries the story"},
                    {"scene": 2, "shot": 2, "verdict": "keep", "reason": "the sip landing on a face"},
                    {"scene": 2, "shot": 3, "verdict": "cut", "reason": "the glass again, nothing new"},
                    {"scene": 2, "shot": 4, "verdict": "merge", "merge_with": "scene 3 shot 2", "reason": "the same drink from another side"},
                    {"scene": 3, "shot": 2, "verdict": "cut", "reason": "scene 3 is already the closer view of scene 2"},
                    {"scene": 3, "shot": 3, "verdict": "cut", "reason": "the glass a third time"},
                    {"scene": 4, "shot": 2, "verdict": "keep", "reason": "the realisation lands on her face"},
                    {"scene": 5, "shot": 2, "verdict": "cut", "reason": "a shoulder shot that adds nothing"},
                    {"scene": 6, "shot": 2, "verdict": "keep", "reason": "life around the pack"},
                    {"scene": 6, "shot": 3, "verdict": "cut", "reason": "no reason it should stay"}],
       "notes": [{"scenes": [2, 3], "kind": "repetition", "note": "Scenes 2 and 3 show one moment at two scales.", "suggestion": "Show time passing with variations instead."}]}
check("parse: plain / fenced / with chatter", fr.parse(json.dumps(ANS))["time_passing"] is True and fr.parse("Sure:\n```json\n" + json.dumps(ANS) + "\n```")["turn_scene"] == 4)
check("parse: garbage / empty / a bare list -> None", fr.parse("nope") is None and fr.parse("") is None and fr.parse("[1,2]") is None)

# ---- validate ---------------------------------------------------------------------------------------------------------------------------------
v = fr.validate(ANS, sh)
byk = {(x["scene"], x["shot"]): x for x in v["verdicts"]}
check("validate: exactly one verdict per extra shot (10)", len(v["verdicts"]) == 10 and len(byk) == 10, str(len(v["verdicts"])))
part = fr.validate({**ANS, "verdicts": [x for x in ANS["verdicts"] if (x["scene"], x["shot"]) != (5, 2)]}, sh)
pk = {(x["scene"], x["shot"]): x for x in part["verdicts"]}
check("validate: a shot the review did not mention is KEPT and says so (never cut by silence)", len(part["verdicts"]) == 10 and pk[(5, 2)]["verdict"] == "keep" and "Not singled out" in pk[(5, 2)]["reason"] and (5, 2) not in [(s["scene"], s["shot"]) for s in part["skips"]])
check("validate: the closing product shot is NEVER cut, even when the model says cut (and it is reported)", byk[(6, 3)]["verdict"] == "keep" and any("closing pack shot" in n for n in v["notes_out"]), str(byk[(6, 3)]))
check("validate: skips = the cut and merge verdicts only, each with its place", [(s["scene"], s["shot"], s["place"]) for s in v["skips"]] == [(2, 3, 1), (2, 4, 2), (3, 2, 0), (3, 3, 1), (5, 2, 0)], str(v["skips"]))
check("validate: merge keeps what it merges with", byk[(2, 4)]["verdict"] == "merge" and byk[(2, 4)]["merge_with"] == "scene 3 shot 2")
check("validate: beats, notes, the turn and the carrier are read", v["time_passing"] is True and v["turn_scene"] == 4 and v["carrier_scene"] == 6 and v["beats"][0]["scenes"] == [2, 3] and v["beats"][0]["repetition"] is True and len(v["notes"]) == 1)
bad = fr.validate({"verdicts": [{"scene": 9, "shot": 9, "verdict": "cut", "reason": "no such shot at all"}, {"scene": 2, "shot": 2, "verdict": "cut", "reason": ""},
                                {"scene": 2, "shot": 3, "verdict": "destroy", "reason": "whatever it is"}], "turn_scene": 99}, sh)
bb = {(x["scene"], x["shot"]): x for x in bad["verdicts"]}
check("validate: a verdict for a shot that does not exist is ignored (and reported)", len(bad["verdicts"]) == 10 and any("scene 9 shot 9" in n for n in bad["notes_out"]))
check("validate: a cut with no reason, or an unknown verdict, is kept (never silently applied)", bb[(2, 2)]["verdict"] == "keep" and bb[(2, 3)]["verdict"] == "keep" and bad["skips"] == [])
check("validate: a turn scene that is not in the film is dropped", bad["turn_scene"] is None)
check("validate: garbage never raises", fr.validate(None, sh)["skips"] == [] and len(fr.validate({"verdicts": "x", "beats": 3, "notes": [None]}, sh)["verdicts"]) == 10 and fr.validate({}, [])["verdicts"] == [])

# ---- the pace budget is a RULE: the surplus is cut however many the model kept ------------------------------------------------------------------
ALLKEEP = {"verdicts": [{"scene": s["scene"], "shot": s["shot"], "verdict": "keep", "reason": "it is fine"} for s in sh if s["place"] is not None]}
bud = fr.budgets(ROWS, SECS, "calm", ROLES)
check("budgets: per scene under Calm (hook scene 1 -> 1, an 8 s scene -> 1, a 4 s scene -> 0 unless hook/turn)", bud[1] == 1 and bud[2] == 1 and bud[3] == 1 and bud[5] in (0, 1), str(bud))
vb = fr.validate(ALLKEEP, sh, bud, "calm")
kept_by_scene = {}
for x in vb["verdicts"]:
    if x["verdict"] == "keep":
        kept_by_scene[x["scene"]] = kept_by_scene.get(x["scene"], 0) + 1
check("pace backstop: a scene never keeps more extras than its budget, whatever the model said", all(kept_by_scene.get(no, 0) <= max(bud.get(no, 0), 1 if no == 6 else 0) for no in bud), str(kept_by_scene) + str(bud))
bb2 = {(x["scene"], x["shot"]): x for x in vb["verdicts"]}
check("pace backstop: scene 2 (3 extras, budget 1) keeps the REACTION and cuts the insert and the reveal (job priority)", bb2[(2, 2)]["verdict"] == "keep" and bb2[(2, 3)]["verdict"] == "cut" and bb2[(2, 4)]["verdict"] == "cut", str([bb2[(2, k)]["verdict"] for k in (2, 3, 4)]))
check("pace backstop: the cut says why (the pace) and keeps what the review said", bb2[(2, 3)]["by"] == "pace" and "Calm pace budget" in bb2[(2, 3)]["reason"] and "it is fine" in bb2[(2, 3)]["reason"], bb2[(2, 3)]["reason"])
check("pace backstop: the closing product shot is protected and never trimmed", bb2[(6, 3)]["verdict"] == "keep")
check("pace backstop: trimmed shots are in skips, kept ones are not", [(s["scene"], s["shot"]) for s in vb["skips"] if s["scene"] == 2] == [(2, 3), (2, 4)])
vf = fr.validate(ALLKEEP, sh, fr.budgets(ROWS, SECS, "fast", ROLES), "fast")
check("pace backstop: Fast pace leaves every shot alone here (budgets are big enough)", vf["skips"] == [])
check("pace backstop: with no budgets given, nothing is trimmed (the model's verdicts stand)", fr.validate(ALLKEEP, sh)["skips"] == [])
bud2 = fr.budgets(ROWS, SECS, "calm", {**ROLES, 5: "world"})
vt0 = fr.validate(ALLKEEP, sh, bud2, "calm")
vt1 = fr.validate({**ALLKEEP, "turn_scene": 5}, sh, bud2, "calm")
k0 = {(x["scene"], x["shot"]): x["verdict"] for x in vt0["verdicts"]}; k1 = {(x["scene"], x["shot"]): x["verdict"] for x in vt1["verdicts"]}
check("pace backstop: a 4 s scene gets no extra on Calm pace ... (scene 5, no turn named)", bud2[5] == 0 and k0[(5, 2)] == "cut", str(bud2))
check("pace backstop: ... unless the review names it THE TURN, which may be covered even in a short scene", k1[(5, 2)] == "keep", str(k1))

# ---- the route, stubbed model ------------------------------------------------------------------------------------------------------------------
seen = {}
def fake_complete(messages, **kw):
    seen["messages"], seen["kw"] = messages, kw
    return seen.get("reply", "")
main.completion.complete = fake_complete
main.completion.has_key = lambda: True
def call(**over):
    p = {"scenes": film(), "seconds": SECS, "pace": "fast", "logline": "A mother lets a hem down.", "message": "One glass at a time.", "tone": "tender", "house_id": "h1", "brand_mode": "grounded", **over}
    r = main.film_review(p)
    return r if isinstance(r, dict) else {"status": r.status_code, **json.loads(r.body)}
seen["reply"] = json.dumps(ANS)
r = call()
check("route: a good reply becomes a review with verdicts, skips and the measured stats", r["model"] is True and len(r["verdicts"]) == 10 and len(r["skips"]) == 5 and r["stats"]["shots"] == 16, str(r)[:300])
check("route: the model is called as a film call with the open house and brand mode", seen["kw"].get("film") is True and seen["kw"].get("house_id") == "h1" and seen["kw"].get("brand_mode") == "grounded")
check("route: the prompt got the planner's roles (the turn and the sign-off are known without the page saying so)", "job in the film: hook" in seen["messages"][0]["content"] and "job in the film: brand" in seen["messages"][0]["content"], seen["messages"][0]["content"][:500])
seen["reply"] = "Sure!\n```json\n" + json.dumps(ANS) + "\n```"
check("route: a fenced reply with chatter works", len(call()["skips"]) == 5)
check("route: Calm pace shows in the stats findings (too fast)", any(f["kind"] == "cut-rate" for f in call(pace="calm")["stats"]["findings"]) and not any(f["kind"] == "cut-rate" for f in r["stats"]["findings"]))
seen["reply"] = "I cannot do that"
ru = call()
check("route: an unreadable reply still returns the MEASURED facts, says so, and model is false", ru["model"] is False and ru["stats"]["shots"] == 16 and ru["verdicts"] == [] and "measured" in ru["notes_out"][0], str(ru)[:300])
seen["reply"] = ""
check("route: an empty model reply is the same 502 every generator gives", call().get("status") == 502)
main.completion.has_key = lambda: False
check("route: no Anthropic key is the same 503 every generator gives", call().get("status") == 503)
main.completion.has_key = lambda: True
check("route: no scenes is a 400", call(scenes=[]).get("status") == 400)
seen["reply"] = json.dumps(ANS)
rs = call(seconds=None)
check("route: with no seconds sent they are worked out from the words (never crashes)", rs["model"] is True and rs["stats"]["shots"] >= 6)
rn = call(scenes=[{"no": 1, "visual": "A single quiet scene."}, {"no": 2, "visual": "The end."}], seconds=[8, 6])
check("route: a film with no extra shots at all is still reviewed (beats and notes still make sense)", rn["model"] is True and rn["verdicts"] == [] and rn["stats"]["extras"] == 0)

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
