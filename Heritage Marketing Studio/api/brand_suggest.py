"""brand_suggest.py -- the model drafts answers to the profile's nuance questions (NUANCE_LAYER_PLAN.md, Step 4).

The profile asks sixteen questions the prompts used to answer silently for one brand's category (how the
product is handled, who buys it, where it is met, how a place behaves). Typing them all is the cost of the
form, so the model drafts them and the person confirms. Three rules keep that honest:

  - **Nothing is stored here.** A draft is a suggestion, shown with Accept/Dismiss on the profile screen. A
    suggestion is never read by a prompt; only an answer a person accepted and saved is.
  - **A blank beats an invented specific.** The model is told to leave a value empty, and say what it would
    need, rather than guess. Figures, shares, names and sources are never to be made up.
  - **Every draft names its basis**: `profile` (stated or directly implied by the profile or the brief),
    `context` (text the person pasted in), or `knowledge` (the model's general knowledge, which the person
    must confirm).

The questions are drafted a group at a time, one model call per group, so each request stays well inside a
reverse proxy's timeout (a past 524 on a long brief) and one failure costs one group, not the lot.

Not suggested, on purpose: `trade_terms`. A trade figure needs a published source the studio can name, and a
model's memory of one is not good enough. It is entered by a person, or comes from web research later.
"""
from __future__ import annotations

import json
import re

import brandprofile as bp
import geo
import jsonout

NO_KEY = "no ANTHROPIC_API_KEY"

# One model call each. Place notes, the language mix and the dated moments share a call because they all lean
# on the same thing: where the brand sells.
GROUPS: list[dict] = [
    {"name": "How the product is shown", "keys": ("product_in_use", "must_show", "pack_in_scene", "imagery_style")},
    {"name": "Who buys it and where it is met", "keys": ("buying_unit", "lines", "routes", "meeting_points")},
    {"name": "Proof and marks", "keys": ("statutory_marks", "worst_case")},
    {"name": "Place, language and occasions", "keys": ("place_notes", "language_mix", "calendar_moments")},
    {"name": "Look and sound", "keys": ("people_setting", "sound_world")},
]
NOT_SUGGESTED = {"trade_terms": "A trade figure needs a published source the studio can name. Enter it yourself, "
                                "or wait for web research."}

# What each question is really after, in neutral terms. Deliberately no worked examples: the form's own
# placeholders span several categories, and an example in a prompt is an example the model copies.
HINT = {
    "product_in_use": "What people physically do with the product when they use it (pour, spread, apply, wear, install, eat...). "
                      "Say what is distinctive about the gesture, and what is never done with it.",
    "must_show": "What has to be visible in a photograph of the product for it to look real and right: the details an image "
                 "model leaves out unless it is told.",
    "pack_in_scene": "Whether a pack, bottle, bag, tag or label normally appears in advertising for this product.",
    "imagery_style": "The kind of imagery this category uses, as a creative director would brief it.",
    "buying_unit": "Whether the product is bought for a household or for one person. If it depends on the line or the buyer, say 'either'.",
    "lines": "The product lines of this brand that behave differently from each other (different buyers, different use, "
             "different place of sale). Only lines the profile or your solid knowledge of the brand's category supports.",
    "routes": "The routes by which the product reaches the buyer in this category and market. Never give a share of sales unless "
              "the profile states one: leave share_of_sales empty.",
    "meeting_points": "The physical places where people meet this brand or its category in person.",
    "statutory_marks": "The marks, licence numbers or declarations the regulator requires on the pack and in print for this "
                       "category and market. Leave empty unless you are sure.",
    "worst_case": "The worst public event this category can have (a recall, a failed test, an adverse reaction, a safety "
                  "incident) and who acts first. Say it in terms of this category's real regulator and risks.",
    "place_notes": "For each listed state: how people there buy and use this product, how they speak about it, the festivals and "
                   "seasons that matter to this category there, and local references that are safe to use. Never stereotype; "
                   "if you do not have something solid for a state, leave that row's cells empty.",
    "language_mix": "The language mix copy and voice-over should use for the states the brand sells in.",
    "calendar_moments": "Dated moments that matter to this category (a festival, a season, a sale, a launch window) and where "
                        "each matters. Only moments you are sure of.",
    "people_setting": "Who and where the work should show: the people, homes, sites or shops this brand's buyers actually live in.",
    "sound_world": "What the brand sounds like: the music, the voice accent, the pace.",
}


