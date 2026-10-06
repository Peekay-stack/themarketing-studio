"""provocation_gen.py -- writing a Provocation: the codes audit, the sparks, developing one, pushing it further, and the guardrail check.

Every function here returns `(result, error)` (or a plain result for the pure ones). Nothing is invented when the model is unavailable:
no key, a failed call or an unparseable reply is an honest error the screen shows, never a placeholder dressed as an answer.

How it differs from the studio's other generators (`ideas.py`, `strategy.py`), on purpose:

* The brand's **guardrails** go in (claims it may make, banned words, regulator, never-do list, mandatories). The brand's **tone** does
  NOT: a provocation exists to depart from how the category -- and by default the brand -- sounds, so the voice block is built with the
  tone left out.
* The **competitor evidence** the person gave goes in verbatim, and every code comes back tagged `seen` or `memory`. The tag is checked
  here, not trusted: a code claiming to be `seen` must cite a competitor and channel the person actually provided, or it is downgraded
  to `memory`. The caveat the screen shows is computed here from those tags, never written by the model.
* Competitors are named only in the audit's `seen_in` (internal). The sparks and the provocation must not name a rival; the
  guardrail check enforces it.

The model call is `jsonout.ask_json`, called through `_ask` so a test can replace it.
"""
from __future__ import annotations

import os
import re

import brandprofile
import ideas
import jsonout
import provocation as pv

_SKILL = os.path.join(os.path.dirname(__file__), "provocation_skill")

CODE_KINDS = ("verbal", "visual", "tonal", "structural", "sonic")
NO_KEY = "No ANTHROPIC_API_KEY on the server, so a provocation cannot be drafted here. Nothing is made up in its place."

# The expressions a provocation is asked for (the mediums a producer stands on it for), in the order a screen shows them.
EXPRESSION_KINDS = ("video", "social", "posm", "activation", "pr")


