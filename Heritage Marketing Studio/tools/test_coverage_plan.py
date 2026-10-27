#!/usr/bin/env python
"""test_coverage_plan.py -- offline checks for coverage step 1 (shots within a scene): the planner, the shot-seconds split and the
render route's wiring. No network, no credit, nothing written to the tenant.   Run:  api/.venv/Scripts/python.exe tools/test_coverage_plan.py

The first check is the important one: scenes with no `shots` must produce exactly what they produced BEFORE coverage existed
(tools/golden/coverage_golden.json was written from the unmodified code).
"""
import copy, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); sys.path.insert(0, os.path.join(ROOT, "tools"))
os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import coverage_golden as cg
import filmcut, filmvoice, main, gemini, videoprompt

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

# ---- 1. existing films are untouched (golden) --------------------------------------------------------------------------
gold = json.load(open(cg.GOLDEN, encoding="utf-8")); snap = cg.snapshot()
check("GOLDEN: planner, retime, render prompts and turn positions are byte-identical for films with no shots", snap == gold,
      str([k for k in gold if snap.get(k) != gold[k]]))

# ---- 2. split_shot_seconds --------------------------------------------------------------------------------------------
sp = filmvoice.split_shot_seconds
check("split 6s, two extras of 2s -> [2,2,2]", sp(6, [2, 2]) == ([2, 2, 2], 0), str(sp(6, [2, 2])))
check("split 8s, extras 3,3 -> master takes the remainder [2,3,3]", sp(8, [3, 3]) == ([2, 3, 3], 0), str(sp(8, [3, 3])))
check("split always sums to the scene's seconds", all(sum(sp(t, w)[0]) == t for t in range(4, 21) for w in ([2], [2, 2], [3, 5, 2], [8, 8, 8], [1], [0, 0, 0], ["x", None, 4.6])))
check("split: shortest shot is 2s", all(min(sp(t, w)[0]) >= 2 for t in range(4, 21) for w in ([1], [2, 2], [8, 8, 8], [0, 0])))
check("split: a 4s scene cannot hold 3 extras -> the last are dropped and counted", sp(4, [2, 2, 2]) == ([2, 2], 2), str(sp(4, [2, 2, 2])))
check("split: big extras give seconds back so the master keeps 2s", sp(8, [8, 8]) [0][0] >= 2 and sum(sp(8, [8, 8])[0]) == 8, str(sp(8, [8, 8])))
check("split: no extras -> the scene as one shot", sp(6, []) == ([6], 0))
check("split: garbage weights fall back to the floor", sp(10, ["x", None, -3])[0][1:] == [2, 2, 2], str(sp(10, ["x", None, -3])))
check("split: extra weights are capped at 8s", max(sp(30, [20, 20, 20])[0][1:]) == 8)

# ---- 3. the planner with shots -----------------------------------------------------------------------------------------
def vo(t): return {"kind": "vo", "text": t}
def film():
    return [{"no": 1, "visual": "Mother pours milk.", "frame_url": "/media/m1.jpg"},
            {"no": 2, "title": "Boy steps closer", "visual": "The boy steps closer with his glass.", "desc": "Morning light.", "camera": "handheld",
             "shot_size": "wide", "movement_class": "pan", "frame_url": "/media/m2.jpg", "beat_note": "curious", "audio": [vo("Mornings begin the same way, with a glass of fresh milk poured at the kitchen counter and a promise kept to every family at the table.")],
             "shots": [{"visual": "Close-up of the boy's face.", "shot_size": "close", "camera": "slow push-in", "secs": 2, "frame_url": "/media/m2_1.jpg"},
                       {"visual": "Detail: his hand on the glass.", "shot_size": "detail", "secs": 2, "frame_url": "/media/m2_2.jpg"}]},
            {"no": 3, "visual": "A technician lowers a pipette.", "frame_url": "/media/m3.jpg"},
            {"no": 4, "visual": "Colleagues check a clipboard.", "frame_url": "/media/m4.jpg"},
            {"no": 5, "visual": "The boy drinks.", "frame_url": "/media/m5.jpg"},
            {"no": 6, "visual": "The pack, front-on.", "frame_url": "/media/m6.jpg",
             "shots": [{"visual": "A second angle of the pack.", "secs": 2}, {"visual": "A third.", "secs": 2}]}]
