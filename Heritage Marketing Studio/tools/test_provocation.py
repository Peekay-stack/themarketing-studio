#!/usr/bin/env python
"""test_provocation.py -- the Provocation store and rules (provocation.py), the `stands_on` seam, and the routes.

No key, no credit, nothing generated, nothing real touched (a scratch data folder). The point of P0 is that NOTHING changes
until a person approves a provocation and a producer is told to stand on it, so this pins both halves: the new behaviour, and
that every existing answer is exactly what it was.

    python tools/test_provocation.py       # exit 0 = every case behaves
"""
from __future__ import annotations

import itertools
import os
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="prov_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import ideas         # noqa: E402
import producers     # noqa: E402
import provocation as pv  # noqa: E402
import selfcheck     # noqa: E402
import strategy      # noqa: E402

fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


# ---------------------------------------------------------------- fixtures: a house, a chosen platform
house = strategy.new_house("TestBrand")
HID = house["id"]
pset = ideas.new_set("TestBrand", HID)
pset = ideas.add(pset, {"idea": "Every glass is a small promise", "mechanic": "A mark on the doorframe", "expressions": {"video": "PLATFORM VIDEO", "social": "PLATFORM SOCIAL"}})
PLAT_ID = pset["platforms"][0]["id"]
ideas.choose(pset, PLAT_ID)
other = strategy.new_house("OtherBrand")


def current_platform():
    return ideas.chosen_platform(ideas.for_house(HID))


def good(**kw):
    rec = {"name": "The Quiet Pour", "core": {"line": "Say nothing; show the glass.", "risk": "medium", "message": "Every glass is a small promise", "device": "absence"},
           "expressions": {"video": "A film with no people.", "posm": ""}}
    rec.update(kw)
    return rec


print("shape")
junk = pv.normalise({"id": "x" * 100, "name": "n" * 500, "status": "weird", "core": {"risk": "extreme", "legal_flag": "yes", "line": ["a"], "codes_broken": ["a", 5, None, "b" * 900]},
                     "film": {"cast_approach": "robots", "vo_words": 999, "structure": 7}, "expressions": {"video": "v", "nonsense": "z", "posm": 4}, "evil": 1})
check("unknown keys are dropped and bad enums become empty", "evil" not in junk and junk["status"] == "draft" and junk["core"]["risk"] == "" and junk["film"]["cast_approach"] == "", str(junk)[:200])
tagged = pv.normalise({"core": {"codes_broken": ["Mother as hero (memory)", "Golden light (SEEN)", "Keeps (a) middle", "(memory)"]}})
check("the audit's (memory)/(seen) basis tag is stripped from a code, a lone tag leaves nothing, other brackets stay",
      tagged["core"]["codes_broken"] == ["Mother as hero", "Golden light", "Keeps (a) middle"], str(tagged["core"]["codes_broken"]))
check("overlong text is cut, wrong types become empty", len(junk["name"]) == 120 and junk["core"]["line"] == "" and junk["core"]["legal_flag"] is False and junk["film"]["vo_words"] is None and len(junk["core"]["codes_broken"][-1]) == 200, "")
check("only real media keep an expression", set(junk["expressions"]) == {"video"}, str(junk["expressions"]))
spine = pv.normalise({"core": {"message": "m" * 900, "device": "Proof by Doing", "device_note": "n", "tension": {"category_says": "a", "we_say": 5}, "repeatable": "r" * 400,
                            "act": "Pay the farmer first", "act_note": "Needs procurement to agree"}})
check("the spine is kept, device ids tolerate spaces and capitals, text is cut, wrong types become empty",
      spine["core"]["device"] == "proof_by_doing" and len(spine["core"]["message"]) == 400 and len(spine["core"]["repeatable"]) == 140
      and spine["core"]["tension"] == {"category_says": "a", "we_say": ""} and spine["core"]["act"] == "Pay the farmer first", str(spine["core"]))
check("an unknown device is empty, never invented", pv.normalise({"core": {"device": "magic"}})["core"]["device"] == "", "")
old_style = pv.normalise({"name": "Old", "core": {"line": "L", "codes_broken": ["a"], "risk": "low"}})
check("a draft made before the spine is still a valid record with an empty spine",
      old_style["core"]["message"] == "" and old_style["core"]["device"] == "" and old_style["core"]["tension"] == {"category_says": "", "we_say": ""} and old_style["core"]["act"] == "", "")
