---
name: staleness-tracking-thread
description: "Cross-layer 'computed correctly, never displayed' staleness bugs found and fixed 29 Sep -- campaign expressions, execution briefs, idea platform, campaign findings panel. BUILT + DEPLOYED, owner testing live 30 Sep."
metadata:
  node_type: memory
  type: project
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-09-29T15:27:11.482Z
---

**29 Sep: two commits shipped and confirmed live** (`/selfcheck` on themarketing-studio.com returned
`commit:"7652273093", ok:true` at time of writing). The owner has NOT yet live-tested either -- said
"will test it live tomorrow" (2026-09-30). **Pick up here first if the owner reports anything odd on the
Campaign, Execution, or Idea Platform screens tomorrow.**

**Why:** this grew out of the [[prompt-priority-framework-gate-territory-task-evidence]] upstream-wiring
work -- while live-testing that framework, the owner spotted a stale campaign-expression preview on the
Social producer screen. Diagnosing it surfaced a recurring architecture pattern independently reinvented
in five places across the codebase: an item stores a signature/hash of its upstream inputs at generation
time (`generated_under`/`expr_generated_under`), a `stale()` function compares that stamp against the
upstream's CURRENT signature, and only machine-generated content is trackable this way (a hand-edit
clears the stamp -- "you are the evidence"). `strategy.stale()` (house layers) and `plan.stale()` (plan
layers) were already correctly wired. The other three were not, in three DIFFERENT ways:

**Commit 1 (`5e3cbc8`, backend + frontend):**
- `campaign.stale()` (new) + `ideas.platform_signature()` (new) -- a campaign's per-medium expressions
  now know when the idea platform they were adapted from has moved on. `express()`/`express_many()` take
  a `source` flag so only a model-written adaptation gets stamped.
- Frontend: `refreshProducerStandsOn()` -- POSM/on-ground preview fetch-once guards were silently
  no-op'ing a refresh after adopting an idea or re-expressing a campaign; now reset explicitly.
- Frontend: `execution.status()` had ALWAYS correctly computed `stale_because`/`proof_obligation`
  server-side and every route already returned them -- but under a separate `status` object, never
  merged onto the `execution` object the frontend actually kept in state. All 6 write-sites
  (`createExecution`/`setExecStatus`/`recompose` + video mirrors) fixed via a new `execWithStatus()`
  helper. This was the one PRE-DIAGNOSED wrong before evidence-checking: initially assumed "zero backend
  callers of `stale_because`" from a literal grep of `main.py`, which missed that `execution.status()`
  calls it one level down -- backend was fine, bug was 100% frontend.

**Commit 2 (`7652273`, frontend-only, no backend change needed):**
- `ideas.status()` had always returned `stale` (vs the house's current signature) plus its own finding
  text on every `/idea-platform` GET -- `loadIdea()` never read `d.status` at all. Fixed: now stores
  `stale` + the server's own finding `detail` (not a duplicated local string), new amber banner.
- Campaign findings panel (`cpgFindings`/`hasCpgFindings`): TWO compounding bugs. `loadCampaign()`
  fetched `campaign.status()`'s findings off `GET /campaign` and discarded them every time; separately,
  the render code read `houseStatus.findings` (which `strategy.status()` can NEVER populate with
  campaign-layer findings) and the wrong field name (`f.text` instead of the real `f.detail`). Fixed:
  new `campaignFindings` state, pointed the panel at it with the right field name.

**Verification:** both commits used real tenant data with temporary, fully-reverted test edits (a
plan-row text drift for execution staleness; a house core-message drift + a synthetic
`generated_under` stamp for idea-platform staleness, since none of the dev tenant's platform sets had
ever actually been stamped by a real `/idea-draft` call). Driving the live React instance directly hit a
real gotcha, now recorded in [[change-discipline-working-agreement]]'s dated lessons: `sc.state !==
sc.logic.state` in this app's DC runtime -- writes/reads must go through `sc.logic`, not `sc` itself, or
you silently test against the wrong state object.

**Still open, evidence-checked, not yet requested to be built:** nothing further found in this thread.
The broader [[studio-work-inventory]] pending items are untouched by this work.
