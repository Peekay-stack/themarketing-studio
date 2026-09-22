#!/usr/bin/env python
"""test_carousel_concept.py -- the Carousel concept's new `shows_pack` field (Deploy 2, 22 Sep).

Why: the closing (cta) slide of a Carousel always ends up carrying the real product pack, decided by
main.scene_still from slide POSITION (see packscene.py) -- a stored role would go stale the moment a
person reorders or deletes a slide. Every OTHER slide's pack decision instead comes from a narrative
signal the writer supplies per slide: `shows_pack`. This pins that the model's own flag is trusted when
given, and that a slide it left the field off (or one added by hand with `addSlide`, which never goes
through the writer at all) falls back to `posm.looks_like_pack()` on its own visual note -- the same
vocabulary POSM already trusts, not a new one.

No key, no cost: `producers._ask` is stubbed to return canned JSON, so this proves the PARSING contract,
not what a real model would actually decide to write.

    python tools/test_carousel_concept.py     # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import sys

os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import producers  # noqa: E402

failures = 0


def check(label, ok, extra=""):
    global failures
    print(f"  {'ok  ' if ok else 'FAIL'} {label}" + (f"   [{extra}]" if extra else ""))
    if not ok:
        failures += 1


def stub(routes):
    def _ask(prompt, max_tokens=1500):
        check("the prompt tells the model the CTA slide is handled for it",
              "always places the real product pack into the CLOSING (cta) slide" in prompt)
        check("the prompt asks for shows_pack in the return shape",
              '"shows_pack":false' in prompt)
        return {"routes": routes}, ""
    producers._ask = _ask


REAL_ASK = producers._ask

# 1. the model answers shows_pack itself -- trusted as given, no fallback consulted
stub([{"name": "R1", "rationale": "x", "slides": [
    {"role": "hook", "headline": "h", "visual_note": "A calm kitchen morning.", "shows_pack": False},
    {"role": "value", "headline": "h2", "visual_note": "Nothing about the product at all.", "shows_pack": True},
    {"role": "cta", "headline": "h3", "visual_note": "A clean counter.", "shows_pack": False},
]}])
routes, err = producers.carousel_concept("Sell more milk")
check("routes come back", len(routes) == 1 and not err)
slides = routes[0]["slides"]
check("the model's own False is kept even though the words look pack-free", slides[0]["shows_pack"] is False)
check("the model's own True is kept even though the visual note names nothing pack-like",
      slides[1]["shows_pack"] is True)
check("every slide keeps its role/headline/visual_note",
      [s["role"] for s in slides] == ["hook", "value", "cta"] and slides[2]["headline"] == "h3")

# 2. the model omits the field -- posm.looks_like_pack decides
stub([{"name": "R2", "rationale": "x", "slides": [
    {"role": "hook", "headline": "h", "visual_note": "A woman pours milk from a pouch into a glass."},
    {"role": "value", "headline": "h2", "visual_note": "A child laughing at breakfast, nothing else in frame."},
]}])
routes, err = producers.carousel_concept("Sell more milk")
slides = routes[0]["slides"]
check("no shows_pack given, scene names a pouch -> falls back to True", slides[0]["shows_pack"] is True)
check("no shows_pack given, scene names nothing pack-like -> falls back to False",
      slides[1]["shows_pack"] is False)

# 3. shows_pack explicitly false still overrides pack-sounding words (the model's own call wins)
stub([{"name": "R3", "rationale": "x", "slides": [
    {"role": "value", "headline": "h", "visual_note": "A carton sits blurred in the far background.",
     "shows_pack": False},
]}])
routes, err = producers.carousel_concept("Sell more milk")
check("an explicit False is trusted even over pack-sounding words", routes[0]["slides"][0]["shows_pack"] is False)

# 4. a malformed/missing shows_pack (wrong type) still resolves to a real bool via the fallback path
stub([{"name": "R4", "rationale": "x", "slides": [
    {"role": "value", "headline": "h", "visual_note": "A sachet of milk on the table.", "shows_pack": "yes"},
]}])
routes, err = producers.carousel_concept("Sell more milk")
check("a present-but-non-bool field is still coerced through bool(), not crashing",
      routes[0]["slides"][0]["shows_pack"] is True)

producers._ask = REAL_ASK
print()
if failures:
    print(f"{failures} check(s) FAILED")
    sys.exit(1)
print("Carousel concept's shows_pack contract behaves.")
