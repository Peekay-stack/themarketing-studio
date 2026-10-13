#!/usr/bin/env python
"""test_voice_lang_fallback.py -- a line the voice model can't render in its language is read without a language
hint, not dropped.

Live finding (13 Oct): with the brand's language mix in play, a Telugu on-camera line ("Taaza undi, raa", language
"te") was sent to fal's ElevenLabs multilingual-v2, which does not support Telugu, so it failed and vanished from the
mix. The render loop only retried on an unavailable VOICE, never on an unsupported LANGUAGE. Now, on failure, the same
voice is retried with no language_code -- the model reads the (usually romanised) text as best it can -- before the
voice fallback. An imperfect read beats a missing line.

    python tools/test_voice_lang_fallback.py       # exit 0 = behaves
"""
from __future__ import annotations
import os, sys, tempfile
os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="vlang_")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

import filmvoice as fv       # noqa: E402
import filmaudio            # noqa: E402

fails = 0


def check(name, cond, detail=""):
    global fails
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  -> {detail}"))
    fails += 0 if cond else 1


def run(unsupported: set[str]):
    """Stub fal: fails when a language_code in `unsupported` is present, succeeds otherwise. Returns (seg, notes, attempts)."""
    attempts = []

    def fake(model, args):
        attempts.append(args.get("language_code", "(none)"))
        return None if args.get("language_code") in unsupported else "https://x/line.mp3"
    filmaudio.run_fal = fake
    seg = fv.Segment(kind="dialogue", speaker="Mother", text="Taaza undi, raa.", start=12.0, end=18.0,
                     voice=fv.pool(fv.INDIAN, "female", "adult")[0].id, language="te", emotion="gentle", settings={})
    _ok, notes = fv.synth([seg])
    return seg, notes, attempts


print("A Telugu line the model can't do is read without a language hint (not dropped)")
seg, notes, attempts = run({"te"})
check("the line still renders (url is set)", bool(seg.url), (seg.url, attempts))
check("it tried WITH the language first, then WITHOUT", attempts[:2] == ["te", "(none)"], attempts)
check("a note explains the fallback", any("does not support 'te'" in n for n in notes), notes)

print("A supported-language line is unaffected (renders on the first try, no fallback note)")
seg2, notes2, attempts2 = run(set())   # nothing unsupported
check("renders on the first attempt", bool(seg2.url) and attempts2 == ["te"], attempts2)
check("no fallback note", not any("does not support" in n for n in notes2), notes2)

print()
if fails:
    print(f"{fails} case(s) FAILED")
    sys.exit(1)
print("All voice language-fallback cases behave.")
