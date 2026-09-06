"""socialplan.py — a geography-wise social campaign that holds money. MP·3.

This is the first module in the studio that holds a budget. Everything before it held weights, roles
and intentions; this holds rupees against places, and the reason it may is that the money exists to be
*moved* — optimised against a KPI while the campaign runs — and something has to know what the split
was supposed to be in order to say whether moving it worked.

The unit is a **cell**: one geography, one objective, one window, one budget. That is not an invented
abstraction — it is deliberately the shape of a Meta ad set, which is the object where geography,
budget and the optimisation goal all actually live. A studio plan whose unit does not match the
platform's unit is a plan that has to be translated by hand every time it changes, and translated by
hand is where plans and campaigns start to disagree.

**What this module will not do.** It will not tell you a campaign is working. Optimisation against a
KPI needs delivery data, and until a platform account is connected or someone types the actuals in,
there are none — so there is nothing here that ranks a geography by performance. What it does instead
is the part that can be done honestly before a rupee is spent, and that turns out to be the part most
plans get wrong:

* **It checks whether the split is even runnable.** A conversion-optimised ad set needs about 50
  optimisation events in a rolling 7 days to leave Meta's learning phase. Split a budget across forty
  cities and each cell needs its own fifty. The arithmetic — budget, cost per action, number of cells —
  decides that in advance, and it very often says no. See `feasibility`.
* **It names the tradeoffs rather than resolving them.** Campaign-level budget lets the algorithm move
  money and will starve the markets it finds expensive, which are frequently the strategic ones.
  Ad-set-level budget protects them and forfeits the optimisation. Neither is correct in general, both
  are correct sometimes, and the choice belongs to a person. See `TRADEOFFS`.

Geography comes from `geo`, benchmarks are entered with a source, and a population is never treated as
a reach — `geo.POP_BASIS["platform_reach"]` explains why at length.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid

import geo
import plan as plan_mod
import tenancy

DIR = tenancy.dir("social_plan")

# Meta's documented learning-phase exit: roughly 50 optimisation events per AD SET in a rolling 7-day
# window. Per ad set and not per ad — several creatives inside one cell share the same pool — and
# rolling, so a cell that drops below re-enters. These two constants are the whole reason a geography
# split can be arithmetically impossible, and they are named rather than inlined because the number is
# a platform fact that will change and should change in one place when it does.
# Rendered labels for the verdict. Without these a screen shows the raw enum — "too_fine", with an
# underscore, on the most important panel in the media desk. Design's return reached for
# `verdict_label` before falling back to `verdict`; the key simply did not exist.
VERDICT_LABEL: dict[str, str] = {
    "runnable": "Runnable",
    "too_fine": "Too fine to run",
    "impossible": "Below the threshold at any split",
    "reported": "Reported — no pass or fail",
}

LEARNING_EVENTS = 50
LEARNING_WINDOW_DAYS = 7
LEARNING_SOURCE = ("Meta Business Help Center — an ad set exits the learning phase at approximately 50 "
                   "optimisation events in a rolling 7-day window, counted per ad set across all its "
                   "ads, including modelled conversions")

# How money is held. The distinction is not administrative — it decides whether a strategic market can
# be starved by an algorithm doing exactly what it was asked to do.
BUDGET_MODES: dict[str, dict] = {
    "per_cell": {
        "label": "Budget per cell (ABO)",
        "what": "Every geography holds its own budget. Meta calls this ad-set budget optimisation.",
        "gives": "Each market is guaranteed its spend and each market's result is comparable with the "
                 "others, because none of them was funded differently by an algorithm mid-flight.",
        "costs": "You are overriding the optimisation. Money sits in a market that is not working "
                 "because you said it should, and it does not move to the one that is.",
        "use_when": "Testing distinct geographies, or when a market has to be present for reasons "
                    "media performance does not capture — a launch, a distribution push, a promise to "
                    "the trade.",
    },
    "pooled": {
        "label": "One pooled budget (CBO)",
        "what": "One budget at campaign level, moved between geographies in real time by Meta.",
        "gives": "Money follows the cheapest result without anybody watching, which over a flight is "
                 "usually more efficient than a split a human guessed at.",
        "costs": "It will starve markets. A geography with a higher CPM gets defunded, and 'higher CPM' "
                 "correlates with 'newer market' and 'smaller city' — exactly the places a growth plan "
                 "is trying to build. You also lose the ability to say how a market performed, because "
                 "it may never have been funded enough to find out.",
        "use_when": "Scaling something already proven across similar geographies, with enough events "
                    "for the algorithm to read a signal.",
        "mitigation": "Minimum-spend floors per cell. They keep a strategic market from being zeroed "
                      "out while leaving the rest of the money free to move — the closest thing to "
                      "having both, and it costs some of the efficiency that made pooling attractive.",
    },
}

# The level a cell targets. `radius` is here because it is what Meta actually offers below city level,
# and because its cost behaviour is counter-intuitive enough to be worth stating.
# What the platform optimises for, which is NOT the plan's strategic role and must not be merged with
# it. `plan.ROLES` is reach / proof / conversion / advocacy — what a channel is FOR. This is the
# optimisation event an ad set is bought against, and the two share the words "reach" and "conversion"
# while meaning different things. Keeping them apart is the point: the learning-phase threshold counts
# THIS, so fifty purchases a week and fifty link clicks a week are the same number and nowhere near the
# same bar. `per_week_note` is the honest part — the rarer the event, the more budget one cell needs to
# leave learning at all.
OPTIMISATION: dict[str, dict] = {
    "reach": {"label": "Reach", "what": "Show it to as many different people as possible.",
              "rarity": "common",
              "per_week_note": "Impressions are abundant, so the threshold is rarely the binding "
                               "constraint. Frequency is what to watch instead."},
    "impressions": {"label": "Impressions / frequency", "what": "Buy repeated exposure to the same "
                    "people.", "rarity": "common",
                    "per_week_note": "Also abundant. The question is whether the frequency you get is "
                                     "the frequency you wanted, which the plan states and this does "
                                     "not."},
    "video_views": {"label": "Video views", "what": "Optimise for a view of a defined length.",
                    "rarity": "common",
                    "per_week_note": "Cheap and abundant, and a view is not attention — define the "
                                     "length before comparing costs between cells."},
    "engagement": {"label": "Engagement", "what": "Reactions, comments, shares, saves.",
                   "rarity": "moderate",
                   "per_week_note": "Common enough to clear the threshold in most cells, and the "
                                    "least connected to whether anything was bought."},
    "traffic": {"label": "Link clicks / traffic", "what": "Send people to a destination.",
                "rarity": "moderate",
                "per_week_note": "Usually clears the threshold. A click is not a visit — the landing "
                                 "page decides that, and this plan cannot see it."},
    "leads": {"label": "Leads", "what": "A form completion or a message started.",
              "rarity": "rare",
              "per_week_note": "Rare enough that the threshold bites. Fifty a week per cell is the "
                               "bar, and dividing the budget does not divide it."},
    "conversions": {"label": "Conversions / purchases", "what": "A purchase or a defined action off "
                    "platform.", "rarity": "rare",
                    "per_week_note": "The rarest and the one the threshold was written about. This is "
                                     "where a fine geographic split stops being affordable."},
}

SPLIT_LEVELS: dict[str, dict] = {
    "national": {"label": "National", "what": "One cell for India.",
                 "note": "Cheapest per thousand and blind to geography. Nothing to compare."},
    "state": {"label": "State / UT", "what": "One cell per state or union territory.",
              "note": "The natural unit: it is how language, distribution and trade are organised, and "
                      "Meta targets it directly as a region."},
    "city": {"label": "City", "what": "One cell per city.",
             "note": "Meta's city entity is not the Census city — it is the platform's own boundary "
                     "with an optional radius. Population prioritises; it does not target."},
    "pincode": {
        "label": "Pincodes within a city", "what": "One cell for a named list of pincodes.",
        "note": "Finer than a city and coarser than a pin. A CITY cell already means every pincode in "
                "it — this level is for deliberately buying some and not others, which is a "
                "distribution decision before it is a media one. Pincodes are entered, not chosen from "
                "a list: this studio holds no pincode directory, so the format is checked (six digits, "
                "not starting zero) and existence is not. A typo that is still six digits will be "
                "accepted here and rejected by the platform.",
    },
    "radius": {"label": "Pin and radius", "what": "A dropped pin with a radius in kilometres.",
               "note": "1 km to 70 km outside the US. Tightening the radius raises CPM sharply — a "
                       "very tight radius can cost several times a wide one per thousand impressions, "
                       "for the same people seen more often. Useful for a store catchment, expensive "
                       "as a way to cover a city."},
}

# What a cost benchmark is worth. Same logic as `mediaplan.SOURCE_KINDS`: provenance decides what may
# be computed from it, and the studio's own history is the only kind worth much.
BENCHMARK_KINDS: dict[str, dict] = {
    "own_history": {
        "label": "This brand's own past campaigns", "trust": "high",
        "note": "The only benchmark that knows this brand's creative, offer and audience. Name the "
                "campaign and the window it came from.",
    },
    "platform_estimate": {
        "label": "Ads Manager estimate", "trust": "medium",
        "note": "The platform's own forecast for this targeting. Real, and systematically optimistic "
                "about what a new advertiser will pay.",
    },
    "category": {
        "label": "Category or agency benchmark", "trust": "low",
        "note": "A number from outside this brand. Usable to size an order of magnitude and not to "
                "plan against — cite whose it is and for which market and quarter.",
    },
}

# Stated as a table because these are decisions to be made, not problems to be solved, and a screen
# that lists them is doing more good than one that picks for you. Each carries what is actually known.
TRADEOFFS: tuple[dict, ...] = (
    {"id": "pooling",
     "question": "One pooled budget, or a budget per geography?",
     "gain": "Pooled money finds the cheapest result on its own, continuously.",
     "give_up": "Pooled money starves expensive markets, and the expensive ones are usually the new "
                "and the small. You also lose the comparison — a market that was never funded cannot "
                "be said to have failed.",
     "resolve": "Per-cell budgets while you are still learning which geographies work; pooled with "
                "minimum floors once you know. The floor is what keeps a strategic market alive.",
     "source": "Meta budget-optimisation documentation and consistent 2026 practitioner guidance — "
               "test with per-ad-set budgets, scale with campaign budget."},
    {"id": "depth",
     "question": "How fine can the geography split go?",
     "gain": "A finer split buys precision: different creative, language and weight per market, and a "
             "readable result per market.",
     "give_up": "Every cell needs its own ~50 events in 7 days. The budget does not get bigger when "
                "you divide it, so past a certain number of cells none of them can leave the learning "
                "phase and the whole campaign is delivered by a model that never got to learn.",
     "resolve": "Compute it rather than argue it — `feasibility` divides the weekly budget by the cost "
                "per action and by the number of cells. If the answer is under 50, the split is too "
                "fine for the money, and the fix is fewer cells or a cheaper optimisation event.",
     "source": LEARNING_SOURCE},
    {"id": "radius",
     "question": "Cover a city, or tighten to a catchment?",
     "gain": "A tight radius reaches the people who can actually walk in.",
     "give_up": "Cost per thousand rises steeply as the radius shrinks, and frequency rises with it — "
                "the same small group seen many times over. A very tight radius can cost several times "
                "a wide one per thousand impressions.",
     "resolve": "Tight radii for a store or a launch catchment where the walk-in is the point. City or "
                "state cells for anything meant to build a brand, where the same money buys "
                "materially more people.",
     "source": "Meta location-targeting mechanics: 1–70 km radius outside the US; CPM and frequency "
               "both rise as the radius narrows"},
    {"id": "language",
     "question": "Buy a state whose language the studio cannot write?",
     "gain": "Coverage on the map, and a media plan that looks complete.",
     "give_up": "The message. Creative in a language people there do not speak first is a media cost "
                "with nothing behind it, and it reads as an outsider talking.",
     "resolve": "`geo.language_gaps` lists them before the money is committed. Either commission the "
                "language or drop the state — buying it in Hindi and hoping is the third option and it "
                "is the one that quietly wastes the budget.",
     "source": "geo.STATES — the studio's own held-language list against each state's principal language"},
)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _money(v, currency: str = "") -> str:
    """A budget figure as a person reads it, grouped for its own currency.

    `%g` was here first and turned 1,100,000 into `1.1e+06` inside a sentence about whether a plan
    reconciles. Scientific notation is unreadable for money and it hides precision at exactly the
    magnitudes this module deals in, which is every rupee figure it will ever hold.

    Indian grouping for INR — 40,00,000 rather than 4,000,000 — because a plan denominated in rupees is
    read by people who count in lakhs, and a Western-grouped rupee figure gets misread by a factor of
    ten often enough to matter.
    """
    try:
        n = float(v)
    except (TypeError, ValueError):
        return str(v)
    neg = n < 0
    whole = int(abs(n))
    frac = abs(n) - whole
    s = str(whole)
    if str(currency or "").upper() == "INR" and len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    else:
        s = f"{whole:,}"
    if frac >= 0.005:
        s += f"{frac:.2f}"[1:]
    return ("-" if neg else "") + s


def _path(sid: str) -> str:
    return os.path.join(DIR, f"{sid}.json")


def load(sid: str) -> dict | None:
    try:
        with open(_path(str(sid)), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def save(d: dict) -> dict:
    os.makedirs(DIR, exist_ok=True)
    d["updated"] = _now()
    path = _path(d["id"])
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return d


def listing() -> list[dict]:
    out = []
    for f in sorted(os.listdir(DIR)) if os.path.isdir(DIR) else []:
        if not f.endswith(".json"):
            continue
        d = load(f[:-5])
        if d:
            out.append({"id": d["id"], "name": d.get("name", ""), "brand": d.get("brand", ""),
                        "plan": d.get("plan", ""), "cells": len(d.get("cells") or []),
                        "budget": d.get("budget"), "currency": d.get("currency", ""),
                        "updated": d.get("updated", "")})
    return sorted(out, key=lambda r: r["updated"], reverse=True)


def new_plan(brand: str, name: str = "", plan_id: str = "") -> tuple[dict | None, str]:
    if not str(brand or "").strip():
        return None, "Name the brand this campaign is for."
    d = {
        "id": uuid.uuid4().hex[:10], "brand": str(brand).strip(),
        "name": str(name or "").strip() or "Social campaign",
        "plan": str(plan_id or "").strip(),
        "created": _now(), "updated": _now(),
        "objective": "", "optimisation": "", "budget": None, "currency": "", "days": 0,
        "budget_mode": "per_cell",     # the safer default: nothing gets starved until someone chooses
        "split_level": "state",
        "benchmark": None,             # {cpa?, cpm?, kind, source, as_of}
        "cells": [],
    }
    return save(d), ""


def set_frame(d: dict, *, objective: str = None, optimisation: str = None, budget=None,
              currency: str = None,
              days=None, budget_mode: str = None, split_level: str = None) -> tuple[dict | None, str]:
    """The campaign's frame — what it is for, how much, over how long, held how."""
    if optimisation is not None:
        o = str(optimisation).strip().lower()
        if o and o not in OPTIMISATION:
            return None, (f"Unknown optimisation event {o!r}. One of: {', '.join(OPTIMISATION)}. This "
                          f"is what the platform counts toward the learning threshold, which is why it "
                          f"is not the same field as the strategic objective.")
        d["optimisation"] = o
    if objective is not None:
        o = str(objective).strip().lower()
        if o and o not in plan_mod.ROLES:
            return None, f"Unknown objective {o!r}. One of: {', '.join(plan_mod.ROLES)}."
        d["objective"] = o
    if budget is not None:
        try:
            v = float(str(budget).replace(",", "").strip())
        except (TypeError, ValueError):
            return None, f"Budget {budget!r} is not a number."
        if v <= 0:
            return None, "A budget has to be a positive number."
        d["budget"] = v
    if currency is not None:
        c = str(currency).strip().upper()
        if d.get("budget") is not None and not c:
            return None, "Give the currency — every cost figure here is compared against the budget."
        d["currency"] = c
    if days is not None:
        try:
            n = int(str(days).strip())
        except (TypeError, ValueError):
            return None, f"Days {days!r} is not a whole number."
        if n < 0:
            return None, "A flight cannot run for a negative number of days."
        d["days"] = n
    if budget_mode is not None:
        m = str(budget_mode).strip().lower()
        if m not in BUDGET_MODES:
            return None, f"Unknown budget mode {m!r}. One of: {', '.join(BUDGET_MODES)}."
        d["budget_mode"] = m
    if split_level is not None:
        s = str(split_level).strip().lower()
        if s not in SPLIT_LEVELS:
            return None, f"Unknown split level {s!r}. One of: {', '.join(SPLIT_LEVELS)}."
        d["split_level"] = s
    if d.get("budget") is not None and not d.get("currency"):
        return None, "Give the currency — every cost figure here is compared against the budget."
    return d, ""


