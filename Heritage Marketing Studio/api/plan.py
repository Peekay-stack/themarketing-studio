"""plan.py — the communication plan: who hears it, where, when, and how anyone will know.

The messaging house settles what is said and why it is true. This settles distribution. The spine:

    Brief -> Messaging house -> Communication plan -> Executions

A plan is **bound to a house**, and that binding is the reason this belongs in the portal rather
than in a chat window. Two things fall out of it that a document cannot do:

**Cross-document staleness.** Every layer records the house it was written against. Change the
functional message, or drop one of its reasons-to-believe, and every channel you assigned to *prove*
that pillar is flagged — immediately, by name. A house and a plan authored separately drift apart the
moment either moves, and nobody notices until a shelf strip contradicts a TV end-frame.

**The proof gate.** A channel may not be given the job of proving a pillar whose reasons-to-believe
are unsourced. That is not a style rule; it is the difference between a plan and a wish, and it is
checkable, so it is checked here rather than left to whoever reads the deck.

Layers are tables, not lists of prose — which is why this is a sibling of strategy.py rather than
more layers inside it. The engine ideas are the same; the node shapes are not.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid

import brandprofile
import findings as findings_mod
import geo
import jsonout
import media as media_mod
import project as project_mod
import strategy
import tenancy

# Resolved through tenancy so one deployment can hold several companies. The name is kept
# so every reader in this module is unchanged.
PLAN_DIR = tenancy.dir("plans")
_SKILL = os.path.join(os.path.dirname(__file__), "plan_skill")

# What each channel can be FOR. A reach channel judged on conversion always looks like a failure and
# a conversion channel judged on reach always looks like a triumph; naming the job prevents both.
ROLES = {
    "reach":      "Get to people who do not yet think of us. Judged on coverage and cost per reach.",
    "proof":      "Make a claim believable. Judged on whether the claim lands, not on clicks.",
    "conversion": "Turn intent into purchase. Judged on rate and cost per acquisition.",
    "advocacy":   "Get existing buyers to carry the message. Judged on participation.",
}
SIDES = ("brand", "activation")
DEFAULT_BRAND_SHARE = 60

# Where the 60 comes from, carried in the payload rather than only in a comment. A screen that shows a
# bare "60" is showing arithmetic; one that shows who says so and who disagrees is showing a position
# somebody can argue with — which is what it is.
#
# It is a genuinely contested number, and pretending otherwise would be the studio taking a side by
# omission. Binet and Field are the best-evidenced starting point available; Ehrenberg-Bass think the
# evidence is unsound. Both belong on the screen.
# The shape is `claim` / `source` / `dispute` / `note`, shared with `mediaplan.ESOV_BASIS` so a screen
# can render either without knowing which it has. `claim` is the sentence being asserted and is separate
# from `value`, the number — the two were conflated before, which left a citation on the wire with no
# statement of what it was a citation FOR.
BRAND_SHARE_BASIS: dict = {
    "value": DEFAULT_BRAND_SHARE,
    "claim": f"Split roughly {DEFAULT_BRAND_SHARE}/{100 - DEFAULT_BRAND_SHARE} brand to activation. "
             f"Long-term brand building and short-term activation do different jobs on different "
             f"timescales, and the long one is the one that gets cut first.",
    "source": "Binet & Field, The Long and the Short of It (IPA) — ~1,000 case studies. Roughly 0.5% "
              "annual share growth per 10 points of excess share of voice.",
    "dispute": "Ehrenberg-Bass (Byron Sharp), who hold the underlying awards data unsound and the "
               "rule too elastic to be a general theory, arguing for always-on reach instead.",
    "note": "A default, not a rule. Category, growth stage, distribution and margin all legitimately "
            "move it.",
}

LAYERS: list[dict] = [
    {"id": "objectives", "kind": "rows", "label": "Objectives ladder", "parents": [],
     "cols": ["level", "statement", "measure", "by_when"],
     "asks": ("Three rows — business, marketing, communication — each answerable to the one above. "
              "The business row carries a number and a date.")},
    {"id": "audiences", "kind": "rows", "label": "Audiences", "parents": ["objectives"],
     "cols": ["audience", "rank", "believes_now", "pillar"],
     "asks": ("In priority order, ranked 1..n. Each gets exactly ONE pillar — emotional or "
              "functional. An audience given every pillar has been given none.")},
    {"id": "channels", "kind": "rows", "label": "Channel roles", "parents": ["audiences"],
     "cols": ["channel", "medium", "role", "job", "measure", "side", "share", "owner", "lead"],
     "asks": (f"One job per channel from: {', '.join(ROLES)}. One lead channel. `medium` is which "
              f"one medium from the served list this channel runs in. `side` is brand or "
              f"activation, `share` its percentage of total spend — all channels together must add "
              f"up to 100 — and `owner` who runs it.")},
    {"id": "balance", "kind": "number", "label": "Brand / activation split", "parents": ["channels"],
     "asks": "The brand share as a whole number. Default 60. If you move it, say why."},
    {"id": "phases", "kind": "rows", "label": "Phasing", "parents": ["channels"],
     "cols": ["phase", "window", "occasion", "channels", "hands_over"],
     "asks": ("Built on buying occasions, not quarters. Each phase names the occasion it serves and "
              "what it hands to the next.")},
    {"id": "measures", "kind": "rows", "label": "Measures", "parents": ["channels"],
     "cols": ["role", "leading", "lagging", "would_tell_us_it_failed"],
     "asks": ("Per channel role. The last column is the one plans omit: what would tell you this is "
              "NOT working, decided before launch.")},
    {"id": "governance", "kind": "rows", "label": "Governance", "parents": [],
     "cols": ["who", "speaks_on", "boundary", "decides_changes"],
     "asks": "Boundaries come from the house's avoid list. Name who decides a change."},
]
LAYER_BY_ID = {l["id"]: l for l in LAYERS}


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _path(pid: str) -> str:
    return os.path.join(PLAN_DIR, f"{pid}.json")


def load(pid: str) -> dict | None:
    try:
        with open(_path(pid), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(p: dict) -> dict:
    os.makedirs(PLAN_DIR, exist_ok=True)
    p["updated"] = _now()
    tmp = _path(p["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(p, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path(p["id"]))
    return p


def plans() -> list[dict]:
    """Every plan, as the card the Strategy screen draws.

    Sent no count at all before this, so every plan — however far along — read *"0 of 7 layers written"*.
    Same drift as `strategy.houses()`; see the note there.

    `house_brand` is resolved here rather than on the client, because the card's alternative text is
    *"No house bound — the proof gate cannot run"*, and a plan that IS bound to a house should never show
    that sentence just because the name had to be looked up somewhere else.
    """
    os.makedirs(PLAN_DIR, exist_ok=True)
    order = [l["id"] for l in LAYERS]
    rowish = [l["id"] for l in LAYERS if l.get("kind") == "rows"]
    out = []
    for f in sorted(os.listdir(PLAN_DIR)):
        if not f.endswith(".json"):
            continue
        p = load(f[:-5])
        if not p:
            continue
        nodes = p.get("nodes", {})
        # A layer counts as written when it has rows. `balance` is a number, not rows, so it counts when
        # somebody has given it a reason — a default share nobody argued for is not a decision.
        done = sum(1 for lid in rowish if (nodes.get(lid) or {}).get("rows"))
        if str((p.get("balance") or {}).get("reason") or "").strip():
            done += 1
        nxt = next((lid for lid in order
                    if lid in rowish and not (nodes.get(lid) or {}).get("rows")), "")
        house_id = p.get("house", "")
        h = None
        if house_id:
            try:
                h = strategy.load(house_id)
            except Exception:
                h = None
        hb = (h or {}).get("brand", "") or ""
        try:
            blocking = sum(1 for x in validate(p, h) if x.get("level") == "blocking")
        except Exception:
            blocking = 0
        out.append({
            "id": p["id"], "brand": p.get("brand", ""), "house": house_id,
            # Round 5 (session persistence + picker labelling) — same gap as strategy.houses()'s card.
            "brand_mode": p.get("brand_mode") or "grounded",
            "project": project_mod.of(p) or project_mod.of(h),
            "project_source": p.get("project_source", ""),
            "label": project_mod.label(p if project_mod.of(p) else dict(p, project=project_mod.of(h))),
            "house_brand": hb or p.get("brand", ""),
            "created": p.get("created", ""), "updated": p.get("updated", ""),
            "written": done, "filled_layers": done, "progress": done,
            "total_layers": len(order),
            "next_layer": nxt, "complete": done >= len(order),
            "blocking": blocking,
            "stale": any(stale(p, lid, h) for lid in rowish),
        })
    out.sort(key=lambda r: r.get("updated", ""), reverse=True)
    return out


def new_plan(brand: str, house_id: str = "", brand_mode: str = "") -> dict:
    p = {"id": uuid.uuid4().hex[:10], "brand": brand or "Brand", "house": house_id,
         "created": _now(), "updated": _now(),
         # From the house it serves, which took it from the brief.
         "project": project_mod.of(strategy.load(house_id) if house_id else None),
         "balance": {"brand_share": DEFAULT_BRAND_SHARE, "reason": "", "basis": "year"},
         "geography": [],
         "status": "draft", "pending_approval": None, "approval_log": [],
         "nodes": {l["id"]: {"layer": l["id"], "rows": [], "sig": "", "house_under": ""}
                   for l in LAYERS},
         # Defaults from whichever house this plan was started against — a brand-new plan is Grounded
         # unless something upstream already said General. See BRAND_GROUNDING_MODES_PLAN.md.
         "brand_mode": brand_mode or "grounded"}
    return save(p)


def set_brand_mode(p: dict, mode: str) -> dict:
    """Change a plan's grounding mode after the fact — never locked to what it started as."""
    p["brand_mode"] = "general" if mode == "general" else "grounded"
    return save(p)


