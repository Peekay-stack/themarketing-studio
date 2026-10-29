#!/usr/bin/env python
"""test_scene_shots.py -- offline checks for coverage step 3: sceneshots.py (prompt, parsing, backstops), POST /scene-shots with a stubbed
model, anglecheck.py, and the angle check on /scene-still. No network, no credit, nothing written to the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_scene_shots.py
"""
import base64, io, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import numpy as np
from PIL import Image
import sceneshots as ss, anglecheck as ac, filmvoice, main, gemini, library

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

# ---- max_extras / budget / pace -----------------------------------------------------------------------------------------------
check("max_extras: 3s->0, 4s->1, 5s->1, 6s->2, 8s->3, 20s->3 (capped)", [ss.max_extras(s) for s in (3, 4, 5, 6, 8, 20)] == [0, 1, 1, 2, 3, 3])
check("max_extras: garbage -> 0", ss.max_extras("x") == 0 and ss.max_extras(None) == 0)
check("budget: 8s scene -> calm 1, standard 2, fast 3; unset pace counts as standard",
      [ss.budget(8, p) for p in ("calm", "standard", "fast")] == [1, 2, 3] and ss.budget(8) == 2 and ss.budget(8, "nonsense") == 2)
check("budget: a scene shorter than the pace's minimum gets none (4s: calm/standard 0, fast 1); 3s is always 0",
      [ss.budget(4, p) for p in ("calm", "standard", "fast")] == [0, 0, 1] and ss.budget(3, "fast") == 0 and ss.budget(5, "standard") == 0)
check("budget: the opening (hook) and the turn may be covered even when short; other roles may not",
      ss.budget(4, "standard", "hook") == 1 and ss.budget(4, "calm", "turn") == 1 and ss.budget(4, "standard", "brand") == 0 and ss.budget(4, "standard", "build") == 0)
check("budget: an opted-in sign-off is judged by its seconds, not the pace minimum", ss.budget(4, "standard", "brand", True) == 1)
check("budget: garbage -> 0, never raises", ss.budget(None, "fast") == 0 and ss.budget("x") == 0)
check("pace: normalise accepts the three names (any case) and nothing else", [ss.normalise_pace(x) for x in ("Calm", " FAST ", "standard", "slow", None, "")] == ["calm", "fast", "standard", "", "", ""])
check("pace: tone words pick a default with a reason", ss.suggest_pace("A tender, unhurried story")[0] == "calm" and ss.suggest_pace("Energetic, playful and punchy")[0] == "fast"
      and ss.suggest_pace("")[0] == "standard" and ss.suggest_pace("tender and energetic")[0] == "standard" and "tender" in ss.suggest_pace("tender")[1])
check("pace: the table holds the three presets with extras caps 1 / 2 / 3", [ss.PACE_TABLE[p]["max_extras"] for p in ss.PACES] == [1, 2, 3])

# ---- parse -------------------------------------------------------------------------------------------------------------------
GOOD = {"needs_coverage": True, "why": "The drink is the payoff and needs a face and a detail.",
        "shots": [{"job": "reaction", "why": "his face shows the first sip landing", "camera_position": "The camera is just behind the mother's right shoulder, her shoulder soft in the left foreground, looking at the boy.",
                   "action": "The boy lifts the steel glass in both hands and looks into it.", "shot_size": "over", "camera": "slow push-in", "movement_class": "push-in", "secs": 2},
                  {"job": "insert", "why": "the cold steel glass is the object the story is about", "camera_position": "A low camera at counter height beside the glass, looking up at his face.",
                   "action": "His eyes follow the glass to his lips.", "shot_size": "close", "camera": "locked-off", "movement_class": "static", "secs": 2},
                  {"job": "reveal", "why": "the grip shows how big the glass is in a small hand", "camera_position": "Tight on his hands from above.", "action": "His fingers close around the cold steel.", "shot_size": "detail", "camera": "", "movement_class": "", "secs": 2}]}
