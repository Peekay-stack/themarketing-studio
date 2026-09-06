"""models.py — SQLAlchemy ORM. Briefs and Deliverables share the approval fields
that domain.py operates on. Lists are stored as JSON columns.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # Creator | ApproverL1 | L2 | L3
    # One tenant per user (round 46 call — the smaller build; switching is real future work, not
    # guessed at here). Defaults to the single tenant this process actually serves.
    tenant: Mapped[str] = mapped_column(String, default="default")
    # "salt$iterations$hex_digest", stdlib PBKDF2-HMAC-SHA256 — no new dependency for a Windows dev
    # setup that has already had enough install friction. Empty until /login is used for real.
    password_hash: Mapped[str] = mapped_column(String, default="")
    # Round 92 — the approval-hierarchy/org-chart feature. Contact details for the notification phase
    # that isn't built yet (email/SMS delivery is its own later decision — see MEMORY), and `manager_id`
    # for the org-chart *view* only. Approval GATING itself reads `brandprofile.approval_hierarchy`'s
    # explicit primary/backup assignment, not this chain — a gate should check an explicit allow-list,
    # not walk an inferred reporting graph at request time (see that module's own note).
    email: Mapped[str] = mapped_column(String, default="")
    phone: Mapped[str] = mapped_column(String, default="")
    manager_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    # Soft-deactivate, never delete — an offboarded approver's past approvals must stay attributed
    # correctly. A level assignment pointing at an inactive user is a real, visible finding (see
    # `brandprofile.approval_gaps`), not a silent dangling reference.
    active: Mapped[bool] = mapped_column(default=True)


class Session(Base):
    """A signed-out-by-default session: real server-side revocation on logout, not a client-side
    token discard that leaves a leaked token still valid. Cheap at this scale — one small table,
    one row per active sign-in."""
    __tablename__ = "sessions"
    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    created: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    expires: Mapped[dt.datetime] = mapped_column(DateTime)


class Brief(Base):
    __tablename__ = "briefs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, default="Brief")
    title: Mapped[str] = mapped_column(String)
    brief_type: Mapped[str] = mapped_column(String, default="Comms")  # Comms|IMC|Media|Packaging
    campaign_objective: Mapped[str] = mapped_column(String, default="Brand awareness")
    # strategic + execution fields (free text)
    background_context: Mapped[str] = mapped_column(Text, default="")
    business_objective: Mapped[str] = mapped_column(Text, default="")
    communication_objective: Mapped[str] = mapped_column(Text, default="")
    target_consumer: Mapped[str] = mapped_column(Text, default="")
    consumer_insight: Mapped[str] = mapped_column(Text, default="")
    competitive_context: Mapped[str] = mapped_column(Text, default="")
    single_minded_proposition: Mapped[str] = mapped_column(Text, default="")
    reasons_to_believe: Mapped[str] = mapped_column(Text, default="")
    tone_personality: Mapped[str] = mapped_column(Text, default="")
    mandatories_brand_codes: Mapped[str] = mapped_column(Text, default="")
    deliverables_channels: Mapped[str] = mapped_column(Text, default="")
    timeline_milestones: Mapped[str] = mapped_column(Text, default="")
    success_metrics_kpis: Mapped[str] = mapped_column(Text, default="")
    budget: Mapped[str] = mapped_column(String, default="")
    budget_value: Mapped[int] = mapped_column(Integer, default=0)
    # workflow
    creator_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="Draft")
    required_levels: Mapped[list] = mapped_column(JSON, default=list)
    current_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approvals: Mapped[list] = mapped_column(JSON, default=list)
    history: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    deliverables: Mapped[list[Deliverable]] = relationship(back_populates="brief")


class Deliverable(Base):
    __tablename__ = "deliverables"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, default="Deliverable")
    brief_id: Mapped[str] = mapped_column(ForeignKey("briefs.id"))
    platform: Mapped[str] = mapped_column(String)
    format: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String, default="Post")  # Post|Video|Campaign
    caption: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    rationale: Mapped[str] = mapped_column(Text, default="")
    brand_flags: Mapped[list] = mapped_column(JSON, default=list)
    # creative
    creative_kind: Mapped[str | None] = mapped_column(String, nullable=True)  # image|video
    creative_model: Mapped[str | None] = mapped_column(String, nullable=True)
    creative_url: Mapped[str | None] = mapped_column(String, nullable=True)
    # workflow
    creator_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="Draft")
    required_levels: Mapped[list] = mapped_column(JSON, default=list)
    current_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approvals: Mapped[list] = mapped_column(JSON, default=list)
    history: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    brief: Mapped[Brief] = relationship(back_populates="deliverables")
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="deliverable", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    deliverable_id: Mapped[str] = mapped_column(ForeignKey("deliverables.id"))
    role: Mapped[str] = mapped_column(String)  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    deliverable: Mapped[Deliverable] = relationship(back_populates="messages")