# --- priority geography: state x urban/rural x town class x cities (round 92) --------------------
#
# Not a LAYERS entry. Every real layer shares one mechanism — a model drafts rows, a person edits them,
# a steering note and a "Generate" button sit under the table — and geography has none of that: it is a
# deterministic reference-data picker (choose real places from `geo.py`) plus a computed rollup, never
# AI-drafted. Forcing it into the LAYERS shape would add a "Generate" button with nothing for it to do.
# Lives as its own top-level field instead, same tier as `balance`.

GEO_STRATA = ("urban", "rural")
GEO_TOWN_CLASSES = ("metro", "tier1", "restofurban")


def set_geography(p: dict, rows: list[dict]) -> dict:
    """Replace the plan's whole priority-geography selection in one call.

    One call for the whole list, not a per-row endpoint — the picker can add/remove/edit several rows
    (several states, several town classes each) before anything needs to reach the server, and resending
    the full list is what `plan.add_row`'s own sibling endpoints do NOT do (those are genuinely per-row
    because a layer's rows are independent facts; a geography selection is one set of choices considered
    together, which is also what makes deduplication below possible at all).

    An invalid state name is dropped rather than refusing the whole call — a person editing five rows
    should not lose four of them because the fifth has a typo.
    """
    clean = []
    seen = set()
    for r in rows or []:
        state = geo.resolve_state(r.get("state") or "")
        if not state:
            continue
        stratum = "rural" if str(r.get("stratum") or "").lower() == "rural" else "urban"
        town_class = str(r.get("town_class") or "").lower() if stratum == "urban" else ""
        if stratum == "urban" and town_class not in GEO_TOWN_CLASSES:
            town_class = "restofurban"
        cities = sorted({str(c).strip() for c in (r.get("cities") or []) if str(c).strip()}) \
            if town_class in ("metro", "tier1") else []
        # Two rows naming the exact same unit (the same state's whole rural population, entered twice;
        # the same city picked in two rows) would double the rollup below if both survived — folded here
        # rather than left for `geography_reach` to notice, so the stored list itself never carries a
        # contradiction a person would have to spot by reading it.
        key = (state, stratum, town_class, tuple(cities))
        if key in seen:
            continue
        seen.add(key)
        clean.append({"id": r.get("id") or uuid.uuid4().hex[:8], "state": state,
                      "stratum": stratum, "town_class": town_class, "cities": cities})
    p["geography"] = clean
    return save(p)


def geography_reach(p: dict) -> dict:
    """The rollup: population reached by the plan's current selection, deduplicated by geography UNIT
    (state + stratum + town class + city), not by row — two rows can still name the same unit two
    different ways (a city picked in one row and, separately, an aggregate band that already includes
    it is NOT the same unit, so that pairing is fine; the same city picked twice, or the same state's
    rural total entered twice, is the case this guards against), plus which of the studio's held
    languages cover the states actually selected.
    """
    rows = p.get("geography") or []
    units: dict[tuple, int] = {}
    states_used: set[str] = set()
    stale_states: set[str] = set()
    for r in rows:
        state = r.get("state", "")
        if not state:
            continue
        states_used.add(state)
        bd = geo.town_class_breakdown(state)
        if not bd:
            continue
        if bd.get("data_quality_flag"):
            stale_states.add(state)
        stratum, town_class = r.get("stratum", ""), r.get("town_class", "")
        if stratum == "rural":
            units[(state, "rural", "", "")] = bd["rural"]["pop"]
        elif town_class == "restofurban":
            units[(state, "urban", "restofurban", "")] = bd["restofurban"]["pop"]
        elif town_class in ("metro", "tier1"):
            by_name = {c["name"]: c["pop"] for c in bd[town_class]["cities"]}
            for city in (r.get("cities") or []):
                if city in by_name:
                    units[(state, "urban", town_class, city)] = by_name[city]
    total = sum(units.values())
    by_state: dict[str, int] = {}
    for (state, *_rest), pop in units.items():
        by_state[state] = by_state.get(state, 0) + pop
    return {
        "rows": rows,
        "total_population": total,
        "by_state": [{"state": s, "label": geo.STATES.get(s, {}).get("label", s),
                      "population": pop, "share": round(100 * pop / total, 1) if total else 0}
                     for s, pop in sorted(by_state.items(), key=lambda x: -x[1])],
        "language_gaps": geo.language_gaps(sorted(states_used)),
        "basis": "census_2011", "caveat": geo.CENSUS_2011_CAVEAT if units else "",
        "states_missing_data": sorted(s for s in states_used if not geo.town_class_breakdown(s)),
        "states_with_data_quality_flag": sorted(stale_states),
    }


