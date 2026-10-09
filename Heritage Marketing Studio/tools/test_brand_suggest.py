#!/usr/bin/env python
"""test_brand_suggest.py -- the model drafts answers to the nuance questions, and nothing it drafts is stored (Step 4).

Proves, with the model STUBBED (no key, no spend, scratch data only): which questions are asked, that the prompt
carries nothing from another brand or category, that every draft is cleaned the way a save would store it, that a
failure is reported rather than hidden, that nothing is written, and that the route answers as the page expects.
What it cannot prove is how good a real model's drafts are; tools/suggest_report.py is the real-model run.

    python tools/test_brand_suggest.py          # exit 0 = every case behaves
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="suggest_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"

API = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

import main                       # noqa: E402  (loads .env: the key is removed straight after, and the model is stubbed)
os.environ.pop("ANTHROPIC_API_KEY", None)
import brand_suggest as bs        # noqa: E402
import brandprofile as bp         # noqa: E402
import jsonout                    # noqa: E402
import selfcheck                  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

failures = 0


def expect(label, cond, detail=""):
    global failures
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  -> {str(detail)[:300]}"))
    if not cond:
        failures += 1


CALLS = []
REPLY = {"data": None, "err": ""}


def fake_ask(prompt, **kw):
    CALLS.append({"prompt": prompt, **kw})
    return REPLY["data"], REPLY["err"]


jsonout.ask_json = fake_ask
client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})

DAIRY_MARKERS = re.compile(r"\b(milk|dairy|ghee|curd|paneer|heritage|doodh|amul|nandini|fssai|kirana|pouch|sachet|tetra|hinglish|telugu|sankranti|pongal)\b", re.I)

cement = bp.put({"name": "Probe Cement", "category": "Cement — bagged trade cement", "market": "India, semi-urban and rural",
                 "regulator": "BIS", "decider": "the contractor", "payer": "the home owner", "states": ["Bihar", "Jharkhand"],
                 "languages": ["hi", "en"], "channels": ["dealers"], "competitors": ["Rival Cement"]})

print("Which questions are asked")
pk = bs.pending_keys(cement)
expect("a new brand has 15 pending questions (trade_terms is never drafted)", len(pk) == 15 and "trade_terms" not in pk, pk)
expect("an answered question is not asked again", "worst_case" not in bs.pending_keys(bp.put({"name": "Probe Cement", "worst_case": "a failed test"}, cement["id"])))
bp.put({"name": "Probe Cement", "worst_case": ""}, cement["id"])
heritage = bp.put({"name": "Heritage Foods", "category": "Dairy", "states": ["ap", "tg"]})
expect("a question with a reviewed starting answer is not drafted by the model", "product_in_use" not in bs.pending_keys(heritage) and "product_in_use" in bs.pending_keys(heritage, include_seeded=True))
gv = bs.groups_view(cement)
expect("the five groups are offered, in order", [g["name"] for g in gv] == [g["name"] for g in bs.GROUPS], [g["name"] for g in gv])
nostates = bp.put({"name": "No States Brand", "category": "Cement"})
gv2 = {g["name"]: g for g in bs.groups_view(nostates)}
expect("place notes are skipped, with the reason, when no states are listed", "place_notes" in gv2["Place, language and occasions"]["skipped"] and "place_notes" not in gv2["Place, language and occasions"]["keys"])
expect("no brand, no groups", bs.groups_view(None) == [])

print("The prompt")
p = bs.build_prompt(cement, ["product_in_use", "buying_unit", "place_notes"], context="Notes: roofs are poured before the rains.", brief="Target audience: home builders")
expect("it carries the brand's own profile", "Category: Cement — bagged trade cement" in p and "Who pays: the home owner" in p and "States it sells in: Bihar, Jharkhand" in p)
expect("it asks only the questions it was given", '"product_in_use"' in p and '"place_notes"' in p and '"worst_case"' not in p and '"sound_world"' not in p)
expect("it carries the brief and the pasted context", "home builders" in p and "roofs are poured before the rains" in p)
expect("it tells the model a blank beats an invented specific, and never to invent figures or sources", "A blank is useful; an invented specific is harmful" in p and "Never invent figures" in p)
expect("it names the allowed states for place notes", "Bihar; Jharkhand" in p)
expect("a cement brand's prompt carries nothing from dairy, Heritage or any other brand", not DAIRY_MARKERS.search(p), DAIRY_MARKERS.search(p) and p[max(0, DAIRY_MARKERS.search(p).start() - 80):DAIRY_MARKERS.search(p).end() + 60])
placeholders = [s["placeholder"] for s in bp.SPEC if s.get("placeholder") and s["key"] in bp.NUANCE_KEYS]
expect("none of the form's example placeholders is put in the prompt (an example is an example the model copies)", not any(ph.split(" · ")[0] in p for ph in placeholders))
allp = "\n".join(bs.build_prompt(cement, list(g["keys"])) for g in bs.GROUPS)
expect("trade_terms is never in any prompt", "trade_terms" not in allp)
expect("every group's prompt is free of dairy and Heritage markers for a cement brand", not DAIRY_MARKERS.search(allp))
expect("context is clipped to 4000 characters", len(bs.build_prompt(cement, ["sound_world"], context="x" * 9000)) < len(bs.build_prompt(cement, ["sound_world"])) + 4200)

print("Cleaning what the model returns")
REPLY["data"] = {"answers": {
    "product_in_use": {"value": "  mixed on site\nand laid by a mason  ", "basis": "knowledge", "unknowns": ""},
    "buying_unit": {"value": "Either", "basis": "profile", "unknowns": ""},
    "pack_in_scene": {"value": "sometimes", "basis": "profile", "unknowns": ""},
    "must_show": {"value": ["a", "b", "c", "d", "e", "f", "g", "h"], "basis": "weird", "unknowns": ""},
    "routes": {"value": [{"route": "dealers", "share_of_sales": "", "who_buys_there": "contractors"}, {"route": "", "share_of_sales": "5%"}], "basis": "knowledge", "unknowns": ""},
    "place_notes": {"value": [{"state": "Bihar", "how_people_buy_use": "by the bag", "register": "", "festivals_seasons": "", "references": ""},
                              {"state": "Kerala", "how_people_buy_use": "x"}], "basis": "knowledge", "unknowns": ""},
    "worst_case": {"value": "", "basis": "knowledge", "unknowns": "which regulator applies here"},
    "not_a_question": {"value": "x", "basis": "profile", "unknowns": ""},
}}
REPLY["err"] = ""
CALLS.clear()
r = bs.suggest_group(cement, "How the product is shown")
sg = r["suggestions"]
expect("a text answer is collapsed to one line", sg["product_in_use"]["value"] == "mixed on site and laid by a mason", sg.get("product_in_use"))
expect("an unknown choice value is dropped, not invented", "pack_in_scene" not in sg and "pack_in_scene" not in r["unknown"])
expect("a list is capped at six", sg["must_show"]["value"] == ["a", "b", "c", "d", "e", "f"], sg.get("must_show"))
expect("a basis the rules do not know falls back to 'knowledge' (the one that must be confirmed)", sg["must_show"]["basis"] == "knowledge")
expect("only the group's own questions are returned", set(sg) <= {"product_in_use", "must_show", "pack_in_scene", "imagery_style"} and "not_a_question" not in sg and "routes" not in sg, sorted(sg))
expect("the call's token budget scales with the number of questions", CALLS and CALLS[0]["max_tokens"] == 700 + 650 * 4, CALLS and CALLS[0].get("max_tokens"))
REPLY["data"]["answers"]["buying_unit"] = {"value": "Either", "basis": "profile", "unknowns": ""}
r2 = bs.suggest_group(cement, "Who buys it and where it is met")
expect("a choice answer is matched ignoring case", r2["suggestions"]["buying_unit"]["value"] == "either")
expect("a route without a name is dropped", r2["suggestions"]["routes"]["value"] == [{"route": "dealers", "share_of_sales": "", "who_buys_there": "contractors"}], r2["suggestions"].get("routes"))
r3 = bs.suggest_group(cement, "Place, language and occasions")
expect("a place row for a state the brand does not sell in is dropped, and the state is named as the real vocabulary names it",
       [x["state"] for x in r3["suggestions"]["place_notes"]["value"]] == ["Bihar"], r3["suggestions"].get("place_notes"))
r4 = bs.suggest_group(cement, "Proof and marks")
expect("an empty value with a stated unknown is reported as unknown, not as a suggestion", "worst_case" not in r4["suggestions"] and r4["unknown"].get("worst_case") == "which regulator applies here", r4)

print("Failure is reported, nothing else")
REPLY["data"], REPLY["err"] = None, "the reply was cut off"
r5 = bs.suggest_group(cement, "Look and sound")
expect("a failed call returns its reason and no suggestions", r5["error"] == "the reply was cut off" and r5["suggestions"] == {}, r5)
expect("an unknown group is an error, not a silent empty", bs.suggest_group(cement, "Nope")["error"].startswith("unknown group"))
REPLY["data"], REPLY["err"] = {"answers": {}}, ""
CALLS.clear()
done_look = bp.put({"name": "Probe Cement", "people_setting": "a site", "sound_world": "plain"}, cement["id"])
rn = bs.suggest_group(done_look, "Look and sound")
expect("no model call is made when every question in the group is already answered", CALLS == [] and rn["suggestions"] == {} and rn["error"] == "", (CALLS, rn))
bp.put({"name": "Probe Cement", "people_setting": "", "sound_world": ""}, cement["id"])

print("Nothing is stored")
before = open(os.path.join(os.environ["STUDIO_DATA_DIR"], "tenants", "default", "brands", cement["id"] + ".json"), encoding="utf-8").read()
listing = sorted(os.listdir(os.path.join(os.environ["STUDIO_DATA_DIR"], "tenants", "default")))
REPLY["data"] = {"answers": {"sound_world": {"value": "plain and direct", "basis": "knowledge", "unknowns": ""}}}
bs.suggest_group(bp.load(cement["id"]), "Look and sound")
after = open(os.path.join(os.environ["STUDIO_DATA_DIR"], "tenants", "default", "brands", cement["id"] + ".json"), encoding="utf-8").read()
expect("the profile file is byte-identical after a draft", before == after)
expect("no new store appeared", listing == sorted(os.listdir(os.path.join(os.environ["STUDIO_DATA_DIR"], "tenants", "default"))))

print("The route")
REPLY["data"] = {"answers": {"sound_world": {"value": "plain and direct", "basis": "knowledge", "unknowns": ""},
                             "people_setting": {"value": "a contractor on a half-built wall", "basis": "profile", "unknowns": ""}}}
ok = client.post("/brand-suggest", json={"brand": "Probe Cement", "group": "Look and sound"})
expect("a known brand by name returns suggestions", ok.status_code == 200 and ok.json()["suggestions"]["sound_world"]["value"] == "plain and direct", ok.text[:200])
okid = client.post("/brand-suggest", json={"brand": cement["id"], "group": "Look and sound"})
expect("a known brand by id works too", okid.status_code == 200)
expect("an unknown brand is a 404", client.post("/brand-suggest", json={"brand": "No Such", "group": "Look and sound"}).status_code == 404)
expect("a missing brand is a 404, not a guess at the active one", client.post("/brand-suggest", json={"group": "Look and sound"}).status_code == 404)
REPLY["data"], REPLY["err"] = None, bs.NO_KEY
expect("no key is a 503", client.post("/brand-suggest", json={"brand": "Probe Cement", "group": "Look and sound"}).status_code == 503)
REPLY["err"] = "boom"
bad = client.post("/brand-suggest", json={"brand": "Probe Cement", "group": "Look and sound"})
expect("any other failure is a 502 that carries the reason", bad.status_code == 502 and bad.json()["detail"] == "boom", bad.text[:200])
bf = client.get("/brand-fields", params={"brand": "Probe Cement"}).json()
expect("/brand-fields carries the groups still worth drafting", [g["name"] for g in bf["suggest_groups"]] == [g["name"] for g in bs.GROUPS], bf.get("suggest_groups"))
saved = client.post("/brand-fields", json={"brand": cement["id"], "worst_case": "a failed strength test"}).json()
expect("saving returns the groups too, and the answered question has left its group",
       "worst_case" not in next(g for g in saved["suggest_groups"] if g["name"] == "Proof and marks")["keys"], saved.get("suggest_groups"))

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All brand-suggest cases behave.")
