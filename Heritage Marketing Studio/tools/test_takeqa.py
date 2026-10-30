#!/usr/bin/env python
"""test_takeqa.py -- offline checks for film-builder slice S5 (FILM_BUILDER_PLAN.md): takeqa.py (cheap, deterministic checks on one clip), the routes /take-check and /take-look, and takes.py keeping
`check_accepted` and up to 12 checks. A: synthetic known-bad clips made with the bundled ffmpeg. B: the routes (the model is stubbed; the media folder is a temp folder, nothing touches the tenant).
C: when the 28 Oct trial clips are on this machine, every REAL clip must pass (no false alarm) and the same-frame pairs must be flagged as repeats while genuinely different shots are not.
Run:  api/.venv/Scripts/python.exe tools/test_takeqa.py
"""
import glob, json, os, subprocess, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import takeqa, takes, filmcut, framecheck, gemini, main
import complete as completion

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

exe = filmcut.ffmpeg_exe()
if not exe:
    print("SKIP no ffmpeg on this machine"); sys.exit(0)
tmp = tempfile.mkdtemp()
def make(name, args):
    p = os.path.join(tmp, name + ".mp4")
    subprocess.run([exe, "-y", *args, "-c:v", "libx264", "-pix_fmt", "yuv420p", p], capture_output=True)
    return p
def verdicts(res):
    return {c["id"]: c["verdict"] for c in res["checks"]}

# ---- A. the checks on synthetic clips ---------------------------------------------------------------------------------------------------
moving = make("moving", ["-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24", "-t", "4"])
still_frame = os.path.join(tmp, "f.png"); subprocess.run([exe, "-y", "-i", moving, "-frames:v", "1", still_frame], capture_output=True)
frozen = make("frozen", ["-loop", "1", "-i", still_frame, "-t", "4", "-r", "24"])
black = make("black", ["-f", "lavfi", "-i", "color=c=black:s=320x180:r=24", "-t", "4"])
dark_frame = make("darkframe", ["-i", moving, "-vf", "fade=t=in:st=0:d=3.5"])
other = make("other", ["-f", "lavfi", "-i", "smptebars=size=320x180:rate=24", "-t", "4"])
same_start = make("samestart", ["-i", moving, "-vf", "hue=h=8", "-t", "4"])        # starts from (almost) the same picture, then looks a little different

r = takeqa.check_clip(exe, moving, 4.0)
check("a moving clip of the ordered length passes every check", set(verdicts(r)) == {"readable", "still", "black", "short"} and all(v == "ok" for v in verdicts(r).values()), str(r["checks"]))
check("the measurements ride along (duration, span, brightness)", r["measured"]["duration"] > 3.9 and r["measured"]["span"] > 4 and r["measured"]["mean_luma"] > 15, str(r["measured"]))
r = takeqa.check_clip(exe, frozen, 4.0)
check("a frozen picture is flagged 'still' and says nothing moves", verdicts(r)["still"] == "check" and "does not move at all" in [c for c in r["checks"] if c["id"] == "still"][0]["note"], str(r["checks"]))
r = takeqa.check_clip(exe, black, 4.0)
check("a black clip is flagged 'black'", verdicts(r)["black"] == "check" and "almost black" in [c for c in r["checks"] if c["id"] == "black"][0]["note"], str(r["checks"]))
r = takeqa.check_clip(exe, dark_frame, 4.0)
check("a clip that fades in from black is flagged for a nearly black frame, not as a black clip", verdicts(r)["black"] == "check" and "nearly black frame" in [c for c in r["checks"] if c["id"] == "black"][0]["note"], str(r["checks"]))
check("a clip shorter than ordered is flagged 'short' (4 s ordered 8 s), one within 0.3 s is not", verdicts(takeqa.check_clip(exe, moving, 8.0))["short"] == "check" and verdicts(takeqa.check_clip(exe, moving, 4.2))["short"] == "ok")
check("with no ordered length the length check is left out", "short" not in verdicts(takeqa.check_clip(exe, moving, 0)))
check("without a previous clip the repeat check is left out", "repeat" not in verdicts(takeqa.check_clip(exe, moving, 4.0)))
r = takeqa.check_clip(exe, same_start, 4.0, moving)
check("a clip that starts from the previous shot's picture is flagged as a repeat", verdicts(r).get("repeat") == "check", str(r["checks"]))
r = takeqa.check_clip(exe, other, 4.0, moving)
check("a clip of a different picture is NOT flagged as a repeat", verdicts(r).get("repeat") == "ok", str(r["checks"]))
bad = os.path.join(tmp, "bad.mp4"); open(bad, "wb").write(b"not a video")
r = takeqa.check_clip(exe, bad, 4.0)
check("an unreadable file says so (readable) and guesses nothing else", [c["id"] for c in r["checks"]] == ["readable"] and r["checks"][0]["verdict"] == "check" and r["measured"] == {})
jpg = takeqa.middle_frame_jpeg(exe, moving)
check("the middle frame comes back as JPEG bytes (nothing written to disk); an unreadable clip gives None", bool(jpg) and jpg[:2] == b"\xff\xd8" and takeqa.middle_frame_jpeg(exe, bad) is None)

