# ASK_DESIGN_53 — round 56, the Scripting screen loaded live for the first time in two rounds

Adopt-only, both fixes live-verified. **File: `sha256: 8eae4ca871…`.**

ASK_DESIGN_52 flagged, twice, that the Scripting/"Frame generation guideline" work (rounds 54–55) had
never actually been loaded in a browser — checkfe-clean only, because reaching it needs a real approved
script. This round, I generated a real concept and script (Brand awareness objective, real model calls,
not a fixture) and actually looked at the screen. Found two real defects that checkfe cannot catch because
they're layout/sequencing problems, not structural ones. Both are now fixed and confirmed — one against
the real generated screen, one via an isolated CSS test.

## 1. The primary CTA sat above the section that unlocks it

**Confirmed via actual pixel measurement, not a guess**: "✦ Generate all frames" rendered at `top:1265px`;
"✦ Lock location and cast" — the button that has to be pressed *before* frame generation works at all —
rendered **380px below it**, at `top:1644px`. The individual per-scene "Generate frame" buttons sat lower
still. A person loading this screen hits the big green bulk-generate button, and the DOM order made that
happen before they'd even reached the section that unlocks it — even though a warning banner was correctly
shown above the button (so it wasn't silent), the sequence still put the action before its own
prerequisite.

This predates round 55 — I didn't introduce the ordering, I only edited content inside it — but round 55
was also the first chance to actually see it rendered, and it's a real fix either way.

**Fix**: moved the "Frame generation guideline" card (Look, cast text, Lock button) to sit *before* the
"Storyboard" heading, the gate banner, and the bulk-generate button, instead of after. New order: Location
→ Frame generation guideline (decide + lock) → gate banner (still shown if not yet locked) → Storyboard
heading/button → scene cards → Approve script. Pure block move, no logic changed.

**Verified live, twice**: measured the broken order on the first generated script, made the fix, generated
a *second* real script from scratch to confirm the new order — `Location(1026) → Lock(1570) →
Generate-all(1713) → Scene-1(1909)`, top to bottom, correctly sequenced.

## 2. The single-card Location grid stretched to ~980px wide

Round 55's fix for the Cast-department removal left `scriptDepts` (now permanently one card, Location)
inside a `grid-template-columns:repeat(auto-fit,minmax(280px,1fr))` — reasonable-looking, but a `1fr` max
on an auto-fit grid with exactly one real child stretches that child to the full row width. Confirmed live
against the real rendered screen: the grid container measured 978px, and its lone card measured the same
978px — a card roughly three times the width of every sibling card in this app (Shoot Board's cards sit
around 330px, three to a row).

**Fix**: capped the max to `minmax(280px, 330px)`. Still wraps cleanly to more columns if a department is
ever added back to Scripting; a lone card now sits at a normal card width instead of stretched full-bleed.

**Verified via isolated CSS test** (not by reloading the generated script a third time — a fixed-value CSS
change on an already-proven grid mechanism didn't need another live generation cycle to trust): built the
exact grid rule in a detached DOM node and read `getComputedStyle().gridTemplateColumns` directly —
`"330px 0px"`, confirming `auto-fit` correctly collapses the unused second track to zero and the real card
sits at the capped 330px, not stretched.

## What this round is, in the "do justice to the frontend" sense

Neither of these would have surfaced from reading the template or from checkfe — both are true only once
real content renders into real layout. That's the whole reason "structurally verified, not live" kept
recurring as a caveat across two rounds; this round finally spent the model calls to close it, and found
two things worth fixing once it did.

## Still open

Unchanged from ASK_DESIGN_52 — SSO/desk confirmations, `require_auth`, the ledger schema for #9, all mine.
Shoot Board itself (DoP Note/Prop Master/Wardrobe & Styling cards, now three real cards there instead of
zero) was visible in the same live session but not separately scrutinized this round — approving the
script and opening Shoot Board is the natural next live-verification pass if there's appetite for one.
