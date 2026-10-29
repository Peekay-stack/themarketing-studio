#!/usr/bin/env python
"""test_builder_s0.py -- offline checks for film-builder slice S0 (FILM_BUILDER_PLAN.md): takes.py (the saved builder state), the `video_builder` film field, and the two INERT payload keys on
_produce_video_sync: `only_shot` (render one shot, return before the stitch) and `use_clips` (assemble from chosen clips, never generate). Generators are stubbed; nothing is written to the tenant
(the film store is pointed at a temp folder). The golden test (test_coverage_plan.py) proves a film without these keys renders exactly as before.
Run:  api/.venv/Scripts/python.exe tools/test_builder_s0.py
"""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import takes, filmscript, filmcut, filmvoice, main, gemini

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

# ---- takes.py ------------------------------------------------------------------------------------------------------------------------
check("valid_key: master '3' and extra '3.2' only", [takes.valid_key(k) for k in ("0", "12", "3.1", "3.12", "a", "3.", ".1", "1.2.3", "", "1000")] == [True, True, True, True, False, False, False, False, False, False])
ft = lambda i, **k: {"id": f"fr_{i}", "url": f"/media/frame-{i}.jpg", "status": "done", **k}
doc = {"frames": {"0": [ft(1), ft(2), {"id": "x", "url": "", "status": "done"}, {"id": "y", "url": "/media/z.jpg", "status": "rendering"}, "junk"], "bad key": [ft(3)], "2.1": [ft(4)]},
       "frame_chosen": {"0": "fr_2", "2.1": "nope"}}
n = takes.normalise(doc)
check("normalise: frame takes keep only real ones (a url, not mid-render), bad keys and junk are dropped", [t["id"] for t in n["frames"]["0"]] == ["fr_1", "fr_2"] and "bad key" not in n["frames"] and list(n["frames"]) == ["0", "2.1"], str(n["frames"].keys()))
check("normalise: a chosen id that exists is kept, one that does not is un-chosen", n["frame_chosen"] == {"0": "fr_2"})
check("normalise: nothing in it -> None (a film that never used the builder stores nothing)", takes.normalise({}) is None and takes.normalise(None) is None and takes.normalise({"frames": {}}) is None and takes.normalise("x") is None)
# the page's per-kind fingerprints (why a frame is out of date) survive a save, and junk in them cannot get in
pt = takes.normalise({"frames": {"0": [ft(1, recipe="abc:1", parts={"words": "1a2b", "dept": "zz9", "bad": 5, "": "x", "loc": ["no"]})]}})["frames"]["0"][0]
check("normalise: a frame take keeps its fingerprints (strings only, short)", pt["parts"] == {"words": "1a2b", "dept": "zz9"}, str(pt.get("parts")))
check("normalise: a take with no fingerprints gets an empty dict, and a non-dict is dropped to {}", takes.normalise({"frames": {"0": [ft(1)]}})["frames"]["0"][0]["parts"] == {} and takes.normalise({"frames": {"0": [ft(1, parts="x")]}})["frames"]["0"][0]["parts"] == {})
check("normalise: fingerprints are capped at 12 kinds and 16 characters each", len(takes._parts({f"k{i}": "v" * 40 for i in range(30)})) == 12 and all(len(v) == 16 for v in takes._parts({"a": "v" * 40}).values()))
check("normalise: a data: URI is never stored in a take", takes.normalise({"frames": {"0": [ft(1, url="data:image/png;base64," + "A" * 50)]}}) is None)
many = {"frames": {"0": [ft(i) for i in range(30)]}, "frame_chosen": {"0": "fr_0"}}
nm = takes.normalise(many)
check("normalise: at most 12 takes per shot, the CHOSEN one is never the one dropped, oldest others go first",
      len(nm["frames"]["0"]) == 12 and nm["frames"]["0"][0]["id"] == "fr_0" and nm["frame_chosen"]["0"] == "fr_0", str([t["id"] for t in nm["frames"]["0"]]))
