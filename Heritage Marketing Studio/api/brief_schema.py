"""brief_schema.py — section/sub-section schema + routing per brief format.

Rules:
  • BRAND briefs are drafted with the comprehensive-brand-brief SKILL (rich builder → .docx).
  • COMMUNICATIONS and IMC follow the BUILDER format (curated here).            source="builder"
  • All OTHER formats (Media, Digital, Packaging, Product, PR) follow the FRONT END's
    own sections, extracted verbatim from the original studio HTML.        source="frontend"

Each field is (key, label, hint). This is the single source of truth the app + API use.
"""
from __future__ import annotations

BRAND_BRIEF = {
    "id": "brand", "name": "Brand Strategy Brief", "tag": "BR",
    "uses_skill": True, "source": "skill", "skill": "comprehensive-brand-brief:brand-brief",
    "output": "docx",
    "sections": [
        "Executive summary", "Competitor snapshot", "Messaging comparison matrix",
        "NeedScope brand positioning (Figure 1)", "CB/CA -> DB/DA shift (Figure 2)",
        "Single Minded Proposition + defence + unlocks", "Pricing, distribution & content snapshot",
        "Opportunities & threats", "Recommended actions", "Caveats",
    ],
}

# ---- COMMS & IMC: the BUILDER format (authoritative for these two) -------------
_BUILDER = {
    "comms": {
        "name": "Communications", "tag": "CO", "uses_skill": False, "source": "builder",
        "sections": [
            ("Strategic foundation", [
                ("background", "Background & context", "What business or market situation prompts this brief?"),
                ("businessObjective", "Business objective", "The commercial goal — sales, share, penetration, trials."),
                ("commObjective", "Communication objective", "What the communication must achieve — awareness, consideration, action."),
            ]),
            ("Audience & insight", [
                ("audience", "Target audience", "Demographics, geography, category role and occasions."),
                ("insight", "Consumer insight", "The human truth or tension the work taps into."),
                ("competition", "Competitive context", "Who/what we're up against and how we differ."),
            ]),
            ("Positioning", [
                ("proposition", "Single-minded proposition", "The one thought to land in the audience's mind."),
                ("rtbs", "Reasons to believe", "Proof points that make the proposition credible."),
            ]),
            ("Brand expression", [
                ("tone", "Tone & personality", "How it should feel and sound."),
                ("mandatories", "Mandatories & brand codes", "Logos, claims, legal, brand assets that must appear."),
            ]),
            ("Execution & measurement", [
                ("deliverables", "Deliverables & channels", "What exactly needs to be produced, and where."),
                ("budget", "Budget", "Indicative budget / cost guardrails."),
                ("timeline", "Timeline & milestones", "Key dates and approval gates."),
                ("kpis", "Success metrics / KPIs", "How we'll measure success."),
            ]),
        ],
    },
    "imc": {
        "name": "IMC", "tag": "IM", "uses_skill": False, "source": "builder",
        "sections": [
            ("Strategic foundation", [
                ("background", "Background & context", "What business or market situation prompts this brief?"),
                ("businessObjective", "Business objective", "The commercial goal across the integrated effort."),
                ("commObjective", "Communication objective", "What the integrated communication must achieve."),
            ]),
            ("Audience & insight", [
                ("audience", "Target audience", "Demographics, geography, category role and occasions."),
                ("insight", "Consumer insight", "The human truth or tension the work taps into."),
                ("competition", "Competitive context", "Who/what we're up against and how we differ."),
            ]),
            ("The big idea", [
                ("proposition", "Single-minded proposition", "The one thought to land across every channel."),
                ("bigIdea", "The one big idea", "The unifying creative idea that travels across touchpoints."),
                ("rtbs", "Reasons to believe", "Proof points that make the proposition credible."),
            ]),
            ("Integration", [
                ("channelRoles", "Role of each channel", "How ATL, digital, retail & PR each contribute to the idea."),
                ("tone", "Tone & personality", "How it should feel and sound, consistently."),
                ("mandatories", "Mandatories & brand codes", "Codes and assets that must stay consistent everywhere."),
            ]),
            ("Execution & measurement", [
                ("deliverables", "Deliverables & channels", "What needs producing across every channel."),
                ("budget", "Budget by channel", "How investment splits across channels and phases."),
                ("timeline", "Phasing & milestones", "How the campaign phases over time."),
                ("kpis", "Success metrics / KPIs", "The master KPI framework."),
            ]),
        ],
    },
}

