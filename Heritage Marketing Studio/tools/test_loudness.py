#!/usr/bin/env python
"""test_loudness.py -- the finished mix is measured, and brought to a platform's loudness when one is chosen.

Generated audio only (no key, no credit, nothing real touched). A mix is made from a plain tone, then measured by ffmpeg's
EBU R128 meter (`ebur128`, a different filter from the `loudnorm` the code uses) to check the result against the target.

    python tools/test_loudness.py       # exit 0 = every case behaves
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="loud_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import filmaudio as fa   # noqa: E402
import filmcut           # noqa: E402

EXE = filmcut.ffmpeg_exe()
DIR = tempfile.mkdtemp(prefix="loud_media_")
fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


def ff(*a):
    return subprocess.run([EXE, "-y", "-hide_banner", "-loglevel", "error", *a], capture_output=True, text=True)


def lufs(path):
    """Integrated loudness by the EBU R128 meter (a filter the code under test does not use)."""
    r = subprocess.run([EXE, "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    i = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+) LUFS", r.stderr)
    p = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+) dBFS", r.stderr)
    return (float(i.group(1)) if i else None), (float(p.group(1)) if p else None)


def tone(name, secs=20, level=0.1):
    p = os.path.join(DIR, name)
    ff("-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=44100:duration={secs}", "-af", f"volume={level}", "-ac", "2", "-c:a", "libmp3lame", p)
    return p


def digest(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


print("measuring")
quiet = tone("quiet.mp3")
quiet_digest = digest(quiet)
info = fa.loudness_pass(EXE, quiet, None)
meter = lufs(quiet)[0]
check("a mix is measured even when no target is chosen", "integrated" in info and "target" not in info, str(info))
check("the measurement agrees with the EBU R128 meter", meter is not None and abs(info["integrated"] - meter) <= 0.6, f"{info.get('integrated')} vs {meter}")
check("the true peak is reported", isinstance(info.get("true_peak"), float), str(info))
check("with no target the file is left exactly as it was", digest(quiet) == quiet_digest, "")

print("a target")
for preset, want in (("online", -14.0), ("tv-us", -24.0), ("tv-eu", -23.0)):
    p = tone(f"t_{preset}.mp3")
    h0 = digest(p)
    r = fa.loudness_pass(EXE, p, preset)
    got, peak = lufs(p)
    check(f"'{preset}' brings the mix to {want} LUFS (measured independently)", got is not None and abs(got - want) <= 1.0, f"{got} / {r}")
    check(f"'{preset}' keeps the true peak under the ceiling", peak is not None and peak <= fa.LOUDNESS[preset]["tp"] + 0.6, f"{peak}")
    check(f"'{preset}' reports before, after and the target", r.get("target") == want and "before" in r and "after" in r and digest(p) != h0, str(r))

print("a mix that is already there is left alone")
p = tone("again.mp3")
fa.loudness_pass(EXE, p, "online")
h1 = digest(p)
r2 = fa.loudness_pass(EXE, p, "online")
check("a second pass changes nothing", digest(p) == h1 and abs(r2["integrated"] - (-14.0)) <= 1.0, str(r2))

print("a film (picture + sound)")
vid = os.path.join(DIR, "film.mp4")
ff("-f", "lavfi", "-i", "color=c=black:s=160x90:r=10:d=20", "-i", quiet, "-c:v", "mpeg4", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", vid)
d0 = fa.probe_duration(EXE, vid)
r3 = fa.loudness_pass(EXE, vid, "online")
got, _pk = lufs(vid)
banner = subprocess.run([EXE, "-i", vid], capture_output=True, text=True).stderr
check("the film's sound is brought to the target", got is not None and abs(got - (-14.0)) <= 1.2, f"{got} / {r3}")
check("the picture is still there and the length is unchanged", "Video:" in banner and abs((fa.probe_duration(EXE, vid) or 0) - d0) <= 0.2, "")

print("things it will not guess at")
short = tone("short.mp3", secs=2)
rs = fa.loudness_pass(EXE, short, "online")
check("under three seconds it says so and leaves the file alone", "note" in rs and "too short" in rs["note"], str(rs))
sil = os.path.join(DIR, "silence.mp3")
ff("-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "10", "-c:a", "libmp3lame", sil)
hs = digest(sil)
rsil = fa.loudness_pass(EXE, sil, "online")
check("a silent mix is reported as silent and left alone", "silent" in (rsil.get("note") or "") and digest(sil) == hs, str(rsil))
hq = digest(quiet)
rq = fa.loudness_pass(EXE, quiet, "no-such-preset")
check("an unknown preset only measures", "integrated" in rq and "target" not in rq and digest(quiet) == hq, str(rq))
rn = fa.loudness_pass(EXE, os.path.join(DIR, "missing.mp3"), "online")
check("a file that is not there does not raise", "note" in rn, str(rn))

print()
print("All loudness cases behave." if not fails else f"{fails} loudness case(s) FAILED.")
sys.exit(1 if fails else 0)
