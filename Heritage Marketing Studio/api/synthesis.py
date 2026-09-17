"""synthesis.py — the research-synthesis-deck SKILL's reasoning: turns synthesized research claims into
cross-source linkages, or an honest "no single pattern" verdict. See synthesis_skill/SKILL.md.

Deliberately does NOT re-parse uploaded files. Input is research_parse.ingest_for_brief()'s result — the
same Map->Synthesize claims list the brand brief's Reduce step reads — so this module only ever does one
more thing on top of what Phase 1 already built: look across the (already cross-file-merged, already
confidence-scored) claims for real multi-claim chains. See synthesis_skill/references/
linkage-construction.md for what makes a chain real versus a coincidence.

Requires ANTHROPIC_API_KEY, same as brief_ai.py. Without it, build_linkages() raises NoApiKey.
"""
from __future__ import annotations

import os

_HERE = os.path.dirname(__file__)
_SKILL = os.path.join(_HERE, "synthesis_skill")
_REFS = ["linkage-construction.md", "deck-structure.md"]


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


_LINKAGE_PROMPT = """{skill}

=====  THE SYNTHESIZED RESEARCH CLAIMS FOR THIS DECK  =====
These are already cross-file-merged and confidence-scored by an earlier pass — read them as reliable
inputs, not something to re-verify from scratch.{focus_line}

{claims_block}
{pattern_note_block}
=====  YOUR OUTPUT  =====
Apply the skill above — build real chains from the claims, per references/linkage-construction.md, or
say plainly that none coheres. Return ONLY this JSON object (no prose, no markdown fences):

{{
  "headline": {{
    "has_pattern": true or false,
    "statement": "one or two sentences — the single strongest reading if has_pattern is true, or a plain
                   statement that the sources do not converge on one pattern if false",
    "confidence": "high", "medium", "low", or "" (empty when has_pattern is false)
  }},
  "linkages": [
    {{
      "label": "",                      // set to "Read A", "Read B", etc. ONLY when presenting competing
                                          // reads rather than one chain; otherwise leave empty
      "title": "one-line reading — what the chain points to, in the evidence's own terms, never a plan",
      "confidence": "high|medium|low",   // the chain's own confidence: the WEAKEST claim it depends on
      "claims": [
        {{"text": "one sentence", "confidence": "high|medium|low", "sources": ["filename", ...]}}
      ]
    }}
  ],
  "standalone_findings": [               // used when has_pattern is false: each source's best standalone
                                          // finding, so the deck still orients the reader
    {{"text": "one sentence", "sources": ["filename", ...]}}
  ]
}}

Rules: leave "linkages" empty when has_pattern is false. Every claim's "sources" must be real filenames
that appear in the claims above — never invent a source. Build 2-4 candidate chains before concluding
none holds up. A chain built entirely from claims tracing to ONE file is not a cross-source linkage —
say so in that chain's title rather than presenting it as triangulation."""


def build_linkages(research: dict | None, *, focus: str = "") -> dict:
    """Produce the deck's content from an ingest_for_brief() result.

    research: research_parse.ingest_for_brief() output — {"filenames", "synth", "file_results"}.
    Returns {"filenames", "headline", "linkages", "standalone_findings", "considered_not_used",
    "pattern_note"} — the last two pass straight through from research["synth"] since that phase already
    did the "what wasn't used, and why" and "does this cohere" work; this function only adds the linkage
    layer on top. Raises NoApiKey if no key is set.
    """
    if not has_key():
        raise NoApiKey("ANTHROPIC_API_KEY is not set")
    research = research or {}
    synth = research.get("synth") or {}
    claims = synth.get("claims") or []
    filenames = research.get("filenames") or []

    if not claims:
        # Nothing to link — an honest empty deck, not a failed API call. Mirrors research_parse's own
        # "say what's missing" discipline rather than raising for a case that isn't actually an error.
        return {"filenames": filenames, "headline": {
                    "has_pattern": False,
                    "statement": "No synthesized research claims were available to build a cross-source "
                                 "read from — check that files were uploaded and successfully parsed.",
                    "confidence": ""},
                "linkages": [], "standalone_findings": [],
                "considered_not_used": synth.get("considered_not_used") or [],
                "pattern_note": synth.get("pattern_note") or ""}

    claims_block = "\n".join(
        f"- [{c.get('confidence', '?')}] {c.get('claim', '')} "
        f"(sources: {', '.join(c.get('supporting_sources') or []) or '?'}"
        + (f"; contested by: {', '.join(c.get('dissenting_sources'))}" if c.get("dissenting_sources") else "")
        + ")"
        for c in claims
    )
    focus_line = f"\nThis synthesis is for: {focus}\n" if focus else ""
    pattern_note = synth.get("pattern_note", "")
    pattern_note_block = (f"\nAn earlier cross-file read already noted: {pattern_note}\n"
                          if pattern_note else "")

    prompt = _LINKAGE_PROMPT.format(skill=_skill_instructions(), focus_line=focus_line,
                                    claims_block=claims_block, pattern_note_block=pattern_note_block)

    import jsonout
    data, err = jsonout.ask_json(prompt, max_tokens=3000)
    if data is None:
        # Same fallback shape as research_parse.synthesize_research()'s own failure path — the deck
        # still ships, just without the linkage layer, rather than a hard 500 for a marketer waiting on
        # a deck.
        return {"filenames": filenames, "headline": {
                    "has_pattern": False,
                    "statement": f"Linkage synthesis failed ({err}) — showing the underlying claims "
                                 "unlinked instead.",
                    "confidence": ""},
                "linkages": [],
                "standalone_findings": [{"text": c.get("claim", ""),
                                         "sources": c.get("supporting_sources") or []} for c in claims],
                "considered_not_used": synth.get("considered_not_used") or [],
                "pattern_note": pattern_note}

    data.setdefault("headline", {"has_pattern": False, "statement": "", "confidence": ""})
    data.setdefault("linkages", [])
    data.setdefault("standalone_findings", [])
    data["filenames"] = filenames
    data["considered_not_used"] = synth.get("considered_not_used") or []
    data["pattern_note"] = pattern_note
    return data
