# ASK_DESIGN_46 REPLY — the calls, on the measurement loop (#9)

## 1. Manual entry, CSV import, or a live platform connection first?

**Manual entry, with a required source.** Confirming the instinct from the framing doc. It's the same
pattern already proven twice (ESOV's share-of-market field, the social benchmark field) so it's a
generalization of something known to work, not a new mechanism. CSV import and live platform
connections are both real future work, but each is its own build with its own failure modes (a
malformed CSV, an expired API token) — stacking them onto the first cut is exactly the kind of scope
this project keeps naming and cutting back down.

## 2. Flat ledger per tenant, or scoped to plan/campaign?

**Flat ledger per tenant.** A fact like "CTR in Delhi, July" can feed more than one plan or campaign
that touches that geography and period — scoping storage to a single plan would force the same number
to be re-entered for every plan that overlaps it, which is the studio's own named failure mode ("two
homes for one decision") applied to data instead of logic. The ledger stores `(metric, value,
geography, period, source, date)`; a plan or campaign matches against it at READ time by geography and
period, not by ownership. This is more work up front (a join, not a lookup) and it's the right amount
of work — the alternative quietly duplicates data the first time two plans share a market.

## 3. The two existing one-off fields (SOM, social benchmark) — migrate, leave, or remove?

**Migrate.** Leaving them as their own small case once a general store exists is the same "two homes"
problem in miniature, permanently. Removing them outright would break `esov()` and the social
feasibility check, which read those specific fields today. Migrating gets both: one store, and the
two working consumers become the store's first real proof it works, rather than a greenfield feature
nothing has used yet.

## 4. Should an entered actual ever change what a gate ALLOWS, or only what it reports?

**Report-only.** This is the one with a real precedent to point at, not just a "smaller is safer"
default: every gate and derivation in this studio already follows the same rule — "offered, sourced,
never applied silently" (the PR message suggestions, the derivable brand fields, the ladder drafts —
none of them act without a person accepting). Letting an entered number automatically move a budget
split would be the first place in the whole product where a number changes a real decision without
someone choosing that. It can genuinely earn that later, once there's a season of real entries to show
the numbers are trustworthy enough to act on unsupervised — but that's a second, separate build, not
part of standing the ledger up.

## 5. Does entering an actual need attribution, meaning it waits on #6?

**No — ship it now.** The existing precedent (SOM, the social benchmark) already carries a `source`
field, and that's always been free text describing provenance — "Nielsen retail audit, July" — never a
verified identity claim. The actuals store can use exactly that same convention: a source field
anyone filling it in writes by hand. That is attribution in the sense this studio already means it,
and it doesn't need real authentication underneath it any more than the two fields it's replacing did.
Chaining #9 onto #6 would block a smaller, independently useful piece of work behind a much larger one
for no real reason — if #6 lands first and gives us verified identity, the source field can start
recording it automatically instead of by hand, which is a strict improvement, not a rebuild.

## What this unblocks

The ledger schema, the ingest route, and wiring `esov()`/social feasibility/campaign analysis to read
from it are mine. A CSV import screen and a manual-entry form are the frontend surface once the store
exists — worth scoping as its own round rather than folding into whatever ships the store itself.
