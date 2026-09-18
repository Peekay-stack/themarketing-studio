"""docs.py — Word (.docx) builders for the guided brief and the video script.

These two documents are simple (labelled fields / a script table), so they are built with
python-docx directly — no Node needed. (The rich IMC brand brief, with its NeedScope and
CB/CA figures, still goes through brief_assets/build_brief_docx.js via brandbrief.py.)
"""
from __future__ import annotations

import os
import re
import tempfile

GREEN = "3F814C"
INK = "14331F"
AMBER = "B07A12"    # the one warning colour, matching the portal's

# One human label per brief field key (from the front end's SECTIONS).
LABELS = {
    "background": "Background & context", "businessObjective": "Business objective",
    "commObjective": "Communication objective", "audience": "Target audience",
    "insight": "Consumer insight", "competition": "Competitive context",
    "proposition": "Single-minded proposition", "rtbs": "Reasons to believe",
    "bigIdea": "The one big idea", "channelRoles": "Role of each channel",
    "tone": "Tone & personality", "mandatories": "Mandatories & brand codes",
    "deliverables": "Deliverables & channels", "budget": "Budget",
    "timeline": "Timeline & milestones", "kpis": "Success metrics / KPIs",
    "mediaHabits": "Media consumption habits", "channelMix": "Channel mix & role",
    "reachGoals": "Reach & frequency goals", "markets": "Markets & flighting",
    "digitalBehaviour": "Digital behaviour & platforms", "funnel": "Funnel & customer journey",
    "formats": "Formats & assets", "targeting": "Targeting & tracking",
    "rangeArch": "Range architecture", "shelfContext": "Shelf & competitive context",
    "packHierarchy": "Pack hierarchy & key info", "claims": "Claims & RTBs",
    "consumerNeed": "Consumer need", "concept": "Product concept",
    "pricing": "Pricing & positioning", "feasibility": "Quality, regulatory & feasibility",
    "launch": "Launch plan & timeline", "narrative": "Core narrative & angles",
    "messages": "Key messages", "spokespeople": "Spokespeople & proof points",
    "stakeholders": "Target media & stakeholders", "milestones": "Milestones",
}


def _pretty(key: str) -> str:
    return LABELS.get(key) or re.sub(r"(?<!^)(?=[A-Z])", " ", key).strip().capitalize()


_FOOTER_MARK = os.path.join(os.path.dirname(__file__), "frontend", "assets", "tms-footer-mark.png")


