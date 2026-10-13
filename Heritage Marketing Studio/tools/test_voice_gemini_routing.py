#!/usr/bin/env python
"""test_voice_gemini_routing.py -- Gemini is the default voice engine for every non-child speaker in every
language; ElevenLabs is kept only for child voices (and stays resolvable for old saved films).

Owner call (13 Oct): "keep all voices from Google Flash and not use ElevenLabs at all ... Google is far
superior", then "keep ElevenLabs for child". So: a genuine child is cast to an ElevenLabs child voice
(Gemini has none); every other speaker -- narration, adult, elder, any language -- is cast to a Google
voice and synthesised by Gemini TTS. Child/elderly age range is Gemini's known weak spot, accepted here.

    python tools/test_voice_gemini_routing.py       # exit 0 = behaves
"""
from __future__ import annotations
import os, sys, tempfile
os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="vgem_")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

import filmvoice as fv       # noqa: E402
import filmaudio            # noqa: E402
import gemini               # noqa: E402

assert fv.__file__.replace("\\", "/").endswith("/api/filmvoice.py"), fv.__file__

fails = 0


def check(name, cond, detail=""):
    global fails
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  -> {detail}"))
    fails += 0 if cond else 1


def prov(vid):
    v = fv.resolve(vid)
    return v.provider if v else None


print("The Google roster is gender-balanced and all banded 'adult' (no elderly/child on Gemini)")
g = [v for v in fv.VOICES if v.provider == "gemini"]
check("16 Google voices", len(g) == 16, len(g))
check("8 female / 8 male", sum(v.gender == "female" for v in g) == 8 and sum(v.gender == "male" for v in g) == 8)
check("all banded adult", all(v.age == "adult" for v in g), set(v.age for v in g))
check("the three gender-disputed voices were dropped",
      not any(v.ref in ("Orus", "Vindemiatrix", "Pulcherrima") for v in g))
check("voice_catalog still lists a Google group", any(r["group"].startswith("Google") for r in fv.voice_catalog()))
check("ElevenLabs child voices are still present (for child roles)",
      any(v.provider == "elevenlabs" and v.age == "young" for v in fv.VOICES))

print("\nEngine policy: child -> ElevenLabs, everyone else -> Google")
check("young band -> ElevenLabs child", all(p == "elevenlabs" for p in map(lambda v: v.provider, fv._engine_pool(fv.INDIAN, "female", "young"))))
check("adult band -> Google", fv._engine_pool(fv.INDIAN, "female", "adult")[0].provider == "gemini")
check("mature band widens to a Google voice", fv._engine_pool(fv.INDIAN, "male", "mature")[0].provider == "gemini")

print("\nCasting: adult speakers (any language) -> Google; a child -> ElevenLabs")
segs = [
    fv.Segment(kind="vo", text="Fresh every morning.", language="en"),
    fv.Segment(kind="dialogue", speaker="Mother", text="Taaza undi, raa.", language="te"),
    fv.Segment(kind="dialogue", speaker="Shopkeeper", text="Best in town.", language="en"),
    fv.Segment(kind="dialogue", speaker="Girl", text="Ammi, I want milk!", language="en"),
]
fv.cast(segs, "", "en", characters="Mother (30s, warm); Shopkeeper (male, 40s); Girl (small child, 6)")
by = {s.speaker or "VO": s.voice for s in segs}
check("Mother (Telugu, adult) -> Google", prov(by["Mother"]) == "gemini", by["Mother"])
check("Shopkeeper (English, adult) -> Google", prov(by["Shopkeeper"]) == "gemini", by["Shopkeeper"])
check("Girl (child) -> ElevenLabs child voice", prov(by["Girl"]) == "elevenlabs" and (fv.resolve(by["Girl"]).age == "young"), by["Girl"])
check("Narration default -> Google", prov(by["VO"]) == "gemini", by["VO"])


print("\nSynth dispatch: Google-cast -> Gemini; child/EL-cast -> fal; Gemini failure -> fal")

def run(seg, gemini_returns="/media/vo-x.wav"):
    called = {"gemini": 0, "fal": 0}
    gemini.tts = lambda text, voice, style="": (called.__setitem__("gemini", called["gemini"] + 1) or gemini_returns)
    gemini.available = lambda: True
    filmaudio.run_fal = lambda model, args: (called.__setitem__("fal", called["fal"] + 1) or "https://x/el.mp3")
    fv.synth([seg])
    return called

# adult line cast to a Google voice -> Gemini
c = run(fv.Segment(kind="dialogue", speaker="Mother", text="Taaza undi, raa.", language="te", voice="ga-f-kore", settings={}))
check("Google-cast Telugu line -> gemini.tts, not fal", c["gemini"] == 1 and c["fal"] == 0, c)

c = run(fv.Segment(kind="vo", text="Pure and simple.", language="en", voice="ga-m-charon", settings={}))
check("Google-cast English line -> gemini.tts, not fal", c["gemini"] == 1 and c["fal"] == 0, c)

# a child line (ElevenLabs child voice) stays on fal EVEN in Telugu -- owner wants EL for child
c = run(fv.Segment(kind="dialogue", speaker="Girl", text="Taaza undi, raa.", language="te", voice="in-g-gudiya", settings={}))
check("child (ElevenLabs) Telugu line -> fal, not gemini", c["fal"] >= 1 and c["gemini"] == 0, c)

# an explicit ElevenLabs adult pick stays on fal (explicit choice beats the default engine)
c = run(fv.Segment(kind="vo", text="Hello there.", language="en", voice="in-f-riya", settings={}))
check("explicit ElevenLabs pick -> fal, not gemini", c["fal"] >= 1 and c["gemini"] == 0, c)

# Gemini failure falls through to fal
c = run(fv.Segment(kind="dialogue", speaker="Mother", text="Taaza undi, raa.", language="te", voice="ga-f-kore", settings={}), gemini_returns=None)
check("Gemini failure falls through to fal", c["gemini"] == 1 and c["fal"] >= 1, c)

print()
if fails:
    print(f"{fails} case(s) FAILED")
    sys.exit(1)
print("All Gemini-first routing cases behave.")
