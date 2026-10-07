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
check("notes and links are capped; only the seven channels exist", len(junk["competitors"][0]["channels"]["tvc"]["note"]) == 800 and len(junk["competitors"][0]["channels"]["tvc"]["link"]) == 300 and set(junk["competitors"][0]["channels"]) == set(pv.CHANNELS), "")
check("a non-dict is an empty set of evidence", pv.normalise_evidence(None) == {"competitors": []} and pv.normalise_evidence("x") == {"competitors": []}, "")
pv.evidence_save(HID, {"competitors": EV["competitors"]})
check("evidence saves and comes back once per house", [c["name"] for c in pv.evidence_load(HID)["competitors"]] == ["BrandA", "BrandB", "BrandC"], "")
check("an empty or unknown house has none, and an id is a file name", pv.evidence_load("")["competitors"] == [] and pv.evidence_load("../x")["competitors"] == [] and pv.evidence_load("nope")["competitors"] == [], "")
st = pv.evidence_strength(EV)
check("strength counts competitors with something given, and slots filled of those possible", st == {"competitors": 2, "slots_filled": 3, "slots_total": 21}, str(st))

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
check("the skill and the hard limits are in the prompt", "No celebrity" in p and "belief" in p.lower() and "device" in p.lower(), "")
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
check("it reports how much evidence stood behind it", cv["evidence"] == {"competitors": 2, "slots_filled": 3, "slots_total": 21}, str(cv["evidence"]))
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

print("the three layers: beliefs, behaviours, codes")
gen._ask = stub({"category": "packaged milk", "codes": [
    {"layer": "code", "kind": "visual", "code": "Golden dawn light", "basis": "memory"},
    {"layer": "behaviour", "kind": "behaviour", "code": "Brands show the farmer and never pay him", "basis": "memory"},
    {"layer": "belief", "kind": "belief", "code": "Goodness is proven by where the milk came from", "basis": "memory"},
    {"layer": "belief", "kind": "belief", "code": "Love is what the mother serves", "basis": "memory"},
    {"kind": "behaviour", "code": "Brands compete on price offers", "basis": "memory"},          # layer left out, kind says it
    {"kind": "tonal", "code": "Hushed reassurance", "basis": "memory"},                             # an audit from before layers
    {"layer": "nonsense", "kind": "belief", "code": "Strength is the benefit", "basis": "memory"}]})
out, err = gen.audit_codes(house, pset, platform, EV_EMPTY, "")
lay = [(c["layer"], c["code"]) for c in out["codes"]]
check("beliefs come first, then behaviours, then codes, in the model's own order within each",
      [l for l, _c in lay] == ["belief"] * 3 + ["behaviour"] * 2 + ["code"] * 2
      and [c for l, c in lay if l == "belief"] == ["Goodness is proven by where the milk came from", "Love is what the mother serves", "Strength is the benefit"], str(lay))
check("a missing or unknown layer is read from the kind (belief/behaviour), else it is a code",
      dict((c, l) for l, c in lay)["Brands compete on price offers"] == "behaviour" and dict((c, l) for l, c in lay)["Hushed reassurance"] == "code"
      and dict((c, l) for l, c in lay)["Strength is the benefit"] == "belief", str(lay))
check("only the strongest belief and the strongest behaviour are suggested (ticked) to start",
      [c["code"] for c in out["codes"] if c.get("suggested")] == ["Goodness is proven by where the milk came from", "Brands show the farmer and never pay him"], str([c["code"] for c in out["codes"] if c.get("suggested")]))
check("a belief or behaviour carries its layer as its kind; a code keeps one of the five kinds",
      all(c["kind"] == c["layer"] for c in out["codes"] if c["layer"] != "code") and all(c["kind"] in gen.CODE_KINDS for c in out["codes"] if c["layer"] == "code"), "")
