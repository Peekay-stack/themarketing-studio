"""craft.py -- the film CRAFT BRIEF: what makes a film memorable, entertaining and clear, as prompt text.

**No model is trained here** (see learning.py's header, which stays true). This is a short, versioned, original-safe set of craft notes
(`craft_skill/SKILL.md`, distilled from the reference-ads learning log: AD_LEARNING_LOG.md and FILM_CRAFT_LAYER_PLAN.md, workstream W0) that is put in front of
the model when it writes a film concept or a film script. It is advice for the director, never a rule or a gate.

Two switches, BOTH must be on, so nothing changes until someone chooses it:
  * the server switch  ``CRAFT_BRIEF``  (environment; default off): "1", "true" or "on" turns it on for this server;
  * the request flag   ``craft: true``   (the page sends it on film concept / script calls).
With either off, `for_prompt()` returns "" and every prompt is byte for byte what it was.
"""
from __future__ import annotations

import os
import re

import craft_grammar

_SKILL = os.path.join(os.path.dirname(__file__), "craft_skill")
_cache: dict = {"mtime": None, "text": ""}


def server_on() -> bool:
    """The server-wide switch. Default off."""
    return str(os.environ.get("CRAFT_BRIEF", "")).strip().lower() in ("1", "true", "on", "yes")


def _text() -> str:
    """The skill body without its front matter, cached by file time. Empty if the file is missing (then the feature simply does nothing)."""
    f = os.path.join(_SKILL, "SKILL.md")
    try:
        m = os.path.getmtime(f)
    except OSError:
        return ""
    if _cache["mtime"] != m:
        raw = open(f, encoding="utf-8").read()
        body = re.sub(r"\A---\n.*?\n---\n", "", raw, count=1, flags=re.S).strip()
        _cache["mtime"], _cache["text"] = m, body
    return _cache["text"]


def for_prompt(requested: bool, brand: dict | None = None, grammar: str = "") -> str:
    """The craft block for a film concept/script prompt, or "" unless the server switch AND the request flag are both on.

    When the brand's category (or the person's own pick, `grammar`) has a film grammar (craft_grammar.py), the general notes it contradicts are left out and the grammar's own
    text follows. A category with no grammar gets the general notes exactly as before."""
    if not (requested and server_on()):
        return ""
    body = _text()
    if not body:
        return ""
    gid, _why = craft_grammar.pick(brand, grammar)
    g = craft_grammar.get(gid) if gid else None
    if g and g["sections"].get("FILM"):
        body = craft_grammar.drop_sections(body, g["replaces"])
        if g["sections"].get("INTRO"):   # the general opening paragraph says the film should be people who want something, and talk: a grammar may state its own
            body = re.sub(r"(?m)^\*\*Singleness is about the message.*$", lambda _m: g["sections"]["INTRO"], body, count=1)
        body = body + "\n\n" + g["sections"]["FILM"]
    return "FILM CRAFT NOTES (advice for the director: use what serves this brief, never imitate a known film)\n" + body


def photo_for_prompt(requested: bool, brand: dict | None = None, grammar: str = "") -> str:
    """How this kind of STILL photograph is shot, for the image prompt of a static picture (social post, carousel slide), or "".

    Same two switches as `for_prompt` (server CRAFT_BRIEF and the request flag). It also needs a grammar that applies (the brand's category or the person's pick)
    AND carries a PHOTO section: a category with no grammar, or a grammar with no PHOTO section, adds nothing, so those image prompts stay byte for byte as they were."""
    if not (requested and server_on()):
        return ""
    gid, _why = craft_grammar.pick(brand, grammar)
    return craft_grammar.photo_block(gid).strip() if gid else ""