rows = film(); total, _ = filmvoice.retime(rows, target_total=30); per = filmvoice.scene_seconds(rows, target_total=30)
segs = filmcut.plan_by_scene(rows, per)
bare = filmcut.plan_by_scene([{k: v for k, v in r.items() if k != "shots"} for r in film()], per)
by_no = lambda ss, n: [s for s in ss if (s["scenes"][0] or {}).get("no") == n]
check("scene 2 became 3 segments; the others kept their count", [len(by_no(segs, n)) for n in range(1, 7)] == [len(by_no(bare, n)) for n in range(1, 7)][:1] + [3] + [len(by_no(bare, n)) for n in range(3, 7)], str([len(by_no(segs, n)) for n in range(1, 7)]))
check("INVARIANT: every scene's total seconds is unchanged by coverage", all(sum(s["seconds"] for s in by_no(segs, n)) == sum(s["seconds"] for s in by_no(bare, n)) for n in range(1, 7)))
check("INVARIANT: the film's total is unchanged", sum(s["seconds"] for s in segs) == sum(s["seconds"] for s in bare) == total)
check("shots after the first are marked continues", [s["continues"] for s in by_no(segs, 2)] == [False, True, True])
check("INVARIANT: one role per scene (roles attach to the moment)", len({s["role"] for s in by_no(segs, 2)}) == 1)
check("scenes with no shots keep exactly their old role and seconds", all((s["role"], s["seconds"]) == (b["role"], b["seconds"]) for n in (1, 3, 4, 5) for s, b in zip(by_no(segs, n), by_no(bare, n))))
s2 = by_no(segs, 2); master, x1, x2 = (s["scenes"][0] for s in s2)
check("shot 1 IS the scene's own row (its approved frame stays valid)", master is rows[1])
check("shot 2 carries its own visual, size, camera and frame", x1["visual"] == "Close-up of the boy's face." and x1["shot_size"] == "close" and x1["camera"] == "slow push-in" and x1["frame_url"] == "/media/m2_1.jpg")
check("shot 3 does NOT inherit the master's camera, size, movement, title or description",
      all(k not in x2 for k in ("camera", "movement_class", "title", "desc")) and x2["shot_size"] == "detail" and x2["visual"].startswith("Detail"), str(x2))
check("an extra shot keeps the scene's number and beat direction", x1["no"] == 2 and x1["beat_note"] == "curious")
check("an extra shot carries no spoken words (the words stay with the scene)", x1["dialogue"] == "" and x1["audio"] == [] and rows[1]["audio"][0]["text"])
check("an extra shot knows its place", (x1["shot"], x1["shots_total"], x2["shot"]) == (1, 3, 2))
check("the planner does not mutate the script row", rows[1]["shots"][0]["visual"] == "Close-up of the boy's face." and "shot" not in rows[1])
s6 = by_no(segs, 6)
check("the sign-off scene is never split", len(s6) == len(by_no(bare, 6)) and s6[0].get("collapsed_shots") == 2 and s6[0]["role"] == "brand")
# explicit sign-off in the middle of the film
mid = [{"no": 1, "visual": "a"}, {"no": 2, "visual": "b", "beat_role": "brand", "shots": [{"visual": "x"}]}, {"no": 3, "visual": "c", "shots": [{"visual": "y", "secs": 2}]}]
ps = filmvoice.scene_seconds(mid, 20); pm = filmcut.plan_by_scene(mid, ps)
check("an explicit mid-film sign-off is never split; a normal scene after it is", len(by_no(pm, 2)) == 1 and len(by_no(pm, 3)) >= 2, str([len(by_no(pm, n)) for n in (1, 2, 3)]))
# too short a scene
short = [{"no": 1, "visual": "a", "shots": [{"visual": "b", "secs": 2}, {"visual": "c", "secs": 2}, {"visual": "d", "secs": 2}]}, {"no": 2, "visual": "end"}]
pshort = filmcut.plan_by_scene(short, [4, 4])
check("a 4s scene with 3 extras keeps 2 shots and says 2 were dropped", len(by_no(pshort, 1)) == 2 and by_no(pshort, 1)[0].get("dropped_shots") == 2, str(by_no(pshort, 1)))
# long shot splits into continuing beats
long_ = [{"no": 1, "visual": "a", "shots": [{"visual": "b", "secs": 8}]}, {"no": 2, "visual": "end"}]
pl = by_no(filmcut.plan_by_scene(long_, [20, 4]), 1)
check("a shot longer than 8s becomes continuing beats, total preserved", sum(s["seconds"] for s in pl) == 20 and all(s["seconds"] <= 8 for s in pl) and all(s["continues"] for s in pl[1:]), str(pl))
check("empty / non-dict shots are ignored; more than 3 extras are capped at 3",
      len(filmcut.extra_shots({"shots": [{"visual": ""}, "x", None, {"visual": "ok"}]})) == 1 and len(filmcut.extra_shots({"shots": [{"visual": str(i)} for i in range(9)]})) == 3)
