"""briefstore.py — kept briefs, in a form everything downstream can actually read.

The brief is the first document in the spine and, until now, the only one that was never kept:

    Brief -> Messaging house -> Idea platform -> Communication plan -> Executions

A brief lived in client state, one at a time, and vanished on reload. The messaging house asked for one
in a free-text box and the server discarded it, because it wanted a dict. So every house ever built was
generated against *"(no brief attached)"* while the screen showed the words somebody had typed. That is
the bug this module exists to close.

**Two shapes, kept together.** Briefs arrive from three different screens with three different field
sets — the skill-driven brand brief, the guided formats, and the IMC builder. Rather than force one
schema on all of them, each brief keeps its `fields` verbatim *and* a `canon` translation into the names
the house, plan and executions consume. Nothing is lost and nothing downstream has to know which screen
it came from.

**Saving is automatic.** Anything that produces a brief document saves it on the way past, so briefs
accumulate without anybody choosing to keep them. A store that depends on someone pressing Save is a
store that is empty when it matters.

**Brand is the brief's, and it travels.** A house or plan built from a brief inherits its brand rather
than asking for it again. Typing the brand three times in three screens is what let a brief for one
brand and a house for another sit side by side looking related.
"""
from __future__ import annotations

import json
import os
import time
import uuid

import tenancy

# Resolved through tenancy so one deployment can hold several companies. The name is kept
# so every reader in this module is unchanged.
BRIEF_DIR = tenancy.dir("briefs")
# The names everything downstream reads. `strategy._brief_text()` and the execution envelope use these,
# so a brief from any screen becomes usable by translating into them once, here.
CANON = ("brand", "title", "format", "businessObjective", "marketingObjective", "commObjective",
         "background", "targetAudience", "consumerInsight", "currentBelief", "desiredBelief",
         "smp", "rtbs", "toneOfVoice", "mandatories", "competition", "successMetrics",
         "packHierarchy", "deliverables", "budget", "timeline",
         # ROUND-83 AUDIT: these two were the most distinctive parts of the brand-brief skill's own
         # output (the NeedScope bridge territory and competitor pins, the SMP defence table) and had no
         # canon path at all — `ALIASES` had no key for either, so `canonicalise()` could never produce
         # them regardless of which screen saved. `smp_unlocks` bundled in for the same reason: brand's
         # own "what this proposition unlocks" answer, drafted alongside `smp`/`smp_defence` and equally
         # absent downstream.
         "needscopeAnalysis", "smpDefence", "smpUnlocks",
         # IMC ingestion Phase 3: the brand brief's new Backgrounder section (category perspective,
         # current situation, consumer insights, problem statement — see research_parse.py's Map/
         # Synthesize pipeline and brief_ai.py's `backgrounder` output field) had the same gap the
         # ROUND-83 audit found — real content the skill now drafts, with no canon path to reach the
         # house, so every house built from a brief with real qualitative research behind it was still
         # generated against "(brief is empty)" for the fields that matter most: what consumers actually
         # think, and the specific problem the house exists to solve. `background`/`consumerInsight`
         # already existed as canon fields (see ALIASES below for how they now also catch the
         # backgrounder's content) — `currentSituation` and `problemStatement` did not, so they are new.
         "currentSituation", "problemStatement")

