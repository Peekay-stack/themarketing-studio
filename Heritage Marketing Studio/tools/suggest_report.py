#!/usr/bin/env python
"""suggest_report.py -- the REAL-MODEL run for Step 4 of NUANCE_LAYER_PLAN.md. It SPENDS CREDIT, so it refuses without --yes.

For each probe brand it asks the model for a draft of every nuance question, one group per call (exactly what the
profile screen's button does: it calls brand_suggest.suggest_group), and writes what came back to a markdown report
for a person to judge. It saves nothing to any tenant: a scratch data folder is used, the dev brands come from the
frozen copies in tools/golden_pre_nuance/profiles, and the probes are built here.

    python tools/suggest_report.py --yes --out NUANCE_STEP4_SUGGESTIONS.md
    python tools/suggest_report.py --yes --only "Sthir Cement" --out /tmp/one.md

The key comes the way it does for the studio itself: importing `main` loads the project's own .env. The probes add
states to the dev brands (they have none) so the place question can be judged; that is stated in the report.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import glob
import json
import os
import re
import sys
import tempfile
import time

ap = argparse.ArgumentParser()
ap.add_argument("--yes", action="store_true", help="confirm that real model calls will be made and paid for")
ap.add_argument("--out", default="NUANCE_STEP4_SUGGESTIONS.md")
ap.add_argument("--only", default="", help="run one brand by name")
ap.add_argument("--workers", type=int, default=4)
args = ap.parse_args()

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.abspath(os.path.join(HERE, "..", "api"))
GOLD = os.path.join(HERE, "golden_pre_nuance", "profiles")

os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="suggestrun_")      # BEFORE any import: nothing may touch a real tenant
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, API)
os.chdir(API)

import brandprofile as bp   # noqa: E402
import brand_suggest as bs  # noqa: E402

# Probes: the dev brands as frozen, with states added where they had none, plus the cases the owner named.
DEV = {}
for f in glob.glob(os.path.join(GOLD, "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    DEV[d["name"]] = d
STATES_ADDED = {"Kumkum Beauty": ["Delhi", "West Bengal", "Assam"], "Loomwell": ["Delhi", "West Bengal"], "Sthir Cement": ["Bihar", "West Bengal", "Assam"]}
PROBES = [
    {"name": "Heritage Foods", "_note": "dev profile as frozen; asked even where a reviewed answers file exists, to compare with it", "_seeded": True},
    {"name": "Kumkum Beauty", "_note": "states added for this run: " + ", ".join(STATES_ADDED["Kumkum Beauty"])},
    {"name": "Loomwell", "_note": "states added for this run: " + ", ".join(STATES_ADDED["Loomwell"])},
    {"name": "Sthir Cement", "_note": "states added for this run: " + ", ".join(STATES_ADDED["Sthir Cement"])},
    {"name": "Heritage Ice Cream (probe)", "category": "Dairy — ice cream and frozen desserts", "market": "India, South India",
     "hero_product": "Heritage Ice Cream", "states": ["Telangana", "Andhra Pradesh"], "languages": ["te", "en"], "regulator": "FSSAI",
     "_note": "owner's case: dairy, but ice cream can be family or individual. The profile does NOT say which."},
    {"name": "Vigor Protein for men (probe)", "category": "Functional nutrition — high-protein bars and shakes", "market": "India, metros",
     "hero_product": "Vigor high-protein bar", "positioning": "A high-protein bar for men who train", "decider": "the man himself", "payer": "the man himself",
     "user": "the man himself", "states": ["Delhi", "West Bengal"], "languages": ["hi", "en"],
     "_note": "owner's case: a functional product bought by an individual man"},
    {"name": "Vigor Protein for women (probe)", "category": "Functional nutrition — high-protein bars and shakes", "market": "India, metros",
     "hero_product": "Vigor high-protein bar", "positioning": "A high-protein bar for women who train", "decider": "the woman herself", "payer": "the woman herself",
     "user": "the woman herself", "states": ["Delhi", "West Bengal"], "languages": ["hi", "en"],
     "_note": "owner's case: the same product bought by an individual woman. Compare with the men's probe."},
    {"name": "Sthir Cement, family home build (probe)", "category": "Cement — building materials (OPC and PPC, bagged trade cement)", "market": "India, semi-urban and rural",
     "hero_product": "Sthir PPC 50kg", "decider": "the man of the family, on the contractor's advice", "payer": "the family", "user": "the mason building the family's own house",
     "states": ["Bihar", "Assam"], "languages": ["hi", "as", "en"], "regulator": "BIS",
     "_note": "owner's case: cement as a family decision with a man leading"},
    {"name": "Sthir Cement, trade buyer (probe)", "category": "Cement — building materials (OPC and PPC, bagged trade cement)", "market": "India, semi-urban and rural",
     "hero_product": "Sthir PPC 50kg", "decider": "the contractor", "payer": "the contractor", "user": "the contractor's own crew",
     "states": ["Bihar", "Assam"], "languages": ["hi", "as", "en"], "regulator": "BIS",
     "_note": "owner's case: cement bought by an individual, a contractor. Compare with the family case."},
]
if args.only:
    PROBES = [p for p in PROBES if p["name"] == args.only]
    if not PROBES:
        sys.exit(f"no probe named {args.only!r}")

calls = sum(len([g for g in bs.GROUPS]) for _ in PROBES)
print(f"{len(PROBES)} brands x up to {len(bs.GROUPS)} groups = up to {calls} model calls with the studio's own model "
      f"({os.environ.get('GEN_MODEL', 'claude-opus-4-8')}).")
if not args.yes:
    sys.exit("This spends credit. Re-run with --yes to go ahead.")

import main  # noqa: E402,F401  -- the studio's own start-up loads its key, exactly as it does for a person using the app

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("No ANTHROPIC_API_KEY after loading the studio; nothing was called.")

profiles = []
for p in PROBES:
    base = dict(DEV.get(p["name"], {}))
    base.update({k: v for k, v in p.items() if not k.startswith("_")})
    if p["name"] in STATES_ADDED:
        base["states"] = STATES_ADDED[p["name"]]
    base.pop("id", None)
    saved = bp.put({k: v for k, v in base.items() if k not in ("created", "updated", "active")})
    profiles.append((saved, p))

DAIRY = re.compile(r"\b(milk|dairy|ghee|curd|paneer|fssai|kirana|pouch|sachet|tetra|hinglish|pongal|sankranti)\b", re.I)


def run(item):
    b, probe = item
    out = []
    for g in bs.groups_view(b) if not probe.get("_seeded") else [{"name": x["name"]} for x in bs.GROUPS]:
        t = time.time()
        r = bs.suggest_group(b, g["name"], include_seeded=bool(probe.get("_seeded")))
        out.append((g["name"], r, round(time.time() - t, 1)))
        print(f"  {b['name']} / {g['name']}: {len(r['suggestions'])} drafted, {len(r['unknown'])} blank, {r['error'] or 'ok'} ({out[-1][2]}s)", flush=True)
    return b, probe, out


with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
    results = list(pool.map(run, profiles))


def show(v):
    if isinstance(v, list):
        if v and isinstance(v[0], dict):
            return "<br>".join(" · ".join(f"{c}: {x}" for c, x in r.items() if x) for r in v)
        return "<br>".join(f"- {x}" for x in v)
    return str(v)


lines = [f"# Step 4: what the model drafts (real run, {time.strftime('%Y-%m-%d %H:%M')})", "",
         f"Model: `{os.environ.get('GEN_MODEL', 'claude-opus-4-8')}` (the studio's own). One call per group, exactly as the profile screen's button does it. "
         "Nothing was saved anywhere. Each draft carries its basis: **profile** (stated or directly implied), **context**, or **knowledge** "
         "(the model's general knowledge, which you must confirm). A blank means the model said it could not know.", ""]
tot = {}
for b, probe, out in results:
    n_d = sum(len(r["suggestions"]) for _, r, _ in out)
    n_b = sum(len(r["unknown"]) for _, r, _ in out)
    errs = [f"{g}: {r['error']}" for g, r, _ in out if r["error"]]
    basis = {}
    for _, r, _ in out:
        for s in r["suggestions"].values():
            basis[s["basis"]] = basis.get(s["basis"], 0) + 1
    tot[b["name"]] = (n_d, n_b, basis, errs)
lines += ["| Brand | drafted | left blank | basis | errors |", "|---|---|---|---|---|"]
for name, (n_d, n_b, basis, errs) in tot.items():
    lines.append(f"| {name} | {n_d} | {n_b} | {', '.join(f'{k} {v}' for k, v in sorted(basis.items()))} | {'; '.join(errs) or 'none'} |")
lines.append("")
for b, probe, out in results:
    lines += [f"## {b['name']}", "", f"*{probe.get('_note') or 'dev profile as frozen'}*", "",
              "What it was given: " + bs.profile_text(b).replace("\n", " | "), ""]
    leak = set()
    for gname, r, secs in out:
        lines += [f"### {gname} ({secs}s)", ""]
        if r["error"]:
            lines += [f"**Failed:** {r['error']}", ""]
        for k, s in r["suggestions"].items():
            lines.append(f"- **{bp.SPEC_BY_KEY[k]['label']}** (`{k}`, basis: {s['basis']}): {show(s['value'])}" + (f"  \n  *could not know:* {s['unknowns']}" if s["unknowns"] else ""))
            if b["name"] not in ("Heritage Foods",) and "Ice Cream" not in b["name"]:
                leak |= {m.group(0).lower() for m in DAIRY.finditer(json.dumps(s["value"]))}
        for k, why in r["unknown"].items():
            lines.append(f"- **{bp.SPEC_BY_KEY[k]['label']}** (`{k}`): *left blank.* {why}")
        for k, why in r["skipped"].items():
            lines.append(f"- **{bp.SPEC_BY_KEY[k]['label']}** (`{k}`): *not drafted.* {why}")
        lines.append("")
    if b["name"] not in ("Heritage Foods",) and "Ice Cream" not in b["name"]:
        lines += [f"**Dairy or Heritage words in this brand's drafts:** {sorted(leak) or 'none'}", ""]
open(args.out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print(f"wrote {args.out}")
