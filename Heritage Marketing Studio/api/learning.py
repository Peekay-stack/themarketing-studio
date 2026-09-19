"""learning.py — the learning log: what the studio has been told, and what it does with it.

**No model is being trained here.** Claude, Veo, Imagen and Lyria are frozen; nothing this file
writes changes a weight. Saying otherwise would be the most expensive kind of wrong, because someone
would stop checking the output.

What actually makes the work better is narrower and it does work:

  T1  RETRIEVAL      Approved scripts and films are kept, and the closest few are put in front of
                     the model when it writes the next one. Every anchor used is named on the
                     output, so an odd result can be traced to what informed it. Always on.
  T2  PROMPT LIBRARY Templates carry their own record. One that keeps earning approval is promoted;
                     one that keeps earning rejections is demoted or flagged for a human. A scored
                     library — never a prompt that silently edits itself.
  T3  CORRECTIONS    Every rejection carries a reason, and the reasons become house rules that ride
                     along with the next brief. This is where "the boy sounded like an adult" turns
                     into something the system will not do again.

What learning may never touch (these are enforced, not aspirational):

  * the reference library and locked copy — those change only by human upload and sign-off
  * a hard gate or a human approval — no score buys a bypass
  * anything irreversible — every entry is versioned, visible, and can be rolled back

Metrics here are computed from the log or reported as unknown. An invented dashboard number in a
governance tool is worse than no number, because it is indistinguishable from a real one.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import time
import uuid

import tenancy

# SECURITY / DATA INTEGRITY — found in the save/location audit: this module hardcoded its own directory
# next to the file instead of asking `tenancy`, same gap `library.py` had before its round-90 fix. Every
# tenant on a deployment shared one corrections log, one set of promoted templates, one approve/reject
# history. `_LEGACY_DIR` is kept only so `_migrate_legacy()` can find and move real data that predates
# this fix — nothing reads or writes through it directly once that has run.
_LEGACY_DIR = os.path.join(os.path.dirname(__file__), "learning")
_migrated = False


def _dir() -> str:
    """The active tenant's learning directory, migrating the old shared one into it on first use."""
    global _migrated
    path = tenancy.dir("learning")
    if not _migrated:
        _migrate_legacy(path)
        _migrated = True
    return path


def _migrate_legacy(dest: str) -> None:
    """Move whatever the pre-tenancy shared directory still holds into the active tenant's own.

    One top-level file at a time, never overwriting something already at the destination — same
    non-destructive, idempotent rule `library._migrate_legacy()`/`tenancy.migrate()` use for every
    other retrofitted store, so a second call (a second tenant, a restart) finds nothing left to move.
    """
    if not os.path.isdir(_LEGACY_DIR) or os.path.abspath(_LEGACY_DIR) == os.path.abspath(dest):
        return
    for name in os.listdir(_LEGACY_DIR):
        src = os.path.join(_LEGACY_DIR, name)
        target = os.path.join(dest, name)
        if os.path.exists(target):
            continue
        shutil.move(src, target)
    try:
        if not os.listdir(_LEGACY_DIR):
            os.rmdir(_LEGACY_DIR)
    except OSError:
        pass


def _decisions() -> str:
    return os.path.join(_dir(), "decisions.jsonl")


def _templates_path() -> str:
    return os.path.join(_dir(), "templates.json")


def _examples() -> str:
    return os.path.join(_dir(), "examples.jsonl")

# Promotion needs enough evidence to mean something; three approvals is a mood, not a pattern.
MIN_USES = 6
PROMOTE_AT = 0.70
DEMOTE_AT = 0.35

