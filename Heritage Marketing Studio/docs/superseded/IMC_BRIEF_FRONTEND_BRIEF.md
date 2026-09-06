# Design brief — Heritage Marketing Studio: the IMC Brief flow

**For:** Claude Design (rebuild the brief experience as a simple, clean, intuitive GUI)
**Scope:** The brief-creation experience only. Leave Social / Video / Campaign / Insights studios as they are.
**Goal:** Replace the old, over-complicated brief builder with **one calm, guided screen** where a marketer describes the brief, drops in a few files, lets the built-in **brand-brief skill draft everything**, reviews/edits, and downloads a Word document.

---

## 1. Why this redesign

The old portal had **eight brief formats** and, for brand/comms/IMC, a heavy manual builder: the user had to hand-place every NeedScope pin, type every CB/CA quadrant, and write the SMP themselves, plus a confusing "Guided vs Comprehensive" mode toggle. It felt like data-entry, not thinking.

Two changes drive this redesign:

1. **Three briefs became one.** *Brand Strategy + Communications + IMC* are now a single **"IMC Brief."** (Media, Digital, Packaging, Product, PR stay as separate, simpler formats — do not touch them.)
2. **The brand-brief "skill" is now built into the app.** The user gives a **prompt + files**, and the server runs the skill (Claude) to **draft the entire brief** — competitors, NeedScope positioning, CB/CA → DB/DA shift, and the Single Minded Proposition. The user then **reviews and edits** before generating the Word file.

So the mental model shifts from *"fill in 6 tabs of fields"* to *"describe it → AI drafts it → you refine it → download."*

---

## 2. Design principles

- **One primary path, one primary button.** The hero action is *Draft brief with AI*. Everything else is secondary.
- **Progressive disclosure.** Show the prompt + uploads first. Reveal the detailed sections (competitors, wheel, shift, SMP) only after a draft exists — as a *review*, not a blank form.
- **AI drafts, human owns.** Every AI-generated value must be visibly editable. Never make the user feel locked out of a field.
- **Calm, editorial, confident.** Lots of whitespace, few borders, warm paper background. This is a strategy tool, not a dashboard.
- **Never a dead end.** If the API key is missing or a file won't parse, say so plainly and let the user continue manually.

---

## 3. The end-to-end flow (happy path)

```
Home  →  [IMC Brief]  →  Brief screen
                           │
                           ├── 1. Prompt (what's the brief?)
                           ├── 2. Add files (market share, household, NeedScope wheel, CB/CA, research)
                           │
                           ▼
                     [✦ Draft brief with AI]   ← hero action, calls the skill
                           │  (spinner: "Running the brand-brief skill…")
                           ▼
                     3. Review & refine  (AI-filled, all editable)
                           ├── Brand & competitors
                           ├── NeedScope wheel (pins placed by AI, draggable/clickable)
                           ├── CB/CA → DB/DA
                           └── Single Minded Proposition
                           │
                           ▼
                     [Generate IMC brief (.docx)]  → downloads the Word file
```

The user can also **skip the AI draft** and fill the review sections manually — same screen, same fields.

---

## 4. Screen-by-screen spec

### 4.1 Home — brief formats
- A row of format cards. **"IMC Brief" is first and visually primary** (largest / accent border), tagged `skill`. The others (Media, Digital, Packaging, Product, PR) are smaller, secondary.
- IMC Brief card copy: *"The one strategy brief — prompt, data & files in, a Word brand brief out. NeedScope + CB/CA → DB/DA + SMP, drafted for you."*
- Clicking **IMC Brief** opens the Brief screen below.

### 4.2 Brief screen — top: Prompt + Files (always visible)
Two stacked cards, generous spacing.

**Card A — "Describe the brief" (the prompt)**
- One large textarea. Placeholder: *"e.g. Diwali IMC push for Pure Milk targeting young urban families — move from a trusted daily staple to the pure strength families actively choose, across TV, digital, retail and PR."*
- Small helper line under it: *"This anchors the whole brief. Add files below, then let the skill draft it."*
- **Hero button: `✦ Draft brief with AI`** + inline status text to its right.
- Tiny note: *"Runs the brand-brief skill on your prompt + files. Needs an Anthropic API key on the server."*