check("seven evidence slots exist (five channels, claims, what they do)", pv.CHANNELS[-2:] == ("claims", "actions") and len(pv.CHANNELS) == 7 and len(pv.devices()) == 9, "")
boom = []
for x in (None, [], "x", 5, {"core": []}, {"core": {"stance": 3}}, {"film": "f"}, {"expressions": []}, {"source": {"sparks": [1, None, {"score": "x"}]}}, {"generated_under": 4}):
    try:
        pv.normalise(x)
    except Exception as e:                                  # noqa: BLE001
        boom.append((repr(x), type(e).__name__))
check("nothing malformed raises", not boom, str(boom))

print("the store")
rec = pv.save(pv.apply_edit(None, {**good(), "house": HID, "platform": PLAT_ID}, house, current_platform()))
check("a new provocation is saved as a draft with an id", rec["id"] and rec["status"] == "draft" and pv.load(rec["id"])["name"] == "The Quiet Pour", str(rec)[:120])
check("an id is a file name: path tricks find nothing", pv.load("../../etc/passwd") is None and pv.load("") is None and pv.load(None) is None, "")
check("a house lists its own", [r["id"] for r in pv.for_house(HID)] == [rec["id"]], "")
check("another house sees none of it", pv.for_house(other["id"]) == [], "")
check("an empty house id lists nothing (never every house's)", pv.for_house("") == [] and pv.for_house(None) == [], "")
arch = pv.save(pv.archive(rec))
check("an archived one is hidden by default and shown when asked", pv.for_house(HID) == [] and len(pv.for_house(HID, include_archived=True)) == 1, "")
rec = pv.save(pv.archive(arch, on=False))
check("bringing it back makes it a draft", rec["status"] == "draft", "")

print("approval is a person's, with conditions")
check("a draft is not usable", not pv.usable(rec, HID) and pv.resolve_for(HID, rec["id"]) is None, "")
bare = pv.save(pv.apply_edit(None, {"house": HID, "name": "", "core": {"line": ""}}, house, current_platform()))
new_, problems = pv.approve(bare, "Asha")
check("an empty one cannot be approved, and says what is missing (name, line, message, device, risk)", new_ is None and len(problems) == 5, str(problems))
nospine = pv.apply_edit(None, {**good(), "house": HID, "core": {"line": "x", "risk": "low"}}, house, current_platform())
new_, problems = pv.approve(nospine, "Asha")
check("without the message and the device it cannot be approved (it is a look, not an idea)", new_ is None and len(problems) == 2 and any("message" in p for p in problems) and any("device" in p for p in problems), str(problems))
jab = pv.save(pv.apply_edit(None, {**good(), "house": HID, "core": {"line": "x", "risk": "high", "legal_flag": True, "message": "m", "device": "reversal"}}, house, current_platform()))
new_, problems = pv.approve(jab, "Asha")
check("a competitor jab needs the legal-review acknowledgement", new_ is None and any("legal" in p for p in problems), str(problems))
jab2 = pv.apply_edit(jab, {"core": {"line": "x", "risk": "high", "legal_flag": True, "legal_ack": True, "message": "m", "device": "reversal"}}, house, current_platform())
new_, problems = pv.approve(jab2, "Asha")
check("with the acknowledgement it can be", new_ is not None and new_["status"] == "approved" and new_["approved_by"] == "Asha" and new_["approved_at"], str(problems))
ok_rec, problems = pv.approve(rec, "Asha")
rec = pv.save(ok_rec)
check("a complete one is approved, by name and time", rec["status"] == "approved" and rec["approved_by"] == "Asha", str(problems))
check("an approved one of this house is usable and resolvable", pv.usable(rec, HID) and pv.resolve_for(HID, rec["id"])["id"] == rec["id"], "")
check("not for another house, not for an empty house, not for a missing id", pv.resolve_for(other["id"], rec["id"]) is None and pv.resolve_for("", rec["id"]) is None and pv.resolve_for(HID, "") is None, "")
back, _p = pv.approve(rec, "Asha", on=False)
check("withdrawing approval makes it a draft again", back["status"] == "draft" and back["approved_by"] == "", "")
check("an archived one cannot be approved", pv.approve(pv.archive(rec), "Asha")[0] is None, "")