# ---- B. the routes ---------------------------------------------------------------------------------------------------------------------------
real_dir, gemini.MEDIA_DIR = gemini.MEDIA_DIR, tmp
for n in ("moving", "frozen", "same_start", "other", "black"):
    pass
def call(fn, payload):
    res = fn(payload)
    return res if isinstance(res, dict) else {"status": res.status_code, **json.loads(res.body)}
r = call(main.take_check, {"url": "/media/frozen.mp4", "seconds": 4})
check("/take-check on a frozen clip returns the checks with 'still' flagged", r.get("checks") and {c["id"]: c["verdict"] for c in r["checks"]}["still"] == "check", str(r)[:300])
r = call(main.take_check, {"url": "/media/samestart.mp4", "seconds": 4, "prev_url": "/media/moving.mp4"})
check("/take-check with prev_url runs the repeat check", {c["id"]: c["verdict"] for c in r["checks"]}.get("repeat") == "check", str(r)[:300])
r = call(main.take_check, {"url": "/media/nope.mp4"})
check("/take-check on a clip that is not stored is a 400 with a reason", r.get("status") == 400 and "not a stored file" in r["detail"], str(r))
r = call(main.take_check, {"url": "/media/moving.mp4", "seconds": "abc"})
check("/take-check tolerates a junk `seconds` (length check just left out)", "checks" in r and "short" not in {c["id"] for c in r["checks"]}, str(r)[:200])
real_exe = filmcut.ffmpeg_exe; filmcut.ffmpeg_exe = lambda: None
r = call(main.take_check, {"url": "/media/moving.mp4"})
check("/take-check with no ffmpeg is a 503 saying so", r.get("status") == 503 and "ffmpeg" in r["detail"], str(r))
filmcut.ffmpeg_exe = real_exe

real_key, real_look = completion.has_key, framecheck.look
seen = {}
def fake_look(data, mime, prompt, client=None):
    seen.update({"bytes": len(data), "mime": mime, "prompt": prompt}); return seen.get("reply", '{"verdict":"ok","issues":[],"seen":"A boy at a table."}'), {"input_tokens": 10, "output_tokens": 5}
completion.has_key = lambda: True; framecheck.look = fake_look
r = call(main.take_look, {"url": "/media/moving.mp4", "description": "The boy lifts a glass.", "cast": "A boy of nine."})
check("/take-look sends the MIDDLE FRAME (a JPEG) with the shot's words and returns an ok result with what was seen",
      seen["mime"] == "image/jpeg" and seen["bytes"] > 100 and "The boy lifts a glass." in seen["prompt"] and r["verdict"] == "ok" and r["checks"] == [] and r["seen"].startswith("A boy"), str(r)[:300])
seen["reply"] = '{"verdict":"check","issues":[{"id":"anatomy","note":"The boy has three arms in the middle of the clip."}],"seen":"x"}'
r = call(main.take_look, {"url": "/media/moving.mp4", "description": "d"})
check("/take-look returns a named issue as a check", r["verdict"] == "check" and r["checks"][0]["id"] == "anatomy" and "three arms" in r["checks"][0]["note"], str(r)[:300])
seen["reply"] = "no json at all"
r = call(main.take_look, {"url": "/media/moving.mp4", "description": "d"})
check("/take-look with an unreadable reply is a 502, never a made-up result", r.get("status") == 502, str(r))
completion.has_key = lambda: False
r = call(main.take_look, {"url": "/media/moving.mp4"})
check("/take-look with no model key is a 503 (and takes no frame)", r.get("status") == 503, str(r))
completion.has_key = lambda: True
r = call(main.take_look, {"url": "/media/nope.mp4"})
check("/take-look on a clip that is not stored is a 400", r.get("status") == 400, str(r))
completion.has_key, framecheck.look = real_key, real_look

