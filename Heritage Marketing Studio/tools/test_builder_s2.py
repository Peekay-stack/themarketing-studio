#!/usr/bin/env python
"""test_builder_s2.py -- offline checks for film-builder slice S2 (FILM_BUILDER_PLAN.md), part a: TRIM. A chosen clip's kept window (`in`/`out` seconds) is applied when the film is assembled:
the window is cut into a NEW file (the take itself is never touched), the beat becomes the window's length and the voice follows the trimmed picture.
A: filmcut.trim_window on a synthetic clip with the bundled ffmpeg. B: the assemble path of _produce_video_sync with the cutter stubbed (the media folder is a temp folder; nothing touches the tenant).
Run:  api/.venv/Scripts/python.exe tools/test_builder_s2.py
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import takes, filmcut, filmvoice, main, gemini

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

tmpd = tempfile.mkdtemp()

# ---- A. trim_window with real ffmpeg ---------------------------------------------------------------------------------------------------
exe = filmcut.ffmpeg_exe()
if not exe:
    print("SKIP part A: no ffmpeg on this machine")
else:
    src = os.path.join(tmpd, "src.mp4")
    subprocess.run([exe, "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24", "-t", "6", "-c:v", "libx264", "-pix_fmt", "yuv420p", src], capture_output=True)
    h0 = hashlib.md5(open(src, "rb").read()).hexdigest()
    dst = os.path.join(tmpd, "win.mp4")
    ok = filmcut.trim_window(exe, src, 1.0, 3.5, dst)
    check("trim_window: cuts the kept window into a new file", ok and os.path.exists(dst) and os.path.getsize(dst) > 0)
    d = filmcut.probe_seconds(exe, dst)
    check("trim_window: the new file is the window's length (2.5 s, within a frame or two)", abs(d - 2.5) < 0.12, f"{d}")
    check("trim_window: the source take is never touched", hashlib.md5(open(src, "rb").read()).hexdigest() == h0)
    s_a, s_b = filmcut._frame_signature(exe, dst, 0.1), filmcut._frame_signature(exe, dst, 2.0)
    check("trim_window: the window MOVES (first and last frames differ)", s_a is not None and s_b is not None and s_a != s_b)
    s_src, s_win = filmcut._frame_signature(exe, src, 1.0), filmcut._frame_signature(exe, dst, 0.0)
    check("trim_window: the window starts where you said (its first frame is the source's frame at `in`)", s_src is not None and s_win is not None
          and sum(abs(x - y) for x, y in zip(s_src, s_win)) / len(s_src) < 12)
    bad = os.path.join(tmpd, "bad.mp4")
    check("trim_window: a window shorter than 0.2 s is refused and writes nothing", filmcut.trim_window(exe, src, 2.0, 2.1, bad) is False and not os.path.exists(bad))
    check("trim_window: a missing source fails cleanly (False, no raise)", filmcut.trim_window(exe, os.path.join(tmpd, "nope.mp4"), 0, 2, os.path.join(tmpd, "n.mp4")) is False)
    check("trim_window: a negative `in` is clamped to 0", filmcut.trim_window(exe, src, -1.0, 1.0, os.path.join(tmpd, "neg.mp4")) is True)

# ---- takes.py carries the trim to the payload (already pinned in test_builder_s0; here the shape the page sends) -----------------------------
doc = takes.normalise({"takes": {"0": [{"id": "tk_1", "url": "/media/a.mp4", "status": "done", "seconds": 4.0}]}, "chosen": {"0": "tk_1"}, "trim": {"0": {"in": 0.5, "out": 3.0}}})
check("takes: use_clips_for carries in/out for a single-clip shot, and trims=False leaves them off",
      takes.use_clips_for(doc)["0"][0].get("in") == 0.5 and takes.use_clips_for(doc)["0"][0].get("out") == 3.0 and "in" not in takes.use_clips_for(doc, trims=False)["0"][0])

# ---- B. the assemble path ------------------------------------------------------------------------------------------------------------------
calls, synthed, stitched, cut_calls = [], [], [], []
gemini.available = lambda: False
saved_fal = os.environ.pop("FAL_KEY", None)
main._record_made = lambda *a, **k: None
main._music_bed = lambda *a, **k: ("", "")
filmvoice.synth = lambda segs, *a, **k: (synthed.extend(segs), (0, []))[1]
def fake_stitch(urls, lengths=None):
    stitched.append((list(urls), list(lengths or []))); return None
filmcut.stitch = fake_stitch
real_media_dir, gemini.MEDIA_DIR = gemini.MEDIA_DIR, tmpd          # the trimmed file lands in a temp folder, never in the tenant
def film():
    return [{"no": 1, "visual": "Mother pours milk.", "frame_url": "/media/f0.jpg"},
            {"no": 2, "visual": "The boy steps closer with his glass.", "frame_url": "/media/f1.jpg"},
            {"no": 3, "visual": "The pack, front-on.", "beat_role": "brand", "frame_url": "/media/f2.jpg"}]
def run(rows, **extra):
    stitched.clear(); synthed.clear(); cut_calls.clear()
    payload = {"scenes": rows, "aspect": "16:9", "duration": "15s", "engines": {"video": "google"}, "tier": "lite", "script": {"logline": "A morning."}, **extra}
    try:
        res = main._produce_video_sync(payload)
    except Exception as e:
        return {"raised": f"{type(e).__name__}: {e}"}
    return res if isinstance(res, dict) else {"status": res.status_code, **json.loads(res.body)}

files = {}
def mk(name):
    p = os.path.join(tmpd, name.split("/")[-1]); open(p, "wb").write(b"x"); files[name] = p; return name
real_local = gemini.local_path
gemini.local_path = lambda u: files.get(str(u)) or real_local(u)
durs = {}
filmcut.ffmpeg_exe = lambda: "ffmpeg"
def probe(exe_, p):
    if p in durs: return durs[p]
    return durs.get("__trimmed__", 0.0) if os.path.basename(p).startswith("trim-") else 0.0
filmcut.probe_seconds = probe
plan = {}
segs = filmcut.plan_by_scene(main._rows_for_planning(film()), filmvoice.scene_seconds(film(), target_total=15))
for i, sg in enumerate(segs): plan[str(i)] = sg["seconds"]
chosen = {k: [{"url": mk(f"/media/c{k}.mp4"), "seconds": s}] for k, s in plan.items()}
def stub_cut(ok=True):
    def trim_window(exe_, src_, a, b, dest):
        cut_calls.append((src_, a, b, dest))
        if ok: open(dest, "wb").write(b"t")
        return ok
    filmcut.trim_window = trim_window

stub_cut(True)
r = run(film(), use_clips=chosen)
check("assemble with NO trims is exactly as before: the cutter is never called and the stitch gets the chosen urls", not cut_calls and stitched and stitched[0][0] == [chosen[k][0]["url"] for k in ("0", "1", "2")], str(r)[:500] + " PLAN " + str(plan))

tr = {k: [dict(c) for c in v] for k, v in chosen.items()}
tr["1"][0].update({"in": 0.5, "out": 2.5})
durs["__trimmed__"] = 2.0
r = run(film(), use_clips=tr)
urls, lens = stitched[0]
check("a trimmed shot: the cutter is called once, on the take's own file, with the window, into the media folder",
      len(cut_calls) == 1 and cut_calls[0][0] == files[chosen["1"][0]["url"]] and cut_calls[0][1:3] == (0.5, 2.5) and os.path.dirname(cut_calls[0][3]) == tmpd, str(cut_calls))
check("a trimmed shot: the stitch gets the NEW trimmed file for that shot and the untouched takes for the others", urls[1].startswith("/media/trim-") and urls[0] == chosen["0"][0]["url"] and urls[2] == chosen["2"][0]["url"], str(urls))
check("a trimmed shot: its beat becomes the window's length (the film and the voice follow the trimmed picture) and the note says 'trimmed'",
      abs(lens[1] - 2.0) < 0.01 and "trimmed to 2.0 s" in str(r.get("detail", "") or r.get("errors", "")), f"{lens} {str(r)[:300]}")
check("a trimmed shot: the take's own file still exists and is the original", os.path.exists(files[chosen["1"][0]["url"]]))

# the window is LONGER than the beat: only the beat's worth is used, and the page is told
durs["__trimmed__"] = plan["1"] + 3.0
r = run(film(), use_clips=tr)
check("a window longer than the beat: the beat is kept (the stitch cuts the window to it) and the note says only the first part is used",
      abs(stitched[0][1][1] - plan["1"]) < 0.01 and "only the first" in str(r.get("detail", "") or r.get("errors", "")), f"{stitched[0][1]} {str(r)[:300]}")

# the cut FAILS: the whole clip is used, loudly
stub_cut(False)
durs["__trimmed__"] = 2.0
r = run(film(), use_clips=tr)
check("a trim that cannot be cut falls back to the WHOLE clip and says so (never silently ignored)", stitched[0][0][1] == chosen["1"][0]["url"] and "could not be cut" in str(r.get("detail", "") or r.get("errors", "")), f"{stitched[0][0]} {str(r)[:300]}")

# junk windows are ignored, not fatal
stub_cut(True)
for bad in ({"in": 2.0, "out": 1.0}, {"in": "a", "out": 2}, {"in": 1.0, "out": 1.1}, {"in": 1.0}):
    t2 = {k: [dict(c) for c in v] for k, v in chosen.items()}; t2["1"][0].update(bad)
    r = run(film(), use_clips=t2)
    check(f"an unusable window {bad} is ignored: the whole clip is used and the cutter is not called", not cut_calls and stitched and stitched[0][0][1] == chosen["1"][0]["url"], str(stitched)[:200])

gemini.local_path = real_local
gemini.MEDIA_DIR = real_media_dir
if saved_fal is not None: os.environ["FAL_KEY"] = saved_fal
shutil.rmtree(tmpd, ignore_errors=True)
print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
