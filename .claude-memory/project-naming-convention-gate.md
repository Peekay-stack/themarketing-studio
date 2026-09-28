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

**Status: see UPDATE 25 Sep below (shipped).** User will test on local tomorrow (25 Sep).

## UPDATE 25 Sep — SHIPPED live as 2315e0a, then live-testing found the gap is wide (PICK UP HERE, morning 26 Sep)
Everything above is committed, pushed and live (`/selfcheck` matched `2315e0a`). Same-day additions, also shipped in 2315e0a: house-from-brief inherits the name, duplicate-house detection ("open it instead"), campaign panel vs platform panel mutually exclusive, "Take it to X" hand-offs. Deleted the empty unnamed house `cdfecdbe41`.

**Local, UNCOMMITTED edits in app.dc.html (checkfe passes, not browser-verified, not pushed):** Idea Platform house dropdown (`ideaHouseOpts`) now uses `h.label`; project-name chip beside the "The idea platform" title (`ideaProjectName`/`ideaHasProject`); "Which campaign" field hidden when the house has zero campaigns (both `xFields` and `vxFields`).

**Audit the user asked for (nothing built past the above; user said HOLD, resume in the morning).** Counts are from the local tenant + code grep, not a click-through:
- Data: briefs 1/23 named, houses 6/10 (only 2 real; 4 placeholders like "Heritage — house, September 2026"), plans 9/13 (all placeholders), platforms 2/7 (placeholders), campaigns 0, executions 0/9, PR 0/10, trade 0/1.
- Correct (13): brief builders gate, brief-save refusal, brief library/picker, house/plan/platform/campaign inheritance at creation, house cards, plan cards, Start-a-plan house dropdown, two campaign pickers, dupe banner, house-screen name + cascade; house/platform/plan docx filenames.
- Missing (~12): Idea Platform dropdown + header (fixed locally), plan screen header `pBrand`, plan strip/state line, media-plan header `medPlanName`, PR sheet list/header (no name field), executions (no field, producer "Briefing from the plan" shows none), trade records, all non-house/platform/plan download filenames (incl. app.dc.html ~18455), printable house sheet (~18523/18560), made ledger (accepts project, caller unconfirmed), campaign list header on platform screen (unconfirmed).
- Root gap: placeholders were saved as if real names (label doubles brand: "Heritage Foods · Heritage Foods – house…"); names copy down only at creation; old records only fixed via the house's "Name this project" cascade.
- **Proposed order awaiting approval:** (1) push the two Idea Platform fixes + add name to plan header/media header/printable house sheet; (2) executions + PR sheets get a name copied from their plan; (3) name in all download filenames; (4) show placeholders as "unnamed — name it" instead of doubling the brand.

**Also open — carousel cast options (diagnosed, no fix):** `draftCarouselCast` sends the whole script prose (props included) as `characters` to `/cast-reference` (main.py ~1512), no India/market anchoring, variation rule too loose → oversized glasses, three different compositions, foreign-looking cast. Proposed: extract only people, anchor to brand's market, force same composition; prove on the real Nothing Cut script first (large change → approval first).

## UPDATE 28 Sep — Step 1-3 of the naming order SHIPPED live as 0d3f08e
Built, local-verified (checkfe, py_compile, selfcheck.py, smoke.py) and live-verified in the browser
(logged in locally as seed user `puneet`/`puneet-dev`), then pushed and confirmed live
(`/selfcheck` + `/selfcheck/deep` both clean against `0d3f08e6d7`).

**Step 1 (the 3 local fixes from 25 Sep, plus more header coverage):**
- Idea Platform house dropdown now uses `h.label` (was rebuilding its own brand-only label).
- Project chip added: Idea Platform title, plan-screen header, execution-screen header, printable
  house sheet (title + on-page header), media-plan header ("Derived from X · project").
- "Which campaign" hidden on Social/Video brief forms when the bound house has zero campaigns.