print("editing")
edited = pv.apply_edit(rec, {"core": {**rec["core"], "line": "A different line."}}, house, current_platform())
check("editing an approved one puts it back to a draft with the approval cleared", edited["status"] == "draft" and edited["approved_by"] == "" and edited["approved_at"] == "", "")
same = pv.apply_edit(rec, {"name": rec["name"], "core": rec["core"]}, house, current_platform())
check("a save that changes nothing leaves it approved", same["status"] == "approved" and same["approved_by"] == "Asha", "")
sneaky = pv.apply_edit(edited, {"status": "approved", "approved_by": "Me"}, house, current_platform())
check("an edit can never approve (only approve() does)", sneaky["status"] == "draft" and sneaky["approved_by"] == "", "")
moved = pv.apply_edit(rec, {"house": other["id"]}, house, current_platform())
check("a provocation never changes house", moved["house"] == HID, "")

print("staleness: it must say when what it was written for has moved")
fresh = pv.save(pv.apply_edit(None, {**good(), "house": HID, "platform": PLAT_ID}, house, current_platform()))
check("a fresh one is not stale", pv.stale_because(fresh, house, current_platform()) == [], str(pv.stale_because(fresh, house, current_platform())))
ideas.edit(ideas.for_house(HID), PLAT_ID, {"idea": "Every glass is a loud promise"})
check("the platform's line changing makes it stale", any("platform has changed" in r for r in pv.stale_because(fresh, house, current_platform())), "")
stamped_before = fresh["generated_under"]
resaved = pv.apply_edit(fresh, {"name": fresh["name"]}, house, current_platform())
check("a save that changes nothing does NOT clear the warning (the stamp is kept)", resaved["generated_under"] == stamped_before and pv.stale_because(resaved, house, current_platform()), "")
reviewed = pv.apply_edit(fresh, {"name": "Reviewed and renamed"}, house, current_platform())
check("an edit re-stamps it: the person has just reviewed it against what is there now", pv.stale_because(reviewed, house, current_platform()) == [], "")
house["nodes"]["core"]["options"] = [{"id": "c1", "text": "A brand-new core message"}]
house["nodes"]["core"]["chosen"] = ["c1"]
strategy.save(house)
check("the house changing makes it stale", any("house has changed" in r for r in pv.stale_because(reviewed, house, current_platform())), "")
check("the chosen platform going away is said", any("no longer the chosen" in r for r in pv.stale_because(reviewed, house, None)), "")
check("an archived one is not judged", pv.stale_because(pv.archive(reviewed), house, current_platform()) == [], "")
no_plat = pv.save(pv.apply_edit(None, {**good(), "house": HID, "platform": ""}, house, current_platform()))
check("one with no platform is not told its platform went missing", not any("platform" in r for r in pv.stale_because(no_plat, house, None)), "")

print("the stands_on seam: nothing changes without a provocation")
PLAT = {"idea": "PLATFORM LINE", "expressions": {"video": "PLATFORM VIDEO"}}
CAMP = {"expressions": {"video": "CAMPAIGN VIDEO"}}
HOUSE = {"nodes": {"core": {"options": [{"id": "a", "text": "HOUSE CORE"}], "chosen": ["a"]}, "medium": {"options": [], "chosen": []}}, "brand_mode": "grounded"}
APPROVED = {"status": "approved", "name": "Quiet", "core": {"line": "PROV LINE"}, "expressions": {"video": "PROV VIDEO"}}
expected = {
    ("video", True, True, True): ("CAMPAIGN VIDEO", "the campaign, adapted for video"),
    ("social", True, True, True): ("PLATFORM LINE", "the idea platform"),
    ("video", False, True, True): ("PLATFORM VIDEO", "the idea platform, expressed for video"),
    ("video", False, False, True): ("HOUSE CORE", "the house's core message"),
    ("video", False, False, False): ("typed text", "typed here"),
}
for (kind, camp_on, plat_on, house_on), want in expected.items():
    got = producers.stands_on(kind, HOUSE if house_on else None, PLAT if plat_on else None, "typed text", campaign=CAMP if camp_on else None)
    check(f"{kind} with campaign={camp_on} platform={plat_on} house={house_on} is unchanged", got == want, str(got))