def _spec(key: str) -> dict:
    return bp.SPEC_BY_KEY[key]


def _one_line(v, n: int = 0) -> str:
    t = " ".join(str(v or "").split())
    return t[:n] if n else t


def pending_keys(b: dict, include_seeded: bool = False) -> list[str]:
    """Nuance questions this brand has not answered (and, unless asked, has no reviewed starting answer for)."""
    seeded = set() if include_seeded else set(bp.seed_answers(b))
    return [k for k in bp.NUANCE_KEYS if k not in NOT_SUGGESTED and not bp._has(b, k) and k not in seeded]


def _state_labels(b: dict) -> list[str]:
    return [geo.state_label(c) for c in (b.get("states") or []) if geo.resolve_state(c)]


def groups_view(b: dict | None) -> list[dict]:
    """The groups still worth asking for, each with the keys it would draft and any it cannot draft yet."""
    if not b:
        return []
    pend = set(pending_keys(b))
    out = []
    for g in GROUPS:
        keys, skipped = [], {}
        for k in g["keys"]:
            if k not in pend:
                continue
            if k == "place_notes" and not _state_labels(b):
                skipped[k] = "Say which states it sells in first (Geography and language)."
                continue
            keys.append(k)
        if keys or skipped:
            out.append({"name": g["name"], "keys": keys, "skipped": skipped})
    return out


def profile_text(b: dict) -> str:
    """What the brand has told the studio, as plain labelled lines (not the creative-facing instruction block)."""
    rows = []

    def add(label, v):
        t = ", ".join(_one_line(x) for x in v if _one_line(x)) if isinstance(v, list) else _one_line(v)
        if t:
            rows.append(f"{label}: {t}")

    add("Brand", b.get("name"))
    add("Category", b.get("category"))
    add("Market", b.get("market"))
    add("Hero product", b.get("hero_product"))
    add("Positioning", b.get("positioning"))
    add("States it sells in", _state_labels(b))
    add("Languages it can be written in (language codes)", list(b.get("languages") or []))
    add("Competitors", b.get("competitors"))
    add("Regulator", b.get("regulator"))
    add("Purchase cycle", b.get("purchase_cycle"))
    add("Who decides", b.get("decider"))
    add("Who pays", b.get("payer"))
    add("Who uses it", b.get("user"))
    add("Channels it is sold in", b.get("channels"))
    add("What it loses to", b.get("cheap_alternative"))
    add("Price tier", b.get("price_tier"))
    add("What the category competes on", b.get("category_axis"))
    add("Anything else", b.get("notes"))
    claims = [f"{_one_line(r.get('claim'))}" for r in (b.get("claims") or []) if _one_line(r.get("claim"))]
    add("Claims it makes", claims)
    answered = bp.nuance_lines(b)
    if answered:
        rows.append("ALREADY ANSWERED BY THE BRAND:\n" + "\n".join(answered))
    return "\n".join(rows)


def brief_text(b: dict) -> str:
    """The newest brief for this brand, as the few fields that say who the work is for."""
    try:
        import briefstore
        rows = briefstore.briefs(str(b.get("name") or ""))
        full = briefstore.load(rows[0]["id"]) if rows else None
        canon = (full or {}).get("canon") or {}
    except Exception:                                  # noqa: BLE001 -- context is optional; never fail a draft over it
        return ""
    out = []
    for k, label in (("background", "Background"), ("targetAudience", "Target audience"), ("consumerInsight", "Consumer insight"),
                     ("competition", "Competition")):
        v = canon.get(k)
        t = ", ".join(_one_line(x) for x in v) if isinstance(v, list) else _one_line(v)
        if t:
            out.append(f"{label}: {t[:600]}")
    return "\n".join(out)