pp = ss.parse(json.dumps(GOOD))
check("parse: plain JSON gives shots, needs_coverage and the why", len(pp["shots"]) == 3 and pp["needs_coverage"] is True and "payoff" in pp["why"])
check("parse: fenced and with prose around it", len(ss.parse("Here you go:\n```json\n" + json.dumps(GOOD) + "\n```\nHope that helps.")["shots"]) == 3)
bl = ss.parse(json.dumps(GOOD["shots"]))
check("parse: a bare list still reads (needs_coverage unknown)", len(bl["shots"]) == 3 and bl["needs_coverage"] is None)
zero = ss.parse(json.dumps({"needs_coverage": False, "why": "Scene 3 already shows this closer.", "shots": []}))
check("parse: ZERO shots is a valid reply and keeps its reason", zero["shots"] == [] and zero["needs_coverage"] is False and "already" in zero["why"])
check("parse: garbage / empty -> None", ss.parse("no json here") is None and ss.parse("") is None and ss.parse('{"shots": "nope"}') is None)

# ---- validate ----------------------------------------------------------------------------------------------------------------
v = ss.validate(GOOD["shots"], secs=8, plate_locked=False, pack_in_scene=False, master_size="medium", pace="fast")
check("validate: a good proposal is kept whole, each shot gets an id, a job and a why", len(v["shots"]) == 3 and len({s["id"] for s in v["shots"]}) == 3 and all(s["job"] and s["why"] for s in v["shots"]))
check("validate: INVARIANT shot seconds add up to the scene (master keeps the rest, >= 2s)", v["master_secs"] + sum(s["secs"] for s in v["shots"]) == 8 and v["master_secs"] >= 2, str(v))
check("validate: camera position and action are merged into the shot's visual, position first", v["shots"][0]["visual"].startswith("The camera is just behind the mother") and "lifts the steel glass" in v["shots"][0]["visual"])
check("validate: movement phrases and classes are kept", v["shots"][0]["camera"] == "slow push-in" and v["shots"][0]["movement_class"] == "push-in")
check("validate: reports the scene's budget", v["budget"] == 3)
vstd = ss.validate(GOOD["shots"], secs=8, master_size="medium", pace="standard")
check("validate: STANDARD pace holds an 8s scene to 2 extras and says why", len(vstd["shots"]) == 2 and any("Standard pace" in n and "left out" in n for n in vstd["notes"]), str(vstd["notes"]))
vcalm = ss.validate(GOOD["shots"], secs=8, master_size="medium", pace="calm")
check("validate: CALM pace holds an 8s scene to 1 extra", len(vcalm["shots"]) == 1)
vshort = ss.validate(GOOD["shots"], secs=4, master_size="medium", pace="standard")
check("validate: a 4s scene gets NONE on standard pace (and says so)", vshort["shots"] == [] and any("gets none" in n for n in vshort["notes"]), str(vshort))
vhook = ss.validate(GOOD["shots"], secs=4, master_size="medium", pace="standard", role="hook")
check("validate: ... but a 4s opening (hook) may keep one", len(vhook["shots"]) == 1 and vhook["master_secs"] + vhook["shots"][0]["secs"] == 4, str(vhook))
v4 = ss.validate(GOOD["shots"], secs=4, master_size="medium", pace="fast")
check("validate: a 4s scene on fast pace keeps ONE extra shot and says the rest were left out", len(v4["shots"]) == 1 and any("left out" in n for n in v4["notes"]) and v4["master_secs"] + v4["shots"][0]["secs"] == 4, str(v4))
vw = ss.validate(GOOD["shots"], secs=8, master_size="medium", want=1, pace="fast")
check("validate: want=1 keeps one", len(vw["shots"]) == 1)
vnojob = ss.validate([{"why": "adds a feeling here", "action": "a.", "camera_position": "b.", "shot_size": "close", "secs": 2}, {"job": "decoration", "why": "looks nice", "action": "a.", "camera_position": "b.", "shot_size": "close", "secs": 2}], secs=8, pace="fast")
check("validate: a shot with no recognised JOB is left out and reported", vnojob["shots"] == [] and sum("no clear job" in n for n in vnojob["notes"]) == 2, str(vnojob))
vnowhy = ss.validate([{"job": "reveal", "why": "", "action": "a.", "camera_position": "b.", "shot_size": "close", "secs": 2}, {"job": "reveal", "why": "ok", "action": "a.", "camera_position": "b.", "shot_size": "close", "secs": 2}], secs=8, pace="fast")
check("validate: a shot with no reason (or a throwaway one) is left out and reported", vnowhy["shots"] == [] and sum("no reason" in n for n in vnowhy["notes"]) == 2, str(vnowhy))
check("validate: job synonyms are understood (cutaway -> insert, emotional close-up -> reaction, hold -> payoff-hold, match cut -> match)",
      [ss.job_of(x) for x in ("cutaway", "Emotional close-up", "hold", "match cut", "POV", "reveal", "banana", None)] == ["insert", "reaction", "payoff-hold", "match", "pov", "reveal", "", ""])