check("a typed override still wins over everything, as before",
      producers.stands_on("video", HOUSE, PLAT, "mine", force_typed=True, campaign=CAMP, provocation=APPROVED)[0] == "mine", "")
check("with no provocation passed, the answers are identical to passing None",
      all(producers.stands_on(k, HOUSE, PLAT, "t", campaign=CAMP) == producers.stands_on(k, HOUSE, PLAT, "t", campaign=CAMP, provocation=None) for k in ("video", "social", "posm", "activation")), "")

print("the stands_on seam: an approved provocation is the most deliberate decision in the chain")
t, src = producers.stands_on("video", HOUSE, PLAT, "", campaign=CAMP, provocation=APPROVED)
check("it wins over the campaign, the platform and the house, for its own medium", t == "PROV VIDEO" and src.startswith("the provocation") and "Quiet" in src and "video" in src, f"{t} / {src}")
t, src = producers.stands_on("social", HOUSE, PLAT, "", campaign=CAMP, provocation=APPROVED)
check("a medium it has no expression for gets its line", t == "PROV LINE", f"{t} / {src}")
check("a draft is ignored", producers.stands_on("video", HOUSE, PLAT, "", campaign=CAMP, provocation={**APPROVED, "status": "draft"})[0] == "CAMPAIGN VIDEO", "")
check("an archived one is ignored", producers.stands_on("video", HOUSE, PLAT, "", campaign=CAMP, provocation={**APPROVED, "status": "archived"})[0] == "CAMPAIGN VIDEO", "")
check("switched off for this piece, it is ignored", producers.stands_on("video", HOUSE, PLAT, "", campaign=CAMP, provocation=APPROVED, use_provocation=False)[0] == "CAMPAIGN VIDEO", "")
check("an Independent piece never stands on it", producers.stands_on("video", HOUSE, PLAT, "", campaign=CAMP, provocation=APPROVED, brand_mode="general")[0] == "", "")
check("one with nothing to say falls through to the campaign",
      producers.stands_on("video", HOUSE, PLAT, "", campaign=CAMP, provocation={"status": "approved", "core": {"line": ""}, "expressions": {}})[0] == "CAMPAIGN VIDEO", "")

print("routes")
from starlette.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})
# the route cases get a house of their own, so the unit cases above leave nothing in its lists
RH_house = strategy.new_house("RouteBrand")
RH = RH_house["id"]
rset = ideas.add(ideas.new_set("RouteBrand", RH), {"idea": "Route line", "mechanic": "A device", "expressions": {"video": "PLATFORM VIDEO"}})
RPLAT = rset["platforms"][0]["id"]
ideas.choose(rset, RPLAT)
r = client.post("/provocation", json={"name": "No house"})
check("a provocation needs a house", r.status_code == 400, r.text[:160])
r = client.post("/provocation", json={"house": "nosuchhouse", "name": "x"})
check("an unknown house is refused", r.status_code == 400, r.text[:160])
r = client.post("/provocation", json={"house": RH, "name": "Route one", "core": {"line": "A line.", "risk": "low", "message": "Route line", "device": "demonstration"}, "expressions": {"video": "ROUTE VIDEO"},
                                      "status": "approved", "approved_by": "Me"})
