#!/usr/bin/env python
"""test_video_agnostic_defaults.py -- Video's built-in defaults carry no dairy, family, premium or Heritage language (Step 5, Surface 3).

Surface 3 removed what the Video side said for EVERY brand: the clip prompt's "Authentic Indian family setting ... premium and wholesome", the shared
still and film styles' "food & lifestyle photography ... fresh milk ... dawn dairy-farm" and "premium", the music prompt's "premium Indian dairy brand
film ... gentle Indian instrumentation", the page's default voice "Warm female (Telugu-accented English)" and its script line "Dialogue in English +
Hinglish where natural". "Indian" as the country stays (the studio is India only). The brand's own answers still reach each of these: the music prompt
gets the brand's sound-world answer, the script prompt points at its language answer, and an empty voice field still casts the narrator it always did.

What this proves (no model is called, scratch data only):
  - no still style or film style names food, milk, dairy, farm, pouring, family, premium or condensation;
  - the music prompt for any style carries no dairy / premium / "Indian instrumentation" tail, ends with the plain tail, and carries the brand's sound
    world (labelled, as instrumentation and mood only) only when it is answered, and never in Independent mode;
  - the clip prompt in main.py no longer says "Authentic Indian family setting";
  - an empty voice field casts the same narrator the old default string did;
  - the page: the production defaults are empty, the script sentence points at LANGUAGE OF THE WORK, that label is the one the server really writes,
    and the provocation rewrite's pattern still matches the sentence (so provocation mode still replaces it).

    python tools/test_video_agnostic_defaults.py          # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import re
import sys
import tempfile

os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="videodefaults_")
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.abspath(os.path.join(HERE, "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

import brandprofile   # noqa: E402
import filmaudio      # noqa: E402
import main           # noqa: E402

failures = 0


def expect(label, cond, detail=""):
    global failures
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  -> {str(detail)[:300]}"))
    if not cond:
        failures += 1


BAD_STYLE = re.compile(r"milk|dairy|farm|food|pour|famil|premium|condensation|appetis|wholesome|pouch|doodh|curd", re.I)

print("The still and film styles name no category, family or premium")
for name, table in (("_IMG_STYLES", main._IMG_STYLES), ("_VID_STYLES", main._VID_STYLES)):
    for k, v in table.items():
        m = BAD_STYLE.search(v)
        expect(f"{name}[{k}]", not m, m and v[max(0, m.start() - 60):m.end() + 40])
expect("the photoreal still still describes the look (lens, depth of field, natural light, real people)",
       all(w in main._IMG_STYLES["real"] for w in ("50mm", "shallow depth of field", "natural light", "real people")))
expect("the country stays: 'Indian' is still in the photoreal still and the 2D animation look",
       "Indian" in main._IMG_STYLES["real"] and "Indian" in main._VID_STYLES["animation-2d"])

print("The music prompt")
TAIL = "Instrumental score for a brand film. No vocals, no lyrics."
for style in ("piano-ambient", "upbeat-modern", "warm-strings", "Calm and unhurried", ""):
    p = filmaudio.music_prompt(style)
    expect(f"style {style or '(none)'!r}: no dairy, premium, wholesome or Indian-instrumentation tail, ends with the plain tail",
           not re.search(r"dairy|premium|wholesome|gentle Indian|Indian instrumentation", p, re.I) and p.endswith(TAIL), p)
SW = "Warm and uplifting. A solo bansuri flute over a soft tanpura drone, no vocals. A warm female voice, Telugu-accented English by default."
p = filmaudio.music_prompt("piano-ambient", SW)
expect("an answered sound world is carried, labelled as instrumentation and mood only", "THE BRAND'S SOUND WORLD (instrumentation and mood only" in p and "bansuri flute" in p, p)
expect("and the plain tail still ends the prompt", p.endswith(TAIL), p[-120:])
expect("unanswered: no sound-world label", "SOUND WORLD" not in filmaudio.music_prompt("piano-ambient", ""))

print("The sound world reaches the music only when it is the brand's own")
real_resolve = main.brandprofile.resolve
try:
    main.brandprofile.resolve = lambda *a, **k: {"name": "X", "sound_world": "Quiet piano"}
    expect("grounded and answered: the answer", main._sound_world({}) == "Quiet piano", main._sound_world({}))
    expect("Independent mode: nothing", main._sound_world({"brand_mode": "general"}) == "")
    main.brandprofile.resolve = lambda *a, **k: {"name": "X"}
    expect("unanswered: nothing", main._sound_world({}) == "")
    main.brandprofile.resolve = lambda *a, **k: None
    expect("no brand: nothing", main._sound_world({}) == "")
finally:
    main.brandprofile.resolve = real_resolve

print("The clip prompt")
src = open(os.path.join(API, "main.py"), encoding="utf-8").read()
expect("main.py no longer says 'Authentic Indian family setting' or 'premium and wholesome'", "Authentic Indian family setting" not in src and "premium and wholesome" not in src)
expect("the clip prompt keeps its no-text and silent-clip rules", "No on-screen captions, subtitles, watermarks or logos. No spoken dialogue and no musicians" in src)

print("An empty voice field casts the narrator the old default string did")
old = main._voice_setup({"scenes": [], "duration": "30s", "voice": "Warm female (Telugu-accented English)"})[1]
new = main._voice_setup({"scenes": [], "duration": "30s", "voice": ""})[1]
expect("same narrator (a warm adult female, not a male voice)", old == new, f"old={old} new={new}")
expect("a typed voice still wins", main._voice_setup({"scenes": [], "duration": "30s", "voice": "a deep male voice"})[1] != new)

print("The page")
html = open(os.path.join(API, "frontend", "app.dc.html"), encoding="utf-8").read()
expect("the production voice defaults are empty, in both places", html.count("voice:'', status:'idle'") == 2 and "voice:'Warm female" not in html, html.count("voice:'', status:'idle'"))
expect("no Telugu-accented default and no Hinglish anywhere in the page", "Telugu-accented" not in html and "Hinglish" not in html)
SENT = "Spoken lines are in the languages given by LANGUAGE OF THE WORK in THE BRAND, where natural; English if it gives none."
expect("the script prompt carries the new language sentence", SENT in html and html.count(SENT) == 1, html.count(SENT))
m = re.search(r"\.replace\(/(The film MUST include a pack-shot sign-off\[\\s\\S\]\*\?[^/]*?none\\\.)/, \(\) =>", html)
expect("the provocation rewrite's pattern is there and ends with the same sentence", bool(m) and SENT.replace(".", r"\.") .rstrip("\\") in (m.group(1) if m else ""), m and m.group(1)[-140:])
if m:
    js = m.group(1).replace(r"[\s\S]*?", "[\\s\\S]*?")
    sample = "The film MUST include a pack-shot sign-off — a scene ... on no other. " + SENT + "\n\nCASTING THE SOUND: ..."
    expect("and it matches the sentence in the script prompt (so provocation mode still rewrites it)", re.search(js, sample) is not None, js[-120:])
nl = brandprofile.nuance_lines({"language_mix": "Telugu in Telangana, English for product terms"}, "creative")
expect("LANGUAGE OF THE WORK is the label the server really writes for the language answer", any(l.startswith("LANGUAGE OF THE WORK:") for l in nl), nl)

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All Video-default cases behave.")