ct = lambda i, **k: {"id": f"tk_{i}", "url": f"/media/shot-{i}.mp4", "status": "done", "seconds": 4, "tier": "draft", "engine": "omni", **k}
d2 = takes.normalise({"takes": {"0": [ct(1), ct(2, status="rendering", url=""), ct(3, status="done", url=""), ct(4, tier="weird", engine="x", mode="y")], "1": [ct(5)]},
                      "chosen": {"0": "tk_1", "1": "tk_9"}, "trim": {"0": {"in": 0.5, "out": 3.0}, "1": {"in": 1, "out": 2}, "0.5": {"in": 2, "out": 1}}, "budget": {"cap_usd": "5", "spent_usd": -3}})
tk = {t["id"]: t for t in d2["takes"]["0"]}
check("normalise: a clip take that was RENDERING is 'interrupted' (the job died with its server), a done one with no file is an error", tk["tk_2"]["status"] == "interrupted" and tk["tk_3"]["status"] == "error")
check("normalise: unknown tier / engine / mode fall back to draft / omni / frame", tk["tk_4"]["tier"] == "draft" and tk["tk_4"]["engine"] == "omni" and tk["tk_4"]["mode"] == "frame")
check("normalise: trim kept only for a CHOSEN shot and only when out > in; budget clamped", list(d2["trim"]) == ["0"] and d2["trim"]["0"] == {"in": 0.5, "out": 3.0} and d2["budget"] == {"cap_usd": 5.0, "spent_usd": 0.0}, str(d2["trim"]) + str(d2["budget"]))
check("normalise: an errored take can never stay chosen", takes.normalise({"takes": {"0": [ct(3, url="")]}, "chosen": {"0": "tk_3"}})["chosen"] == {} if takes.normalise({"takes": {"0": [ct(3, url="")]}, "chosen": {"0": "tk_3"}}) else True)
check("normalise: idempotent", takes.normalise(takes.normalise(doc)) == takes.normalise(doc) and takes.normalise(d2) == d2)
check("estimate_clip: Omni Draft 4 s = 0.136, Final 4 s = 0.404 (measured rates x seconds)", takes.estimate_clip(4, "draft") == 0.136 and takes.estimate_clip(4, "final") == 0.404)
check("estimate_clip: a 2 s shot is billed as the 3 s Omni floor", takes.estimate_clip(2, "draft") == 0.102 and takes.estimate_clip(0) == 0.0)
check("estimate_clip: Kling is NOT measured, so there is no number (never a guess)", takes.estimate_clip(4, "draft", "kling") is None)
check("chosen_frame / chosen_clip / use_clips_for", takes.chosen_frame(n, "0")["id"] == "fr_2" and takes.chosen_frame(n, "5") is None and takes.chosen_clip(d2, "0")["id"] == "tk_1" and takes.chosen_clip(None, "0") is None
      and takes.use_clips_for(d2) == {"0": [{"url": "/media/shot-1.mp4", "seconds": 4.0, "mode": "frame", "in": 0.5, "out": 3.0}]} and "in" not in takes.use_clips_for(d2, trims=False)["0"][0])

# ---- the film field ------------------------------------------------------------------------------------------------------------------
tmp = tempfile.mkdtemp()
filmscript._path = lambda house_id: os.path.join(tmp, f"{house_id}.json")
blank = filmscript.load("h1")
check("filmscript: video_builder is a field with an empty default", "video_builder" in filmscript.FIELDS and blank["video_builder"] is None)
filmscript.save("h1", {"video_builder": doc, "full_script": [{"no": 1}]})
check("filmscript: the page's builder state is normalised AT THE STORE and read back", filmscript.load("h1")["video_builder"] == takes.normalise(doc))
filmscript.save("h1", {"full_script": [{"no": 1}, {"no": 2}]})
check("filmscript: a save from a page that does not send the field keeps what is stored (absent-key guard)", filmscript.load("h1")["video_builder"] == takes.normalise(doc))
filmscript.save("h1", {"video_builder": {}})
check("filmscript: an explicitly empty builder clears it", filmscript.load("h1")["video_builder"] is None)

# ---- the render function: only_shot and use_clips -------------------------------------------------------------------------------------
calls, synthed, stitched = [], [], []
gemini.available = lambda: True
gemini.video = lambda prompt, **kw: (calls.append({"prompt": prompt, **{k: kw.get(k) for k in ("seconds", "image_ref", "tier")}}), f"/media/shot-gen{len(calls)}.mp4")[1]
main._record_made = lambda *a, **k: None
main._music_bed = lambda *a, **k: ("", "")
filmvoice.synth = lambda segs, *a, **k: (synthed.extend(segs), (0, []))[1]
def fake_stitch(urls, lengths=None):
    stitched.append((list(urls), list(lengths or []))); return None
