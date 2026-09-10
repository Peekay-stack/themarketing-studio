# ASK_DESIGN_62 — landing.html: mobile layout pass (sections run 2–3 screens)

## Base file — confirm before you start

- File: **`landing.html`** (repo root) — identical to `Heritage Marketing Studio/api/static/landing.html`, which is what the live site serves.
- Base commit: **`f51d912`** (`Peekay-stack/themarketing-studio`, `master`). This already contains the ASK_DESIGN_60/61 work + the last round's fixes (single `<h1>`, `<meta description>`, "THE HUMAN GATE" eyebrow, mailto demo CTA, dot-nav label "Human gate", the `uc-grid` inline-style removal).
- **Diff your working copy against `f51d912` first.** If your base is older, do NOT drop your file in whole — re-apply the change below onto the current file. (Previous rounds shipped stale bases that silently reverted fixes.)

This round is **CSS only**. No markup changes, no copy changes, no desktop changes.

## The problem

The page is built as a desktop "full-screen scroll-snap deck" — `html { scroll-snap-type: y proximity }` + every `section { min-height: 100vh; display: flex; justify-content: center }` — and there are `#product` / `#refusal` tuning rules (some `!important`) that were never walked back for mobile. The `@media (max-width: 640px)` block patches a few things but leaves all of the above intact.

Measured on a 412 × 915 phone viewport (live site):

| Section | Height now | Should be |
|---|---|---|
| `#product` (5 stages + 6 producers) | **1899px** (~2 screens — stages and producers never share a screen, so "5 stages → 6 producers" loses its meaning) | ~1 screen, stages and producers adjacent |
| `#pricing` (4 cards) | **1676px** (~2 screens) | ~1 screen |
| `#demo` (form) | **1015px** (just overflows one screen) | fits one screen |

Also on mobile:
- Section eyebrows ("PRODUCT", "THE FMCG METHOD…") get **clipped under the sticky header** — sections are `min-height:100vh` + vertically centred, so content taller than the viewport overflows upward under the 69px sticky header.
- Producer cards show a **big hollow gap** — `#product .producer { min-height: 150px }` + `justify-content: space-between` around ~90px of content.
- "THE HUMAN GATE" cards feel **hollow / over-tall** — `#refusal .uc-card { padding: 34px 28px !important }` on a 376px-wide card; the icon floats 35px from the top.
- A faint mark pokes above the 2nd Human-gate card — it's the **bottom vertex of the section's decorative background `<svg>`** (`#refusal > svg`, fixed 610px tall, anchored to section top). Same decorative SVGs sit in `#product`, `#pricing`, `#demo`, `footer`.

## The fix — append this one media block

Insert **immediately before `</style>`** (after the `#product .producer .pc-d { … }` rule, currently the last rule in the stylesheet — around line 238). It must come **after** the existing `#product` / `#refusal` override block and after the `@media (max-width: 640px)` / `(max-width: 480px)` blocks so it wins the cascade — several of these selectors have the same specificity as existing rules and rely on source order. The one `!important` below is deliberate: it overrides `#refusal .uc-card { padding: 34px 28px !important }`.

```css
  /* ---------- mobile: collapse the desktop full-screen deck ---------- */
  @media (max-width: 760px) {
    html { scroll-snap-type: none; }
    section { min-height: 0; display: block; scroll-snap-align: none; padding: 52px 0; }

    /* decorative diamonds collide with stacked content */
    #refusal > svg, #product > svg, #pricing > svg, #demo > svg, footer > svg { display: none; }

    /* Product — 5 stages + 6 producers on one screen */
    #product .shead { margin-bottom: 26px; }
    #product .stages { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; overflow-x: visible; margin-bottom: 20px; }
    #product .stage { min-width: 0; padding: 0; border-bottom: 0; }
    #product .stage:not(:last-child) .sn::after { display: none; }
    #product .producers-row { grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }
    #product .producer { min-height: 0; padding: 14px 13px; justify-content: flex-start; }
    #product .producer .pc-t { font-size: 13.5px; }
    #product .producer .pc-d { font-size: 11px; margin-top: 5px; }

    /* Pricing — 2-up, tighter */
    #pricing .price-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
    #pricing .price-card { padding: 16px 14px; }
    #pricing .price-card .amt { font-size: 19px; }
    #pricing .price-card .inc { font-size: 11px; }

    /* Human gate — trim the hollow padding */
    #refusal .shead { margin-bottom: 26px; }
    #refusal .uc-grid { gap: 14px; }
    #refusal .uc-card { padding: 20px 18px !important; }

    /* Demo — pack to one screen */
    #demo .demo-panel { padding: 20px 16px; gap: 16px; }
    #demo .demo-panel h2 { font-size: 22px; margin-bottom: 10px; }
    #demo .demo-panel p.lede { font-size: 13.5px; margin-bottom: 0; }
    #demo .demo-q { margin-top: 12px; padding: 12px 14px; font-size: 12px; }
    #demo .demo-form { gap: 9px; padding: 16px; }
    #demo .demo-form input, #demo .demo-form textarea { padding: 8px 10px; }
  }
```

## Do NOT touch

- The hero visual (`#home` / `#hero` diagram + `.os-legend`) — it stacks fine on mobile, leave it.
- Any copy, any markup, any SVG paths.
- Desktop / tablet ≥ 761px — this block is scoped to ≤ 760px, and 760 is already the file's mobile breakpoint (nav/hamburger swap there).
- The `@media (min-width: 761px) and (max-width: 1100px) { .producers-row … }` rule.

## Acceptance test (do this at 412 px wide before handing back)

1. **No scroll-snap jump** when flicking through the page; **no eyebrow clipped** under the header on any section.
2. `#product`: the 5 stage tiles (2-col grid) and the 6 producer cards (2-col grid) are visible together or within a short scroll — the "5 stages → 6 producers" relationship reads. Section height ≈ 900–1000px.
3. `#pricing`: 4 cards in a 2×2 grid, section ≈ 850px, no card taller than needed.
4. `#demo`: the whole panel (heading → form → "Request a walkthrough" → fallback email) fits in one 915px screen.
5. `#refusal`: cards no longer feel hollow; no stray mark above card 2.
6. Desktop (≥ 1280px) unchanged — spot-check the same four sections.

## Hand-back

Return the full `landing.html`. State the base commit you diffed against. We merge onto the current file and copy to both `landing.html` and `api/static/landing.html`.