gen._ask = stub({"codes": [{"kind": "visual", "code": "Golden light", "basis": "memory"}]})
out, _e = gen.audit_codes(house, pset, platform, EV, "")
pl = seen_prompts[-1]
check("the prompt asks for the three layers and what brands DO, not only how they look", "belief" in pl and "behaviour" in pl and "DOES" in pl and "take for granted" in pl.lower(), pl[-900:])
check("the evidence it is given now has claims and what they do as slots", "Claims and promises" in pv.CHANNEL_LABELS.values() and "What they do" in pv.CHANNEL_LABELS.values(), "")
ev7 = pv.normalise_evidence({"competitors": [{"name": "BrandA", "channels": {"actions": {"note": "Pays farmers a monthly premium"}, "claims": {"note": "Fresh in 6 hours"}}}]})
gen._ask = stub({"codes": [{"layer": "behaviour", "code": "Pays a premium", "basis": "seen", "seen_in": ["BrandA What they do"]},
                            {"layer": "belief", "code": "Freshness is speed", "basis": "seen", "seen_in": ["BrandA Claims and promises"]},
                            {"layer": "belief", "code": "Not given", "basis": "seen", "seen_in": ["BrandA TVC"]}]})
out, _e = gen.audit_codes(house, pset, platform, ev7, "")
bb = {c["code"]: c["basis"] for c in out["codes"]}
check("what a competitor claims or does can ground an item as seen; a channel it gave nothing for cannot",
      bb == {"Pays a premium": "seen", "Freshness is speed": "seen", "Not given": "memory"}, str(bb))
check("what they claim and do reaches the model word for word", "Pays farmers a monthly premium" in seen_prompts[-1] and "Fresh in 6 hours" in seen_prompts[-1], "")

print("sparks")
check("a spark needs at least one code to break", gen.spark(house, pset, platform, EV, [], "")[0] is None and gen.spark(house, pset, platform, EV, "x", "")[1].startswith("Pick"), "")
gen._ask = stub({"sparks": [
    {"text": "A film with no people", "codes": ["Mother as hero"], "stays_true": "the doorframe", "scores": {"breaks": 5, "true": 4, "travels": 4}, "risk": "medium"},
    {"text": "The glass that refuses", "codes": ["x"], "scores": {"breaks": 99, "true": "high", "travels": None}, "risk": "extreme"},
    {"text": "", "codes": []}, "junk", {"text": "Third", "scores": {"breaks": 2, "true": 2, "travels": 2}, "risk": "low"}]})
out, err = gen.spark(house, pset, platform, EV, ["Mother as hero", "Golden light"], "keep it dry", n=3)
sp = out["sparks"]
check("sparks are cleaned and sorted best first", [s["text"] for s in sp] == ["A film with no people", "The glass that refuses", "Third"] and sp[0]["total"] == 22, str([(s['text'], s['total']) for s in sp]))
check("out-of-range scores become 3 and an unknown risk becomes medium", sp[1]["scores"] == {k: 3 for k in gen.SCORE_KEYS} and sp[1]["risk"] == "medium" and sp[2]["risk"] == "low", str(sp[1]))
check("the chosen codes and the steer reach the model", "Mother as hero" in seen_prompts[-1] and "Golden light" in seen_prompts[-1] and "keep it dry" in seen_prompts[-1], "")
gen._ask = stub({"sparks": [
    {"text": "The brand pays the farmer first", "codes": ["x"], "device": "Proof by Doing", "scores": {k: 5 for k in gen.SCORE_KEYS}, "risk": "low"},
    {"text": "Another", "codes": ["x"], "device": "magic", "scores": {}, "risk": "low"}]})
