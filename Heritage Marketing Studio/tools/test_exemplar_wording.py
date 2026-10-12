#!/usr/bin/env python
"""test_exemplar_wording.py -- the teaching examples in the idea, campaign, Brief and Plan-channels prompts are not dairy or Heritage (Step 5, Surface 2).

Surface 2 swapped the examples the model is shown: the campaign shapes (Heritage's own tagline, a dairy mascot, a farm act), the idea skill's
worked mechanic (a dairy), the Brief's output-format examples and its worked backgrounder example (Heritage Foods, dairy), and the Plan channel
example ("Telugu"). Each is now an example from another category, and says so. Nothing else changed.

What this proves (no model is called, scratch data only). It runs the golden capture, so the prompts are the real ones:
  - for a cement, beauty, apparel and biscuit brand, the idea-platform, campaign, Brief and Plan-channels prompts carry no dairy word, no
    "ki Shakti", no Telugu, and none of the dairy competitors the old examples named;
  - the structure those examples taught is still there: all four campaign shapes, the idea skill's mechanic and its five-media line, the Brief's
    worked example with its "notice what it does NOT do" lesson, the channel rule with its example;
  - every example now says it is from another category;
  - Heritage's own stored data and answers are not touched (Heritage's voice block still carries its dairy specifics: the golden compare shows
    voice_block and every producer prompt unchanged).

    python tools/test_exemplar_wording.py          # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = tempfile.mkdtemp(prefix="exemplar_wording_")
r = subprocess.run([sys.executable, os.path.join(HERE, "golden_prompts.py"), "--save", OUT], capture_output=True, text=True, env={**os.environ, "PYTHONUTF8": "1"})
if r.returncode != 0:
    print(r.stdout[-800:], r.stderr[-800:])
    sys.exit("the golden capture failed, so nothing was checked")

failures = 0


def expect(label, cond, detail=""):
    global failures
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  -> {str(detail)[:300]}"))
    if not cond:
        failures += 1


def prompt(brand, surface):
    return open(os.path.join(OUT, brand, surface + ".txt"), encoding="utf-8").read()


SURFACES = ("idea_platform_draft", "campaign_draft", "brief_draft", "plan_channels")
DAIRY = re.compile(r"milk|dairy|doodh|curd|paneer|ghee|ki shakti|telugu|hatsun|arokya|nandini|amul|meet your farmer|topical girl", re.I)

print("A cement, beauty, apparel and biscuit brand's prompts carry no dairy example")
for brand in ("sthir-cement", "kumkum-beauty", "loomwell", "parle-g"):
    for s in SURFACES:
        t = prompt(brand, s)
        m = DAIRY.search(t)
        expect(f"{brand} / {s}: no dairy or Heritage example", bool(t) and "(no prompt captured)" not in t and not m, m and t[max(0, m.start() - 90):m.end() + 60])

print("The structure the examples taught is still there (all five brands)")
for brand in ("sthir-cement", "kumkum-beauty", "loomwell", "parle-g", "heritage-foods"):
    c = prompt(brand, "campaign_draft")
    expect(f"{brand}: all four campaign shapes are listed", all(f"{k} — " in c for k in ("frame", "device", "rule", "act")), c[c.find("The four shapes"):][:200])
    expect(f"{brand}: the campaign examples say they are from another category", c.count("from another category") == 3, c.count("from another category"))
    i = prompt(brand, "idea_platform_draft")
    expect(f"{brand}: the idea skill keeps its mechanic example and the five-media line", "Every shirt carries the name of the mill that wove it" in i and "Same idea, five media" in i and "take the structure, not the words" in i)
    b = prompt(brand, "brief_draft")
    expect(f"{brand}: the Brief keeps its worked example and its lesson, labelled as another category",
           "Worked example (an invented pressure-cooker brand" in b and "another category from yours" in b and "does NOT do" in b and "Problem statement:" in b)
    expect(f"{brand}: the Brief's output contract names the fields without examples",
           "the platform name, in the brand's own words" in b and "where the buyer's attitude sits today, in plain words" in b)
    p = prompt(brand, "plan_channels")
    expect(f"{brand}: the channel rule keeps its example", "'15s vertical reel, in the audience language'" in p, p[p.find("vertical reel") - 40:][:120])

print("Heritage keeps its own specifics")
hv = prompt("heritage-foods", "voice_block")
expect("Heritage's voice block still carries its dairy and place specifics", bool(re.search(r"milk|dairy", hv, re.I)) and "Telangana" in hv, hv[:200])

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All exemplar-wording cases behave.")
