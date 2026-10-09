#!/usr/bin/env python
"""golden_prompts.py -- capture, or compare against, the REAL prompt every surface builds for each dev brand.

Why it exists: the nuance-layer work (NUANCE_LAYER_PLAN.md) changes what goes into prompts in small steps.
Steps 1 and 2 must change NOTHING for a brand with no answers, and Step 5 must change exactly one surface at
a time. A saved copy of what each prompt was is the only thing that makes "nothing changed" provable.

Read only against the real data: it works in a scratch folder, with the model stubbed, and never calls a
model. The brand profiles it uses are FROZEN copies saved beside the goldens (`profiles/`), so a later edit
to the dev tenant cannot move the baseline.

    python tools/golden_prompts.py --save tools/golden_pre_nuance        # capture (copies profiles from the dev tenant)
    python tools/golden_prompts.py --compare tools/golden_pre_nuance     # exit 1 and name every file that differs
    python tools/golden_prompts.py --compare DIR --brand "Sthir Cement"  # one brand
"""
import argparse, glob, hashlib, json, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.abspath(os.path.join(HERE, "..", "api"))

ap = argparse.ArgumentParser()
ap.add_argument("--save", default="")
ap.add_argument("--compare", default="")
ap.add_argument("--brand", default="")
ap.add_argument("--show", action="store_true", help="print a unified diff for each changed file")
args = ap.parse_args()
if bool(args.save) == bool(args.compare):
    sys.exit("give exactly one of --save DIR or --compare DIR")

OUT = os.path.abspath(args.save or args.compare)
SCRATCH = tempfile.mkdtemp(prefix="golden_")
os.environ["STUDIO_DATA_DIR"] = SCRATCH            # BEFORE any import: otherwise the harness writes into the real tenant
os.environ["PYTHONUTF8"] = "1"
os.environ["ANTHROPIC_API_KEY"] = "golden-key-never-used"
BRANDS_DIR = os.path.join(SCRATCH, "tenants", "default", "brands")
os.makedirs(BRANDS_DIR, exist_ok=True)

# the frozen inputs: on --save take them from the dev tenant, on --compare take the saved copies
if args.save:
    src = os.path.join(API, "tenants", "default", "brands")
    os.makedirs(os.path.join(OUT, "profiles"), exist_ok=True)
    for f in sorted(glob.glob(os.path.join(src, "*.json"))):
        if os.path.basename(f).startswith("_"):
            continue
        shutil.copy(f, os.path.join(OUT, "profiles", os.path.basename(f)))
src_profiles = os.path.join(OUT, "profiles")
if not os.path.isdir(src_profiles):
    sys.exit(f"no frozen profiles in {src_profiles}")
for f in glob.glob(os.path.join(src_profiles, "*.json")):
    shutil.copy(f, os.path.join(BRANDS_DIR, os.path.basename(f)))

sys.path.insert(0, API)
os.chdir(API)

CAP = []
import jsonout  # noqa: E402


def fake_ask(prompt, *a, **k):
    CAP.append(prompt)
    return None, "golden: model stubbed"


jsonout.ask_json = fake_ask
import anthropic  # noqa: E402


class _Msgs:
    def create(self, **kw):
        CAP.append((kw.get("system") or "") + "\n\n" + "\n".join(str(m.get("content")) for m in kw.get("messages", [])))
        raise RuntimeError("golden: model stubbed")


class _Client:
    def __init__(self, *a, **k):
        self.messages = _Msgs()


anthropic.Anthropic = _Client

import brandprofile, strategy, ideas, producers, campaign, prompts, plan, sales, brief_ai  # noqa: E402,E401

# Frozen profile text for the ids/dates that would otherwise move between runs
_ID = re.compile(r"\b[0-9a-f]{10}\b")


def norm(t: str) -> str:
    return _ID.sub("<id>", t.replace("\r\n", "\n"))