out, err = gen.spark(house, pset, platform, EV, [{"code": "Goodness is proven by origin", "layer": "belief"}, {"code": "Golden light", "layer": "code"}, "A plain string"], "", n=3)
sp = out["sparks"]
spark_prompt = seen_prompts[-1]
check("a device is read tolerantly and an unknown one is empty, never invented", sp[0]["device"] == "proof_by_doing" and sp[1]["device"] == "", str(sp))
check("sparks are scored on six things, summed", sp[0]["total"] == 30 and set(sp[0]["scores"]) == set(gen.SCORE_KEYS) and len(gen.SCORE_KEYS) == 6, str(sp[0]))
gen._ask = stub({"sparks": [{"text": "Mother signs it off", "codes": ["[belief] Purity is handed down", "[behaviour] Brands show the farm", "[code] Golden light", "Plain one"], "device": "reversal", "scores": {}, "risk": "low"}]})
out, _e = gen.spark(house, pset, platform, EV, [{"code": "[belief] Purity is handed down", "layer": "belief"}], "", n=3)
check("the [belief]/[behaviour]/[code] tag the prompt lists things with is taken off a spark's codes, which the model copies onto them",
      out["sparks"][0]["codes"] == ["Purity is handed down", "Brands show the farm", "Golden light", "Plain one"], str(out["sparks"][0]["codes"]))
check("and off what is picked", gen._picked(["[belief] A thing", {"code": "[Code] Another", "layer": "code"}]) == [("A thing", ""), ("Another", "code")], str(gen._picked(["[belief] A thing", {"code": "[Code] Another", "layer": "code"}])))
gen._ask = stub({"codes": [{"layer": "belief", "code": "x", "basis": "memory"}]})
gen.audit_codes(house, pset, platform, EV_EMPTY, "")
check("the audit asks for what the platform gives a true counter to first, and at least three things a business DOES (a portrayal is a code)",
      "true counter" in seen_prompts[-1] and "At least three" in seen_prompts[-1] and "a portrayal is a code" in seen_prompts[-1], seen_prompts[-1][-1100:])
check("what is to be broken reaches the model with its layer, a plain string still works, and the device menu is given",
      "[belief] Goodness is proven by origin" in spark_prompt and "[code] Golden light" in spark_prompt and "A plain string" in spark_prompt
      and "proof_by_doing" in spark_prompt and "DO" in spark_prompt, spark_prompt[-700:])
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
RAW_SPINE = {**RAW_REC, "core": {**RAW_REC["core"], "message": "", "device": "proof by doing", "device_note": "The brand really pays first",
             "tension": {"category_says": "Brands show the farmer", "we_say": "We pay him first"}, "repeatable": "We pay the farmer first",
             "act": "Pay the farmer before the shop", "act_note": "Procurement must agree"}}
gen._ask = stub(RAW_SPINE)
rec4, _e = gen.develop(house, pset, platform, EV, {"text": "x", "device": "absence", "codes": ["Mother as hero"]}, ["Mother as hero"], "")
c4 = rec4["core"]
check("the message is the platform's own words when the model leaves it out, never blank", c4["message"] == "Every glass is a small promise", c4["message"])
check("the device, the tension, the repeatable line and the act come through, the device read tolerantly",
      c4["device"] == "proof_by_doing" and c4["tension"]["we_say"] == "We pay him first" and c4["repeatable"] == "We pay the farmer first" and c4["act"] == "Pay the farmer before the shop", str(c4))
check("the spine rules reach the model (one device from the list, an act is a proposal, every medium dramatises the same message)",
      "device = exactly one id" in seen_prompts[-1] and "proof_by_doing" in seen_prompts[-1] and "never say the brand already does it" in seen_prompts[-1] and "SAME message" in seen_prompts[-1], "")