def _add_footer(doc):
    """The Marketing Studio's own mark on every page of every document this module builds (guided
    briefs, the production bible, messaging house, idea platform, comm plan, call sheets, scripts) —
    every one of them leaves the portal and gets circulated on its own. The mark (tms-footer-mark.png)
    already renders "the marketing studio" as part of the lockup, so no separate URL text runs
    alongside it — the user asked for the logo alone, a touch larger, after the first version doubled
    up (logo + a second "themarketing-studio.com" caption crowding it). Shared with brief_render.py's
    own copy of this same helper — same asset, same look."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches
    footer = doc.sections[0].footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists(_FOOTER_MARK):
        run = p.add_run()
        try:
            run.add_picture(_FOOTER_MARK, width=Inches(0.9))
        except Exception:
            pass


def _new_doc(title: str):
    from docx import Document
    from docx.shared import Pt, RGBColor
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(11)
    _add_footer(doc)
    h = doc.add_heading(title, level=0)
    for run in h.runs:
        run.font.color.rgb = RGBColor.from_string(INK)
    return doc


def build_brief_docx(title: str, objective: str, fields: dict, out_path: str | None = None) -> str:
    """A labelled brief document for Media/Digital/Packaging/Product/PR."""
    from docx.shared import RGBColor
    doc = _new_doc(title or "Brief")
    if objective:
        p = doc.add_paragraph()
        r = p.add_run("Campaign objective: ")
        r.bold = True
        p.add_run(objective)
    fields = fields or {}
    # keep a stable, readable order: known keys first (in LABELS order), then any extras
    ordered = [k for k in LABELS if k in fields] + [k for k in fields if k not in LABELS]
    for key in ordered:
        val = (fields.get(key) or "").strip() if isinstance(fields.get(key), str) else fields.get(key)
        if not val:
            continue
        h = doc.add_heading(_pretty(key), level=2)
        for run in h.runs:
            run.font.color.rgb = RGBColor.from_string(GREEN)
        doc.add_paragraph(str(val))
    out_path = out_path or os.path.join(tempfile.mkdtemp(prefix="brief_"), "brief.docx")
    doc.save(out_path)
    return out_path


def _normalise(path: str) -> str | None:
    """Re-save through Pillow as a clean PNG.

    python-docx parses image headers itself and rejects files whose markers it doesn't recognise —
    encoder-specific JPEGs (ffmpeg's, for one) fail with an empty error. Round-tripping via Pillow
    guarantees a header it accepts, and also flattens transparency.
    """
    try:
        from PIL import Image
        with Image.open(path) as im:
            im.load()
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            out = os.path.splitext(path)[0] + "-doc.png"
            im.save(out, format="PNG")
        return out
    except Exception:
        return path      # better to try the original than to drop the picture entirely


def _fetch_image(url: str, dest_dir: str, name: str) -> str | None:
    """Download a storyboard frame so python-docx can embed it. None if it can't be had."""
    if not url:
        return None
    try:
        if url.startswith("data:"):
            import base64
            head, _, b64 = url.partition(",")
            ext = ".png" if "png" in head else ".jpg"
            path = os.path.join(dest_dir, name + ext)
            with open(path, "wb") as fh:
                fh.write(base64.b64decode(b64))
            return _normalise(path)
        if not url.lower().startswith(("http://", "https://")):
            return None
        import httpx
        with httpx.stream("GET", url, timeout=90.0, follow_redirects=True) as r:
            r.raise_for_status()
            ext = ".png" if "png" in (r.headers.get("content-type") or "") else ".jpg"
            path = os.path.join(dest_dir, name + ext)
            with open(path, "wb") as fh:
                fh.writelines(r.iter_bytes(1 << 16))
        return _normalise(path)
    except Exception:
        return None


def build_production_bible(title: str, logline: str, scenes: list, departments: list,
                           frames: list | None = None, meta: dict | None = None,
                           cast_sheet: str = "", cast_reference: str = "",
                           out_path: str | None = None) -> str:
    """The whole production in one document: script table, department notes, storyboard images.

    `departments` is [{label, text}]; `frames` is [{scene, tc, visual, url}]. Images are embedded
    (downloaded first); any that can't be fetched are listed as links so nothing is silently lost.
    """
    from docx.shared import Inches, Pt
    doc = _new_doc(title or "Production Bible")
    meta = meta or {}
    if logline:
        p = doc.add_paragraph()
        p.add_run("Logline: ").bold = True
        p.add_run(logline)
    if meta:
        p = doc.add_paragraph()
        bits = [f"{k}: {v}" for k, v in meta.items() if v]
        p.add_run(" · ".join(bits)).italic = True

    tmp = tempfile.mkdtemp(prefix="bible_")

    # --- the cast, and the reference image every frame was generated from ---
    if cast_sheet or cast_reference:
        doc.add_heading("Cast & continuity", level=1)
        if cast_sheet:
            doc.add_paragraph(cast_sheet)
        ref = _fetch_image(cast_reference, tmp, "castref")
        if ref:
            try:
                doc.add_picture(ref, width=Inches(5.5))
            except Exception:
                pass
        elif cast_reference.lower().startswith("http"):
            doc.add_paragraph(f"Cast reference: {cast_reference}")

    # --- script table ---
    doc.add_heading("Shooting script", level=1)
    scenes = [s for s in (scenes or []) if isinstance(s, dict)]
    if scenes:
        cols = ["Scene", "Visual / Action", "Camera", "Dialogue / VO", "Super"]
        table = doc.add_table(rows=1, cols=len(cols))
        try:
            table.style = "Table Grid"
        except Exception:
            pass
        for i, c in enumerate(cols):
            cell = table.rows[0].cells[i]
            cell.text = c
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True
        for sc in scenes:
            row = table.add_row().cells
            no, tc = str(sc.get("no", "") or ""), str(sc.get("tc", "") or "")
            row[0].text = f"{no}\n{tc}" if tc else no
            row[1].text = str(sc.get("visual", "") or "")
            row[2].text = str(sc.get("camera", "") or "")
            row[3].text = str(sc.get("dialogue", "") or "")
            row[4].text = str(sc.get("supr", "") or "")
    else:
        doc.add_paragraph("No scenes yet — write the full script first.")

    # --- storyboard, one frame per scene ---
    frames = [f for f in (frames or []) if isinstance(f, dict) and f.get("url")]
    if frames:
        doc.add_heading("Storyboard", level=1)
        missing = []
        for i, fr in enumerate(frames):
            head = doc.add_paragraph()
            label = f"Scene {fr.get('scene', i + 1)}"
            if fr.get("tc"):
                label += f"  ·  {fr['tc']}"
            head.add_run(label).bold = True
            path = _fetch_image(str(fr.get("url")), tmp, f"frame{i:02d}")
            if path:
                try:
                    doc.add_picture(path, width=Inches(6.0))
                except Exception:
                    missing.append((label, fr.get("url")))
            else:
                missing.append((label, fr.get("url")))
            if fr.get("visual"):
                cap = doc.add_paragraph()
                run = cap.add_run(str(fr["visual"]))
                run.italic = True
                run.font.size = Pt(9)
        for label, url in missing:
            # Never print a data: URI — it would run to hundreds of KB of text.
            where = url if str(url).lower().startswith("http") else "(embedded image could not be read)"
            doc.add_paragraph(f"{label} — image unavailable: {where}")

    # --- department notes ---
    depts = [d for d in (departments or []) if isinstance(d, dict) and (d.get("text") or "").strip()]
    if depts:
        doc.add_heading("Department notes", level=1)
        for d in depts:
            doc.add_heading(str(d.get("label") or "Department"), level=2)
            for para in str(d.get("text") or "").split("\n"):
                if para.strip():
                    doc.add_paragraph(para.strip())

    out_path = out_path or os.path.join(tempfile.mkdtemp(prefix="bible_"), "production_bible.docx")
    doc.save(out_path)
    return out_path


# =====================================================================================
# The two strategy documents — messaging house and communication plan
#
# These get circulated and argued over, which is the whole reason they need to leave the portal. Two
# rules shape both builders:
#
# **The document carries its own findings.** A house that looks finished and is not is worse than one
# that admits it, and a Word file is exactly where that pretence usually happens: the blocking findings
# stay on the screen and the clean-looking export goes to the client. So they are printed, in the
# document, with the overridden ones showing who accepted the risk.
#
# **Empty is not zero.** An unknown owner prints "owner unknown", never a blank cell. A blank reads as
# settled, and in a document nobody can hover over it to find out otherwise.
#
# Headings are the layer labels verbatim, level 2, so a re-import can find them again later.
# =====================================================================================

# What each `source` value means to someone reading the document rather than the screen.
_SOURCE_WORDS = {
    "brief": "from the brief",
    "library": "from the signed library",
    "user": "written here",
    "model": "MODEL SUGGESTION — traces to nothing in the brief or library",
}

# Plan table column headings. A separate map from LABELS on purpose: LABELS belongs to the brief, where
# `audience` means "Target audience". In a plan table the column is just Audience, and borrowing the
# brief's wording put a brief's heading on a plan's table.
_PLAN_COLS = {
    "level": "Level", "statement": "Statement", "measure": "Measure", "by_when": "By when",
    "audience": "Audience", "rank": "Rank", "believes_now": "Believes now", "pillar": "Pillar",
    "channel": "Channel", "role": "Role", "job": "What it is asked to do", "side": "Brand / activation",
    "share": "Share of spend", "owner": "Owner", "lead": "Lead",
    "phase": "Phase", "window": "Window", "occasion": "Occasion", "channels": "Channels",
    "hands_over": "Hands over to",
    "leading": "Leading indicator", "lagging": "Lagging indicator",
    "would_tell_us_it_failed": "What would tell us it failed",
    "who": "Who", "speaks_on": "Speaks on", "boundary": "Boundary",
    "decides_changes": "Decides changes",
}


def _col(key: str) -> str:
    """A column heading for a plan table. Falls back to un-snaking rather than to the brief's labels."""
    return _PLAN_COLS.get(key) or key.replace("_", " ").strip().capitalize()


_LEVEL_WORDS = {
    "blocking": "BLOCKING",
    "unsourced": "Unsourced",
    "stale": "Stale",
    "open": "Open",
    "empty": "Empty",
}


def _heading(doc, text: str, level: int = 2, colour: str = None):
    from docx.shared import RGBColor
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor.from_string(colour or GREEN)
    return h


def _findings_section(doc, findings: list, what: str) -> None:
    """Print the document's own objections to itself. Never omitted, never softened."""
    from docx.shared import Pt
    findings = [f for f in (findings or []) if isinstance(f, dict)]
    _heading(doc, "What is still outstanding", level=1, colour=INK)
    if not findings:
        doc.add_paragraph("Nothing outstanding — every check on this "
                          f"{what} passes.")
        return
    live = [f for f in findings if f.get("level") == "blocking" and "overridden" not in f]
    if live:
        p = doc.add_paragraph()
        r = p.add_run(f"{len(live)} blocking. This {what} is not finished.")
        r.bold = True
    order = {"blocking": 0, "unsourced": 1, "stale": 2, "open": 3, "empty": 4}
    for f in sorted(findings, key=lambda x: order.get(x.get("level"), 9)):
        p = doc.add_paragraph(style="List Bullet")
        tag = _LEVEL_WORDS.get(f.get("level"), str(f.get("level") or ""))
        r = p.add_run(f"[{tag}] ")
        r.bold = f.get("level") == "blocking"
        p.add_run(str(f.get("detail") or ""))
        ov = f.get("overridden")
        if ov:
            note = doc.add_paragraph()
            note.paragraph_format.left_indent = Pt(36)
            run = note.add_run(f"Accepted by {ov.get('who') or 'unattributed'} on "
                               f"{ov.get('at') or 'an unrecorded date'}: {ov.get('reason') or ''}")
            run.italic = True
            run.font.size = Pt(9)


def _write_in_space(doc, rows: int = 3, prompt: str = "") -> None:
    """Ruled space to write in. A bordered table rather than underscores — it prints, it survives being
    photocopied, and it does not reflow into nonsense when someone types into it on a laptop."""
    from docx.shared import Pt
    if prompt:
        p = doc.add_paragraph()
        r = p.add_run(prompt)
        r.bold = True
        r.font.size = Pt(9)
    table = doc.add_table(rows=rows, cols=1)
    try:
        table.style = "Table Grid"
    except Exception:
        pass


def _caveat_block(doc, caveat: dict, worksheet: bool) -> None:
    """The round-trip caveat, at the top of every download and before any house is started."""
    from docx.shared import Pt
    _heading(doc, caveat.get("headline") or "Before you use this file", level=1, colour=INK)
    if worksheet:
        p = doc.add_paragraph()
        p.add_run("This is a worksheet. Write in it, then type your revisions back into the "
                  "portal — this file cannot be read back in.").bold = True
    for line in (caveat.get("points") or []):
        para = doc.add_paragraph(style="List Bullet")
        run = para.add_run(str(line))
        run.font.size = Pt(10)


def _house_summary(doc, house: dict, worksheet: bool) -> None:
    """One page at the front: the argument, in reading order, before any inventory.

    **This is the fix for a real and fair complaint** — that the documents read below what a chat session
    produces. The content was never the problem: every layer, every option, its tag, its source and its
    rationale were all here. The *shape* was. A reader opened five paragraphs of housekeeping, then a
    layer-by-layer catalogue of options with their tags, and had to assemble the argument themselves.

    A strategy document is read as a case: this is true, therefore we say this, and here is why anyone
    should believe it. That case existed in the data and nowhere on the page. So it goes first, as prose,
    and the catalogue becomes the evidence behind it rather than the document itself.

    Nothing here is generated. Every sentence is a line somebody chose, in the order the layers imply.
    """
    from docx.shared import Pt, RGBColor

    import strategy

    def chosen(lid):
        return strategy._chosen_text(house, lid)

    core = chosen("core")
    if not core:
        return                                  # nothing decided yet; a summary would be a blank page

    _heading(doc, "The argument on one page", level=1, colour=INK)

    def para(label, body, *, bold_body=False, size=10.5):
        if not body:
            return
        p = doc.add_paragraph()
        if label:
            r = p.add_run(label + "  ")
            r.bold = True
            r.font.size = Pt(size)
        r2 = p.add_run(body)
        r2.font.size = Pt(size)
        r2.bold = bold_body

    para("", "; ".join(core), bold_body=True, size=13)

    emo, fun = chosen("emotional"), chosen("functional")
    if emo:
        para("We say, to the heart:", "; ".join(emo))
    if fun:
        para("We say, to the head:", "; ".join(fun))

    # The proof, and honestly when there is none. An unsourced reason is the one thing a reader of a
    # strategy document most needs flagged, because it is invisible once the line is written well.
    for lid, label in (("rtb_emotional", "Believable because"),
                       ("rtb_functional", "Provable because")):
        node = (house.get("nodes") or {}).get(lid) or {}
        picked = set(node.get("chosen") or [])
        rows = [o for o in node.get("options", []) if o["id"] in picked]
        if not rows:
            continue
        for o in rows:
            src = str(o.get("source") or "").lower()
            ok = src in ("brief", "library", "user")
            p = doc.add_paragraph(style="List Bullet")
            r = p.add_run(f"{label}: ") if o is rows[0] else p.add_run("")
            r.bold = True
            r.font.size = Pt(10)
            r2 = p.add_run(o.get("text", ""))
            r2.font.size = Pt(10)
            if not ok:
                w = p.add_run("   [not yet sourced — this cannot carry proof]")
                w.font.size = Pt(9)
                w.bold = True
                w.font.color.rgb = RGBColor.from_string(AMBER)

    demo = chosen("proof")
    if demo:
        para("What we can show:", " · ".join(demo))
    cult = [o["text"] for o in ((house.get("nodes") or {}).get("culture") or {}).get("options", [])
            if o["id"] in set(((house.get("nodes") or {}).get("culture") or {}).get("chosen") or [])
            and str(o.get("tag", "")).lower() != "avoid"]
    if cult:
        para("Where we live:", " · ".join(cult))
    avoid = [o["text"] for o in ((house.get("nodes") or {}).get("culture") or {}).get("options", [])
             if o["id"] in set(((house.get("nodes") or {}).get("culture") or {}).get("chosen") or [])
             and str(o.get("tag", "")).lower() == "avoid"]
    if avoid:
        para("Where we never go:", " · ".join(avoid))

    # What the brand says in each medium — the layer most likely to be acted on, and the one buried
    # deepest in the old layout.
    node = (house.get("nodes") or {}).get("medium") or {}
    picked = set(node.get("chosen") or [])
    by_med: dict[str, list[str]] = {}
    for o in node.get("options", []):
        if o["id"] in picked and str(o.get("text") or "").strip():
            by_med.setdefault(str(o.get("tag") or "general").lower(), []).append(o["text"].strip())
    if by_med:
        _heading(doc, "And so, in each medium", level=2)
        for med, lines in by_med.items():
            for line in lines:
                p = doc.add_paragraph(style="List Bullet")
                r = p.add_run(med.upper() + "  ")
                r.bold = True
                r.font.size = Pt(9)
                r2 = p.add_run(line)
                r2.font.size = Pt(10)

    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run("Everything after this page is the evidence: each layer, what else was considered, and "
                  "where every line came from."
                  if not worksheet else
                  "Everything after this page asks you the same questions again, in the same order, with "
                  "space to answer them.")
    r.italic = True
    r.font.size = Pt(9.5)
    doc.add_page_break()


def build_house_docx(house: dict, status: dict | None = None, out_path: str | None = None,
                     mode: str = "record") -> str:
    """The messaging house as a document — every layer, what was chosen, and where it came from.

    Two modes of one document:

    **`record`** — what was decided, for circulating and arguing over.

    **`worksheet`** — the same content plus each layer's actual question and ruled space to answer it
    again. For thinking away from the screen and then re-entering. This exists because the portal cannot
    import a Word file: if somebody is going to redo the exercise on paper, the paper should ask them the
    same questions the screen does, in the same order, or they will come back with answers that do not
    map onto any layer.

    The options *not* chosen go in an appendix rather than being dropped. A strategy document that shows
    only the answer cannot be argued with, and the alternatives are most of what a client actually wants
    to see: they are the evidence that a choice was made rather than a line being written.
    """
    from docx.shared import Pt

    import strategy

    house = house or {}
    status = status or {}
    worksheet = str(mode).lower() == "worksheet"
    brand = house.get("brand") or "Brand"
    doc = _new_doc(f"{brand} — Messaging house" + (" · worksheet" if worksheet else ""))

    p = doc.add_paragraph()
    r = p.add_run(f"Last changed {house.get('updated') or 'unknown'}")
    r.italic = True
    if status.get("complete"):
        doc.add_paragraph("Every layer decided, nothing blocking.")
    else:
        decided = sum(1 for l in status.get("layers", []) if l.get("chosen"))
        total = len(status.get("layers") or strategy.LAYERS)
        doc.add_paragraph(f"{decided} of {total} layers decided. This is a working document.")

    # The argument first. The round-trip caveat matters, but it is housekeeping, and five paragraphs of it
    # was the first thing anybody opening this file saw - so it moves to the back.
    _house_summary(doc, house, worksheet)

    if worksheet:
        _heading(doc, "How to use this", level=2)
        doc.add_paragraph(
            "Each layer below gives you the question, what is currently chosen, and what else was "
            "considered. Underneath is space to write the answer again.")
        doc.add_paragraph(
            "Work down the layers in order. The order is the argument: every layer is written against "
            "the one above it, so changing the core message changes what the pillars should say. "
            "Answering them out of order produces a house that reads well and decides nothing.")
        doc.add_paragraph(
            "When you come back, open Strategy → the layer → Write your own, and type what you wrote "
            "here. A line you have written yourself counts as sourced — you are the evidence for it.")
        doc.add_page_break()

    by_id = {l.get("id"): l for l in (status.get("layers") or [])}
    unchosen: list[tuple[str, list]] = []

    for layer in strategy.LAYERS:
        node = (house.get("nodes") or {}).get(layer["id"]) or {}
        picked = set(node.get("chosen") or [])
        options = node.get("options") or []
        chosen = [o for o in options if o.get("id") in picked]
        rest = [o for o in options if o.get("id") not in picked]

        _heading(doc, layer["label"], level=2)
        st = by_id.get(layer["id"]) or {}
        if st.get("stale"):
            w = doc.add_paragraph()
            run = w.add_run("Stale — written under choices that have since moved.")
            run.bold = True

        # In worksheet mode the layer's own question comes first, before any answer — so someone
        # rethinking this layer is answering the question rather than editing the previous answer.
        if worksheet:
            q = doc.add_paragraph()
            qr = q.add_run(str(layer.get("asks") or ""))
            qr.italic = True

        if not chosen:
            doc.add_paragraph(f"Nothing chosen yet. {layer['asks']}"
                              if not (options or worksheet) else
                              f"{len(options)} option(s) written, none chosen yet."
                              if options else "Nothing here yet.")
            if worksheet:
                _write_in_space(doc, 3, "Your answer:")
                if layer["id"] in ("culture", "medium"):
                    doc.add_paragraph(
                        "Tag each line with which kind it is: "
                        + ", ".join(strategy.CULTURE_KINDS if layer["id"] == "culture"
                                    else strategy.MEDIA)).runs[0].font.size = Pt(9)
            if rest:
                unchosen.append((layer["label"], rest))
            continue

        if worksheet:
            lab = doc.add_paragraph()
            lr = lab.add_run("Currently chosen")
            lr.bold = True
            lr.font.size = Pt(9)

        for o in chosen:
            para = doc.add_paragraph(style="List Bullet")
            para.add_run(str(o.get("text") or "")).bold = True
            bits = []
            if o.get("tag"):
                bits.append(str(o["tag"]))
            bits.append(_SOURCE_WORDS.get(str(o.get("source") or "").lower(),
                                          str(o.get("source") or "source unrecorded")))
            sub = doc.add_paragraph()
            sub.paragraph_format.left_indent = Pt(36)
            run = sub.add_run(" · ".join(bits))
            run.italic = True
            run.font.size = Pt(9)
            if str(o.get("note") or "").strip():
                n = doc.add_paragraph()
                n.paragraph_format.left_indent = Pt(36)
                nr = n.add_run(str(o["note"]).strip())
                nr.font.size = Pt(9)

        # The alternatives sit inline in the worksheet, not in an appendix. Someone rethinking a layer
        # needs to see what was already rejected at the moment they are deciding — flipping to the back
        # of the document is how the same discarded option gets proposed again.
        if worksheet and rest:
            lab = doc.add_paragraph()
            lr = lab.add_run("Also considered, not chosen")
            lr.bold = True
            lr.font.size = Pt(9)
            for o in rest:
                a = doc.add_paragraph(style="List Bullet")
                ar = a.add_run(str(o.get("text") or ""))
                ar.font.size = Pt(9)

        if worksheet:
            _write_in_space(doc, 3, "Write it again — or write what is wrong with the above:")
            src = doc.add_paragraph()
            sr = src.add_run("Where does your line come from? (the brief · the library · your own "
                             "judgement — say which, because an unsourced claim is the one thing this "
                             "house will not let you ship)")
            sr.italic = True
            sr.font.size = Pt(8)
            if layer["id"] in ("culture", "medium"):
                t = doc.add_paragraph()
                tr = t.add_run("Tag each line with which kind it is: "
                               + ", ".join(strategy.CULTURE_KINDS if layer["id"] == "culture"
                                           else strategy.MEDIA))
                tr.font.size = Pt(8)

        if rest and not worksheet:
            unchosen.append((layer["label"], rest))

    _findings_section(doc, status.get("findings"), "house")

    if unchosen:
        _heading(doc, "Also considered, and not chosen", level=1, colour=INK)
        doc.add_paragraph("Kept so the decision can be argued with rather than only read.")
        for label, opts in unchosen:
            _heading(doc, label, level=3)
            for o in opts:
                para = doc.add_paragraph(style="List Bullet")
                para.add_run(str(o.get("text") or ""))
                if str(o.get("note") or "").strip():
                    para.add_run(f"  — {o['note']}").italic = True

    # Retired layers, printed because the content is still the person's work.
    #
    # `status()` keeps these out of `layers` so no screen offers them as something to decide, and the
    # loop above walks `strategy.LAYERS` — so without this block, retiring a layer would silently delete
    # seven chosen paragraphs from every download. That is the difference between moving a question and
    # losing an answer.
    for r in (status.get("retired_layers") or []):
        if not r.get("chosen"):
            continue
        _heading(doc, r.get("label") or r.get("id", ""), level=1, colour=INK)
        wp = doc.add_paragraph()
        wr = wp.add_run(f"No longer asked here — this now lives in {r.get('went', 'the jobs table')}. "
                        f"{r.get('why', '')}")
        wr.italic = True
        wr.font.size = Pt(9)
        wr.font.color.rgb = _amber()
        picked = set(r.get("chosen") or [])
        for o in (r.get("options") or []):
            if o.get("id") not in picked:
                continue
            para = doc.add_paragraph(style="List Bullet")
            para.add_run(str(o.get("text") or ""))
            if str(o.get("tag") or "").strip():
                para.add_run(f"  [{o['tag']}]").italic = True
            if str(o.get("note") or "").strip():
                para.add_run(f"  — {o['note']}").italic = True

    doc.add_page_break()
    _caveat_block(doc, strategy.ROUND_TRIP_CAVEAT, worksheet)

    out_path = out_path or os.path.join(tempfile.mkdtemp(prefix="house_"), "messaging_house.docx")
    doc.save(out_path)
    return out_path


def _amber():
    from docx.shared import RGBColor
    return RGBColor.from_string(AMBER)


def build_platform_docx(platform: dict, status: dict | None = None, out_path: str | None = None,
                        mode: str = "record", house: dict | None = None) -> str:
    """The idea platform as a document — the idea, its mechanic, the tests, and each expression.

    The one document in the spine that did not exist. A platform is the thing every execution is an
    expression of, so it is the page most likely to be circulated and argued over, and there was no way
    to take it out of the screen.

    The tests print with the **verdict and the reason somebody wrote**, not a score. A platform that
    passed because a person said why is a different object from one that passed a checker, and the reason
    is the part a reader needs.
    """
    from docx.shared import Pt

    import ideas as ideas_mod

    platform = platform or {}
    status = status or {}
    worksheet = str(mode).lower() == "worksheet"
    it = ideas_mod.chosen_platform(platform) or {}
    brand = platform.get("brand") or "Brand"
    doc = _new_doc(f"{brand} — Idea platform" + (" · worksheet" if worksheet else ""))

    p = doc.add_paragraph()
    p.add_run(f"Last changed {platform.get('updated') or 'unknown'}").italic = True

    if not it:
        doc.add_paragraph("No platform has been adopted yet. This document is the shape it will take.")
    else:
        _heading(doc, it.get("name") or "The platform", level=1, colour=INK)
        q = doc.add_paragraph()
        r = q.add_run(str(it.get("idea") or ""))
        r.bold = True
        r.font.size = Pt(13)
        for field, label in (("mechanic", "The repeatable device"),
                             ("pillar", "Which pillar it comes out of"),
                             ("rtb", "The reason to believe it dramatises"),
                             ("territory", "Territory"),
                             ("truth", "The truth under it"), ("why", "Why this one")):
            v = str(it.get(field) or "").strip()
            if v:
                s = doc.add_paragraph()
                sr = s.add_run(label + ": ")
                sr.bold = True
                sr.font.size = Pt(10)
                s.add_run(v).font.size = Pt(10)
        src = str(it.get("source") or "")
        if src:
            m = doc.add_paragraph()
            mr = m.add_run("Written by the model and not yet rewritten by a person."
                           if src == "model" else "Written or rewritten by a person — sourced.")
            mr.italic = True
            mr.font.size = Pt(9)
            mr.font.color.rgb = _amber() if src == "model" else _amber()

    # The tests — the person's verdict AND the model's, side by side.
    #
    # Two readers, kept apart on purpose: a model is a fast, harsh first reader and genuinely useful, but
    # the tests are judgements somebody has to own. Printing only one of them would either hide the
    # challenge or present it as the decision. Where they disagree, that is the most useful line on the
    # page, so it is called out rather than left for the reader to spot.
    verdicts = (it.get("verdicts") or {}) if it else {}
    # Read through the alias map, so a verdict stored under the old key for the fifth test still prints
    # against the question it answered rather than as a sixth test nobody was asked.
    judged = ideas_mod.normalise_judged(it.get("judged")) if it else {}
    keys = [k for k in ideas_mod.JUDGED] + [k for k in verdicts if k not in ideas_mod.JUDGED]
    if verdicts or judged or worksheet:
        # Counted, never spelled out. This said "The five tests" for as long as there were five; the
        # tests shrank to two (`ideas.JUDGED`, with `RETIRED_TESTS` recording where the other three
        # went) and the heading did not, so the document announced five and then printed two — while
        # its own outstanding list said "2 of 2 tests not answered" three pages later. A number written
        # as a word is a number that goes stale silently.
        _n = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}.get(len(keys), len(keys))
        _heading(doc, f"The {_n} test{'' if len(keys) == 1 else 's'}", level=1, colour=INK)
        doc.add_paragraph("Two readings. The model's is a challenge; yours is the decision. Where they "
                          "disagree is the part worth reading.")
        if ideas_mod.judged_stale(it):
            sp = doc.add_paragraph()
            sr = sp.add_run("The model read an earlier version of this line. Its verdicts below are kept "
                            "because a superseded challenge is still worth reading — but ask it again "
                            "before treating them as current.")
            sr.italic = True
            sr.font.size = Pt(9)
            sr.font.color.rgb = _amber()
        for key in keys:
            mine = verdicts.get(key) if isinstance(verdicts.get(key), dict) else (
                {"verdict": str(verdicts[key])} if key in verdicts else {})
            theirs = judged.get(key) or {}
            if not (mine or theirs or worksheet):
                continue
            q = ideas_mod.JUDGED.get(key, "")
            _heading(doc, str(key).replace("_", " ").capitalize(), level=3)
            if q:
                qp = doc.add_paragraph()
                qr = qp.add_run(q)
                qr.italic = True
                qr.font.size = Pt(9)

            mv = str(mine.get("verdict") or "").strip()
            tv = str(theirs.get("verdict") or "").strip()
            for who, v, note in (("You", mv, str(mine.get("note") or "").strip()),
                                 ("The model", tv, str(theirs.get("note") or "").strip())):
                if not v and not note:
                    continue
                line = doc.add_paragraph(style="List Bullet")
                wr = line.add_run(who + ": ")
                wr.bold = True
                wr.font.size = Pt(9.5)
                vr = line.add_run(v or "not judged")
                vr.bold = True
                vr.font.size = Pt(9.5)
                if note:
                    nr = line.add_run("  — " + note)
                    nr.font.size = Pt(9.5)
            fix = str(theirs.get("fix") or "").strip()
            if fix and tv in ("weak", "fails"):
                f = doc.add_paragraph(style="List Bullet")
                fr = f.add_run("What would have to change: ")
                fr.bold = True
                fr.font.size = Pt(9)
                f.add_run(fix).font.size = Pt(9)
            if mv and tv and mv.lower() != tv.lower():
                d = doc.add_paragraph()
                dr = d.add_run(f"You and the model disagree here — you say {mv}, it says {tv}.")
                dr.bold = True
                dr.font.size = Pt(9)
                dr.font.color.rgb = _amber()
            elif not mv and tv:
                d = doc.add_paragraph()
                dr = d.add_run("Only the model has answered this one. Its verdict is a challenge, not a "
                               "decision.")
                dr.italic = True
                dr.font.size = Pt(9)
                dr.font.color.rgb = _amber()
            if worksheet:
                _write_in_space(doc, 2, "Your judgement, and why:")

    # What it becomes in each producer.
    expr = {k: str(v).strip() for k, v in ((it.get("expressions") or {}) if it else {}).items()
            if str(v or "").strip()}
    _heading(doc, "What it becomes in each producer", level=1, colour=INK)
    if expr:
        doc.add_paragraph("Every execution is one expression of the idea above. These are the ones "
                          "written so far.")
        for k, v in expr.items():
            e = doc.add_paragraph(style="List Bullet")
            er = e.add_run(str(k).replace("_", " ").upper() + "  ")
            er.bold = True
            er.font.size = Pt(9)
            e.add_run(v).font.size = Pt(10)
    else:
        e = doc.add_paragraph()
        er = e.add_run("Nothing expressed yet. Until a producer has one, the platform is a sentence "
                       "rather than a campaign.")
        er.italic = True
        er.font.size = Pt(10)
    if worksheet:
        for k in ideas_mod.EXPRESSIONS:
            _heading(doc, str(k).replace("_", " ").title(), level=3)
            _write_in_space(doc, 2, "What the platform becomes here:")

    # The routes that were not taken. A strategy document showing only the answer cannot be argued
    # with, and the alternatives are most of what a reader wants: they are the evidence a choice was made
    # rather than a line being written.
    rest = [x for x in (platform.get("platforms") or []) if x.get("id") != (it or {}).get("id")]
    if rest and not worksheet:
        _heading(doc, "Also considered, and not chosen", level=1, colour=INK)
        for x in rest:
            _heading(doc, x.get("name") or "Unnamed route", level=3)
            para = doc.add_paragraph()
            para.add_run(str(x.get("idea") or "")).font.size = Pt(10)
            bits = [f"{lbl}: {x[f]}" for f, lbl in (("pillar", "pillar"), ("rtb", "rests on"),
                                                   ("mechanic", "mechanic"), ("caveat", "thin because"))
                    if str(x.get(f) or "").strip()]
            if bits:
                b = doc.add_paragraph()
                br = b.add_run("  ·  ".join(bits))
                br.italic = True
                br.font.size = Pt(9)

    _findings_section(doc, status.get("findings"), "platform")
    doc.add_page_break()
    import strategy as strategy_mod
    _caveat_block(doc, strategy_mod.ROUND_TRIP_CAVEAT, worksheet)

    out_path = out_path or os.path.join(tempfile.mkdtemp(prefix="platform_"), "idea_platform.docx")
    doc.save(out_path)
    return out_path


