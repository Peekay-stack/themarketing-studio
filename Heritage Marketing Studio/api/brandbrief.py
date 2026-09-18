"""brandbrief.py — turn the Brand Brief Builder payload into the skill's .docx.

Flow: builder payload -> NeedScope wheel PNG (from placed pins) + CB/CA->DB/DA PNG
(from the four quadrants) -> brief.json in the skill's schema -> build_brief_docx.js -> .docx.

Runs the comprehensive-brand-brief skill's own assets, bundled under brief_assets/.
Requires: cairosvg (pip), node + docx (installed in brief_assets/), and the figure templates.
"""
from __future__ import annotations

import html
import json
import math
import os
import subprocess
import tempfile

import jsonout

_HERE = os.path.dirname(__file__)
_ASSETS = os.path.join(_HERE, "brief_assets")
TERR_ANGLE = {"Power": 270, "Freedom": 330, "Vitality": 30, "Belonging": 90, "Security": 150, "Discernment": 210}


def _esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def _wrap(text: str, width: int = 34, maxlines: int = 6) -> list[str]:
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return (lines + [""] * maxlines)[:maxlines]


def _bullets_to_lines(bullets: list[str], maxlines: int = 6) -> list[str]:
    out: list[str] = []
    for b in bullets:
        out += _wrap(b, 34, 2)
    return (out + [""] * maxlines)[:maxlines]


def build_needscope_png(payload: dict, out_png: str):
    import cairosvg
    ns = payload.get("needscope", {})
    svg = open(os.path.join(_ASSETS, "needscope_template.svg")).read()
    pins_svg, anchor = [], None
    for p in ns.get("pins", []):
        x, y, name, isA = p["x"], p["y"], p["brand"], p.get("anchor")
        if isA:
            anchor = p
        col = "#14331F" if isA else "#777777"
        r = 11 if isA else 7
        pins_svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}" stroke="#fff" stroke-width="2"/>')
        dy = -15 if y < 320 else 22
        lbl = _esc(name) + (" (anchor)" if isA else "")
        pins_svg.append(f'<text x="{x}" y="{y+dy}" text-anchor="middle" font-size="12" font-weight="{700 if isA else 600}" fill="#222">{lbl}</text>')
    bridge = ""
    bt = ns.get("bridge_territory")
    if bt and anchor:
        t = math.radians(TERR_ANGLE[bt]); tx, ty = 400 + 120 * math.cos(t), 320 + 120 * math.sin(t)
        mx, my = (anchor["x"] + tx) / 2, (anchor["y"] + ty) / 2
        bridge = (f'<path d="M {anchor["x"]},{anchor["y"]} Q {mx},{my+25} {tx:.0f},{ty:.0f}" fill="none" '
                  f'stroke="#3F814C" stroke-width="2.5" stroke-dasharray="7 5" marker-end="url(#arr)"/>'
                  f'<text x="{mx:.0f}" y="{my+44:.0f}" text-anchor="middle" font-size="12" font-weight="700" fill="#3F814C">"{_esc(ns.get("bridge_label",""))}"</text>'
                  f'<text x="{mx:.0f}" y="{my+60:.0f}" text-anchor="middle" font-size="10" fill="#3F814C">strategic bridge</text>')
    svg = svg.replace("<!-- BRAND_PINS_INSERTION_POINT -->", "\n".join(pins_svg))
    svg = svg.replace("<!-- STRATEGIC_BRIDGE_INSERTION_POINT -->", bridge)
    svg = svg.replace("{{CATEGORY_LABEL}}", _esc(payload.get("category", "")))
    cairosvg.svg2png(bytestring=svg.encode(), write_to=out_png, output_width=1800)


def build_cbca_png(payload: dict, out_png: str):
    import cairosvg
    c = payload.get("cb_ca_db_da", {})
    svg = open(os.path.join(_ASSETS, "cbca_dbda_template.svg")).read()
    cb = _bullets_to_lines(c.get("cb", []))
    db = _bullets_to_lines(c.get("db", []))
    caq = _wrap(c.get("ca_quote", ""), 28, 3)
    daq = _wrap(c.get("da_quote", ""), 28, 3)
    cad = (c.get("ca_declarative", []) + ["", ""])[:2]
    dad = (c.get("da_declarative", []) + ["", ""])[:2]
    rep = {}
    for i in range(6):
        rep[f"CB_LINE_{i+1}"] = cb[i]; rep[f"DB_LINE_{i+1}"] = db[i]
    for i in range(3):
        rep[f"CA_QUOTE_{i+1}"] = caq[i]; rep[f"DA_QUOTE_{i+1}"] = daq[i]
    for i in range(2):
        rep[f"CA_DECLARATIVE_{i+1}"] = cad[i]; rep[f"DA_DECLARATIVE_{i+1}"] = dad[i]
    rep["SHIFT_FROM"] = c.get("shift_from", ""); rep["SHIFT_TO"] = c.get("shift_to", "")
    rep["CAPTION"] = c.get("caption", "")
    for k, v in rep.items():
        svg = svg.replace("{{" + k + "}}", _esc(v))
    cairosvg.svg2png(bytestring=svg.encode(), write_to=out_png, output_width=1800)


