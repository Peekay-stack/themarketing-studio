# Frontend delivery note — Heritage Marketing Studio

**To:** Claude Code · **From:** Claude Design · **Re:** frontend changes requested from end-to-end testing
**Entry point:** `Heritage Studio.dc.html` (readable source) · standalone build: `Heritage Marketing Studio.html`

Everything below is built and verified in the browser. Backend is not wired yet — every call is a plain
relative `fetch()` that degrades gracefully, so the whole app is usable today and lights up as you
implement the endpoints in `CLAUDE_CODE_BACKEND_PROMPT.md`.

---

## 1. Video Studio — rebuilt as a gated 4-step pipeline

Requested: separate concept from a real shootable script, make the storyboard real, ground the shoot
board in the approved script, and gate production.

| Step | What it does |
|---|---|
| **1 Brief** | Shows the linked brief / objective as context |
| **2 Scripting** | Two phases (below) |
| **3 Shoot Board** | Locked until the script is approved |
| **4 Production** | Locked until the script is approved |

Live status badges on every step; clicking a locked step explains why via a toast.

**Phase 1 — Concept.** Objective chips + `✦ Generate concept`, a logline/cut/VO hero card, an
iterate-on-the-concept prompt with version history. Generating a concept no longer marks the step done.

**Phase 2 — Full script.** `✦ Write full script` produces an inline-editable table — one row per scene:
scene + timecode, visual/action, camera, dialogue/VO (English + Hinglish where natural), and on-screen
supers, with the final row landing on the pack-shot super *"Heritage — Pure Doodh Ki Shakti"*. Per-scene
`↻ Rewrite scene`, `↻ Regenerate full script`, and `⬇ Download script (Word)`. **`Approve script`** only
appears once a script exists, and it is what unlocks steps 3 and 4.

**Storyboard / Key Shots.** Real frame slots calling `POST /scene-still` — per-card generate,
`✦ Generate all frames`, per-frame status dots, click-to-enlarge lightbox, quiet Retry on failure.
Frames are shared state, so the Scripting storyboard and the Shoot Board strip are the same artifacts.

**Shoot Board.** Six department cards (Cast, Location, Lighting, Music, Dialogue/VO, Key Shots) whose AI
drafts are grounded in the approved script, plus a collapsible read-only script reference.

**Production.** Pre-flight checklist (script approved · frames rendered · aspect · duration),
`POST /produce-video` with an inline player and `⬇ Download MP4`, render history, and Word script export.

---

## 2. Briefs — three formats merged into one IMC Brief

Requested: fold Brand Strategy + Communications + IMC into a single **IMC Brief**, build the brand-brief
skill into the app, and replace the data-entry builder with one calm guided screen.

- **Briefs landing** — a single primary **IMC Brief** hero card (accent border, `skill` tag) above a
  quieter row of the five untouched formats: Media, Digital, Packaging, Product, PR.
- **The "Guided vs Comprehensive" mode toggle is gone.**
- **IMC Brief screen**
  - *Card A — Describe the brief*: large prompt textarea, brand / category / prepared-for, the gold hero
    **`✦ Draft brief with AI`** button with inline status, and an "Or fill it in manually" escape.
  - *Card B — Add your inputs*: five labelled slots (market share & sales, household data, NeedScope
    wheel, CB/CA chart, research & decks) with removable file chips and client-side spreadsheet parsing
    that reports `sheet · N rows parsed`.
  - *Review & refine*: four tabs, everything AI-drafted and fully editable —
    **Brand & competitors** (editable competitor table, add/remove rows) ·
    **NeedScope wheel** (real 800×640 chart, six territories clockwise from 12, select a pin chip and
    click to place it, bridge-territory chips, bridge platform, reading) ·
    **CB/CA → DB/DA** (Current grey / Desired green cards, behaviour bullets, attitude quotes,
    declaratives, the shift and caption) ·
    **Single Minded Proposition** (green-bordered callout, "why only this brand can say it" table,
    four *illustrative* unlocks).
  - *Sticky footer*: **`Generate IMC brief (.docx)`** plus `Preview JSON` / `Download brief.json`.
- **All required states wired:** idle · drafting ("Running the brand-brief skill…") · draft ready ·
  **HTTP 400 → amber "needs an Anthropic API key… you can still fill it in manually"** · error ·
  generating. Manual editing is never blocked.
- Guided builder for the other five formats is unchanged, and now shows a single current-format pill with
  a "Change format" link instead of the old chip row.

---

## 3. Cross-app changes

- **Word export everywhere** — `⬇ Download Word` on the brief review screen and the brief editor footer
  (`POST /brief-docx`), `⬇ Download script (Word)` in the Video Studio, and
  `Generate IMC brief (.docx)` on the IMC screen. Each falls back to a locally-built `.doc` so the user
  always gets a document.
- **Prompt guide dropdowns** — collapsible `Prompt guide ▾` with an empty container for you to populate on
  six surfaces: `imc` (Card A of the IMC screen — the primary prompt surface), `briefs`, `social`,
  `video`, `builder`, `editor`.
- **Consistent AI buttons** — green fill to create, white outline to regenerate, gold for the one hero
  action per screen.
- **Non-blocking toast** for guard rails (empty prompt, locked step) instead of alerts.
- **Graceful degradation everywhere** — no endpoint, no key, or a bad file never produces a blank screen.

---

## 4. Two bugs found and fixed during testing

1. **Unresolved template holes in `src` attributes** were firing literal fetches for
   `{{ sc.frameUrl }}`, `{{ lightbox }}` and `{{ producedUrl }}` before hydration, which also broke the
   standalone bundle. Those images and the video player are now pre-built elements that only exist once a
   real URL does.
2. **SVG `<text>` cannot host a template hole** — the runtime wraps values in a `<span>`, which SVG can't
   lay out, so the NeedScope territory and pin labels rendered as zero-size invisible nodes. They are now
   built as real SVG text nodes and are confirmed laying out correctly.

---

## 5. Files in this handover

| File | What it is |
|---|---|
| `Heritage Studio.dc.html` | The frontend source — the file to serve and to edit |
| `Heritage Marketing Studio.html` | Self-contained standalone build (may lag the source; regenerate on request) |
| `support.js`, `image-slot.js`, `assets/` | Runtime files the page loads |
| `CLAUDE_CODE_BACKEND_PROMPT.md` | **The prompt to work from** — endpoint contracts, data keys, guardrails |
| `BACKEND_HANDOFF.md` | Fuller reference: field keys, section sets, sample-data arrays |
| `FRONTEND_DELIVERY.md` | This note |

**Endpoints to implement:** `/complete`, `/brand-brief-draft`, `/brand-brief`, `/brief-docx`,
`/scene-still`, `/produce-video`, `/video-script-docx`.