def set_benchmark(d: dict, *, kind: str, source: str, cpa=None, cpm=None,
                  as_of: str = "") -> tuple[dict | None, str]:
    """The cost benchmark the feasibility arithmetic runs on. Entered, sourced, never assumed.

    There is deliberately no default. A default CPA would make `feasibility` produce a confident answer
    about whether a geography split can run, computed from a number nobody chose — and that answer
    would be acted on. Better to refuse until someone says what this brand actually pays.
    """
    k = str(kind or "").strip().lower()
    if k not in BENCHMARK_KINDS:
        return None, f"Unknown benchmark kind {k!r}. One of: {', '.join(BENCHMARK_KINDS)}."
    src = str(source or "").strip()
    if not src:
        return None, (f"Name the source. {BENCHMARK_KINDS[k]['label']} without a citation cannot be "
                      f"checked, and the whole feasibility check is computed from this number.")
    vals = {}
    for key, raw in (("cpa", cpa), ("cpm", cpm)):
        if raw in (None, ""):
            continue
        try:
            v = float(str(raw).replace(",", "").strip())
        except (TypeError, ValueError):
            return None, f"{key.upper()} {raw!r} is not a number."
        if v <= 0:
            return None, f"{key.upper()} has to be a positive number."
        vals[key] = v
    if not vals:
        return None, ("Give a cost per action, a cost per thousand, or both. A conversion objective is "
                      "judged on CPA and a reach objective on CPM — without the relevant one there is "
                      "no arithmetic to run.")
    d["benchmark"] = {"kind": k, "source": src, "as_of": str(as_of or "").strip()[:10],
                      "trust": BENCHMARK_KINDS[k]["trust"], "at": _now(), **vals}
    return d, ""


