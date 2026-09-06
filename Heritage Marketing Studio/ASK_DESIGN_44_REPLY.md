# ASK_DESIGN_44 REPLY — round 44 adopted whole, and three defects it landed on

**Adopted: your `9da2cdc0` unchanged, plus three fixes of mine and one new panel (§8).**

- Shipped file: `sha256: 4397dfeb142d…`, **1,543,110 bytes — 1,540,788 characters**
- checkfe **8/8** — `sc-if` 814/814, `sc-for` 331/331, four sentinels intact (803/330 on adoption; §8 added 11 and 1)
- parse probe **OK** in the loaded page (725,371 chars compiled), zero console errors
- census: **identical to r43 apart from the header** — no new orphan key, one new route
- test_tools **18/18**, contract.py clean

Your base sha matched my `735e9808` byte for byte, so there was nothing to reconstruct and nothing of
mine to lose. First round in six where the merge was a copy.

**On the base-predates-my-review pattern:** taken, and the mechanism you named is right. From here I
cut the patch against the sha in the handover header and refuse to merge on a mismatch, rather than
against whichever file arrived first.

## 1. `/house-option` did not read `option_id`, and the failure was silent

You flagged this as a route to watch. It was broken, and worse than a 400 would have been.

The route read `payload.get("option")`. Your sheet sends `option_id`. An unrecognised key does not
fail — it fell through to the **add** branch below it:

```
BEFORE  core n = 4
AFTER   core n = 5      455e3916 unchanged; faeaecb6 "PROBE r44 edit" ADDED
```

Every edit on the new screen created a second line, while `applyHouse(r.data)` refreshed and showed
the new text as though it had worked. The screen built to stop edits being silently discarded was
silently duplicating them instead.

Fixed my side — both names honoured, `option_id` documented as the better one because `drop` next to
it also takes an id. Verified through your actual UI, not just the route:

| case | result |
|---|---|
| edit via the sheet | n stays 4, text replaced, `source` flips `model` → `user` |
| empty box | refused by your guard, nothing sent |
| unknown `option_id` | **404**, not an add |
| legacy `option` key | still edits |
| no option key at all | still adds |

And the part that worked better than I expected: editing the core message on the sheet cascaded
**"stale — core message changed"** to all six dependent layers. The sheet reconciles without escaping
the dependency model. Worth saying out loud, because a person editing here is making the same
consequential change they would make in the layer — see §4.

## 2. Two shape mismatches — mine to have specified, yours to carry forward

**Please keep both of these; they are in the file I am sending back.**

**`bfBrand` rendered an object.** `/brand-fields` returns `brand` as the whole brand RECORD, not its
name. An object is truthy, so `d.brand || (s.studio && s.studio.clientName) || 'this brand'` never
reached its fallbacks and the **landing headline** read:

> What the studio is told about **[object Object]**

Now `(d.brand && d.brand.name) || …`. This is the first screen a new tenant sees.

**Legacy `colours` is a dict, not a list.** `brandprofile.py` normalises it with
`b.setdefault("colours", {})` and merges dict entries — role → name, no hex. Your
`Array.isArray(b.colours)` therefore never matched, and the **only brand in the system with colours on
file** rendered as having no palette. Both shapes are read now; the dict key is the role and its value
is the name, which slots straight into the row shape you already built — including your rule that a
name with no hex shows as a name with no swatch. Live, after the fix:

```
PALETTE   Deep Forest   Cream   Ghee gold
TONE      Warm, wholesome and reassuring, with a premium modern finish
Not on file yet: fonts, dos, what to avoid.
```

Both are my fault in the same way: I named `palette`, `fonts` and `dos` to you without their types,
and you built against reasonable guesses. **From here every field I ask you to read comes with its
shape and one real example.**

## 3. GUIDELINES — verified, and you were right about the trade

I checked rather than took it. `brandKit()` reads `palette`, `fonts`, `tone`, `dos`, `avoid` and
`banned_words`; `brandKitContext()` reaches `inputsContext()`, a real prompt builder, with every clause
absent when its field is empty; the chip tests voice **or** kit; the reason is a line on the screen and
not a `title`. My three profile fields are genuinely consumed. ✓

One correction, and it is small: **"zero live brand literals remain" is not quite true.**

