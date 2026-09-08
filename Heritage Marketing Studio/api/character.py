"""character.py — brand characters: a recurring, brand-owned face reused until it is retired.

    Segmentation study (or a pen portrait) -> Visual brief -> Cast -> Pressure test -> Approved character

A segmentation study settles *who a piece is for*. It does not settle *who the brand puts in front of
them, again and again, until that face is the brand's own*. Without something holding that decision,
six producers cast six separate stock photos for one idea and nothing accumulates. A character closes
that gap: one locked identity, pointed at by every producer's cast-lock, never redrafted per piece.

This module is the store and the discipline behind `character_skill/SKILL.md` — the skill is the
craft guidance a model follows when drafting; this file holds the resulting document, tracks it
through the pipeline, and refuses to call it approved until the skill's six tests actually pass. Same
"offered, sourced, never silently applied" rule the rest of the studio runs on: nothing here defaults
to approved, and `can_approve()` is a real gate, not a label.

A character is **brand-scoped** (test 6). It never crosses tenants and is not reused for another
brand's campaign. The approved reference frame lives in the reference library as a `cast` item, the
same as any other signed-off ground truth; this store holds everything around it — the pen portrait,
the visual brief, the cast lock, the test record, the approval.

Storage matches every other document store: one JSON file per character under the tenant's own
`character/` directory, resolved through `tenancy.dir()` on each call (not once per process).
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid

import tenancy

try:
    import brandprofile
except Exception:                       # brandprofile pulls optional deps in some contexts; the
    brandprofile = None                 # store must still load without it.

try:
    import jsonout
except Exception:
    jsonout = None

_SKILL = os.path.join(os.path.dirname(__file__), "character_skill")


# ---------------------------------------------------------------------------------------------------
# The pipeline. A character moves forward one stage at a time; a failed test sends it back a stage,
# named — never frozen in place. These are the SKILL.md stages made into state a screen can read.
STATES = ("draft", "candidate", "audition", "pressure", "approved", "retired")

# The six tests from the skill, in order. Each is pending / pass / fail with a note. `can_approve()`
# requires every one to be pass — an approver cannot wave a character through a test it failed.
TESTS = (
    ("pen_portrait_labelled",
     "Has a named, honestly-labelled pen portrait — research-backed or marked a working hypothesis."),
    ("signature_hook",
     "Has one specific, repeatable visual hook that is this character's alone, not a demographic."),
    ("specific_and_presentable",
     "Built from ownable detail AND cast the way a real ambassador is cast — not blandness, not "
     "unglamour-as-authenticity."),
    ("holds_across_contexts",
     "Rendered in at least three genuinely different situations before freezing, and held identity."),
    ("character_not_testimonial",
     "Framed as a character — no first-person product claims, no 'real customer says', no endorsement."),
    ("brand_scoped",
     "Built for one brand's segments. Not a shared library face with a logo dropped beside it."),
)
_TEST_KEYS = tuple(k for k, _ in TESTS)

# The honest label a pen portrait carries (test 1). Mirrors the skill's source tags.
PORTRAIT_SOURCES = ("segmentation", "pen-portrait", "assumed")

# The four shots the pressure test runs before a character is frozen (skill step / test 4). A default
# set, editable per character — the point is three genuinely different contexts, not these exact four.
DEFAULT_PRESSURE_SHOTS = (
    "6 a.m. working shot, vertical crop, available light, working-neutral expression",
    "Flat-lit waist-up POS cut-out, no background, direct closed smile",
    "Wide group frame, mixed warm light, an open expression",
    "Tired-honest close at the end of the day — the mood inversion",
)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(s or "").strip().lower()).strip("-")
    return s or "character"


# --- store ---------------------------------------------------------------------------------------

def _dir() -> str:
    return tenancy.dir("character")


def _path(cid: str) -> str:
    return os.path.join(_dir(), f"{cid}.json")


def load(cid: str) -> dict | None:
    try:
        with open(_path(cid), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(doc: dict) -> dict:
    if not doc.get("id"):
        doc["id"] = f"{_slug(doc.get('name'))}-{uuid.uuid4().hex[:6]}"
    doc.setdefault("created", _now())
    doc["updated"] = _now()
    doc["state"] = derive_state(doc)
    path = _path(doc["id"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return doc


def remove(cid: str) -> bool:
    try:
        os.remove(_path(cid))
        return True
    except OSError:
        return False


def list_characters(brand: str = "") -> list[dict]:
    d = _dir()
    out: list[dict] = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith(".json"):
            continue
        doc = load(f[:-5])
        if not doc:
            continue
        if brand and _slug(doc.get("brand")) != _slug(brand):
            continue
        out.append(summary(doc))
    # approved first, then the furthest along the pipeline
    order = {s: i for i, s in enumerate(STATES)}
    out.sort(key=lambda r: (r["state"] != "approved", -order.get(r["state"], 0), r["name"].lower()))
    return out


def for_brand(brand: str) -> list[dict]:
    """The approved characters a brand's producers may actually cast. Everything else is still a
    candidate and is not offered to a cast-lock."""
    return [load(r["id"]) for r in list_characters(brand) if r["state"] == "approved"]


# --- document ----------------------------------------------------------------------------------

def new_doc(brand: str, name: str, *, segment: str = "", segment_source: str = "assumed") -> dict:
    """A blank character, every section present so a screen never has to guard for a missing key."""
    if segment_source not in PORTRAIT_SOURCES:
        segment_source = "assumed"
    return {
        "id": "",
        "brand": (brand or "").strip(),
        "name": (name or "").strip(),
        "segment": (segment or "").strip(),
        "segment_source": segment_source,
        "scope_note": f"{(brand or 'this brand').strip()} only. Does not cross brands, tenants or "
                      f"campaigns.",
        "state": "draft",
        "version": 1,
        "supersedes": "",
        "pen_portrait": {
            "identity": {},           # name / age / lives / household / role — free key:value
            "background": "",
            "day_in_life": "",
            "head_goals": "",
            "heart_goal": "",
            "challenge": "",
            "context": "",
        },
        "hook": {
            "line": "",               # test 2 — nameable in one clause
            "detail": "",
            "prop": "",
            "prop_load_bearing": False,
            "routes_considered": [],   # [{tag, line}] — the roads not taken, kept on the record
            "route_selected": "",
            "route_confirmed": False,
        },
        "visual_brief": {
            "type_line": "",          # the casting Type — energy and presence in one phrase
            "look": "",               # age, build, hair, makeup, wardrobe palette, the one detail
            "region": "",
            "region_load_bearing": False,
            "setting": "",
            "light": "",
            "texture": "",
            "expression_range": [],    # [{expr, when}] — a range, never one fixed expression
        },
        "cast_lock": {
            "never_changes": [],       # face, build, the identity-anchoring details
            "changes_freely": [],      # wardrobe, hair-of-the-day, setting, and always mood/expression
        },
        "prompt_craft": {
            "base_prompts": [],        # [{label, prompt, negative}]
            "framings_proven": [],     # filled in only after the pressure test passes
        },
        "audition": {
            "spec": "",
            "negative": "",
            "run": False,
            "passed": None,
            "note": "",
        },
        "pressure_test": {
            "shots": [{"label": s, "done": False, "result": ""} for s in DEFAULT_PRESSURE_SHOTS],
            "run_by": "",
        },
        "per_producer": {
            "social": "",
            "pos": "",
            "video": "",
            "onground": "Usually does not apply — an activation is a real promoter in a real street.",
            "pr": "Does not apply — a character is never a spokesperson, source or quoted customer.",
        },
        "hard_lines": [
            "Character, never testimonial. No first-person product claims, no 'real customer says', "
            "no implied endorsement.",
            "Brand-scoped. Not a library face with a logo dropped beside it.",
            "Not approved until a named person approves it. Nothing defaults to approved.",
        ],
        "open_items": [],              # [{item, note, weight}] — the [assumed] things still to validate
        "tests": {k: {"pass": None, "note": ""} for k in _TEST_KEYS},
        "reference": {
            "library_id": "",         # the signed-off `cast` library item, once approved
            "candidates": [],         # raw draft image urls considered at casting
            "chosen": "",             # the one raw candidate taken forward
        },
        "approval": {
            "approved_by": "",
            "approved_date": "",
            "review_retire": "",
        },
        "created": "",
        "updated": "",
    }


def derive_state(doc: dict) -> str:
    """State is computed from what has actually happened, not set by a caller who might skip a step."""
    if doc.get("state") == "retired":
        return "retired"
    if doc.get("approval", {}).get("approved_by") and all_tests_pass(doc):
        return "approved"
    pt = doc.get("pressure_test", {})
    if pt.get("run_by") or any(s.get("done") for s in pt.get("shots", [])):
        return "pressure"
    aud = doc.get("audition", {})
    if aud.get("run"):
        return "audition"
    hook = doc.get("hook", {})
    brief = doc.get("visual_brief", {})
    if hook.get("line") and hook.get("route_selected") and brief.get("type_line"):
        return "candidate"
    return "draft"


def summary(doc: dict) -> dict:
    passed = sum(1 for k in _TEST_KEYS if doc.get("tests", {}).get(k, {}).get("pass") is True)
    return {
        "id": doc.get("id", ""),
        "name": doc.get("name", ""),
        "brand": doc.get("brand", ""),
        "segment": doc.get("segment", ""),
        "segment_source": doc.get("segment_source", "assumed"),
        "state": derive_state(doc),
        "version": doc.get("version", 1),
        "hook": doc.get("hook", {}).get("line", ""),
        "route": doc.get("hook", {}).get("route_selected", ""),
        "route_confirmed": bool(doc.get("hook", {}).get("route_confirmed")),
        "tests_passed": passed,
        "tests_total": len(_TEST_KEYS),
        "reference_id": doc.get("reference", {}).get("library_id", ""),
        "approved_by": doc.get("approval", {}).get("approved_by", ""),
        "updated": doc.get("updated", ""),
    }


# --- the six-test gate ------------------------------------------------------------------------

def record_test(doc: dict, key: str, passed: bool | None, note: str = "") -> tuple[dict | None, str]:
    if key not in _TEST_KEYS:
        return None, f"unknown test {key!r} — one of {', '.join(_TEST_KEYS)}"
    doc.setdefault("tests", {})[key] = {"pass": passed, "note": (note or "").strip()}
    return doc, ""


def all_tests_pass(doc: dict) -> bool:
    t = doc.get("tests", {})
    return all(t.get(k, {}).get("pass") is True for k in _TEST_KEYS)


def can_approve(doc: dict) -> tuple[bool, list[str]]:
    """Everything the skill says must be true before a person may approve. Returned as a list of
    what is still missing so a screen can show the checklist, not just a yes/no."""
    missing: list[str] = []
    hook = doc.get("hook", {})
    if not hook.get("line"):
        missing.append("no signature hook named")
    if not hook.get("route_selected"):
        missing.append("no hook route selected")
    if not hook.get("route_confirmed"):
        missing.append("hook route not confirmed by a person")
    brief = doc.get("visual_brief", {})
    if not brief.get("type_line"):
        missing.append("visual brief has no Type line")
    if not brief.get("look"):
        missing.append("visual brief has no Look")
    aud = doc.get("audition", {})
    if not aud.get("run"):
        missing.append("audition turn not run")
    elif aud.get("passed") is not True:
        missing.append("audition turn did not pass")
    pt = doc.get("pressure_test", {})
    done = [s for s in pt.get("shots", []) if s.get("done")]
    if len(done) < 3:
        missing.append(f"pressure test incomplete ({len(done)}/3 minimum contexts run)")
    if not pt.get("run_by"):
        missing.append("pressure test has no named runner")
    for k, label in TESTS:
        st = doc.get("tests", {}).get(k, {}).get("pass")
        if st is not True:
            missing.append(f"test not passed: {label}")
    if not doc.get("reference", {}).get("library_id"):
        missing.append("no signed-off reference frame in the library")
    return (not missing), missing


def approve(doc: dict, who: str) -> tuple[dict | None, str]:
    who = (who or "").strip()
    if not who:
        return None, "an approval needs a named person — nothing defaults to approved"
    ok, missing = can_approve(doc)
    if not ok:
        return None, "not ready to approve: " + "; ".join(missing)
    doc.setdefault("approval", {})["approved_by"] = who
    doc["approval"]["approved_date"] = _now()
    doc["state"] = "approved"
    return doc, ""


def retire(doc: dict, note: str = "") -> dict:
    doc["state"] = "retired"
    doc.setdefault("approval", {})["review_retire"] = (note or _now()).strip()
    return doc


def set_route(doc: dict, tag: str, *, confirmed: bool = True) -> dict:
    doc.setdefault("hook", {})["route_selected"] = (tag or "").strip()
    doc["hook"]["route_confirmed"] = bool(confirmed)
    return doc


def record_audition(doc: dict, *, run: bool = True, passed: bool | None = None,
                    note: str = "") -> dict:
    a = doc.setdefault("audition", {})
    a["run"] = bool(run)
    a["passed"] = passed
    a["note"] = (note or "").strip()
    return doc


def record_pressure_shot(doc: dict, idx: int, *, done: bool = True, result: str = "",
                         run_by: str = "") -> tuple[dict | None, str]:
    shots = doc.setdefault("pressure_test", {}).setdefault("shots", [])
    if idx < 0 or idx >= len(shots):
        return None, f"no pressure-test shot at index {idx}"
    shots[idx]["done"] = bool(done)
    shots[idx]["result"] = (result or "").strip()
    if run_by:
        doc["pressure_test"]["run_by"] = run_by.strip()
    return doc, ""


def attach_reference(doc: dict, library_id: str) -> dict:
    """Point the character at its signed-off `cast` library item — the frame every producer's
    cast-lock resolves to. The library holds the image; this store holds the pointer."""
    doc.setdefault("reference", {})["library_id"] = (library_id or "").strip()
    return doc


# --- what a producer reads -------------------------------------------------------------------

def cast_lock_block(doc: dict) -> str:
    """The paragraph a producer's cast-lock threads into an image/video prompt. Identity only — the
    scene, wardrobe-of-the-day and, always, the expression are the producer's to set per piece."""
    if not doc:
        return ""
    lines: list[str] = []
    name = doc.get("name") or "the brand character"
    lines.append(f"BRAND CHARACTER — {name} (recurring, {doc.get('brand', 'this brand')}-owned; "
                 f"same identity every render, never redrafted per piece).")
    hook = doc.get("hook", {})
    if hook.get("line"):
        lines.append(f"Signature hook (must be present and recognisable): {hook['line']}")
        if hook.get("detail"):
            lines.append(f"  {hook['detail']}")
    brief = doc.get("visual_brief", {})
    if brief.get("type_line"):
        lines.append(f"Type: {brief['type_line']}")
    if brief.get("look"):
        lines.append(f"Look: {brief['look']}")
    if brief.get("region") and brief.get("region_load_bearing"):
        lines.append(f"Region (load-bearing — name it concretely, never 'Indian'): {brief['region']}")
    lock = doc.get("cast_lock", {})
    if lock.get("never_changes"):
        lines.append("Never changes: " + "; ".join(lock["never_changes"]))
    if lock.get("changes_freely"):
        lines.append("Changes freely (do not lock these): " + "; ".join(lock["changes_freely"])
                     + "; and always mood and expression.")
    prompts = doc.get("prompt_craft", {}).get("base_prompts", [])
    if prompts and prompts[0].get("negative"):
        lines.append("Carry a negative every render, e.g.: " + prompts[0]["negative"])
    lines.append("Character, never testimonial: no first-person product claims, no implied endorsement.")
    return "\n".join(lines)


