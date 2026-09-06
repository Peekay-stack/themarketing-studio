# ASK_DESIGN_46 — framing only: the measurement loop (audit #9)

As agreed — no paragraph, no spec. What's actually true in the code, and the questions I don't have
answers to. Send back questions before either of us builds anything.

## What already exists

**Nothing ingests a delivered impression, click or sale.** Zero actuals store, zero ingest route,
confirmed by grep — `actuals` appears only inside prose explaining that nothing is there yet.

**The consuming screens already agree on the shape, because you wrote it down.** Your own line on the
empty campaign-analysis screen: *"A store for entered actuals — metric, value, geography, period,
source and date — read by this screen, by ESOV and by the social feasibility check, so all three
agree."* Three named consumers, one shape. I'm not proposing anything different from that; I'm asking
what's under it.

**The pattern already exists in miniature, twice, and it's a good one.** `esov()`'s share-of-market
field and the social plan's cost benchmark are both: a person-entered number, a required source, an
`as_of` date, refused if the source is missing. Neither reads from a real store — each is a one-off
field bolted onto its own campaign or plan object. A real actuals store is that same pattern
generalized into one place instead of re-invented per screen each time a new metric shows up.

**Every gate downstream already refuses cleanly when the number isn't there.** ESOV says why it can't
compute; the social feasibility screen names what it needs; campaign analysis names what it would
take. None of them fabricate a figure. The loop has somewhere honest to land.

## What I don't know, and won't guess

- **Manual entry, CSV import, or a live platform connection — which first?** Your own note names all
  three ("no ad platform, no analytics export, no sales ledger"). They're very different builds and
  I don't know which one earns its cost first. My instinct is manual entry with a source, because
  it's the same pattern already proven twice and needs no third-party integration — but that's a
  guess, not a finding.
- **One store per tenant, or does a metric belong to a specific plan/campaign?** `metric, value,
  geography, period, source, date` reads like a flat ledger a tenant owns, not something scoped to
  one social plan or one media plan — but ESOV needs a SOM figure tied to a specific comparison
  period, and the social feasibility check needs a benchmark tied to a specific cell. If the store is
  flat, something has to match a ledger row to the right consumer; I don't know if that's a join key
  you've already got in mind or genuinely open.
- **What happens to the two existing one-off fields (SOM, the social benchmark) once a real store
  exists?** Migrated in, left alone as their own small case, or superseded? Leaving them alone means
  three sources of truth instead of one once the loop ships, which is the exact pattern this project
  keeps tripping on.
- **Does entering an actual ever change what a gate ALLOWS, or only what it reports?** Right now
  every refusal in the studio is about missing information, never about a bad number. A measurement
  loop could stay report-only (the safer, smaller build) or start feeding back into gates — e.g. a
  channel that's underperforming losing budget-split priority. I don't know which this audit item
  means, and it's a large difference in scope.
- **Who enters an actual, and does that need the auth item (#6) first?** A ledger anyone can write to
  is a bigger problem than a ledger nobody can write to. If entries need attribution (who logged this
  number, and when), that's identity, which doesn't exist yet either.

## What I will NOT do without an answer first

Build a general ledger schema, pick manual-vs-CSV-vs-live-connection as the first cut, or decide
whether SOM/benchmark get migrated. Each is a real decision with real cost either way, and I'd rather
ask than build the wrong one and have you revert it.