check("a row with no shots reports none", filmcut.extra_shots({"visual": "x"}) == [] and filmcut.extra_shots({"shots": "nope"}) == [])
check("the two new shot sizes exist beside the four old ones", all(k in main._SHOT_SIZES for k in ("wide", "medium", "close", "product", "detail", "over")))
check("the old shot-size sentences are unchanged", main._SHOT_SIZES["wide"].startswith("Framing: a WIDE shot") and main._SHOT_SIZES["product"].startswith("Framing: a PRODUCT HERO"))

# ---- 3b. SKIP: a shot the person switched off is kept in the script but never planned, rendered or counted -----------------------
sk = film(); sk[1]["shots"][0]["skip"] = True
psk = filmcut.plan_by_scene(sk, per)
check("SKIP: a skipped extra shot is not planned (scene 2: 3 segments -> 2)", len(by_no(psk, 2)) == 2, str([len(by_no(psk, n)) for n in range(1, 7)]))
check("SKIP: INVARIANT the scene's seconds are unchanged and the film total too", sum(s["seconds"] for s in by_no(psk, 2)) == sum(s["seconds"] for s in by_no(segs, 2)) and sum(s["seconds"] for s in psk) == total)
check("SKIP: the shot that stays keeps its own picture and the board number it had (shot 3, not 2)", by_no(psk, 2)[1]["scenes"][0]["visual"].startswith("Detail") and by_no(psk, 2)[1]["scenes"][0]["shot_no"] == 3 and by_no(psk, 2)[1]["scenes"][0]["frame_url"] == "/media/m2_2.jpg")
check("SKIP: unskipped shots report their own board number (2 and 3)", [s["scenes"][0].get("shot_no") for s in by_no(segs, 2)[1:]] == [2, 3])
check("SKIP: the skipped shot stays in the row (nothing is deleted)", sk[1]["shots"][0]["visual"] == "Close-up of the boy's face." and len(sk[1]["shots"]) == 2)
allskip = film()
for r_ in allskip:
    for s_ in r_.get("shots") or []:
        s_["skip"] = True
check("SKIP: INVARIANT every extra skipped -> planned exactly as a film with no shots", [(s["seconds"], s["continues"], s.get("role")) for s in filmcut.plan_by_scene(allskip, per)] == [(s["seconds"], s["continues"], s.get("role")) for s in bare])
check("SKIP: extra_shots leaves skipped ones out; extra_shots_indexed keeps each one's place",
      [s["visual"] for s in filmcut.extra_shots(sk[1])] == ["Detail: his hand on the glass."] and [i for i, _ in filmcut.extra_shots_indexed(sk[1])] == [1])
check("SKIP: the 3-extra cap is applied AFTER skipping", len(filmcut.extra_shots({"shots": [{"visual": "a", "skip": True}] + [{"visual": str(i)} for i in range(4)]})) == 3)

# ---- 4. the turn position does not move with coverage --------------------------------------------------------------------
check("INVARIANT: music_on_turn position is the same with and without shots", main._turn_at_from_rows(film(), "30s") == main._turn_at_from_rows([{k: v for k, v in r.items() if k != "shots"} for r in film()], "30s"))

# ---- 5. live-action scenes ignore shots ---------------------------------------------------------------------------------
real_for_scene = main.shots.for_scene
main.shots.for_scene = lambda no: {"id": "s1", "url": "/x"} if int(no) == 2 else None
pr = main._rows_for_planning(film())
check("a scene with a signed live shot loses its coverage shots", "shots" not in pr[1] and pr[1]["no"] == 2)
check("other scenes (with or without shots) come back untouched", pr[5].get("shots") and pr[0] is not None and "shots" not in film()[0])
main.shots.for_scene = real_for_scene
plain_rows = film()[:1]
check("a film with no shots is returned as the same objects", main._rows_for_planning(plain_rows)[0] is plain_rows[0])

