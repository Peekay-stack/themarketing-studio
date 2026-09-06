# ASK_DESIGN_54 — round 57, Shoot Board reviewed live, one more real bug found and fixed

Adopt-only, verified. **File: `sha256: ccc696085886…`.**

Continuation of ASK_DESIGN_53's live pass: approved the generated script and opened Shoot Board for the
first time with real content — the department cards (DoP Note, Prop Master, Wardrobe & Styling, Lighting,
Music, Dialogue/VO, Key Shots) had never been seen rendered together before.

## The department badge was rendering the full label as wrapping, overflowing text

**Confirmed via computed style, not appearance alone**: every department card's "icon" is a 34×34px
colored square. It was showing `{{ d.label }}` — the *entire* department name — as its content, with
`overflow:visible` and `white-space:normal`. For short names (`Music`, `Lighting`) this mostly held. For
the three departments this project added across rounds 54–55, it didn't: `getComputedStyle` on the
"Wardrobe & Styling" badge showed `scrollWidth: 52` against a `clientWidth: 34` — real overflow, the text
spilling out of its box rather than being clipped. The badge was also the *only* place a card's name
appeared at all — there was no separate heading, so this wasn't a decorative glitch, it was the label
breaking.

**Fix**: `DEPTS` gained an `abbr` field — a short mark that actually fits a 34px badge (`Loc`, `DoP`, `PM`,
`W&S`, `Lt`, `Mu`, `D/V`, `KS`) — and both card templates (Scripting's Location card, Shoot Board's grid)
now render the badge holding just that mark, with a real text heading (`{{ d.label }}`, 14px Epilogue,
navy) beside it. Same visual footprint, but the badge is finally sized for what it holds, and the full
name is legible regardless of length.

**Verified**: live against the real Shoot Board render for the short/medium labels; the worst case
("Wardrobe & Styling") confirmed via an isolated DOM test at the card's real 330px width —
`badgeOverflowed:false`, row height a clean 34px, the label fits alongside it with room to spare.

## Also confirmed clean this round (no fix needed)

- Shoot Board's 7-card grid (`repeat(3,1fr)`, fixed columns): the 7th card sits correctly in column 1 of
  its own row, at the same 329px width as every other card — not stretched, not misplaced. This is a
  different grid mechanism from the Location grid ASK_DESIGN_53 fixed (fixed `repeat(3,1fr)` vs.
  `auto-fit`), and it was already correct.

## Status

This closes the live-verification arc that's been open since round 54: Scripting and Shoot Board have now
both actually been loaded with real generated content and reviewed, not just checkfe-passed. Three real
defects found and fixed across rounds 53/54: the CTA-before-prerequisite ordering, the single-card grid
stretch, and this badge overflow. None were visible from the template source alone.

## Still open

Unchanged — SSO/desk confirmations, `require_auth`, the ledger schema for #9, all mine, none frontend.