def S(**k): return {"job": "reveal", "why": "adds something new here", **k}
vm = ss.validate([S(action="a.", camera_position="b.", shot_size="detail", secs=3), S(action="c.", camera_position="d.", shot_size="over", secs=3),
                  S(action="e.", camera_position="f.", shot_size="close", secs=2)], secs=10, master_size="medium", pace="fast")
check("validate: the master stays at least as long as any extra (10s proposed 3+3+2 -> master 3), total unchanged",
      vm["master_secs"] >= max(s["secs"] for s in vm["shots"]) and vm["master_secs"] + sum(s["secs"] for s in vm["shots"]) == 10 and all(s["secs"] >= 2 for s in vm["shots"]), str(vm))
check("master-longest helper: [2,3,3,2] -> [3,2,3,2]; an already-fine split is untouched; extras never go under 2s",
      ss._master_longest([2, 3, 3, 2]) == [3, 2, 3, 2] and ss._master_longest([4, 2, 2]) == [4, 2, 2] and ss._master_longest([2, 2, 2]) == [2, 2, 2] and min(ss._master_longest([2, 8, 8])[1:]) >= 2 and sum(ss._master_longest([2, 8, 8])) == 18)
vz = ss.validate([S(action="A wide view of the kitchen.", camera_position="From the doorway.", shot_size="wide", secs=2)], secs=6, plate_locked=False, master_size="close")
check("validate: a WIDE shot with no locked location carries the warning", any("not locked" in w for w in vz["shots"][0]["warnings"]), str(vz))
vz2 = ss.validate([S(action="A wide view of the kitchen.", camera_position="From the doorway.", shot_size="wide", secs=2)], secs=6, plate_locked=True, master_size="close")
check("validate: ... and none when the location is locked", vz2["shots"][0]["warnings"] == [])
vs = ss.validate([S(action="Close on her face.", camera_position="Tight.", shot_size="close", secs=2), S(action="Closer still.", camera_position="Tighter.", shot_size="Close-up", secs=2)], secs=8, master_size="close", pace="fast")
check("validate: neighbours with the same size (incl. the master's) are WARNED, not silently changed", any("Same size as shot 1" in w for w in vs["shots"][0]["warnings"]) and any("Same size as shot 2" in w for w in vs["shots"][1]["warnings"]) and vs["shots"][1]["shot_size"] == "close", str(vs))
vq = ss.validate([S(action="She smiles and says “this is the best milk”. A caption reads Heritage Pure. She pours.", camera_position="Beside her.", shot_size="medium", secs=2)], secs=6, master_size="wide")
check("validate: quoted speech and sentences asking for captions are removed (and reported)", "best milk" not in vq["shots"][0]["visual"] and "caption" not in vq["shots"][0]["visual"].lower() and "pours" in vq["shots"][0]["visual"] and len(vq["notes"]) >= 2, str(vq))
vp = ss.validate([S(action="The pack fills the frame.", camera_position="Square on.", shot_size="product", secs=2)], secs=6, pack_in_scene=False, master_size="wide")
check("validate: a product hero outside a pack scene becomes a detail", vp["shots"][0]["shot_size"] == "detail")
vp2 = ss.validate([S(action="The pack fills the frame.", camera_position="Square on.", shot_size="product", secs=2)], secs=6, pack_in_scene=True, master_size="wide")
check("validate: ... but stays a product hero when the scene is about the pack", vp2["shots"][0]["shot_size"] == "product")
vsyn = ss.validate([S(action="x.", camera_position="y.", shot_size="OTS", movement_class="dolly in", secs=2), S(action="z.", camera_position="w.", shot_size="macro", movement_class="nonsense", secs=2)], secs=8, master_size="wide")
check("validate: size and movement synonyms are understood, nonsense movement is cleared", [s["shot_size"] for s in vsyn["shots"]] == ["over", "detail"] and [s["movement_class"] for s in vsyn["shots"]] == ["push-in", ""], str(vsyn))
vu = ss.validate([S(action="", camera_position=""), S(action="Fine.", camera_position="Here.", shot_size="zzz", secs=2)], secs=8, master_size="wide")
check("validate: an empty shot is dropped and an unknown size falls back to medium, both reported", len(vu["shots"]) == 1 and vu["shots"][0]["shot_size"] == "medium" and len(vu["notes"]) >= 2, str(vu))
vn = ss.validate([S(action="Close.", shot_size="close", secs=2)], secs=6, master_size="wide")
check("validate: no camera position is flagged (sizes alone gave near-copies)", any("no camera position" in n for n in vn["notes"]))
check("validate: garbage input never raises", ss.validate(None, secs=6)["shots"] == [] and ss.validate([{}, {"secs": "x"}], secs=6)["shots"] == [])
check("validate: huge / weird seconds are held to 2-8 and still sum", all(ss.validate([S(action="a.", camera_position="b.", secs=w)] * 2, secs=8, master_size="x", pace="fast")["master_secs"] >= 2 for w in (0, -5, 99, "x", None, 3.6)))

