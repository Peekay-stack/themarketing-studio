#!/usr/bin/env python
"""test_nuance_heritage_checklist.py -- Heritage's reviewed answers carry every dairy-level behaviour (Step 3).

The nuance layer moves what the prompts used to assume about dairy out of the code and into answers the brand
owns. This is the CHECKLIST that makes "nothing was lost for Heritage" checkable: once the answers are
accepted, the prompt says each thing the hardcoded text used to say. Step 5 re-runs it after each hardcoded
rule is removed. It also pins that suggestions alone change no prompt, and how the seed file is read.

Scratch data only; no model is called.

    python tools/test_nuance_heritage_checklist.py          # exit 0 = every case behaves
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import tempfile

os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="nuanceh_")
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.abspath(os.path.join(HERE, "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

import brandprofile as bp   # noqa: E402

failures = 0


def expect(label, cond, detail=""):
    global failures
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  -> {str(detail)[:300]}"))
    if not cond:
        failures += 1


# Heritage as the golden baseline froze it (the dev tenant's profile, copied)
GOLD = os.path.join(HERE, "golden_pre_nuance")
heritage = None
for f in glob.glob(os.path.join(GOLD, "profiles", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    if d.get("name") == "Heritage Foods":
        heritage = d
assert heritage, "no frozen Heritage Foods profile in tools/golden_pre_nuance/profiles"
bp.save(heritage)
_ID = re.compile(r"\b[0-9a-f]{10}\b")

print("Suggestions alone change nothing")
before = bp.voice_block(bp.load(heritage["id"]))
golden_voice = open(os.path.join(GOLD, "heritage-foods", "voice_block.txt"), encoding="utf-8", newline="").read().replace("\r\n", "\n")
expect("before accepting, the voice block is byte-identical to the frozen baseline", _ID.sub("<id>", before) == golden_voice)
seed = bp.seed_answers(heritage)
rd = {f["key"]: f for f in bp.readiness(heritage)["fields"]}
expect("Heritage is offered 15 suggested answers (product lines deliberately left empty)", len(seed) == 15 and "lines" not in seed, sorted(seed))
expect("each offered answer is a suggestion with its source named", all(rd[k]["state"] == "derivable" and rd[k].get("suggestion_from") for k in seed))

print("The seed file's rules")
expect("a brand with no file gets nothing", bp.seed_answers({"name": "Sthir Cement"}) == {} and bp.seed_answers({"name": ""}) == {} and bp.seed_answers(None) == {})
expect("notes in the file (underscore keys) are never offered", not any(k.startswith("_") for k in seed))
expect("the empty share of sales is kept as empty, never invented", all(r["share_of_sales"] == "" for r in seed["routes"]))
done = bp.put({"name": "Heritage Foods", "product_in_use": "my own words"}, heritage["id"])
rd2 = {f["key"]: f for f in bp.readiness(done)["fields"]}
expect("an answer the owner already gave is not re-suggested over", rd2["product_in_use"]["state"] == "set" and rd2["must_show"]["state"] == "derivable")
bp.save(heritage)

print("After the owner accepts and saves, the prompt says what the hardcoded text used to say")
accepted = bp.put({"name": "Heritage Foods", **seed}, heritage["id"])
v = bp.voice_block(accepted)
vf = bp.voice_block(accepted, film=True)
CHECKLIST = [
    ("handled like a small pack, not a hero shot", "carried at the side, handed over, tucked into a crate"),
    ("never held out at arm's length / never a lone centrepiece", "never held out at arm's length toward the camera"),
    ("a glass must show visible milk", "a ring at the base"),
    ("a pour is shown clearly", "milk visibly streaming from the pack's opened corner"),
    ("pack only when it is in use", "PACK IN THE PICTURE: only when it is in use"),
    ("one pack, front label toward the camera", "only one pack in the image"),
    ("food and lifestyle photography look", "full-frame DSLR look"),
    ("bought for a household", "BOUGHT FOR: a household"),
    ("family setting", "authentic family setting"),
    ("warm Indian instrumentation", "bansuri flute"),
    ("Telugu-accented default voice", "Telugu-accented English"),
    ("statutory band: FSSAI licence", "FSSAI licence number"),
    ("statutory band: veg mark", "veg mark"),
    ("the kirana venue", "neighbourhood shop (kirana, general trade)"),
    ("the temple or festival venue", "temple or festival ground"),
    ("language mix: each market in its own principal language (changed 9 Oct from today's 'English + Hinglish', to follow the languages the owner listed)", "Each market in its own principal language"),
    ("place: Telangana", "  - Telangana:"),
    ("place: Andhra Pradesh", "  - Andhra Pradesh:"),
    ("Sankranti as a dated moment", "Sankranti (January; matters in Andhra Pradesh and Telangana)"),
    ("Pongal as a dated moment", "Pongal (January; matters in Tamil Nadu)"),
    ("Diwali gifting window", "Diwali (October to November; matters in a gifting window"),
    ("home delivery and milk booths as a route", "home delivery and subscription (including milk booths)"),
]
for name, phrase in CHECKLIST:
    expect(f"voice says: {name}", phrase.lower() in v.lower(), phrase)
expect("the film voice carries them too", "bansuri flute" in vf and "HOUSE STYLE, SOUND" in vf)
import geo   # noqa: E402
for st in ("Telangana", "Andhra Pradesh", "Karnataka", "Tamil Nadu", "Maharashtra", "Delhi", "Haryana"):
    name = geo.LANGUAGE_NAMES[geo.principal_language_of(geo.resolve_state(st))]
    expect(f"the language mix names {name}, the studio's principal language for {st}", re.search(rf"{name} in [^,)]*{re.escape(st)}", accepted["language_mix"]) is not None, accepted["language_mix"])
expect("the language mix no longer carries the old Hinglish default", "Hinglish" not in accepted["language_mix"])
expect("the hardcoded-text behaviours that live outside the voice are in the answers for PR and the trade sheet",
       "24 hours" in accepted["worst_case"] and "Class I" in accepted["worst_case"]
       and any("25-40%" in r["value"] for r in accepted["trade_terms"]) and all(r["source"] for r in accepted["trade_terms"]))
expect("a suggestion is exactly what accepting it stores (normalised like a save)", all(accepted[k] == seed[k] for k in seed), [k for k in seed if accepted[k] != seed[k]])
lines_before = set(before.split("\n"))
expect("every line the voice had before is still there", lines_before <= set(v.split("\n")), sorted(lines_before - set(v.split("\n")))[:3])

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("Heritage's answers carry every dairy-level behaviour on the checklist.")
