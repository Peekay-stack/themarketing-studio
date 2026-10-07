#!/usr/bin/env python
"""probe_brand_signatures.py -- the DYNAMIC half of the brand-agnostic audit (read only; not in the suite, because it reports gaps that exist today).

Builds each surface's REAL prompt for a cement brand (model stubbed, scratch data folder, nothing real called or written) and lists any dairy /
Heritage / Parle / India text that rides along and is not the brand's own profile. Rerun after a fix: a clean surface prints empty lists.
See BRAND_AGNOSTIC_AUDIT_OTHER_SURFACES.md.

    python tools/probe_brand_signatures.py
"""
import os, re, sys, tempfile

os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="probe_")      # BEFORE any import: a harness that imports first writes into the real tenant
os.environ["PYTHONUTF8"] = "1"
os.environ["ANTHROPIC_API_KEY"] = "probe-key-never-used"
API = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

CAP = []

import jsonout  # noqa: E402


def fake_ask(prompt, *a, **k):
    CAP.append(("jsonout", prompt))
    return None, "probe: model stubbed"


jsonout.ask_json = fake_ask

import anthropic  # noqa: E402


class _Msgs:
    def create(self, **kw):
        CAP.append(("anthropic", (kw.get("system") or "") + "\n\n" + "\n".join(str(m.get("content")) for m in kw.get("messages", []))))
        raise RuntimeError("probe: model stubbed")


class _Client:
    def __init__(self, *a, **k):
        self.messages = _Msgs()


anthropic.Anthropic = _Client

import brandprofile, strategy, ideas, producers, campaign, prompts  # noqa: E402,E401

STHIR = {"id": "sth1", "name": "Sthir Cement", "category": "Cement — building materials (OPC and PPC, bagged trade cement)",
         "market": "India, state-level markets weighted to semi-urban and rural", "hero_product": "Sthir PPC 50kg",
         "master_idea": "The bag your mason asks for by name", "positioning": "Consistent strength, bag after bag",
         "tone": "Straight, technical, respectful of the trade", "mandatories": ["BIS grade mark and IS number", "batch and packing date", "MRP on bag"],
         "competitors": ["UltraTech", "Ambuja", "ACC"], "avoid": ["never show unsafe site practice"], "regulator": "BIS"}
brandprofile.save(STHIR)
house = strategy.new_house("Sthir Cement")
house["nodes"]["core"]["options"] = [{"id": "c1", "text": "Strength you can build a house on"}]
house["nodes"]["core"]["chosen"] = ["c1"]
strategy.save(house)
pset = ideas.add(ideas.new_set("Sthir Cement", house["id"]), {"name": "The mason's bag", "idea": "The bag your mason asks for", "mechanic": "A name on the bag"})
ideas.choose(pset, pset["platforms"][0]["id"])
pset = ideas.for_house(house["id"])
platform = ideas.chosen_platform(pset)

SIG = re.compile(r"\b(milk|dairy|ghee|curd|paneer|cow|cows|heritage|doodh|amul|nandini|dodla|fssai|kirana|pouch|sachet|tetra|hinglish|ammamma|saree|parle|nivea|dabur)\b", re.I)
MKT = re.compile(r"\b(india|indian|hindi|telugu|devanagari|lakh|crore|diwali|rupee|rupees)\b|₹", re.I)


def run(name, fn):
    CAP.clear()
    try:
        fn()
    except Exception:                                       # noqa: BLE001 -- the stub raises on purpose
        pass
    if not CAP:
        print(f"[{name}] no prompt captured")
        return
    txt = "\n".join(p for _, p in CAP)
    for own in (STHIR["name"], STHIR["category"], STHIR["market"], STHIR["hero_product"], STHIR["master_idea"], STHIR["positioning"], STHIR["tone"]):
        txt = txt.replace(own, " ")                         # the brand's OWN profile text is grounding, not a leak
    sig = sorted({m.group(0).lower() for m in SIG.finditer(txt)})
    mkt = sorted({m.group(0).lower() for m in MKT.finditer(txt)})
    print(f"[{name}] prompts={len(CAP)} chars={len(txt)}  brand/category={sig}  market={mkt}")
    for m in list(SIG.finditer(txt))[:2]:
        print("      ..." + txt[max(0, m.start() - 90):m.start() + 80].replace("\n", " ") + "...")


import brief_ai  # noqa: E402

run("Brief builder (brief_ai)", lambda: brief_ai.draft_brief({"brand": "Sthir Cement", "category": "Cement", "request": "Launch a new PPC bag"}))
run("Messaging house (strategy.generate)", lambda: strategy.generate(house, "core"))
run("Idea platform draft prompt", lambda: CAP.append(("direct", ideas.draft_prompt("Strength you can build a house on", None, house))))
run("Campaign draft", lambda: campaign.draft(None, house))
run("Social system prompt", lambda: CAP.append(("direct", prompts.system_for([{"role": "user", "content": "You are a social media writer. platform-adapted posts."}], brand=STHIR, house_id=house["id"]))))
run("Carousel concept", lambda: producers.carousel_concept("Brand awareness", house, platform))
run("POSM key visual", lambda: producers.key_visual("A dealer board", house, platform=platform))
run("Onground activation ideas", lambda: producers.activation_ideas(house, platform))

import plan, sales  # noqa: E402

run("Campaign draft (with the platform set)", lambda: campaign.draft(pset, house))
_pl = plan.new_plan("Sthir Cement", house["id"])
run("IMC plan (plan.generate: objectives)", lambda: plan.generate(_pl, "objectives", house))
_sh = sales.new_sheet("Sthir Cement", "", house["id"])
run("Sales enabler (sales.generate: traditional retail)", lambda: sales.generate(_sh, "trad", house))