# Column names a person actually types, mapped to the cell fields they mean. Matched on a normalised
# header (lowercased, non-letters stripped), so "Budget (INR)" and "budget_inr" both land on `budget`.
# Deliberately explicit rather than fuzzy: a near-match that guesses wrong puts money on the wrong row.
IMPORT_COLUMNS: dict[str, tuple[str, ...]] = {
    "state":    ("state", "stateut", "statename", "region", "st"),
    "name":     ("city", "cityname", "town", "name", "geography", "market", "place"),
    "pincodes": ("pincode", "pincodes", "pin", "pins", "pincode", "pincodelist"),
    "budget":   ("budget", "spend", "amount", "budgetinr", "spendinr", "money"),
    "floor":    ("floor", "minimum", "minspend", "minimumspend", "floorinr"),
    "phase":    ("phase", "flight", "window"),
    "priority": ("priority", "strategic"),
    "note":     ("note", "notes", "comment", "comments", "remark", "remarks"),
    "radius_km": ("radius", "radiuskm", "km"),
    "level":    ("level", "splitlevel", "granularity"),
}


def _norm_header(s: str) -> str:
    return "".join(ch for ch in str(s or "").lower() if ch.isalpha())


def map_columns(header: list) -> dict:
    """Header row -> {field: column index}. Unrecognised columns are reported, not silently dropped."""
    found: dict[str, int] = {}
    unknown: list[str] = []
    for i, cell in enumerate(header or []):
        n = _norm_header(cell)
        if not n:
            continue
        hit = next((f for f, names in IMPORT_COLUMNS.items() if n in names), "")
        if hit and hit not in found:
            found[hit] = i
        elif not hit:
            unknown.append(str(cell))
    return {"columns": found, "unknown": unknown}


