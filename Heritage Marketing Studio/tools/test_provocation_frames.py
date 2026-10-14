#!/usr/bin/env python
"""test_provocation_frames.py -- P3: a Video storyboard frame that stands on an approved provocation follows
the provocation's VISUAL LANGUAGE, overriding the generic look; every other /scene-still caller is untouched.

Captures the real prompt /scene-still builds (image generation stubbed -- zero API spend).

    python tools/test_provocation_frames.py       # exit 0 = behaves
"""
from __future__ import annotations
import os, sys, tempfile
os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="p3frame_")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

import main, gemini, provocation     # noqa: E402
assert main.__file__.replace("\\", "/").endswith("/api/main.py"), main.__file__

VIS = "real pre-dawn, handheld and unlit-looking, no clinical blue, no lab cues"
fails = 0


def check(name, cond, detail=""):
    global fails
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  -> {detail}"))
    fails += 0 if cond else 1


# Stub image generation to capture the prompt; force the google branch; pretend an image provider exists.
_cap = {}
main._have_image = lambda: True
main._use = lambda eng, name: name == "google"
# /scene-still uses image_from_reference when refs exist, else gemini.image -- stub both to capture the prompt.
gemini.image_from_reference = lambda prompt, refs, **kw: (_cap.__setitem__("prompt", prompt) or "http://x/frame.png")
gemini.image = lambda prompt, **kw: (_cap.__setitem__("prompt", prompt) or "http://x/frame.png")
# Stub the resolver so we don't need a real tenant/house/approval; returns an APPROVED-style record with film DNA.
provocation.resolve_for = lambda house_id, pid: ({"status": "approved", "film": {"visual_language": VIS}}
                                                 if pid == "prov-1" and house_id == "house-1" else None)


def frame_prompt(payload):
    _cap.clear()
    main.scene_still(payload)
    return _cap.get("prompt", "")


base = {"video_frame": True, "prompt": "a dark kitchen before dawn, a mother at the sink", "style": "real",
        "engines": {"image": "google"}}

print("A provocation frame carries the provocation's visual language, marked as overriding the look")
p = frame_prompt({**base, "provocation_id": "prov-1", "use_provocation": True, "house_id": "house-1"})
check("the frame rendered a prompt", bool(p), p[:80])
check("the provocation's visual language is in the prompt", VIS in p, p[-200:])
check("it is stated as OVERRIDING the generic look", "OVERRIDES any generic look" in p, p[-200:])

print("\nWithout a provocation the prompt is unchanged (no visual-language injection)")
p2 = frame_prompt(base)
check("no provocation visual language", VIS not in p2 and "OVERRIDES any generic look" not in p2, p2[-160:])

print("\nAn UNapproved / wrong-house provocation is ignored (resolve_for returns None)")
p3 = frame_prompt({**base, "provocation_id": "prov-1", "use_provocation": True, "house_id": "other-house"})
check("wrong house -> no injection", VIS not in p3, p3[-120:])
p4 = frame_prompt({**base, "provocation_id": "prov-1", "use_provocation": False, "house_id": "house-1"})
check("set aside (use_provocation false) -> no injection", VIS not in p4, p4[-120:])

print("\nA non-video_frame caller (Social/Carousel/POSM) never gets the injection even with the field present")
p5 = frame_prompt({"prompt": "a social still", "style": "real", "engines": {"image": "google"},
                   "provocation_id": "prov-1", "use_provocation": True, "house_id": "house-1"})
check("no video_frame -> no injection", VIS not in p5, p5[-120:])

print()
if fails:
    print(f"{fails} case(s) FAILED")
    sys.exit(1)
print("All P3 frame cases behave.")