filmcut.stitch = fake_stitch
def film():
    return [{"no": 1, "visual": "Mother pours milk.", "frame_url": "/media/f0.jpg"},
            {"no": 2, "visual": "The boy steps closer with his glass.", "frame_url": "/media/f1.jpg", "camera": "handheld",
             "shots": [{"visual": "Close-up of the boy's face.", "shot_size": "close", "secs": 2, "frame_url": "/media/f1_1.jpg"},
                       {"visual": "Detail: his hand on the glass.", "shot_size": "detail", "secs": 2, "frame_url": "/media/f1_2.jpg", "skip": True}]},
            {"no": 3, "visual": "The pack, front-on.", "beat_role": "brand", "frame_url": "/media/f2.jpg"}]
def run(rows, **extra):
    calls.clear(); synthed.clear(); stitched.clear()
    payload = {"scenes": rows, "aspect": "16:9", "duration": "30s", "engines": {"video": "google"}, "tier": "lite", "script": {"logline": "A morning."}, **extra}
    try:
        res = main._produce_video_sync(payload)
    except Exception as e:
        return {"raised": f"{type(e).__name__}: {e}"}
    return res if isinstance(res, dict) else {"status": res.status_code, **json.loads(res.body)}

r = run(film(), only_shot="1")
check("only_shot: a scene's master shot renders exactly ONE clip, from its own frame, and returns before the stitch/voice/music",
      len(calls) == 1 and calls[0]["image_ref"] == "/media/f1.jpg" and not stitched and not synthed and r.get("shot") == "1" and r["ok"] is True and len(r["clips"]) == 1, str(r)[:300])
check("only_shot: the clip record has its url, seconds, provider, frame flag and the tier", r["clips"][0]["url"] == "/media/shot-gen1.mp4" and r["clips"][0]["provider"] == "google" and r["clips"][0]["from_frame"] is True and r["tier"] == "lite" and r["model"].startswith("Gemini Omni"), str(r))
r = run(film(), only_shot="1.1")
check("only_shot: an EXTRA shot ('<position>.<k>') renders from ITS OWN frame with its own prompt", len(calls) == 1 and calls[0]["image_ref"] == "/media/f1_1.jpg" and "Close-up of the boy" in calls[0]["prompt"] and r["shot"] == "1.1" and r["ok"], str(calls)[:300])
r = run(film(), only_shot="1.2")
check("only_shot: a SKIPPED shot is not in the plan -> 404 with a reason, and nothing was generated", r.get("status") == 404 and "not in the plan" in r["detail"] and not calls, str(r))
r = run(film(), only_shot="7")
check("only_shot: a shot that does not exist -> 404, nothing generated", r.get("status") == 404 and not calls)
nf = film(); nf[1]["shots"][0].pop("frame_url")
r = run(nf, only_shot="1.1")
check("only_shot: a coverage shot with no frame is HELD BACK (never drawn from words) and the page is told why", not calls and r["ok"] is False and r["clips"][0]["url"] == "" and "no frame" in " ".join(r["errors"]), str(r)[:300])
long_ = [{"no": 1, "visual": "A long quiet scene.", "frame_url": "/media/f0.jpg"}]
r = run(long_, only_shot="0", duration="20s")
check("only_shot: a long scene (several continuing beats) renders ALL its beats for that one shot, numbered", len(r["clips"]) >= 2 and [c["beat"] for c in r["clips"]] == list(range(1, len(r["clips"]) + 1)) and len(calls) == len(r["clips"]), str(r)[:300])

import shutil
tmpd = tempfile.mkdtemp()
def plan_keys(rows):
    """[(key, beat ordinal)] for every planned segment, the way the render keys them."""
    segs = filmcut.plan_by_scene(main._rows_for_planning(rows), filmvoice.scene_seconds(rows, target_total=30))
    out, seen = [], {}
    for sg in segs:
        row = (sg["scenes"] or [{}])[0]
        pos = next(i for i, r in enumerate(rows) if int(r.get("no")) == int(row.get("no")))
        k = int(row.get("shot") or 0); key = f"{pos}.{k}" if k else str(pos)
        out.append((key, seen.get(key, 0), sg["seconds"])); seen[key] = seen.get(key, 0) + 1
    return out