def propose_cells(d: dict, rows: list, level_hint: str = "") -> dict:
    """Turn spreadsheet rows into PROPOSED cells. Writes nothing.

    **Every proposal is validated through `add_cell` itself**, against a scratch copy of the plan, and
    the refusal text a row gets is the one it would get if somebody typed it. That is the whole design:
    a second set of rules here would drift from the real ones, and an import that accepted what the form
    refuses is how a spreadsheet becomes the way around a validator.

    The scratch copy also means the dedupe is real — two identical rows in one sheet refuse the second,
    naming the first, exactly as typing them would.

    Returns `{ok, columns, unknown_columns, proposed, refused, header, note}`. `proposed` rows are cells
    as `add_cell` built them; nothing is saved until a person posts them.
    """
    rows = [r for r in (rows or []) if any(str(c or "").strip() for c in r)]
    if not rows:
        return {"ok": False, "note": "That file has no rows with anything in them.",
                "columns": {}, "unknown_columns": [], "proposed": [], "refused": [], "header": []}

    m = map_columns(rows[0])
    cols, unknown = m["columns"], m["unknown"]
    has_header = bool(cols)
    if not has_header:
        return {"ok": False, "columns": {}, "unknown_columns": [str(c) for c in rows[0]],
                "proposed": [], "refused": [], "header": [str(c) for c in rows[0]],
                "note": ("No column in the first row is one this reads. Name a column `state`, `city`, "
                         "`pincodes`, `budget`, `floor`, `phase`, `priority` or `note` — the first row "
                         "has to be a header, because a sheet without one cannot say which number is "
                         "the budget.")}

    scratch = {"cells": [], "split_level": (level_hint or d.get("split_level") or "state")}
    proposed, refused = [], []
    for n, row in enumerate(rows[1:], start=2):
        def cell(field):
            i = cols.get(field)
            return str(row[i]).strip() if i is not None and i < len(row) else ""
        item = {f: cell(f) for f in cols}
        item = {k: v for k, v in item.items() if v != ""}
        if not item:
            continue
        item.setdefault("level", level_hint or scratch["split_level"])
        before = len(scratch["cells"])
        out, err = add_cell(scratch, dict(item))
        if err or out is None:
            refused.append({"row": n, "given": item, "why": err or "This row could not be read."})
            continue
        if len(scratch["cells"]) > before:
            proposed.append(scratch["cells"][-1])
        else:
            proposed.append(scratch["cells"][-1] if scratch["cells"] else item)

    return {
        "ok": bool(proposed),
        "columns": cols, "unknown_columns": unknown,
        "header": [str(c) for c in rows[0]],
        "proposed": proposed, "refused": refused,
        "writes_nothing": True,
        "note": (f"{len(proposed)} row(s) read, {len(refused)} refused. Nothing is saved yet — every "
                 f"proposal was checked by the same rules the form uses, so what is offered here is "
                 f"what typing it would have produced."),
    }


