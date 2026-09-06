# Ask Design — round 31: two Media sub-tabs

Round 30 is integrated. `checkfe` passes all seven — 522/522 `sc-if`, 252/252 `sc-for`, 2059/2059
`<div>`, 643 unique members, 275 handlers reaching the bag. Your pre-merge counts matched mine exactly.
Verified live: the two cards render 8 `can` and 7 `cannot` rows, the stored-work card stands on its own,
and the "being built first" contradiction is gone. LF adopted — thank you for normalising; my Python
writes had been silently converting the file to CRLF, which is what made the diffs noisy.

**Base:** the attached zip. It is your round-30 file plus one fix (§2).

---

## 1. The rail: no new nav items. Your grouping is not needed.

Answered on this side, and the answer questions the premise rather than picking between your options.
**Neither new backend gets a top-level door**, so the nav stays at eleven and nothing has to be
restructured.

- **Geography is a vocabulary, not a destination.** Nobody navigates to "Geography" to do a job — they
  pick states and cities while doing something else, the way languages already work inside PR. It
  becomes a picker inside the screens that need it.
- **The social campaign manager is Media's own subject.** Media already says it owns weight and money;
  a geography-wise social budget *is* weight and money, for social. It belongs as a sub-tab, not a peer.

So the round goes on the screens instead of the chrome. Your grouping proposal was a good answer to the
question as I'd posed it, and worth keeping in the file for whenever a genuinely new destination appears.

### A correction to §1 of my round-30 note

I told you the nav "fits by 0 px" at 1600. **That was wrong — there are 66 px of real headroom.** I had
read `scrollWidth === clientWidth` as "exactly at the limit", but `scrollWidth` returns the *max* of
content and client width, so it reports a zero deficit for any fit at all. Measuring the actual content
edge gives 775 px inside 841 px available.

The clipping findings are unaffected — those had `scrollWidth > clientWidth`, which is genuine overflow,
and I confirmed them by comparing each item's own right edge against the nav's, which is how I could
name *which* items were lost. The fix stands. But the "zero headroom" line was part of my argument for
restructuring, and it was weaker than I made it sound. 66 px is room for one short label, not for
another "Sales enabler".

## 2. One fix in your file: `medNoCan`

Your note says both cards now speak in all five states. The five states exist, but they are
**distributed across the two cards rather than present on each** — and the *can* card is still one short.

| state | CAN card | CANNOT card |
|---|---|---|
| no server | `medNothingToList` | `medNothingToList` |
| answered with nothing | `medAnsweredEmpty` | — |
| shape not read | `medStatusUnread` | `medStatusUnread` |
| no gaps | — | `medNoGaps` |
| gaps listed | — | `medHasCannot` |

Read out of your round-30 file: the *can* card's `sc-if`s are `medNothingToList`, `medAnsweredEmpty`,
`medStatusUnread`, `medHasCan`. The *cannot* card's are `medHasCannot`, `medNothingToList`,
`medStatusUnread`, `medNoGaps`. **The cannot card is genuinely exhaustive** — `medNoGaps` no longer
requiring `can` rows is what did it, and I checked every combination.

The can card is not, because both of its middle states require `!cannot.length`:

```js
medAnsweredEmpty: !!st && !can.length && !cannot.length && Object.keys(st).length === 0,
medStatusUnread:  !!st && !can.length && !cannot.length && Object.keys(st).length > 0,
```

So **status present + `can` empty + `cannot` non-empty** satisfies none of the four: heading, subhead,
nothing. Added:

```js
medNoCan: !!st && !can.length && cannot.length > 0,
```

Reachable how? The desk serves both lists today, so not by accident. It is reachable the way it bit us
last round: **a renamed key.** If `can` ever moves and `cannot` does not, that is exactly this state —
and the amber "shape not read" line would not fire either, because `cannot` parsed fine. The card would
just be empty, on a screen whose entire argument is that an empty card reads as finished.

I checked it as algebra rather than by eye, because this class has now appeared three times: for each
card, every combination of (status present, `can` rows, `cannot` rows, key count) must satisfy exactly
one state. Across all ten combinations both cards now resolve to exactly one — no blanks, no doubles.
Worth running that check whenever a card grows a state, since the failure is invisible by inspection.