# ---- build_prompt --------------------------------------------------------------------------------------------------------------
row = {"no": 4, "visual": "The boy takes the steel glass from the counter; his mother holds the Heritage pouch.", "camera": "slow push-in", "shot_size": "medium",
       "audio": [{"kind": "vo", "text": "Every glass is checked twice."}]}
pr = ss.build_prompt(row=row, secs=8, n_extras=2, logline="A morning with Heritage.", characters="Boy (8) white shirt; Mother cream saree", location_line="a Hyderabad kitchen",
                     plate_locked=False, pack_in_scene=True, prev_visual="Technicians at work.", next_visual="The pour.")
check("prompt: carries the scene, its seconds, the master and the spoken line (for rhythm)", "8 seconds" in pr and "takes the steel glass" in pr and "Every glass is checked twice" in pr)
check("prompt: caps the extras and states the camera POSITION rule", "at most 2 extra shots" in pr and "STATE THE CAMERA POSITION" in pr)
check("prompt: forbids words and text, and says keep objects in the master's state", "NO WORDS ON SCREEN" in pr and "KEEP EVERY OBJECT IN THE STATE IT HAS IN SHOT 1" in pr)
check("prompt: steers away from wide when the location is not locked; allows it when locked", "AVOID wide shots" in pr and "A wide shot is allowed." in ss.build_prompt(row=row, secs=8, n_extras=2, plate_locked=True))
check("prompt: product hero is offered only when the scene is about the pack", "product" in pr.split("SIZES: choose from")[1].split(".")[0] and "product" not in ss.build_prompt(row=row, secs=8, n_extras=2, pack_in_scene=False).split("SIZES: choose from")[1].split(".")[0])
check("prompt: never proposes an arm or hand crossing a face, hands toward the lens, or a limb in extreme close-up (B3)", "Never propose an arm or a hand crossing a face, hands reaching toward the lens, or a limb in extreme close-up" in pr)
check("prompt: neighbours and cast reach the model", "Technicians at work" in pr and "CAST: Boy (8)" in pr and "LOCATION: a Hyderabad kitchen" in pr)
check("prompt: the decision comes FIRST -- three tests (job, new information, serves the film), zero is valid, jobs listed",
      "FIRST DECIDE WHETHER THIS SCENE NEEDS ANY EXTRA SHOT" in pr and "A. JOB" in pr and "B. NEW INFORMATION" in pr and "C. IT SERVES THE FILM" in pr and "ZERO extra shots is a valid" in pr
      and all(f"`{j}`" in pr for j in ss.JOBS))
check("prompt: the neighbour rule and the time-passing rule are stated", "already shows this scene's action at another scale" in pr and "TIME PASSING" in pr)
check("prompt: the schema asks for job, why and needs_coverage", "\"needs_coverage\"" in pr and "\"job\"" in pr and "\"why\"" in pr)
pr2 = ss.build_prompt(row=row, secs=8, n_extras=2, pace="calm", role="turn", message="Real milk, honestly made.", tone="tender and unhurried", scene_index=1,
                      outline=[{"no": 1, "secs": 6, "visual": "Mother measures the boy's trousers.", "says": "Every day he grew."}, {"no": 2, "secs": 8, "visual": "The boy drinks.", "shots": [{"job": "reaction", "visual": "his face"}]}])
