"""provocation.py -- a Provocation: a deliberate, approved break from the category's codes.

    Brief -> Messaging house -> Idea platform -> PROVOCATION (optional) -> Executions

The idea platform settles WHAT the brand says and the device that repeats it. A provocation settles a different thing: where
the work departs from how the whole category talks and looks, and how far. It is optional, made on demand, and written for one
idea platform in one house. Producers use it the way they use a platform or a campaign: they STAND ON it (see
`producers.stands_on`), per medium, and a person can set it aside for any one piece.

**It must come from the platform.** A provocation breaks the category's codes, not the brand's core message: it is built on a
platform, carries the fingerprint of the house and platform it was written under, and says so when either has since moved
(`stale_because`) -- the same way a campaign does -- instead of quietly contradicting a revised platform.

**A person approves it.** Nothing here is usable until `approve()` -- a draft, an archived record and a record for another house
are all ignored by `usable()`. Approval needs a name, the line, a risk label and, when the work jabs at competitors, an
acknowledgement that a human legal review is coming. Editing an approved provocation puts it back to a draft: what was approved
is not what is now written.

**Hard limits are not options.** `HARD_LIMITS` is what no provocation may do (the guardrail check that reads them is built with
the tab). They are listed here so a screen, a prompt and a test all read the same words.

This module is the store and the rules only: no model call, no network, nothing generated. Writing one (the codes audit, the
sparks, the scoring) is the tab's job.

A record:

    {id, house, platform, name, status: draft|approved|archived,
     core: {line, codes_broken[], stance{tone, humour, structure}, risk: low|medium|high, risk_note, safer_version,
            legal_flag, legal_ack, legal_note},
     expressions: {<medium>: text},                  # media.EXPRESSIONS keys, like a campaign
     film: {structure, humour, visual_language, sound_language, cast_approach: people|objects|animated|none,
            vo_words, brand_beat, notes},             # what Video reads (the "Film DNA")
     source: {codes_audit[], sparks[]},
     generated_under: {house, platform},              # fingerprints, for staleness
     approved_by, approved_at, created, updated}
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid

import ideas
import media
import tenancy

DIR = tenancy.dir("provocations")
EVIDENCE_DIR = tenancy.dir("categoryevidence")

STATUSES = ("draft", "approved", "archived")
RISKS = ("low", "medium", "high")
CAST_APPROACHES = ("people", "objects", "animated", "none")

# What no provocation may do. Words a screen shows, a prompt is told and a test pins -- one list, so they cannot drift.
HARD_LIMITS = (
    "No celebrity or real person's likeness.",
    "No health claims.",
    "Nothing that offends on food, children or religion.",
    "Competitors only as an archetype or a category cliche, never a named rival -- and a human legal review is flagged.",
)

_FILM_TEXT = ("structure", "humour", "visual_language", "sound_language", "brand_beat", "notes")


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _s(x, n: int) -> str:
    """Text only: a number or a list in a text field is a mistake, not text, so it becomes empty."""
    return " ".join(x.split())[:n] if isinstance(x, str) else ""


def _strs(x, count: int, n: int) -> list[str]:
    return [t for t in (_s(i, n) for i in (x if isinstance(x, list) else [])[:count]) if t]


def _path(pid: str) -> str:
    return os.path.join(DIR, f"{pid}.json")


def normalise(rec) -> dict:
    """Any dict -> a record of exactly this shape. Unknown keys are dropped, overlong text is cut, wrong types become empty:
    what arrives from a screen is never trusted to be well formed."""
    rec = rec if isinstance(rec, dict) else {}
    core = rec.get("core") if isinstance(rec.get("core"), dict) else {}
    stance = core.get("stance") if isinstance(core.get("stance"), dict) else {}
    film = rec.get("film") if isinstance(rec.get("film"), dict) else {}
    expr = rec.get("expressions") if isinstance(rec.get("expressions"), dict) else {}
    src = rec.get("source") if isinstance(rec.get("source"), dict) else {}
    under = rec.get("generated_under") if isinstance(rec.get("generated_under"), dict) else {}
    status = _s(rec.get("status"), 20).lower()
    risk = _s(core.get("risk"), 20).lower()
    cast = _s(film.get("cast_approach"), 20).lower()
    vo = film.get("vo_words")
    out_film = {k: _s(film.get(k), 800) for k in _FILM_TEXT}
    out_film["cast_approach"] = cast if cast in CAST_APPROACHES else ""
    out_film["vo_words"] = int(vo) if isinstance(vo, (int, float)) and not isinstance(vo, bool) and 0 <= vo <= 120 else None
    sparks = []
    for it in (src.get("sparks") if isinstance(src.get("sparks"), list) else [])[:12]:
        if isinstance(it, dict):
            sparks.append({"text": _s(it.get("text"), 500), "score": it.get("score") if isinstance(it.get("score"), (int, float)) and not isinstance(it.get("score"), bool) else None})
    return {
        "id": _s(rec.get("id"), 40),
        "house": _s(rec.get("house"), 60),
        "platform": _s(rec.get("platform"), 60),
        "name": _s(rec.get("name"), 120),
        "status": status if status in STATUSES else "draft",
        "core": {
            "line": _s(core.get("line"), 400),
            # A code is the audit's wording; the audit's "(memory)" / "(seen)" basis tag is not part of it (drafts made
            # before 6 Oct carry it, and the screen matches codes to the audit by text).
            "codes_broken": [t for t in (re.sub(r"\s*\((?:memory|seen)\)\s*$", "", c, flags=re.I) for c in _strs(core.get("codes_broken"), 8, 200)) if t],
            "stance": {k: _s(stance.get(k), 300) for k in ("tone", "humour", "structure")},
            "risk": risk if risk in RISKS else "",
            "risk_note": _s(core.get("risk_note"), 600),
            "safer_version": _s(core.get("safer_version"), 800),
            "legal_flag": core.get("legal_flag") is True,
            "legal_ack": core.get("legal_ack") is True,
            "legal_note": _s(core.get("legal_note"), 500),
        },
        "expressions": {k: _s(expr.get(k), 1500) for k in media.EXPRESSIONS if _s(expr.get(k), 1500)},
        "film": out_film,
        "source": {"codes_audit": _strs(src.get("codes_audit"), 12, 300), "sparks": sparks},
        "generated_under": {"house": _s(under.get("house"), 40), "platform": _s(under.get("platform"), 40)},
        "approved_by": _s(rec.get("approved_by"), 80),
        "approved_at": _s(rec.get("approved_at"), 20),
        "created": _s(rec.get("created"), 20),
        "updated": _s(rec.get("updated"), 20),
    }


def new(house_id: str, platform_id: str = "", name: str = "") -> dict:
    now = _now()
    rec = normalise({"id": uuid.uuid4().hex[:12], "house": house_id, "platform": platform_id, "name": name})
    rec["created"] = rec["updated"] = now
    return rec


def load(pid: str) -> dict | None:
    pid = "".join(c for c in str(pid or "") if c.isalnum())      # an id is a filename: nothing else gets through
    if not pid:
        return None
    try:
        with open(_path(pid), encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, ValueError):
        return None
    return normalise(rec) if isinstance(rec, dict) else None


def save(rec: dict) -> dict:
    rec = normalise(rec)
    if not rec["id"]:
        rec["id"] = uuid.uuid4().hex[:12]
    rec["id"] = "".join(c for c in rec["id"] if c.isalnum())
    rec["updated"] = _now()
    rec["created"] = rec["created"] or rec["updated"]
    os.makedirs(DIR, exist_ok=True)
    tmp = _path(rec["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path(rec["id"]))
    return rec


def for_house(house_id: str, platform_id: str = "", include_archived: bool = False) -> list[dict]:
    """A house's provocations, newest first. **An empty house id returns nothing, deliberately**: a listing that skipped its
    filter for an empty id would hand one house another's work (ideas.for_house learned this the hard way)."""
    house_id = str(house_id or "").strip()
    if not house_id:
        return []
    out = []
    os.makedirs(DIR, exist_ok=True)
    for f in os.listdir(DIR):
        if not f.endswith(".json"):
            continue
        rec = load(f[:-5])
        if not rec or rec["house"] != house_id:
            continue
        if platform_id and rec["platform"] != platform_id:
            continue
        if rec["status"] == "archived" and not include_archived:
            continue
        out.append(rec)
    return sorted(out, key=lambda r: (r["updated"], r["id"]), reverse=True)