def _plan_serves(doc, plan_doc: dict, house: dict | None) -> None:
    """The house this plan distributes, on the front page, in one block.

    Named `serves` rather than `summary` because that is the relationship: the house decides what is
    said, the plan decides where it is said, and the plan is answerable to it. The document was not even
    passed a house, so a reader got tables of channels with nothing on the page saying what any of them
    were carrying. Distribution detached from the message is the failure this whole spine exists to
    prevent, and the document was the last place it was still happening.
    """
    from docx.shared import Pt

    import strategy
    if not house:
        para = doc.add_paragraph()
        r = para.add_run("No messaging house is bound to this plan, so nothing here has been checked "
                         "against what the brand says, and the proof gate cannot run.")
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = _amber()
        return

    core = strategy._chosen_text(house, "core")
    if not core:
        return
    _heading(doc, "What this plan serves", level=1, colour=INK)
    para = doc.add_paragraph()
    r = para.add_run("; ".join(core))
    r.bold = True
    r.font.size = Pt(12.5)

    import plan as plan_mod
    for lid, label in (("emotional", "Emotional message"), ("functional", "Functional message")):
        v = strategy._chosen_text(house, lid)
        if not v:
            continue
        sourced, total = plan_mod.pillar_evidence(house, lid)
        para = doc.add_paragraph()
        r = para.add_run(label + ": ")
        r.bold = True
        r.font.size = Pt(10)
        r2 = para.add_run("; ".join(v))
        r2.font.size = Pt(10)
        note = para.add_run(f"   [{sourced} of {total} reasons-to-believe sourced"
                            + ("" if sourced else " - may NOT be given proof work") + "]")
        note.font.size = Pt(9)
        note.bold = True
        if not sourced:
            note.font.color.rgb = _amber()

    node = (house.get("nodes") or {}).get("medium") or {}
    picked = set(node.get("chosen") or [])
    meds: dict = {}
    for o in node.get("options", []):
        if o["id"] in picked and str(o.get("text") or "").strip():
            meds.setdefault(str(o.get("tag") or "general").lower(), []).append(o["text"].strip())
    if meds:
        _heading(doc, "What the brand already says in each medium", level=2)
        doc.add_paragraph("Every channel below should be carrying one of these, not a new line.")
        for med, lines in meds.items():
            for line in lines:
                para = doc.add_paragraph(style="List Bullet")
                r = para.add_run(med.upper() + "  ")
                r.bold = True
                r.font.size = Pt(9)
                r2 = para.add_run(line)
                r2.font.size = Pt(9.5)
    doc.add_page_break()


