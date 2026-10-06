#!/usr/bin/env python
"""test_produce_sound.py -- /produce-video, the one route that joins picture, voices, music and extras, run end to end.

Every paid call is stubbed (video clips are one generated local file, voices are silent files, the music a sine tone); the
real joining, voice placement, mix, sound plan and loudness pass all run, and the finished film is measured. The other
routes are covered by test_sound_plan_routes.py; this one exists because it is the route a real render goes through and the
only one whose sound-design wiring would otherwise first run on a paid render.

    python tools/test_produce_sound.py       # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="prodsound_")
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

os.environ["FAL_KEY"] = "stub"          # the route refuses without one; nothing is ever sent with it
EXE = filmcut.ffmpeg_exe()
DIR = tempfile.mkdtemp(prefix="prodsound_media_")
CLIP, MUSIC, SILENT, BLIP = (os.path.join(DIR, n) for n in ("clip.mp4", "bed.mp3", "silent.mp3", "blip.mp3"))


def ff(*a):
    subprocess.run([EXE, "-y", "-hide_banner", "-loglevel", "error", *a], capture_output=True)


ff("-f", "lavfi", "-i", "color=c=black:s=160x90:r=10:d=10", "-c:v", "mpeg4", "-pix_fmt", "yuv420p", CLIP)
ff("-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=40", "-ac", "2", "-c:a", "libmp3lame", MUSIC)
ff("-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "2", "-c:a", "libmp3lame", SILENT)
ff("-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100:duration=1", "-ac", "2", "-c:a", "libmp3lame", BLIP)


def _copy(url, dest, *a, **k):
    with open(url, "rb") as src, open(dest, "wb") as out:
        out.write(src.read())
    return True


filmaudio._download = _copy
filmcut._download = _copy
main.gemini.available = lambda: False
main.creative.generate_creative = lambda model, prompt, **k: {"url": CLIP, "provider": "fal", "kind": "video"}
main.creative.video_from_image = lambda model, prompt, frame, **k: CLIP
main.filmvoice.synth = lambda segs: ([setattr(s, "url", SILENT) for s in segs] and True, [])
main._music_bed = lambda *a, **k: (MUSIC, "stub")
main.library.get = lambda i: ({"id": i, "kind": "ambience", "signed_off": True, "url": MUSIC} if i == "AMB" else
                              {"id": i, "kind": "sfx", "signed_off": True, "url": BLIP} if i == "SFX" else None)
client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})
fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


def db(path, t0, t1):
    r = subprocess.run([EXE, "-hide_banner", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", path, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", r.stderr)
    return -91.0 if (not m or m.group(1) == "-inf") else float(m.group(1))


def lufs(path):
    r = subprocess.run([EXE, "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+) LUFS", r.stderr)
    return float(m.group(1)) if m else None


def rows():
    return [{"no": 1, "tc": "0-8s", "visual": "Scene one.", "camera": "static", "audio": []},
            {"no": 2, "tc": "8-14s", "visual": "Scene two.", "camera": "static", "audio": [{"type": "vo", "text": "One two three four five six seven eight"}]},
            {"no": 3, "tc": "14-22s", "visual": "Scene three.", "camera": "static", "audio": [{"type": "vo", "text": "One two three four five six seven eight"}]},
            {"no": 4, "tc": "22-30s", "visual": "Scene four.", "camera": "static", "audio": [{"type": "vo", "text": "One two three four five six seven eight"}]}]


def produce(**extra):
    body = {"scenes": rows(), "duration": "30s", "aspect": "16:9", "style": "real", "engines": {"video": "fal", "music": "auto"},
            "music_url": MUSIC, "music_level": "balanced", "voice": "Warm female", **extra}
    return client.post("/produce-video", json=body)


def film_path(resp):
    return os.path.join(filmcut.RENDERS_DIR, os.path.basename(resp.json()["video_url"]))


print("a render with no sound plan (how every film was made until now)")
a = produce()
check("it renders", a.status_code == 200 and a.json().get("video_url"), a.text[:300])
check("and reports how loud it is, without changing it", "integrated" in (a.json().get("loudness") or {}) and "target" not in a.json()["loudness"], str(a.json().get("loudness")))
if a.status_code == 200:
    pa = film_path(a)
    check("the music is one steady level", abs(db(pa, 3.0, 6.0) - db(pa, 15.0, 17.0)) <= 0.8, f"{db(pa, 3.0, 6.0):.1f} vs {db(pa, 15.0, 17.0):.1f}")

print("a render with a sound plan, room tone, a key sound and a loudness target")
plan = {"duck": "normal", "ending": "stop", "carve": False, "ambience": {"id": "AMB", "level": "present"}, "sounds": [{"scene": 2, "when": "start", "id": "SFX"}]}
b = produce(sound_plan=plan, loudness="online")
check("it renders", b.status_code == 200 and b.json().get("video_url"), b.text[:300])
if b.status_code == 200:
    d = b.json()
    pb = film_path(b)
    check("it reports the loudness it brought the film to", (d.get("loudness") or {}).get("target") == -14.0, str(d.get("loudness")))
    got = lufs(pb)
    check("the finished film really is at the online target (measured independently)", got is not None and abs(got - (-14.0)) <= 1.3, str(got))
    plan_only = produce(sound_plan={"duck": "normal", "ending": "stop", "carve": False})
    if plan_only.status_code == 200:
        pp = film_path(plan_only)
        check("with a plan the music lifts in a silent scene, where the film without one kept it at its steady level",
              db(pp, 3.0, 6.0) - db(pa, 3.0, 6.0) >= 6.0, f"{db(pp, 3.0, 6.0) - db(pa, 3.0, 6.0):.1f}")
    check("the response carries no error for a clean render", not (d.get("detail") or "").strip() or "could not" not in d["detail"], str(d.get("detail")))

print("a library sound that is gone is said, and the film still renders")
c = produce(sound_plan={"duck": "normal", "sounds": [{"scene": 2, "when": "start", "id": "GONE"}]})
check("the render succeeds and says which sound it left out", c.status_code == 200 and "key sound" in (c.json().get("detail") or ""), c.text[:300])

print("a plan that ffmpeg cannot mix does not cost the film its soundtrack")
real_bed = main.soundplan.bed_filter
main.soundplan.bed_filter = lambda resolved, *a, **k: "volume='((((':eval=frame" if resolved else None
d2 = produce(sound_plan={"duck": "normal"})
main.soundplan.bed_filter = real_bed
check("the render still has its music and says why the plan was not applied",
      d2.status_code == 200 and "music" in (d2.json().get("audio") or "") and "could not be mixed" in (d2.json().get("detail") or ""), d2.text[:300])
if d2.status_code == 200:
    pd = film_path(d2)
    check("and the film carries sound", db(pd, 3.0, 6.0) > -60, f"{db(pd, 3.0, 6.0):.1f}")

print("garbage never breaks a render")
e = produce(sound_plan="nonsense", loudness=42)
check("a plan that is not an object and a loudness that is not a name are ignored", e.status_code == 200 and e.json().get("video_url"), e.text[:300])

print()
print("All produce-with-sound cases behave." if not fails else f"{fails} produce-with-sound case(s) FAILED.")
sys.exit(1 if fails else 0)