check("creating answers with a draft, the chosen platform filled in, and the hard limits", r.status_code == 200 and r.json()["status"] == "draft" and r.json()["platform"] == RPLAT and len(r.json()["hard_limits"]) == 4, r.text[:200])
check("status and approval cannot be sent in", r.json()["approved_by"] == "", "")
PID = r.json()["id"]
r = client.get("/provocations", params={"house": RH})
check("the list shows it, with nothing stale and nothing blocking approval", r.status_code == 200 and len(r.json()["provocations"]) == 1 and r.json()["provocations"][0]["stale_because"] == [] and r.json()["provocations"][0]["problems"] == [], r.text[:200])
check("another house's list is empty", client.get("/provocations", params={"house": other["id"]}).json()["provocations"] == [], "")
check("no house given: nothing, not everything", client.get("/provocations").json()["provocations"] == [], "")
check("an unknown id is a 404", client.get("/provocation", params={"id": "nope"}).status_code == 404 and client.post("/provocation-approve", json={"id": "nope"}).status_code == 404, "")
r = client.post("/provocation", json={"house": RH, "name": "Incomplete"})
bad = client.post("/provocation-approve", json={"id": r.json()["id"], "who": "Asha"})
check("approving an incomplete one is refused with the reasons", bad.status_code == 400 and len(bad.json()["problems"]) >= 2, bad.text[:200])
r = client.post("/provocation-approve", json={"id": PID, "who": "Asha"})
check("approving a complete one works and records who", r.status_code == 200 and r.json()["status"] == "approved" and r.json()["approved_by"] == "Asha", r.text[:200])
r = client.post("/provocation", json={"id": PID, "core": {"line": "A changed line.", "risk": "low", "message": "Route line", "device": "demonstration"}})
check("editing it puts it back to a draft", r.status_code == 200 and r.json()["status"] == "draft", r.text[:200])
r = client.post("/provocation", json={"id": PID, "house": other["id"], "name": "Route one"})
check("sending another house with an id does not move it", r.status_code == 200 and r.json()["house"] == RH, r.text[:200])
client.post("/provocation-approve", json={"id": PID, "who": "Asha"})
scratch = client.post("/provocation", json={"house": RH, "name": "Scratch"}).json()["id"]
check("garbage in an edit is survived", client.post("/provocation", json={"id": scratch, "core": "x", "film": 5, "expressions": [1]}).status_code == 200, "")
client.post("/provocation-approve", json={"id": PID, "who": "Asha"})

print("what a producer's card reads")
base_body = {"kind": "video", "house": RH, "platform": None}
r0 = client.post("/producer-stands-on", json=base_body)
check("with no provocation named, the answer is the platform's, as before", r0.status_code == 200 and r0.json()["text"] == "PLATFORM VIDEO" and r0.json()["has_provocation"] is False, r0.text[:200])
r1 = client.post("/producer-stands-on", json={**base_body, "provocation_id": PID})
check("naming an approved one makes the piece stand on it, and says so", r1.json()["source"].startswith("the provocation") and r1.json()["has_provocation"] is True, r1.text[:240])
r2 = client.post("/producer-stands-on", json={**base_body, "provocation_id": PID, "use_provocation": False})
check("switched off for this piece, it is the platform again", r2.json()["text"] == "PLATFORM VIDEO" and r2.json()["has_provocation"] is True, r2.text[:200])
client.post("/provocation-approve", json={"id": PID, "who": "Asha", "on": False})
r3 = client.post("/producer-stands-on", json={**base_body, "provocation_id": PID})
check("withdrawn, it stops applying at once", r3.json()["text"] == "PLATFORM VIDEO" and r3.json()["has_provocation"] is False, r3.text[:200])
client.post("/provocation-approve", json={"id": PID, "who": "Asha"})
r4 = client.post("/producer-stands-on", json={"kind": "video", "house": other["id"], "provocation_id": PID})
check("another house cannot stand on it", r4.json()["has_provocation"] is False and "provocation" not in r4.json()["source"], r4.text[:200])

print("the Video flag saved with the film")
rows = [{"no": 1, "tc": "0-8s", "visual": "x", "audio": []}]
client.post("/video-script", json={"house": RH, "full_script": rows, "provocation_id": PID, "provocation_on": False})
back = client.get("/video-script", params={"house": RH}).json()
check("the provocation a film stands on, and whether it is switched on, come back", back.get("provocation_id") == PID and back.get("provocation_on") is False, str(back.get("provocation_id")))
client.post("/video-script", json={"house": RH, "full_script": rows})
back = client.get("/video-script", params={"house": RH}).json()
check("a page from before the fields existed does not blank them", back.get("provocation_id") == PID and back.get("provocation_on") is False, "")
check("a house with nothing saved reads 'none, switched on'", client.get("/video-script", params={"house": "nobody"}).json().get("provocation_id") == "" and client.get("/video-script", params={"house": "nobody"}).json().get("provocation_on") is True, "")
client.post("/video-script", json={"house": RH, "full_script": rows, "provocation_id": 5, "provocation_on": "no"})
check("junk types are made safe", isinstance(client.get("/video-script", params={"house": RH}).json().get("provocation_id"), str), "")

print()
print("All provocation cases behave." if not fails else f"{fails} provocation case(s) FAILED.")
sys.exit(1 if fails else 0)