def _format_of(key: str, states: list[str]) -> str:
    s = _spec(key)
    kind = s["kind"]
    if kind == "choice":
        return "one of: " + " | ".join(f'"{o}"' for o in s["options"]) + ' (or "" if you cannot tell)'
    if kind == "list":
        return "a JSON list of at most six short strings"
    if kind == "rows":
        cols = ", ".join(f'"{c}"' for c in s["cols"])
        extra = ""
        if key == "place_notes":
            extra = " One row per state, and the \"state\" cell must be exactly one of: " + "; ".join(states) + "."
        return f"a JSON list of at most six objects, each with exactly these keys: {cols}, every cell a short phrase.{extra}"
    return "a short text of at most two sentences"


def build_prompt(b: dict, keys: list[str], context: str = "", brief: str = "") -> str:
    states = _state_labels(b)
    qs = []
    for i, k in enumerate(keys, 1):
        qs.append(f'{i}. "{k}": {_spec(k)["ask"]}\n   What it is after: {HINT[k]}\n   Value format: {_format_of(k, states)}')
    parts = [
        "You are helping a marketing studio fill in a brand profile. The studio writes work for many brands, in different "
        "categories and countries. What it needs from this profile is the nuance of THIS brand: how its product is really "
        "used, who buys it, where it is met, and how the places it sells in behave.",
        "WHAT THE BRAND HAS ALREADY TOLD US\n" + (profile_text(b) or "(almost nothing yet)"),
    ]
    if brief:
        parts.append("THE LATEST BRIEF FOR THIS BRAND\n" + brief)
    if context.strip():
        parts.append("EXTRA CONTEXT FROM THE PERSON (research notes, pasted text)\n" + context.strip()[:4000])
    parts.append("QUESTIONS (answer only these)\n" + "\n".join(qs))
    parts.append(
        "RULES\n"
        "- Answer for this brand and its category, in the terms people in that category and place really use. Nothing generic, "
        "and nothing borrowed from another category.\n"
        "- If the profile does not let you know, and your general knowledge of the category and the place is not solid, leave "
        "the value empty and say in \"unknowns\" what you would need. A blank is useful; an invented specific is harmful.\n"
        "- Never invent figures, shares, percentages, names of people or sources.\n"
        "- A specific you are not sure of (a colour, a pack or product name, a registration or licence code, an outlet the brand may not have) "
        "does not belong in the value at all: leave it out and name it in \"unknowns\". Never state something in the value and "
        "then list the same thing as unknown.\n"
        "- Do not coin words or phrases in a local language. Use a local word only if you are certain of it and of its script; "
        "otherwise describe the register in English.\n"
        "- If the brand sells lines that behave differently (different buyers, a household versus one person), say so in "
        "\"lines\" and answer \"either\" for who it is bought for, rather than averaging them into one answer.\n"
        "- Keep every answer short and concrete. Say what is distinctive, not what is true of every product.\n"
        "- \"basis\" says where an answer came from: \"profile\" (the profile or the brief says it, or it follows directly from a "
        "stated fact; a plausible inference is NOT \"profile\"), \"context\" (from the extra context, only if there is any above), "
        "or \"knowledge\" (your general knowledge or an inference, which the owner must confirm).")
    parts.append(
        "OUTPUT: only a JSON object, no prose and no code fence:\n"
        '{"answers": {"<key>": {"value": <in the stated format>, "basis": "profile|context|knowledge", "unknowns": "<what you could not know, or empty>"}}}\n'
        "Include every key listed above, with an empty value where you do not know.")
    return "\n\n".join(parts)


