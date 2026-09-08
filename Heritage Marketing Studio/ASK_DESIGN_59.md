# ASK_DESIGN_59 — Public homepage (`/`), restyled into Deep Navy Immersive

**New file for this handover — not `app.dc.html`.** This round is `api/static/landing.html`, sha256
`be9cfc81e9e6bea8…`, 392 lines. It's a plain static HTML file (no Claude Design Component wrapper, no
`sc-if`/`sc-for`, no `data-dc-script`) served directly by FastAPI at `GET /` — `themarketing-studio.com`'s
front door, separate from the studio itself at `/app`. Treat it as its own file; nothing here touches
`app.dc.html`.

## The ask

The page today is built, live, and functionally complete — real nav, a hero, an auto-scrolling feature
marquee, Product/Use&nbsp;cases/Pricing/Book&nbsp;a&nbsp;demo sections, a working section-anchor nav — but
it's skinned in the **"Documentary Minimal"** direction (paper background, white cards, quiet accent).
We reviewed three visual directions together and picked **"Deep Navy Immersive"** instead: full-bleed
dark navy, a faint diamond-motif texture, Signal Orange doing real work as a single glowing accent, more
bold and premium than what's live now. **Restyle the whole page into that direction — content, structure,
sections and the marquee all stay exactly as they are; only the visual system changes.**

## Reference — the exact direction to match

A 3-way concept comparison was built and reviewed before this ask; the direction to build toward is
**Option B ("Deep Navy Immersive")** in that comparison, viewable at:
`https://claude.ai/code/artifact/86d33d10-6f96-4681-b80c-814347eca53e`

What made that option read as bold/immersive, to carry over in full:
- **Full-bleed dark navy throughout — not just the hero.** Nav, hero, marquee strip, every section,
  and the footer all live on the dark ground (`#0B1729`/`#111F38`/`#0E1A30` family) — the whole page
  commits to dark, unlike the current live paper build where only accents are colored.
- **A faint diagonal diamond-motif texture behind the hero** (two overlapping 45°/-45° hairline stripe
  gradients at ~9% opacity, in orange and white) — decorative, not a repeating pattern that competes
  with foreground content.
- **Orange (`#F0561E`) rationed to one live element at a time** — the primary CTA pill, the marquee
  dot/accent, a highlighted word in the headline — never running body text, per the brand book rule
  already enforced elsewhere in the product (`app.dc.html`'s own top-of-file CSS comment says the same
  thing; this page should follow the identical rule).
- **A soft radial glow** behind the hero (blue-tinted, top-right, low opacity) for depth without a hard
  gradient edge.
- Headings in white, body copy in a muted blue-grey (`#A9B7CC` family) — never pure white for anything
  but headings, to keep the hierarchy readable at dark-mode contrast.

## What must not change — it's real, working content, not placeholder

- **The auto-scrolling two-lane marquee** (`.lane.left` / `.lane.right`, opposite-direction CSS
  `@keyframes`, `animation-play-state: paused` on `:hover`, disabled under
  `@media (prefers-reduced-motion: reduce)`). Restyle the chip colors to fit the dark ground; keep the
  animation mechanism and the reduced-motion guard exactly as implemented.
- **All section copy and figures** — Product's 5-stage spine + 4 producers, Use Cases' four illustrated
  example cards (labelled "illustrative, not real brand campaigns" — keep that disclosure), Pricing's
  four real tiers with their actual ₹ figures (Studio ₹40,000/mo, Studio Pro ₹1,20,000/mo, Agency
  ₹15–20k/brand, Enterprise custom) pulled from the business-model work done this session — these are
  real numbers, not filler, don't regenerate them. Book a Demo's qualifying question ("When did you last
  kill a campaign because the numbers didn't support it?") is a deliberately specific line, keep it
  verbatim.
- **The hero visual** — the four layered device-frame cards (social post mockup, POS glyph card,
  onground pin card, video-frames card) are hand-drawn CSS/SVG, not stock photography (there's no real
  campaign imagery to embed honestly). Recolor them to sit on a dark ground; don't replace them with
  photography unless you're adding real, rights-cleared images — flag it here first if so.
- **Nav structure**: Product / Use cases / Pricing are same-page scroll anchors (`#product` etc.), not
  separate pages. "Book a demo" scrolls to `#demo`. "Sign in" is a plain link to `/app` (the real,
  already-gated studio login) — **not** a form on this page; there is no login logic here and shouldn't
  be, see the note below.

## Explicitly out of scope / don't add

- **No functional login on this page.** `/app` already has a real, server-enforced login gate
  (`RequireLoginMiddleware` in `main.py`, backed by real sessions) — don't build a second login form
  here; it would be non-functional decoration at best and confusing at worst.
- **The "Book a demo" form has no submit handler yet** (`onsubmit="return false;"` — intentional, flagged
  in the current build). Style it fully, but don't wire a fake success state that implies it sent
  somewhere — it doesn't yet.
- Fonts stay Epilogue (headings) + IBM Plex Sans (body) + IBM Plex Mono (numerals/labels) — already
  linked in the file's `<head>`, matches the type system used elsewhere in this project's other
  documents this session.

## Verification note

This file has no `checkfe.py` coverage (that tool is scoped to `app.dc.html`'s DC-component syntax) —
it's plain HTML, so a normal browser load is the whole verification: open `http://localhost:8000/`
after any edit, confirm the marquee still animates, all four sections still anchor-scroll correctly,
and `prefers-reduced-motion` still disables the marquee (dev tools → rendering → emulate CSS
media feature).
