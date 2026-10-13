#!/usr/bin/env python
"""test_voice_gemini_routing.py -- Telugu/Indic lines are voiced by Gemini TTS, English/Hindi stay on the fal voices.

Interim engine (13 Oct): the owner chose a native-Telugu engine; Chirp's credential isn't ready, so Gemini Flash
TTS (on the Gemini API key already in .env) is wired in as the stopgap. A line whose language the fal ElevenLabs
voices can't speak (Telugu + the Indic languages EL multilingual-v2 lacks) is routed to gemini.tts; everything
else is unchanged. This pins: the language set, language-aware casting, the synth dispatch, and graceful fall-through.

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

# Scratchpad-shadow guard (CLAUDE.md): make sure we loaded the REAL modules.
assert fv.__file__.replace("\\", "/").endswith("/api/filmvoice.py"), fv.__file__

fails = 0


def check(name, cond, detail=""):
    global fails
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  -> {detail}"))
    fails += 0 if cond else 1


print("Language classification")
for lang, want in [("te", True), ("Telugu", True), ("te-IN", True), ("kn", True), ("mr", True),
                   ("hi", False), ("ta", False), ("en", False), ("", False), (None, False)]:
    check(f"_wants_gemini({lang!r}) == {want}", fv._wants_gemini(lang) == want, fv._wants_gemini(lang))

print("\nThe roster carries Google voices in both genders across bands")
g = [v for v in fv.VOICES if v.provider == "gemini"]
check("at least 12 Google voices", len(g) >= 12, len(g))
for gender in ("female", "male"):
    for age in ("young", "adult", "mature"):
        check(f"a Google {gender}/{age} exists", any(v.gender == gender and v.age == age for v in g))
check("Google voices don't pollute the Indian (EL) pool",
      all(v.provider != "gemini" for v in fv.pool(fv.INDIAN, "female", "adult")))
check("voice_catalog groups them under Google",
      any(row["group"].startswith("Google") for row in fv.voice_catalog()))


print("\nCasting routes a Telugu character to a Google voice, an English one to a fal voice")
segs = [
    fv.Segment(kind="vo", text="Fresh every morning.", language="en"),
    fv.Segment(kind="dialogue", speaker="Mother", text="Taaza undi, raa.", language="te"),
    fv.Segment(kind="dialogue", speaker="Shopkeeper", text="Best in town.", language="en"),
]
fv.cast(segs, "in-f-riya", "en", characters="Mother (30s, warm); Shopkeeper (male, 40s)")
mother = next(s for s in segs if s.speaker == "Mother")
shop = next(s for s in segs if s.speaker == "Shopkeeper")
check("Mother (Telugu) cast to a Google voice", (fv.resolve(mother.voice) or fv.Voice("", "", "x", "", "", "", "")).provider == "gemini", mother.voice)
check("Shopkeeper (English) stays on ElevenLabs", fv.resolve(shop.voice).provider == "elevenlabs", shop.voice)


print("\nSynth dispatch: Telugu -> Gemini, English -> fal, Gemini-cast -> Gemini, failure -> fal fallback")

def run(seg, gemini_returns="/media/vo-x.wav"):
    """Stub both engines; return (which_engine_called, seg)."""
    called = {"gemini": 0, "fal": 0}
    def fake_tts(text, voice, style=""):
        called["gemini"] += 1
        return gemini_returns
    def fake_fal(model, args):
        called["fal"] += 1
        return "https://x/el.mp3"
    gemini.tts = fake_tts
    gemini.available = lambda: True
    filmaudio.run_fal = fake_fal
    fv.synth([seg])
    return called, seg

# a Telugu line cast (by language) onto an EL voice still goes to Gemini, and the plan now shows the Google voice
te = fv.Segment(kind="dialogue", speaker="Mother", text="Taaza undi, raa.", language="te", voice="in-f-kanika", settings={})
c, _ = run(te)
check("Telugu line -> gemini.tts, not fal", c["gemini"] == 1 and c["fal"] == 0, c)
check("its voice is rewritten to the Google voice actually used", (fv.resolve(te.voice) or None) and fv.resolve(te.voice).provider == "gemini", te.voice)
check("the line rendered (url set)", bool(te.url), te.url)

en = fv.Segment(kind="vo", text="Pure and simple.", language="en", voice="in-f-riya", settings={})
c, _ = run(en)
check("English line -> fal, not gemini", c["fal"] == 1 and c["gemini"] == 0, c)

gc = fv.Segment(kind="dialogue", speaker="Host", text="Welcome.", language="en", voice="ga-f-kore", settings={})
c, _ = run(gc)
check("a line explicitly cast to a Google voice -> gemini even in English", c["gemini"] == 1 and c["fal"] == 0, c)

fb = fv.Segment(kind="dialogue", speaker="Mother", text="Taaza undi, raa.", language="te", voice="in-f-kanika", settings={})
c, _ = run(fb, gemini_returns=None)   # Gemini fails
check("Gemini failure falls through to the fal path", c["gemini"] == 1 and c["fal"] >= 1, c)

print()
if fails:
    print(f"{fails} case(s) FAILED")
    sys.exit(1)
print("All Gemini-routing cases behave.")
