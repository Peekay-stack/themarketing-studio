# ASK_DESIGN_40 — two things to build, four to review, and a defect of mine you should know about

Base: **`dc157e00`**. checkfe 8/8 (four sentinels), test_tools 18/18, parse probe clean, CRLF 0.

Round 39 is adopted and unchanged except where noted below. Everything here came out of a person using
the portal and giving ten findings — six are closed, and these are what is left that touches your side.

## 1. To build: the social grid's new levels and the optimisation event

Backend done and served; the panel is yours. Two additions to `/social-plan`'s view:

**`split_levels` has a fifth entry, `pincode`**, between `city` and `radius`:

| field | type |
|---|---|
| `label` | `"Pincodes within a city"` |
| `what` | one line |
| `note` | why it exists and what it will not check |

A cell at this level takes `pincodes` — a list of strings, or a comma/space/semicolon-separated string,
either works. Stored as `pincodes: []` plus `n_pincodes: int`, so a row can read "12 pincodes in
Hyderabad" without counting a string.

**Three refusals worth rendering as themselves rather than as one error:**

- *format* — six digits, not starting zero. `"Not a pincode format: 050001. …Whether a well-formed one
  exists is not something this studio can check — the platform will tell you."` **That second sentence
  is load-bearing.** There is no pincode directory here, so existence is not verified, and a screen that
  implied it was would be making a claim I cannot support.
- *empty* — points at the city level: **a city cell already means every pincode in it.** That is the
  "all pincodes" option and it already existed; please say so rather than adding a checkbox that
  duplicates a level.
- *duplicate* — two pincode cells in one city are **not** duplicates if they buy different pincodes;
  identical sets are refused. The whole point of the level is buying some and not others.

**`optimisation` is a new vocabulary of seven, and it is NOT the strategic objective.** This is the one
place I would ask you to hold a line on the layout:

```
plan.ROLES      reach · proof · conversion · advocacy      what a channel is FOR
OPTIMISATION    reach · impressions · video_views · engagement · traffic · leads · conversions
                                                            what the platform COUNTS
```

They share the words *reach* and *conversion* and mean different things. **The learning threshold counts
the optimisation event**, so fifty purchases a week and fifty link clicks a week are the same number and
nowhere near the same bar. Each entry carries `rarity` (`common` | `moderate` | `rare`) and a
`per_week_note` saying whether the threshold will bite. `optimisation_note` on the payload states the
distinction in one sentence — please put it where the two pickers sit, not in a tooltip.

Two fields, two pickers. One combined control would be one question for two decisions.

## 2. To build or to hand back: the medium expression and role-by-medium

Still not started, and it is the one item from testing I have deliberately not touched. The request was:
*"Medium expression is looking redundant before the big idea… we should merge it in the role by medium
table and cue a message which helps to relay the role better without changing the meaning of campaign
idea."*

My reading, and where I want your judgement: the safe version is **not a merge**. The platform's
per-medium expression is a *message*; a channel role is a *job*. Showing the expression inside the
role-by-medium table, read-only and sourced, gives the person what they asked for — the message beside
the role, cueing what the role has to relay — without creating a second home for the line or letting the
table edit the platform. A true merge risks losing the message, which is the thing the platform exists
to hold.

If you agree, it is a small round on your side (a sourced column, no new writes) and I have left it
alone. If you think it wants more than that, say so and I will build whatever server side it needs.

## 3. To review: four changes I made inside your file

All four are functional-first. The wording and styling are yours to take over, and I have kept each to
as few bag keys as I could.

- **The POS piece's line** (re-applied; sentinel 4). A field under the route cards, prefilled from the
  chosen route, with provenance and a "Use the route's line" revert. `posmLineValue` / `posmLineFrom` /
  `posmLineEdited`. **Still unverified by me: typing into it** — synthetic events do not reach the
  runtime and real keystrokes need a screenshot this pane will not produce. The binding is identical in
  shape to `onKvBrief`.
- **The cast-lock band** (you asked for this, with the constraint that the precondition be visible
  before it blocks). A standing amber band **above** the storyboard heading and the Generate-all button;
  pressing anyway does not add a message, it turns the same band red and sharpens the sentence.
  `castNeedsLockText` plus three colour keys. Verified: 0 API calls without a locked cast on both the
  single-frame and batch paths, 1 with.
- **The on-ground element cards.** `"Brief it first"` is now `"Develop from the idea"`, because that gate
  was this screen's invention — `producers.element_brief` already accepts `'(nothing yet)'` and refuses
  only when there is no *idea*. Each card also carries a relationship line (`el.kvLabel` / `el.kvWhy`)
  and a Render control (see §4).
- **The `medium` cell** on the plan's channels layer, from round 38's ask — unchanged since you adopted
  it, listed only so the set is complete.

## 4. New on the on-ground cards: a producer that now exists

`POST /activation-element-image` is live and renders. The panel used to say *"no producer is wired for
onground artwork yet"*, which was true; it is not any more.

**How it renders is the server's decision, from `activation.kv_role(element, venue)`** — derived from the
element and the venue's own intercept and dwell, not a table. This was the answer to "should the stall
link to the KV or be independent?", which was *"it could be either, based on the selected idea (RWA or
college campus or modern trade outlet)"*:

| role | behaviour | example |
|---|---|---|
| `source` | KV passed as a reference, prompt says keep it — the piece *is* the artwork | van, truck, leave-behind; a stall at a mall atrium or transit hub |
| `reference` | rendered from the brief, KV only for palette and codes | a stall at an RWA or a college, where people stop and talk |
| `none` | **409, refused** — "not a surface for a visual… there is nothing here to render" | promoter training, permissions, capture |

A `source` element with **no KV yet** is also refused (409) rather than invented, because the point of
that role is that the piece is made of the visual.

The card reads `el.canRender` (false on `none`), `el.renderLabel`, `el.shotUrl`, `el.shotNote`, and
`el.shotWhy` for the refusal. **`hint-placeholder-val` on the render `sc-if` is `true`** so the control
shows in your preview before any kit sheet has loaded.

## 5. A defect of mine, found after I had written the previous paragraph

I wired the card to read `og.kit` and **never loaded it.** The only reference to `/activation-kit` in the
file was my own comment. So `ogKv` was always `{}`, which meant the relationship line never rendered and
`canRender` never went false — putting a Render button on promoter training and permissions and leaving
the server to refuse it.

Fixed: `useOgIdea` now fetches the kit sheet alongside the elements it already fetched, on the same
trigger and for the same idea. Verified against the live routes — `stall` comes back `reference`,
`education` comes back `none`.

Worth naming because it is the exact failure I have twice sent back to you: **a consumer with no
producer reads as a feature that simply had nothing to say.** checkfe cannot see it — the hole resolved
to a bag key, the key resolved to a real expression, and the expression resolved to an empty object.

## 6. Not yours, and not done

`REF_LIBRARY` / `CREATIVE_DRIVE` (yours, with the join round). The join itself is mine and next. Also
mine and unstarted: external Excel/PPT into the social plans — the parsers are already installed for the
brief importer, so it is reuse rather than new capability.
