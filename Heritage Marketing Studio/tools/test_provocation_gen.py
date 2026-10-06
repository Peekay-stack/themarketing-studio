#!/usr/bin/env python
"""test_provocation_gen.py -- writing a provocation: the competitor evidence, the codes audit, sparks, developing, pushing, the check.

The model is replaced by a stub (provocation_gen._ask), so this tests everything AROUND the model: what it is given, what is done to
what it returns, and what the screen is told. It cannot say whether a real provocation is any good: that needs one real run, judged
by a person. No key, no credit, a scratch data folder (set BEFORE anything is imported).

    python tools/test_provocation_gen.py       # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="provgen_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import brandprofile      # noqa: E402
import ideas             # noqa: E402
import provocation as pv  # noqa: E402
import provocation_gen as gen  # noqa: E402
import selfcheck         # noqa: E402
import strategy          # noqa: E402

fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


# ---------------------------------------------------------------- fixtures
brandprofile.save({"id": "tb1", "name": "TestBrand", "category": "packaged milk", "tone": "warm, wholesome, reassuring",
                   "competitors": ["Amul", "Nandini"], "banned_words": ["pure", "miracle"], "avoid": ["use cartoon animals", "mock the farmer"],
                   "claims": [{"claim": "Sourced from 3,000 local farms", "proof": "procurement records"}], "regulator": "FSSAI"})
house = strategy.new_house("TestBrand")
HID = house["id"]
house["nodes"]["core"]["options"] = [{"id": "c1", "text": "Honest milk, from farms you could name"}]
house["nodes"]["core"]["chosen"] = ["c1"]
strategy.save(house)
pset = ideas.add(ideas.new_set("TestBrand", HID), {"name": "The small promise", "idea": "Every glass is a small promise", "mechanic": "A mark on the doorframe"})
PLAT = pset["platforms"][0]
ideas.choose(pset, PLAT["id"])
pset = ideas.for_house(HID)
platform = ideas.chosen_platform(pset)

EV_EMPTY = {"competitors": []}
EV = pv.normalise_evidence({"competitors": [
    {"name": "BrandA", "channels": {"tvc": {"note": "Opens on a mother at dawn; ends on the pack shot with a jingle", "link": "https://example.com/a-tvc"},
                                   "packaging": {"note": "Green pouch, cow illustration"}}},
    {"name": "BrandB", "channels": {"instagram": {"note": "Festive recipes, golden light, steel tumblers"}}},
    {"name": "BrandC", "channels": {}}]})

print("competitor evidence")
junk = pv.normalise_evidence({"competitors": [None, 5, {"name": ""}, {"name": "A", "channels": {"tvc": {"note": "n" * 2000, "link": "l" * 900}, "nonsense": {"note": "x"}}},
                                              {"name": "a"}, {"name": "B", "channels": "x"}] + [{"name": f"C{i}"} for i in range(20)]})
check("blank names, repeats (any case) and junk are dropped; at most six competitors", len(junk["competitors"]) == 6 and junk["competitors"][0]["name"] == "A", str([c["name"] for c in junk["competitors"]]))
check("notes and links are capped; only the five channels exist", len(junk["competitors"][0]["channels"]["tvc"]["note"]) == 800 and len(junk["competitors"][0]["channels"]["tvc"]["link"]) == 300 and set(junk["competitors"][0]["channels"]) == set(pv.CHANNELS), "")
check("a non-dict is an empty set of evidence", pv.normalise_evidence(None) == {"competitors": []} and pv.normalise_evidence("x") == {"competitors": []}, "")
pv.evidence_save(HID, {"competitors": EV["competitors"]})
check("evidence saves and comes back once per house", [c["name"] for c in pv.evidence_load(HID)["competitors"]] == ["BrandA", "BrandB", "BrandC"], "")
check("an empty or unknown house has none, and an id is a file name", pv.evidence_load("")["competitors"] == [] and pv.evidence_load("../x")["competitors"] == [] and pv.evidence_load("nope")["competitors"] == [], "")
st = pv.evidence_strength(EV)
check("strength counts competitors with something given, and slots filled of those possible", st == {"competitors": 2, "slots_filled": 3, "slots_total": 15}, str(st))

print("what the model is given")
ORIG_ASK = gen._ask
seen_prompts = []


def stub(reply):
    def _ask(prompt, max_tokens):
        seen_prompts.append(prompt)
        return (reply(prompt) if callable(reply) else reply), ""
    return _ask


gen._ask = stub({"category": "packaged milk", "codes": [{"kind": "visual", "code": "Golden dawn light", "how": "x", "basis": "memory", "seen_in": []}]})
out, err = gen.audit_codes(house, pset, platform, EV, "push against the mother")
p = seen_prompts[-1]
check("the brand's guardrails go in: banned words, never-do, claims, regulator", "pure, miracle" in p and "NEVER DO" in p and "use cartoon animals" in p and "3,000 local farms" in p and "FSSAI" in p, "")
check("the brand's TONE does not (a provocation departs from it)", "TONE:" not in p and "warm, wholesome" not in p, "")
check("the house, the platform and the steer go in", "Honest milk" in p and "Every glass is a small promise" in p and "A mark on the doorframe" in p and "push against the mother" in p, "")
check("the evidence goes in word for word, with its link", "Opens on a mother at dawn" in p and "https://example.com/a-tvc" in p and "Green pouch" in p, "")
check("competitors with no evidence are listed as memory-only", "BrandC" in p and "memory only" in p, "")
check("the skill and the hard limits are in the prompt", "No celebrity" in p and "category code" in p.lower(), "")
gen._ask = stub({"codes": [{"kind": "visual", "code": "x", "basis": "memory", "seen_in": []}]})
gen.audit_codes(house, pset, platform, EV_EMPTY, "")
check("with no evidence the model is told to tag everything as memory", "none provided" in seen_prompts[-1] and "Amul" in seen_prompts[-1], seen_prompts[-1][-400:])

print("the codes audit")
raw = {"category": "packaged milk", "codes": [
    {"kind": "visual", "code": "Golden dawn light", "how": "a", "basis": "seen", "seen_in": ["BrandB Instagram page"]},
    {"kind": "tonal", "code": "Hushed reassurance", "how": "b", "basis": "seen", "seen_in": ["BrandA TVC"]},
    {"kind": "verbal", "code": "Claims 'pure'", "how": "c", "basis": "seen", "seen_in": ["BrandA Instagram page"]},      # BrandA gave no Instagram
    {"kind": "sonic", "code": "Soft strings", "how": "d", "basis": "seen", "seen_in": ["BrandZ TVC"]},                    # BrandZ is not in the evidence
    {"kind": "structural", "code": "A child grows up", "how": "e", "basis": "seen", "seen_in": []},                        # claims seen, cites nothing
    {"kind": "banana", "code": "Mother as hero", "how": "f", "basis": "memory", "seen_in": ["BrandA TVC"]},
    {"code": ""}, "junk", None]}
gen._ask = stub(raw)
out, err = gen.audit_codes(house, pset, platform, EV, "")
by = {c["code"]: c for c in out["codes"]}
check("a code that cites real evidence stays 'seen', with its reference", by["Golden dawn light"]["basis"] == "seen" and by["Golden dawn light"]["seen_in"] == ["BrandB Instagram page"] and by["Hushed reassurance"]["basis"] == "seen", str(by))
check("'seen' is downgraded to memory when the competitor gave no such channel, is not in the evidence, or cites nothing",
      by["Claims 'pure'"]["basis"] == "memory" and by["Soft strings"]["basis"] == "memory" and by["A child grows up"]["basis"] == "memory", str([(c['code'], c['basis']) for c in out["codes"]]))
check("a downgraded code carries no invented reference", all(c["seen_in"] == [] for c in out["codes"] if c["basis"] == "memory"), "")
check("an unknown kind becomes visual; blanks and junk are dropped", by["Mother as hero"]["kind"] == "visual" and len(out["codes"]) == 6, str(len(out["codes"])))
cv = out["caveat"]
check("the caveat is computed from the tags (2 of 6 grounded) and invites more", cv["seen"] == 2 and cv["memory"] == 4 and "2 of 6" in cv["text"] and cv["invite"], str(cv))
check("it reports how much evidence stood behind it", cv["evidence"] == {"competitors": 2, "slots_filled": 3, "slots_total": 15}, str(cv["evidence"]))
gen._ask = stub({"codes": [{"kind": "visual", "code": "Golden light", "basis": "seen", "seen_in": ["BrandB Instagram page"]}]})
out, _e = gen.audit_codes(house, pset, platform, EV_EMPTY, "")
check("with no evidence nothing can be 'seen', even if the model says so, and the caveat says they are hypotheses",
      out["codes"][0]["basis"] == "memory" and "hypotheses" in out["caveat"]["text"] and out["caveat"]["invite"], str(out["caveat"]))
gen._ask = stub({"codes": [{"kind": "visual", "code": "Golden light", "basis": "seen", "seen_in": ["BrandB Instagram page"]}]})
out, _e = gen.audit_codes(house, pset, platform, EV, "")
check("when every code is grounded there is no nudge to add more", out["caveat"]["memory"] == 0 and out["caveat"]["invite"] == "", str(out["caveat"]))
gen._ask = stub({"codes": "nothing useful"})
out, err = gen.audit_codes(house, pset, platform, EV, "")
check("no usable codes is an honest error, not a placeholder", out is None and "usable codes" in err, err)
gen._ask = ORIG_ASK
out, err = gen.audit_codes(house, pset, platform, EV, "")
check("with no key it says so and makes nothing up", out is None and err == gen.NO_KEY, err)
gen._ask = lambda prompt, max_tokens: (None, "the reply was cut off")
check("a failed model call is passed on as the reason", gen.audit_codes(house, pset, platform, EV, "")[1] == "the reply was cut off", "")

print("sparks")
check("a spark needs at least one code to break", gen.spark(house, pset, platform, EV, [], "")[0] is None and gen.spark(house, pset, platform, EV, "x", "")[1].startswith("Pick"), "")
gen._ask = stub({"sparks": [
    {"text": "A film with no people", "codes": ["Mother as hero"], "stays_true": "the doorframe", "scores": {"breaks": 5, "true": 4, "travels": 4}, "risk": "medium"},
    {"text": "The glass that refuses", "codes": ["x"], "scores": {"breaks": 99, "true": "high", "travels": None}, "risk": "extreme"},
    {"text": "", "codes": []}, "junk", {"text": "Third", "scores": {"breaks": 2, "true": 2, "travels": 2}, "risk": "low"}]})
out, err = gen.spark(house, pset, platform, EV, ["Mother as hero", "Golden light"], "keep it dry", n=3)
sp = out["sparks"]
check("sparks are cleaned and sorted best first", [s["text"] for s in sp] == ["A film with no people", "The glass that refuses", "Third"] and sp[0]["total"] == 13, str([(s['text'], s['total']) for s in sp]))
check("out-of-range scores become 3 and an unknown risk becomes medium", sp[1]["scores"] == {"breaks": 3, "true": 3, "travels": 3} and sp[1]["risk"] == "medium" and sp[2]["risk"] == "low", str(sp[1]))
check("the chosen codes and the steer reach the model", "Mother as hero" in seen_prompts[-1] and "Golden light" in seen_prompts[-1] and "keep it dry" in seen_prompts[-1], "")
gen._ask = stub({"sparks": []})
check("no usable sparks is an honest error", gen.spark(house, pset, platform, EV, ["x"], "")[0] is None, "")

print("developing one, and pushing it further")
RAW_REC = {"name": "The quiet pour", "core": {"line": "Say nothing; show the glass.", "codes_broken": ["Mother as hero"], "stance": {"tone": "dry", "humour": "deadpan", "structure": "no arc"},
           "risk": "medium", "risk_note": "Could read as cold", "safer_version": "Her hands only", "legal_flag": False, "legal_ack": True},
           "expressions": {"video": "A film with no people", "social": "The marks", "posm": "", "activation": "x", "pr": "y", "ooh": "dropped", "bogus": "z"},
           "film": {"structure": "s", "humour": "h", "visual_language": "v", "sound_language": "sl", "cast_approach": "objects", "vo_words": 12, "brand_beat": "bb", "notes": "n"}}
gen._ask = stub(RAW_REC)
rec, err = gen.develop(house, pset, platform, EV, {"text": "A film with no people", "codes": ["Mother as hero"]}, ["Mother as hero"], "")
check("developing returns an UNSAVED draft stamped with the house, the platform and the fingerprints",
      rec and rec["id"] == "" and rec["status"] == "draft" and rec["house"] == HID and rec["platform"] == PLAT["id"] and rec["generated_under"]["platform"] and rec["generated_under"]["house"], str(rec)[:200])
check("the model can never pre-tick the legal acknowledgement", rec["core"]["legal_ack"] is False, "")
check("expressions are limited to the mediums asked for; the film part is normalised", set(rec["expressions"]) <= set(gen.EXPRESSION_KINDS) and rec["film"]["cast_approach"] == "objects" and rec["film"]["vo_words"] == 12, str(rec["expressions"]))
check("where it came from travels with it (the codes and the spark)", rec["source"]["codes_audit"] == ["Mother as hero"] and rec["source"]["sparks"][0]["text"] == "A film with no people", "")
gen._ask = stub({**RAW_REC, "core": {**RAW_REC["core"], "codes_broken": ["Mother as hero (memory)", "A reworded one (seen)"]}})
rec2, _ = gen.develop(house, pset, platform, EV, {"text": "x", "codes": ["Mother as hero"]}, ["Mother as hero"], "")
check("the codes the person chose are kept word for word, not the model's rewording or its copied (memory) tag", rec2["core"]["codes_broken"] == ["Mother as hero"], str(rec2["core"]["codes_broken"]))
rec3, _ = gen.develop(house, pset, platform, EV, {"text": "x"}, [], "")
check("with no chosen codes, a copied (memory) or (seen) tag is still stripped from the model's own", rec3["core"]["codes_broken"] == ["Mother as hero", "A reworded one"], str(rec3["core"]["codes_broken"]))
gen._ask = stub({"name": "n", "core": {"line": ""}})
check("the model not writing the provocation is an honest error", gen.develop(house, pset, platform, EV, {"text": "x"}, [], "")[0] is None, "")
check("no spark is an error before any model call", gen.develop(house, pset, platform, EV, {}, [], "")[1].startswith("Pick"), "")
saved = pv.save(rec)
gen._ask = stub({**RAW_REC, "core": {**RAW_REC["core"], "line": "Say nothing. Then take the glass away."}})
pushed, err = gen.push_further(saved, house, pset, platform, EV, "more absurd")
check("pushing returns a bolder one with the old line as its safer version, same id and creation time",
      pushed["core"]["line"].startswith("Say nothing. Then") and pushed["core"]["safer_version"] == "Say nothing; show the glass." and pushed["id"] == saved["id"] and pushed["created"] == saved["created"], str(pushed)[:200])
check("the direction reaches the model", "more absurd" in seen_prompts[-1], "")
check("there is nothing to push without a line", gen.push_further(pv.normalise({}), house, pset, platform, EV, "")[0] is None, "")

print("the guardrail check")
prof = brandprofile.resolve(house, pset)
names = gen.competitor_names(prof, EV)
check("competitor names are the profile's plus the evidence's, once each", names == ["Amul", "Nandini", "BrandA", "BrandB", "BrandC"], str(names))
clean = pv.normalise({"name": "The quiet pour", "core": {"line": "Say nothing; show the glass.", "risk": "low"}, "expressions": {"video": "A film with no people"}})
ck = {c["id"]: c for c in gen.check_guardrails(clean, prof, names)}
check("a clean one passes every machine check and lists what only a person can judge", all(ck[i]["level"] == "pass" for i in ("banned", "rivals", "health", "figures", "never")) and ck["manual"]["level"] == "manual" and "likeness" in ck["manual"]["text"], str(ck))
check("the house's never-do list is shown in the by-eye reminder", "use cartoon animals" in ck["manual"]["text"], "")
dirty = pv.normalise({"name": "Miracle glass", "core": {"line": "Pure goodness, unlike Amul. It boosts immunity by 40%. Please use cartoon animals.", "risk": "high"}})
ck = {c["id"]: c for c in gen.check_guardrails(dirty, prof, names)}
check("a banned word fails (whole words, any case)", ck["banned"]["level"] == "fail" and "pure" in ck["banned"]["text"] and "miracle" in ck["banned"]["text"], ck["banned"]["text"])
check("a named competitor fails", ck["rivals"]["level"] == "fail" and "Amul" in ck["rivals"]["text"], ck["rivals"]["text"])
check("health wording and figures warn", ck["health"]["level"] == "warn" and "immun" in ck["health"]["text"] and ck["figures"]["level"] == "warn", str(ck["health"]))
check("a short never-do phrase found in the text fails", ck["never"]["level"] == "fail", ck["never"]["text"])
hz = lambda t: [c for c in gen.check_guardrails(pv.normalise({"name": "x", "core": {"line": t}}), prof, names) if c["id"] == "health"][0]["level"]
check("film language ('treated', 'treatment') is not a health claim, but treating a condition is",
      hz("A dark, reverent visual treatment, the pour treated as a ritual") == "pass" and hz("It treats a stomach condition") == "warn" and hz("Helps treat diabetes") == "warn", "")
check("'secure' and 'purely' do not trip 'cure' or 'pure'", all(c["level"] == "pass" for c in gen.check_guardrails(pv.normalise({"name": "x", "core": {"line": "A secure, purely practical glass"}}), prof, names) if c["id"] in ("banned", "health")), "")
jab = pv.normalise({"name": "x", "core": {"line": "Everyone else whispers", "legal_flag": True}})
check("a competitor jab asks for the legal tick until it is given", {c["id"]: c for c in gen.check_guardrails(jab, prof, names)}["legal"]["level"] == "warn"
      and {c["id"]: c for c in gen.check_guardrails({**jab, "core": {**jab["core"], "legal_ack": True}}, prof, names)}["legal"]["level"] == "pass", "")
check("blocking reasons are only the hard failures", len(gen.has_failures(gen.check_guardrails(dirty, prof, names))) == 3 and gen.has_failures(gen.check_guardrails(clean, prof, names)) == [], "")
check("with no brand profile the check still runs", gen.check_guardrails(clean, None, [])[0]["level"] == "pass", "")

print("routes")
from starlette.testclient import TestClient  # noqa: E402

import main  # noqa: E402

# `import main` loads the local .env, which puts a real key back. This test must never reach a real model: take the key out again, and
# make any attempt to call one a loud failure rather than a quiet charge.
os.environ.pop("ANTHROPIC_API_KEY", None)


def _no_real_calls(*a, **k):
    raise AssertionError("a real model call was attempted from a test")


gen.jsonout.ask_json = _no_real_calls

client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})
r = client.get("/category-evidence", params={"house": HID})
check("the evidence reads with the competitor names already on file and the five channels", r.status_code == 200 and r.json()["competitors_on_file"] == ["Amul", "Nandini"] and len(r.json()["channels"]) == 5 and r.json()["strength"]["slots_filled"] == 3, r.text[:200])
r = client.post("/category-evidence", json={"house": HID, "competitors": [{"name": "BrandD", "channels": {"posm": {"note": "Shelf strip with a cow"}}}]})
check("saving replaces it whole", r.status_code == 200 and [c["name"] for c in r.json()["evidence"]["competitors"]] == ["BrandD"] and r.json()["strength"]["slots_filled"] == 1, r.text[:200])
check("evidence needs a house", client.post("/category-evidence", json={"competitors": []}).status_code == 400 and client.post("/category-evidence", json={"house": "nope"}).status_code == 400, "")
check("an unknown house has no evidence (never another house's)", client.get("/category-evidence", params={"house": "nope"}).json()["evidence"]["competitors"] == [], "")
client.post("/category-evidence", json={"house": HID, "competitors": EV["competitors"]})

bare_house = strategy.new_house("NoPlatformBrand")
gen._ask = stub({"codes": [{"kind": "visual", "code": "Golden light", "basis": "memory"}]})
check("every generate route needs a house and a chosen platform, and says which is missing",
      client.post("/provocation-codes", json={}).status_code == 400 and "house" in client.post("/provocation-codes", json={}).json()["detail"]
      and "platform" in client.post("/provocation-codes", json={"house": bare_house["id"]}).json()["detail"]
      and client.post("/provocation-sparks", json={"house": bare_house["id"], "codes": ["x"]}).status_code == 400
      and client.post("/provocation-develop", json={"house": bare_house["id"], "spark": {"text": "x"}}).status_code == 400, "")
r = client.post("/provocation-codes", json={"house": HID, "steer": "x"})
check("the codes route answers with codes, the caveat and the competitors", r.status_code == 200 and r.json()["codes"][0]["basis"] == "memory" and r.json()["caveat"]["text"] and "competitors" in r.json(), r.text[:200])
gen._ask = ORIG_ASK
check("with no key the generate routes answer 503 (the same convention /complete uses)", client.post("/provocation-codes", json={"house": HID}).status_code == 503, "")
gen._ask = lambda prompt, max_tokens: (None, "the model returned nothing")
check("any other model failure is a 502 with the reason", client.post("/provocation-codes", json={"house": HID}).status_code == 502, "")
gen._ask = stub({"sparks": [{"text": "A film with no people", "codes": ["x"], "scores": {"breaks": 4, "true": 4, "travels": 4}, "risk": "low"}]})
check("sparks without codes is a 400, with codes a list", client.post("/provocation-sparks", json={"house": HID, "codes": []}).status_code == 400
      and client.post("/provocation-sparks", json={"house": HID, "codes": ["x"], "n": 5}).json()["sparks"][0]["text"] == "A film with no people", "")
gen._ask = stub(RAW_REC)
n_before = len(pv.for_house(HID, include_archived=True))
r = client.post("/provocation-develop", json={"house": HID, "spark": {"text": "A film with no people", "codes": ["x"]}, "codes": ["x"]})
check("developing answers with an unsaved draft and the reasons it cannot be approved yet", r.status_code == 200 and r.json()["id"] == "" and "problems" in r.json(), r.text[:200])
check("developing is not saved by being asked", len(pv.for_house(HID, include_archived=True)) == n_before, "")
r = client.post("/provocation", json={**{k: r.json()[k] for k in ("name", "core", "expressions", "film", "source")}, "house": HID})
PID = r.json()["id"]
check("saving the developed draft works", r.status_code == 200 and PID, r.text[:200])
gen._ask = stub({**RAW_REC, "core": {**RAW_REC["core"], "line": "A bolder line."}})
r = client.post("/provocation-push", json={"id": PID, "direction": "more absurd"})
check("push answers with the bolder version (unsaved) and keeps the id", r.status_code == 200 and r.json()["core"]["line"] == "A bolder line." and r.json()["id"] == PID, r.text[:200])
check("what is saved is still the original until the person saves the bolder one", client.get("/provocation", params={"id": PID}).json()["core"]["line"] == "Say nothing; show the glass.", "")
check("push needs a saved provocation", client.post("/provocation-push", json={"id": "nope"}).status_code == 404, "")
r = client.post("/provocation-check", json={"id": PID})
check("the check route answers with the checks and what blocks approval", r.status_code == 200 and r.json()["blocking"] == [] and any(c["id"] == "manual" for c in r.json()["checks"]), r.text[:200])
r = client.post("/provocation-check", json={"house": HID, "record": {"name": "Miracle", "core": {"line": "Pure and better than Amul"}}})
check("a draft that has not been saved can be checked too", r.status_code == 200 and len(r.json()["blocking"]) == 2, r.text[:200])
check("the check needs a house or an id", client.post("/provocation-check", json={}).status_code == 400, "")

print("approval is blocked by a hard failure")
bad = client.post("/provocation", json={"house": HID, "name": "Bad one", "core": {"line": "Pure magic, unlike Amul", "risk": "low"}}).json()["id"]
r = client.post("/provocation-approve", json={"id": bad, "who": "Asha"})
check("a banned word or a named rival stops approval, with the reasons", r.status_code == 400 and "Amul" in r.json()["detail"], r.text[:240])
ok_id = client.post("/provocation", json={"house": HID, "name": "Fine one", "core": {"line": "Say nothing; show the glass.", "risk": "low"}}).json()["id"]
check("a clean one still approves", client.post("/provocation-approve", json={"id": ok_id, "who": "Asha"}).json()["status"] == "approved", "")
check("withdrawing approval is never blocked by the check", client.post("/provocation-approve", json={"id": bad, "who": "Asha", "on": False}).status_code == 200, "")

print()
print("All provocation-generation cases behave." if not fails else f"{fails} provocation-generation case(s) FAILED.")
sys.exit(1 if fails else 0)