files = {}
def make_clips(rows):
    chosen = {}
    for key, beat, secs in plan_keys(rows):
        name = f"/media/chosen-{key}-{beat}.mp4"; path = os.path.join(tmpd, f"c-{key}-{beat}.mp4"); open(path, "wb").write(b"x"); files[name] = path
        chosen.setdefault(key, []).append({"url": name, "seconds": secs})
    return chosen
real_local = gemini.local_path
gemini.local_path = lambda u: files.get(str(u)) or real_local(u)
durs = {}
filmcut.ffmpeg_exe = lambda: "ffmpeg"
filmcut.probe_seconds = lambda exe, p: durs.get(p, 0.0)
chosen = make_clips(film())
check("assembly fixture: every planned beat of every ACTIVE shot has a chosen clip, the skipped extra has none", len(chosen) == 4 and "1.2" not in chosen, str(sorted(chosen)))
gemini.available = lambda: False
saved_fal = os.environ.pop("FAL_KEY", None)
r = run(film(), use_clips=chosen)
check("use_clips: assembling NEVER generates (zero engine calls) and needs no video provider", not calls and r.get("status") != 501, str(r)[:200])
flat = [c["url"] for k in ("0", "1", "1.1", "2") for c in chosen.get(k, [])]
check("use_clips: the stitch gets the chosen clips in script order (master, its extra, next scene) with the planned beat lengths",
      len(stitched) == 1 and stitched[0][0] == flat and len(stitched[0][1]) == len(flat) and all(x > 0 for x in stitched[0][1]), str(stitched)[:300])
check("use_clips: a skipped shot is simply absent (no key needed for it)", len(stitched[0][0]) == len(flat))
partial = {k: v for k, v in chosen.items() if k != "1.1"}
r = run(film(), use_clips=partial)
check("use_clips: a shot with no chosen clip REFUSES the assembly (400) and names the shot; nothing is generated, stitched or voiced",
      r.get("status") == 400 and "scene 2, shot 2: no chosen clip" in r["detail"] and "Can't assemble yet" in r["detail"] and not calls and not stitched and not synthed, str(r)[:300])
r = run(film(), use_clips={})
check("use_clips: an empty set is a 400 naming every shot (never a short film)", r.get("status") == 400 and "no chosen clip" in r["detail"] and not calls, str(r)[:200])
gone = {k: [dict(c) for c in v] for k, v in chosen.items()}
os.remove(files[gone["1.1"][0]["url"]])
r = run(film(), use_clips=gone)
check("use_clips: a chosen clip whose FILE is gone is refused (400) with the shot named", r.get("status") == 400 and "scene 2, shot 2: the chosen clip's file is missing" in r["detail"] and not stitched, str(r)[:300])
chosen = make_clips(film())
short = {k: [dict(c) for c in v] for k, v in chosen.items()}
victim = short["2"][0]["url"]; plan_secs = [s for key, _, s in plan_keys(film()) if key == "2"][0]
r = run(film(), use_clips=chosen)
check("use_clips: an exactly-as-long clip changes nothing (no note)", "shorter there" not in str(r.get("detail", "")) and stitched and not any(abs(x - round(x)) > 0.01 for x in stitched[-1][1]), str(stitched[-1:]))
durs[files[victim]] = plan_secs - 2.0
r = run(film(), use_clips=short)
lens = stitched[-1][1]
check("use_clips: a chosen clip SHORTER than its planned beat shrinks that beat to the real length (the film and the voice follow the real picture) and says so",
      any(abs(x - (plan_secs - 2.0)) < 0.01 for x in lens) and "the chosen clip is" in str(r.get("detail", "")) and "shorter there" in str(r.get("detail", "")), f"{lens} {str(r.get('detail'))[:300]}")
durs.clear()
r = run(film(), use_clips=chosen, only_shot="0")
check("only_shot and use_clips together is a 400", r.get("status") == 400 and "not both" in r["detail"])
gemini.local_path = real_local
shutil.rmtree(tmpd, ignore_errors=True)
gemini.available = lambda: True
if saved_fal is not None: os.environ["FAL_KEY"] = saved_fal