check("prompt: pace, role, message, tone and the whole script (with this scene marked) reach the model",
      "ITS PACE: Calm" in pr2 and "This scene's job in the film: turn" in pr2 and "Real milk, honestly made." in pr2 and "tender and unhurried" in pr2
      and "THE WHOLE SCRIPT" in pr2 and "Scene 2 (8 s)" in pr2 and "<== THIS SCENE" in pr2 and "extra shots: reaction: his face" in pr2)
check("prompt: no outline -> no script section", "THE WHOLE SCRIPT" not in pr)

# ---- the route, with a stubbed model -------------------------------------------------------------------------------------------
seen = {}
def fake_complete(messages, **kw):
    seen["messages"], seen["kw"] = messages, kw
    return seen.get("reply", "")
main.completion.complete = fake_complete
main.completion.has_key = lambda: True
def call(**over):
    p = {"scene": dict(row), "scene_seconds": 8, "logline": "A morning with Heritage.", "house_id": "h1", "brand_mode": "grounded", "pace": "fast", **over}
    r = main.scene_shots(p)
    return r if isinstance(r, dict) else {"status": r.status_code, **json.loads(r.body)}
seen["reply"] = json.dumps(GOOD)
r = call()
check("route: a good reply becomes a proposal with seconds that add up", len(r["shots"]) == 3 and r["master_secs"] + sum(s["secs"] for s in r["shots"]) == 8 and r["scene_seconds"] == 8, str(r)[:300])
check("route: the proposal carries the pace, the scene's budget, the why and needs_coverage", r["pace"] == "fast" and r["budget"] == 3 and r["needs_coverage"] is True and "payoff" in r["why"], str(r)[:300])
check("route: every shot carries its job and why", all(s["job"] and s["why"] for s in r["shots"]))
check("route: the model is called as a film call with the open house and brand mode", seen["kw"].get("film") is True and seen["kw"].get("house_id") == "h1" and seen["kw"].get("brand_mode") == "grounded")
check("route: the model was given the scene's seconds and the position rule", "8 seconds" in seen["messages"][0]["content"] and "STATE THE CAMERA POSITION" in seen["messages"][0]["content"])
seen["reply"] = "Sure!\n```json\n" + json.dumps(GOOD) + "\n```"
check("route: a fenced reply with chatter around it still works", len(call()["shots"]) == 3)
check("route: n_shots asks for fewer", len(call(n_shots=1)["shots"]) == 1)
check("route: n_shots above what the scene can hold is clamped (6s scene -> at most 2 extras)", len(call(scene_seconds=6, n_shots=9)["shots"]) == 2)
check("route: the default pace is Standard (8s scene -> 2 extras)", len(call(pace="")["shots"]) == 2 and call(pace="")["pace"] == "standard")
check("route: Calm pace -> 1 extra for the same scene", len(call(pace="calm")["shots"]) == 1)
seen["messages"] = None
rs_hold = call(scene_seconds=5, pace="standard")
check("route: a scene under the pace minimum comes back as ONE shot, the model is not called", rs_hold["shots"] == [] and rs_hold["needs_coverage"] is False and "one shot" in rs_hold["reason"] and seen["messages"] is None, str(rs_hold))
seen["reply"] = json.dumps(GOOD)
rhook = call(scene_seconds=5, pace="standard", role="hook")
check("route: ... unless the scene is the opening (role hook)", len(rhook["shots"]) == 1, str(rhook)[:200])
rs = call(is_signoff=True)
check("route: the sign-off scene returns no shots and says why", rs["shots"] == [] and "sign-off" in rs["reason"])
rs2 = call(scene={**row, "beat_role": "brand"})
check("route: a scene marked as the sign-off by its own beat role is also refused", rs2["shots"] == [] and "sign-off" in rs2["reason"])
r3 = call(scene_seconds=3)
check("route: a scene under 4s returns no shots and says why (model not called)", r3["shots"] == [] and "too short" in r3["reason"])
check("route: a missing scene is a 400", call(scene={}).get("status") == 400)
seen["reply"] = json.dumps({"needs_coverage": False, "why": "Scene 3 already shows this closer.", "shots": []})
rz = call()
check("route: the model saying ZERO extras is an answer, not an error, and its reason is shown", rz.get("status") is None and rz["shots"] == [] and rz["needs_coverage"] is False and "already shows" in rz["reason"], str(rz))
seen["reply"] = json.dumps({"needs_coverage": False, "why": "One moment.", "shots": [GOOD["shots"][0]]})
rz2 = call()
check("route: a shot that passes the job/why tests is kept even if the reply also said no coverage", len(rz2["shots"]) == 1)
seen["reply"] = "I cannot do that"
check("route: an unreadable reply is a 502 with a plain message", call().get("status") == 502 and "could not be read" in call().get("detail", ""))
seen["reply"] = json.dumps({"shots": [{"action": "", "camera_position": ""}]})
check("route: a reply whose shots all fail the tests is a 502 that lists why", call().get("status") == 502 and "None of the proposed shots" in call().get("detail", ""))
seen["reply"] = ""
check("route: an empty model reply is the same 502 every generator gives", call().get("status") == 502)
main.completion.has_key = lambda: False
check("route: no Anthropic key is the same 503 every generator gives", call().get("status") == 503)
main.completion.has_key = lambda: True
seen["reply"] = json.dumps(GOOD)
check("route: the outline, role, message and tone reach the model", (lambda c: "THE WHOLE SCRIPT" in c and "This scene's job in the film: turn" in c and "Real milk" in c and "unhurried" in c)(
    (call(outline=[{"no": 1, "secs": 8, "visual": "x"}], scene_index=0, role="turn", message="Real milk", tone="unhurried"), seen["messages"][0]["content"])[1]))

