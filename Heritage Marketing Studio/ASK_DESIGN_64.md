# ASK_DESIGN_64 — landing.html: the mobile hero diagram is taller than the legend (should be shorter)

## Base

Work on top of **your `landing-d861e674.html` hand-back** (the file you just sent — it is
commit `25b2853` + your `.os-vstack` mobile hero work + the Human-gate icon-left change).
`25b2853` is the last *committed* `landing.html`; your `.os-vstack` work is not committed yet, so
this round layers on your file directly. Diff your working copy against `25b2853` and keep the delta;
don't drop a whole fresh file in.

CSS + the two `.os-vstack` markup lines only. No copy, no desktop changes.

## What's wrong

The brief was: on mobile, **flatten** the layered-diamond glyph (flatter / fatter diamonds) so the
whole stack is **shorter than the 6-row legend** and the two sit side by side compactly.

What landed instead: the flat wide diamond *shape* was swapped for **1:1 squares rotated 45°** with
only `-14%` overlap, so `.os-vstack` renders **~443px tall** — taller than the ~430px legend. The
mobile hero visual got bigger, not smaller. `#hero` section is now ~1026px.

Measured at a phone width: `.os-vstack` height 443px; `#home` 915px, `#hero` 1026px.

## The fix — drop `.os-vstack`, shrink the original SVG instead

The inline `<svg>` in each `.hero-visual` is *already* the correct flat wide-diamond shape, with the
outlines, the orange bottom plate, and the running animation. Shrunk to `width: 120px` it is
**~135px tall** — well short of the legend, sits beside it with room to spare, animation intact.

1. **Delete** the whole `.os-vstack { … }` CSS block (the 8 rules added after the round-62
   `@media (max-width: 760px)` block).

2. **Delete** the two markup lines
   `<div class="os-vstack"><div class="vd"></div>…×6</div>` — one inside each `.hero-visual`
   (`#home` and `#hero`).

3. In the `@media (max-width: 900px)` block, replace these two rules:
   ```css
   #home .hero-visual > svg, #hero .hero-visual > svg { display: none; }
   #home .hero-visual .os-vstack, #hero .hero-visual .os-vstack { display: flex; margin-top: 6px; }
   ```
   with this one:
   ```css
   #home .hero-visual > svg, #hero .hero-visual > svg { width: 120px; height: auto; flex: none; margin-top: 4px; }
   ```

4. **Restore `overflow: hidden` on `.hero`** — both the CSS rule
   (`.hero { … overflow: hidden; }`) and the inline `style="…overflow:hidden;"` on the `#home` and
   `#hero` `<section>` tags. (The `overflow: visible` was only added to stop the oversized rotated
   squares from clipping; not needed once they're gone, and `hidden` keeps the large hero background
   glows contained.)

## Keep (from rounds 62 / 63 — do not revert)

- `#refusal .uc-card` icon-left grid in the `@media (max-width: 900px)` block — the glyph in a 22px
  left gutter, `h4` + `p` in column 2. Card height dropped to ~127px, this is good.
- `#home .os-legend, #hero .os-legend { flex: 1; min-width: 0; height: auto; gap: 14px; width: 100%; }`
  and the bigger `.swatch` (20 × 44) rules — fine, keep.
- `.hero-visual { height: auto; min-height: 363px }` / `.os-legend { height: auto; min-height: 309px }`
  — fine, keep.
- The entire round-62 `@media (max-width: 760px)` block — untouched.

## Acceptance test (at 412 px wide, before hand-back)

1. `#home` and `#hero`: the diamond diagram sits **beside** the legend and is **clearly shorter than
   the legend column** — diagram ≲ 150px tall.
2. The diagram still **animates** (plates cycling), and the flat wide-diamond shape + orange bottom
   plate are intact.
3. `#hero` section ≲ 880px; no horizontal scroll at 360 / 390 / 412 px.
4. Desktop (≥ 901px) unchanged — animated SVG at full size, no `.os-vstack` anywhere.

## Alternative (only if there's a reason to avoid the SVG on mobile)

Keep `.os-vstack` but actually flatten it: on `.os-vstack .vd`, add `scaleY(0.5)` to the transform
(`transform: rotate(45deg) scaleY(0.5)`) and tighten `margin-top` to `-4%`. Stack then lands
~150–170px. Downsides: the `scaleY` distorts the border thickness, there's no animation, and it's
more CSS to keep in sync with the desktop SVG. The shrunk-SVG route above is cleaner — prefer it
unless you hit a specific problem.

## Hand-back

Return the full `landing.html`; state the base you diffed against (`25b2853` + your `d861e674`
delta).
