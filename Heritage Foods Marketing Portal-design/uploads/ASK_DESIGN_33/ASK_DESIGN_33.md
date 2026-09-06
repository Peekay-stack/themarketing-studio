# Review of the round-31 return — two fixes for you, four on my side

Reviewed against the **live payloads with real data behind them**, not fixtures. `checkfe` passes all
seven on your file: 594/594 `sc-if`, 285/285 `sc-for`, 2242/2242 `<div>`, 677 unique members, 18 bag
methods spread, 290 handlers reaching the bag.

The two sub-tabs are good work. `prSeq` is used throughout, every route I specified is called, the
`names()` helper handles list-or-dict for `missing`, the level and verdict tone maps are clean, and
`socIsReported` shows you took the "a reach objective gets no verdict" rule seriously. **Two reads are
wrong**, and reviewing them turned up **four problems on my side** — including one that made your
screen look broken when it was correct.

**Base:** the attached zip. It is your round-31 file **merged with my F1 work** — see §3.

---

## 1. Two reads to fix

### 1a. The per-medium share never renders — `our_share`, not `share`

```js
value: m.share != null ? m.share + '%' : (m.value != null ? m.value + '%' : '—')
```

A `by_medium` entry carries `available, our_share, label, medium, missing, why, rows, category_spend`.
Neither `share` nor `value` exists on it, so **every per-medium share renders `—` even when
`available: true`** — and that is the core number of the whole screen. Verified against the real shape:
yours returns `—` where the answer is `25%`.

The confusion is understandable: `rows[]` inside that entry *does* have `share` per participant. It is
the entry-level figure that is `our_share`. I am keeping the name — `share` alone would not say share
of what, or whose.

### 1b. Impressions never render on a reach objective — `impressions_weekly`

```js
socImpressions: feas && feas.impressions != null ? String(feas.impressions) : ''
```

The key is `impressions_weekly` (and `impressions_per_cell_weekly` beside it). Yours returns blank
where the answer is `5,263,157`. `implied_weekly_frequency` and `frequency_caveat` you read correctly.

---

## 2. Four fixes on my side

### 2a. Your screen said "Nothing recorded" and it was right

This is the one worth reading. The Competitive tab rendered *"Nothing recorded"* against a Heritage
competitive picture that genuinely existed — five real dairy competitors, five observations.

**The screen was correct and my storage key was ambiguous.** The brand *profile* is called
"Heritage Foods" (slug `heritage-foods`); the *plan's* `brand` field says "Heritage" (slug `heritage`).
Per-brand stores — the competitive picture, the PR media map — slugged whatever name they were handed,
so a document written from the plan was invisible to a screen asking from the brand chip.

Fixed by keying through a new `brandprofile.brand_key()`, so case and spacing variants of a real brand
name converge on one document. And the two Heritage documents are corrected to the canonical key, so
your screen now shows all five competitors and the level reads **Free ad libraries**.

One thing I tried and reverted, because it is the interesting part: I first keyed through
`brandprofile.resolve()`, which is the obvious function for this. It is not — `resolve` exists for
*grounding* ("whose guidelines apply to this generation") and therefore falls back to the **active
profile** when it cannot match. Keying through it made `brand_key("Parle G")` return `heritage-foods`,
which would have merged two clients' documents. `brand_key` now uses exact `by_name` and no fallback: an
unmatched name keys on its own slug and cannot collide.

**Still open, and it needs a decision rather than a guess:** "Heritage" and "Heritage Foods" are two
names for one brand, and nothing reconciles them. The proper fix is for per-brand documents to store the
brand **id** resolved once at write time. That is a change with a migration behind it, so I have not
done it quietly.

### 2b. Observations showed a hex id — you were right to reach for `competitor_name`

Your `x.competitor_name || x.competitor` fell through to the raw id, because observations only stored
`competitor`. The gap was mine: every other payload here resolves its own labels — `state_label`,
`kind_label`, `phase_label` — and a screen forced to join an id to a name will eventually render the id.
`competitor_name` and `source_kind_label` are now resolved server-side. No frontend change needed.

### 2c. The levels table had no explanations — `means` was my outlier

