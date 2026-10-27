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

# ---- max_extras ------------------------------------------------------------------------------------------------------------
check("max_extras: 3s->0, 4s->1, 5s->1, 6s->2, 8s->3, 20s->3 (capped)", [ss.max_extras(s) for s in (3, 4, 5, 6, 8, 20)] == [0, 1, 1, 2, 3, 3])
check("max_extras: garbage -> 0", ss.max_extras("x") == 0 and ss.max_extras(None) == 0)

# ---- parse -------------------------------------------------------------------------------------------------------------------
GOOD = {"shots": [{"camera_position": "The camera is just behind the mother's right shoulder, her shoulder soft in the left foreground, looking at the boy.",
                   "action": "The boy lifts the steel glass in both hands and looks into it.", "shot_size": "over", "camera": "slow push-in", "movement_class": "push-in", "secs": 2},
                  {"camera_position": "A low camera at counter height beside the glass, looking up at his face.",
                   "action": "His eyes follow the glass to his lips.", "shot_size": "close", "camera": "locked-off", "movement_class": "static", "secs": 2},
                  {"camera_position": "Tight on his hands from above.", "action": "His fingers close around the cold steel.", "shot_size": "detail", "camera": "", "movement_class": "", "secs": 2}]}
check("parse: plain JSON", len(ss.parse(json.dumps(GOOD))) == 3)
check("parse: fenced and with prose around it", len(ss.parse("Here you go:\n```json\n" + json.dumps(GOOD) + "\n```\nHope that helps.")) == 3)
check("parse: a bare list", len(ss.parse(json.dumps(GOOD["shots"]))) == 3)
check("parse: garbage / empty -> None", ss.parse("no json here") is None and ss.parse("") is None and ss.parse('{"shots": "nope"}') is None)

# ---- validate ----------------------------------------------------------------------------------------------------------------
v = ss.validate(GOOD["shots"], secs=8, plate_locked=False, pack_in_scene=False, master_size="medium")
check("validate: a good proposal is kept whole, each shot gets an id", len(v["shots"]) == 3 and len({s["id"] for s in v["shots"]}) == 3)
check("validate: INVARIANT shot seconds add up to the scene (master keeps the rest, >= 2s)", v["master_secs"] + sum(s["secs"] for s in v["shots"]) == 8 and v["master_secs"] >= 2, str(v))
check("validate: camera position and action are merged into the shot's visual, position first", v["shots"][0]["visual"].startswith("The camera is just behind the mother") and "lifts the steel glass" in v["shots"][0]["visual"])
check("validate: movement phrases and classes are kept", v["shots"][0]["camera"] == "slow push-in" and v["shots"][0]["movement_class"] == "push-in")
v4 = ss.validate(GOOD["shots"], secs=4, master_size="medium")
check("validate: a 4s scene keeps ONE extra shot and says the rest were left out", len(v4["shots"]) == 1 and any("left out" in n for n in v4["notes"]) and v4["master_secs"] + v4["shots"][0]["secs"] == 4, str(v4))
vw = ss.validate(GOOD["shots"], secs=8, master_size="medium", want=1)
check("validate: want=1 keeps one", len(vw["shots"]) == 1)
vm = ss.validate([{"action": "a.", "camera_position": "b.", "shot_size": "detail", "secs": 3}, {"action": "c.", "camera_position": "d.", "shot_size": "over", "secs": 3},
                  {"action": "e.", "camera_position": "f.", "shot_size": "close", "secs": 2}], secs=10, master_size="medium")
check("validate: the master stays at least as long as any extra (10s proposed 3+3+2 -> master 3), total unchanged",
      vm["master_secs"] >= max(s["secs"] for s in vm["shots"]) and vm["master_secs"] + sum(s["secs"] for s in vm["shots"]) == 10 and all(s["secs"] >= 2 for s in vm["shots"]), str(vm))
check("master-longest helper: [2,3,3,2] -> [3,2,3,2]; an already-fine split is untouched; extras never go under 2s",
      ss._master_longest([2, 3, 3, 2]) == [3, 2, 3, 2] and ss._master_longest([4, 2, 2]) == [4, 2, 2] and ss._master_longest([2, 2, 2]) == [2, 2, 2] and min(ss._master_longest([2, 8, 8])[1:]) >= 2 and sum(ss._master_longest([2, 8, 8])) == 18)
