#!/usr/bin/env python
"""test_provocation_complete.py -- a piece that stands on an approved provocation is WRITTEN FROM it (P2, Video first).

Tests the server half: `prompts.system_for(..., provocation=)`, the `/complete` route resolving `provocation_id`, and that with no
provocation named the system prompt is exactly what it was. The model is never called (a key is not even present). What the page sends
is covered by driving the real page, not here. Scratch data folder, set before anything is imported.

    python tools/test_provocation_complete.py     # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="provcomplete_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import brandprofile          # noqa: E402
import ideas                 # noqa: E402
import prompts               # noqa: E402
import provocation as pv     # noqa: E402
import selfcheck             # noqa: E402
import strategy              # noqa: E402

fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


# ---------------------------------------------------------------- fixtures
brandprofile.save({"id": "tb1", "name": "TestBrand", "category": "packaged milk", "tone": "warm, wholesome, reassuring",
                   "competitors": ["Amul"], "banned_words": ["miracle"], "avoid": ["use cartoon animals"],
                   "claims": [{"claim": "Sourced from 3,000 local farms", "proof": "procurement records"}], "regulator": "FSSAI"})
prof = brandprofile.resolve(None, None)
house = strategy.new_house("TestBrand")
HID = house["id"]
other = strategy.new_house("OtherBrand")
pset = ideas.add(ideas.new_set("TestBrand", HID), {"name": "The small promise", "idea": "Every glass is a small promise", "mechanic": "A mark on the doorframe",
                                                   "expressions": {"video": "A milk truck idles at 2am outside the plant"}})
ideas.choose(pset, pset["platforms"][0]["id"])

REC = pv.normalise({"id": "p1", "house": HID, "name": "The Plain Glass", "status": "approved", "approved_by": "Asha",
                    "core": {"line": "Milk disappears into everything a family drinks, except the one glass that matters most.",
                             "message": "Strength is given in the plain first glass", "device": "absence", "device_note": "The plain glass is withheld until the end",
                             "tension": {"category_says": "Milk is an ingredient", "we_say": "The first glass is drunk as itself"},
                             "repeatable": "Milk disappears into everything. Except the first glass.",
                             "codes_broken": ["Milk is a commodity input", "The hero shot is the pack, logo forward"],
                             "act": "Pour plain at the shelf", "act_note": "Needs the business",
                             "stance": {"tone": "Quiet, observational", "humour": "None", "structure": "A montage that withholds"},
                             "risk": "low"},
                    "film": {"structure": "A mother's morning of milk vanishing into coffee", "humour": "Light", "visual_language": "Cream and white kitchen",
                             "sound_language": "No music through the montage", "cast_approach": "people", "vo_words": 18, "brand_beat": "Silence, then the line"}})
VIDEO_MSG = [{"role": "user", "content": "You are a film director at an ad agency. Propose a short film script. Return JSON with a logline and scenes."}]
DEPT_MSG = [{"role": "user", "content": "You are the Art department head. Base your plan on this APPROVED SCRIPT: scene one, a kitchen."}]
BRIEF_MSG = [{"role": "user", "content": "You are a brief writer. Write the brief for this request, single-minded."}]

print("with no provocation the system prompt is what it was")
a = prompts.system_for(VIDEO_MSG, brand=prof, house_id=HID)
b = prompts.system_for(VIDEO_MSG, brand=prof, house_id=HID, provocation=None)
check("naming none changes nothing at all (byte for byte)", a == b, "")
check("the ordinary prompt still carries the brand TONE and the conventional film arc", "TONE:" in a and "everyday setup" in a and "THE PROVOCATION" not in a, a[:300])

print("with an approved provocation")
p = prompts.system_for(VIDEO_MSG, brand=prof, house_id=HID, provocation=REC)
check("the brand TONE is gone (the provocation's stance replaces it)", "TONE:" not in p and "warm, wholesome" not in p, "")
check("the guardrails stay in full: banned words, never-do, claims, regulator", "miracle" in p and "use cartoon animals" in p and "3,000 local farms" in p and "FSSAI" in p, p[:600])
check("the conventional film arc is swapped for the provocation-aware film instructions",
      "a small tension or need" not in p and "single, human, spoken line" not in p and "PROVOCATION MODE" in p and "Do NOT impose the usual arc" in p, "")
check("the spine reaches the model: message, device and how it works, the tension, the repeatable line",
      "Strength is given in the plain first glass" in p and "Absence" in p and "withheld until the end" in p
      and "Milk is an ingredient" in p and "drunk as itself" in p and "Except the first glass" in p, "")
check("what it breaks is listed as NOT to be used", "do NOT use any of these" in p and "Milk is a commodity input" in p, "")
check("the film notes and the voice-over length reach the model", "FILM NOTES" in p and "No music through the montage" in p and "voice-over length: 18 words" in p and "cast approach: people" in p, "")
check("the act is given as the idea's proof and a stated promise, never a claim beyond it", "Pour plain at the shelf" in p and "never as a claim beyond it" in p, "")
check("the hard limits ride along", "No health claims" in p and "never a named rival" in p, "")
check("the house and the platform are still there (the provocation never changes what they say)", "Every glass is a small promise" in p, "")
check("the platform's EARLIER expressions are left out in provocation mode (a provocation may depart from them) but kept in the ordinary prompt",
      "already expressed elsewhere" in a and "A milk truck idles at 2am" in a and "already expressed elsewhere" not in p and "A milk truck idles at 2am" not in p, "")
check("the binding section names the provocation as its one exception, only when there is one",
      "The one exception is the PROVOCATION section" in p and "The one exception" not in a and "this section wins" in p, "")
check("the platform's own mechanic is still given", "A mark on the doorframe" in p, "")

print("surfaces and modes")
d = prompts.system_for(DEPT_MSG, brand=prof, house_id=HID, provocation=REC)
check("a department prompt gets the provocation and no TONE, and no video-block swap (it has no film surface)",
      "THE PROVOCATION" in d and "TONE:" not in d and "PROVOCATION MODE" not in d, "")
br = prompts.system_for(BRIEF_MSG, brand=prof, house_id=HID, provocation=REC)
check("a brief is never written from a provocation (it is upstream of any execution)", "THE PROVOCATION" not in br and "TONE:" in br, "")
g = prompts.system_for(VIDEO_MSG, brand=prof, brand_mode="general", house_id=HID, provocation=REC)
check("an Independent piece never stands on one", "THE PROVOCATION" not in g and "PROVOCATION MODE" not in g, "")
objects_rec = pv.normalise({**REC, "film": {**REC["film"], "cast_approach": "none"}})
check("the film notes' cast approach is in the prompt whichever it is", "cast approach: none" in prompts.system_for(VIDEO_MSG, brand=prof, house_id=HID, provocation=objects_rec), "")

print("the /complete route resolves the provocation honestly")
from starlette.testclient import TestClient  # noqa: E402

import main  # noqa: E402

os.environ.pop("ANTHROPIC_API_KEY", None)                 # `import main` loads .env, which can put a real key back
saved = pv.save(pv.normalise({**REC, "id": ""}))
PID = saved["id"]
draft = pv.save(pv.normalise({**REC, "id": "", "status": "draft", "approved_by": "", "name": "A draft"}))
foreign = pv.save(pv.normalise({**REC, "id": "", "house": other["id"], "name": "Someone else's"}))

seen = []
real_complete, real_has_key = main.completion.complete, main.completion.has_key
main.completion.has_key = lambda: True


def fake_complete(messages, **kw):
    seen.append(kw)
    return "stub reply"


main.completion.complete = fake_complete
client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})


def prov_given(**extra):
    seen.clear()
    r = client.post("/complete", json={"messages": VIDEO_MSG, "house_id": HID, **extra})
    return r.status_code, (seen[-1].get("provocation") if seen else "no call")


code, got = prov_given(provocation_id=PID)
check("an approved provocation of this house is passed on", code == 200 and got and got["id"] == PID and got["status"] == "approved", str(got)[:120])
code, got = prov_given()
check("with none named, none is passed", code == 200 and got is None, str(got))
code, got = prov_given(provocation_id=PID, use_provocation=False)
check("set aside for this piece, it is not passed", got is None, str(got))
code, got = prov_given(provocation_id=draft["id"])
check("a draft is not passed", got is None, str(got))
code, got = prov_given(provocation_id=foreign["id"])
check("another house's is not passed", got is None, str(got))
seen.clear()
client.post("/complete", json={"messages": VIDEO_MSG, "provocation_id": PID})
check("with no house open nothing is passed (an empty house resolves nothing)", seen and seen[-1].get("provocation") is None, "")
code, got = prov_given(provocation_id="nope")
check("an unknown id is not passed and does not break the call", code == 200 and got is None, str(got))
code, got = prov_given(provocation_id=PID, brand_mode="general")
check("on an Independent piece the route may resolve it, but the prompt builder ignores it (checked above)", code == 200, "")

main.completion.complete, main.completion.has_key = real_complete, real_has_key

print("the concept written from a provocation saves and comes back with the film")
rows = [{"no": 1, "tc": "0-8s", "visual": "x", "audio": []}]
concept = {"name": "The Plain Glass", "logline": "L", "scenes": [{"t": "0-5s", "title": "a", "desc": "b"}], "vo": "", "duration": "30s",
           "from_provocation": PID, "provocation_name": "The Plain Glass"}
client.post("/video-script", json={"house": HID, "video_concept": concept, "full_script": rows, "provocation_id": PID, "provocation_on": True})
back = client.get("/video-script", params={"house": HID}).json()
check("the concept keeps which provocation it came from, and the film keeps the pick", (back.get("video_concept") or {}).get("from_provocation") == PID
      and (back.get("video_concept") or {}).get("provocation_name") == "The Plain Glass" and back.get("provocation_id") == PID, str(back)[:200])
client.post("/video-script", json={"house": HID, "video_concept": {k: v for k, v in concept.items() if k not in ("from_provocation", "provocation_name")}, "full_script": rows})
back = client.get("/video-script", params={"house": HID}).json()
check("an ordinary concept (a normal route) has no provocation on it, so a later step is ordinary", "from_provocation" not in (back.get("video_concept") or {}), "")

print()
print("All provocation-in-/complete cases behave." if not fails else f"{fails} provocation-in-/complete case(s) FAILED.")
sys.exit(1 if fails else 0)
