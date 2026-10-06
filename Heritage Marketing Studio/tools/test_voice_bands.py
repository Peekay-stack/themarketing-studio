#!/usr/bin/env python
"""test_voice_bands.py -- which default voice a speaker is cast with, from the cast sheet.

Why: on 5 Oct the cast sheet started labelling versions of one adult "MOTHER (young)" / "MOTHER (older)" (so a frame knows
which version a scene shows). The default voice casting reads the sheet for keywords, and "young" was a child word, so the
mother was cast with a child's voice ("Gudiya - very young girl"). A bare "old" also matched inside "six-year-old", casting a
little boy with a mature adult voice. This pins the bands, with no key, no cost and nothing real touched.

    python tools/test_voice_bands.py       # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
import filmvoice as fv  # noqa: E402

fails = 0


def check(name, got, want):
    global fails
    ok = got == want
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + ("" if ok else f"   got {got!r}, want {want!r}"))


OLD = ("Lead: warm Indian mother, late 20s, shoulder-length hair, mustard kurta; daughter ~7 in a navy school uniform; "
       "grandmother in a white saree. Same faces, same wardrobe in every shot.")
NEW = ("MOTHER (young): mid-30s, slim, dark hair in a low bun, warm wheatish skin, simple sky-blue cotton saree. "
       "MOTHER (older): late-50s version, slight stoop, grey-streaked hair, muted cream-and-rust cotton saree. "
       "BOY (4): tiptoe toddler, small slight build, pale yellow kurta-pyjama. BOY (6): slim, cropped black hair, white-and-navy "
       "school uniform. BOY (10): same features, blue cricket jersey. "
       "By scene: 1 MOTHER (young) + BOY (4); 2 MOTHER (young) + BOY (6); 4 MOTHER (older) + BOY (10)")


def band(sheet, who, emotion=""):
    return fv._band(f"{who} {emotion} {fv._sheet_hint(sheet, who)}")


print("the versioned cast sheet")
check("Mother with 'MOTHER (young)' in the sheet is an ADULT woman, not a child", band(NEW, "Mother", "quiet, amazed"), "female_adult")
check("Boy with 'BOY (4): tiptoe toddler' is a young boy", band(NEW, "Boy", "small, eager"), "male_young")
print("the older cast sheet is unchanged")
check("Mother, old sheet", band(OLD, "Mother"), "female_adult")
check("Boy, no sheet entry", band(OLD, "Boy"), "male_young")
print("ages written in the text")
check("'a six-year-old boy' is not 'old' -> still a young boy", fv._band("Boy a six-year-old boy"), "male_young")
check("'a 4 years old boy' is a child", fv._band("Son a 4 years old"), "male_young")
check("a spelled-out adult age is not 'old'", fv._band("Man a forty-year-old man"), "male_adult")
check("a stated age of 70 is mature", fv._band("Man a 70-year-old man"), "male_mature")
check("'late-50s' reads as mature", fv._band("Mother late-50s version"), "female_mature")
print("a grown man described by who he used to be (6 Oct live test: the Father was cast as 'cute young boy')")
FATHER = ("MOTHER (young, dawn flashback): mother, early 30s, soft slender build, faded floral cotton suit. "
          "BOY (6): sleepy six-year-old, slight build, white cotton vest. "
          "FATHER (grown boy, 30s): same face shape and lean build as the boy, short dark hair, casual cream kurta. "
          "DAUGHTER (4): everyday South Indian girl, small build, pale yellow frock")
check("Father 'grown boy, 30s' is an adult man", band(FATHER, "Father", "quiet, to himself"), "male_adult")
check("the Boy in the same sheet is still a young boy", band(FATHER, "Boy", "sleepy"), "male_young")
check("the Daughter in the same sheet is still a young girl", band(FATHER, "Daughter"), "female_young")
check("the Mother in the same sheet is still an adult woman", band(FATHER, "Mother"), "female_adult")
check("'grown' alone makes a boy an adult", fv._band("Son grown boy"), "male_adult")
check("a stated 30s beats 'son'", fv._band("Son a man in his 30s"), "male_adult")
check("'mid-30s' beats 'boy'", fv._band("Man mid-30s, still the boy at heart"), "male_adult")
check("a 50s man is still mature", fv._band("Father late-50s"), "male_mature")
check("a sheet that says only 'boy' is still a child", fv._band("Boy sleepy boy"), "male_young")
print("plain words")
check("'young woman' is an adult", fv._band("Woman a young woman"), "female_adult")
check("'young father' is an adult", fv._band("Father a young father"), "male_adult")
check("Girl is young", fv._band("Girl"), "female_young")
check("elderly grandmother is mature", fv._band("Grandmother elderly, hushed"), "female_mature")
check("a plain adult speaker stays adult", fv._band("Customer"), "male_adult")

print()
print("All voice-band cases behave." if not fails else f"{fails} voice-band case(s) FAILED.")
sys.exit(1 if fails else 0)
