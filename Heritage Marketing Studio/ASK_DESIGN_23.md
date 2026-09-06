# ASK_DESIGN_23 — the activation kit sheet, and the shopkeeper's margin story

**This is queued behind round 22, not stacked on top of it.** Build P3 first (the claim gate context,
the return-trip badge, the campaign's proof axis). Come to this once that's landed and shipped back —
or in parallel if you have the bandwidth to split the work, since the two touch completely different
screens (Strategy/Idea platform vs. Onground activation/Sales enabler) and share no code.

## The base

```
app.dc.html      965,900 bytes
sha256           6f7fed38a32aa64f387d28460a06ab106130a316fb55dd81fff2de083df2a045
```

**Identical to round 22's base** — nothing on the frontend changed while this was built. If you've
already applied round 22's changes on top of this file, that's your correct starting point for this
round too; there's no new base to re-diff against.

`tools/checkfe.py` is in this zip as always. Run it, all seven, before sending anything back.

## Why this round exists

**On-ground.** `producers.VENUES` already has eleven venues, each written with real judgement — who it
reaches, who has to say yes, the trap it sets. What it's never had is a single number. Nobody could
look at a chosen idea and see whether the venue is worth booking without reading a paragraph and
guessing. `activation.py` is the numbers layer for the same eleven venues — footfall, intercept,
cost-per-contact, permission lead time, and what a kit still contains once the scale forces something
to drop.

**Trade.** The sales enabler already lets someone type a pitch card and a counter kit brief by hand.
What it's never computed is the number those two fields are supposed to be built on: what a facing of
the pack actually earns a shopkeeper in a week, set against the unbranded alternative he could stock
instead. *"Stock the trust, not just the litre"* is a slogan without a number under it; this is the
number.

## What NOT to build this round

**Do not touch `/activation-idea` or `/activation-elements`.** Both are unchanged and still work exactly
as before. This round adds a NEW step after an idea and its venue are chosen — it doesn't replace
anything in the idea-generation flow.

**Do not persist MRP, trade price, case size or margin percentages anywhere.** There is nowhere in this
codebase they currently live, and inventing storage for them wasn't part of this round — `POST
/trade-margin-story` is a stateless calculator. Collect the numbers in a form, send them, show the
result. If a return visit should remember the last numbers typed, that's fine to do as ordinary
client-side state (same as the POSM style picker remembers its last choice) — just not as a new backend
field.

## 1 · The activation kit sheet

`GET /activation-status` returns the venues, their footfall/intercept ranges, permission lead times,
elements and the three scale tiers — everything a screen needs to render its choices from data:

```json
{
  "venues": { "rwa": {"label": "Apartment society / RWA", "who": "...", "access": "...", "trap": "..."}, ... },
  "footfall": { "rwa": {"footfall": [80, 250], "intercept": [0.20, 0.40], "dwell_min": [3, 8]}, ... },
  "permission_lead": { "rwa": {"lead_days": [7, 21], "cost_tier": "free–low", "formal": true}, ... },
  "elements": { "stall": "...", "van": "...", ... },
  "scales": { "single-site": "Single site, one day", "multi-site": "...", "tour": "..." },
  "drop_order": ["truck", "van", "leave_behind", "prop", "stall", "uniform", "education", "permissions", "capture"],
  "never_dropped": ["capture", "education"]
}
```

Once an idea is chosen and has a venue, call:

```
POST /activation-kit
{ "idea": {...the chosen idea, must include "venue"...},
  "scale": "single-site" | "multi-site" | "tour",
  "total_cost": 15000,
  "days": 1,
  "start_by": "the launch week" }
```

`total_cost` and `start_by` are optional — the sheet still returns without them, just with `cost` or
`permission.ask_by` reporting why they're not computed yet, on the same "empty is a hole, not hidden"
principle the jobs table already uses.

```json
{
  "available": true,
  "venue": "rwa", "venue_label": "Apartment society / RWA",
  "who": "The household decider, at home, with the family present.",
  "trap": "Access is personal and slow to arrange...",
  "reach": { "available": true, "days": 1.0, "reach": [80, 250], "intercepted": [16, 100],
             "dwell_min": [3, 8], "source": "[assumed] — sensible Indian retail defaults; a real site count always wins" },
  "cost": { "available": true, "total_cost": 15000.0, "cost_per_contact": [150.0, 937.5], "source": "..." },
  "permission": { "available": true, "who": "The RWA committee...", "lead_days": [7, 21],
                   "cost_tier": "free–low", "formal": true, "ask_by": "start asking 21 days before..." },
  "elements": { "scale": "single-site", "label": "Single site, one day",
                "kept": ["uniform", "education", "prop", "capture", "leave_behind", "permissions"],
                "kept_labels": [...], "dropped": [], "dropped_labels": [], "never_dropped": ["education", "capture"] },
  "scales": {"single-site": "...", "multi-site": "...", "tour": "..."}
}
```

**The ask:** a "Kit sheet" panel on the Onground activation screen, opening once an idea and its venue
are chosen — same placement logic as the POS panel's Step 3. Show:
- reach and intercepted as ranges, with the `[assumed]` source line always visible, never presented as
  a measurement
- cost-per-contact only when `total_cost.available` is true; otherwise show the `why` and a way to
  type in the day's real cost (stall/van, staff, props, leave-behind, permission fee)
- a scale picker (the three tiers) that re-fetches the sheet and re-renders `elements.kept` /
  `elements.dropped` — this is the part worth making visually clear: which elements survive is a rule,
  and seeing it change as the scale changes is the point
- the permission timeline as a simple "start asking by" line

`400` with `detail` fires only when the idea's venue isn't one of the eleven — show it as a plain
refusal, same pattern as the POSM library gate.

## 2 · The shopkeeper's margin story

```
POST /trade-margin-story
{ "mrp": 30, "trade_price": 27, "case_size": 20, "units_per_week": 40, "facings": 3,
  "unbranded_price": 26, "unbranded_margin_pct": 8, "pack_name": "Heritage 500ml pouch" }
```

Only `mrp` and `trade_price` are required. Everything else is optional and the response says what's
missing rather than silently omitting it:

```json
{
  "available": true,
  "mrp": 30.0, "trade_price": 27.0, "margin_per_unit": 3.0, "margin_pct": 10.0,
  "case_size": 20, "margin_per_case": 60.0, "facings": 3,
  "weekly_margin": 120.0, "margin_per_facing_per_week": 40.0,
  "missing": [],
  "unbranded": { "price": 26.0, "margin_pct": 8.0, "margin_per_unit": 2.08,
                 "advantage_per_unit": 0.92,
                 "comparison_note": "Assumes the same units sold per week for both — the real difference in rate of sale between the two is not known here and should be checked before this number is quoted." },
  "talk_track": "Heritage 500ml pouch: 10.0% margin, 3.0 per unit. One facing earns roughly 40.0 a week at the quoted rate of sale. That is 0.92 more per unit than the loose or unbranded alternative."
}
```

`400` with `detail` fires if `mrp`/`trade_price` are missing, or if `trade_price` is not below `mrp`
(catches a swapped-field mistake rather than returning a negative margin silently).

**The ask:** a small calculator on the Sales enabler screen, near the `trad` channel's `pitch` and
`card` elements (general trade is where this argument is actually made — modern trade, e-commerce and
quick commerce don't have a shopkeeper counter to pitch across). A form with the six inputs above, a
"calculate" action, and the result shown as:
- margin per unit / per case / **per facing per week** (that last one is the number worth making the
  most visually prominent — it's the one a shopkeeper actually weighs)
- the unbranded comparison, when both its fields were filled, with the rate-of-sale caveat shown
  plainly rather than in fine print
- `talk_track` displayed as the literal sentence, so it can be copied straight onto a pitch card

If you'd like this to pre-fill the existing `pitch` or `card` element's brief text with the
`talk_track` sentence, that's a reasonable convenience to add on your side — the backend doesn't do it
for you, since a person copying a sentence into their own words is exactly the "you are the evidence"
discipline the rest of this product runs on.

## Verify on your end

- The activation kit sheet's scale picker actually changes `elements.dropped` when you switch scales —
  confirm against a `haat` idea specifically, since it's the one with a real `truck` in its elements.
- `total_cost` omitted entirely — confirm the panel shows the `why` rather than a blank or a zero.
- `trade_price` typed higher than `mrp` — confirm the 400 renders as a clear refusal, not a console error.
- `checkfe.py`, all seven, on your actual return.

## Verified on this end before this was written

Every route tested over real HTTP against the running server, not just read from the code: the drop-out
ladder confirmed on a real haat-route idea (kept all seven elements at single-site, dropped only the
truck at multi-site, dropped truck+van+leave-behind at tour); the venue-refusal path; the margin
calculator against real pack numbers and both its refusal paths (missing trade price, and trade price
above MRP). 18/18 `test_tools.py`, `contract.py` clean, 170 routes (167 + these 3, exactly), the
pre-existing `/activation-idea` and `/activation-elements` regression-checked and unaffected, page loads
with only the four pre-existing SVG placeholder warnings.