**Card B — "Add your inputs" (uploads)** — four clearly-labelled drop zones + one catch-all:
| Slot | Accepts | Note |
|---|---|---|
| **Market share & sales** | .xlsx, .csv | Used verbatim in competitor / pricing sections |
| **Household data** | .xlsx, .csv | Penetration / consumption; sizes the audience & shift |
| **NeedScope wheel** | .png, .jpg, .pdf | Optional — if you already have one, the AI reads its positions |
| **CB/CA → DB/DA** | .png, .jpg, .pdf | Optional reference chart |
| **Research & decks** | .pdf, .pptx, .docx | Mined for verbatim consumer quotes & positioning |
- Show uploaded files as removable chips. Spreadsheets show a tiny parsed-rows preview.

### 4.3 Brief screen — Review & refine (appears after a draft, or when manual)
Present the four sections as **tabs or a single scroll** — designer's call, but keep it light. Each is pre-filled by the AI and fully editable:

1. **Brand & competitors** — focal brand, category, "prepared for", date; an editable competitor table (name, hero brands, positioning, recent moves).
2. **NeedScope wheel** — the six-territory colour wheel with brand pins the AI placed. User can click/drag to reposition, pick the strategic-bridge territory, and name the bridge platform. Include a short editable "reading" line.
3. **CB/CA → DB/DA** — two cards side by side: **Current** (grey) and **Desired** (green-tinted). Each holds Behaviour bullets + an Attitude quote + two declarative lines. A "the shift" line (from → to) and a one-sentence caption.
4. **Single Minded Proposition** — one green-bordered callout sentence; a "why only this brand can say it" table (per competitor); and four "what it unlocks" lines (brand line, mass line, activation, product) tagged *illustrative*.

**Footer of the screen (sticky):** `Generate IMC brief (.docx)` primary button, plus secondary `Preview JSON` / `Download brief.json` for power users.

### 4.4 States to design
- **Idle** (no draft yet): review sections collapsed or shown as an empty, inviting outline.
- **Drafting**: hero button shows a spinner; status = *"Running the brand-brief skill…"*; review area shows a skeleton.
- **Draft ready**: green status *"Draft ready — review each tab, then Generate."* Sections fill in.
- **No API key** (HTTP 400 from `/brand-brief-draft`): amber inline message — *"AI drafting needs an Anthropic API key on the server. You can still fill the brief in manually."* Do **not** block manual editing.
- **Generating docx**: primary button spinner *"Building your Word brief…"*; then a success line with the downloaded filename.
- **Error**: red inline message with the server's reason; never a blank failure.

---

## 5. Backend contracts (wire the UI to these — do not change them)

The app is a FastAPI server; the front end is served from `/`. Two endpoints matter:

### `POST /brand-brief-draft` — run the skill to draft the brief
`multipart/form-data`:
- `payload` = JSON string:
  ```json
  {
    "brand": "Heritage", "category": "Indian dairy", "prepared_for": "…",
    "prompt": "the marketer's ask",
    "market_data":   { "sheet": "…", "rows": [[...], ...] } | null,
    "household_data":{ "sheet": "…", "rows": [[...], ...] } | null
  }
  ```
  *(Spreadsheets are parsed client-side into `rows` before sending — reuse the SheetJS/xlsx approach.)*
- `research` = the uploaded files (repeat the field). Images (NeedScope/CB-CA) are read by the AI via vision; docs/sheets are parsed server-side.

**Returns** the builder payload to populate the review sections:
```json
{
  "brand": "…", "category": "…", "prepared_for": "…",
  "competitors": [{ "name","hero_brands","positioning","recent_moves" }],
  "needscope": {
    "pins": [{ "brand","x","y","anchor" }],          // x/y on the 800×640 wheel; one anchor:true
    "bridge_territory": "Belonging", "bridge_label": "Pure Doodh Ki Shakti",
    "reading": "…"
  },
  "cb_ca_db_da": {
    "cb": ["…"], "db": ["…"],
    "ca_quote": "…", "ca_declarative": ["…","…"],
    "da_quote": "…", "da_declarative": ["…","…"],
    "shift_from": "…", "shift_to": "…", "caption": "…"
  },
  "smp": "One sentence.",
  "smp_defence": [{ "competitor","why_collapses" }],
  "smp_unlocks": { "brand_line","mass_line","activation","product" }
}
```
On no key → HTTP 400 with `{ "detail": "…add ANTHROPIC_API_KEY…" }`.