r_no = call(is_signoff=True)
check("route: a sign-off is refused unless shots are allowed, and the reason says how", r_no["shots"] == [] and "unless you allow" in r_no["reason"], str(r_no))
r_so = call(is_signoff=True, allow_signoff=True, scene={**row, "visual": "The Heritage pouch beside a glass; a boy's hand lifts the glass."})
check("route: with shots allowed on the sign-off a proposal comes back", len(r_so.get("shots", [])) == 3, str(r_so)[:200])
sp = seen["messages"][0]["content"]
check("route: the sign-off prompt says the film ends on the last shot, the pack clean, and offers the product hero size",
      "CLOSING SIGN-OFF SCENE" in sp and "LAST extra shot size `product`" in sp and "product" in sp.split("SIZES: choose from")[1].split(".")[0], sp[-900:])
check("route: a normal scene's prompt has no sign-off section", "CLOSING SIGN-OFF SCENE" not in ss.build_prompt(row=row, secs=8, n_extras=2))
vso = ss.validate(GOOD["shots"], secs=8, master_size="medium", signoff=True, pace="fast")
check("validate: a sign-off whose LAST shot is not a product hero is warned that the film ends on it", any("Sign-off scene" in w for w in vso["shots"][-1]["warnings"]) and not any("Sign-off scene" in w for w in vso["shots"][0]["warnings"]), str(vso["shots"][-1]["warnings"]))
good_so = [dict(GOOD["shots"][0]), dict(GOOD["shots"][1], shot_size="product", camera_position="Square on.", action="The pack, clean.")]
vso2 = ss.validate(good_so, secs=6, master_size="medium", signoff=True, pack_in_scene=True, pace="fast")
check("validate: ... and not warned when the last shot is the product hero", vso2["shots"][-1]["shot_size"] == "product" and not any("Sign-off scene" in w for w in vso2["shots"][-1]["warnings"]), str(vso2["shots"][-1]))
check("validate: a normal scene is never given the sign-off warning", not any("Sign-off scene" in w for s_ in ss.validate(GOOD["shots"], secs=8, master_size="medium", pace="fast")["shots"] for w in s_["warnings"]))
rp = main.pace_suggest({"text": "A tender, unhurried story of a mother"})
check("route: /pace-suggest returns a pace, a reason and the table", rp["pace"] == "calm" and "tender" in rp["why"] and set(rp["table"]) == {"calm", "standard", "fast"})

# ---- anglecheck ------------------------------------------------------------------------------------------------------------------
def png(arr):
    b = io.BytesIO(); Image.fromarray(arr.astype("uint8")).save(b, "PNG"); return b.getvalue()
rng = np.random.default_rng(7)
def scene_img(seed):
    r = np.random.default_rng(seed)
    base = r.integers(40, 200, (9, 16, 3)).astype("uint8")
    return np.asarray(Image.fromarray(base).resize((640, 360), Image.BICUBIC)).astype("float32")