def _snapshots(payload: dict) -> dict:
    """Pricing, distribution and content — from what was actually supplied, or an honest absence.

    Each of these is filled from the uploaded market data when there is some. When there is not, it says
    so and names what to upload, rather than printing a sentence that reads like a finding.
    """
    md = payload.get("market_data") or payload.get("marketData") or ""
    hd = payload.get("household_data") or payload.get("householdData") or ""
    has_market = bool(str(md).strip())
    has_house = bool(str(hd).strip())
    return {
        "pricing": (str(payload.get("pricing_note") or "").strip()
                    or ("Per the uploaded market data — validate against the latest reads."
                        if has_market else
                        "NOT SUPPLIED. No market data was uploaded, so there is no pricing read here. "
                        "Attach a price/market-share file to the brief and regenerate.")),
        "distribution": (str(payload.get("distribution_note") or "").strip()
                         or ("Per the supplied data and category context."
                             if has_market or has_house else
                             "NOT SUPPLIED. No distribution or household data was uploaded, so this is "
                             "empty rather than estimated.")),
        "content_campaigns": (str(payload.get("content_note") or "").strip()
                              or "NOT ASSESSED. No campaign audit was supplied with this brief."),
        "content_gaps": (str(payload.get("gaps_note") or "").strip()
                         or "NOT ASSESSED. Content whitespace needs a competitor content audit, which "
                            "was not part of this brief."),
    }


def _backgrounder_defaults(payload: dict) -> dict:
    """Deterministic fallback for the backgrounder — same honesty pattern as _snapshots(): a real
    figure where the data was supplied, an explicit "not supplied" where it wasn't, never a guess.
    `enrich_with_ai()` can fill/sharpen this later; `draft_brief()` may already have filled it if the
    brief went through AI drafting — either way this only fills gaps, never overwrites what's there.
    """
    bg = payload.get("backgrounder") or {}
    md = payload.get("market_data") or payload.get("marketData") or ""
    hd = payload.get("household_data") or payload.get("householdData") or ""
    has_data = bool(str(md).strip()) or bool(str(hd).strip())
    return {
        "category_perspective": str(bg.get("category_perspective") or "").strip()
                                or "NOT ASSESSED. No category-level data was supplied.",
        "current_situation": str(bg.get("current_situation") or "").strip()
                             or ("Per the supplied data — validate against the latest reads." if has_data
                                 else "NOT SUPPLIED. No market-share or household data was uploaded, so "
                                      "there is no current-situation read here."),
        "consumer_insights": bg.get("consumer_insights") or [],
        "problem_statement": str(bg.get("problem_statement") or "").strip()
                             or "NOT DEFINED. Draft with AI, or write directly in the builder.",
    }


def _focal_profile(payload: dict) -> dict:
    """What the focal brand's own column should say, from its profile rather than hardcoded.

    The matrix used to state "Purity-led strength" for whatever brand it was building — dairy language
    left in place when the studio became multi-category. Anything the profile does not hold comes back
    empty and prints as "not stated", which is the honest cell.

    Deliberately `by_name` only, never `resolve()`. `resolve()` exists for GROUNDING and falls back to
    whichever brand is active when the name matches nothing — right for "what should the model assume",
    catastrophic here: a brief for a brand with no profile yet would silently print the ACTIVE brand's
    positioning and hero product as if they belonged to the one being briefed. A brand-new brand with no
    profile has nothing here yet, and "not stated" is the honest cell for that, not another brand's data.
    """
    try:
        import brandprofile
        b = brandprofile.by_name(str(payload.get("brand") or "")) or {}
    except Exception:
        b = {}
    return {"positioning": b.get("positioning", ""), "hero_product": b.get("hero_product", ""),
            "category_axis": b.get("category_axis", ""), "recent_moves": ""}