def _clean_value(key: str, raw, states: list[str]):
    """Normalise one drafted value the way a save would store it; '' or [] when nothing usable is left."""
    s = _spec(key)
    kind = s["kind"]
    if kind == "choice":
        v = _one_line(raw).lower()
        return next((o for o in s["options"] if o.lower() == v), "")
    if kind == "list":
        items = raw if isinstance(raw, list) else bp._listify(raw)
        return [_one_line(x, 200) for x in items if _one_line(x)][:6]
    if kind == "rows":
        rows = bp._rows(raw if isinstance(raw, list) else [], s["cols"])[:6]
        rows = [{c: _one_line(r.get(c), 220) for c in s["cols"]} for r in rows]
        if key == "place_notes":
            keep = []
            allowed = {geo.resolve_state(x) for x in states} - {None, ""}
            for r in rows:
                code = geo.resolve_state(r.get("state", ""))
                # a row that names a state and says nothing about it is not an answer; the model's blank for a place is a blank
                if code and code in allowed and any(v for c, v in r.items() if c != "state"):
                    keep.append({**r, "state": geo.state_label(code)})
            rows = keep
        if key == "routes":
            rows = [r for r in rows if r.get("route")]
        return rows
    return _one_line(raw, 500)


def suggest_group(b: dict, group: str, context: str = "", include_seeded: bool = False) -> dict:
    """Draft one group. Returns {suggestions: {key: {value, basis, unknowns}}, unknown: {key: text}, skipped: {key: reason}, error}.

    Saves nothing. `include_seeded` is only for the calibration run, which asks even where a reviewed file exists.
    """
    g = next((x for x in GROUPS if x["name"] == group), None)
    if not g:
        return {"suggestions": {}, "unknown": {}, "skipped": {}, "error": f"unknown group {group!r}"}
    pend = set(pending_keys(b, include_seeded))
    states = _state_labels(b)
    skipped: dict = {}
    keys = []
    for k in g["keys"]:
        if k not in pend:
            continue
        if k == "place_notes" and not states:
            skipped[k] = "Say which states it sells in first."
            continue
        keys.append(k)
    if not keys:
        return {"suggestions": {}, "unknown": {}, "skipped": skipped, "error": ""}
    prompt = build_prompt(b, keys, context, brief_text(b))
    data, err = jsonout.ask_json(prompt, max_tokens=700 + 650 * len(keys))
    if data is None:
        return {"suggestions": {}, "unknown": {}, "skipped": skipped, "error": err or "no reply"}
    answers = data.get("answers") if isinstance(data.get("answers"), dict) else data
    out, unknown = {}, {}
    for k in keys:
        a = answers.get(k) if isinstance(answers, dict) else None
        if not isinstance(a, dict):
            continue
        val = _clean_value(k, a.get("value"), states)
        conflict = ""
        if k == "place_notes" and isinstance(val, list):
            # The real run once returned two rows for the same state, one of them describing another state. Which one is right
            # cannot be told, so neither is offered: a wrong place note is worse than a blank.
            seen = [r["state"] for r in val]
            dup = sorted({s for s in seen if seen.count(s) > 1})
            if dup:
                val = [r for r in val if r["state"] not in dup]
                conflict = "The model gave conflicting rows for " + ", ".join(dup) + ", so none is offered for it."
        basis = _one_line(a.get("basis")).lower()
        basis = basis if basis in ("profile", "context", "knowledge") else "knowledge"
        if basis == "context" and not context.strip():
            basis = "knowledge"        # the real run labelled drafts 'context' when nothing had been pasted; unconfirmed is the safe reading
        why = _one_line(a.get("unknowns"), 260)
        if conflict:
            why = (why + " " + conflict).strip()
        if val in ("", []):
            if why:
                unknown[k] = why
            continue
        out[k] = {"value": val, "basis": basis, "unknowns": why}
    return {"suggestions": out, "unknown": unknown, "skipped": skipped, "error": ""}