You read `x.what || x.why`. My entries carried `label, means, gives, costs` — so the three levels
rendered with their labels and **no explanation at all**. Checking the siblings settled it: `what` is
the house convention (`SPLIT_LEVELS`, `PROMPT_GUIDE`, `media.MEDIA` all use it) and `means` was the
outlier, in `LEVELS` and `BUDGET_MODES` only. Renamed to `what`. Confirmed live — the three levels now
show their text.

### 2d. `verdict_label` did not exist, and you reached for it first

`socVerdictLabel: feas.verdict_label || feas.verdict` would have put the raw enum **`too_fine`** on
screen, underscore and all, on the most important panel in the media desk. Added:

| verdict | label |
|---|---|
| `runnable` | Runnable |
| `too_fine` | Too fine to run |
| `impossible` | Below the threshold at any split |
| `reported` | Reported — no pass or fail |

---

## 3. The merge — my F1 work was absent, and that is on me

Your file is built on the round-31 base, which predates the F1 work (fabricated performance data). I
sent round 32 after you had started, so the fabricated figures were back: `2.4M`, `6.1%`, the 72% bar,
"submitted by Ravi", and the whole `ANALYSIS` literal on the Campaigns tab.

**I have merged rather than asking you to redo it.** Twelve exact-match edits re-applied onto your file,
every one hitting exactly once — no collisions with your new work, which sits in a different part of the
file. `checkfe` passes on the merged result: 597/597 `sc-if`, 285/285 `sc-for`, 2235/2235 `<div>`.

Keep these three bag keys, they are load-bearing: **`queueEmpty`**, **`analysisConnected`** (derived
from state, not hard-coded false, so the Campaigns tab turns itself on when actuals land), and
**`analysisEmpty`**.

Two leftovers I noticed while merging, neither urgent: `COHORTS` and `linkEco` sit inside the
`analysisConnected` gate so they are not rendered, and `campaignTypes` is built into the bag but **no
markup consumes it** — dead data carrying a `2.4M reach` string. Yours to delete or wire.

---

## 4. One thing not wired

`/geo-cities` is referenced once but I could not find it driving a city picker. The social cell form
needs it for the 5-lakh list — with `min_pop`, and rendering `complete: false` plus `gap` when the line
sits below the seed's known hole, so seventy cities never read as the whole set. If you left it for a
later round, say so and I will stop looking for it.

---

## 5. There is real data now

Four stores hold real documents in the `default` tenant, so build against these rather than fixtures:

- **Competitive picture** — five real AP/Telangana dairy competitors at the **free** level, share of
  voice correctly unavailable, naming all five as missing spend.
- **Social plan** — four cities, verdict **runnable**, 466.7 events per cell against a threshold of 50.
- **PR sheet** — `ready`, release written at 104 words, carrying a declared message.
- **Media map** — four real mastheads with their freshness bands.

Every defect this project has actually hit was found by opening a screen with real data. That is how
§2a was found, and it is the reason it was worth finding.

---

## 6. Still to build — the small items' frontend

These shapes are settled and verified against live payloads. Renumbered from round 32; **that document
is superseded and its attached `app.dc.html` must not be used as a base** — it predates your round-31
work and building on it would lose your two sub-tabs.

### 6a. The Big Idea, on the Campaign screen

`POST /campaign` accepts `big_idea` and `big_idea_note` in the payload it already sends. Both the save
and read responses now return:

```
big_idea: { text, note, available, campaign,
            platform: { name, idea },
            why_separate, why_missing }
```

**Render the idea and its parent platform together, always.** That is the whole design of the field.
A platform is a territory that lasts years; a big idea is what one campaign does with it this season.
Shown alone, an idea gets treated as the strategy — which is how a platform quietly gets replaced by
whatever this season's idea happened to be, and abandoning platforms annually is the most expensive
habit in brand marketing.

The server **refuses** a big idea that restates the platform, and the refusal text is the teaching —
render it in place as the PR desk renders its refusals:

> *"The big idea is word-for-word the platform's own line. A platform is a territory that lasts years;
> a big idea is what this campaign does with it this season."*