def build_plan_docx(plan_doc: dict, status: dict | None = None, out_path: str | None = None,
                    mode: str = "record", house: dict | None = None) -> str:
    """The communication plan as a document. The layers are tables, so these are real Word tables —
    which is also what makes a plan re-importable later in a way a house is not.

    `worksheet` mode adds each layer's question and blank rows to fill, for the same reason the house
    has one: someone redoing the exercise on paper should be answering the same questions in the same
    order, or their answers will not map onto any layer when they come back to type them in.
    """
    from docx.shared import Pt

    import plan as plan_mod
    import strategy

    plan_doc = plan_doc or {}
    status = status or {}
    worksheet = str(mode).lower() == "worksheet"
    brand = plan_doc.get("brand") or "Brand"
    doc = _new_doc(f"{brand} — Communication plan" + (" · worksheet" if worksheet else ""))

    p = doc.add_paragraph()
    p.add_run(f"Last changed {plan_doc.get('updated') or 'unknown'}").italic = True

    _plan_serves(doc, plan_doc, house)

    if worksheet:
        doc.add_paragraph(
            "Each layer gives you its question, the rows as they stand, and blank rows to fill. Work "
            "down in order — the channels are chosen for the audiences, and the measures for the "
            "channels. When you come back, open Plan → the layer → Add a row.")
        doc.add_page_break()
    if not plan_doc.get("house"):
        w = doc.add_paragraph()
        w.add_run("No messaging house attached — the proof gate cannot run, so any channel here "
                  "could have been given proof work it cannot deliver.").bold = True

    ev = status.get("house_evidence") or {}
    if ev:
        _heading(doc, "Evidence behind each pillar", level=2)
        doc.add_paragraph("This is what decides which channels may be given proof work.")
        for pillar in ("emotional", "functional"):
            pair = ev.get(pillar)
            if not pair:
                continue
            sourced, total = (list(pair) + [0, 0])[:2]
            line = doc.add_paragraph(style="List Bullet")
            line.add_run(f"{pillar.capitalize()}: {sourced} of {total} reasons-to-believe sourced")
            if not sourced:
                line.add_run("  — nothing to prove with").bold = True

    by_id = {l.get("id"): l for l in (status.get("layers") or [])}

    for layer in plan_mod.LAYERS:
        node = (plan_doc.get("nodes") or {}).get(layer["id"]) or {}
        _heading(doc, layer["label"], level=2)
        st = by_id.get(layer["id"]) or {}
        if st.get("stale"):
            doc.add_paragraph().add_run(
                "Stale — written against a different messaging house.").bold = True

        # The balance is a number with a claim attached, not a table.
        if layer["kind"] == "number":
            bal = status.get("balance") or plan_doc.get("balance") or {}
            declared = bal.get("brand_share", plan_mod.DEFAULT_BRAND_SHARE)
            act = bal.get("actual") or {}
            doc.add_paragraph(f"Declared: {declared}% brand / {100 - int(declared)}% activation")
            if act.get("brand") is None:
                doc.add_paragraph(f"Actual: not computable — {act.get('basis') or 'no channels yet'}")
            else:
                # The basis is printed verbatim. "spend unknown — computed on channel count" is a
                # materially weaker claim than a weighted one and must not be dressed up as equal.
                doc.add_paragraph(f"Actual from the channels: {act.get('brand')}% brand / "
                                  f"{act.get('activation')}% activation ({act.get('basis')})")
                if abs(int(act["brand"]) - int(declared)) >= 10:
                    doc.add_paragraph().add_run(
                        f"These disagree by {abs(int(act['brand']) - int(declared))} points. "
                        f"The behaviour is what will run.").bold = True
            reason = (bal.get("reason") or "").strip()
            if int(declared) != plan_mod.DEFAULT_BRAND_SHARE:
                doc.add_paragraph(f"Reason for moving off the {plan_mod.DEFAULT_BRAND_SHARE}% default: "
                                  + (reason or "not recorded"))
            doc.add_paragraph(f"Basis: {bal.get('basis') or 'year'}")
            continue

        rows = node.get("rows") or []
        cols = layer.get("cols") or []
        if worksheet:
            doc.add_paragraph().add_run(str(layer.get("asks") or "")).italic = True
        if not rows and not worksheet:
            doc.add_paragraph(f"Empty. {layer['asks']}")
            continue

        table = doc.add_table(rows=1, cols=len(cols))
        try:
            table.style = "Table Grid"
        except Exception:
            pass
        for i, c in enumerate(cols):
            cell = table.rows[0].cells[i]
            cell.text = _col(c)
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True
        for r in rows:
            cells = table.add_row().cells
            for i, c in enumerate(cols):
                val = str(r.get(c, "") or "").strip()
                # Empty is not zero. A blank cell in a printed table reads as settled, and there is no
                # tooltip in Word to say otherwise.
                if not val:
                    val = {"owner": "owner unknown", "measure": "no measure set",
                           "by_when": "no date set", "share": "share unknown",
                           "would_tell_us_it_failed": "failure not named",
                           "occasion": "no occasion named"}.get(c, "—")
                cells[i].text = val
        # Blank rows to fill in, in the same table so the columns line up with the real ones. Three,
        # because two invites a pair and five invites filler.
        if worksheet:
            for _ in range(3):
                for cell in table.add_row().cells:
                    cell.text = ""

        if layer["id"] == "channels":
            roles = status.get("roles") or plan_mod.ROLES
            note = doc.add_paragraph()
            run = note.add_run("Roles: " + "  ·  ".join(f"{k} — {v}" for k, v in roles.items()))
            run.italic = True
            run.font.size = Pt(8)

    _findings_section(doc, status.get("findings"), "plan")

    doc.add_page_break()
    _caveat_block(doc, strategy.ROUND_TRIP_CAVEAT, worksheet)

    out_path = out_path or os.path.join(tempfile.mkdtemp(prefix="plan_"), "communication_plan.docx")
    doc.save(out_path)
    return out_path


