# Ask Design — round 32: everything the small and medium items need on screen

One document rather than two, covering the frontend for **all five completed small items** and the
**three medium items**. Round 31 (the two Media sub-tabs and geography) still stands and is not
repeated — if that is in flight, this is the queue behind it.

**Base:** the attached zip. It is your round-30 file plus my changes in §1, which you must not lose.

**Where the shapes are settled**, they are given verbatim from the live payloads. **Where they are not**
— brand setup and channel weights — the *requirement* is specified and the shapes follow with the
build, which I am starting now. The hard part of those two is information architecture, not key names,
so there is enough here to start.

---

## 1. What I changed in your file — 14 hunks, do not lose them

This is the third round where a fix of mine has been at risk, so it is first. **87 lines added, 15
removed, across 14 hunks.** All of it is the audit's F1: fabricated performance data.

### The four sites

| Where | Was | Now |
|---|---|---|
| Home, "this week at a glance" | `2.4M` / `6.1%` / `18` / `3.2×` as literal markup | one panel: *"No delivery data is connected"* |
| Home, live-campaign bars | widths hard-coded at 72 / 48 / 31% | one panel: *"Nothing is measuring campaigns yet"* |
| Home, approval queue | four invented rows naming people and times | `createdQueue` only, plus a **`queueEmpty`** state |
| Campaigns tab | the whole `ANALYSIS` literal — sales in crore, market share, CPC, CPV, channel spend | one honest panel with *what it would take*, gated on **`analysisConnected`** |

### Three new bag keys — keep them

- **`queueEmpty`** — `queue.length === 0`. The approval list can now genuinely be empty, and without
  this the card is the blank box we have fixed three times already.
- **`analysisConnected`** — `!!(s.analysisData && (s.analysisData.campaigns || []).length)`.
  **Derived, not hard-coded false**, so the Campaigns tab turns itself on the day something populates
  it rather than needing this gate found and removed.
- **`analysisEmpty`** — its inverse, for the panel.

### The one I want you to read the reasoning on

`generateInsights` built its model prompt **from** `ANALYSIS` and `COHORTS` — so the "real" AI path
asked a model to analyse numbers that did not exist, and its catch branch fell back to four hard-coded
insights quoting invented figures. The insights block is now **inside** the `analysisConnected` gate,
*and* the handler refuses independently. Two locks on purpose: a gate in a template is one refactor
away from being removed.

`ANALYSIS` and `COHORTS` are **kept**, annotated as sample shapes, because the renderer will need them
when actuals land. Do not read a figure out of them and put it on a screen.

**Not touched, deliberately:** the demo *content* rows — sample briefs, history items. Those are seed
content, not fabricated measurements, and whether the product ships with sample data at all is a
product decision rather than a defect.

---

## 2. Small items — shapes settled, build against these

### 2a. The Big Idea, on the Campaign screen

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

### 2b. Prompt guides, on every producer panel

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

### 2c. Distributor ROI and the channel contribution gate, on Sales enabler

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

### 2d. Retail media — mostly free

`media.LEAVES` has an eleventh leaf, `retail_media` (label "Retail media"). Any picker built from the
payload gets it automatically — worth confirming yours are, rather than assuming.

One thing to say on screen where it appears: it is deliberately **not** under Digital, because it is the
one medium that is simultaneously a media buy and a trade negotiation. Blinkit's per-SKU listing fee
comes back as ad-wallet credit, so the same rupee is a distribution cost and a media budget depending
on which desk is looking. Filed under Digital it is invisible to the trade desk; under Trade it is
invisible to the media plan.

### 2e. There is real data now

Four stores that had never held a document now hold one, in the `default` tenant: a complete Heritage
PR sheet (`ready`, release written, carrying a declared message), the brand's media map (four real
mastheads), a competitive picture (five real dairy competitors, at the **free** level with share of
voice correctly unavailable), and a social plan (four AP/Telangana cities, verdict **runnable**).

**Build the round-31 screens against these rather than against fixtures.** Every defect this project has
actually hit was found by opening a screen with real data.

---

## 3. Medium items — the requirement, with shapes following

### 3a. Media sub-tabs — see round 31

Unchanged. Competitive intelligence and Social campaigns as sub-tabs under Media, with the strip
alongside Strategy. Now buildable against real documents, per §2e.

### 3b. Brand setup as the portal's entry point

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

### 3c. Channel weights, and the split enforced against them

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

## 4. Two constraints worth knowing

**The nav is full.** Eleven items, and per the earlier measurements it needs the wrap below 1450px.
Neither geography nor the social campaign manager gets a top-level door — geography is a picker, the
campaign manager is a Media sub-tab. Brand setup replaces the Studio-settings entry rather than adding
a twelfth.

**One tenant per process.** Every store binds its directory at import, including the three asset
directories I scoped this round. Fine for a dedicated deployment per client; serving several tenants
from one process needs those to become per-request calls. Not your problem to solve, but it bounds what
"multi-tenant" can mean on screen until it changes.

---

## What to send back

`app.dc.html` and your note. Please build on the attached base so §1 does not have to happen a fourth
time — and flag anything in §3 where the requirement is clear but you would rather wait for the shapes
than guess at the layout.