vz = ss.validate([{"action": "A wide view of the kitchen.", "camera_position": "From the doorway.", "shot_size": "wide", "secs": 2}], secs=6, plate_locked=False, master_size="close")
check("validate: a WIDE shot with no locked location carries the warning", any("not locked" in w for w in vz["shots"][0]["warnings"]), str(vz))
vz2 = ss.validate([{"action": "A wide view of the kitchen.", "camera_position": "From the doorway.", "shot_size": "wide", "secs": 2}], secs=6, plate_locked=True, master_size="close")
check("validate: ... and none when the location is locked", vz2["shots"][0]["warnings"] == [])
vs = ss.validate([{"action": "Close on her face.", "camera_position": "Tight.", "shot_size": "close", "secs": 2}, {"action": "Closer still.", "camera_position": "Tighter.", "shot_size": "Close-up", "secs": 2}], secs=8, master_size="close")
check("validate: neighbours with the same size (incl. the master's) are WARNED, not silently changed", any("Same size as shot 1" in w for w in vs["shots"][0]["warnings"]) and any("Same size as shot 2" in w for w in vs["shots"][1]["warnings"]) and vs["shots"][1]["shot_size"] == "close", str(vs))
vq = ss.validate([{"action": "She smiles and says \u201cthis is the best milk\u201d. A caption reads Heritage Pure. She pours.", "camera_position": "Beside her.", "shot_size": "medium", "secs": 2}], secs=6, master_size="wide")
check("validate: quoted speech and sentences asking for captions are removed (and reported)", "best milk" not in vq["shots"][0]["visual"] and "caption" not in vq["shots"][0]["visual"].lower() and "pours" in vq["shots"][0]["visual"] and len(vq["notes"]) >= 2, str(vq))
vp = ss.validate([{"action": "The pack fills the frame.", "camera_position": "Square on.", "shot_size": "product", "secs": 2}], secs=6, pack_in_scene=False, master_size="wide")
check("validate: a product hero outside a pack scene becomes a detail", vp["shots"][0]["shot_size"] == "detail")
vp2 = ss.validate([{"action": "The pack fills the frame.", "camera_position": "Square on.", "shot_size": "product", "secs": 2}], secs=6, pack_in_scene=True, master_size="wide")
check("validate: ... but stays a product hero when the scene is about the pack", vp2["shots"][0]["shot_size"] == "product")
vsyn = ss.validate([{"action": "x.", "camera_position": "y.", "shot_size": "OTS", "movement_class": "dolly in", "secs": 2}, {"action": "z.", "camera_position": "w.", "shot_size": "macro", "movement_class": "nonsense", "secs": 2}], secs=8, master_size="wide")
check("validate: size and movement synonyms are understood, nonsense movement is cleared", [s["shot_size"] for s in vsyn["shots"]] == ["over", "detail"] and [s["movement_class"] for s in vsyn["shots"]] == ["push-in", ""], str(vsyn))
vu = ss.validate([{"action": "", "camera_position": ""}, {"action": "Fine.", "camera_position": "Here.", "shot_size": "zzz", "secs": 2}], secs=8, master_size="wide")
check("validate: an empty shot is dropped and an unknown size falls back to medium, both reported", len(vu["shots"]) == 1 and vu["shots"][0]["shot_size"] == "medium" and len(vu["notes"]) >= 2, str(vu))
vn = ss.validate([{"action": "Close.", "shot_size": "close", "secs": 2}], secs=6, master_size="wide")
check("validate: no camera position is flagged (sizes alone gave near-copies)", any("no camera position" in n for n in vn["notes"]))
check("validate: garbage input never raises", ss.validate(None, secs=6)["shots"] == [] and ss.validate([{}, {"secs": "x"}], secs=6)["shots"] == [])
check("validate: huge / weird seconds are held to 2-8 and still sum", all(ss.validate([{"action": "a.", "camera_position": "b.", "secs": w}] * 2, secs=8, master_size="x")["master_secs"] >= 2 for w in (0, -5, 99, "x", None, 3.6)))

# ---- build_prompt --------------------------------------------------------------------------------------------------------------
row = {"no": 4, "visual": "The boy takes the steel glass from the counter; his mother holds the Heritage pouch.", "camera": "slow push-in", "shot_size": "medium",
       "audio": [{"kind": "vo", "text": "Every glass is checked twice."}]}
