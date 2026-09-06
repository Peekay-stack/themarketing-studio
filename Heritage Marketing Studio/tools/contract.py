#!/usr/bin/env python
"""contract.py — does the backend send the shape the frontend reads?

Four separate outages came from one mistake made four times: a field whose name the two sides agreed on
and whose *shape* they did not.

    status.layers[].options   sent as a count      read as an array   -> nothing rendered, ever
    status.layers[].rows      sent as a count      read as an array   -> empty tables
    status.layers[].id        sent as `id` only    read as `layer`    -> every layer resolved to null
    status.layers[].asks      sent as a string     read as an array   -> `.map is not a function`, whitescreen

Each was found by a person clicking, after being shipped. None was caught by `checkfe` (which reads
syntax, not meaning) or by the endpoint diff (which reads paths, not payloads). This is the missing check.

It works by treating the frontend as the specification. Wherever the client does `(X.field || []).map(…)`
or `(X.field || []).length`, it is asserting that `field` is a list. This builds a real house, plan and
platform, then verifies every such field really is one.

    python tools/contract.py

It cannot catch everything — a field read as a string but sent as a number will pass. What it does catch
is the exact class that has actually broken this app, which is where a check earns its keep.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
API = os.path.join(ROOT, "api")
FE = os.path.join(API, "frontend", "app.dc.html")

# Scoped deliberately to `status.layers[]`, because that is where every outage happened and because a
# broader scan produced only noise: `added` on an option is a timestamp, but `(d.added||[]).length` in the
# library-upload response is a list, and a name-matching check flags the first because of the second.
#
# A check that reports six phantom problems and no real ones is worse than no check — the next genuine
# failure arrives in a list somebody has learnt to skim. So this asks one precise question instead:
# for the layer rows the house and plan screens read, does every field they iterate come back iterable,
# and does every row carry a name they can identify it by?
#
# `LAYER_LIST_FIELDS` is derived from the client rather than hardcoded: any `(x.field || []).map` where
# the same field name also exists on a layer row counts.
IDENT_READ = re.compile(r"\.find\(\s*\w+\s*=>\s*\(([^)]+)\)\s*===")
LIST_READ = re.compile(r"\(\s*(?:[A-Za-z_$][\w$]*\.)*([A-Za-z_$][\w$]*)\s*\|\|\s*\[\]\s*\)\s*\.\s*(map|length|find|filter|forEach|slice|indexOf|join)")


def frontend_expectations() -> tuple[set[str], list[set[str]], int]:
    """What the client expects of a layer row — and only of a LAYER row.

    `.find(x => (x.a || x.b) === key)` is a common shape, and the client now uses it on collections
    that have nothing to do with layers: a translation looked up by language, a signature looked up by
    role, a library item by id. Counting those as layer lookups produced four confident mismatches
    about fields no layer was ever supposed to carry — and this file's own header says a check that
    reports phantom problems is worse than no check, because the next real one arrives in a list
    somebody has learnt to skim.

    So a match only counts when `layers` appears within the three lines above it, which is where the
    collection being searched is named (`const ls = status.layers;`). A genuine typo inside the real
    lookup still fails, because that line is still in range.
    """
    src = open(FE, encoding="utf-8").read()
    lines = src.split("\n")
    lists = {m.group(1) for m in LIST_READ.finditer(src)}
    idents, skipped = [], 0
    for m in IDENT_READ.finditer(src):
        names = {n.strip().split(".")[-1] for n in m.group(1).split("||") if n.strip()}
        if not names:
            continue
        at = src[:m.start()].count("\n")
        if not any("layers" in ln for ln in lines[max(0, at - 3):at + 1]):
            skipped += 1
            continue
        idents.append(names)
    return lists, idents, skipped


def build_samples() -> dict:
    """One of every status payload, with enough content that empty collections do not hide a bug."""
    sys.path.insert(0, API)
    os.environ["STUDIO_TENANT"] = "contractcheck"
    import shutil
    import tenancy
    shutil.rmtree(os.path.join(tenancy.TENANTS, "contractcheck"), ignore_errors=True)
    import importlib
    for m in ("tenancy", "brandprofile", "briefstore", "strategy", "plan", "ideas",
              "sales", "execution", "findings"):
        importlib.reload(importlib.import_module(m))
    import strategy, plan, ideas, sales, brandprofile
    brandprofile.seed()

    h = strategy.new_house("Contract Co", {"smp": "a proposition"})
    for layer in ("core", "emotional", "functional", "rtb_functional"):
        h = strategy.add_option(h, layer, f"an option for {layer}", note="why")
        h = strategy.choose(h, layer, [h["nodes"][layer]["options"][0]["id"]])
    h = strategy.add_option(h, "culture", "an occasion", tag="occasion")
    h = strategy.choose(h, "culture", [h["nodes"]["culture"]["options"][0]["id"]])

    p = plan.new_plan("Contract Co", h["id"])
    p = plan.add_row(p, "objectives", {"level": "business", "statement": "grow", "measure": "+1%",
                                       "by_when": "FY27"})
    p = plan.add_row(p, "audiences", {"audience": "someone", "rank": "1",
                                      "believes_now": "something", "pillar": "functional"})

    pl = ideas.new_set("Contract Co", h["id"])
    pl = ideas.adopt(pl, {"name": "A platform", "line": "one sentence",
                          "tests": {"true": {"verdict": "holds", "note": "n"}},
                          "routes": {"social": "a", "posm": "b"}})

    sh = sales.new_sheet("Contract Co")
    sh = sales.set_channel(sh, "trad", {"role": "volume", "share_now": "60",
                                        "behaviour": "order weekly", "baseline": "1", "target": "2",
                                        "lever": "trade scheme", "payback": "payback unknown",
                                        "leakage": "loading", "control": "cap on rate of sale",
                                        "residual_risk": "diversion", "receives_money": "retailer",
                                        "sell_through": "secondary", "effective_price": "56"})
    import shots as shots_mod
    shots_mod.plan_from([{"no": 1, "visual": "a shot", "title": "One"}], None, "contract-exec")

    # The list cards are typed here, against these same synthetic documents, because they must be read
    # BEFORE the tenant is torn down below. Reading them afterwards silently returns [] and the check
    # then asserts nothing while still printing green.
    global CARD_ROWS
    CARD_ROWS = {"houses": strategy.houses(), "plans": plan.plans()}

    out = {
        "house": strategy.status(h),
        "plan": plan.status(p, h),
        "platform": ideas.status(pl, h),
        "trade": sales.status(sh, h),
        "shotlist": shots_mod.status("contract-exec"),
    }
    shutil.rmtree(os.path.join(tenancy.TENANTS, "contractcheck"), ignore_errors=True)
    return out


def walk(node, path=""):
    """Every (key, value) in the payload, with the path that reached it."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node[:1]):          # one row is enough to type a collection
            yield from walk(v, f"{path}[]")


