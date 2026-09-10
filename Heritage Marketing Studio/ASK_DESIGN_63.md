# ASK_DESIGN_63 — landing.html: two mobile refinements (hero visual + Human-gate icons)

## Base file — confirm before you start

- File: **`landing.html`** (repo root) — identical to `Heritage Marketing Studio/api/static/landing.html` (what the live site serves).
- Base commit: **`25b2853`** (`Peekay-stack/themarketing-studio`, `master`). This is your ASK_DESIGN_62 output, now merged in. **Diff your working copy against `25b2853` first** and re-apply the changes below — don't drop a whole file in.

CSS only. Mobile only (`≤ 760px`). No markup, no copy, no desktop changes.

Both changes go **inside the existing `@media (max-width: 760px)` block** (the "collapse the desktop full-screen deck" block, currently the last thing before `</style>`), or in a second `@media (max-width: 760px)` block appended right after it — either is fine as long as it's after everything else in the stylesheet.

---

## 1. Hero visual — stop splitting the diagram and its legend across two scroll frames

**Where:** the `.hero-visual` block inside `#home` and `#hero` (the animated layered-diamond `<svg>` + the `.os-legend` list beside it).

**Now (mobile):** the existing `@media (max-width: 640px)` rule sets `.hero-visual { flex-direction: column }`, so the diamond diagram stacks *above* a 6-row legend. Together they run ~450px, and with the headline/lede/buttons above them the diagram lands on one scroll position and the legend on the next — they stop reading as one object.

**Want:** on `≤ 760px`, put the diagram and the legend **side by side** (diagram left, legend right), sized so the whole `.hero-visual` is a single compact block (aim ≲ 260px tall) that reads as one unit — the layered OS with its labels.

**Starter CSS — tune the exact sizes by eye:**

```css
  @media (max-width: 760px) {
    #home .hero-visual, #hero .hero-visual {
      flex-direction: row; align-items: flex-start; gap: 14px; height: auto;
    }
    #home .hero-visual > svg, #hero .hero-visual > svg {
      width: 132px; height: auto; flex: none; margin-top: 4px;
    }
    #home .os-legend, #hero .os-legend {
      flex: 1; min-width: 0; height: auto; gap: 9px;
    }
    #home .os-legend .os-layer span, #hero .os-legend .os-layer span { max-width: none; }
  }
```

Notes:
- The `#home`/`#hero` prefixes are deliberate — they raise specificity above the existing `.hero-visual { flex-direction: column }` and `.hero-visual svg[width="277"] { width: 190px }` rules so this wins without `!important`.
- 132px is a starting point for the SVG width. If the diamond stack gets too small to read, take the legend text down a notch instead (`.os-layer b` → 11.5px, `.os-layer span` → 10px) and give the SVG a bit more.
- Keep the animation working — it's driven by `.hero-visual` class, which is unchanged.

---

## 2. Human-gate cards — diamond glyph to the left of the text (mobile only)

**Where:** `#refusal .uc-card` — the three cards under "AI for creativity. Never for numbers." Each card is: `<svg>` (diamond glyph) → `<h4>` → `<p>`, with the glyph sitting *above* the heading.

**Want:** on `≤ 760px` only, move the glyph into a **left gutter** — glyph on the left, `h4` + `p` stacked in a right column. Makes the cards shorter and tighter. Desktop stays glyph-on-top.

**CSS — drop-in, no markup change:**

```css
  @media (max-width: 760px) {
    #refusal .uc-card {
      display: grid;
      grid-template-columns: 22px 1fr;
      column-gap: 14px;
      align-items: start;
    }
    #refusal .uc-card > svg { grid-row: 1 / span 2; margin-bottom: 0; }
    #refusal .uc-card > h4  { grid-column: 2; }
    #refusal .uc-card > p   { grid-column: 2; }
  }
```

This puts the 22px glyph in column 1 spanning both text rows; `h4` and `p` sit in column 2. The `#refusal .uc-card { padding: 20px 18px !important }` from round 62 still applies — leave it.

---

## Do NOT touch
- Desktop / ≥ 761px (both changes are `≤ 760px` scoped).
- Any copy, markup, SVG paths, the hero animation script.
- The rest of the round-62 mobile block.

## Acceptance test (at 412 px wide, before hand-back)
1. `#home` and `#hero`: the diamond diagram and its 6-row legend sit **side by side** as one block, ≲ 260px tall; diagram still animates; legend text readable.
2. `#refusal`: each card shows the glyph in a left gutter with the heading beside it and the body beneath — cards visibly shorter than before.
3. No horizontal scroll at 360 / 390 / 412 px.
4. Desktop (≥ 1280px) unchanged — spot-check `#home`, `#hero`, `#refusal`.

## Hand-back
Return the full `landing.html`, state the base commit you diffed against (`25b2853`).