def _skill_text() -> str:
    try:
        with open(os.path.join(_SKILL, "SKILL.md"), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _ask(prompt: str, max_tokens: int) -> tuple[dict | None, str]:
    """The one place the model is called (replaced in tests)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, NO_KEY
    return jsonout.ask_json(prompt, max_tokens=max_tokens)


def _s(x, n: int) -> str:
    return " ".join(x.split())[:n] if isinstance(x, str) else ""


# ---- the context every call is given ------------------------------------------------------------------------

def _profile(house: dict | None, pset: dict | None) -> dict | None:
    try:
        return brandprofile.resolve(house, pset)
    except Exception:                                             # noqa: BLE001 -- a missing profile is a normal state
        return None


def competitor_names(profile: dict | None, ev: dict | None) -> list[str]:
    """Every competitor the studio knows by name: the brand profile's list plus the ones the person gave evidence for."""
    seen, out = set(), []
    for n in list((profile or {}).get("competitors") or []) + [c["name"] for c in (ev or {}).get("competitors", [])]:
        n = _s(str(n), 80)
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out


def _evidence_block(ev: dict, names: list[str]) -> str:
    comps = ev.get("competitors") or []
    given = [c for c in comps if any((c["channels"][k].get("note") or c["channels"][k].get("link")) for k in pv.CHANNELS)]
    if not given:
        return ("COMPETITOR EVIDENCE: none provided. Competitor names on file: " + (", ".join(names) or "none") + ". "
                "Everything you say about the category comes from general knowledge, so every code you propose must be tagged "
                "basis \"memory\".")
    lines = ["COMPETITOR EVIDENCE (what the person provided; a code may be tagged basis \"seen\" only when it rests on one of these):"]
    for c in given:
        lines.append(f"- {c['name']}")
        for k in pv.CHANNELS:
            slot = c["channels"][k]
            if slot.get("note") or slot.get("link"):
                lines.append(f"    {pv.CHANNEL_LABELS[k]}: {slot.get('note') or '(link only, you cannot open it)'}"
                             + (f"  [link: {slot['link']}]" if slot.get("link") else ""))
    rest = [n for n in names if n.lower() not in {c['name'].lower() for c in given}]
    if rest:
        lines.append("Other competitors on file, with NO evidence provided (memory only): " + ", ".join(rest))
    return "\n".join(lines)


def _context(house: dict | None, pset: dict | None, platform: dict | None, ev: dict, steer: str = "") -> tuple[str, dict | None, list[str]]:
    prof = _profile(house, pset)
    names = competitor_names(prof, ev)
    basis = ideas.house_basis(house)
    voice = brandprofile.voice_block({**prof, "tone": ""}) if prof else brandprofile.voice_block(None)
    out = ["THE BRAND (its guardrails apply in full; its usual tone is deliberately left out, because a provocation departs from it)",
           voice, "", "THE MESSAGING HOUSE",
           "Core message: " + ("; ".join(basis["core"]) or "(none chosen)"),
           f"Emotional pillar: {basis['emotional'] or '(none chosen)'}",
           f"Functional pillar: {basis['functional'] or '(none chosen)'}"]
    if basis["codes"]:
        out.append("The brand's own cultural codes: " + "; ".join(f"{c['text']} ({c['tag']})" for c in basis["codes"]))
    if basis["avoid"]:
        out.append("MUST NOT DO:\n" + "\n".join(f"  - {a}" for a in basis["avoid"]))
    out += ["", "THE IDEA PLATFORM THIS IS BUILT ON (the provocation may break how it is expressed, never what it says)"]
    if platform:
        out.append(f"Name: {platform.get('name', '')}\nIdea: {platform.get('idea', '')}\nMechanic: {platform.get('mechanic', '')}")
        for k, v in (platform.get("expressions") or {}).items():
            if str(v or "").strip():
                out.append(f"  as {k}: {v}")
    out += ["", _evidence_block(ev, names)]
    if _s(steer, 600):
        out += ["", "THE PERSON ADDS (something they want to push against): " + _s(steer, 600)]
    return "\n".join(out), prof, names


# ---- the caveat (computed, never the model's) ---------------------------------------------------------------

def caveat_for(codes: list[dict], strength: dict) -> dict:
    """What the screen says about how much to trust a codes audit, from the tags the codes actually carry."""
    total = len(codes)
    seen = sum(1 for c in codes if c.get("basis") == "seen")
    memory = total - seen
    if not total:
        text = ""
    elif seen == 0:
        text = ("These codes come from the model's general knowledge of the category and the competitor names on file, not from "
                "anything you have shown it. Treat them as hypotheses.")
    elif memory:
        text = f"{seen} of {total} codes rest on what you gave it; the other {memory} are from the model's memory and unverified."
    else:
        text = "Every code rests on what you gave it. Check them against what you know."
    invite = ("Add what you have seen -- a pack, an Instagram page, a social video, POSM or a TVC -- for 3 or 4 competitors to ground "
              "these and sharpen the break." if seen < total else "")
    return {"text": text, "invite": invite, "seen": seen, "memory": memory, "total": total,
            "evidence": {"competitors": strength["competitors"], "slots_filled": strength["slots_filled"], "slots_total": strength["slots_total"]}}


def _clean_codes(raw, ev: dict) -> list[dict]:
    """The model's codes, made safe, with the `seen` tag checked against the evidence the person actually gave."""
    allowed: dict[str, set[str]] = {}
    for c in ev.get("competitors", []):
        allowed[c["name"].lower()] = {k for k in pv.CHANNELS if c["channels"][k].get("note") or c["channels"][k].get("link")}
    out = []
    for it in (raw if isinstance(raw, list) else [])[:20]:
        if not isinstance(it, dict):
            continue
        code = _s(it.get("code"), 240)
        if not code:
            continue
        kind = _s(it.get("kind"), 20).lower()
        refs = []
        for r in (it.get("seen_in") if isinstance(it.get("seen_in"), list) else [])[:6]:
            r = _s(r, 120)
            low = r.lower()
            for name, chans in allowed.items():
                if name in low and any(pv.CHANNEL_LABELS[k].lower() in low or k.replace("_", " ") in low for k in chans):
                    refs.append(r)
                    break
        basis = "seen" if (_s(it.get("basis"), 10).lower() == "seen" and refs) else "memory"
        out.append({"kind": kind if kind in CODE_KINDS else "visual", "code": code, "how": _s(it.get("how"), 300),
                    "basis": basis, "seen_in": refs if basis == "seen" else []})
    return out


# ---- 1. the category's codes --------------------------------------------------------------------------------

def audit_codes(house: dict | None, pset: dict | None, platform: dict | None, ev: dict, steer: str = "") -> tuple[dict | None, str]:
    ctx, prof, names = _context(house, pset, platform, ev, steer)
    prompt = (_skill_text() + "\n\n---\n" + ctx + "\n\n---\nTASK: THE CATEGORY'S CODES\n"
              "Name the codes this category repeats, five kinds (verbal, visual, tonal, structural, sonic), at least one of each where it "
              "exists, 10 to 16 in all. A code must be really shared by several brands and breakable without losing anything true to "
              "the brand. For each give: kind, code (one specific sentence), how (how it shows up), basis (\"seen\" or \"memory\"), "
              "seen_in (a list of strings like \"<competitor> <channel>\" naming ONLY competitors and channels listed in the evidence "
              "above; empty for memory).\n"
              'Return ONLY: {"category": "the category as you understand it, a few words", "codes": [{"kind": "", "code": "", "how": "", '
              '"basis": "", "seen_in": []}]}')
    data, err = _ask(prompt, 3500)
    if data is None:
        return None, err
    codes = _clean_codes(data.get("codes"), ev)
    if not codes:
        return None, "The model did not return any usable codes. Try again, or add what you have seen of the category's competitors."
    strength = pv.evidence_strength(ev)
    return {"category": _s(data.get("category"), 120), "codes": codes, "caveat": caveat_for(codes, strength), "competitors": names}, ""


# ---- 2. sparks ----------------------------------------------------------------------------------------------

def _score(x) -> int:
    return int(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and 1 <= x <= 5 else 3


def spark(house: dict | None, pset: dict | None, platform: dict | None, ev: dict, codes: list[str], steer: str = "", n: int = 8) -> tuple[dict | None, str]:
    codes = [c for c in (_s(c, 240) for c in (codes if isinstance(codes, list) else [])) if c][:8]
    if not codes:
        return None, "Pick at least one code to break first."
    ctx, prof, names = _context(house, pset, platform, ev, steer)
    n = max(3, min(12, int(n or 8)))
    prompt = (_skill_text() + "\n\n---\n" + ctx + "\n\n---\nCODES THE PERSON WANTS TO BREAK\n" + "\n".join(f"  - {c}" for c in codes) +
              f"\n\n---\nTASK: {n} SPARKS\nGive {n} different sparks. Each is one specific idea in a sentence or two that breaks at least "
              "one of those codes and says what stays true to the idea platform. Spread them: some break one code gently, some break "
              "several, at least one changes who or what is on screen. Never name a competitor. For each give: text, codes (the codes it "
              "breaks, copied from the list above), stays_true (one short line), scores (integers 1 to 5: breaks = how clearly it breaks a "
              "code, true = how true to the platform, travels = how well it works across other mediums), risk (low, medium or high).\n"
              'Return ONLY: {"sparks": [{"text": "", "codes": [], "stays_true": "", "scores": {"breaks": 3, "true": 3, "travels": 3}, "risk": ""}]}')
    data, err = _ask(prompt, 4500)
    if data is None:
        return None, err
    out = []
    for it in (data.get("sparks") if isinstance(data.get("sparks"), list) else [])[:30]:
        if len(out) >= n:
            break                                  # clean first, then cap: a junk entry must not cost a real spark its place
        if not isinstance(it, dict) or not _s(it.get("text"), 600):
            continue
        sc = it.get("scores") if isinstance(it.get("scores"), dict) else {}
        risk = _s(it.get("risk"), 10).lower()
        scores = {"breaks": _score(sc.get("breaks")), "true": _score(sc.get("true")), "travels": _score(sc.get("travels"))}
        out.append({"text": _s(it.get("text"), 600), "codes": [c for c in (_s(c, 240) for c in (it.get("codes") if isinstance(it.get("codes"), list) else [])[:6]) if c],
                    "stays_true": _s(it.get("stays_true"), 240), "scores": scores, "total": sum(scores.values()),
                    "risk": risk if risk in pv.RISKS else "medium"})
    if not out:
        return None, "The model did not return any usable sparks. Try again."
    out.sort(key=lambda s: s["total"], reverse=True)
    return {"sparks": out}, ""


# ---- 3. develop one / push it further -----------------------------------------------------------------------

_RECORD_SHAPE = (
    '{"name": "", "core": {"line": "", "codes_broken": [], "stance": {"tone": "", "humour": "", "structure": ""}, "risk": "low|medium|high", '
    '"risk_note": "", "safer_version": "", "legal_flag": false, "legal_note": ""}, '
    '"expressions": {"video": "", "social": "", "posm": "", "activation": "", "pr": ""}, '
    '"film": {"structure": "", "humour": "", "visual_language": "", "sound_language": "", "cast_approach": "people|objects|animated|none", '
    '"vo_words": 0, "brand_beat": "", "notes": ""}}')


def _record_from(data: dict, house: dict | None, platform: dict | None, codes: list[str], spark_text: str, house_id: str) -> dict:
    data = data if isinstance(data, dict) else {}
    core = data.get("core") if isinstance(data.get("core"), dict) else {}
    expr = data.get("expressions") if isinstance(data.get("expressions"), dict) else {}
    rec = {"name": data.get("name"), "core": {**core, "legal_ack": False}, "film": data.get("film"),
           "expressions": {k: expr.get(k) for k in EXPRESSION_KINDS},
           "source": {"codes_audit": codes, "sparks": [{"text": spark_text, "score": None}] if spark_text else []},
           "platform": (platform or {}).get("id", ""), "house": house_id}
    # The codes the person chose to break are kept word for word: the screen matches them to the audit by text, and a model's
    # rewording (it also copied the audit's "(memory)" tag onto the end of them) broke that match.
    if codes:
        rec["core"]["codes_broken"] = codes
    else:
        rec["core"]["codes_broken"] = [re.sub(r"\s*\((?:memory|seen)\)\s*$", "", str(c), flags=re.I) for c in (rec["core"].get("codes_broken") or [])]
    return pv.apply_edit(None, rec, house, platform)


def develop(house: dict | None, pset: dict | None, platform: dict | None, ev: dict, spark_in: dict, codes: list[str], steer: str = "") -> tuple[dict | None, str]:
    text = _s((spark_in or {}).get("text"), 600) if isinstance(spark_in, dict) else ""
    if not text:
        return None, "Pick a spark to develop."
    ctx, prof, names = _context(house, pset, platform, ev, steer)
    prompt = (_skill_text() + "\n\n---\n" + ctx + "\n\n---\nTHE SPARK TO DEVELOP\n" + text +
              ("\nCodes it breaks: " + "; ".join(_s(c, 240) for c in (spark_in.get("codes") or [])) if isinstance(spark_in, dict) and spark_in.get("codes") else "") +
              "\n\n---\nTASK: DEVELOP IT\nDevelop this spark into a provocation. Honour the hard limits and the brand's guardrails. Never name a competitor. "
              "Set legal_flag true only if the work jabs at the category's rivals, and say why in legal_note. Give an honest risk and why. "
              "The safer_version keeps the idea but keeps more of the category's comfort. expressions: one clear line per medium, saying what "
              "it becomes there. film.vo_words is the voiceover length in words (0 for none).\nReturn ONLY the JSON object: " + _RECORD_SHAPE)
    data, err = _ask(prompt, 3800)
    if data is None:
        return None, err
    rec = _record_from(data, house, platform, [c for c in (_s(c, 240) for c in (codes or [])) if c], text, (house or {}).get("id", ""))
    if not rec["core"]["line"]:
        return None, "The model did not write the provocation itself. Try again."
    return rec, ""


def push_further(rec: dict, house: dict | None, pset: dict | None, platform: dict | None, ev: dict, direction: str = "") -> tuple[dict | None, str]:
    rec = pv.normalise(rec)
    if not rec["core"]["line"]:
        return None, "There is nothing to push yet: write the provocation first."
    ctx, prof, names = _context(house, pset, platform, ev, "")
    prompt = (_skill_text() + "\n\n---\n" + ctx + "\n\n---\nTHE PROVOCATION SO FAR\nName: " + rec["name"] + "\nLine: " + rec["core"]["line"] +
              "\nCodes it breaks: " + "; ".join(rec["core"]["codes_broken"]) + "\nStance: " + "; ".join(v for v in rec["core"]["stance"].values() if v) +
              "\nFilm: " + "; ".join(v for k, v in rec["film"].items() if isinstance(v, str) and v) +
              "\n\n---\nTASK: PUSH IT FURTHER\nMake the break bolder" + (f", in this direction: {_s(direction, 300)}" if _s(direction, 300) else "") +
              ". Keep every hard limit, the brand's guardrails and the idea platform's truth. Never name a competitor. Keep the same JSON shape and "
              "fill every field again for the bolder version. Return ONLY the JSON object: " + _RECORD_SHAPE)
    data, err = _ask(prompt, 3800)
    if data is None:
        return None, err
    pushed = _record_from(data, house, platform, rec["core"]["codes_broken"], "", rec["house"] or (house or {}).get("id", ""))
    if not pushed["core"]["line"]:
        return None, "The model did not write the bolder version. Try again."
    # What was being pushed becomes the safer version, so the person never loses it.
    pushed["core"]["safer_version"] = _s(rec["core"]["line"], 800)
    pushed["id"], pushed["created"] = rec["id"], rec["created"]
    pushed["source"] = rec["source"]
    return pushed, ""


# ---- 4. the guardrail check (no model; what a machine can honestly check) ---------------------------------------

_HEALTH = [r"\bcure[sd]?\b", r"\btreat(?:s|ed|ing|ment)?\s+(?:of\s+|for\s+)?(?:\w+\s+){0,2}(?:disease|illness|condition|symptom|infection|ailment)s?\b", r"\bprevent(?:s|ed|ion)?\b", r"\bheal(?:s|ed|ing)?\b", r"\bimmun(?:e|ity)\b",
           r"\bclinically\b", r"\bdoctors?\b", r"\bmedicin\w*\b", r"\bdiabet\w*\b", r"\bcancer\b", r"\bweight loss\b", r"\blose weight\b",
           r"\bstrong bones\b", r"\bbuilds? bones\b", r"\bboosts?\b"]
_FIGURE = re.compile(r"\d+\s*%|\b\d+\s*x\b|\bclinically proven\b|\bproven\b", re.I)


def _text_of(rec: dict) -> str:
    c = rec["core"]
    parts = [rec["name"], c["line"], c["safer_version"], *c["stance"].values(), *rec["expressions"].values(),
             *(v for v in rec["film"].values() if isinstance(v, str))]
    return " \n".join(p for p in parts if p)


def check_guardrails(rec: dict, profile: dict | None, names: list[str]) -> list[dict]:
    """What a machine can honestly say about a provocation against the house's rules. `fail` blocks approval; `warn` asks for a look;
    `manual` is what only a person can judge (likeness, food, children, religion) and is always listed."""
    rec = pv.normalise(rec)
    text = _text_of(rec)
    low = text.lower()
    out = []

    def word_in(w: str) -> bool:
        w = str(w or "").strip()
        return bool(w) and re.search(r"(?<![A-Za-z0-9])" + re.escape(w) + r"(?![A-Za-z0-9])", text, re.I) is not None

    banned = [w for w in ((profile or {}).get("banned_words") or []) if word_in(w)]
    out.append({"id": "banned", "level": "fail" if banned else "pass",
                "text": ("Uses words the house may not use: " + ", ".join(banned)) if banned else "No banned words from the house."})
    rivals = [n for n in names if word_in(n)]
    out.append({"id": "rivals", "level": "fail" if rivals else "pass",
                "text": ("Names a competitor (" + ", ".join(rivals) + "). Competitors may only appear as an archetype.") if rivals else "No named competitor."})
    health = sorted({m.group(0).lower() for p in _HEALTH for m in re.finditer(p, low)})
    out.append({"id": "health", "level": "warn" if health else "pass",
                "text": ("Reads like a health claim (" + ", ".join(health) + "). Health claims are not allowed.") if health else "No health-claim wording found."})
    fig = bool(_FIGURE.search(text))
    out.append({"id": "figures", "level": "warn" if fig else "pass",
                "text": "Contains a figure or a 'proven' claim. It needs proof on the house's approved claims list." if fig else "No figures or proof claims."})
    avoid = [a for a in ((profile or {}).get("avoid") or []) if str(a).strip() and 0 < len(str(a).split()) <= 4 and str(a).lower() in low]
    out.append({"id": "never", "level": "fail" if avoid else "pass",
                "text": ("Does something the house says never to do: " + "; ".join(avoid)) if avoid else "Nothing on the house's never-do list was found."})
    if rec["core"]["legal_flag"]:
        out.append({"id": "legal", "level": "pass" if rec["core"]["legal_ack"] else "warn",
                    "text": "Jabs at competitors. A human legal review is flagged." + ("" if rec["core"]["legal_ack"] else " Tick that it is going to legal before approving.")})
    out.append({"id": "manual", "level": "manual",
                "text": "Check by eye: no real person's likeness, nothing that offends on food, children or religion"
                        + ((", and the house's never-do list: " + "; ".join(str(a) for a in ((profile or {}).get("avoid") or [])[:6])) if (profile or {}).get("avoid") else "") + "."})
    return out


def has_failures(checks: list[dict]) -> list[str]:
    return [c["text"] for c in checks if c["level"] == "fail"]