# How each screen's names map onto the canonical ones. First hit wins, so the more specific source is
# listed first. A key absent from every alias simply stays in `fields` and is not lost.
ALIASES: dict[str, tuple[str, ...]] = {
    "businessObjective": ("businessObjective", "business_objective", "objective_business"),
    "marketingObjective": ("marketingObjective", "marketing_objective"),
    "commObjective": ("commObjective", "comms_objective", "objective", "campaign_objective",
                      "communication_objective"),
    # `category_perspective` listed before `sources_note`: a real category read (from the backgrounder,
    # when the brief has one) is what "background" is actually for — `sources_note` (a list of uploaded
    # filenames) was only ever the least-wrong thing available before the backgrounder existed.
    "background": ("background", "context", "situation", "category_perspective", "sources_note"),
    "targetAudience": ("targetAudience", "audience", "target_audience", "cohort"),
    "consumerInsight": ("consumerInsight", "insight", "consumer_insight", "consumer_insights"),
    "currentBelief": ("currentBelief", "current_belief", "cb", "shift_from"),
    "desiredBelief": ("desiredBelief", "desired_belief", "db", "shift_to"),
    "smp": ("smp", "proposition", "single_minded_proposition", "bigIdea", "big_idea", "messages"),
    "rtbs": ("rtbs", "reasons_to_believe", "rtb", "claims"),
    "toneOfVoice": ("toneOfVoice", "tone", "tone_of_voice", "personality"),
    "mandatories": ("mandatories", "mandatory", "must_include"),
    "competition": ("competition", "competitors", "competitive_context", "landscape"),
    "successMetrics": ("successMetrics", "kpis", "success_metrics", "measures"),
    "packHierarchy": ("packHierarchy", "pack_hierarchy"),
    "deliverables": ("deliverables",),
    "budget": ("budget", "budget_value"),
    "timeline": ("timeline", "milestones"),
    "brand": ("brand", "brand_name"),
    "title": ("title", "name", "brief_title"),
    "format": ("format", "format_name", "brief_format"),
    "needscopeAnalysis": ("needscope",),
    "smpDefence": ("smp_defence",),
    "smpUnlocks": ("smp_unlocks",),
    "currentSituation": ("currentSituation", "current_situation"),
    "problemStatement": ("problemStatement", "problem_statement"),
}


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _path(bid: str) -> str:
    return os.path.join(BRIEF_DIR, f"{bid}.json")


