"""complete.py — backs the front end's window.claude.complete().

The front end calls window.claude.complete({messages}) for every AI feature
(brief fields, social posts, video scenes, campaigns, insights). That function only
exists inside Claude's artifact sandbox. This endpoint provides it for real:

- If ANTHROPIC_API_KEY is set, it calls Claude and returns the completion text.
- If not, it returns an empty string. The front end's own try/catch then falls back
  to its built-in placeholder content, so nothing breaks — you just don't get live AI
  until a key is present.

The front end already asks for strict JSON in its prompts; this endpoint adds a brand +
quality "master prompt" as the system message (see prompts.py) so every surface stays
on-brand and in the expected shape, then obeys the front end's requested JSON format.
"""
from __future__ import annotations

import os

GEN_MODEL = os.environ.get("GEN_MODEL", "claude-opus-4-8")
MAX_TOKENS = int(os.environ.get("COMPLETE_MAX_TOKENS", "8000"))


def has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def complete(messages: list[dict], execution: str = "", force_typed: bool = False,
             skip_mandatories: bool = False) -> str:
    if not has_key():
        return ""  # front end falls back to its own placeholder content
    import anthropic

    from prompts import system_for
    client = anthropic.Anthropic()
    norm = [{"role": m.get("role", "user"), "content": str(m.get("content", ""))} for m in messages]
    # `execution` names the one briefed piece this call is for, so the spine can bind to its audience and
    # its channel rather than offering the whole plan and letting the model choose. `force_typed` — round
    # 92's "set the platform aside" checkbox, see `system_for`'s own note on exactly what it does and does
    # not skip. `skip_mandatories` — same round, separate flag: the caller's own read on whether none of
    # the plan/idea/brief trio applies to this piece; see `brandprofile.voice_block`'s docstring.
    system = system_for(norm, execution=execution, force_typed=force_typed, skip_mandatories=skip_mandatories)
    # 2000 was too tight once a surface asks for several posts or several scenes: the reply is JSON, so a
    # truncation is not a short answer, it is an unparseable one — which reaches the person as the
    # feature silently doing nothing.
    resp = client.messages.create(model=GEN_MODEL, max_tokens=MAX_TOKENS, system=system, messages=norm)
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