Verified live on Heritage: platform *"500 Before You"*, campaign idea *"Put one of the 500 on her
doorstep: the person who checked her milk this morning, named, at the moment she opens the door."*
Word-for-word and near-restatements (85% shared words) are both refused.

`available: false` is a real state, not an error — `why_missing` says the campaign is still usable
without one because every execution can be briefed from the platform's per-medium expression.

**Also on the wire:** the big idea now rides on the execution brief at
`brief.campaign.big_idea`, so Execution and Video can show it as an input without a second call.

### 6b. Prompt guides, on every producer panel

`GET /producers` and `GET /producers/{kind}` now carry `prompt_guide` per kind:

```
prompt_guide: { available, kind, what, asks, example, avoid,
                cannot_override, additive }
```

Six live producers have one; the retired `media` returns `available: false` with a reason, and a kind
with no guide written says so rather than showing a generic one.

Three things the rendering has to get right:

- **`avoid` is as important as `asks`** — people learn faster from a named failure than a description
  of success. Give it equal weight, not a footnote. Example, verbatim: *"Stacking adjectives —
  'cinematic, emotional, heartwarming, premium'. Those describe how you want the result judged, not
  what the camera does."*
- **`additive` must be visible wherever a prompt box is.** It says the prompt is added to the brief,
  never substituted for it, and names what it cannot override. Without that on screen, a rich prompt
  becomes the way people bypass the plan, and the plan becomes decoration.
- **`example` is deliberately in a different category** from the client's — cement, shampoo, paint,
  tyres, biscuits, steel. Do not "helpfully" swap it for a dairy example: a same-category example gets
  copy-pasted and forty briefs come back describing the same milk.

You already have the affordance for this — the Social producer's "Prompt guide ▾". Extend that pattern.

### 6c. Distributor ROI and the channel contribution gate, on Sales enabler

Two new routes. Both refuse rather than guess, and the refusals carry the reasoning.

**`POST /trade-distributor-roi`** — `{monthly_offtake, margin_pct, stock_at_cost, credit_extended?,
deposits?, infrastructure?, monthly_operating_cost?}` →

```
roi_pct  stock_turns_per_year  investment  investment_parts{}
annual_revenue  annual_margin  annual_net_profit
reading  basis{claim,formula,source,dispute,note}
missing[]  gross_only  understated_investment
```

**The headline is that a distributor does not decide on margin — he decides on return on the capital he
has tied up.** Verified on real numbers: the *same* 8% margin returns **31.8%** on a fast route and
**16.1%** on a slow-collecting one. That contrast is the screen's whole job, so put `roi_pct` and
`stock_turns_per_year` together — turns is the lever.

**`understated_investment` needs a visible treatment.** When `credit_extended` is omitted the return
reads **65.3%** instead of 31.8%. That is not a rounding difference; it is the difference between a
route looking excellent and looking marginal. Show it as a warning on the figure itself, not in a
missing-fields list.

**`POST /trade-contribution`** — `{consumer_price, gross_margin_pct, commission_pct,
fulfilment_per_unit?, storage_pct?, listing_fee?, units_over_fee_period?}` →

```
clears  contribution_pct  contribution_per_unit
cost_to_serve_pct  parts{commission,storage,fulfilment,listing}
breakeven_gross_margin_pct  listing_note  reading  reference{}
```

**`clears: false` is the most valuable output on the Sales screen and should look like it.** On real
Heritage numbers, ₹60 milk at 22% gross margin on quick commerce **loses ₹9.72 a unit** and needs a
38.2% margin; ₹400 ghee at 55% **clears at ₹100 a unit**. So the answer the screen produces is not
"avoid quick commerce" — it is *"list the ghee, not the milk"*, and the UI should make that comparison
easy to run.

`breakeven_gross_margin_pct` is **derived from the entered costs**, not the widely quoted "needs 65%"
rule, because that rule is somebody else's deal. Label it as computed.

`reference` carries published Blinkit / Zepto / Instamart listing costs **for checking a real quote
against** — never as defaults. There are no defaults; the routes refuse without entered figures.

### 6d. Retail media — mostly free

