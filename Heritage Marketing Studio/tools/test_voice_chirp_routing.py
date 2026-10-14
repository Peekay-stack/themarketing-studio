#!/usr/bin/env python
"""test_voice_chirp_routing.py -- the film voice engine is chosen by language + age:

  adult, any Chirp language (English en-IN included) -> Cloud Chirp 3 HD
  child, any language                                -> ElevenLabs child voices (Chirp has none)
  elderly English/Hindi/Tamil                        -> ElevenLabs aged voices (Chirp has no aged voice)
  elderly Telugu/other Indic                         -> Chirp adult (no aged option there)
  Odia/Assamese (no Chirp)                           -> ElevenLabs / fal fallback

History (14 Oct): the owner's ear chose Cloud Chirp 3 HD. en-IN turned out to HAVE Chirp 3 HD voices
(Indian-accented English), which the owner judged good -- so English moved to Chirp too, leaving ElevenLabs
only for what Chirp has no voice for (children, and aged voices in the languages ElevenLabs reads).

    python tools/test_voice_chirp_routing.py       # exit 0 = behaves
"""
from __future__ import annotations
import os, sys, tempfile
os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="vchirp_")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

import filmvoice as fv       # noqa: E402
import filmaudio            # noqa: E402
import cloudtts             # noqa: E402

assert fv.__file__.replace("\\", "/").endswith("/api/filmvoice.py"), fv.__file__

fails = 0


def check(name, cond, detail=""):
    global fails
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  -> {detail}"))
    fails += 0 if cond else 1


def prov(vid):
    v = fv.resolve(vid)
    return v.provider if v else None


print("Roster: Chirp voices + ElevenLabs Indian/child/aged kept; no Gemini")
ch = [v for v in fv.VOICES if v.provider == "chirp"]
check("16 Chirp voices, 8F/8M, all adult", len(ch) == 16 and sum(v.gender == "female" for v in ch) == 8 and all(v.age == "adult" for v in ch))
check("no Gemini voices remain", not any(v.provider == "gemini" for v in fv.VOICES))
check("ElevenLabs child voices present", any(v.provider == "elevenlabs" and v.age == "young" for v in fv.VOICES))
check("ElevenLabs aged (mature) voices present", any(v.provider == "elevenlabs" and v.accent == fv.INDIAN and v.age == "mature" for v in fv.VOICES))
check("en-IN is supported by cloudtts", cloudtts.supports("en") and cloudtts.supports("te"))

print("\nLanguage classification (English is now a Chirp language)")
for lang, want in [("en", True), ("te", True), ("hi", True), ("ta", True), ("kn", True), ("ur", True),
                   ("or", False), ("as", False), ("", False), (None, False)]:
    check(f"_wants_chirp({lang!r}) == {want}", fv._wants_chirp(lang) == want, fv._wants_chirp(lang))

print("\nEngine pool by language + age")
for lang, age, exp in [("en", "adult", "chirp"), ("te", "adult", "chirp"), ("hi", "adult", "chirp"),
                       ("en", "young", "elevenlabs"), ("te", "young", "elevenlabs"),
                       ("en", "mature", "elevenlabs"), ("hi", "mature", "elevenlabs"),
                       ("te", "mature", "chirp"), ("or", "adult", "elevenlabs")]:
    got = fv._engine_pool(fv.INDIAN, "female", age, lang)[0].provider
    check(f"{lang} {age} -> {exp}", got == exp, got)

