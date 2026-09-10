---
name: landing-page-thread
description: The public landing page (landing.html) — where it lives, what's shipped, and the unresolved responsive hero-visual problem with the solution to build
metadata:
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-10T15:42:15.535Z
---

The pre-login marketing page. Route `GET /` in `api/main.py` → serves
`Heritage Marketing Studio/api/static/landing.html`. **Two copies must stay in sync:** the repo-root
`landing.html` (Design's working copy) and `api/static/landing.html` (served). Ship = copy the new
file to BOTH, `git add` both, commit, push → Render auto-deploys (`beta-deploy-plan`). Self-contained
HTML, LF, only external dep is Google Fonts. The login form itself is NOT here — it's inside
`app.dc.html` at `/app`; landing.html only links to `/app`.

## Shipped (LIVE)

- **`f51d912`** — "THE HUMAN GATE" section rewrite (was "THE REFUSAL"): 3 cards (No autonomous
  publishing / Grounded in your truth / You set the boundaries — it never crosses them), sub-headline
  "It generates the work — not the evidence behind it, and never without your sign-off", closing line
  "You bring the evidence and the brand. The studio brings the hours." Also: single `<h1>` (`#hero`
  heading demoted to `<h2 class="display">`, `h1.display`→`.display` selectors), `<meta description>`,
  demo form → `mailto:tmsmarketingstudio@gmail.com` CTA + visible fallback address, dot-nav label
  "Human gate".
- **`25b2853`** (ASK_DESIGN_62) — mobile layout pass, one `@media (max-width:760px)` block appended
  last in `<style>`: kills `scroll-snap-type` + `section{min-height:100vh;display:flex;justify-content:center}`
  on phones (was clipping eyebrows under the sticky header + jank), Product stages + producers → 2-up
  grids so they share a screen, Pricing → 2-up, Demo panel packed to ~1 screen, decorative `#section > svg`
  diamonds hidden (were colliding with stacked content). Verified 412px: Product 1899→930, Pricing
  1676→1121, Demo 1015→841, no h-scroll, desktop untouched.

## NOT shipped — the open item: responsive hero visual

The hero visual (`#home` and `#hero`) = an animated **layered-diamond diagram** beside a **6-row text
legend** (Measurement→Brand Profile, orange bottom plate). On desktop they're height-matched and look
right. On narrower screens they diverge and leave dead space.

**Root cause:** the diamonds have a fixed aspect ratio (SVG `viewBox`, or a `.os-vstack` `aspect-ratio`
experiment Design tried). Narrow column → diamonds get shorter; legend text wraps → legend gets
taller. They must instead stay **locked to the same height at every width**, with the diamonds
absorbing the difference by going flatter/fatter continuously — one behaviour, not "web shape vs phone
shape".

**Rounds that missed:** ASK_DESIGN_63 (shrink SVG side-by-side) + 64 (revert `.os-vstack`) — both
written, both superseded. Design's `landing-d861e674.html` handback (uncommitted, in
`C:\Users\punie\`) added a `.os-vstack` pure-CSS diamond stack replacing the SVG ≤900px: the
**Human-gate icon-left grid in it is GOOD** (glyph in a 22px left gutter, card 206→127px — keep that),
but the `.os-vstack` itself renders **443px tall, taller than the ~430px legend** — wrong.

**THE SOLUTION TO BUILD (agreed for 11 Sep morning) — CSS only, zero breakpoints:**
Legend drives height; diagram column `align-items:stretch` matches it; 6 plates `flex:1 1 0` split
that height; each plate box = colWidth × legendHeight/6, and a `clip-path` diamond in that box
auto-flattens/fattens without losing shape.
- Markup: replace the inline `<svg>` (delete `.os-vstack`) in each `.hero-visual` with
  `<div class="os-stack" aria-hidden="true">` + 6 `<div class="plate" data-layer="…">`
  (measurement, execution, plan, strategy, foundations, profile — top to bottom).
- CSS: `.hero-visual{display:flex;align-items:stretch;gap:clamp(14px,3vw,26px);height:auto}` ·
  `.os-stack{flex:0 0 clamp(104px,30%,300px);display:flex;flex-direction:column;justify-content:center;min-width:0}` ·
  `.os-stack .plate{flex:1 1 0;margin-block:-4%;clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%);background:rgba(255,255,255,.08);transition:opacity .3s,background .3s,filter .3s}`
  · depth-graded `nth-child` backgrounds, `:nth-child(6){background:rgba(240,86,30,.55)}` ·
  `.plate.os-active{background:rgba(240,86,30,.35);filter:drop-shadow(0 0 8px rgba(240,86,30,.5))}` ·
  `.plate.os-dim{opacity:.3}` · `.os-legend{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:space-between;gap:clamp(6px,1.6vw,14px)}`
  · `clamp()` font sizes on `.os-layer b` / `.os-layer span`.
- JS: change the animation selector `'.os-plate,.os-layer'` → `'.os-plate,.plate,.os-layer'` so the
  cycle + hover-sync drives the divs.
- Restore `.hero{overflow:hidden}` (+ inline on both sections); delete every per-width hero-visual
  `@media` rule; delete `.os-vstack`.
- Outline vs fill tradeoff: recommended = semi-transparent filled diamonds. To KEEP outlines: one
  `<svg per plate preserveAspectRatio="none" vector-effect="non-scaling-stroke">` (constant stroke at
  any stretch), same flex mechanism.
- **Plan: I build it directly in `landing.html`, verify at 360/600/900/1280, user reviews — NOT
  another blind Design round.** Full CSS/markup is in the session transcript (my message right before
  the user said "good knight", 10 Sep).

## Browser-pane gotcha (found 10 Sep)

`mcp__Claude_Browser__resize_window` to widths below ~535px does NOT stick — it clamps. So exact
"fits one 915px screen" checks at 375/412 are unreliable in the pane. Workarounds: measure element
heights (viewport-independent for `max-width`/`flex`-bounded blocks like `.os-stack`), use
`documentElement.scrollWidth - clientWidth` for h-overflow, and serve the file with
`py -m http.server` from `C:\Users\punie\` then `preview_start` that localhost URL.

See [[beta-deploy-plan]] (deploy pipeline), [[design-handovers-merge-never-replace]],
[[reload-the-page-after-every-frontend-edit]].
