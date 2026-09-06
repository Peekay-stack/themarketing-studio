"""project.py — the name that tells two pieces of work apart.

Two messaging houses both called "Heritage", both "8 of 8 layers decided", and nothing on the card to
say which is the Diwali push and which is the launch. The brand is not the unit of work — a brand has
many projects, and every document in the spine belongs to exactly one of them.

**Asked once, at the brief, and inherited from there.** The brief is the earliest point in the spine and
everything descends from it, so a house started from a brief takes its project, a plan takes it from the
house, a platform from the house, a shoot from its execution. Asking again at each step would produce
four names for one campaign, which is worse than none.

**A derived name is marked as derived.** Documents made before this existed get one worked out from what
they have — the brief's title, failing that the month they were created. That is a guess, and it says so,
so somebody can correct it rather than discovering later that the studio quietly named their work.

The name is also what makes a folder of downloads legible: `Heritage_Diwali-same-day-push_house.docx`
rather than four files called `Heritage_messaging_house.docx`.
"""
from __future__ import annotations

import re
import time


def clean(name: str) -> str:
    """A project name as typed, trimmed. Empty when there is nothing worth keeping."""
    s = re.sub(r"\s+", " ", str(name or "")).strip(" -–—·")
    return s[:80]


def slug(name: str) -> str:
    """For a filename. Keeps it readable rather than hashing it."""
    s = re.sub(r"[^A-Za-z0-9]+", "-", str(name or "")).strip("-")
    return s[:48] or "untitled"


def of(doc: dict | None) -> str:
    """The project a document belongs to, or "" — never a guess."""
    return clean((doc or {}).get("project") or "")


def inherit(child: dict, *parents) -> dict:
    """Give `child` the project of the first parent that has one. Mutates and returns it.

    Never overwrites a project the child already carries: somebody who has renamed a plan meant it, and
    a later save from the house should not undo it.
    """
    if of(child):
        return child
    for p in parents:
        got = of(p) or clean(((p or {}).get("brief") or {}).get("project") or "")
        if got:
            child["project"] = got
            child["project_source"] = "inherited"
            return child
    return child


def derive(doc: dict | None, kind: str = "") -> dict:
    """A name for a document that predates projects. Returns `{project, project_source, why}`.

    Not saved by the caller until somebody accepts it. A derived name written straight to disk is
    indistinguishable from one a person chose, which is the thing this whole module exists to avoid.
    """
    doc = doc or {}
    brief = doc.get("brief") if isinstance(doc.get("brief"), dict) else {}
    for src, why in ((brief.get("title"), "the brief's title"),
                     (brief.get("project"), "the brief's project"),
                     (doc.get("title"), "its own title")):
        s = clean(src)
        if s:
            return {"project": s, "project_source": "derived", "why": f"taken from {why}"}
    created = str(doc.get("created") or "")
    when = ""
    try:
        t = time.strptime(created[:10], "%Y-%m-%d")
        when = time.strftime("%B %Y", t)
    except (ValueError, TypeError):
        when = "an earlier session"
    label = {"house": "house", "plan": "plan", "platform": "platform"}.get(kind, kind or "document")
    return {"project": f"{doc.get('brand') or 'Brand'} — {label}, {when}",
            "project_source": "derived",
            "why": "nothing named it, so this is its brand and the month it was created"}


def label(doc: dict | None, brand: str = "") -> str:
    """What a card shows: `Heritage · Diwali same-day push`, or just the brand when unnamed."""
    b = clean(brand or (doc or {}).get("brand") or "")
    p = of(doc)
    return f"{b} · {p}" if b and p else (p or b)


def filename(doc: dict | None, brand: str, what: str, ext: str = "docx") -> str:
    """`Heritage_Diwali-same-day-push_messaging-house.docx`.

    A folder of downloads was four files with the same name and a (1), (2), (3) after it. The project is
    the only thing that made them distinguishable, and it was not in the name.
    """
    parts = [slug(brand or "brand")]
    p = of(doc)
    if p:
        parts.append(slug(p))
    parts.append(slug(what))
    return "_".join(parts) + "." + ext.lstrip(".")
