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


print("/sound-plan (the card's starting plan)")
base_rows = [{"no": n, "tc": f"{(n - 1) * 7}-{n * 7}s", "visual": f"Scene {n}.", "audio": []} for n in range(1, 5)]
sb = client.post("/sound-plan", json={"scenes": base_rows})
check("the route answers", sb.status_code == 200, sb.text[:200])
if sb.status_code == 200:
    got = sb.json()["scenes"]
    check("every scene comes back with its role and music state", [(g["no"], g["music"]) for g in got] == [(1, "open"), (2, "open"), (3, "swell"), (4, "swell")], str(got))
    check("roles are the ones the shots are briefed with", [g["role"] for g in got] == ["hook", "mechanism", "turn", "brand"], str([g["role"] for g in got]))
    sb2 = client.post("/sound-plan", json={"scenes": base_rows + [{"no": 5, "tc": "28-32s", "visual": "x", "audio": [], "beat_role": "button"}]})
    check("a Button drops out and the sign-off is still the last Auto scene", [(g["no"], g["music"]) for g in sb2.json()["scenes"]][-2:] == [(4, "swell"), (5, "out")], "")
check("no scenes is fine", client.post("/sound-plan", json={}).json() == {"scenes": []}, "")

print("saved with the film")
SAVED = {"house": "hx", "full_script": base_rows, "sound_plan": {"duck": "strong", "scenes": {"3": "out"}, "mood": "Soft sarangi", "moodTouched": True}}
check("the plan saves", client.post("/video-script", json=SAVED).status_code == 200, "")
back = client.get("/video-script", params={"house": "hx"}).json()
check("and comes back whole", back.get("sound_plan") == SAVED["sound_plan"], str(back.get("sound_plan")))
client.post("/video-script", json={"house": "hx", "full_script": base_rows})        # a page from before the field existed
check("an older page that never sends it does not blank it", client.get("/video-script", params={"house": "hx"}).json().get("sound_plan") == SAVED["sound_plan"], "")
client.post("/video-script", json={"house": "hx", "full_script": base_rows, "sound_plan": {}})
check("sending an empty plan clears it", client.get("/video-script", params={"house": "hx"}).json().get("sound_plan") == {}, "")
check("a house with nothing saved reads an empty plan", client.get("/video-script", params={"house": "nobody"}).json().get("sound_plan") == {}, "")
client.post("/video-script", json={"house": "hx", "full_script": base_rows, "sound_plan": "garbage"})
check("a plan that is not an object is stored as empty", client.get("/video-script", params={"house": "hx"}).json().get("sound_plan") == {}, "")

print("ambience and key sounds come from the library, and only signed-off ones")
BLIP = os.path.join(DIR, "blip.mp3")
ff("-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100:duration=1", "-ac", "2", "-c:a", "libmp3lame", BLIP)
LIB = {"AMB1": {"id": "AMB1", "kind": "ambience", "signed_off": True, "url": MUSIC},
       "SFX1": {"id": "SFX1", "kind": "sfx", "signed_off": True, "url": BLIP},
       "SFX_UNSIGNED": {"id": "SFX_UNSIGNED", "kind": "sfx", "signed_off": False, "url": BLIP},
       "PACK1": {"id": "PACK1", "kind": "pack", "signed_off": True, "url": BLIP}}
main.library.get = lambda i: LIB.get(str(i))
resolved = main.soundplan.resolve({"ambience": {"id": "AMB1", "level": "present"},
                                   "sounds": [{"scene": 2, "when": "start", "id": "SFX1"}, {"scene": 3, "when": "start", "id": "SFX_UNSIGNED"},
                                              {"scene": 3, "when": "end", "id": "PACK1"}, {"scene": 4, "when": "start", "id": "NOPE"}]}, rows(), 30)
args, notes = main._plan_sound_args(resolved)
check("a signed-off ambience and key sound become the mixer's own arguments",
      args.get("ambience") == MUSIC and args.get("ambience_level_name") == "present" and [x["url"] for x in args.get("spots", [])] == [BLIP], str(args))
check("an unsigned item, an item of the wrong kind and a missing one are each said, not skipped silently", len(notes) == 3, str(notes))
check("a plan that names nothing needs nothing", main._plan_sound_args(main.soundplan.resolve({"duck": "normal"}, rows(), 30)) == ({}, []), "")
check("no plan, no arguments", main._plan_sound_args(None) == ({}, []), "")

