#!/usr/bin/env python
"""test_voice_chirp_routing.py -- the film voice engine is chosen by language+age:
Telugu/Indic -> Cloud Chirp 3 HD (native), English/Hindi/Tamil -> ElevenLabs Indian voices (Indian accent,
which Chirp's English lacks), child -> ElevenLabs child voices.

History (14 Oct): the owner's ear chose Cloud Chirp 3 HD for Telugu. The 13 Oct interim had made Gemini the
default for ALL non-child voices including English -- but Gemini/Chirp speak English without an Indian accent,
so a real film's English narration sounded foreign and the Telugu lines were stuck on ElevenLabs (which can't
do Telugu). This pins the corrected, language-gated policy.

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


print("Roster: Chirp voices for Indic, ElevenLabs Indian + child kept; no Gemini left")
ch = [v for v in fv.VOICES if v.provider == "chirp"]
check("16 Chirp voices", len(ch) == 16, len(ch))
check("8 female / 8 male", sum(v.gender == "female" for v in ch) == 8 and sum(v.gender == "male" for v in ch) == 8)
check("all banded adult", all(v.age == "adult" for v in ch), set(v.age for v in ch))
check("Orus is male (API-correct), Vindemiatrix dropped", any(v.ref == "Orus" and v.gender == "male" for v in ch) and not any(v.ref == "Vindemiatrix" for v in ch))
check("no Gemini voices remain", not any(v.provider == "gemini" for v in fv.VOICES))
check("ElevenLabs Indian adults present (for English)", any(v.provider == "elevenlabs" and v.accent == fv.INDIAN and v.age == "adult" for v in fv.VOICES))
check("ElevenLabs child voices present", any(v.provider == "elevenlabs" and v.age == "young" for v in fv.VOICES))

print("\nLanguage classification")
for lang, want in [("te", True), ("Telugu", True), ("te-IN", True), ("kn", True), ("mr", True), ("ur", True),
                   ("hi", False), ("ta", False), ("en", False), ("or", False), ("as", False), ("", False), (None, False)]:
    check(f"_wants_chirp({lang!r}) == {want}", fv._wants_chirp(lang) == want, fv._wants_chirp(lang))

print("\nEngine pool by language + age")
check("Telugu adult -> Chirp", fv._engine_pool(fv.INDIAN, "female", "adult", "te")[0].provider == "chirp")
check("English adult -> ElevenLabs Indian", fv._engine_pool(fv.INDIAN, "female", "adult", "en")[0].provider == "elevenlabs")
check("Hindi adult -> ElevenLabs", fv._engine_pool(fv.INDIAN, "male", "adult", "hi")[0].provider == "elevenlabs")
check("Telugu mature widens to a Chirp voice", fv._engine_pool(fv.INDIAN, "male", "mature", "mr")[0].provider == "chirp")
check("child (any language) -> ElevenLabs child", all(p == "elevenlabs" for p in map(lambda v: v.provider, fv._engine_pool(fv.INDIAN, "female", "young", "te"))))

print("\nCasting a mixed-language film")
segs = [
    fv.Segment(kind="vo", text="We didn't ask you to trust our seal.", language="en"),
    fv.Segment(kind="dialogue", speaker="Mother", text="Roju doodh, roju shakti.", language="te"),
    fv.Segment(kind="dialogue", speaker="Shopkeeper", text="Best in town.", language="en"),
    fv.Segment(kind="dialogue", speaker="Girl", text="Teesko aunty.", language="te"),
]
fv.cast(segs, "", "en", characters="Mother (30s, warm); Shopkeeper (male, 40s); Girl (small child, 6)")
by = {s.speaker or "VO": s.voice for s in segs}
check("Narration (English) -> ElevenLabs Indian", prov(by["VO"]) == "elevenlabs", (by["VO"], prov(by["VO"])))
check("Mother (Telugu, adult) -> Chirp", prov(by["Mother"]) == "chirp", (by["Mother"], prov(by["Mother"])))
check("Shopkeeper (English, adult) -> ElevenLabs", prov(by["Shopkeeper"]) == "elevenlabs", (by["Shopkeeper"], prov(by["Shopkeeper"])))
check("Girl (child, even in Telugu) -> ElevenLabs child", prov(by["Girl"]) == "elevenlabs" and fv.resolve(by["Girl"]).age == "young", (by["Girl"], prov(by["Girl"])))

print("\nSynth dispatch: Chirp-cast -> Cloud TTS; everyone else -> fal; Chirp failure -> fal")

def run(seg, chirp_returns="/media/vo-x.mp3"):
    called = {"chirp": 0, "fal": 0}
    cloudtts.synth = lambda text, short, lang: (called.__setitem__("chirp", called["chirp"] + 1) or chirp_returns)
    cloudtts.available = lambda: True
    filmaudio.run_fal = lambda model, args: (called.__setitem__("fal", called["fal"] + 1) or "https://x/el.mp3")
    fv.synth([seg])
    return called

c = run(fv.Segment(kind="dialogue", speaker="Mother", text="Roju doodh, roju shakti.", language="te", voice="ch-f-achernar", settings={}))
check("Chirp-cast Telugu line -> cloudtts.synth, not fal", c["chirp"] == 1 and c["fal"] == 0, c)

c = run(fv.Segment(kind="vo", text="We didn't ask you to trust our seal.", language="en", voice="in-f-riya", settings={}))
check("English line on an ElevenLabs voice -> fal, not Chirp", c["fal"] == 1 and c["chirp"] == 0, c)

c = run(fv.Segment(kind="dialogue", speaker="Girl", text="Teesko aunty.", language="te", voice="in-g-gudiya", settings={}))
check("child (ElevenLabs) Telugu line -> fal, not Chirp", c["fal"] >= 1 and c["chirp"] == 0, c)

c = run(fv.Segment(kind="dialogue", speaker="Mother", text="Roju doodh.", language="te", voice="ch-f-achernar", settings={}), chirp_returns=None)
check("Chirp failure falls through to fal", c["chirp"] == 1 and c["fal"] >= 1, c)

print()
if fails:
    print(f"{fails} case(s) FAILED")
    sys.exit(1)
print("All Chirp-routing cases behave.")