**Real bug found WHILE testing the above, fixed in the same push:** `/campaign?house=X` falls back to
`ideas.resolve(..., allow_latest=True)` — the newest platform set for the BRAND, across any house —
when the requested house has none of its own. That fallback is intentional and DISCLOSED elsewhere
(`resolvedPlatform()` labels it "the newest house for this brand"), but the execution's campaign
picker didn't disclose it at all: a campaign-less house could still show and let you pick a campaign
that actually belonged to a different house, with no indication. Fixed narrowly in
`loadCampaignsForExec` (frontend only, doesn't touch the shared `ideas.resolve()` used legitimately
elsewhere) — discards the response unless its own `house` matches the plan's house.

**Step 2:** executions and PR sheets now carry `project` (execution.py's `new_execution`, pr.py's
`new_sheet` + `/pr-sheet` route in main.py), copied from their plan, falling back to the house —
same pattern `plan.py`/`ideas.py` already used. PR sheet list rows and the sheet header show it.
Verified live: created a real PR sheet against a named-project plan, both list row and header showed
the project.

**Step 3:** project added to filenames that were brand-only: guided-builder brief docx
(`downloadBriefWord`), IMC brief docx (`generateImcDocx`), research synthesis deck
(`generateSynthesisDeck`), production bible (`downloadProductionBible`), film script
(`downloadScriptWord`). Verified by logic only (isolated JS string-building, no live AI generation —
avoided the API cost), same pattern already proven elsewhere in the file (`downloadBriefWord`'s own
existing `safe` variable). **Also checked and found already correct, no action needed:** the made-work
ledger (`_record_made`/`_made_brand_project` in main.py already resolves and stores `project`).

**Still open (not done):**
- Step 4 — placeholder-name cleanup ("unnamed — name it" instead of doubling the brand like
  "Heritage Foods · Heritage Foods – house, September 2026").
- Call-sheet filename (Shoot Board / `callSheet()`) — deliberately left alone. Couldn't confirm
  `state.house`/`state.plan` reliably matches the actual shoot's own house without risking exactly the
  cross-house mistake just fixed above; needs its own trace before touching.

**Test hygiene:** created and then deleted 2 throwaway plans + 1 PR sheet in the dev tenant purely to
exercise the campaign-picker and PR-sheet code paths (positive and negative cases) — none left behind.

Commit: `0d3f08e` ("Naming convention: idea platform, plan/execution/PR headers, cross-house fix").

## UPDATE 28 Sep, later same session — Step 4 SHIPPED as d914506
`project.looks_derived(name)` — narrow regex, true only for the exact unedited `derive()` suggestion
("Heritage — house, September 2026"), never a real typed name even one starting with the brand
("Heritage Maharashtra Push" stays untouched — verified live, both cases). Needed because accepting a
`/project-suggest` suggestion verbatim legitimately marks a document `project_source: "named"`, so that
field alone can't distinguish a real name from an unedited placeholder — only the string's shape can.

`label()` now renders a placeholder as "Brand · Unnamed — name it" instead of doubling the brand.
Single source for `strategy.houses()`/`plan.plans()`/`ideas.sets()`'s `label` field, so the plan-cards
list and both house dropdowns (fixed in the earlier 0d3f08e push) get this for free.