pv_base = {"scenes": rows(), "duration": "30s", "voice": "Warm female", "music_url": MUSIC, "music_level": "balanced"}
plain = client.post("/voice-preview", json={**pv_base, "scenes": rows(), "sound_plan": PLAN})
withx = client.post("/voice-preview", json={**pv_base, "scenes": rows(), "sound_plan": {**PLAN, "sounds": [{"scene": 2, "when": "start", "id": "SFX1"}, {"scene": 3, "when": "start", "id": "SFX_UNSIGNED"}]}})
check("a preview with a key sound answers and says which sound it left out", withx.status_code == 200 and "key sound" in (withx.json().get("detail") or ""), withx.text[:240])
if plain.status_code == 200 and withx.status_code == 200:
    a, b = path_of(plain.json()["audio_url"]), path_of(withx.json()["audio_url"])
    # The route re-times the scenes from their dialogue first, so the sound lands where THAT timing puts scene 2.
    rr = rows()
    main.filmvoice.retime(rr, target_total=30)
    t_spot = main.soundplan.resolve({"sounds": [{"scene": 2, "when": "start", "id": "SFX1"}]}, rr, 30)["spots"][0]["at"]
    t_gone = main.soundplan.resolve({"sounds": [{"scene": 3, "when": "start", "id": "SFX1"}]}, rr, 30)["spots"][0]["at"]
    check("the key sound is audible in the preview at its scene", db(b, t_spot + 0.1, t_spot + 0.8) - db(a, t_spot + 0.1, t_spot + 0.8) >= 1.0,
          f"{db(b, t_spot + 0.1, t_spot + 0.8) - db(a, t_spot + 0.1, t_spot + 0.8):.1f} at {t_spot}")
    check("and the unsigned one is not (its scene is untouched)", abs(db(b, t_gone + 0.1, t_gone + 0.8) - db(a, t_gone + 0.1, t_gone + 0.8)) <= 0.8,
          f"{db(b, t_gone + 0.1, t_gone + 0.8) - db(a, t_gone + 0.1, t_gone + 0.8):.1f}")
amb = client.post("/voice-preview", json={**pv_base, "scenes": rows(), "sound_plan": {**PLAN, "ambience": {"id": "AMB1", "level": "location"}}})
check("an ambience bed lifts the whole preview", amb.status_code == 200 and db(path_of(amb.json()["audio_url"]), 3.0, 6.0) - db(path_of(plain.json()["audio_url"]), 3.0, 6.0) >= 1.0, "")

print("loudness")


def lufs_of(path):
    r = subprocess.run([EXE, "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+) LUFS", r.stderr)
    return float(m.group(1)) if m else None


lb = {"scenes": rows(), "duration": "30s", "voice": "Warm female", "music_url": MUSIC, "music_level": "forward", "sound_plan": PLAN}
l0 = client.post("/voice-preview", json={**lb, "scenes": rows()})
l1 = client.post("/voice-preview", json={**lb, "scenes": rows(), "loudness": "online"})
l2 = client.post("/voice-preview", json={**lb, "scenes": rows(), "loudness": "tv-us"})
check("a preview always reports how loud it is", l0.status_code == 200 and "integrated" in l0.json().get("loudness", {}) and "target" not in l0.json()["loudness"], l0.text[:200])
check("with a target it reports the target and what it did", l1.status_code == 200 and l1.json()["loudness"].get("target") == -14.0 and "after" in l1.json()["loudness"], l1.text[:200])
if l0.status_code == 200 and l1.status_code == 200 and l2.status_code == 200:
    m1, m2 = lufs_of(path_of(l1.json()["audio_url"])), lufs_of(path_of(l2.json()["audio_url"]))
    check("the preview file itself is at the online target", m1 is not None and abs(m1 - (-14.0)) <= 1.2, str(m1))
    check("and a different target gives a different loudness (TV US is 10 LU quieter)", m2 is not None and m1 is not None and 8.0 <= m1 - m2 <= 12.0, f"{m1} vs {m2}")
l3 = client.post("/voice-preview", json={**lb, "scenes": rows(), "loudness": "nonsense"})
check("an unknown target never fails a preview, it only measures", l3.status_code == 200 and "target" not in l3.json()["loudness"], l3.text[:200])
sr = client.post("/rescore", json={**rb, "scenes": rows(), "sound_plan": PLAN, "loudness": "online"})
check("a re-score reports and applies it too", sr.status_code == 200 and sr.json().get("loudness", {}).get("target") == -14.0, sr.text[:200])
if sr.status_code == 200:
    mv = lufs_of(path_of(sr.json()["video_url"]))
    check("the re-scored film is at the target", mv is not None and abs(mv - (-14.0)) <= 1.5, str(mv))

print("downstream: the Production Bible and the other routes that now receive sound fields")
bible = client.post("/production-bible-docx", json={
    "title": "Test film — production bible", "logline": "A logline.", "scenes": base_rows,
    "departments": [{"label": "Music", "text": "Warm.\nSuggested style: Soft sarangi."},
                    {"label": "Sound design", "text": "AMBIENCE: a quiet kitchen.\nKEY SOUNDS: the pour."}],
    "frames": [], "characters": "MOTHER: blue saree.", "cast_reference": "", "meta": {"Duration": "30s", "Music": "Soft sarangi"}})
check("the production bible builds with the Sound design department in it", bible.status_code == 200, bible.text[:200])
if bible.status_code == 200:
    import io
    from docx import Document
    doc = Document(io.BytesIO(bible.content))
    text = "\n".join(p.text for p in doc.paragraphs) + "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    check("and the note is in the document", "Sound design" in text and "a quiet kitchen" in text, text[:200])
vp = client.post("/voice-plan", json={**pv_base, "scenes": rows(), "sound_plan": PLAN, "loudness": "online"})
check("/voice-plan accepts the new fields and ignores them", vp.status_code == 200, vp.text[:200])

print()
print("All sound-plan route cases behave." if not fails else f"{fails} sound-plan route case(s) FAILED.")
sys.exit(1 if fails else 0)
