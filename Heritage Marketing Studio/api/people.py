"""people.py — the user directory and org chart (round 92).

Thin on purpose: `User` (models.py) already holds everything this needs. This module is where the
approval-hierarchy feature reads/writes that table, kept separate from `main.py`'s routes the same way
every other domain module is, and separate from `auth.py` (password/session mechanics only).

A person is never deleted, only deactivated (`active=False`) — an offboarded approver's past approvals
must stay attributed to a real name. Reassigning a brand's `approval_hierarchy` level away from them is
a separate, explicit act (`brandprofile.py`), not implied by deactivation.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import User


def list_users(db: Session, include_inactive: bool = True) -> list[User]:
    q = select(User)
    if not include_inactive:
        q = q.where(User.active.is_(True))
    return list(db.scalars(q.order_by(User.name)))


def get(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id) if user_id else None


def snapshot(u: User) -> dict:
    return {"id": u.id, "name": u.name, "role": u.role, "email": u.email, "phone": u.phone,
            "manager_id": u.manager_id, "active": bool(u.active)}


def org_chart(db: Session) -> list[dict]:
    """Every active user, with their manager's name resolved — the org-chart *view*. Not used for
    approval gating (see `brandprofile.approval_hierarchy`'s own note on why gating needs an explicit
    allow-list, not an inferred graph)."""
    users = list_users(db)
    by_id = {u.id: u for u in users}
    return [{**snapshot(u), "manager_name": (by_id.get(u.manager_id).name if u.manager_id in by_id else "")}
            for u in users]


def set_contact(db: Session, user_id: str, email: str = "", phone: str = "",
                manager_id: str | None = None) -> User | None:
    u = db.get(User, user_id)
    if not u:
        return None
    if email:
        u.email = email
    if phone:
        u.phone = phone
    if manager_id is not None:
        u.manager_id = manager_id or None
    db.commit()
    return u


def set_active(db: Session, user_id: str, active: bool) -> User | None:
    """Offboard or restore a person. Never a delete — see the module's own docstring."""
    u = db.get(User, user_id)
    if not u:
        return None
    u.active = active
    db.commit()
    return u