# ---- MEDIA/DIGITAL/PACK/PRODUCT/PR: verbatim from the FRONT END ----------------
_FRONTEND = {
    "media": {
        "name": "Media", "tag": "ME", "uses_skill": False, "source": "frontend",
        "sections": [
            ("Strategic foundation", [
                ("background", "Background & context", "Market, seasonality and media-landscape context."),
                ("businessObjective", "Business objective", "The commercial goal this media plan supports."),
                ("commObjective", "Media objective", "Reach, frequency and outcome the plan must deliver."),
            ]),
            ("Audience", [
                ("audience", "Target audience", "Who we are buying — demographics, geography, role."),
                ("mediaHabits", "Media consumption habits", "When/where they watch, scroll, listen and shop."),
            ]),
            ("Media strategy", [
                ("channelMix", "Channel mix & role", "Which channels, and the job each one does."),
                ("reachGoals", "Reach & frequency goals", "1+/3+ reach targets and effective frequency."),
                ("markets", "Markets & flighting", "Priority markets and how spend is flighted."),
            ]),
            ("Investment & deliverables", [
                ("budget", "Budget", "Total budget and split across media."),
                ("deliverables", "Deliverables", "Plan, calendar and reporting outputs."),
            ]),
            ("Measurement", [
                ("kpis", "Media KPIs", "Reach, GRPs, CPM/CPRP efficiency, ROAS."),
            ]),
        ],
    },
    "digital": {
        "name": "Digital", "tag": "DG", "uses_skill": False, "source": "frontend",
        "sections": [
            ("Strategic foundation", [
                ("background", "Background & context", "Digital landscape and where the brand stands."),
                ("businessObjective", "Business objective", "The commercial outcome — trials, subscriptions, repeat."),
                ("commObjective", "Digital objective", "Awareness, consideration or conversion goal."),
            ]),
            ("Audience", [
                ("audience", "Target audience & segments", "Core segments and who we retarget."),
                ("digitalBehaviour", "Digital behaviour & platforms", "Where they discover, research and transact."),
            ]),
            ("Approach", [
                ("funnel", "Funnel & customer journey", "How content moves people from reach to action."),
                ("proposition", "Key message", "The core message for the work."),
            ]),
            ("Execution", [
                ("formats", "Formats & assets", "The creative formats and cuts needed."),
                ("deliverables", "Deliverables", "Assets, landing pages and CRM outputs."),
                ("targeting", "Targeting & tracking", "Audiences, geo/interest targeting, UTMs and tracking."),
                ("budget", "Budget", "Spend by platform and funnel stage."),
            ]),
            ("Measurement", [
                ("kpis", "Digital KPIs", "CTR, CPA, install->subscribe, ROAS, engagement."),
            ]),
        ],
    },
    "pack": {
        "name": "Packaging", "tag": "PK", "uses_skill": False, "source": "frontend",
        "sections": [
            ("Context", [
                ("background", "Background & context", "Why the pack needs to evolve now."),
                ("commObjective", "Role of the pack", "The job the pack must do at the shelf."),
                ("rangeArch", "Range architecture", "How variants relate within one family look."),
            ]),
            ("Consumer & shelf", [
                ("audience", "Target consumer", "Who picks it up and what they value."),
                ("shelfContext", "Shelf & competitive context", "How it competes and blocks on shelf."),
            ]),
            ("Design direction", [
                ("packHierarchy", "Pack hierarchy & key info", "The order of information front-of-pack."),
                ("claims", "Claims & RTBs", "Claims to feature and their substantiation."),
            ]),
        ],
    },
    "product": {
        "name": "Product Development", "tag": "PD", "uses_skill": False, "source": "frontend",
        "sections": [
            ("Opportunity", [
                ("background", "Market context & gap", "The unmet need or whitespace in market."),
                ("businessObjective", "Business objective", "Incremental volume, mix or premiumisation goal."),
            ]),
            ("Consumer", [
                ("consumerNeed", "Consumer need", "The functional/emotional need being served."),
                ("audience", "Target consumer", "Who the product is for."),
                ("insight", "Consumer insight", "The human truth behind the need."),
            ]),
            ("Concept", [
                ("concept", "Product concept", "What the product is and how it works."),
                ("rtbs", "Benefits & RTBs", "Benefits and the reasons to believe."),
                ("pricing", "Pricing & positioning", "Price ladder and where it sits in the range."),
            ]),
            ("Feasibility & launch", [
                ("feasibility", "Quality, regulatory & feasibility", "Shelf-life, plant capability, clearances."),
                ("deliverables", "Deliverables", "Concept board, sensory, launch checklist."),
                ("launch", "Launch plan & timeline", "Pilot, review and roll-out phasing."),
            ]),
            ("Measurement", [
                ("kpis", "Success metrics", "Trial, repeat, distribution, margin."),
            ]),
        ],
    },
    "pr": {
        "name": "Public Relations", "tag": "PR", "uses_skill": False, "source": "frontend",
        "sections": [
            ("Context", [
                ("background", "Background & context", "The reputation situation and opportunity."),
                ("businessObjective", "Reputation / business objective", "What trust or reputation goal this serves."),
                ("commObjective", "Communication objective", "What earned media must achieve."),
            ]),
            ("Audience", [
                ("stakeholders", "Target media & stakeholders", "Press, influencers and stakeholders to reach."),
                ("insight", "Insight / angle", "The truth that makes the story land."),
            ]),
            ("Narrative", [
                ("narrative", "Core narrative & angles", "The story and the angles we can pitch."),
                ("messages", "Key messages", "The messages every piece must carry."),
                ("spokespeople", "Spokespeople & proof points", "Who speaks and the proof they bring."),
            ]),
            ("Execution", [
                ("deliverables", "Deliverables", "Release, media list, Q&A, calendar."),
                ("mandatories", "Approvals & embargo", "Sign-offs, quotes and embargo timing."),
            ]),
        ],
    },
}

FRONTEND_FORMATS = {**_BUILDER, **_FRONTEND}
# stable display order
ORDER = ["comms", "imc", "media", "digital", "pack", "product", "pr"]


def resolve(format_id: str) -> dict:
    if format_id == "brand":
        return BRAND_BRIEF
    return FRONTEND_FORMATS.get(format_id, FRONTEND_FORMATS["comms"])


def uses_skill(format_id: str) -> bool:
    return resolve(format_id).get("uses_skill", False)


def source_of(format_id: str) -> str:
    return resolve(format_id).get("source", "frontend")


def draft_keys(format_id: str) -> list[str]:
    schema = resolve(format_id)
    if schema.get("uses_skill"):
        return []
    return [f[0] for _t, fields in schema["sections"] for f in fields]