def build_callsheet_docx(shots: list, idea: dict | None = None,
                         out_path: str | None = None) -> str:
    """The shot list as a call sheet — the one document here that goes to a crew.

    So the rule is stricter than anywhere else: **nothing is filled in**. An unknown location prints
    *"location not set"*, not a guess and not a blank. A blank on a call sheet reads as "someone will
    tell me on the day"; a guess sends people to the wrong place. Both are expensive, and only one is
    obviously wrong when you read it.
    """
    from docx.shared import Pt
    idea = idea or {}
    doc = _new_doc("Call sheet")
    line = str(idea.get("line") or idea.get("idea") or "").strip()
    if idea.get("name") or line:
        p = doc.add_paragraph()
        if idea.get("name"):
            p.add_run(str(idea["name"])).bold = True
        if line:
            p.add_run(("  ·  " if idea.get("name") else "") + line).italic = True

    rows = [s for s in (shots or []) if isinstance(s, dict)]
    if not rows:
        doc.add_paragraph("No shots planned yet.")
        out_path = out_path or os.path.join(tempfile.mkdtemp(prefix="call_"), "call_sheet.docx")
        doc.save(out_path)
        return out_path

    cols = [("no", "#"), ("slug", "Shot"), ("action", "What happens"), ("talent", "Talent"),
            ("location", "Location"), ("length", "Length"), ("state", "State"), ("take", "Take")]
    table = doc.add_table(rows=1, cols=len(cols))
    try:
        table.style = "Table Grid"
    except Exception:
        pass
    for i, (_, label) in enumerate(cols):
        cell = table.rows[0].cells[i]
        cell.text = label
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True

    unset = {"talent": "nobody cast", "location": "no location", "length": "no length set",
             "action": "not written yet"}

    def _stage(s: dict) -> str:
        """Derived, because the row no longer stores it.

        This column used to read `s["state"]`, which is now computed rather than saved — so every row
        printed blank, including the signed ones. A call sheet that says nothing about where each shot has
        got to is the one document on a shoot where that matters.
        """
        if s.get("signed"):
            who = (s["signed"] or {}).get("who") or ""
            return f"signed{f' — {who}' if who else ''}"
        if s.get("selected_take"):
            return f"take {s['selected_take']} selected"
        if s.get("takes") or str(s.get("take") or "").strip():
            n = len(s.get("takes") or [])
            return f"{n} take{'s' if n != 1 else ''} logged" if n else "footage attached"
        if str(s.get("action") or "").strip() and str(s.get("ref") or "").strip():
            return "briefed"
        return "planned"

    def _take(s: dict) -> str:
        """The take NUMBER, never the url. `take` holds a path now, and a call sheet is read on paper."""
        if s.get("selected_take"):
            return str(s["selected_take"])
        nums = [str(t.get("n")) for t in (s.get("takes") or []) if t.get("n")]
        return ", ".join(nums) if nums else "—"

    for s in rows:
        cells = table.add_row().cells
        for i, (key, _) in enumerate(cols):
            if key == "state":
                val = _stage(s)
            elif key == "take":
                val = _take(s)
            else:
                val = str(s.get(key, "") or "").strip() or unset.get(key, "—")
            cells[i].text = val

    sel = [s for s in rows if s.get("state") == "selected"]
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run(f"{len(sel)} of {len(rows)} shots selected.").bold = True
    gaps = [s.get("slug") or f"shot {s.get('no')}" for s in rows
            if not str(s.get("location") or "").strip() or not str(s.get("talent") or "").strip()]
    if gaps:
        g = doc.add_paragraph()
        r = g.add_run("Still to be decided before this can be shot: " + ", ".join(gaps))
        r.italic = True
        r.font.size = Pt(9)

    out_path = out_path or os.path.join(tempfile.mkdtemp(prefix="call_"), "call_sheet.docx")
    doc.save(out_path)
    return out_path