def build(profile):
    """{surface: text} for one brand."""
    name = profile["name"]
    house = strategy.new_house(name)
    house["nodes"]["core"]["options"] = [{"id": "c1", "text": f"{name} core message"}]
    house["nodes"]["core"]["chosen"] = ["c1"]
    # a ladder path (functional truth -> bridge -> feeling): campaign.draft refuses without one
    house["nodes"]["functional"]["options"] = [{"id": "f1", "text": f"{name} functional truth"}]
    house["nodes"]["functional"]["chosen"] = ["f1"]
    house["nodes"]["emotional"]["options"] = [{"id": "e1", "text": f"{name} emotional truth"}]
    house["nodes"]["emotional"]["chosen"] = ["e1"]
    house["nodes"]["bridge"]["options"] = [{"id": "b1", "text": f"{name} bridge"}]
    house["nodes"]["bridge"]["chosen"] = ["b1"]
    house["ladders"] = [{"id": "l1", "f": "f1", "e": "e1", "b1": "b1"}]
    strategy.save(house)
    pset = ideas.adopt(ideas.new_set(name, house["id"]), {"name": f"{name} platform", "idea": f"{name} idea", "mechanic": f"{name} mechanic", "ladder": "l1"})
    pset = ideas.for_house(house["id"])
    platform = ideas.chosen_platform(pset)
    out = {}

    def grab(label, fn):
        CAP.clear()
        try:
            r = fn()
            if isinstance(r, str) and r:
                CAP.append(r)
        except Exception:                                     # noqa: BLE001 -- the stub raises on purpose
            pass
        out[label] = "\n\n=====\n\n".join(CAP) if CAP else "(no prompt captured)"

    grab("voice_block", lambda: brandprofile.voice_block(profile))
    grab("voice_block_film", lambda: brandprofile.voice_block(profile, film=True))
    grab("voice_block_none", lambda: brandprofile.voice_block(None))
    msgs = [{"role": "user", "content": "You are a social media writer. platform-adapted posts. Write posts."}]
    grab("social_system", lambda: prompts.system_for(msgs, brand=profile, house_id=house["id"]))
    grab("video_system", lambda: prompts.system_for([{"role": "user", "content": "You are a film director writing a shootable script."}],
                                                    brand=profile, house_id=house["id"], film=True))
    grab("carousel", lambda: producers.carousel_concept("Brand awareness", house, platform))
    grab("posm", lambda: producers.key_visual("A point of sale board", house, platform=platform))
    grab("onground", lambda: producers.activation_ideas(house, platform))
    grab("idea_platform_draft", lambda: ideas.draft_prompt(f"{name} core message", None, house))
    grab("campaign_draft", lambda: campaign.draft(pset, house))
    grab("house_core", lambda: strategy.generate(house, "core"))
    pl = plan.new_plan(name, house["id"])
    grab("plan_objectives", lambda: plan.generate(pl, "objectives", house))
    sh = sales.new_sheet(name, "", house["id"])
    grab("sales_trad", lambda: sales.generate(sh, "trad", house))
    grab("brief_draft", lambda: brief_ai.draft_brief({"brand": name, "category": profile.get("category", ""), "request": "Launch a new product"}))
    return out


profiles = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(BRANDS_DIR, "*.json")))]
profiles = [p for p in profiles if p.get("name") and (not args.brand or p["name"] == args.brand)]
if not profiles:
    sys.exit("no brand matched")

changed = unchanged = missing = 0
manifest = {}
for p in profiles:
    slug = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
    got = build(p)
    for surface, text in got.items():
        text = norm(text)
        rel = f"{slug}/{surface}.txt"
        path = os.path.join(OUT, rel)
        manifest[rel] = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        if args.save:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            continue
        if not os.path.exists(path):
            missing += 1
            print(f"MISSING  {rel}")
            continue
        old = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")     # git may check the goldens out as CRLF
        if old == text:
            unchanged += 1
        else:
            changed += 1
            print(f"CHANGED  {rel}  ({len(old)} -> {len(text)} chars)")
            if args.show:
                import difflib
                for ln in list(difflib.unified_diff(old.split("\n"), text.split("\n"), "before", "after", lineterm="", n=0))[:60]:
                    print("    " + ln[:200])

if args.save:
    with open(os.path.join(OUT, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    print(f"saved {len(manifest)} prompts for {len(profiles)} brands to {OUT}")
else:
    print(f"{unchanged} unchanged, {changed} changed, {missing} missing")
    sys.exit(1 if (changed or missing) else 0)