def add_cell(d: dict, item: dict) -> tuple[dict | None, str]:
    """One geography that holds money. Returns (plan, error).

    Geography resolves through `geo`, so a state is a state and not a spelling. A city is checked
    against the seeded list only as a *hint* — the seed is knowingly incomplete, so an unseeded city is
    allowed through with a flag rather than refused. Refusing it would make the seed's own gap look
    like a rule about the world.
    """
    level = str(item.get("level") or d.get("split_level") or "state").strip().lower()
    if level not in SPLIT_LEVELS:
        return None, f"Unknown level {level!r}. One of: {', '.join(SPLIT_LEVELS)}."

    state = geo.resolve_state(item.get("state") or "")
    name = str(item.get("name") or "").strip()
    seeded = None
    if level == "state":
        if not state:
            return None, (f"{item.get('state')!r} is not a state or union territory. Names and codes "
                          f"both work — 'Maharashtra', 'mh', even 'Orissa'.")
        name = geo.state_label(state)
    elif level in ("city", "radius", "pincode"):
        if not name:
            return None, "Name the city."
        hit = [c for c in geo.seed_cities() if c["name"].lower() == name.lower()]
        if hit:
            seeded = hit[0]
            state = state or seeded["state"]
            name = seeded["name"]
        if not state:
            return None, (f"Name the state {name} is in. It is not in the seeded city list, which "
                          f"stops about fifteen cities short in the 9.6-12 lakh band, so the state "
                          f"cannot be inferred from the name alone.")
    elif level == "national":
        name = name or "India"

    # Pincodes: format checked, existence not, and the difference said out loud. There is no pincode
    # directory in this studio, so "530068 is a real pincode" is not a claim it can make — six digits
    # not starting zero is. A typo that passes here fails at the platform, which is a better place for
    # it to fail than a silent cell that buys nothing.
    pincodes = None
    if level == "pincode":
        raw = item.get("pincodes")
        parts = ([str(x) for x in raw] if isinstance(raw, (list, tuple))
                 else [p for p in re.split(r"[,\s;]+", str(raw or "")) if p])
        parts = [p.strip() for p in parts if p.strip()]
        if not parts:
            return None, ("A pincode cell needs at least one pincode. If you mean the whole city, use "
                          "a CITY cell — that already covers every pincode in it.")
        bad = [p for p in parts if not re.fullmatch(r"[1-9][0-9]{5}", p)]
        if bad:
            return None, (f"Not a pincode format: {', '.join(bad[:6])}. Indian pincodes are six digits "
                          f"and do not start with zero. Whether a well-formed one exists is not "
                          f"something this studio can check — the platform will tell you.")
        seen: list[str] = []
        for p in parts:
            if p not in seen:
                seen.append(p)
        pincodes = seen

    radius = None
    if level == "radius":
        try:
            radius = float(str(item.get("radius_km") or "").strip())
        except (TypeError, ValueError):
            return None, "A radius cell needs a radius in kilometres."
        if not 1 <= radius <= 70:
            return None, ("Radius must be between 1 and 70 km — that is the range Meta allows outside "
                          "the US. Note that tightening it raises cost per thousand steeply.")

    budget = None
    if item.get("budget") not in (None, ""):
        try:
            budget = float(str(item["budget"]).replace(",", "").strip())
        except (TypeError, ValueError):
            return None, f"Cell budget {item['budget']!r} is not a number."
        if budget < 0:
            return None, "A cell budget cannot be negative."

    floor = None
    if item.get("floor") not in (None, ""):
        try:
            floor = float(str(item["floor"]).replace(",", "").strip())
        except (TypeError, ValueError):
            return None, f"Floor {item['floor']!r} is not a number."
        if floor < 0:
            return None, "A minimum-spend floor cannot be negative."

    cid = str(item.get("id") or "").strip() or uuid.uuid4().hex[:8]
    cells = d.setdefault("cells", [])
    dupe = [c for c in cells if c.get("id") != cid and c.get("level") == level
            and c.get("name", "").lower() == name.lower()
            and str(c.get("radius_km") or "") == str(radius or "")
            # Two pincode cells in one city are only duplicates if they buy the SAME pincodes — the
            # whole point of the level is buying some and not others.
            and sorted(c.get("pincodes") or []) == sorted(pincodes or [])]
    if dupe:
        return None, (f"{name} is already a cell at this level. Two cells for one geography compete "
                      f"with each other in the same auction and split their own events between them, "
                      f"which is the one thing that makes both look worse than either would alone.")

    row = {
        "id": cid, "level": level, "name": name, "state": state,
        "state_label": geo.state_label(state) if state else "",
        "radius_km": radius, "budget": budget, "floor": floor,
        # Stored as a list, and `n_pincodes` beside it so a screen can say "12 pincodes in Hyderabad"
        # without counting a string. Empty for every other level.
        "pincodes": pincodes or [],
        "n_pincodes": len(pincodes or []),
        "phase": str(item.get("phase") or "").strip(),
        "priority": str(item.get("priority") or "").strip().lower(),   # strategic | standard
        "note": str(item.get("note") or "").strip(),
        "pop": (seeded or {}).get("pop"),
        "pop_basis": "census_2011_city" if seeded else "",
        "seeded": bool(seeded),
        "languages": geo.languages_of(state) if state else [],
        "principal_language": geo.principal_language_of(state) if state else "",
        "added": _now(),
    }
    for i, c in enumerate(cells):
        if c.get("id") == cid:
            row["added"] = c.get("added", row["added"])
            cells[i] = row
            return d, ""
    cells.append(row)
    return d, ""


