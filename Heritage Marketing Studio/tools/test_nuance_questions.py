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

print("Languages: names or codes")
import geo as _geo   # noqa: E402
import pr as _pr     # noqa: E402
expect("the names table holds exactly the studio's thirteen codes", set(_geo.LANGUAGE_NAMES) == set(_geo.language_codes()), set(_geo.LANGUAGE_NAMES) ^ set(_geo.language_codes()))
expect("and agrees with pr.LANGUAGES on every label (one truth, guarded)", all(_pr.LANGUAGES[c]["label"] == n for c, n in _geo.LANGUAGE_NAMES.items()),
       [c for c, n in _geo.LANGUAGE_NAMES.items() if _pr.LANGUAGES.get(c, {}).get("label") != n])
expect("a code, a name, any case and spacing, and an alternative spelling all resolve (exact)",
       [_geo.resolve_language(x) for x in ("te", "Telugu", "  KANNADA ", "Tamil", "english", "Bangla", "Oriya", "Panjabi")] == ["te", "te", "kn", "ta", "en", "bn", "or", "pa"],
       [_geo.resolve_language(x) for x in ("te", "Telugu", "  KANNADA ", "Tamil", "english", "Bangla", "Oriya", "Panjabi")])
expect("anything else resolves to nothing, never a guess", [_geo.resolve_language(x) for x in ("Klingon", "", None, "Hinglish", "tel")] == ["", "", "", "", ""])
lb = bp.put({"name": "Lang Probe", "languages": ["Telugu", "Kannada", "ta", "  Marathi ", "english", "Bangla", "Klingon", "Telugu"]})
expect("typed names are saved as codes, de-duplicated, in the order given", lb["languages"] == ["te", "kn", "ta", "mr", "en", "bn"], lb["languages"])
expect("what is not a language is kept as typed in languages_unresolved, not dropped", lb["languages_unresolved"] == ["Klingon"], lb["languages_unresolved"])
expect("the question says names or codes work, and gives an example", "Names or codes both work" in bp.SPEC_BY_KEY["languages"]["ask"] and "Telugu" in bp.SPEC_BY_KEY["languages"].get("placeholder", ""))

print("Cities in the states box")
expect("a city resolves to its state through resolve_place",
       [_geo.resolve_place(x) for x in ("Mumbai", "Pune", "  noida ", "Gurgaon", "Bengaluru", "Hyderabad", "Kolkata")] == ["mh", "mh", "up", "hr", "ka", "tg", "wb"],
       [_geo.resolve_place(x) for x in ("Mumbai", "Pune", "  noida ", "Gurgaon", "Bengaluru", "Hyderabad", "Kolkata")])
expect("common alternative names resolve too",
       [_geo.resolve_place(x) for x in ("Bangalore", "Gurugram", "Vizag", "Secunderabad", "Navi Mumbai", "Calcutta", "Madras", "Cochin")] == ["ka", "hr", "ap", "tg", "mh", "wb", "tn", "kl"])
expect("a state name, a code, 'Delhi NCR' and an old state name still resolve as states",
       [_geo.resolve_place(x) for x in ("Karnataka", "tn", "Delhi NCR", "Orissa")] == ["ka", "tn", "dl", "or"], [_geo.resolve_place(x) for x in ("Karnataka", "tn", "Delhi NCR", "Orissa")])
expect("an unknown place resolves to nothing, never a guess", [_geo.resolve_place(x) for x in ("Atlantis", "", None, "Mumbaii")] == ["", "", "", ""])
expect("resolve_state ITSELF is unchanged: a city is still 'not a state' there (the social plan relies on that)", _geo.resolve_state("Mumbai") == "" and _geo.resolve_state("Pune") == "")
expect("every alias target is a real state", all(v in _geo.STATES for v in _geo._CITY_ALIASES.values()), [k for k, v in _geo._CITY_ALIASES.items() if v not in _geo.STATES])
_seed0 = _geo._SEED
_geo._SEED = list(_seed0) + [("Aurangabad", "mh", 1), ("Aurangabad", "br", 1)]
expect("a city name that belongs to two states resolves to nothing rather than to one of them", _geo.city_state("Aurangabad") == "", _geo.city_state("Aurangabad"))
_geo._SEED = _seed0
sb = bp.put({"name": "Cities Probe", "states": ["Mumbai", "Pune", "Delhi NCR", "Karnataka", "tn", "Gurugram", "Atlantis"]})
expect("the states box saves cities as their state, once each, and keeps what it could not place", sb["states"] == ["mh", "dl", "ka", "tn", "hr"] and sb["states_unresolved"] == ["Atlantis"], (sb["states"], sb["states_unresolved"]))
expect("the question says a big city stands for its state", "city stands for its state" in bp.SPEC_BY_KEY["states"]["ask"])

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

# (Step 1 also pinned "voice_block ignores the new answers". From Step 2 the answers ARE consumed; that is
# pinned in tools/test_nuance_prompt_lines.py, and an unanswered brand's prompts by tools/golden_prompts.py.)

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All nuance-question cases behave.")