def to_skill_brief(payload: dict, ns_png: str, cbca_png: str) -> dict:
    """Map the builder payload to the skill's brief.json schema, synthesising the
    narrative sections the builder doesn't capture from the structured inputs."""
    brand = payload.get("brand", "Brand")
    comps = payload.get("competitors", [])
    smp = payload.get("smp", "")
    shift = payload.get("cb_ca_db_da", {}).get("shift_line", "")
    bridge = payload.get("needscope", {}).get("bridge_territory", "")
    prompt = (payload.get("prompt") or "").strip()
    exec_summary = [
        f"{brand} is positioned on the NeedScope wheel from the inputs supplied, with the focal "
        f"brand anchored and a strategic bridge into {bridge or 'an adjacent territory'}. "
        f"The competitive set comprises {', '.join(c['name'] for c in comps) or 'the named competitors'}.",
        f"The strategic shift is {shift or 'defined in the CB/CA → DB/DA section'}. The Single Minded "
        f"Proposition that follows is: {smp}",
    ]
    if prompt:
        exec_summary.insert(0, f"Brief ask: {prompt}")
    # The comparison matrix, built from the fields that exist rather than from whichever was nearest.
    #
    # It used to fill "Target buyer" with each competitor's HERO BRANDS, give "Tagline" and "Key
    # differentiator" the SAME `positioning` value, hardcode the focal column as "Focal audience" /
    # "Purity-led strength" / "—", and truncate every cell to 24 characters. The result was the most
    # looked-at table in the brief saying nothing — and the hardcoded strings were dairy language sitting
    # in a product now sold to any category.
    #
    # Each row reads one field, once. A row with no data behind it says so, because an empty cell in a
    # comparison invites the reader to fill it in themselves.
    ns = payload.get("needscope", {}) or {}
    prof = _focal_profile(payload)
    dims, cells = [], []

    def row(label, focal, getter):
        vals = [str(getter(c) or "").strip() for c in comps]
        if not str(focal or "").strip() and not any(vals):
            return
        dims.append(label)
        cells.append([str(focal or "not stated").strip()]
                     + [v or "not stated" for v in vals])

    row("Positioning, in one line", prof.get("positioning") or ns.get("bridge_label", ""),
        lambda c: c.get("positioning"))
    row("Hero brands / range", prof.get("hero_product", ""), lambda c: c.get("hero_brands"))
    row("What it competes on", prof.get("category_axis", ""), lambda c: c.get("competes_on"))
    row("Recent moves", prof.get("recent_moves", ""), lambda c: c.get("recent_moves"))
    brands = [brand] + [c["name"] for c in comps]
    return {
        "brand": brand,
        "prepared_for": payload.get("prepared_for", ""),
        "date": payload.get("date", ""),
        "sources_note": payload.get("sources_note", ""),
        "executive_summary": exec_summary,
        "backgrounder": _backgrounder_defaults(payload),
        "smp": smp,
        "competitors": comps,
        "messaging_matrix": {"dimensions": dims, "brands": brands, "cells": cells},
        "needscope": {
            "figure_path": ns_png,
            "reading": payload.get("needscope", {}).get("reading", ""),
            "strategic_implication": (
                f"Defend the anchor territory by activating it, and extend one disciplined thread into "
                f"{bridge or 'the bridge territory'} via the \"{payload.get('needscope',{}).get('bridge_label','')}\" "
                f"platform. No competitor on this wheel can credibly occupy that bridge."
            ),
        },
        "cb_ca_db_da": {
            "figure_path": cbca_png,
            "shift_line": shift,
            "caption": payload.get("cb_ca_db_da", {}).get("caption", ""),
        },
        "smp_defence": payload.get("smp_defence", []),
        "smp_unlocks": payload.get("smp_unlocks", {}),
        # Section 7 used to print four sentences shaped like content and containing none — "Pricing
        # landscape per uploaded market data" when no market data had been uploaded. A sentence that
        # says nothing is worse than a blank, because the reader has to work out that it is empty.
        "snapshots": _snapshots(payload),
        "opportunities_threats": [
            {"opportunity": f"Own the '{payload.get('needscope',{}).get('bridge_label','')}' bridge first",
             "threat": "Larger competitors expanding into the focal brand's strongholds"},
        ],
        "recommendations": {
            "preface": f"All actions ladder to the SMP — {smp} — and respect the NeedScope discipline.",
            "quick_wins": [
                f"Codify '{payload.get('needscope',{}).get('bridge_label','')}' as the single brand platform.",
                "Audit quick-commerce and metro availability within 60 days.",
                "Launch a hero film that dramatises the desired attitude.",
            ],
            "strategic_moves": [
                payload.get("smp_unlocks", {}).get("product", "Develop a product/pricing move that productises the SMP."),
                payload.get("smp_unlocks", {}).get("activation", "Build an activation platform that lives the SMP."),
                "Stand up an always-on creator and content engine.",
            ],
        },
        "caveats": payload.get("sources_note", "") + " NeedScope positions are as placed in the builder; "
                   "validate market-share, pricing and competitor activity before externalising.",
    }