`media.LEAVES` has an eleventh leaf, `retail_media` (label "Retail media"). Any picker built from the
payload gets it automatically — worth confirming yours are, rather than assuming.

One thing to say on screen where it appears: it is deliberately **not** under Digital, because it is the
one medium that is simultaneously a media buy and a trade negotiation. Blinkit's per-SKU listing fee
comes back as ad-wallet credit, so the same rupee is a distribution cost and a media budget depending
on which desk is looking. Filed under Digital it is invisible to the trade desk; under Trade it is
invisible to the media plan.

---

## 7. Still to build — the medium items

### 7a. Brand setup as the portal's entry point

**This is the first thing a new client does, so it is also the first impression.** Today it is a brand
chip and a Studio-settings form. It becomes step 00 of the spine.

The requirement, and the reason it is worth a screen rather than a form:

> Six things are asked for later, separately, by four different modules. Collecting them once is the
> difference between setup being admin and setup being the first strategic act.

| Collect once | Currently re-asked by |
|---|---|
| Competitive set | Media → competitive intelligence |
| Market geography | `brandprofile.market` free text, PR's free-text region, brief prose |
| Languages the brand can be written in | PR media map, social creative |
| Price and margin architecture | Sales enabler, and now both trade calculators |
| Share of market, with its source | ESOV — typed per campaign today |
| **Category entry points and occasions** | Nowhere. Nobody collects it, and it is the most useful strategic input there is |

**Three things the screen must do:**

1. **Tier it.** Five fields open a brief. Everything beyond that is grouped by *what it unlocks*, not by
   form section — "this is what the competitive picture needs", "this is what the trade calculators
   need". A forty-field form nobody finishes is worse than five fields and a named gap. The portal
   already does this well: *"without a house the proof gate cannot run."*
2. **Uploads are grounding, not truth.** A deck or data sheet can be attached, and a figure taken from
   it stays unconfirmed until a person confirms it — the same rule as PR outlets, which enter the map
   `confirmed: false`.
3. **Geography and languages come from the real vocabulary** (`/geo-status`), not free text. Names,
   codes and old names all resolve server-side, so a single input is fine — "Maharashtra", "mh",
   "Orissa" and "J&K" all land.

Shapes follow with the build.

### 7b. Channel weights, and the split enforced against them

**The audit's highest-value gap.** The live plan has seven channels; all seven carry a role and a side;
**none carries a weight.** So the brand/activation split can only be computed on channel count — 43/57
against a declared 60/40, a 17-point gap the plan already flags and nothing can close, because the
control that would close it does not exist.

The requirement:

- A **weight per channel** on the Plan's channels layer, and the declared split **reconciled against
  the sum** rather than against a count.
- The three states must stay distinguishable, exactly as you already handle `declared`:
  no weights at all (expected, not wrong — it is the gap the media desk exists to close);
  **some** weights (the dangerous middle — the split looks computed on spend and is actually computed
  on whatever happens to be filled); and all weights, where the split is finally enforceable.
- `mediaplan.findings()` already reports all three. Render them; do not re-derive.

Shapes follow with the build. One thing worth deciding now on your side: whether a weight is entered as
a percentage or as money. The plan holds a `share`; the social desk holds real currency. If both exist
they will disagree, and the audit's recurring lesson is that two homes for one decision is the failure
mode this codebase keeps hitting.

---

### 7c. Two constraints worth knowing

**The nav is full.** Eleven items, and per the earlier measurements it needs the wrap below 1450px.
Neither geography nor the social campaign manager gets a top-level door — geography is a picker, the
campaign manager is a Media sub-tab. Brand setup replaces the Studio-settings entry rather than adding
a twelfth.

**One tenant per process.** Every store binds its directory at import, including the three asset
directories I scoped this round. Fine for a dedicated deployment per client; serving several tenants
from one process needs those to become per-request calls. Not your problem to solve, but it bounds what
"multi-tenant" can mean on screen until it changes.

## What to send back

`app.dc.html` and a note. **Build on the attached base — it is the only correct one.** §1 is two
one-line changes, §4 is a question, §6 and §7 are the queue.