# ---- 6. the real render route, generators stubbed ----------------------------------------------------------------------------
calls, synthed = [], []
gemini.available = lambda: True
gemini.video = lambda prompt, **kw: (calls.append({"prompt": prompt, **{k: kw.get(k) for k in ("seconds", "image_ref", "tier")}}), f"/media/shot-{len(calls)}.mp4")[1]
main._record_made = lambda *a, **k: None
main._music_bed = lambda *a, **k: ("", "")
filmvoice.synth = lambda segs, *a, **k: (synthed.extend(segs), (0, []))[1]
def run(rows_, stitch=None, **extra):
    calls.clear(); synthed.clear()
    filmcut.stitch = (lambda urls, lengths=None: stitch) if stitch is not None else (lambda urls, lengths=None: None)
    payload = {"scenes": rows_, "aspect": "16:9", "duration": "30s", "engines": {"video": "google"}, "tier": "lite", "script": {"logline": "A morning."}, **extra}
    try:
        res = main._produce_video_sync(payload)
    except Exception as e:
        return {"raised": f"{type(e).__name__}: {e}"}
    return res if isinstance(res, dict) else {"status": res.status_code, **json.loads(res.body)}
res = run(film())
check("route: one generation per shot (6 scenes + 2 extra; the sign-off's two extras are not used)", len(calls) == 8, str(len(calls)))
role2 = by_no(segs, 2)[0]["role"]; role_text = videoprompt._ROLE_NOTE.get(role2, "")
c_master = [c for c in calls if "steps closer" in c["prompt"]]; c_x1 = [c for c in calls if "Close-up of the boy's face" in c["prompt"]]; c_x2 = [c for c in calls if "Detail: his hand" in c["prompt"]]
check("route: each shot is animated from ITS OWN frame", c_master[0]["image_ref"] == "/media/m2.jpg" and c_x1[0]["image_ref"] == "/media/m2_1.jpg" and c_x2[0]["image_ref"] == "/media/m2_2.jpg")
check("route: each shot is asked for its own seconds (2s extras are asked as 2; the engine floors to 3 and the stitch trims) and they add up to the scene",
      c_x1[0]["seconds"] == 2 and c_x2[0]["seconds"] == 2 and c_master[0]["seconds"] + 4 == per[1], str([c["seconds"] for c in c_master + c_x1 + c_x2]) + f" scene={per[1]}")
check("route: an extra shot's prompt does not carry the master's visual or description", "steps closer" not in c_x1[0]["prompt"] and "Morning light" not in c_x1[0]["prompt"])
check("route: an extra shot's prompt carries its own camera", "slow push-in" in c_x1[0]["prompt"], c_x1[0]["prompt"][:400])
check("route: an extra shot is told it continues the previous shot", "continues the previous shot" in c_x1[0]["prompt"] and "continues the previous shot" not in c_master[0]["prompt"])
check("route: the role sentence appears on the scene's FIRST shot only", (role_text in c_master[0]["prompt"]) and role_text not in c_x1[0]["prompt"] and role_text not in c_x2[0]["prompt"], role_text)
check("route: the scene's beat direction reaches every shot", all("Direction: curious." in c["prompt"] for c in (c_master[0], c_x1[0], c_x2[0])))
detail = str(res.get("detail", ""))
check("route: the sign-off's ignored shots are reported", "scene 6 is the sign-off" in detail, detail[:300])
# the sign-off scene was one shot: exactly one call mentions it
check("route: the sign-off scene was generated once", len([c for c in calls if "pack, front-on" in c["prompt"]]) == 1 and not [c for c in calls if "second angle of the pack" in c["prompt"]])
# ---- step 2: a coverage shot is NEVER rendered without its frame ------------------------------------------------------------
nf = film(); nf[1]["shots"][1].pop("frame_url")
r_nf = run(nf)
check("route: a coverage shot with no frame is held back, not drawn from words (7 generations, not 8)", len(calls) == 7 and not [c for c in calls if "Detail: his hand" in c["prompt"]], str(len(calls)))
check("route: the held-back shot says why, by scene and shot", "scene 2, shot 3: no frame, so this shot was not rendered" in str(r_nf.get("detail")), str(r_nf.get("detail"))[:300])
check("route: the cut is reported incomplete with the 'missing a shot' wording (the scene still has two shots)", "INCOMPLETE CUT" in str(r_nf.get("detail")) and "scene(s) 2 are missing a shot" in str(r_nf.get("detail")), str(r_nf.get("detail"))[:400])
sc_nf = [c for c in r_nf["shot_clips"] if c["no"] == 2]
check("route: shot_clips still lists the held-back shot, marked not ok", [c["ok"] for c in sc_nf] == [True, True, False] and sc_nf[2]["url"] == "", str(sc_nf))
# a master scene (no coverage) without a frame keeps today's behaviour: the text-to-video branch, which also uses the new shot sizes
plain_nf = film(); plain_nf[2].pop("frame_url"); plain_nf[2]["shot_size"] = "detail"
run(plain_nf)
c_pl = [c for c in calls if "pipette" in c["prompt"]][0]
check("route: an ordinary scene with no frame still goes through the text-to-video branch, and the new 'detail' size reaches it", not c_pl["image_ref"] and "DETAIL INSERT" in c_pl["prompt"], c_pl["prompt"][:300])

