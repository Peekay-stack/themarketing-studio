#!/usr/bin/env python
"""test_builder_s4.py -- offline checks for film-builder slice S4 (FILM_BUILDER_PLAN.md), CHAIN continuity: a shot (or the later pieces of a long shot) starts from the LAST FRAME of the clip before it
instead of from its own storyboard frame. A: filmcut.last_frame on a real synthetic clip. B: the single-shot render (`only_shot`) with the new keys `chain_from` / `chain_beats`, the video engine stubbed
to write REAL clip files (so each extraction is from what the engine "made"); the media folder is a temp folder, nothing touches the tenant. Extend (Omni previous_interaction_id) is NOT in this slice.
Run:  api/.venv/Scripts/python.exe tools/test_builder_s4.py
"""
import json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import takes, filmcut, main, gemini

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

exe = filmcut.ffmpeg_exe()
if not exe:
    print("SKIP no ffmpeg on this machine"); sys.exit(0)
tmp = tempfile.mkdtemp()
def mad(a, b): return sum(abs(x - y) for x, y in zip(a, b)) / max(1, len(a))
def sig(path, t=0.0):
    if str(path).lower().endswith((".jpg", ".jpeg", ".png")):          # a still image: no seeking
        r = subprocess.run([exe, "-y", "-i", path, "-frames:v", "1", "-vf", "scale=64:36,format=gray", "-f", "rawvideo", "-"], capture_output=True)
        return r.stdout if (r.returncode == 0 and r.stdout) else None
    return filmcut._frame_signature(exe, path, t)

# a clip whose picture changes all the way through, so "the last frame" is unmistakable
src = os.path.join(tmp, "src.mp4")
subprocess.run([exe, "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24", "-t", "4", "-c:v", "libx264", "-pix_fmt", "yuv420p", src], capture_output=True)

# ---- A. last_frame ----------------------------------------------------------------------------------------------------------------------------
dst = os.path.join(tmp, "last.jpg")
check("last_frame writes a non-empty JPEG", filmcut.last_frame(exe, src, dst) and os.path.getsize(dst) > 0 and open(dst, "rb").read(2) == b"\xff\xd8")
d = filmcut.probe_seconds(exe, src)
check("it is the clip's LAST picture (matches the frame just before the end, differs from the first)", mad(sig(dst, 0), sig(src, d - 0.12)) < 8 and mad(sig(dst, 0), sig(src, 0.1)) > 5,
      f"end {mad(sig(dst, 0), sig(src, d - 0.12)):.1f} first {mad(sig(dst, 0), sig(src, 0.1)):.1f}")
check("a missing file or an unreadable one returns False and writes nothing", filmcut.last_frame(exe, os.path.join(tmp, "nope.mp4"), os.path.join(tmp, "n.jpg")) is False and not os.path.exists(os.path.join(tmp, "n.jpg"))
      and filmcut.last_frame(exe, dst, os.path.join(tmp, "n2.jpg")) is False)
tiny = os.path.join(tmp, "tiny.mp4")
subprocess.run([exe, "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24", "-t", "0.3", "-c:v", "libx264", "-pix_fmt", "yuv420p", tiny], capture_output=True)
check("a very short clip still gives a frame (it steps back further)", filmcut.last_frame(exe, tiny, os.path.join(tmp, "t.jpg")) is True)

# ---- takes.py -------------------------------------------------------------------------------------------------------------------------------------
t = takes.clip_take({"id": "tk_1", "url": "/media/a.mp4", "status": "done", "seconds": 4, "mode": "chain", "chain_from": "/media/prev.mp4", "frame": "/media/chain-1.jpg"})
check("takes: a chain take keeps its mode, the clip it continued from and its start frame", t["mode"] == "chain" and t["chain_from"] == "/media/prev.mp4" and t["frame"] == "/media/chain-1.jpg" and takes.clip_take({"url": "/media/a.mp4", "status": "done"})["chain_from"] == "")

# ---- B. the single-shot render ------------------------------------------------------------------------------------------------------------------
real_dir, gemini.MEDIA_DIR = gemini.MEDIA_DIR, tmp
real_local = gemini.local_path
gemini.local_path = lambda u: (os.path.join(tmp, os.path.basename(str(u))) if str(u).startswith("/media/") and os.path.exists(os.path.join(tmp, os.path.basename(str(u)))) else real_local(u))
calls, n_made = [], [0]
fail_at = [None]
def fake_video(prompt, **kw):
    calls.append({"prompt": prompt, "image_ref": kw.get("image_ref"), "seconds": kw.get("seconds")})
    if fail_at[0] is not None and len(calls) == fail_at[0]:
        return None
    n_made[0] += 1
    name = f"shot-gen{n_made[0]}.mp4"; shutil.copy(src, os.path.join(tmp, name)); return "/media/" + name