---

## 3. Media becomes sub-tabbed

Media is one screen today and needs a strip: **Strategy** (what you built), **Competitive**, **Social
campaigns**. Same pattern as Execution's — a local table of labels, since these are screen decisions,
not server ones. No `/producers`-style filtering needed here.

Both new sub-tabs are live and tested. Every vocabulary below is a **dict keyed by id** — reach for
`prSeq` as usual.

---

## 4. Competitive intelligence

`GET /media-competitive?brand=<name>&period=<YYYY|YYYY-Qn|YYYY-MM>`

```
brand slug currency competitors[] observations[] set_complete{} som period periods[]
level{} sov{} esov{} presence{} media[] source_kinds{} findings[] blocking[] why_before_the_split
```

Writes, all returning the same full view: `POST /media-competitor` `{brand, competitor:{name, us?,
note?, id?}}` · `/media-competitor-drop` `{brand, id}` · `/media-competitive-set` `{brand, complete,
note}` · `/media-observation` `{brand, observation:{competitor, period, medium?, source_kind, source,
spend?, currency?, running?, creative?, as_of?}}` · `/media-observation-drop` `{brand, id}` ·
`/media-market-share` `{brand, value, source, as_of?, note?}`.

**This module's whole point is what it refuses to compute, so the refusals are the screen.** Four
things that must land:

**`level.level`** is `licensed` | `disclosed` | `free` | `empty`, and it is the headline. It answers
"can we do share of voice?" — which depends entirely on what the studio can buy. `level.levels` is the
full three-level table and `level.free_sources` is a catalogue of the free ad libraries *with each one's
real limit* (they publish spend for political ads only). At the `free` level, share of voice is
**unavailable, not zero** — a state to report, never a gap to fill with an estimate.

**`sov.total.available === false` carries `missing` and `why`.** Render the names. A participant with no
figure contributes nothing to the denominator and inflates every other share *while the shares still sum
to 100* — so there is nothing on screen to show it happened, which is why the refusal exists. The remedy
in `why` is real and worth surfacing: enter a **measured zero** where a competitor was checked and ran
nothing. That is a fact, and it is different from an absence.

**`sov.category_claim`** decides how a share describes itself. `false` means it is a share of the
*listed set*, not of the category — the weaker, true claim. `sov.basis` is the sentence to print.
`sov.by_medium` is keyed by medium and each entry has its own `available`/`missing`, so some media can be
computable while others are not; `media_note` explains when an annual-only competitor is the reason.

**`esov`** needs both terms or nothing. When `available` is false, `why` says which is missing.
`esov.basis` is `{claim, source, dispute, note}` — same shape as the Plan screen's citation card, so the
disclosure you built there should transplant. **`esov.caution`** appears when the set is undeclared:
subtracting a category share of market from a listed-set share of voice compares two different
universes. If it is present it must be visible, not behind a toggle.

There is no AVE here and no blended figure, exactly as in PR coverage.

## 5. Social campaigns

`GET /social-plans` · `POST /social-plan` `{brand, name?, plan?}` · `GET /social-plan/{id}` — all
returning:

```
plan{} cells[] feasibility{} allocation{equal,population,entered} tradeoffs[]
budget_modes{} split_levels{} benchmark_kinds{} objectives{} language_gaps[]
counts{} findings[] blocking[] what_this_cannot_do
```

Writes: `/social-plan-frame` `{id, objective?, budget?, currency?, days?, budget_mode?, split_level?}` ·
`/social-plan-benchmark` `{id, kind, source, cpa?, cpm?, as_of?}` · `/social-cell` `{id, cell:{level,
state?, name?, radius_km?, budget?, floor?, phase?, priority?, note?}}` · `/social-cell-drop`
`{id, cell_id}`.

**`feasibility` is the screen's headline, and `verdict` is the word to lead with.**

| verdict | means | treatment |
|---|---|---|
| `runnable` | every cell clears the threshold | pass |
| `too_fine` | more cells than the money supports | **blocking** — `max_cells` says how many it does support |
| `impossible` | below the threshold at any split, including one cell | **blocking** |
| `reported` | a reach objective — **no pass or fail** | see below |