def build_script_docx(title: str, logline: str, scenes: list, out_path: str | None = None) -> str:
    """A shooting-script document: logline + one table row per scene."""
    doc = _new_doc(title or "Film Script")
    if logline:
        p = doc.add_paragraph()
        p.add_run("Logline: ").bold = True
        p.add_run(logline)
    scenes = scenes or []
    if scenes:
        cols = ["Scene", "Visual / Action", "Camera", "Dialogue / VO", "Super"]
        table = doc.add_table(rows=1, cols=len(cols))
        try:
            table.style = "Table Grid"   # guaranteed present in python-docx's default template
        except Exception:
            pass
        for i, c in enumerate(cols):
            cell = table.rows[0].cells[i]
            cell.text = c
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True
        for sc in scenes:
            if not isinstance(sc, dict):
                continue
            row = table.add_row().cells
            scene_no = str(sc.get("no", "") or "")
            tc = str(sc.get("tc", "") or "")
            row[0].text = (f"{scene_no}\n{tc}" if tc else scene_no)
            row[1].text = str(sc.get("visual", "") or "")
            row[2].text = str(sc.get("camera", "") or "")
            row[3].text = str(sc.get("dialogue", "") or "")
            row[4].text = str(sc.get("supr", "") or "")
    else:
        doc.add_paragraph("No scenes yet — write the full script first.")
    out_path = out_path or os.path.join(tempfile.mkdtemp(prefix="script_"), "script.docx")
    doc.save(out_path)
    return out_path
