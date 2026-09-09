# ASK_DESIGN_60 — reply: panel adopted, but merged not dropped (your base was stale)

The Brand characters panel is **built correctly** and is now live. Thank you. Two things to carry
into the next round.

## Your base was ~2,900 lines behind

ASK_DESIGN_60 named the base explicitly: `api/frontend/app.dc.html`, sha256 `f37998982400cf8db469…`,
**23,910 lines**. Your handback was **21,006 lines** — it was built on the Sep-2 `app.dc.html` (the
copy sitting at the repo root), not the file the ask pointed at.

The handover doc didn't open with the usual *"Verified before editing: N bytes, sha256 X — matches."*
step. That's the step that would have caught this. Please put it back for every round.

Dropping your file in whole would have reverted, at least: the **Carousel** feature (161 refs),
**Priority geography**, Video's **"Briefed from the plan"** plan-binding (`bagVideoExec`), and ~40
references' worth of the four-toggle grounding UI.

## What actually happened

Your work is purely additive — 6 clean hunks, no deletions:

| hunk | what | ~lines |
|---|---|---|
| 1 | panel markup (after "Briefs in memory", before "Add to the library") | 241 |
| 2 | state keys (`characters`, `charDetail`, `charDraftSeed`, …) | 3 |
| 3 | `componentDidUpdate`: `if (screen === 'library') this.loadCharacters();` | 1 |
| 4 | handlers (`CHAR_TEST_DEFS`, `loadCharacters` … `removeCharacter`) | 174 |
| 5 | `bagCharacters(s)` | 125 |
| 6 | `...this.bagCharacters(s)` in the bag spread | 1 |

I extracted those 6 hunks and re-applied them onto the live 23,910-line file. `checkfe.py` clean
afterward (`sc-if` 1024/1024, `sc-for` 398/398, `<div>` 3204/3204, 917 members, 23 bags, 4 sentinels).
Browser-verified against a real backend: panel renders, empty state + count correct, `loadCharacters`
fires brand-scoped, a real `/character-draft` round-trips a full document and the detail view + the
"still blocking approval" checklist render.

## One bug from the merge, fixed

When re-applying hunk 3 with fuzz, `patch` mis-placed the `loadCharacters()` call **inside the state
object initializer** instead of `componentDidUpdate` — a statement in an object literal, which killed
the whole DC logic class (`SyntaxError: Unexpected token '==='`, template fell back to props-only).
Moved it next to `this.loadMade()` in `componentDidUpdate`. Not your error — flagging it so it's on
the record.

## Next round

**Base ASK_DESIGN_61 on the merged `api/frontend/app.dc.html`** this session sends back — NOT on the
root-level `app.dc.html`, and NOT on your round-60 handback. Confirm its sha before editing.
