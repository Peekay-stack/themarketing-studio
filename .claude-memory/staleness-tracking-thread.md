---
name: staleness-tracking-thread
description: "Cross-layer 'computed correctly, never displayed' staleness bugs found and fixed 29-30 Sep -- campaign expressions, execution briefs, idea platform, campaign findings panel, plus the 30 Sep idea-platform/campaign wiring saga (6 commits, all live). Nothing known open; 'Previous Campaign' picker discussed-but-unbuilt is the pickup point."
metadata:
  node_type: memory
  type: project
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-09-30T13:53:19.945Z
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

**Still open, evidence-checked, not yet requested to be built:** nothing further found as of 29 Sep.
The broader [[studio-work-inventory]] pending items are untouched by that work.

---

## 30 Sep: idea-platform / campaign wiring saga -- 6 commits, all shipped and confirmed live

Grew directly out of the owner live-testing the 29 Sep fixes: reviewing the real Idea Platform screen
surfaced that "expression by medium" (the platform's own Step 4) and "campaign idea" have a real
ambiguity for the user -- after adopting a platform, should you write per-medium expressions directly,
or build a campaign first (whose own per-medium adaptation should then win)? And a deeper bug: adopting
a genuinely NEW platform could still show a PRIOR platform's stale per-medium expressions, because
nothing cleared them. Same underlying pattern as the 29 Sep bugs above (computed/precedence correct
somewhere, not everywhere) but this time found by a full backend sweep the owner explicitly requested
("check once in the backend for any wiring with 'expression by medium' and 'campaign idea' across the
entire portal") rather than a single live report.

**Commit `5dc02e1` -- Media Channel rename** (display-only, both singular+plural for consistency, per
owner's explicit pick of "Media Channel" over alternatives discussed to avoid colliding with "Idea
Platform"/"Execution"/"campaign expression"): `COL_LABEL` map, `P_LAYERS` array, a hardcoded Media-screen
table header in `app.dc.html`; `plan.py`'s layer label; `docs.py`'s `_PLAN_COLS` dict.

**Commit `ef48b59` -- two independent builds, both pre-approved ("Build all three now" covered items 1+3
of a 3-item list; item 2, "Previous Campaign", was discussed at length but deliberately NOT built --
see below):**
- Plan-tab campaign-awareness: `plan.house_block()`'s `by_med` now checks the adopted platform's
  CAMPAIGN's own `expressions` before the platform's, with a new explanatory line distinguishing "the
  season's own adapted line" from "the platform's own text, applies only where the campaign is silent."
  Answers the owner's own follow-up question (when idea platform is skipped, since it's an optional sub
  tab) correctly: the campaign-check is gated on an adopted platform existing at all, so skipping idea
  platform falls straight through to messaging-house-only behavior unchanged.
- A1 auto-select + channel filtering (execution briefs): new `execution.channel_options(rows, kind)` --
  filters by medium via `media.migrate()`-normalized matching, fails CLOSED (no silent wrong-medium
  fallback) on zero matches, returns `(matched_rows, is_unambiguous_bool)`. Wired into `/execution-options`
  as `channels`/`channel_unambiguous`; `execution.brief_from()` got a server-side medium-match guard on
  `channel` as defence in depth; frontend auto-fills `execDraft.channel`/`videoExecDraft.channel` only
  when unambiguous AND nothing already chosen. **Self-caught bug during build**: an edit meant for
  `bagExec()`'s channel field landed in `bagVideoExec()`'s near-identical block instead, leaving
  `bagExec()` unwired and `bagVideoExec()` referencing undefined vars (would have thrown at render) --
  caught via `git diff` before shipping, both fixed correctly.

**Commit `b67e355` -- idea-platform staleness fix + branch-choice banner v1**, the core fix of this
thread, built after the owner explicitly confirmed the scoping ("yes.. scope this and also, let the
expression by medium be empty the moment a new idea is adopted... otherwise it will keep on floating in
producers, randomly"):
- `ideas.adopt()`'s two-door bug: a prior (23 Sep) fix gated the `prior`-inheritance path on
  `_same_platform`, but left the payload-driven `data.get("expressions")`/`routes` merge from the
  client completely UNGUARDED -- stale client-side state could silently overwrite a genuinely different
  new platform's expressions. Fixed: `_trust_payload = _same_platform or not prior`, gating both the
  routes-merge and the payload-expressions-merge. Verified via 3 direct-Python cases (new
  idea+stale-payload -> correctly empty; same-idea-resave -> correctly inherits; first-ever-adopt ->
  correctly keeps typed) plus a live API replay against real house `68c50487e3`.
- `ideaDraft()` frontend: success setState now also clears `expressions: {}, exprSaved: '', routes: {}`
  so a freshly-generated platform draft can't carry forward the PREVIOUS platform's in-memory state
  either (belt-and-suspenders with the backend fix, since the frontend state and the backend payload are
  two separate places the same staleness could hide).
- New branch-choice banner: answers the owner's screen-flow question directly -- after adopting, ask
  "go to expression by medium, or build a campaign first" rather than silently defaulting either way.
  `showBranchChoice: freshAdopt ? true : ...`, dismiss/branchToCampaign/branchToExpressions handlers,
  scrolls to `id="tms-campaign"` (Step 3) or Step 4 respectively.
- **Owner's own live testing later confirmed this fix holding in real production use** (Step 4 correctly
  empty on a fresh, genuinely different adopted platform) -- referenced in the `b892783` commit message.

**Commit `6f66835` -- backend sweep result, `campaign.jobs()` precedence fix + new campaign docx
export**, built after the owner's explicit "check once in the backend... report to me" (a report-only
pass, no building) was followed by "fix everything you found":
- `campaign.jobs()`: docstring already claimed campaign-then-platform-then-house authority (matching
  `producers.stands_on()`), but the code only ever read `_item(p)`'s (the platform's) `expressions` --
  the campaign object `c` was used for typed roles only, never `c.get("expressions")`. So the one table
  meant to show "role + message side by side" could show a medium's OLD platform-level line even after
  the campaign had written its own different, currently-winning adaptation -- same "campaign should win,
  doesn't" bug as `plan.house_block()`, found here by systematic sweep rather than a live report. Fixed:
  two-pass resolution (campaign's own `expressions` checked first per medium via `slots.get(leaf,[])`,
  falls to platform's only if the campaign has nothing), `source` field says "this campaign" vs "the
  platform" accordingly. Verified via negative control (real campaign, no expressions -> falls to
  platform) and positive control (in-memory injected campaign expression -> correctly wins), both via
  direct Python call AND the live `/jobs?house=...` route.
