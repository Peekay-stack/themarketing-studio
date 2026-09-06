"""research_parse.py — extract text from uploaded research files for the brand brief.

Follows the skill's input-parsing rules: PDF via pdfplumber, DOCX via python-docx,
PPTX via python-pptx (text + speaker notes), XLSX via openpyxl, CSV/TXT/MD as text.
Returns a list of {filename, kind, text} blobs, each capped so the prompt stays bounded.
"""
from __future__ import annotations

import csv
import os

PER_FILE_CHARS = 8000  # cap per file so the enrichment prompt stays bounded


def _cap(s: str) -> str:
    s = (s or "").strip()
    return s[:PER_FILE_CHARS]


def _pdf(path: str) -> str:
    import pdfplumber
    out = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:30]:
            out.append(page.extract_text() or "")
    return "\n".join(out)


def _docx(path: str) -> str:
    import docx
    d = docx.Document(path)
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    for t in d.tables:
        for row in t.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n".join(parts)


def _pptx(path: str) -> str:
    from pptx import Presentation
    prs = Presentation(path)
    parts = []
    for i, slide in enumerate(prs.slides, 1):
        parts.append(f"[Slide {i}]")
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                parts.append(shape.text_frame.text)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            note = slide.notes_slide.notes_text_frame.text.strip()
            if note:
                parts.append(f"(notes) {note}")
    return "\n".join(parts)


def _xlsx(path: str) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    parts = []
    for ws in wb.worksheets[:4]:
        parts.append(f"[Sheet {ws.title}]")
        for r in ws.iter_rows(values_only=True):
            cells = [str(c) for c in r if c is not None]
            if cells:
                parts.append(" | ".join(cells))
            if len(parts) > 200:
                break
    return "\n".join(parts)


def _csv(path: str) -> str:
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        rows = list(csv.reader(f))
    return "\n".join(" | ".join(r) for r in rows[:200])


def _text(path: str) -> str:
    return open(path, encoding="utf-8", errors="ignore").read()


_DISPATCH = {
    ".pdf": ("pdf", _pdf), ".docx": ("brand/qual doc", _docx), ".doc": ("brand/qual doc", _docx),
    ".pptx": ("competitor deck", _pptx), ".xlsx": ("data", _xlsx), ".xls": ("data", _xlsx),
    ".csv": ("data", _csv), ".txt": ("qual notes", _text), ".md": ("qual notes", _text),
}


def table_rows(path: str, limit: int = 500) -> dict:
    """A spreadsheet as ROWS, not as flattened text.

    `_xlsx` and `_csv` above join every row with " | " because their consumer is a model reading prose.
    A geography-and-budget sheet is not prose: the columns carry the meaning, and re-splitting the
    flattened string would be a second parser guessing where a cell containing " | " ended.

    Returns `{"kind": "table"|"text", "rows": [[...]], "sheet": str, "text": str, "why": str}`.
    `kind` is "text" for anything that is not a spreadsheet — a deck or a PDF has no rows to map, and
    saying so is better than returning one row per paragraph and calling it a table.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        rows = []
        for r in ws.iter_rows(values_only=True):
            cells = ["" if c is None else str(c).strip() for c in r]
            if any(cells):
                rows.append(cells)
            if len(rows) >= limit:
                break
        return {"kind": "table", "rows": rows, "sheet": ws.title, "text": "",
                "why": "" if rows else "The first sheet has no rows with anything in them."}
    if ext == ".csv":
        with open(path, newline="", encoding="utf-8", errors="ignore") as f:
            rows = [[(c or "").strip() for c in r] for r in csv.reader(f)]
        rows = [r for r in rows if any(r)][:limit]
        return {"kind": "table", "rows": rows, "sheet": "", "text": "",
                "why": "" if rows else "That CSV has no rows with anything in them."}
    blob = parse_file(path)
    return {"kind": "text", "rows": [], "sheet": "", "text": blob.get("text", ""),
            "why": (f"{blob.get('kind', 'that file')} carries prose, not rows — there are no columns "
                    f"to map to cells. The text is handed over for reading instead.")}


def parse_file(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    kind, fn = _DISPATCH.get(ext, ("unknown", None))
    if fn is None:
        return {"filename": os.path.basename(path), "kind": "unsupported", "text": ""}
    try:
        text = _cap(fn(path))
    except Exception as e:
        text = f"[could not parse: {e}]"
    return {"filename": os.path.basename(path), "kind": kind, "text": text}


def parse_paths(paths: list[str]) -> list[dict]:
    return [parse_file(p) for p in paths if p]
