"""schemas.py — request bodies and response shapes."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    role: str
    tenant: str


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    user: UserOut


class BriefIn(BaseModel):
    title: str
    brief_type: str = "Comms"
    campaign_objective: str = "Brand awareness"
    background_context: str = ""
    business_objective: str = ""
    communication_objective: str = ""
    target_consumer: str = ""
    consumer_insight: str = ""
    competitive_context: str = ""
    single_minded_proposition: str = ""
    reasons_to_believe: str = ""
    tone_personality: str = ""
    mandatories_brand_codes: str = ""
    deliverables_channels: str = ""
    timeline_milestones: str = ""
    success_metrics_kpis: str = ""
    budget: str = ""
    budget_value: int = 0
    required_levels: list[int] | None = None  # explicit override


class BriefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    brief_type: str
    campaign_objective: str
    background_context: str
    business_objective: str
    communication_objective: str
    target_consumer: str
    consumer_insight: str
    competitive_context: str
    single_minded_proposition: str
    reasons_to_believe: str
    tone_personality: str
    mandatories_brand_codes: str
    deliverables_channels: str
    timeline_milestones: str
    success_metrics_kpis: str
    budget: str
    budget_value: int
    creator_id: str
    status: str
    required_levels: list[int]
    current_level: int | None
    approvals: list
    history: list
    created_at: dt.datetime


class DeliverableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    brief_id: str
    platform: str
    format: str
    content_type: str
    caption: str
    hashtags: list
    rationale: str
    brand_flags: list
    creative_kind: str | None
    creative_model: str | None
    creative_url: str | None
    creator_id: str
    status: str
    required_levels: list[int]
    current_level: int | None
    approvals: list
    history: list
    created_at: dt.datetime


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    role: str
    content: str
    created_at: dt.datetime


class GenTarget(BaseModel):
    platform: str
    format: str = "Static"
    content_type: str = "Post"


class GenerateIn(BaseModel):
    targets: list[GenTarget]
    creative_model: str | None = None  # if set, also generate a creative per post
    avatar: str | None = None           # HeyGen avatar id (avatar video)
    voice: str | None = None            # HeyGen voice id (avatar video)
    ratio: str | None = None            # "9:16" | "16:9" | "1:1"


class EditDeliverableIn(BaseModel):
    caption: str | None = None
    hashtags: list[str] | None = None


class ChatIn(BaseModel):
    message: str


class CreativeIn(BaseModel):
    model_id: str
    prompt: str | None = None
    avatar: str | None = None   # HeyGen avatar id (when model is an avatar provider)
    voice: str | None = None    # HeyGen voice id
    ratio: str | None = None    # "9:16" | "16:9" | "1:1"


class ApproveIn(BaseModel):
    note: str = ""