- New `docs.build_campaign_docx()` (mirrors `build_platform_docx()`: insight/resolution/shape/frame/
  slots, "Roles by medium", "This campaign's own expression by medium" with an honest "nothing expressed
  yet" fallback, findings, caveat), new `/campaign-docx/{set_id}?campaign=<id>` route, two new download
  buttons on Step 3. **Bug self-caught before shipping**: `campaign_mod.SHAPES.get(shape)` returns a
  plain string not a `(label, desc)` tuple -- an initial `[0]`-index would have sliced the first
  character; fixed via direct grep/Read confirmation of `SHAPES`'s actual shape before shipping.

**Commit `b892783` -- live-testing feedback, banner reorder + restyle** (most recent, "2 tests frame
should come before the 'build a campaign'/'expression by medium' button... make the panel and buttons
in the bifurcation panel little more bolder and cleaner + visible"): moved the branch-choice banner from
between Step 1 and Step 2 to right after Step 2 ("Two tests") and before Step 3 -- the tests judge
whether the platform itself holds; the branch choice is about what to do with it once it does, so it
read oddly argued before the thing being branched on had been checked. Restyled: heavier blue left
border, "NEXT" eyebrow + real heading, both paths as actual buttons (solid primary "Build a campaign",
outlined secondary "Write expressions directly") instead of plain underlined text links.

**All 6 commits confirmed live via the standard gate** (`tools/checkfe.py` clean, 0 CRLF, `py_compile` +
`selfcheck.py` clean, `smoke.py` before push, `/selfcheck` commit match after each Render deploy, log
scan for new 5xx -- none found beyond the familiar single-instance-cutover 502 blip). Deploy IDs tied to
each commit were separately confirmed via `get_deploy` per the owner's standing template.

**Two distinct "expressions" objects, a recurring source of confusion this thread**: `ideas.py`'s
platform-level `expressions` (Step 4, "the platform's own baseline") vs `campaign.py`'s campaign-level
`expressions` (the campaign's seasonal adaptation) -- both keyed by the same `media.EXPRESSIONS` dict,
living on different objects, with campaign always meant to win where present. Every fix in this thread
was a version of "campaign should win over platform, some caller forgot."

**Explicitly discussed, NOT built -- the "Previous Campaign" browsing/picker feature**: the owner wants
a way to browse/select an older campaign (keyed by campaign+brief name) from the Idea Platform tab,
because a campaign can run long enough that producers may still need to generate against an OLDER
campaign while a newer platform/idea has since been adopted. Data-model gaps identified during
discussion: campaigns carry no `brief_id`/`brief_title` stamp for labeling; `ideas.as_read()` always
resolves the currently-`chosen_platform()`, never a specific non-adopted historical item; the EXISTING
"Which campaign" execution-brief dropdown (`execution.brief_from()`'s `sel.campaign_id`) already does
most of the needed selection, just scoped to the currently-adopted platform's own campaigns via
`/campaign`'s `_item(p)` resolution -- widening that scope to include historical platforms' campaigns
was the leading shape discussed, over building a whole new picker UI. The owner also raised whether Idea
Platform's 4-layer structure needs a genuinely different (5th?) treatment for "browsing an old campaign"
vs the first 3 generation layers -- unresolved. **This is the agreed pickup point for the next session**;
nothing here is scheduled, the owner said "let's take it up tomorrow" with no further build requested.