check("the spark's device and its chosen codes reach the model", "Its device: absence" in seen_prompts[-1], "")
gen._ask = stub({**RAW_REC})
rec5, _e = gen.develop(house, pset, platform, EV, {"text": "x", "device": "absence"}, ["Mother as hero"], "")
check("when the model names no device the spark's stands", rec5["core"]["device"] == "absence", str(rec5["core"]["device"]))
rec6, _e = gen.develop(house, pset, platform, EV, {"text": "x"}, ["Mother as hero"], "")
check("with neither, the device is empty (and the screen will ask for one)", rec6["core"]["device"] == "", "")
saved4 = pv.save(rec4)
gen._ask = stub({**RAW_SPINE, "core": {**RAW_SPINE["core"], "line": "A bolder line.", "message": "DRIFTED TO SOMETHING ELSE", "device": "reversal"}})
pushed4, _e = gen.push_further(saved4, house, pset, platform, EV, "braver")
check("pushing keeps the message it stood on, even if the model drifts, and may change the device", pushed4["core"]["message"] == "Every glass is a small promise" and pushed4["core"]["device"] == "reversal", str(pushed4["core"]["message"]))
check("pushing is given the spine, not just the line", "Message: Every glass is a small promise" in seen_prompts[-1] and "Device: proof_by_doing" in seen_prompts[-1] and "What it breaks:" in seen_prompts[-1] and "sharper tension" in seen_prompts[-1], "")

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
ck_spine = {c["id"]: c for c in gen.check_guardrails(clean, prof, names)}
check("a draft with no message or device is warned: it is a look, not an idea", ck_spine["spine"]["level"] == "warn" and "message" in ck_spine["spine"]["text"] and "device" in ck_spine["spine"]["text"], str(ck_spine["spine"]))
whole = pv.normalise({**clean, "core": {**clean["core"], "message": "m", "device": "absence"}})
ck_whole = {c["id"]: c for c in gen.check_guardrails(whole, prof, names)}
check("with a message and a device the spine check passes, and no act means no act line", ck_whole["spine"]["level"] == "pass" and "act" not in ck_whole, "")
withact = pv.normalise({**whole, "core": {**whole["core"], "act": "Pay the farmer first", "act_note": "Needs procurement"}})
ck_act = {c["id"]: c for c in gen.check_guardrails(withact, prof, names)}
check("an act asks the business to agree and to fit the approved claims", ck_act["act"]["level"] == "manual" and "business" in ck_act["act"]["text"] and "claims" in ck_act["act"]["text"], "")
claimy = pv.normalise({**whole, "core": {**whole["core"], "act": "Add a promise that it boosts immunity", "message": "m", "device": "absence"}})
check("the claims checks read the act and the message too (an act that promises is a claim)", {c["id"]: c for c in gen.check_guardrails(claimy, prof, names)}["health"]["level"] == "warn", "")
rival_in_tension = pv.normalise({**whole, "core": {**whole["core"], "tension": {"category_says": "Amul says it is pure", "we_say": "x"}}})
check("a named rival in the two-sentence test fails like anywhere else", {c["id"]: c for c in gen.check_guardrails(rival_in_tension, prof, names)}["rivals"]["level"] == "fail", "")
check("blocking reasons are only the hard failures", len(gen.has_failures(gen.check_guardrails(dirty, prof, names))) == 3 and gen.has_failures(gen.check_guardrails(clean, prof, names)) == [], "")
check("with no brand profile the check still runs", gen.check_guardrails(clean, None, [])[0]["level"] == "pass", "")

print("the stranger's reading")
secret = pv.normalise({"name": "The ritual", "core": {"line": "No faces, only the pour, repeated.", "message": "SECRET INTENDED MESSAGE", "device": "absence", "repeatable": "SECRET REPEATABLE"},
                       "expressions": {"video": "A dark kitchen, a packet, a glass.", "social": "One pour held."},
                       "film": {"structure": "One take", "visual_language": "Deep forest", "notes": "SECRET NOTES"}})
gen._ask = stub({"takeaway": "A dairy brand that likes quiet mornings", "repeat": "nothing much", "ownable": {"answer": "no", "why": "any dairy could"},
                 "cuts": ["the closing line", "the slow open", "the dark palette", "a fourth"]})
out, err = gen.message_test(secret, house)
tp = seen_prompts[-1]
check("the reader is given the line, what it becomes and the film, and the brand's name", "No faces, only the pour" in tp and "A dark kitchen" in tp and "One take" in tp and "TestBrand" in tp, tp[:500])
check("the reader is NEVER told the intended message, the device, the repeatable line, the platform or the notes",
      "SECRET INTENDED MESSAGE" not in tp and "SECRET REPEATABLE" not in tp and "SECRET NOTES" not in tp and "absence" not in tp and "Every glass is a small promise" not in tp and "The small promise" not in tp, tp)