print("\nCasting a mixed film: English narration -> Chirp now; Telugu -> Chirp; child -> EL; elder EN -> EL")
segs = [
    fv.Segment(kind="vo", text="We didn't ask you to trust our seal.", language="en"),
    fv.Segment(kind="dialogue", speaker="Mother", text="Roju doodh, roju shakti.", language="te"),
    fv.Segment(kind="dialogue", speaker="Girl", text="Teesko aunty.", language="te"),
    fv.Segment(kind="dialogue", speaker="Grandmother", text="Beta, idhar aao.", language="en"),
]
fv.cast(segs, "", "en", characters="Mother (30s, warm); Girl (small child, 6); Grandmother (elderly, 70s)")
by = {s.speaker or "VO": s.voice for s in segs}
check("Narration (English) -> Chirp", prov(by["VO"]) == "chirp", (by["VO"], prov(by["VO"])))
check("Mother (Telugu, adult) -> Chirp", prov(by["Mother"]) == "chirp", (by["Mother"], prov(by["Mother"])))
check("Girl (child) -> ElevenLabs child", prov(by["Girl"]) == "elevenlabs" and fv.resolve(by["Girl"]).age == "young", (by["Girl"], prov(by["Girl"])))
check("Grandmother (elderly English) -> ElevenLabs aged", prov(by["Grandmother"]) == "elevenlabs" and fv.resolve(by["Grandmother"]).age == "mature", (by["Grandmother"], prov(by["Grandmother"])))

print("\nSynth dispatch: Chirp-cast (any language) -> Cloud TTS; EL-cast -> fal; Chirp failure -> fal")

def run(seg, chirp_returns="/media/vo-x.mp3"):
    called = {"chirp": 0, "fal": 0}
    cloudtts.synth = lambda text, short, lang: (called.__setitem__("chirp", called["chirp"] + 1) or chirp_returns)
    cloudtts.available = lambda: True
    filmaudio.run_fal = lambda model, args: (called.__setitem__("fal", called["fal"] + 1) or "https://x/el.mp3")
    fv.synth([seg])
    return called

c = run(fv.Segment(kind="vo", text="We didn't ask you to trust our seal.", language="en", voice="ch-f-achernar", settings={}))
check("Chirp-cast English line -> cloudtts.synth, not fal", c["chirp"] == 1 and c["fal"] == 0, c)

c = run(fv.Segment(kind="dialogue", speaker="Mother", text="Roju doodh.", language="te", voice="ch-f-kore", settings={}))
check("Chirp-cast Telugu line -> cloudtts.synth, not fal", c["chirp"] == 1 and c["fal"] == 0, c)

c = run(fv.Segment(kind="dialogue", speaker="Girl", text="Teesko aunty.", language="te", voice="in-g-gudiya", settings={}))
check("child (ElevenLabs) line -> fal, not Chirp", c["fal"] >= 1 and c["chirp"] == 0, c)

c = run(fv.Segment(kind="vo", text="We didn't ask.", language="en", voice="ch-f-achernar", settings={}), chirp_returns=None)
check("Chirp failure falls through to fal", c["chirp"] == 1 and c["fal"] >= 1, c)

print("\nDirect ElevenLabs path: built but DORMANT, activatable by a voice row + the key")
import ellabs  # noqa: E402
check("no voice uses provider el-direct (dormant)", not any(v.provider == "el-direct" for v in fv.VOICES))
check("ellabs.available() is False without ELEVENLABS_API_KEY", not ellabs.available())
# register a temporary el-direct voice (as a future clone would be) to prove activation needs no code change
fv.VOICES.append(fv.Voice("el-brand", "Brand clone (direct EL)", "el-direct", "voiceid123", fv.INDIAN, "female", "adult"))
fv._BY_ID["el-brand"] = fv.VOICES[-1]


def run_el(seg, el_available=True):
    called = {"el": 0, "fal": 0}
    ellabs.synth = lambda text, voice, **kw: (called.__setitem__("el", called["el"] + 1) or "/media/vo-el.mp3")
    ellabs.available = lambda: el_available
    filmaudio.run_fal = lambda model, args: (called.__setitem__("fal", called["fal"] + 1) or "https://x/el.mp3")
    fv.synth([seg])
    return called

c = run_el(fv.Segment(kind="vo", text="Hello from the brand.", language="en", voice="el-brand", settings={}))
check("an el-direct voice + key -> ellabs.synth, not fal", c["el"] == 1 and c["fal"] == 0, c)
c = run_el(fv.Segment(kind="vo", text="Hello.", language="en", voice="el-brand", settings={}), el_available=False)
check("el-direct with key OFF -> falls through to fal (graceful/dormant)", c["el"] == 0 and c["fal"] >= 1, c)

print()
if fails:
    print(f"{fails} case(s) FAILED")
    sys.exit(1)
print("All Chirp-routing cases behave.")
