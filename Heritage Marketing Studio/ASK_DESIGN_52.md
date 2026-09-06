# ASK_DESIGN_52 — round 55, all shipped and live-verified, adopt-only

Everything below is built, verified, and installed to both copies. Nothing here is a request — adopt
`app.dc.html` as-is. **File: `sha256: b0bcc84162…`.**

This round came from four pieces of user feedback: two were UI restructuring calls, two were bug reports.
All four are done; the two bugs were root-caused and fixed, not just patched around.

## 1. DoP Note / Prop Master / Wardrobe & Styling moved to Shoot Board

They were in Scripting (added round 54) alongside Cast and Location. On reflection that was the wrong
split: Cast and Location are pre-production decisions that gate the cast-reference lock (decide who/where
*before* the reference image exists); DoP/Props/Wardrobe are shoot-day crew decisions with no such gate,
and they're what actually feeds the per-frame render prompt (`generateFrame`'s `deptNote` calls, built
round 54). Having them live where they take effect is more honest than having them upstream, disconnected
from the render. `DEPTS` entries changed `home:'scripting'` → `home:'shoot'` for all three. Mechanical.

## 2. Cast department card removed — merged into the box that was already doing its job

This is the fix for the duplication you flagged: two boxes both claiming to be "the cast" — the Cast
department's own prose casting-brief, and the separate character-reference-sheet textarea
(`videoCharacters`) that's the one actually sent to every generation call (`/cast-reference`,
`/scene-still`, `/produce-video`, `/production-bible-docx`, `voicePayload`).

**Not a data migration** — `videoCharacters` already has six real consumers across the pipeline; renaming
or replacing it would have been the riskier move. Instead: the redundant Cast department card is deleted
from `DEPTS` entirely (Scripting's Departments grid now holds only Location). Nothing is lost —
`deriveCharacters` (the AI-draft button for the reference sheet) already read `shoot.cast.text` as
*optional supporting context* before drafting; that plumbing is untouched, it just has one less input
source now that there's no separate box to write into. `deptFallback`'s now-dead `cast` entry removed too.

## 3. "Cast & continuity sheet" renamed to "Frame generation guideline"

Because it's more than a cast list: with #1 and #2 above, this box is now the one place that explains
everything that goes into a frame. New fine print under the heading: *"More than a cast list — this is
everything about the shot itself. Covers the cast written below, the Location note above, and the Look
chosen here. DoP Note, Prop Master and Wardrobe & Styling, drafted in Shoot Board, fold into every
rendered frame too, once written."* `castRefNote`'s copy (the sentence next to the Lock button) updated to
match — mentions the setting now, not just faces and clothes.

**Layout**: Scripting's Departments grid (now just Location, in a responsive grid rather than a
hard-coded 3-column one that would've left two-thirds of the row empty) sits directly above this renamed
section — so "Lock location and cast" ends up directly under both inputs without needing to move anything.

**Caveat, stated plainly, same as last round**: this has not been loaded in a browser. Reaching it needs a
real approved script (real model calls). Verified structurally only — checkfe clean, and I traced
`scriptDepts`/`shootDepts` → the template by hand to confirm the grid change doesn't orphan anything.

## 4. Plan screen — "Brand / activation balance" now actually shows what generating it does

**Root cause, confirmed via live network capture, not guessed:** the balance layer is `kind:"number"` in
`plan.py`, not `kind:"rows"` like the other six layers. Generating it writes straight into the plan's
`balance` object (`brand_share`/`reason`/`basis`/`declared`) and **never touches `nodes.balance.rows`** —
by design, that array is permanently empty for this layer. The frontend rendered the same generic "Draft
this layer" panel for every layer, watching `rows` for a change. For balance, it never got one — so the
panel said "Nothing written yet" forever, no matter how many times the button under it was pressed, even
while the click was genuinely succeeding and changing the Declared card two inches above it.

**Fix**: that generic panel now only renders for `kind:"rows"` layers (wrapped in `sc-if pIsTable`). The
balance card gained its own "✦ Suggest a split" button, calling the same `/plan-generate` endpoint, sitting
next to the Brand-share slider it actually updates.

**Verified live**, real model call: clicked Suggest, `200 OK`, the Declared bar moved from "60% — the
default, not a split anyone has declared yet" to "60% declared," a real reason appeared, and the plan's
completeness count updated. Not something I inferred from the code — watched it happen.

## 5. POS key visual — the "upload the pack shot" refusal was a false positive on nearly every route

**Root cause, confirmed against three real live-drafted routes, not a hypothesis:** `looks_like_pack()`
(`posm.py`) does a blind substring match for words like "pack" across the *entire* hero description. But
every route this producer's own prompt drafts is instructed to say the pack sits masked and locked at the
base — that's the studio's own point (`"The pack is always present and never the hero"`). Pulled three
real `/posm-keyvisual` responses this round: all three said "pack" in that exact, correct, benign way.
Every one would have tripped the refusal. This wasn't an edge case — uploading a pack shot to Memory,
signing it off, and selecting it (the refusal's own advice) changes nothing, because the check never looks
at the library at all.

**Fix**: `hero_type` (the KV route's own declared hero type — `metaphor-object`, `demonstration`,
`person-in-benefit`, etc., already returned by `/posm-keyvisual`) is now sent from the frontend to
`/posm-image`. The backend only runs the blind word-match when `hero_type` is *not* a recognized type —
i.e. only for a raw, routeless override, which is what that check was actually meant to catch. A route
that came from the model's own vetted hero-type system is trusted; the real library requirement for the
two hero types where the pack genuinely *is* the subject (`endorser-with-pack`, `range-array`) is still
enforced, by the separate, correct gate that already existed for exactly that (`posm.gate(hero_type)`) —
which, as a side effect of finally receiving `hero_type` from the frontend, now actually engages for the
first time instead of silently being inert.

**Verified live end to end, real render:** developed routes, picked one whose description explicitly said
"the real pack masked small in the lower corner," rendered it — `200 OK`, a real image came back
(`provider: google`). Also confirmed the *old* code would have refused this exact request, by re-running
the same check directly against the captured route text before the fix went live.

**One thing to know if you're testing this yourselves**: the local studio server does not auto-reload on
file changes — my own first live test still hit the old code because of this, not because the fix was
wrong. Restart the server after pulling this file if you're testing generation routes locally.

## Still open

- SSO/desk confirmations — unchanged.
- `require_auth` on the ~150 live routes, ledger schema + SOM/benchmark repoint for #9 — mine, next.
- The Scripting screen (department cards, the renamed Frame generation guideline section) has not been
  loaded in a browser across two rounds now — both times because reaching it needs a real approved script.
  If either of us sees something off there once one exists, that's why.