A = scene_img(1); Bn = scene_img(2)
check("angle: identical frames -> same (correlation ~1)", ac.check(png(A), png(A))["verdict"] == "same" and ac.check(png(A), png(A))["correlation"] > 0.99)
noisy = np.clip(A + rng.normal(0, 6, A.shape), 0, 255)
check("angle: a re-render with small noise and a slight brightness shift -> still same", ac.check(png(np.clip(noisy + 8, 0, 255)), png(A))["verdict"] == "same")
check("angle: a different picture -> different", ac.check(png(Bn), png(A))["verdict"] == "different")
shifted = np.roll(A, 120, axis=1)
check("angle: the same picture panned a long way -> different", ac.check(png(shifted), png(A))["verdict"] == "different", str(ac.check(png(shifted), png(A))))
check("angle: a flat frame cannot be compared -> unclear", ac.check(png(np.full((360, 640, 3), 90)), png(A))["verdict"] == "unclear")
check("angle: garbage bytes -> unclear, never raises", ac.check(b"nope", png(A))["verdict"] == "unclear")
check("angle: the threshold is the one measured on 27 Oct", ac.SAME_AT == 0.95)
D = r"C:\Users\punie\Downloads\engine-trial"; S0 = os.path.join(D, "coverage_step0")
pairs = [("cand_B_28.5.jpg", "frame_B_over.jpg", "same"), ("frame_first.jpg", "frame_A_medium.jpg", "same"), ("cand_B_28.5.jpg", "frame_B_close.jpg", "different"),
         ("cand_B_28.5.jpg", "frame_B_detail.jpg", "different"), ("frame_first.jpg", "frame_A_detail.jpg", "different"), ("frame_first.jpg", "frame_A_wide.jpg", "different")]
if all(os.path.exists(os.path.join(D if m.startswith(("cand", "frame_first")) else S0, m)) for m, _, _ in pairs) and os.path.isdir(S0):
    for m, f, want in pairs:
        got = ac.check(open(os.path.join(S0, f), "rb").read(), open(os.path.join(D, m), "rb").read())
        check(f"angle (REAL trial frames): {m} vs {f} -> {want}", got["verdict"] == want, str(got))
else:
    print("SKIP real trial frames not on this machine")

# ---- /scene-still reports the angle check when a coverage frame sends compare_to ---------------------------------------------------
MASTER = "data:image/png;base64," + base64.b64encode(png(A)).decode()
NEAR = "data:image/png;base64," + base64.b64encode(png(np.clip(noisy, 0, 255))).decode()
FAR = "data:image/png;base64," + base64.b64encode(png(Bn)).decode()
main._record_made = lambda *a, **k: None
library.shot_references = lambda **k: {"refs": [], "kinds": [], "cast": "", "pack": "", "plate": "", "has_cast": False, "has_pack": False, "has_plate": False, "dropped": [], "why": ""}
which = {"v": NEAR}
gemini.image_from_reference = lambda prompt, refs, **kw: which["v"]
real_b64 = gemini._as_base64
def fake_b64(src):
    if str(src).startswith("data:"):
        head, _, b = src.partition(","); return head[5:].split(";")[0], b
    return real_b64(src)
gemini._as_base64 = fake_b64
body = {"scene_no": 4, "prompt": "Close-up of the boy.", "ratio": "16:9", "style": "real", "video_frame": True, "shot_size": "close", "use_cast": False,
        "include_pack": False, "engines": {"image": "google"}, "reference_urls": [MASTER], "compare_to": MASTER}
r1 = main.scene_still(dict(body))
check("/scene-still: a near-copy of the master reports angle_check 'same'", isinstance(r1, dict) and (r1.get("angle_check") or {}).get("verdict") == "same", str(r1)[:300])
which["v"] = FAR
r2 = main.scene_still(dict(body))
check("/scene-still: a different angle reports 'different'", (r2.get("angle_check") or {}).get("verdict") == "different")
b2 = dict(body); b2.pop("compare_to")
check("/scene-still: with no compare_to the response has no angle result (existing callers unaffected)", main.scene_still(b2).get("angle_check") is None)
check("/scene-still: an unreadable compare_to never costs the frame", main.scene_still({**body, "compare_to": "/media/does-not-exist.jpg"}).get("image_url") == FAR)

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
