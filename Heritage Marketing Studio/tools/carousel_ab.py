#!/usr/bin/env python
"""carousel_ab.py -- REAL-MODEL comparison of the Carousel concept prompt on the same Heritage inputs. It SPENDS CREDIT, so it refuses without --yes.

Why: on 12 Oct the owner's first real Heritage carousel after Step 5 Surface 1 had a closing slide that poured from a second pack. One run
cannot say whether the new Carousel wording caused it, whether the pour gesture in Heritage's own "how it is used or handled" answer did, or
whether the idea simply wants a pour. This runs the CONCEPT step (the writer, where that slide's note is written) several times per arm:

    B  current wording  + Heritage's accepted answers      (what the owner ran)
    A  OLD wording      + the same answers                  (producers.py from the commit before Surface 1)
    D  current wording  + the answers with the pour made conditional and the closing slide still   (the proposed fix, R1)

and scores each closing slide: does it pour, how many packs does it name, whose hand is in it. It saves nothing to any tenant (a scratch
data folder), calls no image model (concepts only) and takes the key the way the studio does (importing `main`).

    python tools/carousel_ab.py --yes --runs 3 --out NUANCE_CAROUSEL_AB.md
"""
from __future__ import annotations

import argparse
import concurrent.futures
import glob
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time

ap = argparse.ArgumentParser()
ap.add_argument("--yes", action="store_true", help="confirm that real model calls will be made and paid for")
ap.add_argument("--runs", type=int, default=3)
ap.add_argument("--workers", type=int, default=3)
ap.add_argument("--out", default="NUANCE_CAROUSEL_AB.md")
ap.add_argument("--old-commit", default="55df1c9^", help="the commit whose producers.py is the OLD wording")
args = ap.parse_args()

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.abspath(os.path.join(HERE, "..", "api"))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GOLD = os.path.join(HERE, "golden_pre_nuance", "profiles")

ARMS = ["B", "A", "D"]
print(f"3 arms x {args.runs} runs = {3 * args.runs} concept calls with the studio's own model ({os.environ.get('GEN_MODEL', 'claude-opus-4-8')}).")
if not args.yes:
    sys.exit("This spends credit. Re-run with --yes to go ahead.")

os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="carouselab_")      # BEFORE any import: nothing may touch a real tenant
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, API)
os.chdir(API)

import brandprofile as bp   # noqa: E402
import ideas                # noqa: E402
import jsonout              # noqa: E402
import strategy             # noqa: E402

import main  # noqa: E402,F401  -- the studio's own start-up loads its key
import producers            # noqa: E402

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("No ANTHROPIC_API_KEY after loading the studio; nothing was called.")

# the OLD producers.py, straight from git, loaded under another name (it imports the same live modules)
blob = subprocess.run(["git", "-C", REPO, "show", f"{args.old_commit}:Heritage Marketing Studio/api/producers.py"], capture_output=True, check=True).stdout
old_path = os.path.join(tempfile.mkdtemp(prefix="producers_old_"), "producers_old.py")
open(old_path, "wb").write(blob)
spec = importlib.util.spec_from_file_location("producers_old", old_path)
producers_old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producers_old)

# Heritage as the live profile stands: the dev profile frozen in the golden baseline, the owner's wider market and languages, and the
# starting answers the owner ACCEPTED on live (every seed answer except imagery and meeting points, which were still pending).
heritage = next(json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(GOLD, "*.json")) if json.load(open(f, encoding="utf-8")).get("name") == "Heritage Foods")
base = bp.save(heritage)
seed = bp.seed_answers(base)
accepted = {k: v for k, v in seed.items() if k not in ("imagery_style", "meeting_points")}
MARKET = ("India, strongest across South India (Telangana, Andhra Pradesh, Karnataka, Tamil Nadu), expanding nationally with presence "
          "in Mumbai, Pune, Delhi NCR and Haryana")
R1_USE = ("A small pack of milk is handled the way people really handle one: carried at the side, handed over, tucked into a crate, set down on a "
          "counter. It is poured from its opened corner into a glass or a vessel only in a slide whose story pours, from the one real pack; the "
          "closing slide shows that real pack upright and still, never a second pack and never a pour. Never held out at arm's length toward the "
          "camera, and never left alone as a centrepiece with no one touching it, because both read as an advertising hero shot and make the pack "
          "render oversized.")


def set_profile(arm: str):
    answers = dict(accepted)
    if arm == "D":
        answers["product_in_use"] = R1_USE
    return bp.put({"name": "Heritage Foods", "market": MARKET, "states": ["ap", "tg", "ka", "tn", "mh", "dl", "hr"],
                   "languages": ["te", "kn", "ta", "mr", "hi", "en"], **answers}, base["id"])


house = strategy.new_house("Heritage Foods")
house["nodes"]["core"]["options"] = [{"id": "c1", "text": "The strength of pure milk"}]
house["nodes"]["core"]["chosen"] = ["c1"]
strategy.save(house)
IDEA = ("We mark the first glass of every day – the one a family drinks before anything else – as the one Heritage is poured for, turning the "
        "ordinary breakfast glass into a visible daily ritual of strength given.")
