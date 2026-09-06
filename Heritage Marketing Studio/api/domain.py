"""domain.py — roles + the flexible multi-level approval engine.

Single source of truth for the workflow. Operates on objects that expose:
status, creator_id, kind, required_levels (list[int]), current_level (int|None),
approvals (list[dict]), history (list[dict]). Pure, deterministic, no I/O.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class Role(str, Enum):
    creator = "Creator"
    approver_l1 = "ApproverL1"
    approver_l2 = "ApproverL2"
    approver_l3 = "ApproverL3"


ROLE_AUTHORITY: dict[str, int] = {
    "Creator": 0, "ApproverL1": 1, "ApproverL2": 2, "ApproverL3": 3,
}


class Status(str, Enum):
    draft = "Draft"
    pending = "Pending"      # in the approval chain at current_level (prototype vocabulary)
    approved = "Approved"
    live = "Live"
    changes = "Changes"      # changes requested — editable, like Draft, but visually distinct


HIGH_VALUE_BUDGET = 1_000_000
MID_VALUE_BUDGET = 250_000


def required_levels(kind: str, attrs: dict[str, Any]) -> list[int]:
    """Flexible chain length — the one place this is decided."""
    override = attrs.get("required_levels")
    if override:
        return sorted({int(x) for x in override if 1 <= int(x) <= 3})
    objective = attrs.get("campaign_objective")
    budget = int(attrs.get("budget_value", 0) or 0)
    if kind == "Brief":
        if objective in {"Product launch", "Festive / seasonal"} or budget >= HIGH_VALUE_BUDGET:
            return [1, 2, 3]
        if objective in {"Brand awareness", "Performance / DR"} or budget >= MID_VALUE_BUDGET:
            return [1, 2]
        return [1]
    parent = attrs.get("brief_required_levels")
    return sorted({int(x) for x in parent}) if parent else [1, 2]


def _audit(item, event: str, actor: str, **extra) -> None:
    h = list(item.history or [])
    h.append({"event": event, "actor": actor, **extra})
    item.history = h


EDITABLE = {Status.draft.value, Status.changes.value}


def submit(item, actor_id: str):
    if item.status not in EDITABLE:
        raise ValueError(f"Can only submit from Draft/Changes (was {item.status}).")
    if actor_id != item.creator_id:
        raise ValueError("Only the creator can submit the item for review.")
    levels = item.required_levels or []
    if not levels:
        raise ValueError("Item has no required approval levels configured.")
    item.status = Status.pending.value
    item.current_level = levels[0]
    item.approvals = []
    _audit(item, "submit", actor_id, to_level=levels[0])
    return item


def approve(item, approver_id: str, approver_role: str):
    if item.status != Status.pending.value:
        raise ValueError(f"Can only approve while Pending (was {item.status}).")
    if approver_id == item.creator_id:
        raise ValueError("Creator cannot approve their own item (separation of duties).")
    level = item.current_level
    if ROLE_AUTHORITY.get(approver_role, 0) < level:
        raise ValueError(f"{approver_role} lacks authority to approve level {level}.")
    approvals = list(item.approvals or [])
    approvals.append({"level": level, "approver_id": approver_id, "role": approver_role})
    item.approvals = approvals
    _audit(item, "approve", approver_id, level=level, role=approver_role)
    levels = item.required_levels
    idx = levels.index(level)
    if idx + 1 < len(levels):
        item.current_level = levels[idx + 1]
    else:
        item.status = Status.approved.value
        item.current_level = None
        _audit(item, "fully_approved", approver_id)
    return item


def request_changes(item, approver_id: str, note: str = ""):
    if item.status != Status.pending.value:
        raise ValueError(f"Can only request changes while Pending (was {item.status}).")
    item.status = Status.changes.value      # prototype's 'Changes' pill
    item.current_level = None
    item.approvals = []
    _audit(item, "request_changes", approver_id, note=note)
    return item


def publish(item, actor_id: str):
    if item.kind != "Deliverable":
        raise ValueError("Only deliverables can go Live.")
    if item.status != Status.approved.value:
        raise ValueError("Publish gate: item must be Approved before Live.")
    item.status = Status.live.value
    _audit(item, "publish", actor_id)
    return item


def can_generate(brief) -> bool:
    return getattr(brief, "status", None) == Status.approved.value