def usable(rec: dict | None, house_id: str) -> bool:
    """Approved, and belonging to THIS house. The only test a producer applies."""
    return bool(rec and rec.get("status") == "approved" and str(house_id or "").strip()
                and rec.get("house") == str(house_id).strip())


def resolve_for(house_id: str, provocation_id: str) -> dict | None:
    """The provocation a request names, or None: unknown, not approved, or another house's."""
    if not str(provocation_id or "").strip():
        return None
    rec = load(provocation_id)
    return rec if usable(rec, house_id) else None


def expression_for(rec: dict | None, kind: str) -> str:
    """What the provocation says this medium becomes: its own expression, else its line."""
    if not rec:
        return ""
    return str((rec.get("expressions") or {}).get(kind) or "").strip() or str((rec.get("core") or {}).get("line") or "").strip()


# ---- approval ---------------------------------------------------------------------------------

def approval_problems(rec: dict) -> list[str]:
    rec = normalise(rec)
    out = []
    if not rec["name"]:
        out.append("Give it a name -- it is how a producer will pick it.")
    if not rec["core"]["line"]:
        out.append("Write the provocation itself: the line that says where this departs from the category.")
    if not rec["core"]["risk"]:
        out.append("Say how risky it is (low, medium or high) -- an approval without a risk label hides the one thing a reviewer needs.")
    if rec["core"]["legal_flag"] and not rec["core"]["legal_ack"]:
        out.append("It jabs at competitors, so a human legal review is needed: tick that it is going to legal before approving.")
    return out


