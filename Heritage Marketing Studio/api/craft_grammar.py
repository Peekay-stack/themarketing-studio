"""craft_grammar.py -- film GRAMMARS: how one KIND of film is shot and shown (beauty is not food is not home care).

The general craft notes (`craft_skill/SKILL.md`) are one way of making an ad: people who want something, talk, a gag, a bet. That is the grammar of a household or
food story and it fights the grammar of a beauty film, which is looked at more than followed. A grammar is a short, reviewable text file in `craft_skill/grammars/`
(front matter, then `## SECTIONS`) that is chosen from the brand's category, or by the person, and that replaces the parts of the general notes it contradicts.

Only a category that has a grammar file is affected; any other category gets the general notes exactly as before. Craft mode is itself off unless the server switch
CRAFT_BRIEF and the request flag are both on (craft.py), so none of this reaches a prompt until then.

Sections a grammar file may carry:
  INTRO                replaces the general notes opening paragraph (the one about people who want something, and talk)
  FILM                 added to the craft block in the system prompt (what the writer is told about this kind of film)
  ROUTES_STAND         the page's "three routes" wording when an idea platform is attached (replaces the general one)
  ROUTES_STAND_FREE    the same, with no platform
  ROUTES_ALIVE         the page's "make each route ..." paragraph (replaces the general one)
  SPEECH               the sentence that follows the page's speech budget
  SCRIPT               how this kind of film is written as scene rows from a chosen concept (the stake seen, show before say, the pack as a hero shot, ...); added to the full-script prompt by the page
  FRAME                how this kind of FILM FRAME (the picture one scene is drawn from) is drawn: what the scene text names must be IN the frame; added to the image prompt of /scene-still for
                       film frames only (video_frame), and only when craft mode is on (craft.frame_for_prompt)
  PHOTO                how this kind of STILL photograph is shot and shown (a social post, a carousel slide, a key visual); added to the image prompt of /scene-still
                       for static images only, never to a film frame, and only when craft mode is on (craft.photo_for_prompt)
Front matter keys: id, label, match (comma separated category words, matched as word starts), vo_mult (speech budget multiplier; general craft mode uses 1.5),
replaces (comma separated titles of general-note sections to leave out when this grammar applies).
"""
from __future__ import annotations

import os
import re

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "craft_skill", "grammars")
_cache: dict = {"sig": None, "items": {}}


def _parse(raw: str) -> dict | None:
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", raw, flags=re.S)
    if not m:
        return None
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    gid = re.sub(r"[^a-z0-9_]", "", meta.get("id", "").lower())
    if not gid:
        return None
    sections: dict[str, str] = {}
    cur = None
    for line in m.group(2).splitlines():
        h = re.match(r"##\s+([A-Z_]+)\s*$", line)
        if h:
            cur = h.group(1)
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    sections = {k: "\n".join(v).strip("\n") for k, v in sections.items()}
    try:
        vo = float(meta.get("vo_mult", "")) if meta.get("vo_mult") else None
    except ValueError:
        vo = None
    return {"id": gid, "label": meta.get("label") or gid,
            "match": [w.strip().lower() for w in meta.get("match", "").split(",") if w.strip()],
            "vo_mult": vo, "replaces": [w.strip() for w in meta.get("replaces", "").split(",") if w.strip()],
            "sections": sections}


def _all() -> dict[str, dict]:
    """Every grammar file, cached by file times. A missing folder or a malformed file simply means no grammar (the general notes apply)."""
    try:
        names = sorted(n for n in os.listdir(_DIR) if n.endswith(".md"))
        sig = tuple((n, os.path.getmtime(os.path.join(_DIR, n))) for n in names)
    except OSError:
        return {}
    if _cache["sig"] != sig:
        items = {}
        for n in names:
            try:
                g = _parse(open(os.path.join(_DIR, n), encoding="utf-8").read())
            except OSError:
                g = None
            if g:
                items[g["id"]] = g
        _cache["sig"], _cache["items"] = sig, items
    return _cache["items"]


def options() -> list[dict]:
    return [{"id": g["id"], "label": g["label"]} for g in _all().values()]


def get(gid: str) -> dict | None:
    return _all().get(str(gid or "").strip().lower())


def pick(brand: dict | None, chosen: str = "") -> tuple[str, str]:
    """(grammar id, why). `chosen` is the person's own pick: a grammar id, or "general" for the general notes; blank means choose from the brand's category.
    ("", why) means no grammar applies and the general notes stand."""
    c = str(chosen or "").strip().lower()
    if c == "general":
        return "", "you chose the general notes"
    if c and get(c):
        return c, "you chose it"
    cat = str((brand or {}).get("category") or "").strip().lower()
    if cat:
        for g in _all().values():
            for w in g["match"]:
                if re.search(r"\b" + re.escape(w), cat):
                    return g["id"], f"the brand's category is “{(brand or {}).get('category')}”"
    return "", ("no brand category on file" if not cat else f"no grammar written yet for “{(brand or {}).get('category')}”")


def drop_sections(body: str, titles: list[str]) -> str:
    """The general notes without the `## ` sections whose heading starts with one of `titles`."""
    if not titles:
        return body
    parts = re.split(r"(?m)^(?=## )", body)
    keep = [p for p in parts if not (p.startswith("## ") and any(p[3:].strip().lower().startswith(t.lower()) for t in titles))]
    return "".join(keep).strip()


def block(gid: str) -> str:
    g = get(gid)
    return (g["sections"].get("FILM") or "") if g else ""


def photo_block(gid: str) -> str:
    g = get(gid)
    return (g["sections"].get("PHOTO") or "") if g else ""


def frame_block(gid: str) -> str:
    g = get(gid)
    return (g["sections"].get("FRAME") or "") if g else ""


def view(brand: dict | None, chosen: str = "") -> dict:
    """What the page needs: which grammar applies and why, its wording, and the list to choose from. With none, the page keeps its own (general) wording."""
    gid, why = pick(brand, chosen)
    g = get(gid) if gid else None
    s = (g or {}).get("sections", {})
    return {"id": gid, "label": (g["label"] if g else "General"), "why": why, "options": options(),
            "routes_stand": s.get("ROUTES_STAND", ""), "routes_stand_free": s.get("ROUTES_STAND_FREE", ""),
            "routes_alive": s.get("ROUTES_ALIVE", ""), "speech_note": s.get("SPEECH", ""), "script_note": s.get("SCRIPT", ""),
            "vo_mult": (g or {}).get("vo_mult")}