# ---- inert when absent ------------------------------------------------------------------------------------------------------------------
r = run(film())
_rows = film(); _per = filmvoice.scene_seconds(_rows, target_total=30); _segs = filmcut.plan_by_scene(main._rows_for_planning(_rows), _per)
check("inert: with neither key a normal render generates exactly one clip per planned segment (the skipped extra is not planned, so not drawn)", len(calls) == len(_segs) and len(_segs) > 3 and not any("Detail: his hand" in c["prompt"] for c in calls), f"{len(calls)} vs {len(_segs)}")

# ---- the master shot's key is "0": a JSON number 0 must NEVER fall through to a full paid render ----------------------------------------------------------------
r = run(film(), only_shot=0)
check("only_shot as the NUMBER 0 means shot '0' (only that scene's beats, all from its own frame), not 'no key' (which would render the whole film)",
      r.get("shot") == "0" and r["ok"] is True and len(calls) == len(r["clips"]) and all(c["image_ref"] == "/media/f0.jpg" for c in calls) and len(calls) < 6, f"{len(calls)} calls; {str(r)[:200]}")
r = run(film(), only_shot="")
check("only_shot as an empty string is a 400 (it does not mean 'render everything'), nothing generated", r.get("status") == 400 and "empty" in r["detail"] and not calls, str(r)[:200])

# ---- S1b: multi-beat takes, job id, and the single-shot render is idempotent while it runs ------------------------------------------------------------------
mb = takes.normalise({"takes": {"0": [{"id": "tk_m", "status": "done", "url": "", "beats": [{"url": "/media/b1.mp4", "seconds": 8}, {"url": "/media/b2.mp4", "seconds": 4}, {"url": "data:x", "seconds": 1}, "junk"], "job_id": "abc123", "seconds": 12}]},
                      "chosen": {"0": "tk_m"}})
check("clip take: a multi-beat shot keeps one clip per beat (junk and data: URIs dropped), `url` is the first, the job id is kept", mb["takes"]["0"][0]["url"] == "/media/b1.mp4" and len(mb["takes"]["0"][0]["beats"]) == 2 and mb["takes"]["0"][0]["job_id"] == "abc123" and mb["chosen"] == {"0": "tk_m"}, str(mb))
check("use_clips_for: a multi-beat take hands the server ALL its clips in order", takes.use_clips_for(mb) == {"0": [{"url": "/media/b1.mp4", "seconds": 8.0, "mode": "frame"}, {"url": "/media/b2.mp4", "seconds": 4.0, "mode": "frame"}]})
ir = takes.normalise({"takes": {"0": [{"id": "tk_r", "status": "rendering", "url": "", "job_id": "j1"}]}})
check("clip take: a render that was in flight when the film was saved restores as 'interrupted' WITH its job id (so the page can recover the finished clip)", ir["takes"]["0"][0]["status"] == "interrupted" and ir["takes"]["0"][0]["job_id"] == "j1")

import threading, time
started, release, runs = threading.Event(), threading.Event(), []
def slow_sync(payload):
    runs.append(payload.get("only_shot")); started.set(); release.wait(5)
    return {"shot": payload.get("only_shot"), "clips": [], "ok": True}
real_sync = main._produce_video_sync
main._produce_video_sync = slow_sync
p1 = {"only_shot": "1", "scenes": [{"no": 1}], "tier": "lite"}
r1 = main.produce_video(dict(p1)); started.wait(5)
r2 = main.produce_video(dict(p1))
n_after_join = len(runs)
r3 = main.produce_video({**p1, "tier": "standard"})
check("single-shot render: an identical request while the first is still running JOINS that job (no second paid call)", r2["job_id"] == r1["job_id"] and r2.get("joined") is True and n_after_join == 1, str((r1, r2, runs)))
check("single-shot render: a different request (another tier) is its own job", r3["job_id"] != r1["job_id"])
release.set(); time.sleep(0.6)
st = main.render_status(r1["job_id"])
release.clear(); r4 = main.produce_video(dict(p1)); release.set(); time.sleep(0.3)
check("single-shot render: after it finishes the same request starts a NEW job (a deliberate re-roll); the finished job reports its clips", st["status"] == "done" and st["shot"] == "1" and r4["job_id"] != r1["job_id"] and not r4.get("joined"), str((st, r4)))
main._produce_video_sync = real_sync

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