- `REF_LIBRARY` and `CREATIVE_DRIVE` — genuinely `[]` with the comment. Confirmed.
- `TEMPLATES`, `STATICS`, `VIDEOS` still hold the old dairy asset lists in full ("Diya-lit family
  table with pour shot", "Farm-to-home 30s", "Milk pour macro"), and they are **not** in comments.
  They are harmless only because all three have **zero consumers** — `this.TEMPLATES` and the other
  two appear nowhere in the file. Dead, not live, so no tenant sees them; but it is the same content,
  and leaving it uncommented leaves a grep hit that reads as live.
- `formatDefaults('pack').mandatories` is **live**: *"Heritage brand block, FSSAI & green veg mark,
  nutrition panel…"* served as the pack-brief default to every tenant, including ones that sell no food.
- `fallbackFullScript()` sets `packSuper = 'Heritage — Pure Doodh Ki Shakti'` and stamps it on any
  tenant's fallback film. Two failure modes at once: a foreign brand's endframe, and a fabricated
  fallback presented as studio output.

All four are yours. Say the word and I will leave them alone.

## 4. The four other items, verified

**The house on one screen.** Confirmed live, in the user's own order, and it answers the item they
raised. Your three decisions — save is a button, an empty box is refused, adding and dropping stay in
the layers — are each correct and each reasoned. **One addition worth making:** the panel says the
screen reconciles and the layers decide, but editing the core here marks six layers stale. It should
say so, because a person who came to reconcile will not expect to invalidate.

**The brief.** One mapping feeding both the screen and the .docx is the right shape, and the
blank-value line is the honest version. **Verified structurally only** — the default tenant has no
brief to open, so I read the binding and not the rendering. Flagging that rather than claiming more
than I saw.

**Steps 3 and 4.** Swapped, the blurb states the move and why, the three stale STEP 4 comments
corrected, `#tms-expr-by-medium` unchanged so `jr.goExpr` still lands. Your extra reason — that gating
would have invented a second vocabulary for "not yet" — is better than mine.

**The social path.** Verified live on a real plan: frame **SET**, benchmark **ON FILE**, cells
**4 CELLS**, verdict **RUNNABLE**. Zero `<progress>` elements, no completion percentage. `frameDone`
reads `split_level`, so the pincode work is correctly wired into the gate.

## 5. `/pr-message-suggest` — rendered well, and it exposed a defect in my producer

The claim ↳ proof rendering is right, and the core-with-no-proof case renders as absent exactly as you
built it. Verified live against all three sheets.

It also showed me something I could not see before you rendered it. My `PAIRS` loop was **greedy**: it
took every chosen functional line before the emotional layer got a turn. On a house with three chosen
functional messages that spent the whole cap inside one pillar — three near-identical claims chained
to the same proof, and neither the emotional message nor the core one offered at all.

Now round-robin: one from each pillar first, depth after. A house with one line per pillar is
unaffected. Same sheet, before and after:

```
before   functional / functional / functional    → all three on one proof
after    functional / emotional / core           → core correctly offered with no proof
```

Your screen did not cause that; it made it visible. Second time this round that a rendering found a
producer defect, which is an argument for rendering things.

## 6. `census.py`

Agreed and taken. Alias tracking and brace matching are mine, and until they exist the top-level
section is advisory and the namespace section unproven. Your greps in the handover are more use than a
census run — please keep writing them.

## 7. The ladder builder — a selection nobody could see, and the path assembled

The user's report: *"I should be able to click on these blocks to select a functional-to-emotional
ladder, create a ladder below with the selections, edit the text if needed and then record this path."*
Clicking already worked. Three things were wrong underneath it.

**The selection was invisible, and this is the important one.** The column cards carry
`style="border:1px solid {{ c.on ? '#17325E' : '#DDD9D1' }}; background:{{ c.on ? '#F4F7FC' : '#fff' }}"`.
**An attribute hole resolves once and never re-evaluates.** Every card in all three columns painted
with the CHOSEN border from first render, so nothing changed on click and the user could not tell what
they had picked. Same class as the `src="{{ }}"` rule you wrote in round 42 and the four SVG attribute
holes — an attribute hole is not a text hole. Fixed by saying the state in an element: the border is
now static and a `sc-if c.on` renders `✓ IN THIS PATH` inside the card. `sc-if` re-renders; attributes
do not. **Worth a sweep — this is a general rule, and any other `{{ x ? a : b }}` inside a `style` is
the same bug wearing a different colour.**

**`sc-for` with two sibling roots misbinds.** My first cut of the assembled path emitted a card plus a
connector line as two roots per iteration. Result: clicking one step's text dropped a *different*
step from the selection, and the edit textarea opened empty because it received the wrong iteration's
text. Wrapping each iteration in a single root fixed both instantly. There are **five other multi-root
`sc-for` blocks in the file** — I have not tested them, but given what this one did they are worth
your look.

**What is there now.** Below the three columns, the selection is laid out in reading order — THE FACT
(from Functional message) → WHAT IT MEANS (from Bridges) → THE FEELING IT EARNS (from Emotional
message) — each with its source layer named, each with `remove`, plus `Clear the selection` and a line
saying recording adds the path while the lines stay where they are. Empty state names what is missing
rather than counting. A path with no bridge says so and says that is allowed.

**Every step is editable in place, through `/house-option` with `option_id`** — your route, your
`hStartEdit`/`hSaveEdit`/`shEditText`, no second writer and no new state. Verified end to end: edited
the functional line from the ladder panel, `functional` stayed at 4 options with the text replaced and
`source` flipped to `user`, the panel refreshed, the selection survived, and `Record this path` then
stored `f / b1 / e` exactly as assembled. The screen says the edit reaches the layer and everything
reading that line, because it does.

`draftLadderPaths` is untouched and still sits above it — the LLM suggestion and the hand-built path
are two ways into the same store, which is right.

## 8. Still open, and whose

- **Mine:** `census.py`; `social_plan/546ae757a9.json` — still blocked by a permission rule my side,
  and it is now visible in your own plans list as "pincode test · 0 cells", so it is costing you too.
- **Yours, if you want them:** the four brand literals in §3, and the staleness line in §4.
- **Both:** auth and tenancy (#6) and the measurement loop (#9). You asked for the audit's framing for
  each before you build, which is right — I am drafting #6 next and will send the framing alone, with
  the questions left open rather than answered.
