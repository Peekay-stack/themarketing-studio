#!/usr/bin/env python
"""test_pack_wording.py -- the pack and carousel prompt WORDING carries no dairy (Step 5, Surface 1), and Heritage still gets its specifics.

Surface 1 changed wording only: the Carousel's two milk rules, the two milk phrases in the pack prompts sent to the image model, and the
word "pouch" in the page's Social prompt. It deliberately did NOT touch the pack-DETECTION words (the regexes in packscene.py, main.py and the
page that decide when a real pack photo is attached): changing those changes behaviour for Heritage, and waits for sub-step 1b.

What this proves (no model is called, scratch data only):
  - a cement, beauty, apparel and biscuit brand's real Carousel prompt carries no milk or dairy word;
  - the generic craft rules the milk rules were wrapped around are still there (the hero-shot rule, the fixed pack, the one-line identity);
  - the Carousel now points at the brand's own answers instead of naming milk;
  - Heritage, with its starting answers accepted, still gets the specifics (carried, handed over, tucked into a crate; a visible ring at the base of the glass);
  - the pack prompts sent to the image model say "the product", not milk;
  - the page's Social prompt says "the pack", not "a pouch";
  - the detection words are exactly as they were (so the pack-attachment behaviour is unchanged).

    python tools/test_pack_wording.py          # exit 0 = every case behaves
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import tempfile

os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="packwording_")
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.abspath(os.path.join(HERE, "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

import anthropic              # noqa: E402
import brandprofile as bp     # noqa: E402
import ideas                  # noqa: E402
import jsonout                # noqa: E402
import packscene              # noqa: E402
import producers              # noqa: E402
import strategy               # noqa: E402

failures = 0


def expect(label, cond, detail=""):
    global failures
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  -> {str(detail)[:300]}"))
    if not cond:
        failures += 1


CAP = []
jsonout.ask_json = lambda prompt, *a, **k: (CAP.append(prompt) or (None, "stubbed"))


class _M:
    def create(self, **kw):
        CAP.append((kw.get("system") or "") + "\n\n" + "\n".join(str(m.get("content")) for m in kw.get("messages", [])))
        raise RuntimeError("stubbed")


class _C:
    def __init__(self, *a, **k):
        self.messages = _M()


anthropic.Anthropic = _C
os.environ["ANTHROPIC_API_KEY"] = "never-used"

# the dev brands as the golden baseline froze them
profiles = {}
for f in glob.glob(os.path.join(HERE, "golden_pre_nuance", "profiles", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    profiles[d["name"]] = bp.save(d)


def carousel_prompt(name, answered=False):
    p = bp.load(profiles[name]["id"])
    if answered:
        p = bp.put({"name": name, **bp.seed_answers(p)}, p["id"])
    house = strategy.new_house(name)
    house["nodes"]["core"]["options"] = [{"id": "c1", "text": "core"}]
    house["nodes"]["core"]["chosen"] = ["c1"]
    strategy.save(house)
    pset = ideas.adopt(ideas.new_set(name, house["id"]), {"name": "p", "idea": "i", "mechanic": "m"})
    pf = ideas.chosen_platform(ideas.for_house(house["id"]))
    CAP.clear()
    try:
        producers.carousel_concept("Brand awareness", house, pf)
    except Exception:                                  # noqa: BLE001 -- the stub raises on purpose
        pass
    return "\n".join(CAP)


print("A cement, beauty, apparel and biscuit brand's Carousel carries no dairy")
for name in ("Sthir Cement", "Kumkum Beauty", "Loomwell", "Parle G"):
    t = carousel_prompt(name)
    hit = re.search(r"milk|dairy|doodh|curd", t, re.I)
    expect(f"{name}: no milk or dairy word in the Carousel prompt", bool(t) and not hit, hit and t[max(0, hit.start() - 80):hit.end() + 60])

print("The generic craft rules are still there")
t = carousel_prompt("Sthir Cement")
for label, phrase in (("never a hero shot held out to the camera", "never held out at arm's length toward the camera"),
                      ("never a lone centrepiece", "resting alone as a centrepiece with no one touching it"),
                      ("the pack renders oversized otherwise", "the pack renders oversized"),
                      ("the pack is a fixed product photograph", "a real, fixed product photograph"),
                      ("the time period opens every slide", "EVERY slide's visual_note opens by stating its own time period")):
    expect(f"kept: {label}", phrase in t, phrase)
expect("the Carousel now points at the brand's own answers (HOW IT IS USED OR HANDLED, MUST BE VISIBLE) instead of naming milk",
       "HOW IT IS USED OR HANDLED in THE BRAND" in t and "MUST BE VISIBLE IN ANY IMAGE OF IT" in t)

print("Heritage, with its starting answers accepted, still gets the specifics")
th = carousel_prompt("Heritage Foods", answered=True)
expect("the handling comes from the answer: carried at the side, handed over, tucked into a crate, set down on a counter", "carried at the side, handed over, tucked into a crate, set down on a counter" in th)
expect("the visible-milk rule comes from the answer: a ring at the base, full, half or already drained", "a ring at the base" in th and "already drained" in th)
expect("and the pack-in-picture answer is there", "PACK IN THE PICTURE: only when it is in use" in th)

print("The pack prompts sent to the image model say 'the product'")
side = packscene._PLACEMENT["side"]
expect("the side-placement clause no longer says 'a real pack of milk'", "milk" not in side.lower() and "pack of this kind" in side, side[-260:])
expect("the in-use clause says the product, not milk", "milk" not in packscene.VIDEO_PACK_IN_USE.lower() and "If the scene pours the product" in packscene.VIDEO_PACK_IN_USE, packscene.VIDEO_PACK_IN_USE)
expect("every placement clause is free of milk", all("milk" not in v.lower() for v in packscene._PLACEMENT.values()), [k for k, v in packscene._PLACEMENT.items() if "milk" in v.lower()])

print("The Social prompt in the page")
html = open(os.path.join(API, "frontend", "app.dc.html"), encoding="utf-8").read()
expect("it says 'the pack', not 'a pouch'", 'holding the pack unless "pack" is "in_use"' in html and "holding a pouch unless" not in html)

print("The detection words are exactly as they were (so which scenes get a real pack photo has not changed)")
expect("packscene's pack-noun detector still has its milk alternatives", "milk\\s+bags?" in packscene._PACK_NOUN and "bags?\\s+of\\s+milk" in packscene._PACK_NOUN)
expect("the pour detector still has 'streams of milk'", "streams?\\s+of\\s+milk" in packscene._POUR_OR_OPEN.pattern)
main_src = open(os.path.join(API, "main.py"), encoding="utf-8").read()
expect("scene_still's word lists are unchanged", r'\bglass of milk\b|\blabel\b' in main_src and r'\bmilk bags?\b|\bbags? of milk\b' in main_src)
expect("the page's three detectors are unchanged", html.count(r"milk\s+bags?|bags?\s+of\s+milk") >= 3, html.count(r"milk\s+bags?|bags?\s+of\s+milk"))
sample = {"a pouch of milk is poured": True, "a bag of cement is lifted": False, "a glass of milk on the table": False, "the pack is opened": True}
expect("the pour/open detector gives the answers it always gave on four sample scenes",
       {k: packscene.video_pack_in_use(k) for k in sample} == {"a pouch of milk is poured": True, "a bag of cement is lifted": False, "a glass of milk on the table": False, "the pack is opened": True},
       {k: packscene.video_pack_in_use(k) for k in sample})

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All pack-wording cases behave.")