pset = ideas.adopt(ideas.new_set("Heritage Foods", house["id"]), {"name": "The First Pour", "idea": IDEA, "mechanic": "A named first glass, poured for the family each morning"})
platform = ideas.chosen_platform(ideas.for_house(house["id"]))
OBJECTIVE = "develop a carousel with clear call to action for the attached idea"

# capture each call's real prompt (to prove the arms differ as intended), then make the real call
_orig = jsonout.ask_json
_seen = threading.local()


def _wrapped(prompt, *a, **k):
    _seen.prompt = prompt
    return _orig(prompt, *a, **k)


jsonout.ask_json = _wrapped


def run_once(arm: str, i: int):
    mod = producers_old if arm == "A" else producers
    t = time.time()
    routes, note = mod.carousel_concept(OBJECTIVE, house, platform, None, None, "auto", 5)
    return {"arm": arm, "run": i, "routes": routes, "note": note, "secs": round(time.time() - t, 1), "prompt": getattr(_seen, "prompt", "")}


results = []
for arm in ARMS:
    set_profile(arm)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        got = list(pool.map(lambda i: run_once(arm, i), range(args.runs)))
    results += got
    print(f"  arm {arm}: " + ", ".join(f"run {r['run']}: {len(r['routes'])} routes ({r['secs']}s){' NOTE: ' + r['note'] if r['note'] else ''}" for r in got), flush=True)

POUR = re.compile(r"\bpour(?:s|ed|ing)?\b|mid-pour|\bstream(?:s|ing)?\b", re.I)
CHILD = re.compile(r"\b(?:small hand|child|boy|girl|grandson|granddaughter|kid|little)\b", re.I)
ADULT = re.compile(r"\b(?:man|woman|father|mother|adult|grandmother|grandfather)\b", re.I)
GLASS_OK = re.compile(r"film|ring at|line of milk|visible milk|milk in|rising|half-filled|half filled|full glass|white", re.I)


def cta_of(route):
    slides = route.get("slides") or []
    c = next((s for s in slides if s.get("role") == "cta"), None)
    return c or (slides[-1] if slides else None)


lines = [f"# Carousel concept A/B, real model ({time.strftime('%Y-%m-%d %H:%M')})", "",
         f"Model `{os.environ.get('GEN_MODEL', 'claude-opus-4-8')}`, the concept step only (no images), the owner's idea platform and objective, Heritage as it stands on live. "
         f"{args.runs} runs per arm, each run gives up to three routes, so up to {3 * args.runs} closing slides per arm. Arms: **B** current wording + Heritage's accepted answers (what the owner ran); "
         "**A** the OLD wording (producers.py from the commit before Surface 1) + the same answers; **D** current wording + answers with the pour made conditional and the closing slide still (the proposed fix).", ""]
summary = {}
for arm in ARMS:
    rs = [r for r in results if r["arm"] == arm]
    ctas = [(r["run"], rt.get("name", ""), cta_of(rt)) for r in rs for rt in r["routes"] if cta_of(rt)]
    pours = [c for c in ctas if POUR.search(str(c[2].get("visual_note", "")))]
    packs = [len(re.findall(r"\bpacks?\b", str(c[2].get("visual_note", "")), re.I)) for c in ctas]
    child = [c for c in ctas if CHILD.search(str(c[2].get("visual_note", "")))]
    glass = [s for r in rs for rt in r["routes"] for s in rt.get("slides", []) if re.search(r"\bglass\b", str(s.get("visual_note", "")), re.I)]
    glass_ok = [s for s in glass if GLASS_OK.search(str(s.get("visual_note", "")))]
    nopack = sum(1 for r in rs for rt in r["routes"] for s in rt.get("slides", []) if not s.get("shows_pack"))
    allsl = sum(len(rt.get("slides", [])) for r in rs for rt in r["routes"])
    summary[arm] = {"ctas": len(ctas), "pours": len(pours), "packs_avg": round(sum(packs) / len(packs), 1) if packs else 0, "child": len(child),
                    "glass": len(glass), "glass_ok": len(glass_ok), "slides": allsl, "nopack": nopack}
    p0 = rs[0]["prompt"] if rs else ""
    lines += [f"## Arm {arm}", "",
              f"- closing slides: {len(ctas)}; **that pour: {len(pours)}**; average mentions of 'pack' in the closing note: {summary[arm]['packs_avg']}; mention a child or small hand: {len(child)}",
              f"- slides naming a glass: {len(glass)}, of which describe visible milk: {len(glass_ok)}; slides with no pack: {nopack} of {allsl}", ""]
    for run, name, c in ctas:
        lines.append(f"- run {run} / {name[:48]}: {'POURS | ' if POUR.search(str(c.get('visual_note', ''))) else ''}{str(c.get('visual_note', ''))[:420]}")
    lines.append("")

lines = lines[:4] + ["| arm | closing slides | that pour | avg 'pack' mentions | mention a child | glass slides with visible milk | no-pack slides |", "|---|---|---|---|---|---|---|"] + \
    [f"| {a} | {s['ctas']} | {s['pours']} | {s['packs_avg']} | {s['child']} | {s['glass_ok']}/{s['glass']} | {s['nopack']}/{s['slides']} |" for a, s in summary.items()] + [""] + lines[4:]
open(args.out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("wrote", args.out)
print(json.dumps(summary, indent=1))
