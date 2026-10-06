#!/usr/bin/env python
"""test_beat_prompts.py -- what each shot of a film is briefed with, role and beat direction included.

Drives /produce-video in-process with every paid call stubbed (no key, no cost, nothing real written): the stubs only
capture the prompt each shot would have been sent. Pins that
  * a film with no beat_role/beat_note is briefed exactly as it was (positional roles, the last shot is the ENDFRAME);
  * a `button` after the sign-off gets the button direction and the sign-off keeps the ENDFRAME one (never two);
  * a scene's own Beat direction text rides on that shot only.

    python tools/test_beat_prompts.py       # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="beatprompts_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import main          # noqa: E402
import selfcheck     # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

os.environ["FAL_KEY"] = "stub"          # the route refuses without one; nothing is ever called with it
seen: dict[int, str] = {}


def _capture(model_id, prompt, *a, **k):
    seen[len(seen)] = prompt
    return {}          # no url: the shot 'fails', which is all this test needs


main.gemini.available = lambda: False
main.creative.generate_creative = _capture
main.creative.video_from_image = lambda model_id, prompt, *a, **k: _capture(model_id, prompt)

client = TestClient(main.app, raise_server_exceptions=True,
                    headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})
fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


def scene(no, visual, **extra):
    return {"no": no, "tc": f"{(no - 1) * 6}-{no * 6}s", "visual": visual, "camera": "static",
            "audio": [{"type": "vo", "text": "A short line of narration for this scene."}], **extra}


def prompts_for(scenes):
    seen.clear()
    client.post("/produce-video", json={"scenes": scenes, "duration": "30s", "aspect": "16:9", "style": "real",
                                        "engines": {"video": "fal"}, "music": "warm"})
    return [seen[i] for i in sorted(seen)]


def shot(ps, marker):
    """The prompt of the shot whose scene text contains `marker` (shots render in parallel, so order is not scene order)."""
    hits = [p for p in ps if marker in p]
    return hits[0] if hits else ""


def count(ps, text):
    return sum(1 for p in ps if text in p)


plain = [scene(i, f"Scene number {i} visual.") for i in range(1, 5)]
base = prompts_for(plain)
check("every scene produced a shot prompt", len(base) >= 4, str(len(base)))
check("no explicit role: exactly one ENDFRAME, on the last scene's shot", count(base, "ENDFRAME") == 1 and "ENDFRAME" in shot(base, "Scene number 4 visual"))
check("no explicit role: no button, no beat direction", count(base, "BUTTON") == 0 and count(base, "Direction for this beat") == 0)
check("the emphasis sentence is on the non-endframe roles", count(base, "The scene's own description decides what is shown") >= 2)
check("the endframe direction does not carry it", "decides what is shown" not in shot(base, "Scene number 4 visual").split("ENDFRAME")[1][:400])

with_button = [scene(i, f"Scene number {i} visual.") for i in range(1, 5)] + [scene(5, "A last small joke at the doorframe.", beat_role="button")]
ps = prompts_for(with_button)
check("with a button: one ENDFRAME and one BUTTON", count(ps, "ENDFRAME") == 1 and count(ps, "BUTTON") == 1)
check("the button is on the joke scene, the sign-off on scene 4", "BUTTON" in shot(ps, "last small joke") and "ENDFRAME" in shot(ps, "Scene number 4 visual"))
check("the button is briefed with no pack presentation", "no pack presentation" in shot(ps, "last small joke"))

noted = [scene(1, "Scene number 1 visual.", beat_note="Hold on the hands, very quiet."), *[scene(i, f"Scene number {i} visual.") for i in range(2, 5)]]
ps = prompts_for(noted)
check("a beat direction rides on its own shot", "Direction for this beat: Hold on the hands, very quiet." in shot(ps, "Scene number 1 visual"))
check("and on no other shot", count(ps, "Hold on the hands") == 1)

print()
print("All beat-prompt cases behave." if not fails else f"{fails} beat-prompt case(s) FAILED.")
sys.exit(1 if fails else 0)