pr = ss.build_prompt(row=row, secs=8, n_extras=2, logline="A morning with Heritage.", characters="Boy (8) white shirt; Mother cream saree", location_line="a Hyderabad kitchen",
                     plate_locked=False, pack_in_scene=True, prev_visual="Technicians at work.", next_visual="The pour.")
check("prompt: carries the scene, its seconds, the master and the spoken line (for rhythm)", "8 seconds" in pr and "takes the steel glass" in pr and "Every glass is checked twice" in pr)
check("prompt: asks for 2 extra shots and for the camera POSITION", "Write 2 EXTRA shots" in pr and "STATE THE CAMERA POSITION" in pr)
check("prompt: forbids words and text, and says keep objects in the master's state", "NO WORDS ON SCREEN" in pr and "KEEP EVERY OBJECT IN THE STATE IT HAS IN SHOT 1" in pr)
check("prompt: steers away from wide when the location is not locked; allows it when locked", "AVOID wide shots" in pr and "A wide shot is allowed." in ss.build_prompt(row=row, secs=8, n_extras=2, plate_locked=True))
check("prompt: product hero is offered only when the scene is about the pack", "product" in pr.split("SIZES: choose from")[1].split(".")[0] and "product" not in ss.build_prompt(row=row, secs=8, n_extras=2, pack_in_scene=False).split("SIZES: choose from")[1].split(".")[0])
check("prompt: neighbours and cast reach the model", "Technicians at work" in pr and "CAST: Boy (8)" in pr and "LOCATION: a Hyderabad kitchen" in pr)

# ---- the route, with a stubbed model -------------------------------------------------------------------------------------------
seen = {}
def fake_complete(messages, **kw):
    seen["messages"], seen["kw"] = messages, kw
    return seen.get("reply", "")
main.completion.complete = fake_complete
main.completion.has_key = lambda: True
def call(**over):
    p = {"scene": dict(row), "scene_seconds": 8, "logline": "A morning with Heritage.", "house_id": "h1", "brand_mode": "grounded", **over}
    r = main.scene_shots(p)
    return r if isinstance(r, dict) else {"status": r.status_code, **json.loads(r.body)}
seen["reply"] = json.dumps(GOOD)
r = call()
check("route: a good reply becomes a proposal with seconds that add up", len(r["shots"]) == 3 and r["master_secs"] + sum(s["secs"] for s in r["shots"]) == 8 and r["scene_seconds"] == 8, str(r)[:300])
check("route: the model is called as a film call with the open house and brand mode", seen["kw"].get("film") is True and seen["kw"].get("house_id") == "h1" and seen["kw"].get("brand_mode") == "grounded")
check("route: the model was given the scene's seconds and the position rule", "8 seconds" in seen["messages"][0]["content"] and "STATE THE CAMERA POSITION" in seen["messages"][0]["content"])
seen["reply"] = "Sure!\n```json\n" + json.dumps(GOOD) + "\n```"
check("route: a fenced reply with chatter around it still works", len(call()["shots"]) == 3)
check("route: n_shots asks for fewer", len(call(n_shots=1)["shots"]) == 1)
check("route: n_shots above what the scene can hold is clamped (6s scene -> at most 2 extras)", len(call(scene_seconds=6, n_shots=9)["shots"]) == 2)
rs = call(is_signoff=True)
check("route: the sign-off scene returns no shots and says why", rs["shots"] == [] and "sign-off" in rs["reason"])
rs2 = call(scene={**row, "beat_role": "brand"})
check("route: a scene marked as the sign-off by its own beat role is also refused", rs2["shots"] == [] and "sign-off" in rs2["reason"])
r3 = call(scene_seconds=3)
check("route: a scene under 4s returns no shots and says why (model not called)", r3["shots"] == [] and "too short" in r3["reason"])
check("route: a missing scene is a 400", call(scene={}).get("status") == 400)
seen["reply"] = "I cannot do that"
check("route: an unreadable reply is a 502 with a plain message", call().get("status") == 502 and "could not be read" in call().get("detail", ""))
seen["reply"] = json.dumps({"shots": [{"action": "", "camera_position": ""}]})
check("route: a reply with no usable shots is a 502 that lists why", call().get("status") == 502 and "None of the proposed shots" in call().get("detail", ""))
seen["reply"] = ""
check("route: an empty model reply is the same 502 every generator gives", call().get("status") == 502)
main.completion.has_key = lambda: False
check("route: no Anthropic key is the same 503 every generator gives", call().get("status") == 503)
main.completion.has_key = lambda: True

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
