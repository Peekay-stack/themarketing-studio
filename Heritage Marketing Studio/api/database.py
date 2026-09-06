"""database.py — engine, session, init, and dev seed data."""
from __future__ import annotations

import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import auth
import domain
from models import Base, Brief, User

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./heritage.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SEED_USERS = [
    ("puneet", "Puneet (Creator)", "Creator"),
    ("ravi", "Ravi K. (L1 — Team Lead)", "ApproverL1"),
    ("meera", "Meera S. (L2 — Marketing Manager)", "ApproverL2"),
    ("ananya", "Ananya R. (L3 — Head/CMO)", "ApproverL3"),
]
# Round 92 — email/phone (for the notification phase, not built yet) and `manager_id` (the org-chart
# view, not what gates approval — see `models.User`'s own note). A real deployment enters its own; this
# is dev-seed data exactly like `SEED_PASSWORDS` below, same "fine for a local box, never real" caveat.
SEED_CONTACT = {
    "puneet": {"email": "puneet@example.com", "phone": "+91 90000 00001", "manager_id": "ravi"},
    "ravi": {"email": "ravi@example.com", "phone": "+91 90000 00002", "manager_id": "meera"},
    "meera": {"email": "meera@example.com", "phone": "+91 90000 00003", "manager_id": "ananya"},
    "ananya": {"email": "ananya@example.com", "phone": "+91 90000 00004", "manager_id": None},
}


def _add_missing_columns() -> None:
    """`create_all` only creates tables that don't exist yet -- it never alters an existing one, and
    `users` already existed (from before round 46) without `tenant`/`password_hash`. SQLite's ADD
    COLUMN is the honest fix; a migration framework for two columns on one table would be its own
    kind of overbuilt."""
    if not DB_URL.startswith("sqlite"):
        return
    with engine.connect() as conn:
        have = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)")}
        if "tenant" not in have:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN tenant VARCHAR DEFAULT 'default'")
        if "password_hash" not in have:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN password_hash VARCHAR DEFAULT ''")
        if "email" not in have:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN email VARCHAR DEFAULT ''")
        if "phone" not in have:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN phone VARCHAR DEFAULT ''")
        if "manager_id" not in have:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN manager_id VARCHAR")
        if "active" not in have:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN active BOOLEAN DEFAULT 1")
        conn.commit()


# Dev-only seed passwords -- these seeded accounts exist to make /login testable end to end without
# a registration flow, which nobody asked for. Same convention as any other placeholder credential:
# fine for a local dev box, never meant to reach anything real. Override with real accounts before
# this touches production.
SEED_PASSWORDS = {"puneet": "puneet-dev", "ravi": "ravi-dev", "meera": "meera-dev",
                   "ananya": "ananya-dev"}


def init_db() -> None:
    Base.metadata.create_all(engine)
    _add_missing_columns()
    with SessionLocal() as db:
        if not db.scalar(select(User).limit(1)):
            for uid, name, role in SEED_USERS:
                c = SEED_CONTACT.get(uid, {})
                db.add(User(id=uid, name=name, role=role, tenant="default",
                            password_hash=auth.hash_password(SEED_PASSWORDS[uid]),
                            email=c.get("email", ""), phone=c.get("phone", ""),
                            manager_id=c.get("manager_id"), active=True))
            db.commit()
        else:
            # Backfill existing rows created before round 46 (tenant/password_hash) or round 92
            # (contact/org-chart fields), so nothing needs a fresh DB to pick up either change.
            changed = False
            for u in db.scalars(select(User)):
                if not u.tenant:
                    u.tenant = "default"; changed = True
                if not u.password_hash and u.id in SEED_PASSWORDS:
                    u.password_hash = auth.hash_password(SEED_PASSWORDS[u.id]); changed = True
                c = SEED_CONTACT.get(u.id, {})
                if not u.email and c.get("email"):
                    u.email = c["email"]; changed = True
                if not u.phone and c.get("phone"):
                    u.phone = c["phone"]; changed = True
                if u.manager_id is None and c.get("manager_id"):
                    u.manager_id = c["manager_id"]; changed = True
                if u.active is None:
                    u.active = True; changed = True
            if changed:
                db.commit()
        if not db.scalar(select(Brief).limit(1)):
            _seed_brief(db)
            db.commit()


def _seed_brief(db: Session) -> None:
    attrs = {"campaign_objective": "Festive / seasonal", "budget_value": 1_500_000}
    b = Brief(
        id="brief_seed_1",
        title="Festive IMC plan FY26 — Pure Doodh Ki Shakti",
        brief_type="IMC",
        campaign_objective="Festive / seasonal",
        background_context="Diwali festive window; dairy gifting and daily-strength messaging.",
        business_objective="Grow Toned Milk + Ghee festive sales 15% YoY.",
        communication_objective="Own 'purity = family strength' during the festive season.",
        target_consumer="Urban mothers 28-40 buying daily fresh milk for the family.",
        consumer_insight="Festivals are when mothers most want to give their family the 'purest' nourishment.",
        competitive_context="Regional dairy brands pushing festive packs aggressively.",
        single_minded_proposition="(sample brief — replace with your own proposition)",
        reasons_to_believe="Farm-fresh sourcing; rigorous purity testing; trusted since decades.",
        tone_personality="Warm, trustworthy, rooted in everyday Indian family life.",
        mandatories_brand_codes="(sample brief — the brand profile holds the real codes)",
        deliverables_channels="Instagram, LinkedIn, Facebook, YouTube.",
        timeline_milestones="Teaser W1, launch W2, sustain W3-4.",
        success_metrics_kpis="Reach, engagement rate, festive pack sell-through.",
        budget="₹15,00,000",
        budget_value=1_500_000,
        creator_id="puneet",
        status="Draft",
        required_levels=domain.required_levels("Brief", attrs),
        approvals=[], history=[],
    )
    db.add(b)
