"""made.py — the record of everything the studio has generated.

The gap this closes: today, what a person or the model has actually produced is only visible for as
long as the browser tab that made it stays open. Every generation route in this app (POSM renders,
Onground elements, storyboard frames, cast-reference candidates, produced films) writes a real file to
`/media/`/`/renders/` and hands back a bare URL — the bytes are safe, but nothing indexes them. One flat,
per-tenant ledger, written to at the moment something is generated, is the fix — same shape as
`actuals.py` (append-only, atomic writes, no owner-scoping baked into storage), because this is the same
kind of problem: a fact that many screens need to read, not a document that belongs to one of them.

**One row per candidate, not one row per generation call.** Several routes return more than one option
per click (`/cast-reference` can return up to 4, `/posm-scamps` a full layout set). A single row holding
several URLs, with one `approved` flag on the row, would retire every unpicked candidate the moment one
is approved — losing the record of what was actually offered and rejected. A row per candidate costs
nothing at this app's scale and keeps that history intact.

**Approval is a state change, not a copy.** `approve()` marks a row `approved:true` and records which
library item it became — it never deletes the row (an audit trail this app has never had before is worth
keeping quietly), but `list_entries()` excludes approved rows by default, so a promoted item is never
shown as pending *and* live in the library at once. One home at a time, same as the user asked for.

**No locking.** This ledger will be written far more often than `actuals.py` (every generation click,
not an occasional manual entry) — the same-second append-index tiebreak in `list_entries()` is copied
from there deliberately, not optionally, because that collision is more likely here, not less. Still no
lock file or revision check, matching the rest of this app's stores (a known, documented, systemic gap —
see the round-83 audit). Accepted here specifically because the failure mode is low-stakes: a lost race
loses a *ledger row*, not the generated asset itself, which is already written to `/media/`/`/renders/`
independently of this module before `record()` is ever called.
"""
from __future__ import annotations

import json
import os
import time
import uuid

import tenancy


def _dir() -> str:
    """Resolved per call, not cached at import — the pattern `library._dir()` uses, not `actuals.DIR`'s
    module-level constant. Harmless either way while `STUDIO_TENANT` is fixed for a process's lifetime,
    but there is no reason to copy the older module's shortcut into a new one."""
    return tenancy.dir("made")


def _path() -> str:
    return os.path.join(_dir(), "ledger.json")


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _load() -> list[dict]:
    try:
        with open(_path(), encoding="utf-8") as fh:
            rows = json.load(fh)
        return rows if isinstance(rows, list) else []
    except (OSError, ValueError):
        return []


def _save(rows: list[dict]) -> None:
    d = _dir()
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, "ledger.json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path())


def record(kind: str, title: str, *, url: str = "", ref_kind: str = "", ref_id: str = "",
           brand: str = "", project: str = "", made_by: str = "", route: str = "",
           note: str = "") -> dict:
    """Record one thing the studio produced. Returns the row.

    `kind` and `title` are the only things a caller must supply — everything else this app already
    knows how to leave blank honestly (see `strategy.py`'s "unattributed is a true answer" precedent for
    `made_by`) rather than guess. `ref_kind`/`ref_id` is a generic pointer (`"execution"`/`<id>`,
    `"brief"`/`<id>`) rather than a dedicated field per possible parent — most generation routes in this
    app don't operate against any single parent document at all, so a field that's usually empty isn't
    worth naming specially.
    """
    kind = str(kind or "").strip()
    title = str(title or "").strip()
    if not kind or not title:
        raise ValueError("made.record() needs both a kind and a title — 'what' and 'what to call it'.")
    row = {
        "id": uuid.uuid4().hex[:12], "kind": kind, "title": title, "url": url,
        "ref_kind": ref_kind, "ref_id": ref_id, "brand": brand, "project": project,
        "made_by": made_by or "Unattributed", "route": route, "note": note,
        "made_at": _now(),
        "approved": False, "approved_at": "", "approved_by": "", "approved_into": "",
    }
    rows = _load()
    rows.append(row)
    _save(rows)
    return row


def approve(made_id: str, library_item_id: str, who: str = "") -> dict | None:
    """Mark a row as promoted into the library. Never deletes it — see the module docstring."""
    rows = _load()
    for r in rows:
        if r.get("id") == made_id:
            r["approved"], r["approved_into"] = True, library_item_id
            r["approved_by"], r["approved_at"] = who or "Unattributed", _now()
            _save(rows)
            return r
    return None


def remove(made_id: str) -> bool:
    rows = _load()
    keep = [r for r in rows if r.get("id") != made_id]
    if len(keep) == len(rows):
        return False
    _save(keep)
    return True


def list_entries(kind: str = "", include_approved: bool = False) -> list[dict]:
    """Most recent first. Same-second tiebreak copied from `actuals.py` — see that module's own comment
    on why a plain `sort(reverse=True)` silently inverts same-second ordering."""
    rows = list(enumerate(_load()))
    if kind:
        rows = [(i, r) for i, r in rows if r.get("kind") == kind]
    if not include_approved:
        rows = [(i, r) for i, r in rows if not r.get("approved")]
    rows.sort(key=lambda pair: (pair[1].get("made_at", ""), pair[0]), reverse=True)
    return [r for _, r in rows]


def kinds() -> list[str]:
    """Every distinct kind anyone has recorded, for a filter chip list — not a fixed vocabulary, same
    reasoning as `actuals.metrics()`: this ledger doesn't know in advance every kind of thing a producer
    will ever generate."""
    return sorted({r.get("kind", "") for r in _load() if r.get("kind")})
