"""generation.py — copy generation, brand check, and chat-based refinement.

Uses the Anthropic SDK when ANTHROPIC_API_KEY is set; otherwise a deterministic MOCK so
the app runs end-to-end with zero keys. Mirrors the LangGraph pipeline's gates: structured
output + a brand-mandatory check. The brief-Approved gate is enforced in the route layer.
"""
from __future__ import annotations

import json
import os
import re

import brandprofile

GEN_MODEL = os.environ.get("GEN_MODEL", "claude-opus-4-8")

_PLATFORM_HINT = {
    "Instagram": "punchy, visual, emoji-light, 1-2 short paras",
    "LinkedIn": "professional, value-led, slightly longer",
    "Facebook": "warm, community tone",
    "Meta": "concise cross-feed copy",
    "YouTube": "a title + short description for the video",
}


def _client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    import anthropic
    return anthropic.Anthropic()


def _text(resp) -> str:
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()


def _strip(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        s = s.removesuffix("```")
    return s.strip()


def _mock(brief: dict, platform: str, fmt: str, instruction: str | None, prior: dict | None) -> dict:
    """The no-API-key path. Built from the brief and the brand profile rather than a hardcoded brand.

    Deliberately reads as a placeholder, and says so in the caption. An offline fallback that looked like
    finished copy is one somebody ships without ever realising no model ran.
    """
    b = brandprofile.resolve(brief) or {}
    smp = brief.get("single_minded_proposition") or b.get("master_idea") or "(no proposition yet)"
    base = prior.get("caption") if prior else smp
    tweak = f" ({instruction})" if instruction else ""
    idea = b.get("master_idea") or b.get("name") or "the brand"
    caption = (f"{base}{tweak}\n\n{idea}. "
               f"[{platform} · {fmt} — placeholder, no model was called]")
    return {
        "caption": caption,
        "hashtags": list(b.get("hashtags") or []) + [f"#{platform}"],
        "rationale": f"Offline placeholder from the brief and brand profile; shaped for {platform} {fmt}.",
    }


def _prompt(brief: dict, platform: str, fmt: str, instruction: str | None, prior: dict | None) -> str:
    b = brandprofile.resolve(brief)
    base = f"""{brandprofile.voice_block(b)}

You are this brand's copywriter. Write ONE {platform} post in {fmt} format.
Style for {platform}: {_PLATFORM_HINT.get(platform, "concise social copy")}.

Brief:
- SMP: {brief.get('single_minded_proposition','')}
- Target consumer: {brief.get('target_consumer','')}
- Tone: {brief.get('tone_personality','')}
- Mandatories (MUST appear): {brief.get('mandatories_brand_codes','')}
- Communication objective: {brief.get('communication_objective','')}"""
    if prior:
        base += f"\n\nPrevious version to revise:\n{json.dumps(prior, ensure_ascii=False)}"
    if instruction:
        base += f"\n\nApply this change: {instruction}"
    base += ('\n\nReturn ONLY JSON, no fences: '
             '{"caption":"...","hashtags":["..."],"rationale":"one line tying to the SMP"}')
    return base


def generate_copy(brief: dict, platform: str, fmt: str,
                  instruction: str | None = None, prior: dict | None = None) -> dict:
    client = _client()
    if client is None:
        return _mock(brief, platform, fmt, instruction, prior)
    resp = client.messages.create(
        model=GEN_MODEL, max_tokens=1024, temperature=0.8,
        messages=[{"role": "user", "content": _prompt(brief, platform, fmt, instruction, prior)}],
    )
    try:
        data = json.loads(_strip(_text(resp)))
        tags = data.get("hashtags", [])
        tags = [t if t.startswith("#") else f"#{t}" for t in tags if t.strip()]
        return {"caption": data["caption"], "hashtags": tags,
                "rationale": data.get("rationale", "")}
    except Exception:
        return _mock(brief, platform, fmt, instruction, prior)


def brand_check(caption: str, mandatories: str) -> list[str]:
    """Deterministic check: are the required brand codes present in the caption?"""
    flags: list[str] = []
    if not mandatories.strip():
        return flags
    # Pull quoted phrases as hard mandatories (e.g. 'Pure Doodh Ki Shakti').
    quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", mandatories)
    phrases = [a or b for a, b in quoted]
    for p in phrases:
        if p and p.lower() not in caption.lower():
            flags.append(f"Missing mandatory: '{p}'")
    return flags
