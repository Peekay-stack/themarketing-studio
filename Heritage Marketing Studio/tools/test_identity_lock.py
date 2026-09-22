#!/usr/bin/env python
"""test_identity_lock.py -- the "reuse the exact people" wording /scene-still sends when a cast/plate
reference is attached. Had no test coverage at all before 22 Sep, despite being the load-bearing prompt
every Social, Carousel and Video continuity shot with a real cast reference goes through.

Why now: a real Carousel (a recurring milkman across a 1994-to-present before/after, one signed-off cast
reference for the whole set) held his FACE correctly -- the cast-reference fix earlier the same day made
that work -- but never let him age. Traced to "identical faces, hair, skin tone, body type and AGES" being
unconditional, the same failure mode this file had already fixed once for clothing (a 5:45am bedroom shot
kept the exam-hall outfit, because the fixed clause always won over the shot's own words). Age now gets the
identical treatment: it follows the shot's OWN description when the description says something about age,
and only defaults to matching the reference when it says nothing.

Calls the real `/scene-still` route in-process with the image providers stubbed -- no key, no cost, nothing
real touched. Proves the WORDING sent, not what a real model then draws with it.

    python tools/test_identity_lock.py       # exit 0 = every check behaves
"""
from __future__ import annotations

import os
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="identity_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import main          # noqa: E402
import selfcheck     # noqa: E402
import library       # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

seen_prompts: list[str] = []

main._have_image = lambda: True
main._record_made = lambda *a, **k: None
main.gemini.image_from_reference = lambda prompt, refs, **k: (seen_prompts.append(prompt) or "http://stub/img.png")
main.creative.image_from_reference = lambda prompt, refs, **k: (seen_prompts.append(prompt) or "http://stub/img.png")

CAST_ID = "CAST1"
CAST_URL = "http://stub/cast.png"
library.reference_url = lambda kind, brand="": CAST_URL if kind == "cast" else ""
library.get = lambda i: ({"id": i, "url": CAST_URL, "kind": "cast", "signed_off": True} if i == CAST_ID else None)
library._owned = lambda row: True

client = TestClient(main.app, raise_server_exceptions=True,
                    headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})

failures = 0


def check(label, ok, extra=""):
    global failures
    print(f"  {'ok  ' if ok else 'FAIL'} {label}" + (f"   [{extra}]" if extra else ""))
    if not ok:
        failures += 1


def send(scene, cast_id=CAST_ID, use_cast=True):
    seen_prompts.clear()
    body = {"scene_no": 1, "ratio": "16:9", "style": "real", "prompt": scene, "brand_mode": "grounded",
            "use_cast": use_cast, "cast_id": cast_id}
    r = client.post("/scene-still", json=body)
    return r.status_code, (seen_prompts[0] if seen_prompts else "")


st, pr = send("A man waters the plants in his garden at dawn.")
check("face/hair/skin tone/body type still lock unconditionally (identity, never touched by this fix)",
      "identical faces, hair, skin tone and body type" in pr)
check("age is NOT in that unconditional list any more -- the exact 22 Sep failure",
      "identical faces, hair, skin tone and body type and ages" not in pr
      and "skin tone, body type and ages" not in pr)
check("a scene with nothing about age keeps the instruction to default to the reference's own age",
      "otherwise identical age to the reference" in pr)
check("the age instruction still tells the model to follow the shot's own words when they say something",
      "as this new shot's own description calls for" in pr and "how old they look or how much time has passed" in pr)
check("...while keeping the same identifiable person, older or younger -- not a licence to swap faces",
      "keeping the same face, bone structure and identity clearly recognisable" in pr)
check("clothing's own existing conditional wording is untouched by this change",
      "clothing as described for this new shot if it says anything about what they are wearing" in pr)

# The instruction text is identical regardless of what the scene says -- this is a MODEL instruction, not
# server-side branching (the same design as clothing) -- so every scene gets the same wording, and the
# model itself decides whether ITS scene calls for a different age. Pin that this holds for an explicitly
# age-driven scene too, so the wording is proven present in the exact case that mattered live.
st, pr = send("1994. A young man hands milk to an elderly woman at the same doorstep, 31 years before today.")
check("an explicitly age-driven scene gets the SAME instruction (the model reads the scene, not the server)",
      "as this new shot's own description calls for" in pr and "otherwise identical age to the reference" in pr)

st, pr = send("A man waters the plants in his garden at dawn.", cast_id="", use_cast=False)
check("cast explicitly switched off -> the identity-lock opening never appears (nothing to lock to)",
      "reusing the EXACT same people" not in pr and "Reuse the EXACT same people" not in pr)

print()
if failures:
    print(f"{failures} check(s) FAILED")
    sys.exit(1)
print("Identity-lock wording (age now conditional, like clothing) behaves.")