A conversion ad set needs about 50 optimisation events in a rolling week (`rule`, `window_days`,
`rule_source`) and dividing the budget does not divide the threshold. Seventy cities on ₹40 lakh at a
₹250 cost per action returns `too_fine — about 37 cells supportable`. That is the most useful thing this
screen does and it happens before any money moves.

**Reach objectives get the arithmetic and no verdict.** `verdict: "reported"`, `basis: "impressions"`,
and there is deliberately no `max_cells`. There is no defensible universal target frequency, so none is
asserted — please do not add a pass/fail read, a target line or a rating to that panel.
`implied_weekly_frequency` arrives with a `frequency_caveat` that must travel with it: it divides by a
Census 2011 municipal population, which is not the platform's boundary and counts people rather than
reachable accounts.

**No default cost anywhere.** There is no default CPA or CPM in the backend and the screen must not
prefill one — every feasibility figure divides by it, so an assumed number would produce a confident
verdict nobody chose. `benchmark_kinds` grades provenance: `own_history` (high) / `platform_estimate`
(medium, and systematically optimistic) / `category` (low, sizes an order of magnitude and should not be
what a plan is committed against).

**`allocation` has three modes and `population` refuses.** When a cell has no population figure it
returns `available: false` naming the cells — same reason as share of voice. `entered` carries
`reconciles`; when false, `note` states the difference and says which of the two is wrong is a decision,
not something to round away.

**`tradeoffs` is four rows of `{id, question, gain, give_up, resolve, source}`** — pooling, split depth,
radius, language. Render them as **decisions**, not warnings: each has a real gain and a real cost and
the choice belongs to a person. The pooling one is the important one — a pooled budget starves expensive
markets, and expensive correlates with new and small, which is exactly where a growth plan is spending.
`budget_modes.pooled.mitigation` is the minimum-spend floor.

**`what_this_cannot_do`** should be on screen, not buried: this cannot say whether a campaign is
*working*. That needs delivery data, and nothing here ranks a geography by performance.

## 6. Geography as a picker, not a screen

`GET /geo-status` → `states[] zones{} aliases{} pop_basis{} threshold_caveat seed{} counts{}
why_population_is_not_reach`

`GET /geo-cities?min_pop=500000&basis=census_2011_city&states=mh,gj` → `available basis basis_label
min_pop rows[] count states_covered[] source caveat threshold_caveat complete gap{} language_gaps[]`

Each row: `{name, state, state_label, zone, pop, basis, source, languages}`. All 36 states and UTs;
names, codes and old names all resolve server-side, so a free-text field is fine — "Maharashtra", "mh",
"Orissa" and "J&K" all land.

Three things the picker has to carry:

- **`complete: false` and `gap`.** The seeded city list is knowingly short — two verified extractions
  from the source did not meet, and roughly fifteen cities between 9.6 lakh and 12 lakh are named in
  `gap.names_known` but absent, because an unverified figure in a seed is indistinguishable from a fact.
  A list of seventy that reads as the whole 5-lakh-plus set is the failure here.
- **`threshold_caveat`.** A 5-lakh cutoff on Census 2011 is a *2011* cutoff. Census 2021 was postponed
  and Census 2027 enumerates on 1 March 2027, so the list is short at the bottom by an amount nobody can
  state per city. One line, visible near the threshold control.
- **`language_gaps`.** Ten of thirty-six states have a principal language the studio cannot write in.
  This belongs *before* the money is committed, not in a footnote — buying a state in Hindi and hoping
  is a media cost with no message behind it.

And `pop_basis` is the one gate that matters: a population is **not** a reachable audience. Meta's
"Hyderabad" is its own boundary with an optional radius; the Census's is the Municipal Corporation. The
figures are for prioritising which cities matter, never for sizing reach, and there is deliberately no
blended field — same discipline as PR keeping circulation and digital apart.
`why_population_is_not_reach` is the sentence for it.

---

## What to send back

`app.dc.html` and your note. Flag any shape here you had to guess around — everything above is dumped
from the live payloads rather than written from memory, so a mismatch means I documented it wrong and I'd
rather fix the backend than have you read a worse key, as with `brand_share` last round.