gemini.available = lambda: True; gemini.video = fake_video; gemini.video_error = lambda: "the engine said no"
main._record_made = lambda *a, **k: None
saved_fal = os.environ.pop("FAL_KEY", None)
prev = os.path.join(tmp, "prevclip.mp4"); shutil.copy(src, prev)
def run(rows, **extra):
    calls.clear(); n_made[0] = 0
    payload = {"scenes": rows, "aspect": "16:9", "duration": "20s", "engines": {"video": "google"}, "tier": "lite", "script": {"logline": "A morning."}, **extra}
    try:
        res = main._produce_video_sync(payload)
    except Exception as e:
        return {"raised": f"{type(e).__name__}: {e}"}
    return res if isinstance(res, dict) else {"status": res.status_code, **json.loads(res.body)}
long_ = lambda: [{"no": 1, "visual": "A long quiet scene.", "frame_url": "/media/f0.jpg"}]

r = run(long_(), only_shot="0")
check("INERT: a single-shot render with no chain keys is as before (storyboard frame for every piece, mode frame, no chain frame)",
      len(r["clips"]) >= 2 and all(c["frame_url"] == "" for c in r["clips"]) and all(c["image_ref"] == "/media/f0.jpg" for c in calls) and r["mode"] == "frame", str(r)[:300])
pieces = len(r["clips"])

r = run(long_(), only_shot="0", chain_from="/media/prevclip.mp4")
c0 = r["clips"][0]
check("chain_from: the FIRST piece starts from the last frame of the previous clip (a new chain-*.jpg), not the storyboard frame",
      calls[0]["image_ref"].startswith("/media/chain-") and os.path.exists(os.path.join(tmp, os.path.basename(calls[0]["image_ref"]))) and c0["frame_url"] == calls[0]["image_ref"] and r["mode"] == "chain", str(calls[0]))
check("chain_from: the extracted picture really is the previous clip's last frame", mad(sig(os.path.join(tmp, os.path.basename(calls[0]["image_ref"])), 0), sig(prev, filmcut.probe_seconds(exe, prev) - 0.12)) < 8)
check("chain_from alone leaves the later pieces on the storyboard frame", all(c["image_ref"] == "/media/f0.jpg" for c in calls[1:]) and all(c["frame_url"] == "" for c in r["clips"][1:]), str(calls))

r = run(long_(), only_shot="0", chain_beats=True)
frames = [c["frame_url"] for c in r["clips"]]
check("chain_beats: the first piece uses the storyboard frame, each LATER piece starts from the last frame of the piece before it",
      calls[0]["image_ref"] == "/media/f0.jpg" and frames[0] == "" and all(f.startswith("/media/chain-") for f in frames[1:]) and len(set(frames[1:])) == len(frames) - 1, str(frames))
out1 = os.path.join(tmp, os.path.basename(r["clips"][0]["url"]))
check("chain_beats: piece 2's start frame is piece 1's OUTPUT's last frame (the engine's real result, not the storyboard)", mad(sig(os.path.join(tmp, os.path.basename(frames[1])), 0), sig(out1, filmcut.probe_seconds(exe, out1) - 0.12)) < 8)
check("chain_beats: the pieces ran ONE AFTER ANOTHER, in order (each call's frame existed before it was made)", [c["image_ref"] for c in calls][1:] == frames[1:])

r = run(long_(), only_shot="0", chain_from="/media/prevclip.mp4", chain_beats=True)
check("both keys: every piece is chained (first from the previous clip, the rest from the piece before)", all(c["frame_url"].startswith("/media/chain-") for c in r["clips"]) and r["ok"] is True and len(calls) == pieces, str(r)[:300])

# ---- chain from the clip's USED end (found in the 28 Oct wiring audit): a trim, or a 2 s shot cut from a 3 s clip, means the file's end is NOT what was on screen -------------------------------
at_dst = os.path.join(tmp, "at.jpg")
check("last_frame(at=2.0) takes the picture where the film STOPS using the clip, not the end of the file",
      filmcut.last_frame(exe, src, at_dst, 2.0) and mad(sig(at_dst, 0), sig(src, 2.0 - 0.12)) < 8 and mad(sig(at_dst, 0), sig(src, d - 0.12)) > 5, f"at {mad(sig(at_dst, 0), sig(src, 1.88)):.1f} end {mad(sig(at_dst, 0), sig(src, d - 0.12)):.1f}")