# ---- step 2: one record per shot in the response -------------------------------------------------------------------------------
res = run(film(), stitch="film-fake.mp4")
sc = res["shot_clips"]
check("shot_clips: one record per planned shot, in film order", [(c["no"], c["shot"]) for c in sc] == [(1, 1), (2, 1), (2, 2), (2, 3), (3, 1), (4, 1), (5, 1), (6, 1)], str([(c["no"], c["shot"]) for c in sc]))
check("shot_clips: a scene's shots add up to the scene's seconds and the film's to the total", sum(c["seconds"] for c in sc if c["no"] == 2) == per[1] and sum(c["seconds"] for c in sc) == total)
check("shot_clips: urls, provider, from_frame and role are filled in", all(c["ok"] and c["url"] and c["provider"] == "google" and c["from_frame"] and c["role"] for c in sc), str(sc[1]))
check("shot_clips: later shots are marked continues, the first of a scene is not", [c["continues"] for c in sc if c["no"] == 2] == [False, True, True])
check("shot_clips: the old `clips` list is unchanged (bare urls of the shots that rendered, in order)", res["clips"] == [c["url"] for c in sc if c["ok"]])
check("shot_clips: also present on the unstitched fallback response", "shot_clips" in run(film()))

# ---- step 2: a shot that fails is named by scene and shot, the rest of the film still ships -----------------------------------------
real_video, real_err = gemini.video, gemini.video_error
def flaky(prompt, **kw):
    if "Detail: his hand" in prompt:
        calls.append({"prompt": prompt, **{k: kw.get(k) for k in ("seconds", "image_ref", "tier")}}); return None
    return real_video(prompt, **kw)
gemini.video, gemini.video_error = flaky, (lambda: "Google's safety filter blocked this shot (no video returned)")
r_fail = run(film())
d = str(r_fail.get("detail"))
check("failure: the log names the shot by scene and place", "scene 2, shot 3 on Google: Google's safety filter blocked this shot" in d, d[:400])
check("failure: the cut is incomplete and says the scene lost a shot", "INCOMPLETE CUT" in d and "scene(s) 2 are missing a shot" in d and "1 of 8 shots did not render" in d, d[:400])
check("failure: seven shots still rendered", len([c for c in r_fail["shot_clips"] if c["ok"]]) == 7)
# an ordinary film keeps the old wording exactly
plain = [{"no": i + 1, "visual": f"scene {i + 1}", "frame_url": f"/media/p{i}.jpg"} for i in range(4)]
def flaky2(prompt, **kw):
    if "scene 3" in prompt:
        return None
    return real_video(prompt, **kw)
gemini.video = flaky2
d2 = str(run(plain).get("detail"))
check("failure on an ordinary film: the old wording, byte for byte ('scene(s) 3 are missing and this film is')", "so scene(s) 3 are missing and this film is" in d2 and "shot 3: no URL returned" in d2, d2[:400])
gemini.video, gemini.video_error = real_video, real_err

# dropped shots are reported
tiny = [{"no": 1, "visual": "a", "frame_url": "/media/a.jpg", "shots": [{"visual": "b", "secs": 2, "frame_url": "/media/b.jpg"}] * 3},
        {"no": 2, "visual": "b", "frame_url": "/media/c.jpg"}, {"no": 3, "visual": "c", "frame_url": "/media/d.jpg"}, {"no": 4, "visual": "d", "frame_url": "/media/e.jpg"}]
r_tiny = run(tiny, duration="10s")
check("route: a scene too short for its shots says so", "extra shot(s) left out" in str(r_tiny.get("detail", "")), str(r_tiny)[:300])
# the shot cap
many = [{"no": i + 1, "visual": f"s{i}", "shots": [{"visual": "x"}, {"visual": "y"}, {"visual": "z"}]} for i in range(13)]   # 13 x 4 = 52 shots
rc = run(many)
check("route: more than 48 shots is refused with 400, nothing generated", rc.get("status") == 400 and "capped at 48" in str(rc.get("detail")) and not calls, str(rc)[:200])
check("route: a film with 24 scenes and no shots is not affected by the shot cap", len(run([{"no": i + 1, "visual": f"s{i}"} for i in range(12)]).get("detail", "") or "") >= 0 and len(calls) == 12)