# --- the list cards -----------------------------------------------------------------------------
#
# `status.layers[]` was the only thing checked here, and that scope was too narrow. The Strategy and
# Plan screens draw a card per document from `strategy.houses()` / `plan.plans()`, and those payloads
# drifted the same way `layers[]` did: the client read `chosen_layers` / `filled_layers`, the backend
# sent `decided` and nothing at all respectively. Both fell back to 0, so a house with all eight layers
# settled rendered as "0 of 8 layers decided — Not started." and every plan read "0 of 7 layers written".
#
# Nothing crashed, which is what makes it worse than the `layers[]` bug: a person looking at a finished
# house is told their work is not there, and has no reason to disbelieve the screen.
#
# So the rule these enforce is not "these keys exist" — it is: **the field the client actually reads for
# a number must be present**, because a missing key here is silently 0 rather than an error. `|| 0` and
# `!= null ? … : …` are exactly the patterns that turn drift into a confident lie.
CARD_ROWS: dict = {}

CARD_READS = {
    "houses": {
        # the client does: h.chosen_layers != null ? h.chosen_layers : (h.progress || 0)
        "count":  ("chosen_layers", "progress"),
        "single": ("next_layer", "blocking", "stale", "brand", "id"),
    },
    "plans": {
        # the client does: p.filled_layers != null ? p.filled_layers : (p.progress || 0)
        "count":  ("filled_layers", "progress"),
        "single": ("house", "house_brand", "blocking", "stale", "brand", "id"),
    },
}


def check_cards(problems: list, skipped: list) -> int:
    """Every field the card reads must be present on the row the backend actually returns.

    These type a real row, so they need a document on disk. When there is none the check is **reported
    as skipped, not as passed** — a green line covering zero assertions is how a check stops being worth
    running, and this file already had one of those.
    """
    checked = 0
    for name in ("houses", "plans"):
        rows = CARD_ROWS.get(name) or []
        if not rows:
            skipped.append(name)
            continue
        row, spec = rows[0], CARD_READS[name]
        checked += 1
        if not (set(spec["count"]) & set(row)):
            problems.append(
                f"{name}[] carries none of {sorted(spec['count'])} — the client reads the progress "
                f"count by those names and falls back to 0, so a finished document renders as empty")
        for key in spec["single"]:
            checked += 1
            if key not in row:
                problems.append(f"{name}[].{key} is absent — the card reads it")
    return checked


