# Input Parsing

How to read each file type the user might upload, and what data to extract.

## File type → parser

| File type | Tool | Notes |
|---|---|---|
| PNG / JPG (NeedScope chart, screenshots) | Built-in vision via Read tool | Read the file directly; the tool returns the image to Claude for visual inspection |
| PDF (NeedScope reports, brand docs, research) | `pdfplumber` for text, `pdf2image` + vision for chart pages | Install: `pip install pdfplumber pdf2image --break-system-packages` (and `poppler-utils` for pdf2image) |
| PPTX (competitor decks, NeedScope slides) | `python-pptx` for text, render via `soffice --convert-to png` for chart slides | Install: `pip install python-pptx --break-system-packages` |
| DOCX (brand strategy docs, briefs) | `pandoc` or `extract-text` (from docx skill) for text; `python-docx` for tables | The system already has the docx skill installed |
| XLSX (market share, HH data) | `openpyxl` or `pandas.read_excel` | Install: `pip install openpyxl pandas --break-system-packages` |
| CSV (market share, HH data) | `pandas.read_csv` | Standard |
| TXT / MD (qualitative notes) | Built-in Read tool | No parser needed |

## What to extract from each

### NeedScope chart image (PNG, JPG, PDF slide, PPTX slide)

Inspect with vision and produce a structured table:

```
| Brand | Territory (Power/Freedom/Vitality/Belonging/Security/Discernment) | Pull direction (or "centred") | Approximate position on chart |
|-------|-------------------------------------------------------------------|-------------------------------|------------------------------|
| ... | ... | ... | ... |
```

Use this table to populate the wheel rather than inferring from communications.

If the chart shows numerical scores rather than pin positions, convert: largest score → primary territory; second largest → pull direction.

### Market-share spreadsheet (XLSX, CSV)

Expect columns like:

- Brand
- Value share (%)
- Volume share (%)
- Year-on-year growth
- Region (optional)
- Channel (optional)

Extract the latest period's value share and volume share per brand, plus YoY growth. Use these numbers verbatim in the Competitor Snapshot and Pricing/Distribution sections.

If the schema is unusual, parse the header row to identify columns by keyword (`share`, `growth`, `value`, `volume`, `region`).

### HH consumption / penetration data (XLSX, CSV)

Expect columns like:

- Brand or Category
- Household penetration (%)
- Frequency of purchase (per HH per year)
- Average spend per HH
- Demographic cuts (urban/rural, NCCS, age band)
- Occasion (chai-time, breakfast, snacking, etc.)

Use this to:

- Identify occasions where the focal brand under-indexes — these become DB targets.
- Identify demographic segments where penetration is lowest — these inform the "Opportunities" section.
- Confirm or refute hypotheses about reflex purchase and habit (high frequency + low spend often signals habit, not choice).

### Brand strategy doc (PDF, DOCX)

Extract:

- Current positioning statement.
- Current taglines and brand lines.
- Stated values, vision, mission.
- Brand voice notes.
- Any historical NeedScope or archetype work.

Use these as the authoritative source for current state in the messaging matrix and the CA cell.

### Competitor deck (PPTX)

Extract per slide:

- Slide title (a heading often reveals positioning hierarchy).
- Body text per shape.
- Speaker notes (often contain the strategic intent).
- Image alt text or shape names (sometimes hint at category framing).

Mine for: taglines, claimed differentiators, target audience descriptions, feature emphasis, recent campaign references.

### Qualitative research notes (TXT, MD, DOCX, PDF)

Extract:

- Verbatim consumer quotes — store under emotional tags (love, frustration, indifference, aspiration).
- Recurring phrases — these often become the CA verbatim quote.
- Behavioural anecdotes — these populate CB.
- Stated aspirations — these populate DA.

Never paraphrase verbatim quotes. The CA quote in the framework must be a real consumer voice, character-for-character if possible. If only a paraphrase is available, mark it `[paraphrased]`.

## Cross-input reconciliation

When multiple inputs cover the same fact, apply this precedence:

1. The user's NeedScope chart (for NeedScope positions only).
2. The user's market-share data (for share, growth, distribution numbers).
3. The user's HH data (for penetration, frequency, occasion data).
4. The user's brand docs (for positioning, taglines, values, voice).
5. The user's competitor decks (for competitor positioning, taglines).
6. The user's qualitative notes (for verbatim quotes and anecdotes).
7. Web research (for everything not covered above).

If two sources at the same precedence level disagree, choose the more recent and flag the conflict in the Caveats section.

## Sandbox setup once at the start of a run

```bash
pip install pdfplumber python-pptx openpyxl pandas cairosvg pdf2image --break-system-packages -q
```

Node side (for the docx build script):

```bash
cd /sessions/.../mnt/outputs && npm install docx --silent
```

Only install dependencies that are actually needed for the inputs the user has uploaded — do not install all of them every time.
