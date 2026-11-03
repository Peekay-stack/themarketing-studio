#!/usr/bin/env python
"""test_craft_brief.py -- offline checks for workstream W0 of FILM_CRAFT_LAYER_PLAN.md: the film CRAFT BRIEF (api/craft.py + api/craft_skill/SKILL.md) rides in the system prompt of a film
concept/script call ONLY when the server switch CRAFT_BRIEF and the request's `craft` flag are both on, and otherwise every prompt is byte for byte what it was. No network, no model, nothing
written to the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_craft_brief.py
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import craft, prompts

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

MSGS = [{"role": "user", "content": "Write a video script for a 30 second film about a grandmother who tests milk at home. Scenes and voiceover please."}]
MARK = "FILM CRAFT NOTES"
BRAND = {"name": "Testco", "category": "dairy", "tone": "warm"}

def sp(**kw):
    return prompts.system_for(MSGS, brand=BRAND, **kw)

os.environ.pop("CRAFT_BRIEF", None)
base = sp()
check("switch OFF, flag not sent: the prompt is the same as with no craft argument at all", sp(craft=False) == base and sp(film=True) == sp(film=True, craft=False))
check("switch OFF, flag ON: nothing is added (the server decides)", sp(craft=True) == base and sp(film=True, craft=True) == sp(film=True) and MARK not in sp(film=True, craft=True))

for v in ("0", "", "off", "no"):
    os.environ["CRAFT_BRIEF"] = v
    check(f"switch set to {v!r} counts as OFF", MARK not in sp(film=True, craft=True))

for v in ("1", "true", "ON", "Yes"):
    os.environ["CRAFT_BRIEF"] = v
    check(f"switch set to {v!r} counts as ON", craft.server_on())

os.environ["CRAFT_BRIEF"] = "1"
on_film = sp(film=True, craft=True)
check("switch ON + flag ON + film: the craft block is in the system prompt", MARK in on_film and "One message." in on_film and "Proposition moves" in on_film)
check("switch ON + flag OFF: still nothing (the page must ask)", MARK not in sp(film=True) and MARK not in sp(film=True, craft=False))
check("switch ON + flag ON but NOT a film call and not the video surface: nothing is added",
      MARK not in prompts.system_for([{"role": "user", "content": "Write one LinkedIn post about our new curd."}], brand=BRAND, craft=True))
check("the block goes in without removing anything: every part of the OFF prompt is still there, in order",
      on_film.replace(on_film[on_film.index(MARK):], "") != "" and base.split("\n\n")[0] in on_film)
idx_craft, idx_video = on_film.index(MARK), on_film.rindex(prompts.VIDEO.strip()[:60]) if prompts.VIDEO.strip()[:60] in on_film else -1
check("the craft block sits BEFORE the video surface instructions (the instruction stays last and closest)", idx_video == -1 or idx_craft < idx_video, (idx_craft, idx_video))

body = craft._text()
check("the skill file loads without its front matter", body.startswith("# Film craft") and "name: film-craft" not in body)
check("the brief is short (under 9,000 characters) so it cannot bloat a film prompt", 0 < len(body) < 9000, len(body))
NAMES = ["cadbury", "surf excel", "oral-b", "oral b", "good knight", "godrej", "fevi", "pidilite", "mother dairy", "cred ", "sting", "tata sky", "uninor", "ipl", "flipkart", "bappi", "dravid", "akshay", "heritage"]
hits = [n for n in NAMES if re.search(r"\b" + re.escape(n.strip()) + r"\b", body.lower())]
check("ORIGINAL-SAFE: the brief names no reference ad, brand, star or the studio's own client", not hits, hits)
check("the brief states the director's-vision principle and the original-only guard", "director's vision decides" in body and "Original only" in body)
check("the brief carries the moves, the sound layers and the two honest sound builds", body.count("**") > 20 and "jingle film" in body and "voice-and-dialogue film" in body)

os.environ["CRAFT_BRIEF"] = "1"
f = os.path.join(craft._SKILL, "SKILL.md"); keep = f + ".keep"
os.rename(f, keep)
try:
    craft._cache["mtime"] = None
    check("a missing skill file does nothing (never raises, never blanks a prompt)", craft.for_prompt(True) == "" and MARK not in sp(film=True, craft=True))
finally:
    os.rename(keep, f); craft._cache["mtime"] = None
os.environ.pop("CRAFT_BRIEF", None)

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