GUARDRAILS = [
    "The reference library and locked copy. Those change only by human upload and sign-off.",
    "A hard gate or a human approval. No score and no approval rate buys a bypass.",
    "Another brand's work. What is learned here stays scoped to this brand.",
    "Anything irreversible. Every entry is versioned and can be rolled back on its own.",
]


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _append(path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read(path: str) -> list[dict]:
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue           # one bad line must not lose the rest of the log
    except OSError:
        pass
    return out


# --- decisions ---------------------------------------------------------------------------------

def record(kind: str, decision: str, *, subject: str = "", reason: str = "",
           template: str = "", who: str = "", meta: dict | None = None, brand: str = "") -> dict:
    """Log one human decision. `reason` is the valuable part — a bare reject teaches nothing.

    `brand` — same SECURITY / DATA INTEGRITY gap as `library.py` had: this store was tenant-scoped
    (round-90 fix) but never brand-scoped within a tenant, despite `GUARDRAILS` above literally
    claiming "what is learned here stays scoped to this brand." It didn't — a Heritage rejection
    ("the boy sounded like an adult") would surface as a house rule on a Parle G generation. Left
    blank for a genuinely brand-agnostic decision; every read below only filters by it when a caller
    passes one, so this is additive.
    """
    row = {"id": uuid.uuid4().hex[:8], "at": _now(), "kind": kind,
           "decision": (decision or "").lower(), "subject": subject[:300],
           "reason": (reason or "").strip()[:600], "template": template, "who": who,
           "meta": meta or {}, "brand": brand}
    _append(_decisions(), row)
    if template:
        _score(template, row["decision"])
    return row


def decisions(limit: int = 60, kind: str = "", brand: str = "") -> list[dict]:
    rows = _read(_decisions())
    if kind:
        rows = [r for r in rows if r.get("kind") == kind]
    if brand:
        rows = [r for r in rows if not r.get("brand") or r.get("brand") == brand]
    return list(reversed(rows))[:limit]


# --- approved work, kept as anchors -------------------------------------------------------------

def keep_example(kind: str, *, title: str, body: str, brief: str = "", meta: dict | None = None,
                 brand: str = "") -> dict:
    """Keep an approved piece of work so later generations can be anchored on it. `brand` — see
    `record()`'s note; the same scoping gap applied to T1 retrieval."""
    row = {"id": uuid.uuid4().hex[:8], "at": _now(), "kind": kind, "title": title[:200],
           "brief": (brief or "")[:2000], "body": (body or "")[:8000], "meta": meta or {}, "brand": brand}
    _append(_examples(), row)
    return row


def _words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", (s or "").lower())}


def anchors(kind: str, brief: str = "", n: int = 3, brand: str = "") -> list[dict]:
    """The most relevant approved examples of this kind.

    Overlap on meaningful words, which is crude but honest and needs no embedding service. Recency
    breaks ties, so the house style can move without old work outvoting it forever.

    `brand` restricts retrieval to that brand's own approved work (plus brand-agnostic examples) —
    without it, a brand-new brand's very first generation could be anchored on another brand's
    approved script, and the output would read as finished, competent, and wrong.
    """
    rows = [r for r in _read(_examples()) if r.get("kind") == kind
            and (not brand or not r.get("brand") or r.get("brand") == brand)]
    if not rows:
        return []
    want = _words(brief)
    if not want:
        return list(reversed(rows))[:n]
    scored = []
    for i, r in enumerate(rows):
        overlap = len(want & _words(r.get("brief", "") + " " + r.get("title", "")))
        scored.append((overlap, i, r))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [r for _o, _i, r in scored[:n]]


def anchor_block(kind: str, brief: str = "", n: int = 3, brand: str = "") -> tuple[str, list[str]]:
    """Approved examples formatted for a prompt, plus their titles so the output can name them."""
    picks = anchors(kind, brief, n, brand=brand)
    if not picks:
        return "", []
    parts = ["Work already approved for this brand. Match its judgement — its length, its restraint, "
             "what it leaves unsaid — without copying its words:"]
    for p in picks:
        parts.append(f"\n--- {p.get('title', 'approved')} ---\n{p.get('body', '')[:1500]}")
    return "\n".join(parts), [p.get("title", "approved") for p in picks]


# --- house rules, learned from rejections --------------------------------------------------------

def house_rules(limit: int = 12, brand: str = "") -> list[str]:
    """Reasons given when work was rejected, newest first, deduplicated. `brand` — see `record()`'s
    note; without it a correction logged against one brand was silently binding on every other."""
    seen, out = set(), []
    for r in reversed(_read(_decisions())):
        if r.get("decision") != "reject":
            continue
        if brand and r.get("brand") and r.get("brand") != brand:
            continue
        reason = (r.get("reason") or "").strip()
        key = re.sub(r"[^a-z]", "", reason.lower())[:60]
        if reason and key not in seen:
            seen.add(key)
            out.append(reason)
        if len(out) >= limit:
            break
    return out


def rules_block(brand: str = "") -> str:
    """House rules as a prompt fragment. Empty until someone has actually said something."""
    rules = house_rules(brand=brand)
    if not rules:
        return ""
    lines = "\n".join(f"- {r}" for r in rules)
    return ("Corrections this brand's team has given before. They are not preferences; treat each "
            f"as a rule:\n{lines}")


# --- the prompt library --------------------------------------------------------------------------

def _templates() -> dict:
    try:
        with open(_templates_path(), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_templates(data: dict) -> None:
    path = _templates_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def register(template_id: str, desc: str = "", kind: str = "") -> dict:
    data = _templates()
    row = data.setdefault(template_id, {"id": template_id, "desc": desc, "kind": kind,
                                        "uses": 0, "approvals": 0, "rejections": 0,
                                        "state": "Active", "since": _now()})
    if desc:
        row["desc"] = desc
    if kind:
        row["kind"] = kind
    _write_templates(data)
    return row


def used(template_id: str, desc: str = "", kind: str = "") -> None:
    data = _templates()
    row = data.get(template_id) or register(template_id, desc, kind)
    data = _templates()
    row = data[template_id]
    row["uses"] = int(row.get("uses", 0)) + 1
    _write_templates(data)


def _score(template_id: str, decision: str) -> None:
    data = _templates()
    if template_id not in data:
        register(template_id)
        data = _templates()
    row = data[template_id]
    if decision == "approve":
        row["approvals"] = int(row.get("approvals", 0)) + 1
    elif decision == "reject":
        row["rejections"] = int(row.get("rejections", 0)) + 1
    judged = row["approvals"] + row["rejections"]
    rate = (row["approvals"] / judged) if judged else 0.0
    # Movement is recorded with its reason, so a demotion can be argued with.
    if judged >= MIN_USES and rate >= PROMOTE_AT:
        state = "Promoted"
    elif judged >= MIN_USES and rate <= DEMOTE_AT:
        state = "Demoted"
    elif row["rejections"] >= 2 and judged < MIN_USES:
        state = "Flagged"
    else:
        state = "Active"
    if state != row.get("state"):
        row.setdefault("history", []).append(
            {"at": _now(), "from": row.get("state"), "to": state,
             "why": f"{row['approvals']} approved / {row['rejections']} rejected"})
    row["state"] = state
    _write_templates(data)


def templates() -> list[dict]:
    out = []
    for row in _templates().values():
        judged = row.get("approvals", 0) + row.get("rejections", 0)
        out.append({**row,
                    "judged": judged,
                    # None, not 0 — "never judged" and "always rejected" are different facts.
                    "rate": round(row["approvals"] / judged, 2) if judged else None})
    return sorted(out, key=lambda r: (-(r["rate"] or 0), -r.get("uses", 0)))


# --- the log's own honest summary ------------------------------------------------------------

def status() -> dict:
    decs = _read(_decisions())
    exs = _read(_examples())
    tpl = templates()
    judged = [t for t in tpl if t["judged"]]
    approvals = sum(1 for d in decs if d.get("decision") == "approve")
    rejections = sum(1 for d in decs if d.get("decision") == "reject")
    with_reason = sum(1 for d in decs if d.get("decision") == "reject" and d.get("reason"))
    return {
        "tiers": [
            {"num": "T1", "name": "Retrieval", "autonomy": "Always on",
             "desc": "Approved work is kept and the closest few anchor the next generation. Every "
                     "anchor is named on the output that used it.",
             "stats": [{"val": str(len(exs)), "label": "approved examples kept"},
                       {"val": "3", "label": "anchors per generation"}]},
            {"num": "T2", "name": "Prompt library", "autonomy": "Semi-autonomous",
             "desc": "Templates are scored by what they earn. Promotion and demotion are logged "
                     "with the counts behind them, and every move is reversible.",
             "stats": [{"val": str(len(tpl)), "label": "templates"},
                       {"val": str(sum(1 for t in tpl if t["state"] == "Promoted")), "label": "promoted"},
                       {"val": str(sum(1 for t in tpl if t["state"] in ("Flagged", "Demoted"))),
                        "label": "flagged or demoted"}]},
            {"num": "T3", "name": "Corrections", "autonomy": "Semi-autonomous",
             "desc": "Every rejection carries a reason, and those reasons ride along with the next "
                     "brief as house rules.",
             "stats": [{"val": str(len(house_rules(99))), "label": "rules in force"},
                       {"val": f"{with_reason}/{rejections}" if rejections else "0",
                        "label": "rejections with a reason"}]},
        ],
        "guardrails": GUARDRAILS,
        "decisions": len(decs),
        "approvals": approvals,
        "rejections": rejections,
        # Stated as a fraction, never a percentage with no denominator behind it.
        "approval_rate": round(approvals / (approvals + rejections), 2) if (approvals + rejections) else None,
        "examples": len(exs),
        "templates": len(tpl),
        "judged_templates": len(judged),
        "rules": house_rules(),
        "empty": not decs and not exs and not tpl,
    }
