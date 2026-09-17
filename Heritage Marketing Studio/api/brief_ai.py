"""brief_ai.py — run the brand-brief SKILL's reasoning inside the app.

This replaces the old "user hand-builds every field" mechanism: the marketer gives a
prompt plus files (NeedScope chart image, market-share / household spreadsheets, decks,
research), and Claude — following the vendored brand-brief skill (SKILL.md + references) —
returns the full builder payload (competitors, NeedScope pin coordinates, CB/CA → DB/DA,
SMP, defence, unlocks). The front end then lets the user review/edit before rendering the
Word brief through the existing /brand-brief pipeline.

Requires ANTHROPIC_API_KEY. Without it, draft_brief() raises NoApiKey so the caller can
tell the user to add a key (the manual builder still works as a fallback).
"""
from __future__ import annotations

import json
import os

_HERE = os.path.dirname(__file__)
_SKILL = os.path.join(_HERE, "brief_skill")

# The framework references the model needs to reason well. Operational refs
# (input-parsing, docx-assembly) are not needed for the JSON reasoning step.
_REFS = ["needscope-framework.md", "cb-ca-db-da-framework.md", "smp-guidance.md"]


class NoApiKey(RuntimeError):
    """Raised when no ANTHROPIC_API_KEY is configured."""


def has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _read(path: str) -> str:
    try:
        return open(path, encoding="utf-8").read()
    except Exception:
        return ""


def _skill_instructions() -> str:
    parts = [_read(os.path.join(_SKILL, "SKILL.md"))]
    for r in _REFS:
        txt = _read(os.path.join(_SKILL, "references", r))
        if txt:
            parts.append(f"\n\n===== reference: {r} =====\n{txt}")
    return "\n".join(p for p in parts if p)


# The exact JSON the front-end builder consumes (buildBrief() in brand-brief-builder.html),
# which brandbrief.to_skill_brief() then maps into the .docx. The wheel geometry is spelled
# out so pin x/y land correctly on the 800x640 template.
_OUTPUT_CONTRACT = """
=====  YOUR OUTPUT  =====
Apply the skill above to the inputs, then return ONLY a single JSON object (no prose, no
markdown fences) with EXACTLY these keys. Every field must be filled from the inputs where
present, and sensibly inferred (and later flagged in caveats) where the inputs are silent.

{
  "brand": string,                       // focal brand
  "category": string,
  "prepared_for": string,
  "competitors": [                        // 3-5 direct competitors
    { "name": string, "hero_brands": string, "positioning": string, "recent_moves": string }
  ],
  "needscope": {
    "pins": [                             // one per brand: the focal brand AND every competitor
      { "brand": string, "x": int, "y": int, "anchor": bool }
    ],
    "bridge_territory": one of ["Power","Freedom","Vitality","Belonging","Security","Discernment"],
    "bridge_label": string,               // the platform name, e.g. "Pure Doodh Ki Shakti"
    "reading": string                     // 2-3 sentences: each brand's territory + whitespace
  },
  "cb_ca_db_da": {
    "cb": [string, ...],                  // 3 current-behaviour bullets
    "db": [string, ...],                  // 3 desired-behaviour bullets
    "ca_quote": string,                   // ONE verbatim current consumer quote (from research if provided)
    "ca_declarative": [string, string],   // 2 short lines on how the brand is currently held
    "da_quote": string,                   // ONE aspirational desired consumer quote
    "da_declarative": [string, string],   // 2 short lines on the desired attitude
    "shift_from": string,                 // e.g. "dependable purity"
    "shift_to": string,                   // e.g. "chosen family strength"
    "caption": string                     // one sentence: layer desired ON TOP of current, never replace
  },
  "smp": string,                          // ONE sentence, <=14 words, ends in a full stop
  "smp_defence": [                        // one row per direct competitor
    { "competitor": string, "why_collapses": string }
  ],
  "smp_unlocks": {
    "brand_line": string, "mass_line": string, "activation": string, "product": string
  }
}

=====  NEEDSCOPE PIN COORDINATES (critical)  =====
The wheel template is an 800x640 canvas. Centre = (400, 320). Place each pin with:
  x = 400 + r * cos(theta_deg in radians)
  y = 320 + r * sin(theta_deg in radians)
Territory centre angles (degrees): Power 270, Freedom 330, Vitality 30, Belonging 90,
Security 150, Discernment 210. Radii: focal/anchor brand r=125, major competitors r=140,
fringe brands r=150. To show a "pull" toward an adjacent territory, shift theta 10-25 deg
toward that territory's centre. Round x and y to integers. Exactly ONE pin has "anchor": true
(the focal brand). Do NOT put the anchor and its bridge_territory on opposite sides — the
bridge must be an ADJACENT territory.
"""