# --- the house it is answerable to --------------------------------------------------------------

def house_fingerprint(house: dict | None) -> str:
    """A hash of the house decisions this plan depends on."""
    if not house:
        return ""
    parts = []
    for layer in ("core", "emotional", "functional", "culture"):
        node = house.get("nodes", {}).get(layer) or {}
        picked = set(node.get("chosen") or [])
        texts = sorted(o["text"] for o in node.get("options", []) if o["id"] in picked)
        parts.append(f"{layer}:{'~'.join(texts)}")
    # RTB evidence counts matter too: losing a sourced RTB invalidates proof work downstream.
    for layer in ("rtb_emotional", "rtb_functional"):
        s, t = pillar_evidence(house, layer.replace("rtb_", ""))
        parts.append(f"{layer}:{s}/{t}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


# What counts as sourced, in one place. It was written out twice - once here as a count and once where
# each RTB is listed - and the two disagreed, so a block could say "1 of 1 sourced" two lines above the
# RTB it had just labelled UNSOURCED. The proof gate reads this, so it has to mean one thing.
def _sourced(option: dict) -> bool:
    return str(option.get("source", "")).lower() in ("brief", "library", "user")


def pillar_evidence(house: dict | None, pillar: str) -> tuple[int, int]:
    """(sourced, chosen) reasons-to-believe behind a pillar. The proof gate reads this."""
    if not house:
        return 0, 0
    node = house.get("nodes", {}).get(f"rtb_{pillar}") or {}
    picked = set(node.get("chosen") or [])
    rows = [o for o in node.get("options", []) if o["id"] in picked]
    return sum(1 for o in rows if _sourced(o)), len(rows)


def pillar_text(house: dict | None, pillar: str) -> str:
    if not house:
        return ""
    node = house.get("nodes", {}).get(pillar) or {}
    picked = set(node.get("chosen") or [])
    return next((o["text"] for o in node.get("options", []) if o["id"] in picked), "")


# --- rows and staleness -------------------------------------------------------------------------

# A cell that must hold one of a fixed set. Told to the generator in `_COLUMN_RULES` and enforced here,
# because an instruction is not a constraint: `pillar` arrived holding a whole sentence and the one-pillar
# check then reported six pillars on one audience.
_ENUMS: dict[tuple[str, str], tuple[str, ...]] = {
    ("audiences", "pillar"): ("emotional", "functional"),
    ("channels", "role"): tuple(ROLES),
    ("channels", "side"): SIDES,
    ("objectives", "level"): ("business", "marketing", "communication"),
    ("measures", "role"): tuple(ROLES),
}


def _coerce(layer_id: str, col: str, value: str) -> str:
    """Pull a fixed-set cell back to its value when the model wrote a sentence around it.

    Finds the allowed word inside what came back rather than rejecting the row: "functional — 'Heritage
    moves every single day…'" plainly means `functional`, and dropping the row over it would lose an
    audience somebody wanted. Anything with no allowed word in it is left alone, so a genuinely odd value
    stays visible and gets flagged by `validate` rather than being silently rewritten.
    """
    allowed = _ENUMS.get((layer_id, col))
    if not allowed:
        return value
    v = value.strip()
    if v.lower() in allowed:
        return v.lower()
    hits = [a for a in allowed if re.search(rf"\b{re.escape(a)}\b", v, re.IGNORECASE)]
    return hits[0] if len(hits) == 1 else v


def add_row(p: dict, layer_id: str, row: dict, source: str = "user") -> dict:
    l = LAYER_BY_ID[layer_id]
    clean = {c: _coerce(layer_id, c, str(row.get(c, "") or "").strip()) for c in l["cols"]}
    clean.update({"id": uuid.uuid4().hex[:8], "source": source, "added": _now()})
    p["nodes"][layer_id]["rows"].append(clean)
    return save(p)


def edit_row(p: dict, layer_id: str, row_id: str, row: dict) -> dict | None:
    """Change cells in a row that already exists. Returns None if there is no such row.

    A row the author has edited becomes theirs. `source` flips to `user` on any change to a cell,
    which matters downstream: a model-written channel row that somebody has gone through and corrected
    is no longer a model suggestion, and continuing to mark it as one trains people to ignore the mark.

    Only the layer's own columns are writable. `id`, `source` and `added` are not — a client that
    could rewrite an id could silently detach a row from every execution pointing at it.
    """
    node = p["nodes"][layer_id]
    cols = LAYER_BY_ID[layer_id]["cols"]
    for r in node["rows"]:
        if r.get("id") != row_id:
            continue
        before = {c: r.get(c, "") for c in cols}
        for c in cols:
            if c in row:
                r[c] = str(row.get(c, "") or "").strip()
        if {c: r.get(c, "") for c in cols} != before:
            r["source"] = "user"
            r["edited"] = _now()
        return save(p)
    return None


def drop_row(p: dict, layer_id: str, row_id: str) -> dict:
    node = p["nodes"][layer_id]
    node["rows"] = [r for r in node["rows"] if r.get("id") != row_id]
    return save(p)


def set_balance(p: dict, brand_share: int, reason: str = "", basis: str = "year",
                source: str = "user") -> dict:
    """The split is the author's to set. Moving off the default asks for one sentence, not permission.

    Recorded rather than enforced: category, growth stage, distribution and margin all legitimately
    move it, and in six months somebody will ask why — the answer belongs in the plan.
    """
    share = max(0, min(100, int(brand_share)))
    # `declared` is the point of this write. Without it a deliberate 60 and an untouched one were the
    # same record, so the plan could not tell "we chose the Binet-Field optimum" from "nobody looked at
    # this yet" — and every split downstream inherited that ambiguity.
    #
    # `source` is a second, separate question: a row-generated suggestion and a person's own typed
    # reason both count as declared (every other layer already treats a model-written row as real
    # content, tagged rather than hidden) — but "the skill suggested this" and "I decided this" are not
    # the same claim, and this record used to make no distinction at all.
    p["balance"] = {"brand_share": share, "reason": reason.strip(),
                    "basis": basis if basis in ("year", "window") else "year",
                    "declared": True, "source": source if source in ("user", "model") else "user"}
    return save(p)


def balance_of(p: dict) -> dict:
    """The split as stored, with `declared` folded in for plans that predate the flag.

    Fold-on-read rather than a migration, the same way `_fold_routes` and `normalise_judged` work. An
    older plan that carries a reason plainly declared its split deliberately; one with no reason and
    the default value did not.
    """
    rec = dict((p or {}).get("balance") or {})
    share = int(rec.get("brand_share", DEFAULT_BRAND_SHARE))
    if "declared" not in rec:
        rec["declared"] = bool(str(rec.get("reason") or "").strip()) or share != DEFAULT_BRAND_SHARE
    # Every record without a `source` predates "Suggest a split" (round 58) — `/plan-balance` was the
    # only way to write this record before that, so it was necessarily a person's own entry.
    if "source" not in rec:
        rec["source"] = "user"
    rec["brand_share"] = share
    return rec


def _num(v: float) -> str:
    """A weight as a person wrote it: 40 not 40.0, 12.5 kept."""
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


def medium_suggestions(p: dict) -> dict:
    """Row id -> the medium its prose reads like, for rows that have not declared one.

    Served BESIDE the rows, never merged into them. A suggestion written onto the row is one save away
    from becoming a declaration nobody made, which is the trap `big_idea` needed `bigIdeaView` for.

    Only confident matches appear, and only for undeclared rows: once somebody picks a medium this
    stops second-guessing them. On the plans in this repo it fires on a minority of channels, because
    a name like "Outdoor / transit near residential clusters" leads with neither an id nor a label.
    """
    out: dict[str, dict] = {}
    for r in ((p.get("nodes") or {}).get("channels") or {}).get("rows") or []:
        if str(r.get("medium") or "").strip():
            continue
        s = media_mod.resolve_text(r.get("channel", ""))
        if s["confident"]:
            out[str(r.get("id") or "")] = {"medium": s["medium"], "label": s["label"]}
    return out


def actual_split(p: dict) -> dict:
    """What the channels actually add up to, versus what was declared.

    Weighted by share where it is known; by channel count where it is not. Which basis was used is
    reported, because a split computed on counts and one computed on spend are different claims.

    Three things this used to compute silently, all of them the same failure — a number arrived at on
    a basis nobody chose, printed with the confidence of one that was.

    Weights that did not sum to 100 were normalised by their own total: a column reading 40/20/15 came
    back as 57% brand, which is arithmetically true of the three-quarters that was filled in and says
    nothing about the plan. Nothing on screen could tell that apart from a complete column.

    A column filled on some rows and not others fell all the way back to channel count, so a plan with
    weights on four of seven channels reported identically to one with none. The half-done state was
    invisible, which is the state a person actually needs to see.

    `trusted` is served as a flag rather than left to be read off the basis sentence, because the Plan
    rail was colouring its warning by pattern-matching that prose (`/unknown|count/i`) and a reworded
    sentence would have silently turned the warning off.
    """
    rows = p["nodes"]["channels"]["rows"]
    if not rows:
        return {"brand": None, "activation": None, "basis": "no channels yet",
                "weighted": 0, "n_channels": 0, "sum": None, "sums_to_100": None, "trusted": False}
    shares = []
    for r in rows:
        try:
            shares.append(float(str(r.get("share", "")).replace("%", "").strip()))
        except ValueError:
            shares.append(None)
    entered = [s for s in shares if s is not None]
    n, n_weighted = len(rows), len(entered)
    entered_sum = round(sum(entered), 2) if entered else None
    sums_to_100 = (round(sum(entered)) == 100) if entered else None

    if n_weighted == n and sum(entered) > 0:
        total = sum(entered)
        brand = sum(s for s, r in zip(shares, rows) if r.get("side") == "brand")
        if sums_to_100:
            basis, trusted = "weighted by planned spend", True
        else:
            # Kept as a figure rather than withheld: it is the true ratio of the weight that WAS
            # entered, and the basis says so in the same breath. Withholding it would hide a 90/10
            # brand tilt just because the column adds to 95.
            basis = (f"weighted by planned spend — but the weights add up to "
                     f"{_num(entered_sum)}%, not 100, so this is a ratio of what was entered")
            trusted = False
    else:
        total = n
        brand = sum(1 for r in rows if r.get("side") == "brand")
        basis = (f"spend unknown on {n - n_weighted} of {n} channels — computed on channel count"
                 if n_weighted else "spend unknown — computed on channel count")
        trusted = False
    pct = round(100 * brand / total) if total else 0
    return {"brand": pct, "activation": 100 - pct, "basis": basis,
            "weighted": n_weighted, "n_channels": n, "sum": entered_sum,
            "sums_to_100": sums_to_100, "trusted": trusted}


def signature(p: dict, layer_id: str, house: dict | None) -> str:
    parents = LAYER_BY_ID[layer_id]["parents"]
    basis = []
    for par in parents:
        rows = p["nodes"].get(par, {}).get("rows", [])
        basis.append(f"{par}:{len(rows)}:" + "~".join(sorted(json.dumps(r, sort_keys=True) for r in rows)))
    basis.append("house:" + house_fingerprint(house))
    return hashlib.sha256("|".join(basis).encode("utf-8")).hexdigest()[:16]


def stale(p: dict, layer_id: str, house: dict | None) -> bool:
    node = p["nodes"].get(layer_id) or {}
    if not node.get("rows") or not node.get("house_under"):
        return False                      # hand-written rows are the author's, whatever moved above
    return node["house_under"] != signature(p, layer_id, house)


def mark_written(p: dict, layer_id: str, house: dict | None) -> dict:
    p["nodes"][layer_id]["house_under"] = signature(p, layer_id, house)
    return save(p)


# --- validation: the plan's own teeth -----------------------------------------------------------

def validate(p: dict, house: dict | None = None) -> list[dict]:
    out: list[dict] = []

    def add(level, layer, detail):
        out.append({"level": level, "layer": layer, "detail": detail})

    rows = {l["id"]: p["nodes"][l["id"]]["rows"] for l in LAYERS}

    # 0. a layer generated twice, with both attempts kept
    #
    # Generating no longer appends, but plans written before that fix are carrying two sets of rows and
    # nothing on the screen says so — the second set simply sits under the first and both print. It shows
    # up as a repeated first column: two rows both called "1 — Recognition", or two "business" objectives.
    # Named rather than cleaned up automatically, because deleting somebody's rows to tidy a list is not a
    # thing a document should do to itself.
    # Matching the first column does not find it: two generations produce *differently worded* phases,
    # so "1 — Recognition" and "1 — Make the dawn story known" are the same row written twice and share no
    # text. What they do share is when they arrived — one generation writes all its rows in the same
    # minute. Two clusters of model rows with different timestamps is a layer that was generated twice.
    for l in LAYERS:
        if l.get("kind") != "rows":
            continue
        batches: dict[str, int] = {}
        for r in rows[l["id"]]:
            if str(r.get("source", "")).lower() != "model":
                continue          # hand-written rows arrive whenever somebody types them
            batches[str(r.get("added", ""))] = batches.get(str(r.get("added", "")), 0) + 1
        runs = sorted((t for t, n in batches.items() if n >= 2), reverse=True)
        if len(runs) >= 2:
            add("open", l["id"],
                f"{l['label']} holds {sum(batches[t] for t in runs)} generated rows written in "
                f"{len(runs)} separate goes — the most recent at {runs[0]}, an earlier one at "
                f"{runs[-1]}. This layer was generated more than once and every attempt was kept, so the "
                f"document is printing two plans as one. Delete the set you do not want. Generating again "
                f"now replaces rather than adds.")

    # 1. the ladder
    levels = {str(r.get("level", "")).lower() for r in rows["objectives"]}
    for want in ("business", "marketing", "communication"):
        if rows["objectives"] and want not in levels:
            add("open", "objectives", f"No {want} objective — the ladder has a missing rung")
    for r in rows["objectives"]:
        if str(r.get("level", "")).lower() == "business" and not str(r.get("measure", "")).strip():
            add("blocking", "objectives",
                "The business objective carries no number. Everything below it is then unfalsifiable.")

    # 2. one pillar per audience, and ranked
    for r in rows["audiences"]:
        pillars = [x for x in re.split(r"[,/&+]| and ", str(r.get("pillar", ""))) if x.strip()]
        if len(pillars) > 1:
            add("blocking", "audiences",
                f"{r.get('audience','an audience')} is assigned {len(pillars)} pillars. One each — "
                f"an audience given both has been given neither, and the creative brief becomes "
                f"unwritable.")
        if not str(r.get("rank", "")).strip():
            add("open", "audiences", f"{r.get('audience','an audience')} has no rank")

    # 3. channels: one job, valid role, role/measure agreement, exactly one lead
    leads = [r for r in rows["channels"] if str(r.get("lead", "")).lower() in ("y", "yes", "true", "1")]
    if rows["channels"] and len(leads) != 1:
        add("open", "channels",
            f"{len(leads)} lead channels. Name exactly one — a plan with no lead has no centre of "
            f"gravity, and one with three has no priorities.")
    for r in rows["channels"]:
        ch, role = r.get("channel", "a channel"), str(r.get("role", "")).lower()
        if role not in ROLES:
            add("open", "channels", f"{ch}: '{role or 'no role'}' is not a job. Use one of: "
                                    f"{', '.join(ROLES)}")
        if not str(r.get("measure", "")).strip():
            add("open", "channels", f"{ch}: no measure. A channel without one cannot be judged, so "
                                    f"it will be judged on someone else's metric.")
        else:
            m = str(r.get("measure", "")).lower()
            # Spelled-out metrics are the norm in a plan, so match the words as well as the
            # acronyms — "cost per acquisition" slipped straight past a list containing only "cpa".
            CONVERSION_WORDS = ("conversion", "cpa", "cost per acquisition", "cost per sale",
                                "sales", "roas", "revenue", "purchase", "cpl", "leads")
            REACH_WORDS = ("reach", "impression", "awareness", "coverage", "opportunity to see",
                           "ots", "grp", "frequency")
            if role == "reach" and any(k in m for k in CONVERSION_WORDS):
                add("open", "channels",
                    f"{ch} is a reach channel measured on conversion. Measured that way it will "
                    f"always look like a failure — this is the classic misallocation.")
            if role == "conversion" and any(k in m for k in REACH_WORDS):
                add("open", "channels",
                    f"{ch} is a conversion channel measured on reach, so it will always look like a "
                    f"triumph whether or not it sells anything.")
        if str(r.get("side", "")).lower() not in SIDES:
            add("open", "channels", f"{ch}: mark it brand or activation — the split cannot be "
                                    f"computed without it")
        if not str(r.get("owner", "")).strip():
            add("open", "channels", f"{ch}: owner unknown. Left blank it reads as settled.")

    # 4. THE PROOF GATE — the cross-document check, and the reason this lives in the portal
    if house:
        by_aud = {str(r.get("audience", "")).strip(): str(r.get("pillar", "")).strip().lower()
                  for r in rows["audiences"]}
        for r in rows["channels"]:
            if str(r.get("role", "")).lower() != "proof":
                continue
            # which pillar is this channel proving? its audience's, or the functional one by default
            pillar = next((v for v in by_aud.values() if v in ("emotional", "functional")), "functional")
            sourced, total = pillar_evidence(house, pillar)
            if sourced == 0:
                add("blocking", "channels",
                    f"{r.get('channel','a channel')} is given proof work against the {pillar} "
                    f"pillar, which has {sourced} of {total} reasons-to-believe sourced. There is "
                    f"nothing to prove with. Move it to reach, or hold it until the facts exist.")
    else:
        add("open", "channels", "No messaging house attached — the proof gate cannot run, so any "
                               "channel could be assigned proof work it cannot deliver")

    # A plan takes both the brief and the house. When they point at different briefs it is usually a
    # mistake and occasionally deliberate, and the two look identical from here — so it is asked about
    # rather than resolved. Silently preferring one would be a decision made on somebody's behalf.
    if house:
        p_brief = str(p.get("brief_id") or "")
        h_brief = str(house.get("brief_id") or "")
        if p_brief and h_brief and p_brief != h_brief:
            add("blocking", "objectives",
                f"This plan is written against a different brief from its messaging house "
                f"({p.get('brief_title') or 'one brief'} vs "
                f"{house.get('brief_title') or 'another'}). One of them is answering the wrong "
                f"question — point them at the same brief, or say why they differ.")
        elif h_brief and not p_brief:
            add("open", "objectives",
                "No brief attached to this plan. It will inherit the house's, which is usually right — "
                "attach it explicitly so the objectives can be checked against something.")
    if not p.get("brief_id") and not house:
        add("open", "objectives",
            "Neither a brief nor a house. The objectives ladder has nothing above it to answer to.")

    # 5. the split, declared against actual
    bal = balance_of(p)
    declared = int(bal["brand_share"])
    act = actual_split(p)
    # A split nobody chose is worth saying out loud. Previously invisible: an untouched plan reported
    # the same 60 as a deliberate one, so this finding could never fire.
    if not bal["declared"]:
        add("open", "balance",
            f"The brand/activation split is sitting on the {DEFAULT_BRAND_SHARE}% default and nobody "
            f"has confirmed it. It is the best-evidenced starting point there is, and it is also "
            f"disputed — either way it should be a decision rather than an inheritance.")
    # Ten points is a tenth of the budget. Inclusive, because a plan that says 60 and builds 50
    # has a stated intention and an opposite behaviour, and the behaviour is what runs.
    if act["brand"] is not None and abs(act["brand"] - declared) >= 10:
        add("open", "balance",
            f"Declared {declared}/{100-declared} brand/activation, but the channels add up to "
            f"{act['brand']}/{act['activation']} ({act['basis']}). The behaviour is what will run.")
    if declared != DEFAULT_BRAND_SHARE and not bal.get("reason", "").strip():
        add("open", "balance",
            f"The split is set to {declared}% brand rather than the {DEFAULT_BRAND_SHARE}% default. "
            f"Record one sentence of reason — somebody will ask in six months.")

    # The weight column is what makes the split checkable rather than aspirational, and one thing
    # about it was checked nowhere: whether the weights add up.
    #
    # Deliberately NOT flagged here: "no channel carries a weight" and "n of m are unweighted".
    # `mediaplan.findings` already owns both, in the voice of the desk that needs them, and its own
    # docstring is right that saying a thing twice in two vocabularies is how the two start to
    # disagree. Both states also already reach this screen through the balance finding above, whose
    # basis clause now names them ("spend unknown on 2 of 4 channels"). Do not re-add them.
    #
    # A column that sums to 87 or 140 is the one nobody checked. It is not a media question — it is
    # arithmetic on rows this layer owns, and it silently renormalised into a confident percentage.
    if act.get("weighted") and act.get("sums_to_100") is False and act["weighted"] == act["n_channels"]:
        add("open", "channels",
            f"The channel weights add up to {_num(float(act['sum']))}%, not 100. Everything computed "
            f"from them — the split above, and the weight the media desk reads — is a ratio of what "
            f"was entered rather than a share of the plan. Make them total 100.")

    # 6. phases need occasions
    for r in rows["phases"]:
        if not str(r.get("occasion", "")).strip():
            add("open", "phases", f"{r.get('phase','a phase')} names no occasion. A calendar built "
                                  f"on occasions has a reason; one built on dates has a habit.")

    # 7. the measure everyone omits
    for r in rows["measures"]:
        if not str(r.get("would_tell_us_it_failed", "")).strip():
            add("open", "measures",
                f"{r.get('role','a role')}: no failure signal. Decide it before launch — nobody "
                f"agrees on it afterwards.")

    for l in LAYERS:
        if stale(p, l["id"], house):
            add("stale", l["id"], f"{l['label']} was written against a different messaging house — "
                                  f"the house has moved since")
        if not rows.get(l["id"]) and l["kind"] == "rows":
            add("empty", l["id"], f"{l['label']} is empty")
    return out


# --- approval gate (round 92) ---------------------------------------------------------------------
#
# Closes the actual race this was built to fix: a submitter kept editing while an approver was also
# looking at the same plan. Not a general lock — a plan is editable by anyone right up until it is
# explicitly submitted, and the freeze applies only to the `pending_approval` window itself. Enforced
# in `main.py`'s mutating routes (`is_locked` below), not inside `add_row`/`edit_row`/`set_balance`/
# `set_geography` themselves — those functions have no error-return channel today, and giving all four
# one now, for every existing caller, is a bigger change than this gate needs to make.
#
# The identity check is real but not session-cookie-enforced: `approve`/`reject` take the ACTING
# user's id and check it against the level's own primary/backup assignment — a wrong id is refused,
# so this is not an honesty system. It stops short of requiring a real login only because nothing in
# the live product requires signing in today (see CLAUDE.md — the session system exists and works,
# it's just never been a gate on any product route). Wiring `current_user` here instead of a passed id
# is the natural next step once sign-in is a real gate on the app itself, not a bigger redesign of
# this mechanism.
def is_locked(p: dict) -> bool:
    return p.get("status") == "pending_approval"


def submit_for_approval(p: dict, hierarchy: list[dict], submitted_by: str) -> tuple[dict | None, str]:
    """Send the plan into its brand's first approval level. Refuses if the brand has no hierarchy
    defined yet — there is nothing to route to — or if it is already pending."""
    if is_locked(p):
        return None, "Already pending approval."
    if not hierarchy:
        return None, ("This brand has no approval hierarchy defined yet — set one up in Brand setup "
                      "before a plan can be submitted.")
    first = hierarchy[0]
    p["status"] = "pending_approval"
    p["pending_approval"] = {"level": first["level"], "title": first["title"],
                             "primary_user_id": first.get("primary_user_id", ""),
                             "backup_user_id": first.get("backup_user_id", ""),
                             "submitted_by": submitted_by, "since": _now()}
    p.setdefault("approval_log", []).append({"action": "submitted", "level": first["level"],
                                             "by": submitted_by, "at": _now()})
    return save(p), ""


def _is_assigned(pa: dict, user_id: str) -> bool:
    return bool(user_id) and user_id in (pa.get("primary_user_id", ""), pa.get("backup_user_id", ""))


def approve(p: dict, hierarchy: list[dict], user_id: str, who_name: str) -> tuple[dict | None, str]:
    """Approve at the current level. Advances to the next level if the hierarchy has one, else the
    plan is fully approved. Refuses if `user_id` is not this level's primary or backup — the actual
    gate, see the module note above on what "real" means here."""
    pa = p.get("pending_approval")
    if not is_locked(p) or not pa:
        return None, "This plan is not pending approval."
    if not _is_assigned(pa, user_id):
        return None, f"{who_name or user_id} is not the assigned approver for {pa['title']}."
    p.setdefault("approval_log", []).append({"action": "approved", "level": pa["level"],
                                             "by": who_name or user_id, "user_id": user_id, "at": _now()})
    nxt = next((r for r in hierarchy if r["level"] > pa["level"]), None)
    if nxt:
        p["pending_approval"] = {"level": nxt["level"], "title": nxt["title"],
                                 "primary_user_id": nxt.get("primary_user_id", ""),
                                 "backup_user_id": nxt.get("backup_user_id", ""),
                                 "submitted_by": pa.get("submitted_by", ""), "since": _now()}
    else:
        p["status"] = "approved"
        p["pending_approval"] = None
    return save(p), ""


def reject(p: dict, user_id: str, who_name: str, reason: str) -> tuple[dict | None, str]:
    """Send it back to draft, fully editable again. Requires a reason — a rejection with no reason is
    a delay with no way to act on it."""
    pa = p.get("pending_approval")
    if not is_locked(p) or not pa:
        return None, "This plan is not pending approval."
    if not _is_assigned(pa, user_id):
        return None, f"{who_name or user_id} is not the assigned approver for {pa['title']}."
    if not str(reason or "").strip():
        return None, "Say why, so the submitter knows what to fix."
    p["status"] = "draft"
    p["pending_approval"] = None
    p.setdefault("approval_log", []).append({"action": "rejected", "level": pa["level"],
                                             "by": who_name or user_id, "user_id": user_id,
                                             "reason": reason.strip(), "at": _now()})
    return save(p), ""


def status(p: dict, house: dict | None = None) -> dict:
    findings = findings_mod.annotate(validate(p, house), p.get("overrides"))
    live = findings_mod.live_blocking(findings)
    layers = []
    for l in LAYERS:
        node = p["nodes"][l["id"]]
        ok = all(p["nodes"][par]["rows"] for par in l["parents"])
        # `rows` carries the actual rows, not a count — every table on the plan screen reads
        # `layerStatus(status, layer).rows` and maps over it. Same mistake as the house's `options`,
        # and the same consequence: an integer draws an empty table on a layer that has data.
        # `n_rows` is there for anything that only wants the count.
        # `layer` and `key` alias `id` — the plan screen resolves a layer the same way the house does,
        # so without them every table on this screen was empty too. See the note in strategy.status().
        layers.append({"id": l["id"], "layer": l["id"], "key": l["id"],
                       "label": l["label"], "name": l["label"], "kind": l["kind"],
                       # Same shape as the house's, so the plan screen cannot hit the crash the house did.
                       "asks": strategy.split_asks(l["asks"]), "asks_text": l["asks"],
                       "cols": l.get("cols", []),
                       "rows": node["rows"], "n_rows": len(node["rows"]),
                       "ready": ok, "stale": stale(p, l["id"], house),
                       "blocked_because": "" if ok else
                       f"fill {', '.join(LAYER_BY_ID[x]['label'] for x in l['parents'])} first"})
    act = actual_split(p)
    return {
        "id": p["id"], "brand": p.get("brand", ""), "house": p.get("house", ""),
        "updated": p.get("updated", ""),
        "layers": layers, "findings": findings,
        "blocking": live,
        "overridden": findings_mod.overridden_count(findings),
        **findings_mod.counts(findings, p.get("overrides")),
        "balance": {**balance_of(p), "actual": act, "default": DEFAULT_BRAND_SHARE,
                    "basis_of_default": BRAND_SHARE_BASIS},
        "geography": geography_reach(p),
        "approval": {"status": p.get("status", "draft"), "locked": is_locked(p),
                    "pending": p.get("pending_approval"), "log": p.get("approval_log") or []},
        "roles": ROLES,
        # The eleven leaves plus the not-one-medium option, for the `medium` column's select. Served
        # rather than assembled on the client, because a media list built in the frontend is exactly
        # the MEDIA_DEFS failure media.py exists to end.
        "media": media_mod.options(),
        "medium_suggestions": medium_suggestions(p),
        "house_evidence": {
            "emotional": pillar_evidence(house, "emotional"),
            "functional": pillar_evidence(house, "functional"),
        } if house else {},
        "complete": all(x["rows"] for x in layers if x["kind"] == "rows") and not live,
    }


# --- generation ---------------------------------------------------------------------------------

def _skill_text() -> str:
    parts = []
    for rel in ("SKILL.md", os.path.join("references", "balance.md")):
        f = os.path.join(_SKILL, rel)
        if os.path.exists(f):
            parts.append(open(f, encoding="utf-8").read())
    return "\n\n".join(parts)


# Per-column constraints, where a column takes a value rather than prose.
#
# Two things in a real plan came from the absence of these. The audience `pillar` column arrived holding a
# whole sentence — "functional — 'Heritage moves every single day…'" — which then tripped the one-pillar
# check and produced a blocking finding about six pillars. And every objective row came back with
# `by_when` empty, on a layer whose own question asks for a date.
#
# The fix is not a stricter parser. It is telling the generator that some cells are a value and not a
# place to explain yourself.
_COLUMN_RULES: dict[str, str] = {
    "objectives": (
        "`level` is exactly one of: business, marketing, communication — one row each, in that order.\n"
        "`measure` is the number this is judged on. The BUSINESS row must carry one; without it nothing "
        "below it can be falsified.\n"
        "`by_when` is a date or a period — 'FY27', 'end Q3', 'within 12 months'. If nobody has set one, "
        "write who has to set it rather than leaving it blank.\n"),
    "audiences": (
        "`pillar` is exactly ONE WORD: emotional or functional. Nothing else — no explanation, no "
        "quotation, no second pillar. Put your reasoning in `believes_now`, which is prose.\n"
        "`rank` is a bare integer starting at 1, each used once.\n"),
    "channels": (
        "`role` is exactly one of: reach, proof, conversion, advocacy. One word.\n"
        "`side` is exactly one of: brand, activation. One word.\n"
        "`lead` is 'yes' on exactly one row and empty on the rest.\n"
        "`medium` is one id from the served media list and nothing else. It is what lets a channel be "
        "weighted, coloured and joined to the jobs table, and it is the only column here that is a "
        "vocabulary rather than prose. `channel` stays prose: it says what is being made and where "
        "('15s vertical reel, Telugu'), which an id cannot. A row that genuinely covers several media "
        "takes the not-one-medium option rather than its largest part -- a budget line dressed as a "
        "medium cannot carry a weight.\n"
        "`share` is a whole-number percentage of TOTAL spend, and every row's share together must "
        "add up to exactly 100 — a column that sums to anything else is not used at all. "
        "Leave the whole column empty rather than filling some rows: partly weighted is "
        "worth nothing.\n"
        "`owner` is a named team or role, or who must name them.\n"),
    "measures": (
        "`role` matches a role used in Channel roles above — reach, proof, conversion or advocacy.\n"),
}


def _column_rules(layer_id: str) -> str:
    r = _COLUMN_RULES.get(layer_id, "")
    # Live-tested bug: `medium` was told to pick "one id from the served media list" in three places in
    # this file and the list itself was never actually built or sent anywhere — the model, correctly,
    # would not invent a channel/medium it had nothing real to choose from, and left both columns
    # honestly blank on every row rather than guess. `LEGACY_STRATEGY_MEDIA` is the same seven-id
    # vocabulary the house's own medium layer already uses (tv/digital/social/on-ground/ooh/trade/posm)
    # — a fixed studio vocabulary, not brand-specific, so this applies the same in Grounded and
    # Independent plans alike.
    if layer_id == "channels":
        r += ("The served media list — the only values `medium` may hold: "
              + ", ".join(media_mod.LEGACY_STRATEGY_MEDIA)
              + ". There is no 'mixed' or 'multi' option on this list — a row that genuinely spans more "
                "than one of these leaves `medium` empty and says so (e.g. 'spans tv + digital, split "
                "not yet decided') rather than picking one and hiding the rest, same as any other cell "
                "with nothing settled to put in it.\n")
    return ("THESE COLUMNS TAKE A VALUE, NOT A SENTENCE:\n" + r) if r else ""


def house_block(house: dict, layer_id: str = "") -> str:
    """The whole messaging house, as the plan's brief.

    **This used to send four lines** — the core, the two pillar texts with a count of sourced RTBs, and
    the culture codes. So the plan was generated from the brief and a summary of the house, and the
    observation that landed it was exact: the house's *Message by medium* layer already says what the
    brand says on TV, in social, at POS, on-ground and in trade, and the plan's job is mapping channels
    and media. Those two were never introduced to each other. The plan re-derived channel messaging that
    had already been decided one layer up, and the two copies were free to disagree.

    What is added: the per-medium messages verbatim, the reasons to believe as **text** rather than as a
    count, what can be demonstrated, and the avoid list as a hard constraint. Plus, for the layers where
    it changes the answer, an instruction to carry the house's wording rather than write new wording.
    """
    se, te = pillar_evidence(house, "emotional")
    sf, tf = pillar_evidence(house, "functional")
    out = ["THE MESSAGING HOUSE THIS PLAN SERVES — decided by a person, and not open for revision here.",
           f"Core: {'; '.join(strategy._chosen_text(house, 'core')) or '(none chosen)'}",
           f"Emotional pillar: {pillar_text(house, 'emotional')}  [{se} of {te} RTBs sourced]",
           f"Functional pillar: {pillar_text(house, 'functional')}  [{sf} of {tf} RTBs sourced]"]

    for lid, label in (("rtb_emotional", "Reasons to believe the emotional pillar"),
                       ("rtb_functional", "Reasons to believe the functional pillar")):
        node = (house.get("nodes") or {}).get(lid) or {}
        picked = set(node.get("chosen") or [])
        rows = [o for o in node.get("options", []) if o["id"] in picked]
        if rows:
            out.append(f"{label} — a channel may only be given proof work against one of these, and only "
                       f"where it is sourced:\n"
                       + "\n".join(f"  - {o['text']}"
                                   + ("  [sourced: " + str(o.get("source")) + "]" if _sourced(o)
                                      else "  [UNSOURCED - cannot carry proof]")
                                   for o in rows))

    demo = strategy._chosen_text(house, "proof")
    if demo:
        out.append("What can be SHOWN — prefer these for any channel whose job is proof:\n"
                   + "\n".join(f"  - {t}" for t in demo))

    cult = strategy._chosen_text(house, "culture")
    if cult:
        out.append("Culture codes and occasions the brand owns: " + "; ".join(cult))

    # The half that was missing entirely, and the reason this function exists.
    node = (house.get("nodes") or {}).get("medium") or {}
    picked = set(node.get("chosen") or [])
    by_med: dict[str, list[str]] = {}
    for o in node.get("options", []):
        if o["id"] in picked and str(o.get("text") or "").strip():
            by_med.setdefault(str(o.get("tag") or "general").lower(), []).append(o["text"].strip())
    if by_med:
        out.append("WHAT THE BRAND ALREADY SAYS IN EACH MEDIUM — decided in the house. Use these; do not "
                   "write new messaging for a medium that already has one:\n"
                   + "\n".join(f"  {m}: " + " | ".join(v) for m, v in by_med.items()))
        if layer_id == "channels":
            out.append("This layer maps channels onto those media. For every channel you name, the `job` "
                       "should be the work the medium's message above is doing — not a fresh line. Where "
                       "you propose a channel whose medium has no message in the house, say so in the "
                       "row rather than inventing one: that is a gap in the house, and naming it is more "
                       "useful than papering over it.")
        elif layer_id == "phases":
            out.append("Phases are built on the occasions above, not on quarters.")
    elif layer_id == "channels":
        out.append("The house has NO per-medium messages chosen yet, so every channel you name will need "
                   "one written later. Say that in the row rather than writing the message here — this "
                   "layer decides distribution, and a message invented here would compete with the one "
                   "the house eventually settles.")

    avoid = [o["text"] for o in ((house.get("nodes") or {}).get("culture") or {}).get("options", [])
             if o["id"] in set(((house.get("nodes") or {}).get("culture") or {}).get("chosen") or [])
             and str(o.get("tag", "")).lower() == "avoid"]
    if avoid:
        out.append("MUST NOT DO: " + "; ".join(avoid))

    out.append("A pillar with 0 sourced RTBs may NOT be given proof work. Say so instead.")
    return "\n".join(out)


def prompt_for(p: dict, layer_id: str, house: dict | None = None, extra: str = "",
               anchors: str = "", rules: str = "", locked: list[dict] | None = None) -> str:
    l = LAYER_BY_ID[layer_id]
    # General-mode plans (deliberately not tied to a brand — see BRAND_GROUNDING_MODES_PLAN.md) must
    # never reach `resolve()` — with more than one profile on file it falls back to whichever is
    # ACTIVE, exactly the silent substitution this mode exists to prevent. Same fix as
    # strategy.py's own prompt_for.
    _plan_general = p.get("brand_mode") == "general"
    brand_for_prompt = None if _plan_general else brandprofile.resolve(p, house)
    out = [_skill_text(),
           "\n\n---\nTHE BRAND\n" + brandprofile.voice_block(brand_for_prompt)]
    # Phase 2 (BRAND_GROUNDING_MODES_PLAN.md): this used to pull the bound house's real content in
    # unconditionally whenever one existed, same shape as the Phase 1 leaks already fixed in
    # producers.stands_on()/_ctx() and prompts.py's house_block/platform_block — a General plan with a
    # house bound for its OTHER layers (channels, audiences) would still stand on that house's real
    # core message, RTBs and avoid list for the layer actually being generated. `voice_block` above is
    # already correctly gated; this is the second, separate mechanism that needed the same gate.
    if house and not _plan_general:
        out.append("\n\n---\n" + house_block(house, layer_id))
    for par in l["parents"]:
        rws = p["nodes"][par]["rows"]
        if rws:
            out.append(f"\n\n---\nALREADY DECIDED · {LAYER_BY_ID[par]['label']}\n"
                       + "\n".join("  - " + json.dumps({k: v for k, v in r.items()
                                                        if k in LAYER_BY_ID[par]["cols"]},
                                                       ensure_ascii=False) for r in rws))
    if layer_id == "balance":
        b = p.get("balance", {})
        out.append(f"\n\n---\nCURRENT SPLIT: {b.get('brand_share')}% brand, basis "
                   f"{b.get('basis')}. Actual from channels: {actual_split(p)}")
    if anchors:
        out.append("\n\n---\n" + anchors)
    if rules:
        out.append("\n\n---\n" + rules)
    if locked:
        out.append("\n\n---\nLOCKED COPY — verbatim, never paraphrased:\n"
                   + "\n".join(f"  - {c['text']}" for c in locked))
    if extra.strip():
        out.append("\n\n---\nTHE USER ADDS\n" + extra.strip())
    if l["kind"] == "number":
        out.append(f"\n\n---\nNOW: {l['label']}\n{l['asks']}\n"
                   'Return ONLY JSON: {"brand_share": 60, "reason": "...", "basis": "year|window"}')
    else:
        out.append(f"\n\n---\nNOW: {l['label']}\n{l['asks']}\n"
                   f"Columns: {', '.join(l['cols'])}\n"
                   + _column_rules(layer_id) +
                   'Return ONLY JSON: {"rows":[{' +
                   ", ".join(f'"{c}":"..."' for c in l["cols"]) + '}]}\n'
                   "Leave a cell empty rather than inventing a number, an owner or a budget — but where "
                   "you leave one empty, say in that cell what has to be decided and by whom, in three "
                   "or four words. An empty cell reads as an oversight; 'finance to confirm' reads as a "
                   "task.")
    return "\n".join(out)


def generate(p: dict, layer_id: str, house: dict | None = None, extra: str = "",
             anchors: str = "", rules: str = "", locked: list[dict] | None = None,
             replace: bool = False) -> tuple[dict, str]:
    l = LAYER_BY_ID[layer_id]
    for par in l["parents"]:
        if not p["nodes"][par]["rows"]:
            return p, f"Fill {LAYER_BY_ID[par]['label']} first — this layer is written against it."
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return p, "No ANTHROPIC_API_KEY — the plan can still be filled in by hand."
    data, err = jsonout.ask_json(prompt_for(p, layer_id, house, extra, anchors, rules, locked), max_tokens=4000)
    if data is None:
        return p, f"Generation failed: {err}"
    if l["kind"] == "number":
        p = set_balance(p, int(data.get("brand_share", DEFAULT_BRAND_SHARE)),
                        str(data.get("reason", "")), str(data.get("basis", "year")), source="model")
        return p, ""
    # **Generating onto a layer that already has rows used to APPEND.** A plan came back with five phases
    # — three good ones with windows, then two thinner ones with none — because the layer had been
    # generated twice and both attempts were kept. Both then went into the Word file as one plan.
    #
    # A plan layer is a set, not a list you add to: three objectives, N audiences, the channels you bought.
    # A second full set is never the answer. So:
    #
    #   nothing there yet          -> generate
    #   only the model's own rows  -> replace them, which is plainly what "generate again" means
    #   anything a person wrote    -> refuse, and name the control that would overwrite it
    #
    # The last case is the one worth protecting. Replacing the model's previous guess is free; replacing
    # somebody's typing without asking is the kind of loss that is discovered days later.
    existing = p["nodes"][layer_id]["rows"]
    if existing and not replace:
        mine = [r for r in existing if str(r.get("source", "")).lower() != "model"]
        if mine:
            return p, (f"{LAYER_BY_ID[layer_id]['label']} already has "
                       f"{len(mine)} row{'s' if len(mine) != 1 else ''} you wrote or edited, so nothing "
                       f"was generated — a second set would sit underneath the first and both would go "
                       f"into the document. Use 'Replace these rows' to overwrite, or add rows by hand.")
        p["nodes"][layer_id]["rows"] = []
    elif replace:
        p["nodes"][layer_id]["rows"] = []

    made = 0
    for r in (data.get("rows") or []):
        if isinstance(r, dict) and any(str(v).strip() for v in r.values()):
            p = add_row(p, layer_id, r, source="model")
            made += 1
    if not made:
        return p, "Nothing usable came back. Try again, or write the rows by hand."
    return mark_written(p, layer_id, house), ""