# ---- B2. the look at SEVERAL frames of one clip (FILM_PHASE5_AND_PLACE_PLAN.md P5.1-P5.3) ----------------------------------------------------------------
fr3 = takeqa.frames_jpeg(exe, moving)
check("frames_jpeg: three frames at 25 / 50 / 75 % of a moving clip, all real JPEGs, all different (time order)", len(fr3) == 3 and all(f[:2] == b"\xff\xd8" for f in fr3) and len(set(fr3)) == 3, [len(f) for f in fr3])
check("frames_jpeg: one fraction gives one frame; an unreadable clip gives none, never raises", len(takeqa.frames_jpeg(exe, moving, (0.5,))) == 1 and takeqa.frames_jpeg(exe, os.path.join(tmp, "missing.mp4")) == [])
p1 = framecheck.vision_prompt(description="The boy lifts a glass.", cast="A boy of nine.")
check("vision_prompt: frames=1 (or unset) is byte for byte the single-frame brief", framecheck.vision_prompt(description="The boy lifts a glass.", cast="A boy of nine.", frames=1) == p1 and "`drift`" not in p1)
p3 = framecheck.vision_prompt(description="The boy lifts a glass.", cast="A boy of nine.", frames=3, pack_expected=True)
check("vision_prompt: 3 frames -> the brief is about CHANGE between frames of ONE clip, names drift first, limbs, a hand crossing a face, a pack that smears, and asks which frame",
      "3 attached frames" in p3 and "ONE short video clip, in time order" in p3 and "1. `drift`" in p3 and "stretches, splits, merges" in p3 and "crosses the face" in p3 and "smearing or going out of focus" in p3
      and "Name the frames" in p3 and "SHOULD appear" in p3 and "The boy lifts a glass." in p3 and p3.rstrip().endswith("leave it out."), p3[:300])
check("clean_issues: `drift` is accepted for a look at several frames and ignored for a single frame (it cannot happen in one picture)", [i["id"] for i in framecheck.clean_issues({"issues": [{"id": "drift", "note": "The arm stretches across the face in the middle frame."}]}, motion=True)] == ["drift"]
      and framecheck.clean_issues({"issues": [{"id": "drift", "note": "The arm stretches across the face in the middle frame."}]}) == [])
class FakeClient:
    def __init__(self): self.sent = None
    class _M:
        def __init__(self, outer): self.o = outer
        def create(self, **kw):
            self.o.sent = kw
            class R:
                content = [type("B", (), {"type": "text", "text": '{"verdict":"ok","issues":[],"seen":"s"}'})()]
                usage = type("U", (), {"input_tokens": 7, "output_tokens": 3})()
            return R()
    @property
    def messages(self): return FakeClient._M(self)
fcx = FakeClient(); txt, use = framecheck.look_many([b"a", b"b", b"c"], "image/jpeg", "BRIEF", client=fcx)
blocks = fcx.sent["messages"][0]["content"]
check("look_many: ONE call with the images first, in order, then the brief; same reply and usage shape as look", [b["type"] for b in blocks] == ["image", "image", "image", "text"] and blocks[-1]["text"] == "BRIEF" and use == {"input_tokens": 7, "output_tokens": 3} and "verdict" in txt)

real_many, real_frames = framecheck.look_many, takeqa.frames_jpeg
seen2 = {}
def fake_many(images, mime, prompt, client=None):
    seen2.update({"n": len(images), "prompt": prompt}); return seen2.get("reply", '{"verdict":"ok","issues":[],"seen":"A boy lifts a glass; nothing changes."}'), {"input_tokens": 30, "output_tokens": 9}
completion.has_key = lambda: True; framecheck.look_many = fake_many; framecheck.look = fake_look
seen.clear()
r = call(main.take_look, {"url": "/media/moving.mp4", "description": "The boy lifts a glass.", "frames": 3})
check("/take-look frames=3 sends THREE frames in one call with the motion brief and says how many it looked at", seen2["n"] == 3 and "3 attached frames" in seen2["prompt"] and r["frames"] == 3 and r["verdict"] == "ok" and "bytes" not in seen, str(r)[:300])
seen2["reply"] = '{"verdict":"check","issues":[{"id":"drift","note":"The arm stretches across the face between the middle and late frames."}],"seen":"x"}'
r = call(main.take_look, {"url": "/media/moving.mp4", "description": "d", "frames": 3})
check("/take-look frames=3 returns a drift issue as a check", r["verdict"] == "check" and r["checks"][0]["id"] == "drift" and r["checks"][0]["label"] == "Changes between frames", str(r)[:300])
seen.clear(); seen2.clear()
r = call(main.take_look, {"url": "/media/moving.mp4", "description": "The boy lifts a glass."})
check("/take-look with no `frames` is exactly as before: ONE middle frame, the single-frame brief, frames reported as 1", seen.get("bytes", 0) > 100 and "n" not in seen2 and "`drift`" not in seen["prompt"] and r["frames"] == 1, str(r)[:200])
for bad in ("abc", 0, -2, None):
    seen.clear(); seen2.clear(); r = call(main.take_look, {"url": "/media/moving.mp4", "description": "d", "frames": bad})
    check("/take-look frames=%r is treated as 1 (never an error)" % (bad,), r.get("frames") == 1 and seen.get("bytes", 0) > 100, str(r)[:160])