for bad in (None, 0, 0.1, -3, 99):
    p_ = os.path.join(tmp, "bad_at.jpg")
    if os.path.exists(p_): os.remove(p_)
    ok_ = filmcut.last_frame(exe, src, p_, bad)
    check(f"an unusable or out-of-range `at` ({bad!r}) falls back to the end of the file", ok_ and mad(sig(p_, 0), sig(src, d - 0.12)) < 8, f"{mad(sig(p_, 0), sig(src, d - 0.12)):.1f}")
check("a take keeps chain_at (a number, 0 when absent)", takes.clip_take({"url": "/media/a.mp4", "status": "done", "chain_at": 2.5})["chain_at"] == 2.5 and takes.clip_take({"url": "/media/a.mp4", "status": "done"})["chain_at"] == 0.0)
r = run(long_(), only_shot="0", chain_from="/media/prevclip.mp4", chain_from_at=2.0)
f0 = os.path.join(tmp, os.path.basename(r["clips"][0]["frame_url"]))
check("chain_from_at: the FIRST piece starts from the previous clip's picture at that second", mad(sig(f0, 0), sig(prev, 2.0 - 0.12)) < 8 and mad(sig(f0, 0), sig(prev, filmcut.probe_seconds(exe, prev) - 0.12)) > 5)
r = run(long_(), only_shot="0", chain_from="/media/prevclip.mp4", chain_from_at="junk")
check("a junk chain_from_at is ignored (the end of the file, as before)", mad(sig(os.path.join(tmp, os.path.basename(r["clips"][0]["frame_url"])), 0), sig(prev, filmcut.probe_seconds(exe, prev) - 0.12)) < 8)
r = run(long_(), only_shot="0", chain_from="/media/prevclip.mp4", chain_from_at=1.0, chain_beats=True)
out1 = os.path.join(tmp, os.path.basename(r["clips"][0]["url"])); f1 = os.path.join(tmp, os.path.basename(r["clips"][1]["frame_url"]))
check("chain_from_at applies ONLY to the first piece: a later piece starts from the END of the piece before it", mad(sig(f1, 0), sig(out1, filmcut.probe_seconds(exe, out1) - 0.12)) < 8)

# ---- refusals -------------------------------------------------------------------------------------------------------------------------------------
r = run(long_(), chain_from="/media/prevclip.mp4")
check("chain_from without only_shot is a 400 (a full render never chains) and generates nothing", r.get("status") == 400 and "single-shot" in r["detail"] and not calls, str(r)[:200])
r = run(long_(), chain_beats=True)
check("chain_beats without only_shot is a 400", r.get("status") == 400 and not calls)
r = run(long_(), only_shot="0", chain_from="/media/not-there.mp4")
check("chain_from naming a clip that is not stored is a 400 with the reason, nothing generated", r.get("status") == 400 and "not a stored file" in r["detail"] and not calls, str(r)[:200])
real_lf = filmcut.last_frame; filmcut.last_frame = lambda *a, **k: False
r = run(long_(), only_shot="0", chain_from="/media/prevclip.mp4")
check("a chain whose last frame cannot be taken is REFUSED, never a quiet fall back to the storyboard frame: nothing is generated and the reason is given",
      not calls and r["ok"] is False and all(c["url"] == "" for c in r["clips"]) and "could not take the last frame" in " ".join(r["errors"]) and "never falls back" in " ".join(r["errors"]), str(r)[:400])
filmcut.last_frame = real_lf
fail_at[0] = 1
r = run(long_(), only_shot="0", chain_beats=True)
check("if a piece fails, the pieces after it are NOT rendered (they would have nothing to continue from) and the notes say why",
      len(calls) == 1 and r["ok"] is False and "did not render" in " ".join(r["errors"]) and len(r["clips"]) == pieces, str(r)[:400])
fail_at[0] = None

gemini.local_path = real_local; gemini.MEDIA_DIR = real_dir
if saved_fal is not None: os.environ["FAL_KEY"] = saved_fal
shutil.rmtree(tmp, ignore_errors=True)
print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