def approve(rec: dict, who: str, on: bool = True) -> tuple[dict | None, list[str]]:
    """Approve (or withdraw approval from) a record. Returns (record, problems); problems non-empty means nothing changed."""
    rec = normalise(rec)
    if rec["status"] == "archived":
        return None, ["An archived provocation cannot be approved -- bring it back to a draft first."]
    if not on:
        rec["status"], rec["approved_by"], rec["approved_at"] = "draft", "", ""
        return rec, []
    problems = approval_problems(rec)
    if problems:
        return None, problems
    rec["status"], rec["approved_by"], rec["approved_at"] = "approved", _s(who, 80) or "someone", _now()
    return rec, []


def _content(rec: dict) -> dict:
    """What a person wrote: the record without its bookkeeping (status, approval, stamps, fingerprints)."""
    r = normalise(rec)
    for k in ("id", "status", "approved_by", "approved_at", "created", "updated", "generated_under"):
        r.pop(k, None)
    return r


def apply_edit(existing: dict | None, data: dict, house: dict | None, platform: dict | None) -> dict:
    """The record after the person edited it. Status and approval can never be set through an edit: only `approve()` approves.

    What was approved is not what is now written, so an edited approved record is a draft again. The fingerprints are
    re-stamped only when the content changed (or the record is new) -- the person has just reviewed it against the house and
    platform as they stand -- and NOT on a save that changed nothing, which would silently clear a staleness warning."""
    base = normalise(existing) if existing else {}
    data = data if isinstance(data, dict) else {}
    merged = normalise({**base, **data, "id": base.get("id") or data.get("id") or "", "house": base.get("house") or data.get("house") or "",
                        "status": base.get("status") or "draft",
                        "approved_by": base.get("approved_by", ""), "approved_at": base.get("approved_at", ""),
                        "created": base.get("created", ""), "generated_under": base.get("generated_under") or {}})
    if not existing or _content(merged) != _content(base):
        merged["generated_under"] = basis(house, platform)
        if merged["status"] == "approved":
            merged["status"], merged["approved_by"], merged["approved_at"] = "draft", "", ""
    return merged


def archive(rec: dict, on: bool = True) -> dict:
    rec = normalise(rec)
    rec["status"] = "archived" if on else "draft"
    rec["approved_by"] = rec["approved_at"] = ""
    return rec


# ---- staleness --------------------------------------------------------------------------------

def basis(house: dict | None, platform: dict | None) -> dict:
    """The fingerprints a provocation is written under: the house's decisions and the platform's own line, mechanic and
    expressions (the same two fingerprints a platform and a campaign already use)."""
    return {"house": ideas.house_basis(house)["signature"] if house else "",
            "platform": ideas.platform_signature(platform) if platform else ""}


