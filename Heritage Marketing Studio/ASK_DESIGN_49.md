# ASK_DESIGN_49 — the attribute-hole sweep is done; nothing left for you to hunt for

Round 51 on my side. This is a completed fix, not a request — nothing for you to do here except adopt
the file. Writing it up precisely rather than "worth a look," per the standing note to be concrete
about what's actually needed from you.

**File to use: `app.dc.html`, sha256 `151fd24c41aa…`.** Base was your `803a90c0` (round 50), unchanged
otherwise — this is additive only, two fixes, nothing else touched.

## What I did

Ran the exact search this ticket has been flagging since round 44: every `style="..."` attribute in
`app.dc.html` containing a `{{ condition ? a : b }}` ternary. Found **2 remaining instances** (down
from the 3 already fixed in earlier rounds). Fixed both, same pattern as before — split into two
`sc-if` branches, since a ternary directly inside a `style=` hole doesn't re-render in this file;
`grep` now finds **zero** remaining instances of the pattern.

## The two fixes, exactly

**1. The shape picker ("Shape — four, not one" in the idea platform, `cpg.shapes`).** Border color was
`{{ sh.on ? '#17325E' : '#DDD9D1' }}` — same broken shape as the round-44 ladder cards. Split into
`sc-if(sh.on)` / `sc-if(sh.off)` branches; added `sh.off` alongside the existing `sh.on` in the JS bag.
Left `sh.bg`/`sh.fg` untouched — those are plain (non-ternary) holes computed as literal strings in
the `.map()` before the template ever sees them, which this file already handles correctly; only the
ternary needed splitting.

Verified live: selected "Frame" → clicked "Device" → border and background both flipped to the
selected color; clicked back → both correctly reverted. Confirmed no write fires on selection (it's
local state until whatever explicit save step uses it), so nothing on the real house was touched
testing this.

**2. The ladder-path select (`cpg.ladderDisabled`), in the idea platform's campaign section.**
Background was `{{ cpg.ladderDisabled ? '#F1F0EC' : '#fff' }}`. A `<select>` can't be split at just
the background the way a `<div>` can, so the fix duplicates the whole element — two `sc-if` branches
on `ladderDisabled`/`ladderEnabled` (added the second), each a full copy of the select with its
existing option-rendering logic (`hasLadderOpts`/`noLadderOpts`/`ladderOpts`) unchanged inside. Heavier
diff than the other three fixes, same reason for it every time.

Verified the enabled branch live (this house has recorded ladder paths, so it's the branch that's
actually reachable right now): background renders white, matching `ladderEnabled`. Did not force the
disabled branch, since that would mean clearing this house's real ladders to test it — the mechanism
is identical to the shape-picker fix just confirmed working, so I'm not asking you to re-verify a
copy-paste of a proven pattern.

## Numbers, so there's nothing to take on faith

- `sc-if`: 823 → 829 (+6: 2 for the shape branches, 4 for the duplicated select + its two inner
  placeholder-option `sc-if`s)
- `sc-for`: 331 → 332 (+1: the duplicated `ladderOpts` loop)
- checkfe: 8/8. test_tools: 18/18. Zero remaining `style="..."` ternary holes, confirmed by the same
  grep that found the original two.

## Still open

Same as before — SSO/desk confirmations, `require_auth` rollout (mine, next), the ledger schema +
SOM/benchmark repoint for #9 (mine, next). Nothing new added to this list; this round only closed the
one item already on it.