def load(bid: str) -> dict | None:
    try:
        with open(_path(bid), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(b: dict) -> dict:
    os.makedirs(BRIEF_DIR, exist_ok=True)
    b["updated"] = _now()
    tmp = _path(b["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(b, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path(b["id"]))
    return b


def _flatten(value) -> str:
    """Briefs arrive with nested objects and lists. Downstream wants sentences."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(x for x in (_flatten(v) for v in value) if x)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            t = _flatten(v)
            if t:
                parts.append(f"{str(k).replace('_', ' ')}: {t}")
        return " · ".join(parts)
    return str(value)


def canonicalise(fields: dict) -> dict:
    """Translate any screen's field names into the ones the rest of the spine reads.

    Shallow keys are searched first, then one level of nesting — the IMC builder posts
    `cb_ca_db_da: {shift_from, shift_to}` and the brand brief posts `needscope: {...}`, and the useful
    values are inside. Anything unmatched stays in `fields`; this is a translation, not a filter.
    """
    flat: dict = {}
    for k, v in (fields or {}).items():
        flat.setdefault(str(k), v)
        if isinstance(v, dict):
            for k2, v2 in v.items():
                flat.setdefault(str(k2), v2)

    out: dict = {}
    for canon, names in ALIASES.items():
        for n in names:
            if n in flat and _flatten(flat[n]):
                out[canon] = _flatten(flat[n])
                break
    return out


def origin(brief: dict) -> str:
    """'drafted' if nobody has explicitly saved since the AI wrote it, 'reviewed' once they have.

    Derived from `source` rather than a second stored field — `source` already carries exactly this
    distinction and is already set correctly at the two moments that matter: `/brand-brief-draft`
    writes `"brand-brief-draft"` the instant the model returns, before any human has read a word of it;
    every explicit Save (the only route behind an actual button click) overwrites it unconditionally.
    A parallel `origin` field would just be a second home for the same decision, with no way to stop
    the two drifting apart — the exact failure this codebase's own stores warn against by name.

    One honest caveat: unlike `strategy.py`'s `edit_option()`, which only re-sources an option to
    `"user"` when its text actually changed, an explicit brief Save flips this to `"reviewed"` whether
    or not anything was touched — a whole-document save is a coarser grain than one option line, and a
    real diff check across an entire `fields` dict is a bigger job than the benefit justifies for v1.
    """
    return "reviewed" if brief.get("source") not in ("", "brand-brief-draft") else "drafted"


def as_text(b: dict, limit: int = 2400) -> str:
    """The brief as prose, for a generation prompt. Empty fields are omitted, not padded."""
    canon = b.get("canon") or {}
    lines = [f"{k}: {v}" for k, v in canon.items() if str(v).strip() and k not in ("title", "format")]
    return "\n".join(lines)[:limit] or "(the brief is empty)"


def snapshot(b: dict) -> dict:
    """The row shape every picker and panel reads.

    The four summary values appear **both** at the top level and under `fields`. That is not sloppiness:
    the client normalises rows in one place and reads `fields.proposition`, while other callers had been
    reading the flat keys since before `fields` existed. Sending one shape would have broken whichever
    caller was not chosen, and the duplication costs four strings per row.

    `status` comes from the brief's own fields — the editor sets it to Draft, Pending or Approved — and a
    picker that could not show it would offer an unapproved brief exactly as confidently as an approved
    one. `no_profile` says the brand behind this brief has no profile, which is the difference between
    grounded generation and generic.
    """
    c = b.get("canon") or {}
    f = b.get("fields") or {}
    summary = {
        "proposition": c.get("smp", ""),
        "audience": c.get("targetAudience", ""),
        "tone": c.get("toneOfVoice", ""),
        "objective": c.get("commObjective") or c.get("businessObjective", ""),
    }
    brand = c.get("brand", "")
    return {"id": b.get("id", ""), "brief_id": b.get("id", ""),
            "brand": brand, "title": b.get("title", ""), "format": b.get("format", ""),
            # The project this brief starts. Everything downstream inherits it, so this is the one
            # place it is asked for.
            "project": str(b.get("project") or "").strip(),
            "project_source": b.get("project_source", ""),
            "label": (f"{brand} \u00b7 {b['project']}" if str(b.get("project") or "").strip()
                      and brand else str(b.get("project") or "") or brand),
            "status": str(f.get("status") or "").strip(),
            "origin": origin(b),
            "no_profile": not _has_profile(brand),
            "brand_mode": b.get("brand_mode") or "grounded",
            "updated": b.get("updated", ""), "created": b.get("created", ""),
            **summary, "fields": dict(summary)}


def _has_profile(brand: str) -> bool:
    """Whether a brand profile stands behind this brand name. Kept tolerant: an unreadable profile store
    must not make every brief claim to be ungrounded."""
    if not str(brand or "").strip():
        return False
    try:
        import brandprofile
        return brandprofile.by_name(brand) is not None
    except Exception:
        return True


def put(fields: dict, *, brand: str = "", title: str = "", fmt: str = "",
        source: str = "", brief_id: str = "", project: str = "", brand_mode: str = "") -> dict:
    """Save a brief. Upserts on `brief_id`, so re-generating does not litter the store with near-copies.

    Called automatically by everything that produces a brief document, which is what makes the store
    fill up on its own. A store that waits for somebody to press Save is empty when it matters.

    `brand_mode` — `"grounded"` or `"general"`, a DECISION someone made, not inferred from whether
    `brand` happens to be blank. A blank `brand` has always been possible by accident (nothing typed
    yet); it is not the same fact as "this work is deliberately not tied to a brand," and treating
    them as one is what let generation downstream silently borrow whichever brand was active for a
    brief that was never meant to have one. Unset (the default) preserves the prior caller's own value
    on an edit, or falls to `"grounded"` for a brand-new brief — today's exact behavior, unchanged
    until a caller actually starts passing `"general"` on purpose.
    """
    fields = fields or {}
    existing = load(brief_id) if brief_id else None
    new_canon = canonicalise(fields)
    brand = (brand or new_canon.get("brand") or "").strip()
    title = (title or new_canon.get("title") or "").strip()
    fmt = (fmt or new_canon.get("format") or "").strip()
    # DATA-LOSS BUG (round-83 audit, confirmed live): a screen whose payload nests one level deeper than
    # `canonicalise()` expects extracts an incomplete `new_canon` — this used to REPLACE the brief's
    # canon outright, silently deleting fields a PRIOR, correctly-shaped save had already extracted (the
    # IMC builder's own visible "Save" button did exactly this to belief fields its own auto-save had
    # just written correctly). Merge onto whatever canon already exists: a save only ever adds or
    # updates a field it actually found something for this time, never blanks one just because this
    # particular payload didn't repeat it.
    canon = dict((existing or {}).get("canon") or {})
    canon.update({k: v for k, v in new_canon.items() if v})
    if brand:
        canon["brand"] = brand
    if not title:
        title = f"{brand or 'Untitled'} — {fmt or 'brief'}"

    b = existing or {"id": uuid.uuid4().hex[:10], "created": _now()}
    # The project is named here and inherited by everything downstream. Only set when given, so a later
    # save that does not mention it cannot wipe a name somebody typed.
    proj = str(project or fields.get("project") or "").strip()
    if proj:
        b["project"] = proj[:80]
        b.setdefault("project_source", "named")
    b.update({"brand": brand, "title": title, "format": fmt,
              "source": source or b.get("source", ""),
              "fields": fields, "canon": canon,
              "brand_mode": brand_mode or b.get("brand_mode") or "grounded"})
    return save(b)


def briefs(brand: str = "") -> list[dict]:
    """Newest first — the order somebody looking for what they just wrote expects."""
    os.makedirs(BRIEF_DIR, exist_ok=True)
    out = []
    for f in os.listdir(BRIEF_DIR):
        if not f.endswith(".json"):
            continue
        b = load(f[:-5])
        if not b:
            continue
        if brand and str(b.get("brand", "")).strip().lower() != brand.strip().lower():
            continue
        out.append(snapshot(b))
    return sorted(out, key=lambda x: x.get("updated", ""), reverse=True)


def brands() -> list[dict]:
    """Every brand that has a brief, and how many. What makes a second brand visible at all.

    A brief with no brand is counted separately rather than listed as a brand called "Unnamed". This is a
    list somebody picks a brand from, and an entry that is not a brand does not belong in it — but the
    count is still reported, because briefs missing a brand are worth knowing about.
    """
    counts: dict[str, int] = {}
    unbranded = 0
    for f in os.listdir(BRIEF_DIR) if os.path.isdir(BRIEF_DIR) else []:
        if not f.endswith(".json"):
            continue
        b = load(f[:-5])
        if not b:
            continue
        name = str(b.get("brand") or "").strip()
        if not name:
            unbranded += 1
        else:
            counts[name] = counts.get(name, 0) + 1
    # `active` and `profile_id` are carried here so a screen listing brands from briefs can mark which one
    # the studio is working on without a second call and a client-side join. The Memory panel needs
    # exactly that, and a join it has to do itself is a join it will get wrong.
    active_name, by_name = "", {}
    try:
        import brandprofile
        for p in brandprofile.profiles():
            by_name[str(p.get("name", "")).strip().lower()] = p["id"]
            if p.get("active"):
                active_name = str(p.get("name", "")).strip().lower()
    except Exception:
        pass          # the brief library must list even if profiles are unreadable

    out = []
    for k, v in sorted(counts.items()):
        # `name` and `brand` both carry it. The Memory panel reads `name`; the pickers read `brand`.
        row = {"brand": k, "name": k, "briefs": v, "count": v,
               "active": k.strip().lower() == active_name}
        if k.strip().lower() in by_name:
            row["profile_id"] = by_name[k.strip().lower()]
        else:
            # A brand with briefs but no profile is worth surfacing: it is why generation for it will
            # come back ungrounded.
            row["no_profile"] = True
        out.append(row)
    if unbranded:
        out.append({"brand": "", "name": "", "briefs": unbranded, "count": unbranded,
                    "no_brand": True, "active": False,
                    "detail": f"{unbranded} brief(s) with no brand named"})
    return out


def remove(bid: str) -> bool:
    try:
        os.remove(_path(bid))
        return True
    except OSError:
        return False


def resolve(value, *, keep: bool = False) -> dict | None:
    """Take whatever a screen sent for "the brief" and return a brief-shaped dict.

    Accepts an id, a dict of fields, or free text.

    **Free text is not filed in the library.** The messaging-house screen sends the brief's words as
    text on purpose — the core message is drafted from what is on screen, so it has to stay readable and
    editable. Filing each one produced a library row per house started, titled "Typed at the messaging
    house" with no brand, and a library of nameless fragments is worse than the bug it replaced: it makes
    the picker useless, which is the one thing the library exists for.

    So typed text comes back as an unsaved brief. It still reaches the house — `new_house` stores it, so
    the generator sees it and nothing is lost — it just does not pretend to be a document somebody wrote.
    `keep=True` files it anyway, for a caller that genuinely means to.
    """
    if not value:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        found = load(text)          # an id, most often
        if found:
            return found
        if keep:
            return put({"background": text}, title="Typed at the messaging house", source="typed")
        return {"id": "", "title": "", "brand": "", "format": "",
                "fields": {"background": text}, "canon": canonicalise({"background": text}),
                "unsaved": True}
    if isinstance(value, dict):
        if value.get("id") and load(str(value["id"])):
            return load(str(value["id"]))
        return put(value, source="inline")
    return None