check("it answers with the takeaway, what they would repeat, ownable yes/no, at most three cuts, and the intended message beside it",
      out["takeaway"].startswith("A dairy brand") and out["repeat"] == "nothing much" and out["ownable"]["answer"] == "no" and len(out["cuts"]) == 3 and out["intended"] == "SECRET INTENDED MESSAGE", str(out))
gen._ask = stub({"takeaway": "x", "ownable": {"answer": "maybe"}, "cuts": "none"})
out, _e = gen.message_test(secret, house)
check("an odd ownable answer is 'unclear' and a non-list of cuts is empty", out["ownable"]["answer"] == "unclear" and out["cuts"] == [], str(out))
gen._ask = stub({"takeaway": ""})
check("no takeaway is an honest error", gen.message_test(secret, house)[0] is None, "")
check("nothing to test without a line", gen.message_test(pv.normalise({}), house)[1].startswith("There is nothing"), "")
gen._ask = ORIG_ASK
check("with no key it says so", gen.message_test(secret, house)[1] == gen.NO_KEY, "")

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
check("the evidence reads with the competitor names already on file and the seven channels", r.status_code == 200 and r.json()["competitors_on_file"] == ["Amul", "Nandini"] and len(r.json()["channels"]) == 7 and r.json()["strength"]["slots_filled"] == 3, r.text[:200])
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
check("the list carries the nine devices for the screen", len(client.get("/provocations", params={"house": HID}).json()["devices"]) == 9, "")
gen._ask = stub({"takeaway": "A dairy brand that likes quiet", "repeat": "nothing", "ownable": {"answer": "yes", "why": "w"}, "cuts": ["c"]})
n_before = len(pv.for_house(HID, include_archived=True))
r = client.post("/provocation-test", json={"id": PID})
check("the message test answers for a saved provocation, and saves nothing", r.status_code == 200 and r.json()["takeaway"].startswith("A dairy") and "intended" in r.json() and len(pv.for_house(HID, include_archived=True)) == n_before, r.text[:200])
r = client.post("/provocation-test", json={"house": HID, "record": {"name": "x", "core": {"line": "A line"}}})
check("an unsaved draft can be tested too", r.status_code == 200, r.text[:200])
check("the test needs a house or an id", client.post("/provocation-test", json={}).status_code == 400, "")
gen._ask = lambda prompt, max_tokens: (None, "the model returned nothing")
check("a failed reading is a 502 with the reason", client.post("/provocation-test", json={"id": PID}).status_code == 502, "")
gen._ask = ORIG_ASK
check("with no key the test answers 503", client.post("/provocation-test", json={"id": PID}).status_code == 503, "")

print("approval is blocked by a hard failure")
bad = client.post("/provocation", json={"house": HID, "name": "Bad one", "core": {"line": "Pure magic, unlike Amul", "risk": "low"}}).json()["id"]
r = client.post("/provocation-approve", json={"id": bad, "who": "Asha"})
check("a banned word or a named rival stops approval, with the reasons", r.status_code == 400 and "Amul" in r.json()["detail"], r.text[:240])
ok_id = client.post("/provocation", json={"house": HID, "name": "Fine one", "core": {"line": "Say nothing; show the glass.", "risk": "low", "message": "Every glass is a small promise", "device": "absence"}}).json()["id"]
check("a clean one still approves", client.post("/provocation-approve", json={"id": ok_id, "who": "Asha"}).json()["status"] == "approved", "")
check("withdrawing approval is never blocked by the check", client.post("/provocation-approve", json={"id": bad, "who": "Asha", "on": False}).status_code == 200, "")

print()
print("All provocation-generation cases behave." if not fails else f"{fails} provocation-generation case(s) FAILED.")
sys.exit(1 if fails else 0)