# --- drafting (the skill, applied) ----------------------------------------------------------

def _skill_text() -> str:
    f = os.path.join(_SKILL, "SKILL.md")
    return open(f, encoding="utf-8").read() if os.path.exists(f) else ""


_OUTPUT_CONTRACT = """
---
RETURN ONLY a JSON object with exactly these keys (no prose, no code fence):

{
  "name": "...",
  "segment": "...",
  "pen_portrait": {"identity": {"Age": "...", "Lives": "...", "Household": "...", "Role at home": "..."},
                   "background": "...", "day_in_life": "...", "head_goals": "...", "heart_goal": "...",
                   "challenge": "...", "context": "..."},
  "hook": {"line": "<one clause>", "detail": "...", "prop": "<or ''>", "prop_load_bearing": false,
           "routes_considered": [{"tag": "B", "line": "..."}, {"tag": "C", "line": "..."}],
           "route_selected": "A"},
  "visual_brief": {"type_line": "<energy/presence in one phrase>", "look": "...", "region": "...",
                   "region_load_bearing": true, "setting": "...", "light": "...", "texture": "...",
                   "expression_range": [{"expr": "Working neutral", "when": "Default."}]},
  "cast_lock": {"never_changes": ["..."], "changes_freely": ["..."]},
  "prompt_craft": {"base_prompts": [{"label": "...", "prompt": "<full, sensory, named light/lens/palette>",
                   "negative": "<the generic-default failures to exclude>"}]},
  "audition": {"spec": "<a 6s profile-centre-profile turn, framed as presenting for selection>",
               "negative": "<cuts, morphing, expression change mid-turn, ...>"},
  "per_producer": {"social": "...", "pos": "...", "video": "...",
                   "onground": "...", "pr": "..."},
  "open_items": [{"item": "...", "note": "why it needs validation", "weight": 1}]
}

The hook must be nameable in one clause and be this character's alone — not a demographic. Region is
load-bearing only when the brief is built for a specific regional market; name the real geography and
community, never a whole country. Every base prompt carries a negative. per_producer.onground and .pr
should say "does not apply" with the reason unless there is a genuine, non-testimonial use.
"""