def drop_cell(d: dict, cid: str) -> tuple[dict | None, str]:
    cells = d.setdefault("cells", [])
    if not any(c.get("id") == cid for c in cells):
        return None, "No cell with that id."
    d["cells"] = [c for c in cells if c.get("id") != cid]
    return d, ""


# --------------------------------------------------------------------------------------
# The arithmetic
# --------------------------------------------------------------------------------------

def _weekly(d: dict) -> float | None:
    """The budget as a weekly rate, because the learning-phase window is weekly."""
    b, days = d.get("budget"), int(d.get("days") or 0)
    if b is None or days <= 0:
        return None
    return float(b) / days * LEARNING_WINDOW_DAYS


def feasibility(d: dict) -> dict:
    """Can this geography split actually run? The one check worth doing before any money moves.

    For a conversion objective the constraint is hard and arithmetic: each cell needs about 50
    optimisation events in a rolling week, and dividing the budget does not divide the threshold. So
    `max_cells` is the number of cells the money can actually support, and if the plan has more than
    that, the plan does not work — not because it is badly judged, but because it cannot be delivered.

    For a reach objective the 50-event rule does not apply, and this returns the impression arithmetic
    instead **without a verdict**. There is no defensible universal "right" frequency, so inventing a
    threshold here would be exactly the kind of confident number this codebase refuses. The planner
    gets the maths and makes the call.
    """
    cells = list(d.get("cells") or [])
    bm = d.get("benchmark") or {}
    weekly = _weekly(d)
    role = str(d.get("objective") or "")
    out = {
        "objective": role, "objective_note": plan_mod.ROLES.get(role, ""),
        "cells": len(cells), "weekly_budget": weekly, "currency": d.get("currency", ""),
        "rule": LEARNING_EVENTS, "window_days": LEARNING_WINDOW_DAYS, "rule_source": LEARNING_SOURCE,
        "available": False, "verdict": "", "verdict_label": "", "why": "",
    }
    if not cells:
        out["why"] = "No cells yet. There is no split to test."
        return out
    if weekly is None:
        out["why"] = ("Needs a budget and a flight length. The learning-phase threshold is weekly, so "
                      "a total with no duration cannot be turned into a weekly rate.")
        return out
    if not bm:
        out["why"] = ("No cost benchmark entered. Every number here divides by a cost per action or a "
                      "cost per thousand, and there is deliberately no default — a feasibility verdict "
                      "computed from an assumed cost would be acted on as though it meant something.")
        return out

    # Conversion and advocacy are judged on events; reach and proof are not.
    events_rule = role in ("conversion", "advocacy")
    cpa, cpm = bm.get("cpa"), bm.get("cpm")

    if events_rule:
        if not cpa:
            out["why"] = (f"A {role} objective is judged on cost per action, and the benchmark has only "
                          f"a cost per thousand. Enter a CPA.")
            return out
        per_cell_weekly = weekly / len(cells)
        events_per_cell = per_cell_weekly / cpa
        max_cells = int(weekly // (LEARNING_EVENTS * cpa))
        out.update({
            "available": True, "basis": "events",
            "cpa": cpa, "per_cell_weekly": round(per_cell_weekly, 2),
            "events_per_cell_weekly": round(events_per_cell, 1),
            "max_cells": max_cells,
            "total_events_weekly": round(weekly / cpa, 1),
            "needed_weekly_for_current_split": round(len(cells) * LEARNING_EVENTS * cpa, 2),
        })
        if events_per_cell >= LEARNING_EVENTS:
            out["verdict"] = "runnable"
            out["why"] = (f"Each of the {len(cells)} cells clears roughly "
                          f"{out['events_per_cell_weekly']} events a week against a threshold of "
                          f"{LEARNING_EVENTS}. The split is supportable at this budget.")
        elif max_cells <= 0:
            out["verdict"] = "impossible"
            cur = d.get("currency", "")
            out["why"] = (f"At {_money(cpa, cur)} per action, a single cell needs "
                          f"{_money(LEARNING_EVENTS * cpa, cur)} {cur} a week to leave the "
                          f"learning phase and the whole campaign has {_money(weekly, cur)}. "
                          f"No split works, "
                          f"including one cell — the budget is below the platform's learning threshold "
                          f"for this cost per action.")
        else:
            out["verdict"] = "too_fine"
            cur = d.get("currency", "")
            out["why"] = (f"{len(cells)} cells at {_money(cpa, cur)} per action need "
                          f"{_money(out['needed_weekly_for_current_split'], cur)} "
                          f"{cur} a week; there is {_money(weekly, cur)}. Each cell would get "
                          f"about {out['events_per_cell_weekly']} events against a threshold of "
                          f"{LEARNING_EVENTS}, so none of them would leave the learning phase. This "
                          f"budget supports about {max_cells} cell(s) — group the rest, or optimise "
                          f"for a cheaper event.")
        out["verdict_label"] = VERDICT_LABEL.get(out["verdict"], out["verdict"])
        return out

    # Reach and proof: report the arithmetic, assert nothing.
    if not cpm:
        out["why"] = (f"A {role or 'reach'} objective is judged on coverage, and the benchmark has only "
                      f"a cost per action. Enter a CPM.")
        return out
    impressions = weekly / cpm * 1000.0
    pop_cells = [c for c in cells if c.get("pop")]
    base = sum(int(c["pop"]) for c in pop_cells) if pop_cells else None
    out.update({
        "available": True, "basis": "impressions", "cpm": cpm,
        "impressions_weekly": int(impressions),
        "impressions_per_cell_weekly": int(impressions / len(cells)),
        "population_base": base,
        "population_basis": "census_2011_city" if base else "",
        "population_cells": len(pop_cells), "cells_without_population": len(cells) - len(pop_cells),
        "verdict": "reported",
        "why": ("Reach objectives are not bound by the learning-phase event threshold, so there is no "
                "pass or fail here — this is the impression arithmetic and the judgement is yours. "
                "There is no defensible universal target frequency, so none is asserted."),
    })
    out["verdict_label"] = VERDICT_LABEL.get(out["verdict"], out["verdict"])
    if base:
        out["implied_weekly_frequency"] = round(impressions / base, 2)
        out["frequency_caveat"] = (
            "Impressions divided by a Census 2011 municipal population. That population is fifteen "
            "years old, it is not the platform's own boundary, and it counts people rather than "
            "reachable accounts — so treat this as an order of magnitude and read the platform's "
            "estimated audience for the real denominator. " + geo.POP_BASIS["platform_reach"]["caveat"])
    return out


def allocation(d: dict, mode: str = "equal") -> dict:
    """How the money divides across cells. `equal`, `population`, or `entered`.

    `population` is offered and fenced: it splits by Census 2011 municipal figures, which is a
    reasonable proxy for how much of the country a city is and a poor one for how many reachable
    accounts it holds. Cells without a figure on that basis make it unavailable rather than getting
    zero — the same refusal as `mediaplan._share_block`, and for the same reason. A silent zero for a
    city nobody has a population for looks exactly like a decision to skip it.
    """
    cells = list(d.get("cells") or [])
    total = d.get("budget")
    out = {"mode": mode, "currency": d.get("currency", ""), "total": total,
           "available": False, "rows": [], "why": ""}
    if not cells:
        out["why"] = "No cells to allocate across."
        return out
    if total is None:
        out["why"] = "No budget set."
        return out

    if mode == "equal":
        share = float(total) / len(cells)
        out["rows"] = [{"id": c["id"], "name": c["name"], "amount": round(share, 2),
                        "share": round(100.0 / len(cells), 1)} for c in cells]
        out["available"] = True
        out["note"] = ("Equal money per geography, which is equal only in rupees — a cell covering "
                       "Uttar Pradesh and a cell covering Ulhasnagar are not comparable jobs.")
        return out

    if mode == "population":
        missing = [c["name"] for c in cells if not c.get("pop")]
        if missing:
            out["why"] = (f"No population on the census basis for {', '.join(missing)}. Splitting money "
                          f"by population with figures missing would give those cells nothing and "
                          f"inflate every other share, and the shares would still add to 100 — so "
                          f"there would be nothing on screen to show it happened. Enter their figures, "
                          f"or allocate equally.")
            return out
        base = sum(int(c["pop"]) for c in cells)
        out["rows"] = [{"id": c["id"], "name": c["name"], "pop": c["pop"],
                        "amount": round(float(total) * int(c["pop"]) / base, 2),
                        "share": round(100.0 * int(c["pop"]) / base, 1)} for c in cells]
        out["available"] = True
        out["basis"] = "census_2011_city"
        out["note"] = ("Split by Census 2011 municipal population. That is a measure of how much of the "
                       "country a city is, not of how many reachable accounts it has, and the two "
                       "diverge most in exactly the smaller cities a growth plan cares about.")
        return out

    if mode == "entered":
        missing = [c["name"] for c in cells if c.get("budget") is None]
        if missing:
            out["why"] = f"No budget entered for {', '.join(missing)}."
            return out
        got = sum(float(c["budget"]) for c in cells)
        out["rows"] = [{"id": c["id"], "name": c["name"], "amount": float(c["budget"]),
                        "share": round(100.0 * float(c["budget"]) / got, 1) if got else 0.0}
                       for c in cells]
        out["available"] = True
        out["entered_total"] = got
        out["reconciles"] = abs(got - float(total)) < 0.01
        if not out["reconciles"]:
            cur = d.get("currency", "")
            diff = got - float(total)
            out["note"] = (f"The cell budgets add to {_money(got, cur)} and the campaign budget is "
                           f"{_money(total, cur)} — a difference of "
                           f"{'+' if diff >= 0 else '-'}{_money(abs(diff), cur)}. One of the two is "
                           f"wrong, and which one is a decision rather than something to be rounded "
                           f"away.")
        return out

    out["why"] = f"Unknown allocation mode {mode!r}. One of: equal, population, entered."
    return out


def findings(d: dict) -> list[dict]:
    """What would make this campaign spend money badly."""
    out: list[dict] = []
    cells = list(d.get("cells") or [])
    fe = feasibility(d)

    if not cells:
        out.append({"level": "gap", "blocking": True, "what": "No geographies yet",
                    "why": "A geography-wise campaign needs at least one geography."})
    if d.get("budget") is None:
        out.append({"level": "gap", "blocking": True, "what": "No budget",
                    "why": "This module exists to hold the money. Without it nothing here computes."})
    elif not int(d.get("days") or 0):
        out.append({"level": "gap", "blocking": True, "what": "No flight length",
                    "why": "The learning-phase threshold is weekly, so a total with no duration cannot "
                           "be tested against it."})
    if not d.get("objective"):
        out.append({"level": "gap", "blocking": True, "what": "No objective",
                    "why": "A reach cell and a conversion cell are judged by different rules and only "
                           "one of them is bound by the 50-event threshold. Without the objective the "
                           "feasibility check does not know which arithmetic applies."})
    if not d.get("benchmark"):
        out.append({"level": "gap", "blocking": True, "what": "No cost benchmark",
                    "why": "Entered with a source, never assumed — every figure here divides by it."})
    elif (d["benchmark"].get("trust") == "low"):
        out.append({"level": "risk", "blocking": False, "what": "Benchmark is a category number",
                    "why": BENCHMARK_KINDS["category"]["note"] + " It will size the plan; it should not "
                           "be what the plan is committed against."})

    if fe.get("verdict") == "too_fine":
        out.append({"level": "risk", "blocking": True,
                    "what": f"The split is too fine for the budget — {fe['cells']} cells, "
                            f"about {fe['max_cells']} supportable",
                    "why": fe["why"]})
    elif fe.get("verdict") == "impossible":
        out.append({"level": "gap", "blocking": True,
                    "what": "Below the learning threshold at any split",
                    "why": fe["why"]})

    if d.get("budget_mode") == "pooled":
        unfloored = [c["name"] for c in cells
                     if c.get("priority") == "strategic" and not c.get("floor")]
        if unfloored:
            out.append({"level": "risk", "blocking": False,
                        "what": f"{len(unfloored)} strategic market(s) pooled with no floor",
                        "why": (f"{', '.join(unfloored)} are marked strategic and share a pooled "
                                f"budget with no minimum spend. Pooled money defunds expensive "
                                f"markets, and a market is usually marked strategic precisely because "
                                f"its media performance does not yet justify it. "
                                + BUDGET_MODES["pooled"]["mitigation"])})

    gaps = geo.language_gaps([c["state"] for c in cells if c.get("state")])
    if gaps:
        out.append({"level": "risk", "blocking": False,
                    "what": f"{len(gaps)} state(s) whose principal language the studio cannot write",
                    "why": ("; ".join(f"{g['label']}: {g['gap']}" for g in gaps)
                            + " Buying these in a language people there do not speak first is a media "
                              "cost with no message behind it.")})

    unseeded = [c["name"] for c in cells if c.get("level") in ("city", "radius") and not c.get("seeded")]
    if unseeded:
        out.append({"level": "note", "blocking": False,
                    "what": f"{len(unseeded)} city cell(s) not in the seeded list",
                    "why": (f"{', '.join(unseeded)} carry no population figure, so population-weighted "
                            f"allocation is unavailable while they are here. The seeded list stops "
                            f"about fifteen cities short in the 9.6-12 lakh band, so this is expected "
                            f"rather than wrong - split the budget by hand or drop these cells.")})

    order = {"gap": 0, "risk": 1, "note": 2}
    out.sort(key=lambda f: (not f["blocking"], order.get(f["level"], 3)))
    return out


def view(d: dict) -> dict:
    """The whole campaign screen in one payload."""
    fs = findings(d)
    cells = list(d.get("cells") or [])
    return {
        "plan": {k: d.get(k) for k in ("id", "name", "brand", "plan", "objective", "budget",
                                      "currency", "days", "budget_mode", "split_level",
                                      "benchmark", "created", "updated")},
        "cells": cells,
        "feasibility": feasibility(d),
        "allocation": {m: allocation(d, m) for m in ("equal", "population", "entered")},
        "tradeoffs": TRADEOFFS,
        "budget_modes": BUDGET_MODES,
        "split_levels": SPLIT_LEVELS,
        # Served beside the strategic objective, never merged with it. A screen that offered one
        # list would be asking one question for two decisions — and the threshold counts this one.
        "optimisation": OPTIMISATION,
        "optimisation_note": (
            "The strategic objective says what the channel is FOR; the optimisation event is what "
            "the platform counts. They share the words reach and conversion and are not the same "
            "field — the learning threshold of fifty a week counts the OPTIMISATION event, so fifty "
            "purchases and fifty link clicks are the same number and nowhere near the same bar."),
        "benchmark_kinds": BENCHMARK_KINDS,
        "objectives": plan_mod.ROLES,
        "language_gaps": geo.language_gaps([c["state"] for c in cells if c.get("state")]),
        "counts": {
            "cells": len(cells),
            "states": len({c["state"] for c in cells if c.get("state")}),
            "with_budget": sum(1 for c in cells if c.get("budget") is not None),
            "strategic": sum(1 for c in cells if c.get("priority") == "strategic"),
            "seeded": sum(1 for c in cells if c.get("seeded")),
        },
        "findings": fs,
        "blocking": [f["what"] for f in fs if f["blocking"]],
        "what_this_cannot_do": (
            "Say whether the campaign is working. That needs delivery data, and until a platform "
            "account is connected or the actuals are entered there are none — so nothing here ranks a "
            "geography by performance. What it does is check, before the money moves, whether the "
            "split can be delivered at all, and name the tradeoffs rather than resolve them."),
    }
