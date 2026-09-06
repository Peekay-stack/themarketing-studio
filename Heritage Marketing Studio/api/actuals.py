"""actuals.py — the measurement ledger. Audit #9.

One flat, per-tenant store for facts measured after the fact rather than planned in advance: a market
share from a retail audit, a real cost-per-action from a live campaign, a delivered reach. Agreed shape
(`ASK_DESIGN_46_REPLY.md`, confirmed `ASK_DESIGN_47.md`): manual entry with a required source, one
ledger per tenant rather than one per plan or campaign, report-only.

**Flat per tenant, not scoped to a plan.** A fact like "CTR in Delhi, July" can feed more than one plan
or campaign that touches that geography and period. Scoping storage to a single plan would force the
same number to be re-entered for every plan that overlaps it — this studio's own named failure mode,
"two homes for one decision", applied to data instead of logic. A plan or campaign matches against this
ledger at READ time, by geography and period — see `match()` — never by ownership.

**Report-only, same as everywhere else in this studio.** Nothing here changes what a gate ALLOWS. Every
gate and derivation already follows "offered, sourced, never applied silently" — the PR message
suggestions, the derivable brand fields, the ladder drafts, none of them act without a person choosing
to. An entered actual automatically moving a budget split would be the first place a number changes a
real decision unsupervised, and that is a separate, later, and much more carefully considered build.

**Source is free text, same convention `som`/`benchmark` already used.** It is provenance a person
types — "Nielsen retail audit, July" — not a verified identity claim, so this does not need #6's
authentication underneath it any more than the two fields it is replacing did. If #6 lands first, the
source field can start recording a verified actor automatically; that is a strict improvement on top of
this, not a precondition for it.

**What this file does NOT yet do.** `mediaplan.esov()`'s share-of-market and `socialplan`'s cost
benchmark still read their own one-off fields — migrating those two live, already-verified consumers
onto this ledger is the next deliberate step (`ASK_DESIGN_46_REPLY.md` #3: migrate, not remove, so
`esov()` and the feasibility check are never left with nothing to read), not part of standing the
ledger up. Nothing importing this module today changes behaviour anywhere on screen.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid

import geo
import tenancy

DIR = tenancy.dir("actuals")

# Same shape as `mediaplan._PERIOD`: a year, a year-quarter or a year-month. Enforced rather than free
# text, because "Q2" and "2026-Q2" would be two different periods for the same three months and a match
# against either one would silently miss the other.
_PERIOD = re.compile(r"^(20\d{2})(-(Q[1-4]|(0[1-9]|1[0-2])))?$")

NATIONAL = "national"


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _path() -> str:
    return os.path.join(DIR, "ledger.json")


def _load() -> dict:
    """The tenant's ledger, or a fresh empty one. Never None — "no ledger yet" and "an empty ledger"
    are one state to every caller, same reason `mediaplan.ci_load` is never None."""
    try:
        with open(_path(), encoding="utf-8") as fh:
            doc = json.load(fh)
        if isinstance(doc, dict):
            doc.setdefault("entries", [])
            return doc
    except (OSError, ValueError):
        pass
    return {"tenant": tenancy.tenant(), "created": _now(), "updated": _now(), "entries": []}


def _save(doc: dict) -> dict:
    os.makedirs(DIR, exist_ok=True)
    doc["updated"] = _now()
    path = _path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return doc


def _geography(raw: str) -> str:
    """A state resolves to its code so 'Maharashtra' and 'MH' land on the same row; anything else
    (a city, 'national', a free-text market) passes through lower-cased and stripped, unjudged — this
    ledger does not gate on knowing every place a fact might be measured at."""
    raw = str(raw or "").strip()
    if not raw:
        return NATIONAL
    state = geo.resolve_state(raw)
    return state or raw.lower()


def add(*, metric: str, value, geography: str = "", period: str, source: str,
        date: str = "", note: str = "") -> tuple[dict | None, str]:
    """Record one measured fact. Returns (entry, error).

    There is deliberately no default for any field a reader would need to trust the number: a metric
    names what was measured, a period says when, a geography says where (`national` when the fact
    genuinely isn't geography-specific — not a blank, which would read as an omission rather than a
    claim), and a source is required outright. An unsourced figure is exactly the case `set_som` and
    `set_benchmark` already refuse, generalised.
    """
    metric = str(metric or "").strip().lower().replace(" ", "_")
    if not metric:
        return None, "Name the metric — what was measured."
    try:
        v = float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None, f"Value {value!r} is not a number."
    period = str(period or "").strip().upper()
    if not _PERIOD.match(period):
        return None, ("Period must be a year, a year-quarter or a year-month — 2026, 2026-Q2 or "
                      "2026-07. 'Q2' alone is not a period: it does not say which year.")
    source = str(source or "").strip()
    if not source:
        return None, ("Name where this figure came from — a retail audit, a platform's own delivery "
                      "report, a client's ledger. An unsourced actual cannot be checked, and every "
                      "consumer of this ledger trusts the number only as far as this line.")
    entry = {
        "id": uuid.uuid4().hex[:12], "metric": metric, "value": v,
        "geography": _geography(geography), "period": period, "source": source,
        "date": str(date or "").strip()[:10], "note": str(note or "").strip(), "at": _now(),
    }
    doc = _load()
    doc["entries"].append(entry)
    _save(doc)
    return entry, ""


def remove(entry_id: str) -> tuple[dict | None, str]:
    doc = _load()
    entries = doc.get("entries") or []
    if not any(e.get("id") == entry_id for e in entries):
        return None, "No entry with that id."
    doc["entries"] = [e for e in entries if e.get("id") != entry_id]
    _save(doc)
    return doc, ""


def list_entries(metric: str = "", geography: str = "", period: str = "") -> list[dict]:
    """Every entry matching the given filters (any left blank matches everything), most recent first.

    `at` only has one-second resolution, so two entries added in the same second tie on it — which a
    plain `sort(reverse=True)` would resolve by leaving them in their original (oldest-first, append)
    order, silently making the OLDER of the two look most-recent. The append index is the real
    tiebreaker: whichever of two same-second entries was appended later genuinely is the later one.
    """
    doc = _load()
    rows = list(enumerate(doc.get("entries") or []))
    if metric:
        m = str(metric).strip().lower().replace(" ", "_")
        rows = [(i, r) for i, r in rows if r.get("metric") == m]
    if geography:
        g = _geography(geography)
        rows = [(i, r) for i, r in rows if r.get("geography") == g]
    if period:
        rows = [(i, r) for i, r in rows if r.get("period") == str(period).strip().upper()]
    rows.sort(key=lambda pair: (pair[1].get("at", ""), pair[0]), reverse=True)
    return [r for _, r in rows]


def match(metric: str, geography: str = "", period: str = "") -> dict | None:
    """The one entry a plan or campaign screen should read for `(metric, geography, period)`.

    Exact match only, most recent if more than one was entered for the same three keys — a correction
    entered later is presumed to supersede rather than average with the one it corrects. Deliberately
    NOT falling back from a state to `national`, or from one period to an adjacent one: a consumer that
    needs that ladder (and `mediaplan.esov()`, which has no geography dimension at all today, may not)
    should decide and state its own fallback rather than have one silently built in here — see the
    module docstring on what migrating `esov()`/the social benchmark still has to decide.
    """
    rows = list_entries(metric=metric, geography=geography, period=period)
    return rows[0] if rows else None


def metrics() -> list[str]:
    """Every distinct metric name anyone has entered, for a picker — not a fixed vocabulary. This
    ledger is a general store for facts with no existing field of their own; it does not know in
    advance what will be measured."""
    doc = _load()
    return sorted({r.get("metric", "") for r in doc.get("entries") or [] if r.get("metric")})
