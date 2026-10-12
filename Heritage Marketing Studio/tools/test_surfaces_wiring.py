#!/usr/bin/env python
"""test_surfaces_wiring.py -- Step 5 Surfaces 1, 2, 2b and 3, end to end through the REAL routes (model, image and music engines stubbed).

The other tests prove the wording. This proves the wiring around it: each changed text is reached by the route that is supposed to use it, the route
still answers with the shape the page reads, the brand's own answers still arrive next to it, a non-dairy brand sees no dairy, and the page sends the
fields the backend needs (the Video music/voice calls must say Independent mode, or the brand's sound world reaches an Independent film).

  Surface 1   POST /social-carousel-concept      carousel wording points at the brand's answers (Heritage keeps its specifics)
  Surface 2   POST /campaign-draft, /idea-draft, /plan-generate (channels), /brand-brief-draft     examples are from other categories
  IMC fix     POST /brand-brief-draft            a redraft with the screen's id corrects its row; without one it adds a row
  Surface 3   POST /music-options, /voice-plan, /scene-still, /produce-video    no dairy/family/premium defaults; sound world only when it is the brand's
  Page        the four calls that reach the music bed send brand_mode

    python tools/test_surfaces_wiring.py          # exit 0 = every case behaves
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import tempfile

os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="wiring_")
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.abspath(os.path.join(HERE, "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

import anthropic            # noqa: E402
import brandprofile as bp   # noqa: E402
import brief_ai             # noqa: E402
import briefstore           # noqa: E402
import ideas                # noqa: E402
import jsonout              # noqa: E402
import plan as plan_mod     # noqa: E402
import strategy             # noqa: E402
import main                 # noqa: E402
import selfcheck            # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

failures = 0


def expect(label, cond, detail=""):
    global failures
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  -> {str(detail)[:300]}"))
    if not cond:
        failures += 1


# ---- stubs: nothing is ever called ---------------------------------------------------------------------------------------------------------
CAP: list[str] = []
CANNED_CAROUSEL = {"routes": [{"name": "R1", "rationale": "r", "slides": [
    {"role": "hook", "headline": "H", "visual_note": "v", "shows_pack": False},
    {"role": "cta", "headline": "C", "visual_note": "v2", "shows_pack": True}]}]}


def _ask_json(prompt, *a, **k):
    """Records every prompt. A carousel concept gets a valid reply (so the route's own success shape can be checked); the rest fail quietly."""
    CAP.append(prompt)
    return (CANNED_CAROUSEL, "") if "carousel" in prompt.lower() and "visual_note" in prompt else (None, "stubbed")


jsonout.ask_json = _ask_json


class _M:
    def create(self, **kw):
        CAP.append((kw.get("system") or "") + "\n\n" + "\n".join(str(m.get("content")) for m in kw.get("messages", [])))
        raise RuntimeError("stubbed")


class _C:
    def __init__(self, *a, **k):
        self.messages = _M()


anthropic.Anthropic = _C
os.environ["ANTHROPIC_API_KEY"] = "never-used"
os.environ["FAL_KEY"] = "stub"
os.environ["GOOGLE_API_KEY"] = "stub"
IMG: list[str] = []
MUS: list[str] = []
VID: list[str] = []
main._have_image = lambda: True
main.gemini.image = lambda prompt, **k: (IMG.append(prompt) or "https://example.invalid/still.png")
main.gemini.image_from_reference = lambda prompt, refs, **k: (IMG.append(prompt) or "https://example.invalid/still.png")
main.gemini.available = lambda: True
main.gemini.music = lambda prompt, seconds=None, **k: (MUS.append(prompt) or "https://example.invalid/bed.mp3")
main._record_made = lambda *a, **k: None
main.creative.generate_creative = lambda model_id, prompt, *a, **k: (VID.append(prompt) or {})
main.creative.video_from_image = lambda model_id, prompt, *a, **k: (VID.append(prompt) or {})

client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})