### `POST /brand-brief` — render the reviewed brief to Word
`multipart/form-data`:
- `payload` = JSON string: the **same builder payload** the review sections hold, PLUS `date`, `sources_note`, `market_data`, `household_data`, and a derived `needscope.reading` and `cb_ca_db_da.shift_line` (`"From {from} to {to}."`).
- `research` = the same uploaded files.

**Returns** the `.docx` (stream it to a download). Filename: `{brand}_IMC_Brief.docx`.

### NeedScope wheel geometry (for placing/reading pins)
Canvas **800×640**, centre **(400, 320)**. `x = 400 + r·cos(θ)`, `y = 320 + r·sin(θ)` (θ in degrees).
Territory centre angles: **Power 270, Freedom 330, Vitality 30, Belonging 90, Security 150, Discernment 210.** Radii: anchor ≈125, competitors ≈140, fringe ≈150. Territories clockwise from 12 o'clock: **Power · Freedom · Vitality · Belonging · Security · Discernment** — never reorder.

---

## 6. Visual system (keep on-brand)

- **Palette:** deep green `#14331F` (ink/primary), leaf green `#3F814C` (accent, headings, SMP border), gold `#E8A93C` (hero action), cream `#FBF6EA` (page background), paper `#FFFFFF` (cards), warm line `#ECE3CE`, muted text `#7A8A7E`.
- **NeedScope territory colours:** Power `#E8736A`, Freedom `#E89A4E`, Vitality `#E8C547`, Belonging `#5BA86B`, Security `#4F8AC9`, Discernment `#9A6BB8`.
- **Type:** Headings `Bricolage Grotesque`; body/UI `Plus Jakarta Sans`. Generous line-height, sentence case everywhere (never Title Case).
- **Shape:** 14–16px card radius, soft 1px `#ECE3CE` borders, very light shadow. Rounded 10–12px inputs/buttons.
- **Buttons:** primary = green fill / cream text; hero (Draft) = gold fill / dark text with a ✦; secondary = white / green text / hairline border.
- **Tone of copy:** warm, plain, confident. No jargon in the chrome. Emoji only the single ✦ on the Draft button.

---

## 7. Explicitly remove / avoid

- The separate **Brand Strategy** and **Communications** format cards (folded into IMC Brief).
- The **"Guided vs Comprehensive" mode toggle** — gone.
- Any flow that asks the user to build the analysis *before* seeing an AI draft. Manual editing lives in **Review**, not as the front door.
- Dense multi-column forms, tiny labels, or anything that reads as data-entry.

---

## 8. Accessibility & responsiveness

- Works at mobile / tablet / desktop widths; sections stack gracefully; the wheel scales and stays usable (tap to place on touch).
- All controls keyboard-reachable; visible focus rings; inputs have real `<label>`s.
- Colour is never the only signal (icons/text back up the Current/Desired and status states).
- Wide content (competitor table, wheel) scrolls inside its own container — the page never scrolls sideways.

---

## 9. One-paragraph summary to paste at the top of the design prompt

> Redesign the Heritage Marketing Studio brief experience into a single, calm "IMC Brief" flow. The user writes a short prompt and drops in a few files (market share, household data, an optional NeedScope wheel and CB/CA chart, research), then presses one hero button — **Draft brief with AI** — which calls the server's brand-brief skill and fills in the whole brief: competitors, a NeedScope positioning wheel, a CB/CA → DB/DA shift, and a Single Minded Proposition. The user reviews and edits everything in place, then presses **Generate IMC brief (.docx)** to download a Word document. Warm, editorial, on-brand (Heritage greens, cream paper, Bricolage Grotesque headings). One primary path, one hero action, progressive disclosure, and never a dead end when the API key or a file is missing.