def enrich_with_ai(payload: dict, research: dict | None) -> dict | None:
    """Mine the parsed research + structured inputs into the brief's narrative sections.

    research: research_parse.ingest_for_brief() output (Map+Synthesize) for uploaded docs/sheets,
              or None when nothing was uploaded.
    Returns a dict of overrides (executive_summary, needscope reading/implication, snapshots,
    opportunities_threats, recommendations, ca_quote, da_quote, caveats) or None if no API key
    is configured or the call fails — in which case the caller keeps the synthesized defaults.
    Verbatim consumer quotes are taken from research as-is and never paraphrased.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
        import research_parse
        # Was its own independent raw-concatenate-to-14000-chars truncation — the same bug pattern as
        # brief_ai.py's draft step, just duplicated here for the export path. Now reads the same
        # Map→Synthesize claims list both AI-enrichment call sites share.
        research_text = research_parse.research_context_block(research)
        def _rows_text(data):
            if isinstance(data, dict) and data.get("rows"):
                return "\n".join(" | ".join(str(c) for c in r) for r in data["rows"][:25])
            return ""
        market_text = _rows_text(payload.get("market_data"))
        household_text = _rows_text(payload.get("household_data"))
        brief_ask = (payload.get("prompt") or "").strip()
        comps = ", ".join(c.get("name", "") for c in payload.get("competitors", []))
        prompt = (
            "You are a brand strategist writing sections of a brand brief for "
            f"{payload.get('brand')} in {payload.get('category','the category')}. "
            f"Competitors: {comps}. SMP: \"{payload.get('smp','')}\". "
            f"Strategic shift: {payload.get('cb_ca_db_da',{}).get('shift_line','')}. "
            f"NeedScope bridge: into {payload.get('needscope',{}).get('bridge_territory','')} "
            f"via \"{payload.get('needscope',{}).get('bridge_label','')}\".\n\n"
            + (f"BRIEF ASK (the marketer's request — anchor the brief to this):\n{brief_ask}\n\n" if brief_ask else "")
            + (f"MARKET SHARE / SALES DATA (use figures verbatim):\n{market_text}\n\n" if market_text else "")
            + (f"HOUSEHOLD / PENETRATION DATA (use figures verbatim):\n{household_text}\n\n" if household_text else "")
            # research_context_block() already carries its own "RESEARCH FINDINGS ..." header.
            + (f"{research_text}\n\n" if research_text else "")
            + "Return ONLY a JSON object (no markdown) with keys: "
            "executive_summary (array of exactly 2 paragraphs), "
            "backgrounder (object: category_perspective, current_situation — each 2-4 sentences on the "
            "CATEGORY vs the FOCAL BRAND respectively, from real data where given, else say not supplied; "
            "consumer_insights — array of 3-5 specific citable findings from qualitative research, or an "
            "empty array if none was supplied; problem_statement — ONE paragraph naming the real business/"
            "marketing problem the SMP and CB/CA shift must answer, not a KPI target and not a solution in "
            "disguise), "
            "needscope_reading (string), needscope_strategic_implication (string), "
            "snapshots (object: pricing, distribution, content_campaigns, content_gaps — each 1-2 sentences, "
            "using the market figures where given), "
            "opportunities_threats (array of 3 objects {opportunity, threat}), "
            "recommendations (object: preface, quick_wins array of 3, strategic_moves array of 3-5), "
            "ca_quote (a real verbatim consumer quote from the research if present, else empty string), "
            "da_quote (aspirational consumer voice if present, else empty string), "
            "caveats (string naming what to validate). "
            "Every recommendation must ladder to the SMP. Do not paraphrase verbatim quotes."
        )
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=os.environ.get("GEN_MODEL", "claude-opus-4-8"),
            # Was 2000 before the backgrounder existed, then 3200. Still too small: a real 18 Sep export
            # produced the exact same "structural defaults" caveat as before with ZERO trace in the logs
            # even after the print-visibility fix below — traced to a SECOND silent-failure path this
            # function had (see the jsonout.extract() call just below) rather than a buffering problem.
            # This contract asks for a lot inside one JSON object (a 2-paragraph exec summary, the whole
            # backgrounder incl. a 3-5 item list, needscope reading/implication, 4-field snapshots, 3
            # opportunities/threats rows, recommendations with up to 8 bullets, 2 quotes, caveats) — the
            # same shape of bug already found and fixed twice in this file's siblings
            # (synthesize_research 4000→7000, summarize_document 1800→3200). Sized up with real headroom.
            max_tokens=4500, messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
        raw = raw[raw.find("{"): raw.rfind("}") + 1]
        data, err = jsonout.extract(raw)
        if data is None:
            # THE bug the print below couldn't catch: extract() failing (malformed/truncated JSON) is a
            # normal return, not an exception — the real 18 Sep failure took this exact path, and the
            # `except` clause's print never fired because nothing raised. Log it here too, with the
            # actual parse error, so the next occurrence says WHY rather than just THAT it failed.
            print(f"[brandbrief.enrich_with_ai] JSON extraction failed: {err}")
            return {}
        return data
    except Exception as e:
        # Was a bare `except Exception: return None` — indistinguishable from the "no API key"
        # case above, and with nothing printed, a real failure here (a timeout, a rate limit, a bug in
        # this prompt) silently degraded a shared, external-facing document to its deterministic
        # defaults with zero trace anywhere. A real user's real export did exactly this: the
        # backgrounder and NeedScope/CB-CA/SMP came through fine (they're the draft step's own output,
        # not this call's), but executive_summary, the pricing/distribution snapshot, opportunities &
        # threats and recommended actions were all still the hardcoded to_skill_brief() placeholders,
        # and nothing anywhere said so. Logged now so a future failure is diagnosable; see generate()
        # below for how the caller turns this into an honest caveat in the document itself.
        print(f"[brandbrief.enrich_with_ai] failed: {type(e).__name__}: {e}")
        return None


def _apply_enrichment(brief: dict, payload: dict, ai: dict):
    """Merge AI overrides into the assembled brief, keeping figures and structured inputs."""
    if ai.get("executive_summary"):
        brief["executive_summary"] = ai["executive_summary"]
    if ai.get("needscope_reading"):
        brief["needscope"]["reading"] = ai["needscope_reading"]
    if ai.get("needscope_strategic_implication"):
        brief["needscope"]["strategic_implication"] = ai["needscope_strategic_implication"]
    if isinstance(ai.get("snapshots"), dict):
        brief["snapshots"].update({k: v for k, v in ai["snapshots"].items() if v})
    if isinstance(ai.get("backgrounder"), dict):
        brief["backgrounder"].update({k: v for k, v in ai["backgrounder"].items() if v})
    if ai.get("opportunities_threats"):
        brief["opportunities_threats"] = ai["opportunities_threats"]
    if isinstance(ai.get("recommendations"), dict):
        brief["recommendations"].update({k: v for k, v in ai["recommendations"].items() if v})
    if ai.get("caveats"):
        brief["caveats"] = ai["caveats"]
    # verbatim quotes only fill gaps; never overwrite a quote the user typed in the builder
    cc = payload.get("cb_ca_db_da", {})
    return brief


def generate(payload: dict, research: dict | None = None, workdir: str | None = None) -> str:
    """Produce the .docx and return its path. NOT the live export path — main.py's /brand-brief route
    calls brief_render.generate() (pure-Python, no Node), which calls this module's enrich_with_ai()
    directly. This function shells out to a Node script and has no caller in main.py; kept for
    reference only. research: research_parse.ingest_for_brief() output, or None.
    """
    workdir = workdir or tempfile.mkdtemp(prefix="brandbrief_")
    ns_png = os.path.join(workdir, "needscope_filled.png")
    cbca_png = os.path.join(workdir, "cbca_dbda_filled.png")
    build_needscope_png(payload, ns_png)
    build_cbca_png(payload, cbca_png)
    brief = to_skill_brief(payload, ns_png, cbca_png)
    ai = enrich_with_ai(payload, research)
    if ai:
        brief = _apply_enrichment(brief, payload, ai)
    brief_path = os.path.join(workdir, "brief.json")
    json.dump(brief, open(brief_path, "w"), ensure_ascii=False)
    out_docx = os.path.join(workdir, f"{payload.get('brand','brand')}_Brand_Brief.docx")
    subprocess.run(
        ["node", os.path.join(_ASSETS, "build_brief_docx.js"), brief_path, out_docx],
        cwd=_ASSETS, check=True, capture_output=True,
    )
    return out_docx