# ---- two brands as the golden baseline froze them: a cement brand, and Heritage with its accepted starting answers ---------------------------
profiles = {}
for f in glob.glob(os.path.join(HERE, "golden_pre_nuance", "profiles", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    profiles[d["name"]] = bp.save(d)
# importing `main` seeds a first "Heritage Foods" profile of its own; two profiles with one name would let a route resolve the one without answers
import tenancy  # noqa: E402
_keep = {p["id"] for p in profiles.values()}
for _f in glob.glob(os.path.join(tenancy.dir("brands"), "*.json")):
    if os.path.basename(_f).startswith("_"):
        continue
    _d = json.load(open(_f, encoding="utf-8"))
    if _d.get("id") and _d["id"] not in _keep:
        bp.remove(_d["id"])
seed = bp.seed_answers(profiles["Heritage Foods"])
accepted = {k: v for k, v in seed.items() if k not in ("imagery_style", "meeting_points")}
heritage = bp.put({"name": "Heritage Foods", **accepted}, profiles["Heritage Foods"]["id"])


def build(name):
    """Make `name` the active brand and give it a house, an adopted platform and a plan with audiences. Returns their ids."""
    bp.set_active(profiles[name]["id"])
    house = strategy.new_house(name)
    house["nodes"]["core"]["options"] = [{"id": "c1", "text": "core"}]
    house["nodes"]["core"]["chosen"] = ["c1"]
    # a ladder path (functional truth -> bridge -> feeling): /campaign-draft refuses without one
    for node, oid in (("functional", "f1"), ("emotional", "e1"), ("bridge", "b1")):
        house["nodes"][node]["options"] = [{"id": oid, "text": f"{name} {node}"}]
        house["nodes"][node]["chosen"] = [oid]
    house["ladders"] = [{"id": "l1", "f": "f1", "e": "e1", "b1": "b1"}]
    strategy.save(house)
    pset = ideas.adopt(ideas.new_set(name, house["id"]), {"name": "p", "idea": "i", "mechanic": "m", "ladder": "l1"})
    p = plan_mod.new_plan(name, house["id"])
    p = plan_mod.add_row(p, "objectives", {"level": "business", "statement": "Grow", "measure": "share"})
    p = plan_mod.add_row(p, "audiences", {"audience": "Buyers", "rank": "1", "believes_now": "x", "pillar": "emotional"})
    plan_mod.save(p)
    return {"house": house["id"], "set": pset["id"], "plan": p["id"]}


def last(n=1):
    return "\n".join(CAP[-n:]) if CAP else ""


def run(path, body, **kw):
    CAP.clear()
    r = client.post(path, json=body, **kw)
    return r, "\n".join(CAP)


DAIRY = re.compile(r"milk|dairy|doodh|curd|paneer|ghee|ki shakti|telugu|hinglish|amul|hatsun|arokya|nandini|meet your farmer|topical girl", re.I)

for name, is_dairy in (("Sthir Cement", False), ("Heritage Foods", True)):
    print(f"\n=== {name} (active brand)")
    ids = build(name)

    print("Surface 1: the carousel concept route")
    r, t = run("/social-carousel-concept", {"house": ids["house"], "objective": "Brand awareness", "slide_count_mode": "auto", "brand_mode": "grounded"})
    expect("the route answers 200 with the shape the page reads (routes, count, note)", r.status_code == 200 and {"routes", "count", "note"} <= set(r.json()), r.text[:200])
    expect("the prompt points at the brand's own answers (HOW IT IS USED OR HANDLED / MUST BE VISIBLE) instead of naming milk",
           "HOW IT IS USED OR HANDLED in THE BRAND" in t and "MUST BE VISIBLE IN ANY IMAGE OF IT" in t)
    if is_dairy:
        expect("Heritage's specifics arrive from its answers (handling, the ring at the base, pack in the picture)",
               "carried at the side, handed over, tucked into a crate, set down on a counter" in t and "a ring at the base" in t and "PACK IN THE PICTURE: only when it is in use" in t)
    else:
        expect("a cement brand's carousel prompt carries no dairy", not re.search(r"milk|dairy|doodh|curd", t, re.I), re.search(r"milk|dairy|doodh|curd", t, re.I) and t[max(0, re.search(r'milk|dairy|doodh|curd', t, re.I).start() - 60):][:140])

    print("Surface 2: idea, campaign, plan channels")
    r, t = run("/idea-draft", {"house": ids["house"], "n": 1, "brand_mode": "grounded"})
    expect("/idea-draft reaches the model with the skill's other-category mechanic", "Every shirt carries the name of the mill that wove it" in t and "keep the city running" in t, r.status_code)
    r, t = run("/campaign-draft", {"set": ids["set"], "ladder": "", "brand_mode": "grounded"})
    expect("/campaign-draft prompt lists the four shapes with other-category examples and no mother-and-growth insight example",
           "The four shapes:" in t and "Share a Coke with {name}" in t and "Duracell bunny" in t and "Red Bull" in t and "Urban renters 25-35" in t
           and not re.search(r"ki Shakti|Meet Your Farmer|topical girl|pressure of his growth|learning matters more", t), (r.status_code, t[:80]))
    r, t = run("/plan-generate", {"id": ids["plan"], "layer": "channels"})
    expect("/plan-generate (channels) carries the audience-language example, not Telugu", "in the audience language" in t and "reel, Telugu" not in t, (r.status_code, t[:80]))

    print("Surface 4: POSM key-visual and mandatories")
    r, t = run("/posm-keyvisual", {"house": ids["house"], "brief": "", "n": 2, "brand_mode": "grounded"})
    expect("/posm-keyvisual answers 200 with routes and the stands-on shape the page reads", r.status_code == 200 and {"options", "stands_on", "layouts"} <= set(r.json()), r.text[:160])
    expect("the POSM opener says 'Indian retail', not 'Indian FMCG'", "Indian retail point-of-sale" in t and "Indian FMCG" not in t, t[t.find("Indian "):][:60])
    if is_dairy:
        expect("Heritage's own marks and routes answers reach the POSM prompt", "MARKS AND DECLARATIONS THAT MUST APPEAR" in t and "FSSAI" in t and "ROUTES TO MARKET" in t)
    else:
        expect("a cement brand's POSM prompt carries no dairy word", not re.search(r"milk|dairy|doodh|curd", t, re.I), re.search(r"milk|dairy|doodh|curd", t, re.I) and t[max(0, re.search(r'milk|dairy|doodh|curd', t, re.I).start() - 60):][:140])
    md = client.get("/posm-mandatories", params={"brand": name})
    expect("/posm-mandatories returns this brand's own declared mandatories", md.status_code == 200 and isinstance(md.json().get("mandatories"), list), md.text[:120])

    print("Surface 5: Onground activation")
    r, t = run("/activation-idea", {"house": ids["house"], "brand_mode": "grounded"})   # no 'idea' key -> generate, which builds the prompt
    expect("the activation prompt no longer hardcodes 'in India' / an 'Indian' activation (market comes from the brand block)",
           bool(t) and "activation in India" not in t and "activations in India" not in t and "Indian consumer activation" not in t, t[:120])
    expect("the brand's own meeting points reach the activation prompt", "WHERE PEOPLE MEET THE BRAND IN PERSON" in t or "VENUES YOU MAY USE" in t, t[:120])
    if not is_dairy:
        expect("a cement brand's activation prompt carries no dairy word", not re.search(r"milk|dairy|doodh|curd", t, re.I), re.search(r"milk|dairy|doodh|curd", t, re.I) and t[max(0, re.search(r'milk|dairy|doodh|curd', t, re.I).start() - 60):][:140])

print("\n=== Surface 2 + the IMC fix: /brand-brief-draft")
bp.set_active(profiles["Sthir Cement"]["id"])
CAP.clear()
r = client.post("/brand-brief-draft", data={"payload": json.dumps({"brand": "Sthir Cement", "category": "Cement", "prompt": "A brief for a cement brand"})})
t = "\n".join(CAP)
expect("the Brief's prompt carries the other-category worked example and no dairy example or example output values",
       "invented pressure-cooker brand" in t and "the platform name, in the brand's own words" in t and not re.search(r"Pure Doodh|dependable purity|chosen family strength|Hatsun/Arokya|Heritage Foods, dairy", t), r.status_code)
brief_ai.draft_brief = lambda base, research=None, images=None: {"brand": base.get("brand", ""), "title": "T", "smp": "S"}


def draft(**payload):
    r = client.post("/brand-brief-draft", data={"payload": json.dumps({"brand": "Sthir Cement", "category": "Cement", "prompt": "p", **payload})})
    return r.status_code, (r.json() or {}).get("brief_id")


def rows():
    return len(briefstore.briefs())


n0 = rows()
s1, a = draft()
s2, a2 = draft(brief_id=a)
n_after_redraft = rows()
s3, b = draft()
n_after_new = rows()
expect("a first draft saves a row and hands back its id", s1 == 200 and bool(a), (s1, a))
expect("a redraft that sends the screen's id corrects the SAME row (same id, no new row)", s2 == 200 and a2 == a and n_after_redraft == n0 + 1, (a, a2, n0, n_after_redraft))
expect("a draft with no id adds a new row (a new brief)", s3 == 200 and b and b != a and n_after_new == n0 + 2, (a, b, n0, n_after_new))

print("\n=== Surface 3: the Video side")
for name, answered in (("Heritage Foods", True), ("Sthir Cement", False)):
    bp.set_active(profiles[name]["id"])
    print(f"-- {name}")
    MUS.clear()
    r = client.post("/music-options", json={"style": "piano-ambient", "seconds": 10, "count": 1, "brand_mode": "grounded", "engines": {"music": "google"}})
    expect("/music-options answers 200 and a bed is made", r.status_code == 200 and MUS, (r.status_code, r.text[:160]))
    p = MUS[-1] if MUS else ""
    expect("grounded: the sound world is in the prompt only when the brand answered it",
           ("THE BRAND'S SOUND WORLD" in p and "bansuri" in p) if answered else ("SOUND WORLD" not in p), p[-260:])
    expect("and the prompt ends with the plain tail, no dairy, no premium", p.endswith("Instrumental score for a brand film. No vocals, no lyrics.") and not re.search(r"dairy|premium Indian", p), p[-160:])
    MUS.clear()
    client.post("/music-options", json={"style": "piano-ambient", "seconds": 10, "count": 1, "brand_mode": "general", "engines": {"music": "google"}})
    expect("Independent mode: the brand's sound world never reaches the music", MUS and "SOUND WORLD" not in MUS[-1], MUS[-1][-200:] if MUS else "no prompt")

bp.set_active(profiles["Sthir Cement"]["id"])
new_nar = client.post("/voice-plan", json={"scenes": [], "duration": "30s", "voice": ""})
old_nar = client.post("/voice-plan", json={"scenes": [], "duration": "30s", "voice": "Warm female (Telugu-accented English)"})
expect("/voice-plan with an empty voice answers exactly what the old default string did (same narrator, same plan)", new_nar.status_code == 200 and new_nar.json() == old_nar.json(),
       (new_nar.status_code, str(new_nar.json())[:120], str(old_nar.json())[:120]))

IMG.clear()
r = client.post("/scene-still", json={"prompt": "A mason checks a finished joint", "style": "real", "ratio": "3:4", "brand_mode": "grounded"})
expect("/scene-still answers 200 and its look carries no dairy, farm or premium", r.status_code == 200 and IMG and not re.search(r"milk|dairy|farm|food|premium|condensation", IMG[-1], re.I) and "50mm" in IMG[-1],
       (r.status_code, IMG[-1][:200] if IMG else "no prompt"))
VID.clear()
r = client.post("/produce-video", json={"scenes": [{"no": 1, "tc": "0-6s", "visual": "A mason checks a finished joint", "camera": "static", "audio": [{"type": "vo", "text": "A short line."}]}],
                                       "duration": "30s", "aspect": "16:9", "style": "real", "engines": {"video": "fal"}, "music": "warm", "brand_mode": "grounded"})
clip = VID[-1] if VID else ""
expect("a clip prompt is built, with no 'Indian family' or 'premium and wholesome' and with its silent-clip rules", bool(clip) and not re.search(r"Indian family|premium and wholesome|dairy", clip) and "No on-screen text or logos" in clip, clip[:200])

VID.clear()
client.post("/produce-video", json={"scenes": [{"no": 1, "tc": "0-6s", "visual": "A mason checks a finished joint", "camera": "static", "audio": [{"type": "vo", "text": "A short line."}]}],
                                    "duration": "30s", "aspect": "16:9", "style": "real", "engines": {"video": "fal"}, "music": "warm", "brand_mode": "general"})
gclip = VID[-1] if VID else ""
expect("Independent mode: the clip prompt does not name the active brand ('a brand' instead)", bool(gclip) and "Sthir" not in gclip and "brand film for a brand" in gclip, gclip[:160])

print("\n=== The page sends brand_mode on every call that reaches the music bed")
html = open(os.path.join(API, "frontend", "app.dc.html"), encoding="utf-8").read()


def region(start, end):
    i = html.find(start)
    j = html.find(end, i + 1)
    return html[i:j] if i >= 0 and j > i else ""


expect("/music-options", "brand_mode" in region("apiCall('/music-options', {", "});"))
expect("/rescore", "brand_mode" in region("apiCall('/rescore', {", "});"))
expect("the shared voice/preview payload (voicePayload)", "brand_mode" in region("return { scenes:this.state.fullScript||[], duration:this.state.prodDuration, voice:p.voice,", "};"))
expect("/produce-video", "brand_mode" in region("const body = { scenes:rows, aspect:p0.aspect", "apiCall('/produce-video', body)"))

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All surface-wiring cases behave.")