def check_jobs(problems: list) -> int:
    """The jobs table's row shape, asserted before a screen is built against it.

    Deliberately earlier than the rest of this file's checks. Every outage this module exists to catch
    was found by a person clicking, after the shape had already shipped — so for the one table that is
    replacing three screens, the contract is written first and the panel is built against a shape that
    is already guaranteed.

    A row is checked for the fields a table has to have to render at all: something to label the row,
    a role and its reasoning, the expression and where it came from, and the two booleans the empty and
    review states are drawn from. `expression` is allowed to be empty — an empty cell is the finding,
    not a fault — but the KEY must exist, because `row.expression` on an absent key is how a cell
    silently renders as undefined.
    """
    sys.path.insert(0, API)
    import campaign, media, strategy, ideas                      # noqa: E402

    required = ("medium", "label", "parent", "role", "role_source", "why",
                "expression", "source", "needs_review", "empty")
    checked = 0

    house = None
    for hid in [h.get("id") for h in strategy.houses()] if hasattr(strategy, "houses") else []:
        got = strategy.load(hid)
        if got and ((got.get("nodes") or {}).get("medium") or {}).get("chosen"):
            house = got
            break
    pl, _it, _why = ideas.resolve({"house": (house or {}).get("id", "")}, allow_latest=True)

    for label, table in (("computed", campaign.jobs(house, pl, None)),
                         ("bare", campaign.jobs(None, None, None))):
        rows = table.get("rows")
        if not isinstance(rows, list) or not rows:
            problems.append(f"jobs({label}): rows is {type(rows).__name__}, and the client maps it")
            continue
        # One row per leaf, always. A table that silently drops a medium is a job nobody is doing.
        checked += 1
        if len(rows) != len(media.LEAVES):
            problems.append(f"jobs({label}): {len(rows)} rows for {len(media.LEAVES)} leaves — a "
                            f"medium has gone missing from the table")
        for r in rows:
            for key in required:
                checked += 1
                if key not in r:
                    problems.append(f"jobs({label}): row '{r.get('medium', '?')}' has no '{key}' — "
                                    f"the client reads it and would render undefined")
            for key in ("needs_review", "empty"):
                if key in r and not isinstance(r[key], bool):
                    problems.append(f"jobs({label}): row '{r.get('medium','?')}'.{key} is "
                                    f"{type(r[key]).__name__}, not a bool")
        checked += 1
        if not isinstance(table.get("findings"), list):
            problems.append(f"jobs({label}): findings is not a list, and the client maps it")
    return checked


def main() -> int:
    lists, idents, skipped_idents = frontend_expectations()
    samples = build_samples()
    problems, checked = [], 0

    for doc, payload in samples.items():
        rows = (payload.get("layers") or [])
        if not rows or not isinstance(rows, list):
            continue
        row = rows[0]

        # 1. every layer field the client iterates must be iterable
        for key, value in row.items():
            if key not in lists:
                continue
            checked += 1
            if not isinstance(value, (list, tuple)):
                problems.append(
                    f"{doc}: status.layers[].{key} is {type(value).__name__}, but the client does "
                    f"({key} || []).map/.length on a layer — it must be a list")

        # 2. every layer must carry a name the client can find it by
        for names in idents:
            checked += 1
            if not (names & set(row)):
                problems.append(
                    f"{doc}: status.layers[] carries none of {sorted(names)} — the client finds a layer "
                    f"by those names and would resolve null for all of them")

    skipped: list = []
    card_checks = check_cards(problems, skipped)
    job_checks = check_jobs(problems)

    print(f"the client iterates {len(lists)} field names and identifies layer rows {len(idents)} way(s) "
          f"({skipped_idents} find-by-name lookups on other collections skipped); "
          f"{checked} layer-shape checks on {len(samples)} documents, "
          f"{card_checks} card-field checks on the house and plan lists, "
          f"{job_checks} jobs-row checks\n")
    if problems:
        for p in sorted(set(problems)):
            print(f"  MISMATCH  {p}")
        print(f"\n{len(set(problems))} shape mismatch(es). Each one is a blank screen, a crash, or a "
              f"document that reports itself as empty.")
        return 1
    print("  every field the client iterates on a layer is a list, every layer carries a name it looks "
          "for, and the house and plan cards carry the count the client reads"
          + (" (where there was a document to check)." if skipped else "."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