def stale_because(rec: dict | None, house: dict | None, platform: dict | None) -> list[str]:
    """Why this provocation may no longer fit what it was written for (empty when it still does). An archived or
    never-stamped record is not judged."""
    if not rec or rec.get("status") == "archived":
        return []
    under = rec.get("generated_under") or {}
    out = []
    if under.get("house") and house is not None and under["house"] != ideas.house_basis(house)["signature"]:
        out.append("The messaging house has changed since this was written.")
    if rec.get("platform"):
        if platform is None or str(platform.get("id") or "") != rec["platform"]:
            out.append("The idea platform it was built on is no longer the chosen one.")
        elif under.get("platform") and under["platform"] != ideas.platform_signature(platform):
            out.append("The idea platform has changed since this was written.")
    return out


def as_read(rec: dict, house: dict | None = None, platform: dict | None = None) -> dict:
    """The record as a screen reads it: itself plus why it is stale, what blocks approval, and the hard limits."""
    return {**rec, "stale_because": stale_because(rec, house, platform), "problems": approval_problems(rec),
            "hard_limits": list(HARD_LIMITS)}


# ---- competitor evidence: what the person has SEEN, saved once per house ------------------------------------------
#
# The codes audit is only as good as what it is shown. Names alone leave the model working from memory of the brands, which is
# dated and sometimes wrong, so a person may add, per competitor, what they have actually seen in five places. Everything is
# optional; with none of it the audit still runs and says plainly that its codes are hypotheses. The evidence is text and links
# only: the studio's AI path cannot open a link or read an image, so what it reads is what the person wrote.

CHANNELS = ("packaging", "instagram", "social_video", "posm", "tvc")
CHANNEL_LABELS = {"packaging": "Packaging", "instagram": "Instagram page", "social_video": "Social video", "posm": "POSM", "tvc": "TVC"}
MAX_COMPETITORS = 6


def normalise_evidence(data) -> dict:
    """Any dict -> {competitors: [{name, channels: {<channel>: {note, link}}}]}. Blank names are dropped, repeats merged away,
    everything capped; a client is never trusted to be well formed."""
    raw = (data.get("competitors") if isinstance(data, dict) else None)
    out, seen = [], set()
    for c in (raw if isinstance(raw, list) else []):
        if not isinstance(c, dict):
            continue
        name = _s(c.get("name"), 80)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        ch = c.get("channels") if isinstance(c.get("channels"), dict) else {}
        out.append({"name": name, "channels": {k: {"note": _s((ch.get(k) or {}).get("note") if isinstance(ch.get(k), dict) else "", 800),
                                                   "link": _s((ch.get(k) or {}).get("link") if isinstance(ch.get(k), dict) else "", 300)}
                                               for k in CHANNELS}})
        if len(out) >= MAX_COMPETITORS:
            break
    return {"competitors": out}


def _evidence_path(house_id: str) -> str:
    return os.path.join(EVIDENCE_DIR, "".join(c for c in str(house_id or "") if c.isalnum()) + ".json")


def evidence_load(house_id: str) -> dict:
    """The saved evidence for a house, or an empty one. An empty house id has none (never another house's)."""
    if not "".join(c for c in str(house_id or "") if c.isalnum()):
        return {"competitors": [], "updated": ""}
    try:
        with open(_evidence_path(house_id), encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        return {"competitors": [], "updated": ""}
    return {**normalise_evidence(raw), "updated": _s(raw.get("updated") if isinstance(raw, dict) else "", 20)}


def evidence_save(house_id: str, data) -> dict:
    ev = normalise_evidence(data)
    ev["updated"] = _now()
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    tmp = _evidence_path(house_id) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(ev, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _evidence_path(house_id))
    return ev


def evidence_strength(ev: dict | None) -> dict:
    """How much the person has actually given: competitors with at least one slot filled, and slots filled out of those possible."""
    comps = (ev or {}).get("competitors") or []
    filled = sum(1 for c in comps for k in CHANNELS if (c["channels"][k].get("note") or c["channels"][k].get("link")))
    with_any = sum(1 for c in comps if any((c["channels"][k].get("note") or c["channels"][k].get("link")) for k in CHANNELS))
    return {"competitors": with_any, "slots_filled": filled, "slots_total": len(comps) * len(CHANNELS)}
