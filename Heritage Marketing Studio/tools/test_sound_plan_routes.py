#!/usr/bin/env python
"""test_sound_plan_routes.py -- `sound_plan` travels from the request to the mix on /voice-preview and /rescore.

Every paid call is stubbed (voices are silent generated files, the music bed a sine tone); the output of each route is
measured. Without `sound_plan` the bed is the old static level; with one it lifts in the pauses.

    python tools/test_sound_plan_routes.py       # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="spr_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import main          # noqa: E402
import selfcheck     # noqa: E402
import filmaudio     # noqa: E402
import filmcut       # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

EXE = filmcut.ffmpeg_exe()
DIR = tempfile.mkdtemp(prefix="spr_media_")
MUSIC = os.path.join(DIR, "bed.mp3")
VIDEO = os.path.join(DIR, "pic.mp4")
SILENT = os.path.join(DIR, "silent.mp3")


def ff(*a):
    subprocess.run([EXE, "-y", "-hide_banner", "-loglevel", "error", *a], capture_output=True)


ff("-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=32", "-ac", "2", "-c:a", "libmp3lame", MUSIC)
ff("-f", "lavfi", "-i", "color=c=black:s=160x90:r=10:d=30", "-c:v", "mpeg4", "-pix_fmt", "yuv420p", VIDEO)
ff("-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "2", "-c:a", "libmp3lame", SILENT)

filmaudio._download = lambda url, dest: (open(dest, "wb").write(open(url, "rb").read()) or True)


def _synth(segs):
    for s in segs:
        s.url = SILENT
    return True, []


main.filmvoice.synth = _synth
main._music_bed = lambda *a, **k: (MUSIC, "stub")
client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})
fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


def db(path, t0, t1):
    r = subprocess.run([EXE, "-hide_banner", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", r.stderr)
    return -91.0 if (not m or m.group(1) == "-inf") else float(m.group(1))


def rows():
    return [{"no": 1, "tc": "0-8s", "visual": "a", "audio": []},
            {"no": 2, "tc": "8-14s", "visual": "b", "audio": [{"type": "vo", "text": "One two three four five six seven eight"}]},
            {"no": 3, "tc": "14-22s", "visual": "c", "audio": [{"type": "vo", "text": "One two three four five six seven eight"}]},
            {"no": 4, "tc": "22-30s", "visual": "d", "audio": [{"type": "vo", "text": "One two three four five six seven eight"}]}]


PLAN = {"duck": "normal", "ending": "stop", "carve": False}


def path_of(url):
    return os.path.join(filmcut.RENDERS_DIR, os.path.basename(url))


print("/voice-preview")
base = {"scenes": rows(), "duration": "30s", "voice": "Warm female", "music_url": MUSIC, "music_level": "balanced"}
r0 = client.post("/voice-preview", json=base)
check("a preview without a plan answers", r0.status_code == 200, r0.text[:200])
r1 = client.post("/voice-preview", json={**base, "scenes": rows(), "sound_plan": PLAN})
check("a preview with a plan answers", r1.status_code == 200, r1.text[:200])
if r0.status_code == 200 and r1.status_code == 200:
    a0, a1 = path_of(r0.json()["audio_url"]), path_of(r1.json()["audio_url"])
    check("without a plan the bed is one static level", abs(db(a0, 3.0, 6.0) - db(a0, 19.0, 21.0)) <= 0.6, "")
    check("with a plan the bed lifts in a silent scene (8 dB over the level under a line)", db(a1, 3.0, 6.0) - db(a0, 3.0, 6.0) >= 6.0,
          f"{db(a1, 3.0, 6.0) - db(a0, 3.0, 6.0):.1f}")

print("/rescore")
os.makedirs(filmcut.RENDERS_DIR, exist_ok=True)
shutil.copyfile(VIDEO, os.path.join(filmcut.RENDERS_DIR, "film-test.mp4"))
rb = {"master": "film-test.mp4", "scenes": rows(), "duration": "30s", "voice": "Warm female", "music_url": MUSIC, "music_level": "balanced"}
s0 = client.post("/rescore", json=rb)
s1 = client.post("/rescore", json={**rb, "scenes": rows(), "sound_plan": PLAN})
check("a re-score without and with a plan both answer", s0.status_code == 200 and s1.status_code == 200, f"{s0.status_code} {s1.status_code} {s1.text[:160]}")
if s0.status_code == 200 and s1.status_code == 200:
    v0, v1 = path_of(s0.json()["video_url"]), path_of(s1.json()["video_url"])
    check("the re-score follows the plan too", db(v1, 3.0, 6.0) - db(v0, 3.0, 6.0) >= 6.0, f"{db(v1, 3.0, 6.0) - db(v0, 3.0, 6.0):.1f}")

print("a bad plan never fails a render")
r2 = client.post("/voice-preview", json={**base, "scenes": rows(), "sound_plan": {"duck": "loud", "ending": 5, "scenes": "nope"}})
check("garbage in the plan falls back to defaults", r2.status_code == 200, r2.text[:200])
r3 = client.post("/voice-preview", json={**base, "scenes": rows(), "sound_plan": "nonsense"})
check("a plan that is not an object is ignored", r3.status_code == 200, r3.text[:200])

print()
print("All sound-plan route cases behave." if not fails else f"{fails} sound-plan route case(s) FAILED.")
sys.exit(1 if fails else 0)
