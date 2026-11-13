#!/usr/bin/env python
"""test_craft_grammar.py -- film GRAMMARS (api/craft_grammar.py + api/craft_skill/grammars/*.md): how one KIND of film is shot and shown.

Proves, offline (no model, no network, every write in a scratch data directory):
  - a grammar is chosen from the brand's category (beauty words), by the person's own pick, or not at all, and a category with no grammar written yet is untouched;
  - with a grammar the general notes it contradicts are left out and its own text follows; without one the craft block is exactly what it was;
  - nothing changes unless craft mode is on (server switch AND request flag), Independent (general) work never gets a grammar;
  - the page asks the server for the grammar and the route/speech wording follows it; a bad or missing grammar folder never raises.

    api/.venv/Scripts/python.exe tools/test_craft_grammar.py      # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import re
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="craftgrammar_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
os.environ["GOOGLE_API_KEY"] = "test-key"
os.environ["CRAFT_BRIEF"] = "1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "api")
sys.path.insert(0, API)
os.chdir(API)

import craft                      # noqa: E402
import craft_grammar as cg        # noqa: E402
import prompts                    # noqa: E402

fails: list[str] = []


def check(name: str, cond: bool, extra: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond:
        fails.append(name)


def heads(t: str) -> list[str]:
    return [l for l in t.splitlines() if l.startswith("## ")]


# ---- choosing -------------------------------------------------------------------------------------------------
for cat in ("Beauty", "make-up", "Makeup", "Color cosmetics", "skincare", "Skin care", "Skin & hair care", "BEAUTY & PERSONAL CARE"):
    check(f"category {cat!r} gets the beauty grammar", cg.pick({"category": cat})[0] == "beauty", str(cg.pick({"category": cat})))
for cat in ("Personal care", "dairy", "cement", "apparel", "Home insecticide", "Foundation (building)", "packaged food", ""):
    check(f"category {cat!r} gets none (its grammar is not written yet): the general notes stand", cg.pick({"category": cat})[0] == "", str(cg.pick({"category": cat})))
check("no brand at all: none", cg.pick(None)[0] == "" and cg.pick({})[0] == "")
check("the person's own pick wins over the category", cg.pick({"category": "dairy"}, "beauty")[0] == "beauty" and cg.pick({"category": "beauty"}, "general")[0] == "")
check("an unknown pick is ignored and the category decides", cg.pick({"category": "beauty"}, "nonsense")[0] == "beauty" and cg.pick({"category": "dairy"}, "nonsense")[0] == "")
check("the reason is given in words", "category" in cg.pick({"category": "beauty"})[1] and "chose" in cg.pick({"category": "dairy"}, "beauty")[1])

# ---- the craft block ------------------------------------------------------------------------------------------
GEN = craft.for_prompt(True)
BEAUTY = craft.for_prompt(True, brand={"category": "beauty"})
check("general block: unchanged shape, 'Make it live' and 'Proposition moves' present", {"## Make it live", "## Proposition moves"} <= {h.split(" (")[0] for h in heads(GEN)})
check("a category with no grammar: the block is exactly the general one", craft.for_prompt(True, brand={"category": "dairy"}) == GEN and craft.for_prompt(True, brand=None) == GEN)
check("beauty block: the two general sections the grammar replaces are gone", not any(h.startswith(("## Make it live", "## Proposition moves")) for h in heads(BEAUTY)), str(heads(BEAUTY)))
check("beauty block: the tests, shape and pace, sound and guards still apply", all(any(h.startswith(x) for h in heads(BEAUTY)) for x in ("## The tests", "## Shape and pace", "## Sound", "## Guards")))
check("beauty block: the general opening paragraph about people who want something and talk is replaced", "people who want something, something in their way, others who react, and talk" not in BEAUTY
      and "A beauty film delivers it through what is SEEN" in BEAUTY)
check("beauty block: carries the grammar (looked at, macro, honest light, no bets or sceptics proved wrong, no unsourced hours)", all(x in BEAUTY for x in ("LOOKED AT", "macro", "honest skin", "bet, a wager", "sceptic who is proved wrong", "no number of hours or days")))
check("beauty block is longer than the general one by about the grammar's text, and stays under 9,000 characters", len(GEN) < len(BEAUTY) < 9000, (len(GEN), len(BEAUTY)))
check("the general craft text no longer names 'an elder' as the example third person (the dairy-era habit)", "an elder" not in GEN.split("## Make it live")[1].split("## Proposition moves")[0])
check("pick by hand: a dairy brand told 'beauty' gets it; a beauty brand told 'general' gets the general block",
      "BEAUTY AND SKIN" in craft.for_prompt(True, brand={"category": "dairy"}, grammar="beauty") and craft.for_prompt(True, brand={"category": "beauty"}, grammar="general") == GEN)

# ---- nothing changes unless craft mode is on ------------------------------------------------------------------
MSGS = [{"role": "user", "content": "Write a video script for a 30 second film about a lipstick. Scenes and voiceover please."}]
B = {"name": "Kumkum", "category": "beauty", "tone": "warm"}
os.environ["CRAFT_BRIEF"] = "1"
base = prompts.system_for(MSGS, brand=B)
check("craft flag not sent: the prompt is byte-identical to one with no craft argument, whatever the category", prompts.system_for(MSGS, brand=B, film=True, craft=False) == prompts.system_for(MSGS, brand=B, film=True))
on = prompts.system_for(MSGS, brand=B, film=True, craft=True)
check("craft on + beauty brand: the system prompt carries the beauty grammar", "BEAUTY AND SKIN" in on and "FILM CRAFT NOTES" in on)
check("craft on + the person picks general: the grammar is not there", "BEAUTY AND SKIN" not in prompts.system_for(MSGS, brand=B, film=True, craft=True, craft_grammar="general"))
check("Independent (general-mode) work has no brand, so no grammar", "BEAUTY AND SKIN" not in prompts.system_for(MSGS, brand=B, brand_mode="general", film=True, craft=True))
os.environ.pop("CRAFT_BRIEF")
check("server switch off: nothing is added even with the flag and a beauty brand", "BEAUTY AND SKIN" not in prompts.system_for(MSGS, brand=B, film=True, craft=True) and prompts.system_for(MSGS, brand=B, film=True, craft=True) == prompts.system_for(MSGS, brand=B, film=True))
os.environ["CRAFT_BRIEF"] = "1"

# ---- the page's view and the route ----------------------------------------------------------------------------
v = cg.view({"category": "beauty"})
check("view: id, label, why, options and every piece of wording the page replaces", v["id"] == "beauty" and v["label"] == "Beauty and skin" and v["why"]
      and any(o["id"] == "beauty" for o in v["options"]) and all(v[k] for k in ("routes_stand", "routes_stand_free", "routes_alive", "speech_note", "script_note")) and v["vo_mult"] == 1.0, str(v)[:300])
check("view for a category with no grammar: empty wording, still lists the options", cg.view({"category": "dairy"})["id"] == "" and cg.view({"category": "dairy"})["routes_alive"] == "" and cg.view({"category": "dairy"})["options"])
check("the routes wording leaves out stunts: no 'bet', 'dare' or 'swap' prompt in it, and says 'hero image'", all(w not in (v["routes_stand"] + v["routes_alive"]).replace("a bet, a wager, a test or a sceptic proved wrong is not", "") for w in ("a dare", "a race", "a swap")) and "hero image" in v["routes_stand"])

import main                       # noqa: E402
import brandprofile               # noqa: E402
brandprofile.put({"name": "Kumkum Beauty", "category": "Beauty", "market": "India", "positioning": "Real radiance"})
r = main.craft_grammar_get(brand="Kumkum Beauty")
check("GET /craft-grammar by brand name: the beauty grammar, with the switch state", r["id"] == "beauty" and r["craft_on"] is True and r["options"])
check("GET /craft-grammar with the pick 'general' or in Independent mode: none", main.craft_grammar_get(brand="Kumkum Beauty", grammar="general")["id"] == ""
      and main.craft_grammar_get(brand="Kumkum Beauty", brand_mode="general")["id"] == "")
check("GET /craft-grammar with a brand that is not on file falls back to the active brand and never raises", isinstance(main.craft_grammar_get(brand="Nobody At All"), dict))

# ---- the files themselves -------------------------------------------------------------------------------------
raw = open(os.path.join(cg._DIR, "beauty.md"), encoding="utf-8").read()
check("beauty.md has every section the page and the prompt read", all(("## " + s) in raw for s in ("FILM", "INTRO", "ROUTES_STAND", "ROUTES_STAND_FREE", "ROUTES_ALIVE", "SPEECH", "SCRIPT")))
NAMES = ["cadbury", "surf excel", "oral-b", "good knight", "godrej", "mother dairy", "cred ", "tata sky", "flipkart", "nykaa", "lakme", "maybelline", "heritage", "kumkum"]
hits = [n for n in NAMES if re.search(r"\b" + re.escape(n.strip()) + r"\b", raw.lower())]
check("ORIGINAL-SAFE: the grammar names no brand, reference ad or client", not hits, hits)
check("the beauty grammar is short enough to review in one sitting (FILM under 5,000 characters)", 0 < len(cg.block("beauty")) < 5000, len(cg.block("beauty")))

real = cg._DIR
cg._DIR = os.path.join(_scratch, "no-such-folder")
cg._cache["sig"] = None
check("a missing grammar folder means no grammar and never raises", cg.pick({"category": "beauty"})[0] == "" and craft.for_prompt(True, brand={"category": "beauty"}) == GEN and cg.options() == [])
os.makedirs(cg._DIR)
open(os.path.join(cg._DIR, "bad.md"), "w", encoding="utf-8").write("no front matter here\n## FILM\nx")
open(os.path.join(cg._DIR, "empty.md"), "w", encoding="utf-8").write("---\nlabel: no id\n---\n## FILM\nx")
cg._cache["sig"] = None
check("a malformed grammar file is skipped, not fatal", cg.options() == [] and cg.pick({"category": "beauty"})[0] == "")
cg._DIR = real
cg._cache["sig"] = None
SC = cg.get("beauty")["sections"].get("SCRIPT", "")
check("beauty SCRIPT: stake shown as something seen, show before say, the closing shot glorifies the pack, one place is fine, limbs safe, and it stays under 4,000 characters", all(x in SC for x in ("stake", "Show before you say", "glorifies the pack or range", "one place is fine", "Keep limbs safe")) and len(SC) < 4000, len(SC))
check("beauty SPEECH replaces the general dialogue preference for a person alone on screen", "CASTING THE SOUND" in cg.get("beauty")["sections"]["SPEECH"] and "ALONE" in cg.get("beauty")["sections"]["SPEECH"])
check("beauty ROUTES_STAND keeps the platform's own turn and does not break the limb rule", "names a specific turn" in cg.get("beauty")["sections"]["ROUTES_STAND"] and "without the hand crossing the face" in cg.get("beauty")["sections"]["ROUTES_STAND"])
check("beauty SCRIPT: the voice and the super never repeat each other, one scene = one action and one camera view, scene 1 shows motion in its first second", all(x in SC for x in ("never say the same words", "one action and one camera view", "Scene 1 shows motion in its first second")), SC[:80])
check("beauty routes: a signature ingredient or making is named in the message line and made visible in the move (both route wordings), brand-agnostic", all("signature ingredient" in cg.get("beauty")["sections"][k] and "\"message\" line NAMES it" in cg.get("beauty")["sections"][k] for k in ("ROUTES_STAND", "ROUTES_STAND_FREE")))
check("the real folder loads again", cg.pick({"category": "beauty"})[0] == "beauty")

# ---- the page -------------------------------------------------------------------------------------------------
html = open(os.path.join(API, "frontend", "app.dc.html"), encoding="utf-8").read()
check("the page reads GET /craft-grammar, picks the wording from it and offers the selector", "/craft-grammar?brand=" in html and "craftGrammarNow()" in html and "{{ onCraftGrammar }}" in html and "craft_grammar:" in html)
check("the page asks for the grammar before it writes a concept and before it writes a script", html.count("await this.ensureCraftGrammar();") == 2)
check("the page's general craft wording no longer names an elder or the dairy examples", "an elder" not in html.split("MAKE EACH ROUTE ALIVE")[1][:900] and "cold crate" not in html and "network of farmers" not in html)
check("the speech budget uses the grammar's multiplier and note", "gm.vo_mult" in html and "gm.speech_note" in html)
check("a route card with no hook says so (the guard)", "No hook was written for this route" in html and "!String((c && c.hook) || '').trim()" in html)
check("the script writer is given the grammar's SCRIPT notes (through craftWriterText, only when a grammar applies)", "gm.script_note" in html and html.count("this.craftWriterText(vc)") == 1)

# ---- still photographs (the PHOTO section, /scene-still for Social and Carousel) --------------------------------
import gemini                     # noqa: E402
PH = craft.photo_for_prompt(True, brand={"category": "beauty"})
check("photo: a beauty brand gets the PHOTO notes (register clean/bold/natural, real skin texture, no lettering or packaging drawn)", all(x in PH for x in ("clean, bold or natural", "real texture", "No lettering and no packaging")), PH[:120])
check("photo: the person's pick works as it does for film, and 'general' gives none", "clean, bold or natural" in craft.photo_for_prompt(True, brand={"category": "dairy"}, grammar="beauty") and craft.photo_for_prompt(True, brand={"category": "beauty"}, grammar="general") == "")
check("photo: no grammar for the category, or no brand, or craft flag off: nothing", craft.photo_for_prompt(True, brand={"category": "dairy"}) == "" and craft.photo_for_prompt(True, brand=None) == "" and craft.photo_for_prompt(False, brand={"category": "beauty"}) == "")
os.environ.pop("CRAFT_BRIEF")
check("photo: server switch off: nothing even with the flag", craft.photo_for_prompt(True, brand={"category": "beauty"}) == "")
os.environ["CRAFT_BRIEF"] = "1"
check("photo: the PHOTO section is short enough to review (under 3,000 characters) and names no brand or reference ad", 0 < len(PH) < 3000 and not [n for n in NAMES if re.search(r"\b" + re.escape(n.strip()) + r"\b", PH.lower())])

_cap: dict = {}
main._have_image = lambda: True
main._use = lambda eng, name: name == "google"
gemini.image_from_reference = lambda prompt, refs, **kw: (_cap.__setitem__("prompt", prompt) or "http://x/f.png")
gemini.image = lambda prompt, **kw: (_cap.__setitem__("prompt", prompt) or "http://x/f.png")


def still(payload: dict) -> str:
    _cap.clear()
    main.scene_still({"prompt": "a face in soft light", "style": "real", "engines": {"image": "google"}, **payload})
    return _cap.get("prompt", "")


MARK = "HOW THIS KIND OF PHOTOGRAPH IS SHOT"
brandprofile.set_active(brandprofile.by_name("Kumkum Beauty")["id"])
base_p = still({})
check("scene-still: a plain static call (no craft flag) is untouched", MARK not in base_p and bool(base_p))
cur = brandprofile.resolve()
check("scene-still: precondition, the active brand is a beauty brand", bool(cur) and "beauty" in str(cur.get("category", "")).lower(), str(cur)[:80])
on_p = still({"craft": True})
check("scene-still: craft flag + beauty brand: the static image prompt carries the PHOTO notes", MARK in on_p and "clean, bold or natural" in on_p, on_p[-200:])
check("scene-still: with craft the prompt is the plain one plus the notes, nothing else moved", on_p.replace(" " + MARK + ": " + PH, "") == base_p and len(on_p) > len(base_p), on_p[-160:])
check("scene-still: a film frame never gets them (it follows its script)", MARK not in still({"craft": True, "video_frame": True}))
check("scene-still: Independent (general) mode never gets them", MARK not in still({"craft": True, "brand_mode": "general"}))
check("scene-still: the person's pick 'general' removes them", MARK not in still({"craft": True, "craft_grammar": "general"}))
os.environ.pop("CRAFT_BRIEF")
check("scene-still: server switch off: byte-identical to the plain call", still({"craft": True}) == base_p)
os.environ["CRAFT_BRIEF"] = "1"
check("the page sends the craft fields on all four Social/Carousel still calls and defines them once", html.count("...this.photoCraftFields(),") == 4 and "photoCraftFields(){" in html)

check("the server tells the page whether its craft switch is on (on)", main.studio_settings_get().get("craft_available") is True)
os.environ.pop("CRAFT_BRIEF")
check("the server tells the page whether its craft switch is on (off)", main.studio_settings_get().get("craft_available") is False)
os.environ["CRAFT_BRIEF"] = "1"
check("the page hides the Craft mode tick and keeps craft off until the server says on",
      '<sc-if value="{{ craftAvail }}"' in html and "craftOn: false," in html and "craftOn: avail && want" in html and "if (!this.state.craftAvail) return;" in html)
check("film and POSM pickers read this brand's library items and every pack/cast/location upload tags the brand",
      html.count("/library?for_brand=1") >= 3 and html.count("fd.append('scope_brand', '1')") >= 4)

# ---- 13 Nov, items 6 and 7: the stake must be SEEN BY THE CAMERA (SCRIPT rule + FRAME section reaching film frames), and the page re-reads the grammar every time ----------------------------------
import craft_grammar  # noqa: E402
bg = craft_grammar.get("beauty")
check("script rule: the stake is something the CAMERA SEES, named in the scene's own visual line in the first two scenes, with examples, and not as thought or voiceover",
      all(x in bg["sections"]["SCRIPT"] for x in ("the CAMERA SEES", "`visual` line", "first two scenes", "garment bag", "Not as her thought")), bg["sections"]["SCRIPT"][:200])
check("script rule: it keeps the concept's own stake (no swapping the object)", "Keep the concept's own stake" in bg["sections"]["SCRIPT"])
FR = craft.frame_for_prompt(True, brand={"category": "beauty"})
check("frame: a beauty brand gets the FRAME notes (the stake object drawn in frame, one view, nothing the scene does not name)", all(x in FR for x in ("names the stake", "not hidden behind the face", "One person, one action", "Nothing the scene does not name")), FR[:120])
check("frame: the pick works as for film; 'general', no grammar, no brand, craft flag off: nothing",
      craft.frame_for_prompt(True, brand={"category": "dairy"}, grammar="beauty") == FR and craft.frame_for_prompt(True, brand={"category": "beauty"}, grammar="general") == ""
      and craft.frame_for_prompt(True, brand={"category": "dairy"}) == "" and craft.frame_for_prompt(True, brand=None) == "" and craft.frame_for_prompt(False, brand={"category": "beauty"}) == "")
os.environ.pop("CRAFT_BRIEF")
check("frame: server switch off: nothing even with the flag", craft.frame_for_prompt(True, brand={"category": "beauty"}) == "")
os.environ["CRAFT_BRIEF"] = "1"
check("frame: the section is short enough to review (under 1,500 characters) and names no brand or reference ad", 0 < len(FR) < 1500 and not [n for n in NAMES if re.search(r"\b" + re.escape(n.strip()) + r"\b", FR.lower())])
check("frame: the view still hands the page its other notes untouched (script_note carries the new stake rule)", "the CAMERA SEES" in craft_grammar.view({"category": "beauty"}).get("script_note", ""))

# 13 Nov night: the closing pack shot must glorify the range (the Kumkum end frame was a cluttered table, a lifted bangle and a small range)
check("script rule: the closing shot glorifies the pack or range (only subject, clean surface, nothing competing, no hand lifting a prop)",
      all(x in bg["sections"]["SCRIPT"] for x in ("closing shot glorifies the pack or range", "ONLY subject", "clean surface", "Nothing competes", "no hand lifting")), bg["sections"]["SCRIPT"][:120])
check("frame rule: a closing pack scene is drawn as a product hero and wins over listed props",
      all(x in FR for x in ("closing pack scene is drawn as a product hero", "wins over any props", "no hand lifting anything")), FR[-300:])
check("frame notes stay under the review length and still name no brand", len(FR) < 2000 and not [n for n in NAMES if re.search(r"\b" + re.escape(n.strip()) + r"\b", FR.lower())], len(FR))
FMARK = "HOW THIS KIND OF FILM FRAME IS DRAWN"
fbase = still({"video_frame": True})
check("scene-still: a plain film frame (no craft flag) is untouched", FMARK not in fbase and bool(fbase))
fon = still({"video_frame": True, "craft": True})
check("scene-still: craft flag + beauty brand: the FILM FRAME prompt carries the FRAME notes", FMARK in fon and "names the stake" in fon, fon[-200:])
check("scene-still: with craft the frame prompt is the plain one plus the notes, nothing else moved", fon.replace(" " + FMARK + ": " + FR, "") == fbase and len(fon) > len(fbase), fon[-160:])
check("scene-still: a static photo never gets the frame notes, and a film frame never gets the photo notes", FMARK not in still({"craft": True}) and MARK not in fon)
check("scene-still: Independent (general) mode and the person's pick 'general' never get them", FMARK not in still({"video_frame": True, "craft": True, "brand_mode": "general"}) and FMARK not in still({"video_frame": True, "craft": True, "craft_grammar": "general"}))
os.environ.pop("CRAFT_BRIEF")
check("scene-still: server switch off: the film frame is byte-identical to the plain one", still({"video_frame": True, "craft": True}) == fbase)
os.environ["CRAFT_BRIEF"] = "1"
fb_src = html.split("  frameBody(idx, k = 0){")[1].split("  frameRecipe(idx, k = 0){")[0]
rec_src = html.split("  frameRecipe(idx, k = 0){")[1].split("  // WHY a frame is out of date")[0]
check("the page sends the craft fields with every film frame (frameBody), and the staleness recipe does not read them (no frame is reflagged by craft mode)",
      "video_frame:true, ...this.photoCraftFields()" in fb_src and "craft" not in rec_src.replace("camera_notes", "").replace("cast_", "").replace("craftGrammar", ""), rec_src[:400])
eg_src = html.split("  ensureCraftGrammar = async (force, on, pick) => {")[1].split("  onCraftGrammar = (e) =>")[0]
check("page: the grammar is re-read on every call (no tab-long cache), never from the HTTP cache, and a failed read keeps this brand's copy instead of dropping to the general notes",
      "if (!force && this._cgKey === key && this._cg) return;" not in eg_src and "{ cache: 'no-store' }" in eg_src and "if (this._cgKey === key && this._cg) return;" in eg_src)

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