def _payload_context(base: dict, research: dict | None) -> str:
    def rows_text(data):
        if isinstance(data, dict) and data.get("rows"):
            return "\n".join(" | ".join(str(c) for c in r) for r in data["rows"][:30])
        return ""
    market = rows_text(base.get("market_data"))
    household = rows_text(base.get("household_data"))
    # Was a raw concatenate-and-truncate of every uploaded file to 16000 chars combined — the root
    # cause the user's own A/B test surfaced (a real slide's brand-equity scorecard fell past the cut).
    # Now reads research_parse's Map→Synthesize output: a short, cross-file-merged claims list with
    # confidence and citations, not a dump of the source text. See research_context_block()'s docstring.
    import research_parse
    research = research_parse.research_context_block(research)
    # General-mode work (deliberately not tied to a brand — see BRAND_GROUNDING_MODES_PLAN.md) must
    # not fall into "(infer from the ask)" here: that instruction is exactly what produced the
    # user-reported case of a brief inventing "India's favorite Biscuit" as a brand name it was never
    # given. Category-level inference is left alone — that's legitimate analysis, not a fabricated
    # brand identity.
    focal_brand = base.get("brand") or (
        "GENERAL WORK — no brand name has been given, and none should be invented or inferred. "
        "Write category-level analysis only; where the brief needs a brand name to make sense, say "
        "so rather than naming one."
        if base.get("brand_mode") == "general" else "(infer from the ask)")
    lines = [
        f"FOCAL BRAND: {focal_brand}",
        f"CATEGORY: {base.get('category') or '(infer from the ask)'}",
        f"PREPARED FOR: {base.get('prepared_for') or ''}",
        "",
        "BRIEF ASK (the marketer's request — anchor everything to this):",
        (base.get("prompt") or "").strip() or "(none given — build from the files and category)",
    ]
    if market:
        lines += ["", "MARKET SHARE / SALES DATA (use figures verbatim):", market]
    if household:
        lines += ["", "HOUSEHOLD / PENETRATION DATA (use figures verbatim):", household]
    if research:
        # research_context_block() already carries its own "RESEARCH FINDINGS ..." header.
        lines += ["", research]
    lines += ["", "Any attached images are NeedScope charts or CB/CA diagrams — read their brand "
              "positions as ground truth and reproduce them on the wheel."]
    return "\n".join(lines)


def draft_brief(base: dict, research: dict | None = None,
                images: list[dict] | None = None) -> dict:
    """Produce the builder payload by running the skill via Claude.

    base:     {brand, category, prepared_for, prompt, market_data, household_data}
    research: research_parse.ingest_for_brief() output for uploaded docs/sheets (Map+Synthesize
              result) — pass None when no files were uploaded
    images:   [{media_type, data_b64, filename}] for uploaded NeedScope/CB-CA chart images
    Returns the builder-payload dict. Raises NoApiKey if no key is set.
    """
    if not has_key():
        raise NoApiKey("ANTHROPIC_API_KEY is not set")
    import anthropic

    system = _skill_instructions() + "\n\n" + _OUTPUT_CONTRACT
    content: list[dict] = [{"type": "text", "text": _payload_context(base, research)}]
    for img in (images or [])[:4]:
        if img.get("data_b64") and img.get("media_type"):
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": img["media_type"], "data": img["data_b64"]}})

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=os.environ.get("GEN_MODEL", "claude-opus-4-8"),
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    raw = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise RuntimeError("Model did not return a JSON object")
    data = json.loads(raw[start:end + 1])
    return _normalise(data, base, research)


def _normalise(data: dict, base: dict, research: dict | None = None) -> dict:
    """Fill defaults and derive the shift_line so the payload is render-ready."""
    # sources_note used to be whatever the model volunteered (nothing in the output contract even
    # asked for it) — brief_render.py printed "Sources: none attached" even when files WERE attached,
    # a real contradiction the user's A/B test caught. Set it here from the actual filenames the route
    # was given, deterministically, not from a model self-report.
    # Left "" (not a fallback string) when nothing was attached — brief_render.py already has its own
    # "none attached" copy for that case; duplicating it here risks the two drifting apart.
    filenames = (research or {}).get("filenames") or []
    data["sources_note"] = f"{', '.join(filenames)}." if filenames else ""
    data.setdefault("brand", base.get("brand", "Brand"))
    data.setdefault("category", base.get("category", ""))
    data.setdefault("prepared_for", base.get("prepared_for", ""))
    ns = data.setdefault("needscope", {})
    ns.setdefault("pins", [])
    ns.setdefault("bridge_territory", "")
    ns.setdefault("bridge_label", "")
    ns.setdefault("reading", "")
    c = data.setdefault("cb_ca_db_da", {})
    for k in ("cb", "db", "ca_declarative", "da_declarative"):
        c.setdefault(k, [])
    for k in ("ca_quote", "da_quote", "shift_from", "shift_to", "caption"):
        c.setdefault(k, "")
    c["shift_line"] = f"From {c.get('shift_from','')} to {c.get('shift_to','')}."
    data.setdefault("competitors", [])
    data.setdefault("smp", "")
    data.setdefault("smp_defence", [])
    data.setdefault("smp_unlocks", {"brand_line": "", "mass_line": "", "activation": "", "product": ""})
    return data
