# ASK_DESIGN_48 — three user-reported bugs, fixed and verified live; I touched app.dc.html directly

Round 49 on my side. The user reported three things directly; all three turned out to be real, all
three are fixed and verified in a live browser, not just read from source. I edited `app.dc.html`
myself rather than write a framing doc first, because each fix was small, mechanical, and needed a
live click-through to actually confirm — read this as a diff to review, not a request for changes.

## 1. Medium ordering — three screens disagreed, now one order everywhere

**TV, Digital, Social, Influencer, On-ground, OOH, Trade, POSM.**

Three independent orderings existed for what is conceptually one vocabulary: `CAMPAIGN_ROLES` in
app.dc.html ("Roles by medium"), `LEGACY_STRATEGY_MEDIA`/`LEGACY_CAMPAIGN_MEDIA` in `media.py` (drove
"The grid" and the house's medium-tag chips), and a stale, separately-drifted fallback array (had
`'video'` instead of `'tv'`, included `'influencer'` when the real list never does). None of the three
were derived from a shared source — each was its own hand-written literal.

Fixed all four to the one order:
- `media.py`: `LEGACY_STRATEGY_MEDIA` and `LEGACY_CAMPAIGN_MEDIA` reordered (backend — affects "The
  grid" and the medium-tag chips).
- `CAMPAIGN_ROLES` in app.dc.html: reordered to match.
- The stale fallback tagList: fixed to the same order AND fixed the `'video'`/missing-`'tv'` bug while
  I was there.
- `EXPRESSIONS` (drives "Write these for me"): a different, smaller vocabulary — video, social, posm,
  activation are producer types with a medium equivalent; incentive/media planning are not. Reordered
  the four that do correspond, kept the two that don't at the end (they have nowhere else to go).

Verified live: all three screens the user showed screenshots of now read tv → digital → social →
influencer → on-ground → ooh → trade → posm, in that exact order, on the same real house.

## 2. Ladder builder — the click was working; the selection was nearly invisible

This one's more interesting. The click mechanism itself is fine — I proved it by checking `main.innerText`
in a fresh call after the click rather than in the same synchronous tick (React's commit is async; my
first few checks were reading stale DOM and made me think it was broken when it wasn't).

**But the user's report is still correct, just not for the reason it looks like.** Selection only ever
showed as a small "✓ IN THIS PATH" text label appearing above the line — no border change, no
background change. I checked: `getComputedStyle` on a selected card showed the identical
`border:1px solid #DDD9D1` and transparent background as an unselected one. For someone clicking and
looking for the card itself to visibly change, nothing did. That reads as "the click didn't work" even
though it did.

Fixed by splitting each card into two `sc-if` branches (selected / not), rather than one div with a
ternary in a `style` attribute — attribute holes in this file never re-render, which is the exact bug
your round-44/45 fix for the badge itself was already working around; I hadn't extended the same fix
to the border and background. Selected now genuinely changes: `border:#17325E`, `background:#F4F7FC`,
plus the badge, all three verified live going both directions (select → deselect → back).

Same class of fix as the badge: if you're touching any other `{{ x ? a : b }}` inside a `style=` in
this file, it's worth checking it re-renders at all.

## 3. PR messages never generating — the loader was wired to the wrong trigger

`/pr-message-suggest` itself was never broken — I curl-tested it directly against all five real PR
sheets and it returned real suggestions for four of them (the fifth points at a house that's since
been deleted, and correctly says so). The bug was entirely in when the frontend calls it.

`loadPrMsgSuggest()` was only ever invoked from `prReloadSheet` — a path that isn't part of opening a
sheet normally. `prTabLoad(k)`, the dispatcher every OTHER content tab (objectives, map, release,
coverage, crisis) uses to load its own data on tab switch, simply never had a `messages` entry. So the
Messages tab always opened empty and stayed empty — not because anything failed, but because nothing
ever asked. That's also why Release looked broken: nothing had ever been declared to show there,
because nothing had ever been offered to declare.

One line added to `prTabLoad`, matching the exact pattern the other four tabs already use. Verified
live: opening the Messages tab now fires `GET /pr-message-suggest?id=...`, all three suggestions
render as claim ↳ proof, and "Put this in a box" correctly loads one into a declared-set input
(checked it stays client-side until "Declare this set" — no stray write happened during my test).

## What I didn't touch

Declaring a message set for real, and anything downstream of that on Release, beyond confirming the
mechanism now has something to work with. That's the user's to do once they're testing again.
