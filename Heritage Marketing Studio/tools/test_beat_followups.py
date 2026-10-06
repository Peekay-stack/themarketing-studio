#!/usr/bin/env python
"""test_beat_followups.py -- the Beat role's reach beyond the prompt: the Word script file and the continuity check.

  * The script's Word export has a Beat column (role, then the person's direction) and importing an edited file reads it
    back; a file from before the column existed imports exactly as it did.
  * The continuity check keeps a `button` shot out of the location-look comparison, as it already did the `brand`
    endframe (a comeback after the sign-off may change set or light), and still reports it.

    python tools/test_beat_followups.py       # exit 0 = every case behaves   (no key, no cost, nothing real touched)
"""
from __future__ import annotations

import os
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="beatfollow_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import continuity  # noqa: E402
import docs        # noqa: E402
import roundtrip   # noqa: E402

fails = 0


def check(name, got, want):
    global fails
    ok = got == want
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + ("" if ok else f"   got {got!r}, want {want!r}"))


def sc(no, **kw):
    return {"no": no, "tc": f"{(no - 1) * 6}-{no * 6}s", "visual": f"Scene {no} visual.", "camera": "static",
            "dialogue": f"VO: line {no}", "supr": "", **kw}


def roundtrip_rows(scenes):
    path = docs.build_script_docx("T", "A logline.", scenes)
    return roundtrip.import_script(open(path, "rb").read())["rows"]


print("the Word script file")
rows = roundtrip_rows([sc(1, beat_note="Hold on the hands."), sc(2), sc(3, beat_role="brand"),
                       sc(4, beat_role="button", beat_note="A quick comeback at the doorframe.")])
check("an Auto scene with no direction reads back with no beat keys", [k for k in rows[1] if k.startswith("beat")], [])
check("a direction alone reads back as a direction", (rows[0].get("beat_role"), rows[0].get("beat_note")), (None, "Hold on the hands."))
check("a Sign-off reads back as brand", rows[2].get("beat_role"), "brand")
check("a Button with a direction reads back as both", (rows[3].get("beat_role"), rows[3].get("beat_note")), ("button", "A quick comeback at the doorframe."))
check("the other columns are untouched", [r["visual"] for r in rows], [f"Scene {i} visual." for i in range(1, 5)])
check("scene numbers are untouched", [r["no"] for r in rows], [1, 2, 3, 4])

print("an older file (no Beat column) imports as before")
from docx import Document  # noqa: E402

d = Document()
t = d.add_table(rows=2, cols=5)
for i, h in enumerate(["Scene", "Visual / Action", "Camera", "Dialogue / VO", "Super"]):
    t.rows[0].cells[i].text = h
for i, v in enumerate(["1\n0-6s", "Kitchen at dawn.", "static", "VO: hello", ""]):
    t.rows[1].cells[i].text = v
p = os.path.join(_scratch, "old.docx")
d.save(p)
old = roundtrip.import_script(open(p, "rb").read())["rows"]
check("one row read", len(old), 1)
check("no beat keys appear", [k for k in old[0] if k.startswith("beat")], [])
check("parse: a label with a dash tail still reads as the role", roundtrip.parse_beat_cell("Button — after the sign-off"), {"beat_role": "button"})
check("parse: unknown first line is all direction", roundtrip.parse_beat_cell("Make it quieter"), {"beat_note": "Make it quieter"})
check("parse: empty cell sets nothing", roundtrip.parse_beat_cell("  "), {})

print("the continuity check")
M = {"a": (10.0, 30.0, 50.0), "b": (11.0, 31.0, 51.0), "c": (12.0, 32.0, 52.0), "d": (45.0, 70.0, 80.0)}   # d is far off


def run(role_of_d):
    continuity.clip_metrics = lambda path, seconds=0: dict(zip(("warmth", "saturation", "luma"), M[os.path.basename(path)]))
    clips = [{"n": i + 1, "role": (role_of_d if k == "d" else ""), "seconds": 6, "path": k} for i, k in enumerate("abcd")]
    return continuity.drift(clips, "")


auto = run("")
check("with the far-off shot as an ordinary scene, the film is flagged", auto["ok"], False)
btn = run("button")
check("as a button it is kept out of the comparison: the film reads as one film", btn["ok"], True)
check("and the button is still measured and reported", btn["spread"]["warmth"]["button"], [{"n": 4, "warmth": 45.0}])
check("the compared shots exclude it", btn["spread"]["warmth"]["compared"], [1, 2, 3])
brand = run("brand")
check("the brand endframe still behaves as before", (brand["ok"], brand["spread"]["warmth"]["endframe"]), (True, [{"n": 4, "warmth": 45.0}]))
check("a film with no brand/button has empty lists", (auto["spread"]["warmth"]["endframe"], auto["spread"]["warmth"]["button"]), ([], []))

print()
print("All beat follow-up cases behave." if not fails else f"{fails} beat follow-up case(s) FAILED.")
sys.exit(1 if fails else 0)