seen2.clear(); r = call(main.take_look, {"url": "/media/moving.mp4", "description": "d", "frames": 99})
check("/take-look frames=99 is held to 5", seen2.get("n") == 5 and r["frames"] == 5, str(seen2) + str(r)[:120])
takeqa.frames_jpeg = lambda exe_, path_, fr=(): []
seen.clear(); seen2.clear(); r = call(main.take_look, {"url": "/media/moving.mp4", "description": "d", "frames": 3})
check("/take-look frames=3 on a clip where no extra frame can be taken falls back to the one middle frame (never a refusal)", seen.get("bytes", 0) > 100 and r["frames"] == 1, str(r)[:200])
takeqa.frames_jpeg = lambda exe_, path_, fr=(): [b"\xff\xd8only-one"]
seen.clear(); seen2.clear(); r = call(main.take_look, {"url": "/media/moving.mp4", "description": "d", "frames": 3})
check("/take-look frames=3 with only ONE frame obtainable looks at that frame with the single-frame brief", seen.get("bytes") == len(b"\xff\xd8only-one") and r["frames"] == 1, str(r)[:200])
takeqa.frames_jpeg = real_frames; framecheck.look_many = real_many
gemini.MEDIA_DIR = real_dir

# ---- takes.py -----------------------------------------------------------------------------------------------------------------------------------
t = takes.clip_take({"id": "tk_1", "url": "/media/a.mp4", "status": "done", "seconds": 4, "check_accepted": True,
                     "checks": [{"id": f"c{i}", "label": "L", "verdict": "check", "note": "n"} for i in range(14)]})
check("takes: a clip take keeps check_accepted and up to 12 checks; absent means False", t["check_accepted"] is True and len(t["checks"]) == 12 and takes.clip_take({"url": "/media/a.mp4", "status": "done"})["check_accepted"] is False)

# ---- C. real clips (when present): no false alarms --------------------------------------------------------------------------------------------------
corpus = r"C:\Users\punie\Downloads\engine-trial"
real = sorted(glob.glob(os.path.join(corpus, "coverage_step0", "shot_*.mp4")) + glob.glob(os.path.join(corpus, "flow_trials", "omni", "**", "*.mp4"), recursive=True) + glob.glob(os.path.join(corpus, "i2v_*.mp4")))
if len(real) < 5:
    print("SKIP part C: the real trial clips are not on this machine")
else:
    flagged = [(os.path.basename(p), [c["id"] for c in takeqa.check_clip(exe, p, 0)["checks"] if c["verdict"] == "check"]) for p in real]
    flagged = [x for x in flagged if x[1]]
    check(f"{len(real)} REAL clips (Omni, Kling, Veo, Wan, Seedance, MiniMax): none is flagged as unreadable, still or black", not flagged, str(flagged))
    a, b = os.path.join(corpus, "coverage_step0", "a_2s_615.mp4"), os.path.join(corpus, "coverage_step0", "a_2s_648.mp4")
    if os.path.exists(a) and os.path.exists(b):
        check("two real clips animated from the same frame ARE flagged as repeats", {c["id"]: c["verdict"] for c in takeqa.check_clip(exe, b, 0, a)["checks"]}.get("repeat") == "check")
    s1, s2, sb = (os.path.join(corpus, "coverage_step0", n) for n in ("shot_A_1.mp4", "shot_A_2.mp4", "shot_B_1.mp4"))
    if all(os.path.exists(x) for x in (s1, s2, sb)):
        check("real clips of different angles / different scenes are NOT flagged as repeats", all({c["id"]: c["verdict"] for c in takeqa.check_clip(exe, y, 0, x)["checks"]}.get("repeat") == "ok" for x, y in ((s1, s2), (s1, sb), (s2, sb))))

shutil.rmtree(tmp, ignore_errors=True)
print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
