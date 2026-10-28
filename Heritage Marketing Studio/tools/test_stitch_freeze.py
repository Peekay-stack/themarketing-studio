#!/usr/bin/env python
"""test_stitch_freeze.py -- the joined film must never show one frame for seconds. Found 28 Oct 2026: the studio's own render of the re-directed Heritage film came out with the picture FROZEN from
16 s to 26 s although every one of its 7 clips moved (the clips that had been trimmed from 3 s to 2 s sat between untouched ones; both the stream-copy join and a re-encoded demuxer join froze, the
concat FILTER did not). filmcut.stitch now looks at the joined film and rebuilds it with the filter when two neighbouring clips show the same frame.

Offline: synthetic clips made with the bundled ffmpeg, plus (when present on this machine) the seven real clips of that render as a regression case. Nothing is written to the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_stitch_freeze.py
"""
import json, os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api"))
import filmcut

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

exe = filmcut.ffmpeg_exe()
if not exe:
    print("SKIP no ffmpeg on this machine"); sys.exit(0)
tmp = tempfile.mkdtemp(prefix="stitchtest-")

def make(name, secs, source="testsrc2", size="320x180"):
    p = os.path.join(tmp, name)
    src = f"{source}=size={size}:rate=24" if source != "color" else f"color=c=0x886644:size={size}:rate=24"
    subprocess.run([exe, "-y", "-f", "lavfi", "-i", src, "-t", str(secs), "-c:v", "libx264", "-pix_fmt", "yuv420p", p], capture_output=True)
    return p

# ---- frozen_join on synthetic films -------------------------------------------------------------------------------------------------------------------
moving = make("moving.mp4", 10); still = make("still.mp4", 10, "color")
check("frozen_join: a moving film is not frozen", filmcut.frozen_join(exe, moving, [3, 3, 4]) is False)
check("frozen_join: a film that holds one frame across clip windows IS frozen", filmcut.frozen_join(exe, still, [3, 3, 4]) is True)
check("frozen_join: clips shorter than 1 s are not compared; a single clip cannot be frozen against itself", filmcut.frozen_join(exe, still, [0, 0]) is False and filmcut.frozen_join(exe, still, [10]) is False)
check("frozen_join: an unreadable file says nothing (False), never raises", filmcut.frozen_join(exe, os.path.join(tmp, "nope.mp4"), [3, 3]) is False and filmcut.frozen_join(exe, moving, []) is False)

# ---- the concat filter join ---------------------------------------------------------------------------------------------------------------------------
a, b, c = make("a.mp4", 4), make("b.mp4", 3, size="320x180"), make("c.mp4", 5)
out = os.path.join(tmp, "joined.mp4")
ok = filmcut._join_filter(exe, [a, b, c], out, 12.0)
dur = filmcut.probe_seconds(exe, out) if ok else 0
info = subprocess.run([exe, "-hide_banner", "-i", out], capture_output=True, text=True).stderr if ok else ""
check("_join_filter: joins three clips into one film of the planned length", ok and abs(dur - 12.0) < 0.1, str(dur))
check("_join_filter: the film keeps the clips' size and a (silent) audio stream, as the demuxer join had", "320x180" in info and "Audio:" in info, info[-300:])
check("_join_filter: the joined film moves in every clip's window", ok and filmcut.frozen_join(exe, out, [4, 3, 5]) is False)
check("_join_filter: a missing clip fails cleanly (False) and leaves nothing half-written that counts", filmcut._join_filter(exe, [a, os.path.join(tmp, "missing.mp4")], os.path.join(tmp, "bad.mp4"), 7.0) is False)

# ---- stitch(): trimmed clips between untouched ones (the real failure shape) ---------------------------------------------------------------------------
parts = {"u0": make("u0.mp4", 4), "u1": make("u1.mp4", 6), "u2": make("u2.mp4", 3), "u3": make("u3.mp4", 3), "u4": make("u4.mp4", 6)}
real_dl = filmcut._download
filmcut._download = lambda url, dest: shutil.copyfile(parts[url], dest)
name = filmcut.stitch(["u0", "u1", "u2", "u3", "u4"], [4, 6, 2, 2, 6])
joined = os.path.join(filmcut.RENDERS_DIR, name) if name else ""
check("stitch: trimmed 3 s clips between untouched ones join into a 20 s film", bool(name) and abs(filmcut.probe_seconds(exe, joined) - 20.0) < 0.1, str(name))
check("stitch: the result moves in every clip's window", bool(name) and filmcut.frozen_join(exe, joined, [4, 6, 2, 2, 6]) is False)
if name: os.remove(joined)
filmcut._download = real_dl

# ---- Draft (360p) and Final (720p) takes in ONE film: the demuxer cannot join different sizes, so the concat filter does, at the largest size --------------------------------
mix = {"m0": make("m0.mp4", 4, size="320x180"), "m1": make("m1.mp4", 4, size="640x360"), "m2": make("m2.mp4", 3, size="320x180")}
filmcut._download = lambda url, dest: shutil.copyfile(mix[url], dest)
name = filmcut.stitch(["m0", "m1", "m2"], [4, 4, 3])
joined = os.path.join(filmcut.RENDERS_DIR, name) if name else ""
dims = filmcut._video_dims(exe, joined) if name else None
check("stitch: clips of DIFFERENT sizes (a 320x180 and a 640x360 take) join into one film at the LARGEST size, the full length", bool(name) and dims == (640, 360) and abs(filmcut.probe_seconds(exe, joined) - 11.0) < 0.1, f"{name} {dims}")
check("stitch: ... and the mixed-size film moves in every clip's window", bool(name) and filmcut.frozen_join(exe, joined, [4, 4, 3]) is False)
if name: os.remove(joined)
filmcut._download = real_dl

# ---- regression on the REAL clips of the frozen render (when this machine has them) ----------------------------------------------------------------------
plan_path = r"C:\\Users\\punie\\Downloads\\engine-trial\\heritage_redirect\\plan.json"
if os.path.exists(plan_path):
    plan = json.load(open(plan_path, encoding="utf-8"))
    clips = (plan.get("render") or {}).get("shot_clips") or []
    media = os.path.join(ROOT, "api", "tenants", "default", "media")
    files = [os.path.join(media, os.path.basename(c["url"])) for c in clips]
    if clips and all(os.path.exists(f) for f in files):
        lens = [int(c["seconds"]) for c in clips]
        name = filmcut.stitch([f for f in files], lens)
        joined = os.path.join(filmcut.RENDERS_DIR, name) if name else ""
        check("REAL clips of the 28 Oct render (7 clips, two trimmed 3 s -> 2 s): the film is 30 s and NOT frozen", bool(name) and abs(filmcut.probe_seconds(exe, joined) - sum(lens)) < 0.1
              and filmcut.frozen_join(exe, joined, lens) is False, str(name))
        if name: os.remove(joined)
    else:
        print("SKIP the real clips are not on this machine")
else:
    print("SKIP the real render record is not on this machine")

shutil.rmtree(tmp, ignore_errors=True)
print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
