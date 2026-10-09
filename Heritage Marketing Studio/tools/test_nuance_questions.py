#!/usr/bin/env python
"""test_nuance_questions.py -- the profile questions added for the nuance layer (NUANCE_LAYER_PLAN.md, Step 1).

What it proves: the new questions are stored and returned like every other profile field, are grouped and
counted, leave `CORE` and every existing brand's completeness alone, and (in Step 1) change no prompt text.
It uses a scratch data directory, calls no model and touches no real data.

    python tools/test_nuance_questions.py          # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="nuanceq_")
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

import brandprofile as bp  # noqa: E402

failures = 0


def expect(label, cond, detail=""):
    global failures
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  -> {detail}"))
    if not cond:
        failures += 1


NEW_FIELDS = ("product_in_use", "pack_in_scene", "imagery_style", "buying_unit", "worst_case", "language_mix",
              "people_setting", "sound_world")
NEW_LISTS = ("must_show", "meeting_points", "statutory_marks")
NEW_ROWS = {"lines": ["line", "who_uses", "who_decides_pays", "how_bought", "where_sold", "how_used"],
            "routes": ["route", "share_of_sales", "who_buys_there"],
            "trade_terms": ["term", "value", "source"],
            "place_notes": ["state", "how_people_buy_use", "register", "festivals_seasons", "references"],
            "calendar_moments": ["moment", "when", "where_it_matters"]}
NEW_ALL = NEW_FIELDS + NEW_LISTS + tuple(NEW_ROWS)
GROUP_OF = {"product_in_use": "How the product is shown", "must_show": "How the product is shown",
            "pack_in_scene": "How the product is shown", "imagery_style": "How the product is shown",
            "buying_unit": "Who buys it and where it is met", "lines": "Who buys it and where it is met",
            "routes": "Who buys it and where it is met", "meeting_points": "Who buys it and where it is met",
            "trade_terms": "The trade calculators", "statutory_marks": "Proof and marks", "worst_case": "Proof and marks",
            "place_notes": "Geography and language", "language_mix": "Geography and language",
            "calendar_moments": "Occasion-led strategy", "people_setting": "Look and sound", "sound_world": "Look and sound"}

print("The spec")
keys = [s["key"] for s in bp.SPEC]
expect("spec keys are unique", len(keys) == len(set(keys)))
expect("all 16 new questions are in the spec", all(k in bp.SPEC_BY_KEY for k in NEW_ALL), str([k for k in NEW_ALL if k not in bp.SPEC_BY_KEY]))
_storable = set(bp.FIELDS) | set(bp.LIST_FIELDS) | set(bp.ROW_FIELDS)
expect("every question can be stored (no question without a storage list)", set(keys) <= _storable, str(set(keys) - _storable))
expect("every new storable field has a question (no storage without a question)",
       set(NEW_ALL) <= set(keys) and all(k in _storable for k in NEW_ALL))
expect("none of the new questions is required, so CORE is unchanged",
       bp.CORE == ("name", "category", "category_axis", "claims", "channels"), str(bp.CORE))
expect("every new question has an ask, a why and a group", all(bp.SPEC_BY_KEY[k].get("ask") and bp.SPEC_BY_KEY[k].get("why") and bp.SPEC_BY_KEY[k].get("unlocks") for k in NEW_ALL))
expect("kinds match the storage lists",
       all(bp.SPEC_BY_KEY[k]["kind"] in ("text", "textarea", "choice") for k in NEW_FIELDS)
       and all(bp.SPEC_BY_KEY[k]["kind"] == "list" for k in NEW_LISTS)
       and all(bp.SPEC_BY_KEY[k]["kind"] == "rows" and bp.SPEC_BY_KEY[k]["cols"] == c for k, c in NEW_ROWS.items()))
expect("choice questions carry options", all(bp.SPEC_BY_KEY[k].get("options") for k in ("pack_in_scene", "buying_unit")))
group_names = {g["name"] for g in bp.SETUP_GROUPS}
expect("every new question's group exists", all(GROUP_OF[k] == bp.SPEC_BY_KEY[k]["unlocks"] and GROUP_OF[k] in group_names for k in NEW_ALL),
       str([k for k in NEW_ALL if bp.SPEC_BY_KEY[k]["unlocks"] not in group_names]))

print("Storing and reading back")
answers = {"name": "Probe Brand", "category": "Cement — bagged trade cement",
           "product_in_use": "mixed on site and laid by a mason", "pack_in_scene": "only when it is in use",
           "imagery_style": "documentary, on site", "buying_unit": "either", "worst_case": "a failed strength test",
           "language_mix": "Hindi and English", "people_setting": "a mason on a half-built wall", "sound_world": "plain and direct",
           "must_show": ["the stencil facing out", "the bag stacked, not leaning"], "meeting_points": "dealer counter\nbuilding site",
           "statutory_marks": "BIS grade mark, batch and packing date",
           "lines": [{"line": "PPC bag", "who_uses": "mason", "who_decides_pays": "contractor decides, owner pays",
                      "how_bought": "by the bag, on credit", "where_sold": "dealers", "how_used": "mixed on site"}],
           "routes": [{"route": "dealers", "share_of_sales": "70%", "who_buys_there": "contractors"}],
           "trade_terms": [{"term": "dealer margin", "value": "about 6%", "source": "trade interview, 2026"}],
           "place_notes": [{"state": "Bihar", "how_people_buy_use": "bought by the bag for the roof pour", "register": "plain Hindi",
                            "festivals_seasons": "before the monsoon", "references": "the mason's name on the wall"}],
           "calendar_moments": [{"moment": "pre-monsoon build rush", "when": "April to May", "where_it_matters": "the north"}]}
b = bp.put(answers)
back = bp.load(b["id"])
expect("text and choice answers round-trip", all(back[k] == answers[k] for k in NEW_FIELDS if k in answers), str({k: back.get(k) for k in NEW_FIELDS}))
expect("a list sent as an array (what the page sends) keeps a comma inside an item",
       back["must_show"] == ["the stencil facing out", "the bag stacked, not leaning"], str(back["must_show"]))
expect("a list sent as a newline-separated string becomes a list", back["meeting_points"] == ["dealer counter", "building site"], str(back["meeting_points"]))
expect("rows round-trip with every column", all(back[k] == answers[k] for k in NEW_ROWS), str({k: back[k] for k in NEW_ROWS}))
expect("place_notes keeps the state as typed (resolved at read time, not rewritten)", back["place_notes"][0]["state"] == "Bihar")
fresh = bp.put({"name": "Empty Brand"})
expect("a brand saved with none of the new answers gets empty values, not missing keys",
       all(k in fresh for k in NEW_ALL) and all(fresh[k] in ("", []) for k in NEW_ALL))
again = bp.put({"name": "Probe Brand", "worst_case": "a recall"}, b["id"])
expect("saving one question leaves the others alone", again["product_in_use"] == answers["product_in_use"] and again["worst_case"] == "a recall")
junk = bp.put({"name": "Probe Brand", "not_a_question": "x"}, b["id"])
expect("an unknown key is ignored", "not_a_question" not in junk)
rows_blank = bp.put({"name": "Probe Brand", "lines": [{"line": "", "who_uses": ""}]}, b["id"])
expect("a blank row is dropped", rows_blank["lines"] == [])

print("Readiness and groups")
rd = bp.readiness(bp.load(b["id"]))
expect("readiness carries the new questions", all(any(f["key"] == k for f in rd["fields"]) for k in NEW_ALL))
expect("the needed-answers count is unchanged (still the 5 core)", rd["core_total"] == 5, str(rd["core_total"]))
expect("an answered new question counts as set", next(f for f in rd["fields"] if f["key"] == "worst_case")["state"] == "set")
sv = bp.setup_view(bp.load(b["id"]))
by_group = {g["name"]: [f["key"] for f in g["fields"]] for g in sv["groups"]}
expect("each new question appears in its group", all(k in by_group.get(GROUP_OF[k], []) for k in NEW_ALL), str(by_group))
expect("none of the new questions lands in 'Sharpens the work'", not any(k in by_group.get("Sharpens the work", []) for k in NEW_ALL))
expect("the four new groups are present", all(n in by_group for n in ("How the product is shown", "Who buys it and where it is met", "Proof and marks", "Look and sound")))

print("Step 1 guarantee: no prompt changes yet")
base = bp.put({"name": "Twin Brand", "category": "Cement", "market": "India"})
plain = bp.voice_block(base)
twin = bp.voice_block(bp.put({**answers, "name": "Twin Brand", "category": "Cement", "market": "India"}, base["id"]))
expect("voice_block ignores the new answers (they are stored, not consumed, until Step 2)", plain == twin)

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All nuance-question cases behave.")