Frontend mirror `looksDerivedProject()`/`projectChip()` (JS can't import project.py) applied at every
place still building its own label text client-side: the 3 single-project header chips (idea platform,
plan, execution), media-plan header, printable house sheet, campaign picker options, PR sheet list row
+ header, PR's "plan it sits under" picker.

Also fixed the one place with a real ACCEPT affordance: the house screen's own breadcrumb
(`hHasProject`/`hNoProject`/`hHasProjectSuggest`) previously treated an accepted placeholder as "named"
and hid the "Name this project" prompt permanently. Now treats a derived placeholder the same as no
project at all, so the nudge (and the Accept-a-suggestion flow) stays reachable.

Deliberately left filenames alone — a derived placeholder is still specific enough to avoid the
download-collision problem `project.filename()` exists to solve; "Unnamed" for every file would
reintroduce it.

Verified: checkfe, py_compile, selfcheck.py, smoke.py all clean; live in the local browser (placeholder
houses/plans → "Unnamed — name it"; "Heritage Maharashtra Push" untouched; house breadcrumb nudges
again). Pushed, deploy confirmed live via `/selfcheck` matching `d914506`.

**Naming order (all 4 steps) is now fully shipped.** Nothing known open on this thread.

## UPDATE 28 Sep, same session — two real bugs found in step-4 live testing, both fixed as cad1abc
Live-tested d914506 and found two real problems the user caught:

1. **"Unnamed — name it" read as a dead button almost everywhere.** `label()`'s new phrasing was correct
   in meaning but wrong in every context except the ONE place with an actual click handler (the house
   screen's own breadcrumb). Plan cards, dropdowns, header chips, PR rows all showed the SAME "— name
   it" wording with nothing behind it. Fixed: dropped the suffix from `project.label()` and its JS
   mirror `projectChip()` — both just say "Unnamed" now. The house screen's own prompt keeps its
   separate, genuinely-clickable "Name this project" wording, untouched.
2. **The house screen's Accept flow was a dead loop for exactly the case d914506 introduced.**
   `/project-suggest`'s worst-case answer IS the boilerplate `derive()` string; accepting it verbatim
   re-saved that same string, which the new `looks_derived()` check immediately re-flagged as still
   unnamed — "Name this project" just reappeared, no visible feedback, forever. Fixed: the suggestion
   is now an editable text input (defaults to the guess, but typing over it is how you actually name the
   thing); "Accept" relabelled "Save". Verified end to end on a real house (renamed, confirmed, then
   reverted its project field back to empty — it had none before the test).

Both verified locally (checkfe, py_compile, selfcheck.py, smoke.py) and live in the browser, pushed as
`cad1abc`, confirmed live (`/selfcheck` + `/selfcheck/deep` both clean, commit `cad1abce6d`).

## OPEN — a third issue from the same testing round, NOT fixed, needs the user's test result first
User reported: the Idea Platform's "campaign expression by medium" panel used to correctly hand off to
producers via "Take it to X", but an already-briefed Social execution is now reading the platform's
plain "Expression by medium" instead of the campaign's adapted line, even though a real campaign exists
with its own written Social expression.

Traced two candidate causes, not yet distinguished:
1. **Likely benign — staleness, not a bug.** `ideaGoTo`'s hot hand-off (`loadSocialStandsOn`/
   `loadVideoStandsOn`) only ever updates the READ-ONLY preview box (`socialStandsOn`); it never writes
   into `execDraft.campaign_id`, the field `createExecution()` actually reads when "Brief it" persists
   the execution. Separately, `execution.brief_from()`'s own default (empty `campaign_id`) already
   falls back to `campaign_mod.get(pset, "")` → the platform's most-recently-written campaign — so a
   FRESH execution briefed while a campaign exists should bind correctly regardless of hot/cold path.
   `brief_from()` runs once, at creation, and is never recomputed later (`stale_because()` only catches
   a bound campaign being DROPPED or REWRITTEN, not "no campaign existed yet when this was briefed, one
   exists now"). If the execution in question predates the campaign, this is expected behavior, not a
   bug — the fix is just re-briefing it.
2. **A real, separate latent bug, if the platform ever has >1 campaign.** The empty-`campaign_id`
   fallback binds the LAST-WRITTEN campaign, not necessarily the one whose panel button was clicked —
   so on a platform with multiple campaigns, "Take it to Social" from an older campaign's row could
   silently bind whichever is now newest once actually briefed. Worth a defensive fix (thread the
   clicked `campaignId` into `execDraft.campaign_id` in `ideaGoTo`) regardless of what the test below
   shows, but not done yet — asked the user to test first rather than guess.

**Asked the user to test:** click "Take it to Social" again and brief a FRESH execution (not the
existing one) on the same plan, right after — does the new one show the campaign's adapted line? Answer
tells us whether this is (1) staleness (no fix needed) or (2) a real resolution bug (needs the fix in
2 above, and possibly more). **PICK UP HERE with whatever the user reports.**

## UPDATE 28 Sep, later same session — the campaign-wiring bug (issue 1) diagnosed, confirmed, fixed as 990d7f3
User re-tested per the ask (fresh execution, right after clicking "Take it to Social" from the campaign
panel) and it STILL showed the platform's plain line — ruling out staleness, confirming a real bug, and
they explicitly approved the fix ("take it to social ... should be the first one to go").

**Root cause, exactly as suspected:** `loadSocialStandsOn` only forwarded the campaign panel's explicit
`campaignId`/`houseId` to `/producer-stands-on` when `!e.id` (no execution yet briefed for that tab) —
i.e. only ever worked the FIRST time. `campaignId`/`houseId` only ever arrive from a deliberate "Take it
to Social" click, so the guard was silently discarding an explicit click in favour of whatever old,
unrelated execution already sat in that tab's own in-memory state (`state.execs.social`, which persists
across navigation within a session, populated only by `createExecution`/revise, never auto-refetched).
`loadVideoStandsOn` never had this guard — only Social needed the fix.

**Fix:** send `campaignId`/`houseId` unconditionally whenever explicitly given. Confirmed safe by reading
`_exec_ctx`'s own conditional (main.py): `if not (brief or {}).get("campaign") and payload.get("campaign")
and house:` — the cold-campaign fold-in only fires when the resolved brief DOESN'T already have a real
bound campaign, so an execution with its own genuine campaign binding is still never overridden; this
only fills the gap when there isn't one, exactly matching "an explicit click should win over nothing."

**Verified two ways:** (1) confirmed the mechanism directly against `/producer-stands-on` using a
duplicated-then-deleted real execution with no campaign bound — the exact call the fix now makes went
from `has_campaign:false` (platform's plain text) to `has_campaign:true, source:"the campaign, adapted
for social"` (the real campaign text). (2) checkfe/selfcheck.py/smoke.py all clean. Pushed as `990d7f3`.

**All 3 issues from this round of live testing are now fixed and pushed** (naming misleading-affordance,
Accept-loop, campaign hot-hand-off). Confirm live deploy status before closing this out.

## UPDATE 28 Sep, still same session — POSM + Onground campaign wiring built (8f7ab2b), PR scoped separately
User confirmed Social's fix worked and asked for the same for Activation/POSM/PR ("Video is working
fine" — confirmed correct, `loadVideoStandsOn` never had the `!e.id` guard to begin with).

Swept all three before touching anything:
- **POSM and Onground**: same root cause class as Social, but a different starting point — their
  "Take it to X" links only ever navigated (per the pre-existing "cold Take it to X only navigates"
  limitation), never threading `campaignId`/`houseId` anywhere at all. Built the wiring fresh, mirroring
  Social's now-fixed pattern: `ideaGoTo` captures `campaignId`/`houseId` for both; POSM stashes them on
  `state.posm` and `developKv()` ("Develop key visual") now sends `body.campaign`/`body.house`; Onground's
  `loadOgStandsOn()` now takes and forwards them (bypassing its own `_ogStandsAsked` once-guard for an
  explicit click, same reasoning as Social's fix), stashing onto `state.og` so the later `developIdea()`
  ("sharpen") call keeps reading the same campaign. Both reuse the already-proven-safe `_exec_ctx`
  cold-campaign fold-in server-side — no backend changes needed.
- **PR is NOT a wiring-lost bug — it was never built.** `pr.py` never imports `campaign` at all; no PR
  route reads campaign data. The Idea Platform's campaign panel DOES show a "Take it to PR" link with the
  campaign's own written PR expression, but it only navigates, same as POSM/Onground did — except there is
  no existing spine-walk to extend here (PR sheets bind to a PLAN, not an execution; `_pr_context` doesn't
  touch `_exec_ctx` at all). Real design question before building: should the campaign's PR expression
  surface through `release_suggestions`'s `source_material` (the same "quoted fact, never written for
  you" pattern PR already uses for the brand profile/sheet messages) or somewhere else? **Reported to the
  user, asked before scoping/building — awaiting their answer.**

Verified live (local browser + real API calls, no test data left behind): Onground's preview showed
"FROM THE CAMPAIGN, ADAPTED FOR ACTIVATION" with the real campaign text; POSM's real `/posm-keyvisual`
response came back `"source":"the campaign, adapted for posm"` with the campaign's own line. checkfe,
selfcheck.py, smoke.py all clean. Pushed as `8f7ab2b`, confirmed live (`/selfcheck` + `/selfcheck/deep`,
commit `8f7ab2b4c4`, 0 problems).

**Campaign→producer hand-off is now consistent across Social/Video/POSM/Onground. PR is the one
remaining gap, scoped but not built — pick up there next.**
