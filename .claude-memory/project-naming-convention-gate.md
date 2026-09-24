---
name: project-naming-convention-gate
description: "Required project-name gate at brief creation, plus the discovery that project.py already existed for house/plan and just needed extending to platform/campaign — built and locally verified"
metadata: 
  node_type: memory
  type: project
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-09-24T18:08:24.752Z
---

24 Sep: triggered by the user hitting real picker ambiguity while testing [[campaign-medium-adaptation-wiring]]
— duplicate "Heritage Foods · 8 of 8 decided" house cards, and 17 campaigns all literally named "IMC 2026"
under one platform. User's ask: a naming convention, chosen by the user, threaded from brief through to
every downstream picker. Decision after a pros/cons discussion: **required, blocking brief creation until
named** (not optional-with-a-nudge).

**Key discovery before building anything**: a `project.py` module already existed, fully designed
("asked once, at the brief, inherited from there... a derived name is marked as derived") and already
wired into `strategy.py` (house) and `plan.py` — houses and plans already had `project`/`project_source`/
a `label()` renderer. The actual gap was narrower than it looked: the idea platform (`ideas.py`) and the
campaign layer (`campaign.py`) had never been wired to it, and nothing made naming non-optional, so most
real houses in the dev tenant were simply never given one.

**Built and live-verified:**
- `ideas.new_set()` and `ideas.sets()` now inherit/report `project` the same one-time-copy way
  `plan.new_plan()`/`plan.plans()` already do.
- `campaign.save()` inherits `project` from the containing platform set, stored on each campaign
  (doesn't disambiguate two campaigns on the SAME platform from each other — that's `name`'s job, still
  not enforced unique — but disambiguates which platform's/house's campaigns a picker is looking at).
- `/brief-save` refuses a brand-new brief (no existing id) with no project name — a backend safety net
  behind the real, screen-level gate.
- Frontend: a required "Name this project" wall (not a dismissible modal — this app has none, and the
  point here is that it truly cannot be skipped) on both remaining brief-creation entry screens: the
  guided builder and the IMC research builder. Down from three screens because retiring `comms` (below)
  collapsed one entry point. Typing alone never dismisses it — only an explicit Continue click with real
  text does, so a half-typed name can't be mistaken for a confirmed one.
- Fixed a real, separate frontend bug found while building this: the house-picker dropdown (`houseOpts`,
  used on the "Start a plan" screen — the exact screen in the user's original screenshot) was rebuilding
  its own brand-only label from scratch instead of using the `label` field the backend already computed
  correctly (a sibling list on the same screen, `houseCards`, already used `h.label` correctly). Fixed to
  use `h.label`.
- Campaign pickers (built in the sibling wiring project) now prefix with the project name.
- Verified the whole chain live through the real API: a brief saved with a project name → a fresh house
  → a fresh platform set → a fresh campaign, confirming the same project string landed correctly three
  layers down (`"Heritage — house, September 2026"`), and confirmed the `/brief-save` refusal fires
  correctly with and without a project.

**Side finding, fixed as its own small piece first**: "+ New brief" on the Home screen was a silent
shortcut into a `comms` format that has no card anywhere in the Briefs picker (can only be reached by
accident) and mislabelled its own screen "IMC Brief" in the header (`fmt('comms')` falling back to
`FORMATS[0]` when `'comms'` matches nothing in the registered list — `window.claude.complete` itself was
NOT the problem here; verified live that the AI co-writer box genuinely works, real grounded generation
through the server-injected `/complete` bridge). User decided: retire `comms` outright (IMC already
covers the same ground) and repoint "+ New brief" to the Briefs page, matching the precedent
`goSocial`/`goPosmShortcut` already set for their own producers. `SECTIONS.comms`/`formatDefaults.comms`
left in place, unreferenced by any entry point now, so an already-saved `comms` brief still opens.

**Not retroactively fixed, on purpose**: existing unnamed houses/platforms/campaigns stay unnamed (no
backfill pass) until someone edits them or a new one is created under this gate.

**Deferred, not built**: campaign-name uniqueness (nothing stops two campaigns on one platform sharing a
literal `name` even with the project prefix now distinguishing platforms) — flagged, not asked for yet.
Also deferred: a home-page hero-row redesign question (3 shortcut buttons vs. a proposed 4 tab-style
buttons) — recommended keeping true zero-setup shortcuts distinct from plain tab links, since the top nav
already covers tab-style navigation; parked at the user's own request, not decided.

**Status: fully built, fully local, nothing deployed.** User will test on local tomorrow (25 Sep).