def draft(brand: str, seed: str, *, segment: str = "", segment_source: str = "assumed",
          house: dict | None = None, brand_doc: dict | None = None) -> tuple[dict | None, str]:
    """Draft a full character document from a pen portrait or segment description, following the
    skill. Returns (doc, error). The result is a `draft`-state document — nothing about it is
    approved, and every test still reads pending."""
    if jsonout is None:
        return None, "generation is unavailable (jsonout did not import)"
    if not (seed or "").strip():
        return None, "a pen portrait or segment description is needed to draft from"

    parts = [_skill_text()]
    if brandprofile is not None:
        try:
            b = brand_doc or brandprofile.resolve(house, {"brand": brand})
            if b:
                parts.append("\n\n---\nTHE BRAND\n" + brandprofile.voice_block(b))
        except Exception:
            pass
    parts.append("\n\n---\nWHO THIS CHARACTER IS FOR\n" + seed.strip())
    if segment:
        parts.append(f"\nSegment: {segment}  [{segment_source}]")
    parts.append("\n\n---\nDraft one brand character for " + (brand or "this brand")
                 + ", following the skill above." + _OUTPUT_CONTRACT)

    data, err = jsonout.ask_json("\n".join(parts), max_tokens=4000)
    if err or not data:
        return None, err or "no draft returned"

    doc = new_doc(brand, data.get("name") or "", segment=segment or data.get("segment") or "",
                  segment_source=segment_source)
    for section in ("pen_portrait", "hook", "visual_brief", "cast_lock", "prompt_craft", "audition",
                    "per_producer"):
        val = data.get(section)
        if isinstance(val, dict):
            doc[section] = {**doc[section], **val}
    if isinstance(data.get("open_items"), list):
        doc["open_items"] = data["open_items"]
    doc["hook"].setdefault("route_confirmed", False)
    doc["state"] = derive_state(doc)
    return doc, ""