# ---- 7. the scene's words lie across ALL its shots ------------------------------------------------------------------------
fv = film()
res = run(fv, stitch="film-fake.mp4", duration="30s")
rows_t, _ = fv, filmvoice.retime(fv, target_total=30)
per_t = filmvoice.scene_seconds(fv, target_total=30)
win_start = sum(per_t[:1]); win_end = win_start + per_t[1]
line = [s for s in synthed if "Mornings begin" in s.text]
check("voice: scene 2's line was handed to the voice", len(line) == 1, str(len(synthed)))
if line:
    check("voice: the line spans the scene's WHOLE window (all three shots), not just shot 1", abs(line[0].start - win_start) < 0.01 and abs(line[0].end - win_end) < 0.01,
          f"line {line[0].start}-{line[0].end} vs window {win_start}-{win_end}")

# ---- 8. OPT-IN shots on the sign-off scene ----------------------------------------------------------------------------------------
def so_film(opt_in):
    f = film()
    f[5] = {**f[5], "visual": "The Heritage pouch beside a glass; a boy's hand enters frame to lift the glass.", "frame_url": "/media/so0.jpg",
            "audio": [vo("Heritage. Health and happiness, in every glass, every morning, for every family that trusts us with the start of their day.")],
            "shots": [{"visual": "Close on the boy's hand lifting the glass.", "shot_size": "close", "camera": "slow push-in", "secs": 2, "frame_url": "/media/so1.jpg"},
                      {"visual": "The pouch square to camera, nothing in front of it.", "shot_size": "product", "camera": "locked-off", "secs": 2, "frame_url": "/media/so2.jpg"}]}
    if opt_in: f[5]["signoff_shots"] = True
    return f
HOLD = "Hold the shot locked and still"; CLOSING = "closing product shot"
rows_so = so_film(True); filmvoice.retime(rows_so, target_total=30); per_so = filmvoice.scene_seconds(rows_so, target_total=30)
seg_so = [s for s in filmcut.plan_by_scene(rows_so, per_so) if (s["scenes"][0] or {}).get("no") == 6]
check("sign-off OPT-IN: the scene is expanded into 3 shots, still one role (brand), total seconds unchanged",
      len(seg_so) == 3 and {s["role"] for s in seg_so} == {"brand"} and sum(s["seconds"] for s in seg_so) == per_so[5], str(seg_so))
check("sign-off OPT-IN: only the LAST segment is marked as the scene's end", [bool(s.get("scene_last")) for s in seg_so] == [False, False, True])
rows_no = so_film(False); filmvoice.retime(rows_no, target_total=30); per_no = filmvoice.scene_seconds(rows_no, target_total=30)
seg_no = [s for s in filmcut.plan_by_scene(rows_no, per_no) if (s["scenes"][0] or {}).get("no") == 6]
check("sign-off NOT opted in: still collapsed to one shot (default unchanged)", len(seg_no) == 1 and seg_no[0].get("collapsed_shots") == 2 and not seg_no[0].get("scene_last"))
run(so_film(True), duration="30s")
p_master = [c for c in calls if "boy's hand enters frame" in c["prompt"]][0]["prompt"]
p_mid = [c for c in calls if "Close on the boy's hand" in c["prompt"]][0]["prompt"]
p_last = [c for c in calls if "pouch square to camera" in c["prompt"]][0]["prompt"]
check("sign-off OPT-IN: the locked-still pack hold and the 'closing product shot' sentence are on the LAST shot only",
      HOLD in p_last and CLOSING in p_last and HOLD not in p_master and CLOSING not in p_master and HOLD not in p_mid and CLOSING not in p_mid, p_last[:300])
check("sign-off OPT-IN: the middle shot keeps its own camera movement", "slow push-in" in p_mid and HOLD not in p_mid)
run(so_film(False), duration="30s")
p_single = [c for c in calls if "boy's hand enters frame" in c["prompt"]][0]["prompt"]
check("sign-off NOT opted in: the single sign-off shot keeps the pack hold and the closing sentence exactly as before", HOLD in p_single and CLOSING in p_single and len([c for c in calls if "boy's hand enters frame" in c["prompt"]]) == 1)

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
