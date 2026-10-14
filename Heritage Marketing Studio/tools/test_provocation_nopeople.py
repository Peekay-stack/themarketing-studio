#!/usr/bin/env python
"""test_provocation_nopeople.py -- P3b: a Video storyboard frame standing on a provocation that casts
OBJECTS / ANIMATED / NONE has no people to hold identical, so the "reuse the EXACT same people" frame
clause is swapped for object/style continuity. A people-cast provocation, and any non-provocation frame,
keep the people clause exactly as before.

Captures the real prompt /scene-still builds (image generation stubbed -- zero API spend).

    python tools/test_provocation_nopeople.py       # exit 0 = behaves
"""
from __future__ import annotations
import os, sys, tempfile
os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="p3bframe_")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

import main, gemini, provocation     # noqa: E402
assert main.__file__.replace("\\", "/").endswith("/api/main.py"), main.__file__

VIS = "flat hand-drawn 2D animation, bold outlines, no photoreal lighting"
PEOPLE = "reusing the EXACT same people"
FACES = "identical faces, hair, skin tone and body type"
OBJECTS = "objects, materials, colours and visual style consistent with the other shots"
fails = 0


def check(name, cond, detail=""):
    global fails
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  -> {detail}"))
    fails += 0 if cond else 1


_cap = {}
main._have_image = lambda: True
main._use = lambda eng, name: name == "google"
main._record_made = lambda *a, **k: None          # never write a real ledger file
gemini.image_from_reference = lambda prompt, refs, **kw: (_cap.__setitem__("prompt", prompt) or "http://x/frame.png")
gemini.image = lambda prompt, **kw: (_cap.__setitem__("prompt", prompt) or "http://x/frame.png")

# resolve_for returns an approved record whose cast_approach we vary per case.
_cast = {"v": "people"}
provocation.resolve_for = lambda house_id, pid: (
    {"status": "approved", "film": {"visual_language": VIS, "cast_approach": _cast["v"]}}
    if pid == "prov-1" and house_id == "house-1" else None)


def frame_prompt(payload, cast="people"):
    _cast["v"] = cast
    _cap.clear()
    main.scene_still(payload)
    return _cap.get("prompt", "")


# A caller reference (the locked image) forces the reference path -> the people/continuity branch.
base = {"video_frame": True, "prompt": "a glass of milk on a windowsill at dawn", "style": "real",
        "engines": {"image": "google"}, "reference_url": "http://x/lock.png",
        "provocation_id": "prov-1", "use_provocation": True, "house_id": "house-1"}

print("A people-cast provocation frame keeps the 'same people' continuity clause")
p = frame_prompt(base, cast="people")
check("the frame rendered a prompt from the reference path", bool(p), p[:80])
check("'reuse the EXACT same people' is present", PEOPLE.lower() in p.lower(), p[:220])
check("the faces/hair/skin lock is present", FACES in p, p[:260])
check("object-style continuity is NOT used", OBJECTS not in p, p[:260])
check("the provocation's visual language still rides (P3a)", VIS in p, p[-200:])

for ca in ("objects", "animated", "none"):
    print(f"\nA '{ca}'-cast provocation frame swaps to object/style continuity, no people")
    q = frame_prompt(base, cast=ca)
    check("no 'same people' clause", PEOPLE.lower() not in q.lower(), q[:260])
    check("no faces/hair/skin lock", FACES not in q, q[:260])
    check("object/style continuity is used", OBJECTS in q, q[:260])
    check("the provocation's visual language still rides (P3a)", VIS in q, q[-200:])

print("\nA non-provocation frame (no provocation_id) keeps the people clause unchanged")
noprov = {"video_frame": True, "prompt": "a glass of milk on a windowsill at dawn", "style": "real",
          "engines": {"image": "google"}, "reference_url": "http://x/lock.png"}
r = frame_prompt(noprov)
check("'reuse the EXACT same people' is present", PEOPLE.lower() in r.lower(), r[:220])
check("object/style continuity is NOT used", OBJECTS not in r, r[:220])

print()
if fails:
    print(f"{fails} case(s) FAILED")
    sys.exit(1)
print("All P3b no-people frame cases behave.")
