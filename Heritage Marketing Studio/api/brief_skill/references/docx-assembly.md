# DOCX Assembly Contract

The skill assembles the final `.docx` by writing a `brief.json` file alongside the two figure PNGs, then invoking the parameterised Node script `assets/build_brief_docx.js`. The script reads `brief.json`, embeds the figures, and writes the `.docx` to the workspace.

## brief.json schema

```json
{
  "brand": "Parle-G",
  "prepared_for": "Parle Products Pvt. Ltd. (Parle-G brand team)",
  "date": "14 May 2026",
  "sources_note": "Public company communications, packaging, retail channels, press coverage, and review/social sentiment. Quantitative share figures should be validated against the latest Nielsen/Kantar reads before publication.",

  "executive_summary": [
    "First paragraph of the executive summary...",
    "Second paragraph that calls out the NeedScope read and the SMP..."
  ],

  "smp": "Parle-G is India's most affordable act of ambition.",

  "competitors": [
    {
      "name": "Britannia",
      "hero_brands": "Tiger, Marie Gold, Good Day, NutriChoice",
      "positioning": "Portfolio play — a biscuit for every occasion and price point",
      "recent_moves": "Deeper Hindi-belt distribution; fortification push; IPL-heavy media"
    }
  ],

  "messaging_matrix": {
    "dimensions": ["Tagline", "Target buyer", "Key differentiator", "Tone", "Core value prop"],
    "brands": ["Parle-G", "Britannia Tiger", "Sunfeast (mother)", "Patanjali", "Priya Gold"],
    "cells": [
      ["\"G for Genius\"", "\"Power ka asli pack\"", "..."],
      ["Mass household, all India", "Kids + value mass-market", "..."]
    ]
  },

  "needscope": {
    "figure_path": "needscope_filled.png",
    "reading": "Parle-G owns Belonging (Green) at mass uncontested...",
    "strategic_implication": "Don't chase the claimed poles..."
  },

  "cb_ca_db_da": {
    "figure_path": "cbca_dbda_filled.png",
    "shift_line": "From passive trust to active pride.",
    "caption": "Layer ambition on top of belonging — never replace it. Green anchor stays; Red thread is added."
  },

  "smp_defence": [
    { "competitor": "Britannia Tiger", "why_collapses": "Claims power but at ₹5 cannot earn \"ambition\" — its register is strength, not striving." },
    { "competitor": "Sunfeast Dark Fantasy", "why_collapses": "Claims indulgence but at ₹30+ cannot be \"affordable\"." }
  ],

  "smp_unlocks": {
    "brand_line": "\"G for Genius. Always was.\"",
    "mass_line": "\"Bharat ka ₹5 ka spark.\"",
    "activation": "Parle-G Genius Scholarship + exam-season platform.",
    "product": "Fortified Parle-G Genius variant at ₹10."
  },

  "snapshots": {
    "pricing": "Paragraph on pricing landscape with the implication for the focal brand.",
    "distribution": "Paragraph on distribution gaps and strengths.",
    "content_campaigns": "Paragraph on content / campaign activity.",
    "content_gaps": "Paragraph on the content gaps the focal brand should claim."
  },

  "opportunities_threats": [
    { "opportunity": "Reclaim everyday energy via fortified variant", "threat": "Tiger closing the rural distribution gap" }
  ],

  "recommendations": {
    "preface": "All actions ladder to the SMP and respect the NeedScope discipline — Green anchor stays, one Red thread added.",
    "quick_wins": [
      "Launch a 'G for Genius' exam-season creator content slate.",
      "Audit and fix quick-commerce listings within 60 days.",
      "Run a competitive grammage and shelf-price audit across the top 50 SKUs."
    ],
    "strategic_moves": [
      "Launch Parle-G Genius — fortified variant at ₹10.",
      "Build the Parle-G Genius Scholarship/Fund.",
      "Develop a premium-glucose proposition.",
      "Codify a sustainability roadmap.",
      "Stand up an always-on creator programme."
    ]
  },

  "caveats": "Built from publicly available context and category memory. Before externalising, validate (a) latest market-share figures, (b) current pricing and grammage at each price point, (c) most recent campaign activity, and (d) any regulatory action affecting any of the named competitors."
}
```

## Running the build

```bash
cd <workspace> && node assets/build_brief_docx.js brief.json <output_path>.docx
```

The script:

- Forces page size US Letter (12240 × 15840 DXA).
- Uses 0.75" margins (1080 DXA) on all sides.
- Sets default body to Arial 11pt.
- Sets H1 to Arial 14pt bold dark-grey (`#2A2A2A`); H2 to Arial 12pt bold green (`#3F814C`).
- Uses `LevelFormat.BULLET` for bullets and `LevelFormat.DECIMAL` for numbered items.
- Sets table column widths in DXA summing to 9360 (page content width with 0.75" margins ... actually 12240 - 2*1080 = 10080; the script uses 10080).
- Uses `ShadingType.CLEAR` (never SOLID) for table header shading.
- Adds cell margins `{ top: 80, bottom: 80, left: 120, right: 120 }`.
- Embeds the two figure PNGs as `ImageRun` with `type: "png"` and resolved alt text.
- Renders the SMP as a green-bordered centred callout.
- Adds a footer "Brand Brief · Page X of Y" — centred.

## Verification

After the script returns successfully:

```bash
python3 /sessions/.../mnt/.claude/skills/docx/scripts/office/validate.py <output_path>.docx
python3 /sessions/.../mnt/.claude/skills/docx/scripts/office/soffice.py --headless --convert-to pdf <output_path>.docx
pdftoppm -jpeg -r 110 <output_path>.pdf brief_page
```

Then visually inspect at least pages 1, 2, and 3 to confirm:

- Both figures are present and crisp.
- The SMP is rendered as a green-bordered callout.
- Table columns do not overflow.
- Page count is 5–7.

Only after these checks present the file to the user with a `computer://` link.
