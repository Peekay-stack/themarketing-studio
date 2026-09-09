---
name: studio-work-inventory
description: "The single tracked inventory for The Marketing Studio — the Tab-by-Tab audit's order of work plus both user-testing rounds, with verified status as of 28 Aug 2026"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5e956381-ce19-4f83-93e1-71a73ced8b2b
  modified: 2026-09-07T05:33:37.025Z
---

**The one list.** Supersedes the separate user-testing note. Status verified against the code on
28 Aug 2026 (merged file `7dadac19`, Design round 47 — the sign-in screen, adopted whole), not
recalled. Re-verify before claiming anything here is done — this project's whole history is things
that looked done in a diff and were not.

Source A: *The Studio, Tab by Tab* — https://claude.ai/code/artifact/c26e0b2c-9d04-4162-8c4b-18bb606c306b
Source B: user testing round 1 (10 items). Source C: user testing round 2 (5 items), 27 Aug.

**NEXT UP (as of 6 Sep, later same day):** the user said to build Onground's per-idea Adjust (done, see
item 7 below, verified live with a real generation + real adjust round-trip) and to start on the
deferred list. Done from that list: Video's six-entry-point grounding audit (all six now call
`loadGrounding`/`loadVideoStandsOn`, matching Social's own earlier audit), and threading
`force_typed`/`skip_mandatories` into `reworkPosts`/`adjustPost` (previously neither was sent at all).
Before returning to plan-binding, the user redirected to a more fundamental question: "even before we can
think of channels... we need to get the video based on SMP, Messaging house and Idea platform big idea
with insights pooled in from the platform... tell me what it is today, what this will change/alter."
Traced precisely rather than guessed: the idea platform is saved with seven fields (`ideas._FIELDS`:
name/idea/mechanic/territory/proof/why/rtb), but `prompts.spine_block()` — the ONE shared function every
producer going through `system_for()`/`/complete` uses (Social today, Video too since its free-text field
shipped) — only ever surfaced two of them (`idea`, `mechanic`), silently dropping `why` (the insight the
bet is built on), `territory` (the creative world it lives in), `proof` (what demonstrates it), and `rtb`
(which house reason-to-believe it dramatises). Not video-specific — every producer using spine_block had
this same gap. **Fixed, at the user's go-ahead ("yes... this is basic wiring we need to do"):**
`spine_block()` now surfaces all four. `rtb` handled defensively rather than assumed: `ideas.py`'s own
comments already flag `rtb`/`rtb_id` as an inconsistent field across this codebase (sometimes an id,
sometimes free text), and checking the REAL "The Head Start" platform confirmed it — `rtb` holds free
text there, not an id. The fix resolves against the house's sourced RTBs when it matches a real id,
otherwise uses the field's own text directly, so the honest (free-text) case isn't silently dropped.
Verified at zero API cost via direct Python against the real tenant data — the new RTB line renders
correctly; why/territory/proof didn't print only because they're genuinely blank on this specific
platform, not because the wiring is broken. Server restarted clean afterward, no errors in logs.

**Still not started: Video's "Briefed from the plan" chips** — the biggest deferred item, genuinely a
new feature (video has no execution-binding concept today, unlike Social/POSM/Onground's `xTab` system)
rather than a copy/wiring fix. Scope this with the user before building — in particular whether it needs
the full audience/channel/occasion/measure/message picker the three producers get, or a lighter version,
since video's "role"/proof-measure alignment may not map the same way. This is the next thing to raise
with the user, since they deliberately paused it to get the insight-pooling fix done first — that's now
done, so it's fair to ask if they want to return to plan-binding or have something else in mind.

**UPDATE (6 Sep, later same day): built end-to-end, at the user's instruction ("you fix it end to end and
then i will do user testing").** The premise from the note above turned out to be wrong in the important
way — checked before building rather than assumed: `execution.py`'s own `MANIFEST` already declares
`kind:'video'` a full first-class producer, identical `needs` shape to social/posm/activation
(`audience/pillar/channel/occasion/measure/message`). The backend never needed a single change — every
route (`/execution-new`, `/execution-options/{plan}/{kind}`, `/execution-status`, `/execution-rebrief`,
`/execution-recompose`) already checks `kind in execution.MANIFEST`, not a hardcoded list, and
`prompts._execution_block()` resolves any execution id generically. This was a pure frontend gap: Video
just never built the UI. Built:
- `bagVideoExec(s)` (new method, not folded into the shared `bagExec` — that one's `tab = this.xTab()`
  would resolve to whichever xTab producer was last active, not 'video', since video was never added to
  `X_TABS`/`xLive()` and restructuring it in would be a much bigger, riskier change than this feature
  needed). Mirrors `bagExec`'s field-construction logic exactly (audience/pillar/channel/occasion/measure/
  message select options, proof-obligation gap warnings, stale-plan detection), all keys prefixed `vx` to
  stay clear of both the shared `x`-prefixed keys and video's own pre-existing `v`-prefixed ones.
- New handlers, own draft/open state (`videoExecDraft`/`videoBriefOpen`, NOT shared with the xTab
  producers' `execDraft`/`briefOpen`, since video is a separate screen not a tab switch): `videoExec()`,
  `videoExecPillar()`, `onVideoExecField`, `toggleVideoBrief`, `loadVideoExecOptions`,
  `videoExecOptionList()`, `videoExecMessageText()`, `createVideoExecution`, `setVideoExecStatus`,
  `rebriefVideo`, `recomposeVideo`. `componentDidUpdate()` now also fires `loadVideoExecOptions()` on
  entering the video screen, mirroring the xTab producers' own `loadExecOptions()` trigger.
- Markup: the same "Briefed from the plan" panel (chips/status pills/field-selector form) plus the
  stale-plan-moved banner, duplicated into Video's screen between "What this film is given" and "Inputs
  to guide generation" — same visual position the three producers use.
- `generateVideo()` now passes `execution: vexec.id` to `/complete` when bound, so `_execution_block()`
  actually binds the film to one audience/channel/occasion/measure/message rather than none — the
  Prompt guide's own "cannot override: the plan's audience, channel..." notice is true now, not aspirational.
  `noTrio` (the mandatories-skip check) now checks a real bound execution instead of just `s.plan` existing.
- **Deliberately NOT built**: the 409-conflict-resolution UI the xTab producers have (`setConflict`/
  `xConflict`/`dismissConflict`) — a real but separate edge case (two people editing the same execution at
  once), scoped out rather than silently promised.
- `checkfe.py` clean (975/975 sc-if, 378/378 sc-for, 3051/3051 div, 865 class members). No backend files
  touched at all for this piece — confirmed via `execution.py`/`main.py` read, not assumed.
- **Verified live, partially**: the no-plan state renders correctly ("Nothing is briefed yet... Choose a
  plan"), no console errors. Could NOT verify the full field-selector → Brief it → chips → status-pill
  flow live — this tenant's "Heritage Foods" test brand has no IMC plan at all yet ("No plans yet" on the
  Plan screen itself, consistent with everything seen all session), and creating one from scratch is a
  separate, larger flow out of scope for this fix. Confidence is high on structural grounds (the bag
  logic and markup are near-verbatim copies of the exact code already proven working live for Social/
  POSM/Onground all session, and the backend is 100% shared/unmodified) but this specific piece needs the
  user's own live test with a real plan to close the loop — which is exactly what they asked to do next.

## A. The audit's recommended order of work

| # | Item | Size | Status |
|---|---|---|---|
| 1 | Fabricated Home metrics (F1) | S | **Done** |
| 2 | Scope assets to tenant + authenticate mounts (F10) | S | **Half** — scoping done (`tenancy.asset_path`, routes not mounts); **no auth at all** (0 login route, 0 `require_auth`). The auth half belongs to #6. |
| 3 | Ship the two Media sub-tabs (F4) | M | **Done** (r31) |
| 4 | Brand setup as the entry point | M | **Done** — Design r42 (`maybeLandOnSetup`, `clientNotReady`, unproven-claims panel); I added `palette`/`fonts`/`dos` to the profile |
| 5 | Walk one real PR sheet + competitive picture (F5) | S | **Done** — the user's two testing rounds are this |
| 6 | Auth, desks and authority | **L** | **Not started** |
| 7 | Channel weights + split enforced (F3) | M | **Done** |
| 8 | Prompt guides; Big Idea threaded | S | **Done** |
| 9 | Activation APIs, then the actuals store (F2) | **L** | **Not started** — 0 actuals store, 0 ingest route |
| 10 | Retail-media leaf; distributor ROI; contribution gate (F9) | S | **Done** |

## B. User testing round 1 — all ten closed

medium-in-house · medium expression into role-by-medium (Design r40) · POS refusal + editable line ·
activation KV-or-independent **and** the visuals producer · video cast-lock · social Excel/PPT import ·
state→city→pincode + optimisation events · PR objectives · release derivation · media map from
geographies.

## C. User testing round 2 — all five closed in round 44

| # | Item | Status |
|---|---|---|
| 1 | Brief shows raw JSON after approval | **Done** — new first tab "The brief" renders `imcWordRows(d)`, the same rows `generateImcDocx` writes, so screen and .docx cannot disagree. Blank values say the Word brief will carry the gap. Verified structurally only — no brief on the default tenant to open |
| 2 | Messaging house / RTB / ladder reconciliation | **Done** — `housesheet` screen, reached from the house header, in the user's own order: core → functional + RTBs → bridges → emotional + RTBs → recorded paths → hero demo. Layers were NOT merged. Verified live: edit-in-place works, the empty box is refused, and editing the core correctly cascaded "stale" to six dependent layers |
| 3 | Expression by medium before the campaign idea | **Done** — campaign is STEP 3, expression by medium STEP 4, and the blurb states the move |
| 4 | PR sub-tabs not generating | **Done** — `/pr-message-suggest`, now rendered as claim ↳ proof with each half's layer |
| 5 | Social campaigns needs a flow | **Done** — frame → benchmark → cells → verdict, four cards each stating state/needs/unlocks. No progress bar, no completion percentage. Verified live on a real plan |

## Round 45 — Design's clean adopt of my three fixes + the ladder builder, plus a full literal sweep

Base matched my shipped `4397dfeb` exactly. Design verified my `option_id`/`bfBrand`/`colours` fixes
and the ladder builder's attribute-hole + multi-root `sc-for` fix live before touching anything, then
took all four brand literals I flagged in ASK_DESIGN_44_REPLY plus found two more of their own in the
same code path: `writeFullScript`/`refineScript` both hardcoded `"Heritage — Pure Doodh Ki Shakti"`
into the model prompt regardless of tenant. `packSuper` is now `brandName() + (brandIdea() ? ' — ' +
brandIdea() : '')`, empty when neither is on file — one accessor, reused rather than duplicated. Housesheet
gained one sentence: editing the core there marks dependent layers stale, same as the layer screen.
checkfe 814/814 `sc-if`, 331/331 `sc-for` — unchanged, exactly as claimed (literal swaps only, no new
control flow). census: no new orphan key. All claims verified live and in source; nothing to fix.

## Round 44 — three defects I found and fixed, all mine to carry forward

1. **`/house-option` ignored `option_id`.** The sheet sent `option_id`; the route read `option`. An
   unrecognised key does not fail — it fell through to the ADD branch, so every sheet edit created a
   duplicate line while the screen showed the new text as though it had worked. Reproduced (4 options
   → 5), fixed to accept both names, re-verified through the full UI.
2. **`message_suggestions()` was greedy, not round-robin.** A house with 3+ chosen functional lines
   spent the whole `MESSAGE_MAX` cap inside one pillar — three near-identical claims on one proof, no
   emotional or core offered. Now one per pillar first, depth after.
3. **Two shape mismatches in Design's new code** — `bfBrand: d.brand || …` rendered the whole brand
   RECORD (an object is truthy), so the landing headline read "…about [object Object]"; and
   `Array.isArray(b.colours)` never matched because `colours` is a DICT on the server, so the only
   brand with colours on file showed as having no palette. Both fixed in the frontend; both must go
   in the ask or the next round reverts them. See [[design-contracts-need-shapes-not-names]].

## What is actually left

1. **Audit #6, auth and tenancy** — framing (`ASK_DESIGN_45.md`) → answered (`ASK_DESIGN_45_REPLY.md`)
   → Design accepted all five calls, gave a login contract, I built and tested it (`ASK_DESIGN_47.md`).
   **Live and tested:** `POST /login {username,password}` → `200 {user:{id,name,role,tenant}}` + an
   httpOnly `studio_session` cookie, `401` on bad credentials (same message for unknown-user and
   wrong-password, no enumeration); `POST /logout` deletes the session row server-side — verified a
   captured cookie is refused immediately after logout, not just forgotten client-side; `current_user`
   now requires the cookie instead of trusting an `X-User-Id` header defaulting to `"puneet"`. `User`
   gained `tenant` + `password_hash` (PBKDF2-HMAC-SHA256, stdlib only, no new dependency); `Session` is
   a new table. Migration is an `ALTER TABLE` on startup, backfills existing rows automatically. Dev
   accounts: `<id>-dev` for all four seeded users. Zero product-visible change — `current_user` only
   gates the dead `/briefs`/`/users`/`/me` routes the frontend never calls. **Deliberately NOT done:**
   wiring `require_auth` onto the ~150 live studio routes — waiting for Design's sign-in screen so the
   cutover is coordinated, not a silent lockout. Real bug caught and fixed during testing: SQLite
   round-trips `DateTime` as naive, comparing against an aware `now()` raised `TypeError` on every
   request — fixed with one `auth.utcnow()` used consistently for storage and comparison.
   Still open: SSO and desk-naming, both need confirmation from outside either side's authority.

**Round 47 — the sign-in screen, built and verified live.** Design built exactly to the login contract
from `ASK_DESIGN_47.md`: three-state gate (checking / unreachable / signed-out, kept visually and
logically distinct — a network blip must never read as a bad password), `GET /me` on load decides
which, all tenant data loading moved out of `componentDidMount` into `afterSignIn()` so nothing loads
before a session is confirmed, header avatar now shows the signed-in user's initial with a name/role/
sign-out menu, global 401 handler wired on both `apiCall` and `apiGet` (excluding `/login` and
`/logout` themselves) ready for when `require_auth` reaches the rest of the routes. `sc-if` 819/819
matched their claim exactly, my prior work (housesheet, ladder builder, message suggestions) all
confirmed present.

**Found and fixed a real bug — mine, not Design's.** `ASK_DESIGN_47.md` documented `POST /login` as
returning `200 {user:{...}}`; the actual route shipped the object unwrapped, `200 {...}`. My own
testing before writing that doc used raw curl/urllib and printed the unwrapped shape, but I wrote the
wrapped contract anyway — never caught the mismatch until loading Design's actual screen and watching
a correct password come back as "Could not reach the server." Fixed by wrapping the response
(`schemas.LoginOut`) rather than asking Design to rebuild already-correct code. Reinforces
[[design-contracts-need-shapes-not-names]] from the other direction — this time the mismatch was
between my own documentation and my own code, and only a live browser test against the real frontend
caught it. A curl-only verification pass is not sufficient once the other side has built a real UI
against the contract — [[browser-verification-available]].

Verified live end to end after the fix: wrong password (exact server message, fields preserved
correctly), correct login, sign-out then re-login as a different user (no session bleed), page reload
mid-session (session persists), the gate overlay confirmed to actually block pointer events to the
app underneath (`elementFromPoint` resolves inside the gate), and logout-then-replay-old-cookie still
correctly refused (401).
   Key finding while grounding it: a real authorization model exists (`domain.py` — approval levels,
   separation of duties, audit trail) behind a `User`/`Brief` SQL system the frontend never calls —
   0 references to `/briefs`, `/users`, `/me` in app.dc.html. The live product runs on `tenancy.py`'s
   JSON stores instead, which have **no identity concept at all** — `tenancy.tenant()` reads a single
   process-wide env var. Two disconnected systems; the one in use has nothing. Waiting on Design's
   questions before building.
2. **Audit #9, the measurement loop** — framing (`ASK_DESIGN_46.md`) → answered
   (`ASK_DESIGN_46_REPLY.md`): manual entry first, flat ledger per tenant (matched to plans/campaigns
   by geography+period at read time), report-only (matches the studio's "offered, sourced, never
   applied silently" convention), does not wait on #6. **The one open sub-question Design raised —
   repoint or replace SOM/benchmark — answered in `ASK_DESIGN_47.md`: repoint.** The two existing
   in-context fields stay exactly where they are on screen; underneath, they write through to the new
   ledger instead of their own one-off spot, and `esov()`/the social feasibility check get repointed
   to read from the ledger. A general manual-entry/CSV surface is separate future work for facts with
   no existing field, not a replacement for these two. **Not yet built:** the ledger schema, the
   ingest route, and the actual repoint — next round.
   Grounded in Design's own stated shape (metric/value/geography/period/source/date, feeding ESOV +
   social feasibility + campaign analysis) and the precedent that already exists twice in miniature
   (ESOV's share-of-market field, the social benchmark field — both person-entered, sourced, refused
   without a source). Open questions: manual/CSV/live-connection first, flat ledger vs. plan-scoped,
   whether it stays report-only or starts feeding gates, and whether entry needs #6's identity first.
3. **Design's literal-sweep overstatement — resolved.** They caught it themselves in round 45 without
   being asked again: `TEMPLATES`/`STATICS`/`VIDEOS` emptied, `formatDefaults('pack')` genericized,
   `packSuper` computed per-tenant, plus two live prompts (`writeFullScript`/`refineScript`) I hadn't
   caught. Zero live brand literals now, verified by grep.
4. **census.py rebuilt.** Both named gaps fixed: real brace matching (the old `[^}]{0,600}` regex was
   silently truncating 193 of 524 `setState(` calls at the first nested `}`, dropping every key after
   it from the written set with no signal that it happened) and alias tracking (`const o = this.og()`
   then `o.kit` now attributes correctly). Found a third gap while fixing the first two: most bags in
   this file are written via `setState(s => ({ ns: {...} }))`, a shape the old writer-search never
   covered at all — now does. Output split into real bags vs. plain getters (`activeBrand`, `tiers`,
   etc. have no writer contract and aren't a finding) to keep the report skimmable despite the extra
   coverage. Verified against synthetic fixtures reproducing both named bug classes.
5. **Housekeeping — done.** `social_plan/546ae757a9.json` ("pincode test") deleted; confirmed gone,
   no dangling references. ASK_DESIGN_43 was recovered after an accidental deletion (see chat) and is
   confirmed superseded by round 44/45 — does not need shipping.

## Round 53–54 (31 Aug 2026) — Expression by medium rebuilt; location wired into generation

Doc: `ASK_DESIGN_51.md`, folder `ask-design-round54/`, sha `5d820cc1ad27`. All shipped, adopt-only.

1. **Expression by medium rebuilt onto the medium vocabulary** — 6 producer-kind rows → 7 medium rows
   (TV, Social, Influencer, On-ground, OOH, Trade, POS material), same order as `CAMPAIGN_ROLES`/"Roles
   by medium." Digital dropped (it's Social run at high intent, not its own slot — user's own framing:
   "digital is social+influencer+seo... no need for an even message generation for digital"). Media
   planning dropped (retired producer, not a medium). Storage keys unchanged for the 5 pre-existing rows
   so no user data moved. Backend `media.py EXPRESSIONS` got `influencer`/`ooh` entries, verified via
   `media.normalise()` directly.
2. **Real `hasGo`/`goneAway`/`noProducer` three-state fix** — the old two-state logic showed a dead,
   empty-label button for any row with no `EXPRESSION_GO` entry at all. Influencer/OOH (no producer
   screen yet) now correctly render "No producer for this yet" instead. Verified live via page-text read
   — all 7 rows confirmed rendering the right state.
3. **"Lock the cast" → "Lock location and cast," backed by real wiring, not just a rename.** Traced
   `buildCastReference`→`/cast-reference` and `generateFrame`→`/scene-still` by hand: neither read
   Location/DoP/Props/Wardrobe text before this round — pure planning documents with zero effect on
   generated visuals. Answered the user's direct question with that finding, then wired it: cast
   reference image now anchors in the Location department's text when written (falls back to neutral
   backdrop when empty); every frame prompt now folds in Location/DoP/Props/Wardrobe text when written.
   `api/main.py` `py_compile` clean; frontend checkfe clean before and after.
4. **Not verified live end-to-end**: the Scripting screen's department cards and the location-aware cast
   lock — same reason as round 52's item 3 (needs a real generated concept + approved script, not free
   to force for a screenshot). Verified structurally only.

## Round 55 (31 Aug 2026) — Departments split fixed; two real bugs root-caused and fixed live

Doc: `ASK_DESIGN_52.md`, folder `ask-design-round55/`, sha `b0bcc84162`. All shipped, adopt-only.

1. **DoP Note/Prop Master/Wardrobe & Styling → Shoot Board.** Cast department card removed entirely —
   merged into the pre-existing "Frame generation guideline" (renamed from "Cast & continuity sheet")
   box, which is the field with all six real pipeline consumers (`videoCharacters`). Not a data
   migration — the redundant box was deleted, the load-bearing one kept as-is.
2. **Plan balance layer fixed** — root cause: `kind:"number"` layers write to `plan.balance`, never to
   `nodes.balance.rows`, so the generic "Draft this layer" panel (watching `rows`) showed "Nothing
   written yet" forever regardless of success. New "✦ Suggest a split" button lives in the card it
   actually changes. Verified live: real `/plan-generate` call, Declared bar updated from default to
   declared with a real reason.
3. **POS pack-gate false positive fixed** — root cause: `looks_like_pack()` blind-matched "pack" across
   the model's full route description, but every route is *correctly* instructed to mention the pack
   sitting locked at the base. Confirmed against 3 live-drafted routes: all 3 would have refused. Fixed
   by threading `hero_type` from frontend to backend so the check only applies to raw, routeless input;
   the real library gate for `endorser-with-pack`/`range-array` (which was previously inert — frontend
   never sent `hero_type` at all) now actually engages. Verified live end-to-end: real render succeeded
   (`200`, real image, `provider:google`) on the exact route text that would have been refused before.
4. **Tooling note**: the local studio server does not auto-reload on file changes — caught this the hard
   way mid-verification (fix looked broken, was actually stale process). Restart after backend edits.

Still not verified live across two rounds now: the Scripting screen (department cards, Frame generation
guideline) — needs a real approved script both times, which nothing this round required either.

## Round 56 (31 Aug 2026) — the Scripting screen finally loaded live; two real bugs found and fixed

Doc: `ASK_DESIGN_53.md`, folder `ask-design-round56/`, sha `8eae4ca871`. Adopt-only.

Spent real generation calls (twice — once to find the bugs, once to confirm the fix) to close the
"structurally verified, not live" caveat that had recurred across rounds 54/55. Found two real, checkfe-
invisible layout defects:
1. **CTA-before-prerequisite**: "Generate all frames" rendered 380px above "Lock location and cast" (its
   own gate), confirmed by pixel measurement. Fixed by moving the Frame generation guideline card above
   the Storyboard header/button. Re-verified against a second freshly-generated script: correct order.
2. **Single-card grid stretch**: round 55's Location-only grid (`minmax(280px,1fr)`) stretched its one
   card to ~980px — nearly 3x every sibling card in the app. Fixed by capping to `minmax(280px,330px)`.
   Verified via isolated `getComputedStyle` test (`"330px 0px"`), not a third live generation.

Prompted by the user pointing at the Anthropic `frontend-design` plugin/skill and asking for the same
rigor already applied to backend work — pulled the full skill + cookbook content verbatim (not summarized)
and applied its *process* discipline (plan → critique before shipping) rather than its aesthetic-reinvention
advice, since this app has an established visual system (Epilogue, Paper theme, navy `#17325E`) that a
"take a bold typography risk per screen" mandate would fragment, not improve.

Shoot Board (DoP/Props/Wardrobe cards) was reachable in the same live session but not separately reviewed
this round — natural next live-verification pass.

## Round 57 (31 Aug 2026) — Shoot Board reviewed live, department badge overflow fixed

Doc: `ASK_DESIGN_54.md`, folder `ask-design-round57/`, sha `ccc696085886`. Adopt-only.

Approved the round-56 script and opened Shoot Board with real content for the first time. Found the
department badge (34×34px colored square) was rendering the FULL label as wrapping text with
`overflow:visible` — confirmed via `getComputedStyle`, `scrollWidth:52` vs `clientWidth:34` on "Wardrobe &
Styling". The badge was the ONLY place a card's name appeared, so this wasn't decorative — short labels
(Music, Lighting) mostly survived, the three departments added in rounds 54/55 (DoP Note, Prop Master,
Wardrobe & Styling) didn't. Fixed: `DEPTS` gained a short `abbr` field per entry (`Loc`/`DoP`/`PM`/`W&S`/
`Lt`/`Mu`/`D/V`/`KS`) for the badge, plus a real text heading (`d.label`) beside it in both card templates
(Scripting's Location card and Shoot Board's grid). Verified live for short labels, worst-case
("Wardrobe & Styling") confirmed via isolated DOM test at the real 330px card width — no overflow, clean
34px row height. Also confirmed Shoot Board's 7-card `repeat(3,1fr)` grid was already correct (7th card
sits normally in column 1, not stretched — different mechanism from the auto-fit grid round 56 fixed).

This closes the "structurally verified, not live" arc open since round 54 — Scripting and Shoot Board have
both now actually been loaded with real content and reviewed. Three real defects found across rounds
53/54/57 (CTA ordering, grid stretch, badge overflow), none visible from template source alone.

## Round 58 (1 Sep 2026) — first real user-testing results, three findings, one is a genuine architecture fix

Doc: `ASK_DESIGN_55.md`, folder `ask-design-round58/`, sha `2b5d71db9bcc` (frontend; item 3 is backend-only).

1. **Cast department resurrected.** Round 55 removed it as a duplicate of the reference-sheet box: wrong
   call, caught by testing. The department box is a *casting brief* (who to hire, region, performance
   quality); the reference-sheet box is a *rendering spec* (age, build, wardrobe colour) — different
   writing, no other home for the former. `cast` back in `DEPTS`, `home:'scripting'`. Fine print corrected
   to say what's actually true about what feeds the reference sheet vs. what's read directly at lock time.
2. **Plan balance provenance.** "Suggest a split" and a human's own "Record the split" wrote an identical
   `declared:true` record — no way to tell a model suggestion from a real decision, the exact ambiguity
   `declared` itself exists to prevent, one level up. Added `source:'user'|'model'` to `plan.set_balance()`
   / `balance_of()` (old records fold to `'user'` — they predate Suggest, so that's not a guess), surfaced
   as a "Suggested by the skill" chip on the Declared card. Verified directly against a disposable test
   plan id (deleted after — see [[synthetic-dicts-write-real-tenant-files]]).
3. **POS key visual — root-caused, not patched.** The bad image from round 57 (an unrecognisable masked
   face on what was meant to be a calm schoolgirl) was NOT a prompt failure — the actual prompt sent
   matched `.claude/skills/posm/references/key-visual.md`'s hero-cutout template character-for-character.
   **Root cause: Google's Gemini/Imagen models have a documented, inconsistent safety filter against
   generating photorealistic minors — it distorts rather than refuses.** The deeper bug: the skill's own
   spec already said `person-in-benefit` needs "casting and usage rights" (same category as
   `endorser-with-pack`'s "signed talent... cast reference"), but the code only ever enforced that for
   `endorser-with-pack` — `person-in-benefit` rendered from raw hallucinated text same as a safe subject
   like a clock. Fixed by extending the existing gate + the existing (already-working)
   `gemini.image_from_reference()` path to cover `person-in-benefit` too: no cast reference in library →
   clean 409 refusal; a reference exists → generated from the real photo, not hallucinated. This also
   fixes the underlying safety-filter risk generally, not just for children. Verified live against the
   real server both directions (409 without a reference, 200 with a safe hero type — no regression) and
   confirmed `endorser-with-pack`/`range-array` gates untouched.
   **Found while investigating**: a purpose-built "Key Visual" skill already exists at
   `.claude/skills/posm/` — well-researched for Indian general/modern trade, matching everything the user
   asked me to build from scratch. The gap was never the skill; it was the implementation not fully
   enforcing what the skill already specified.
   **Not fixed, flagged**: `producers.key_visual()`'s drafting prompt has no library awareness, so it can
   still suggest `person-in-benefit`/`endorser-with-pack` routes that immediately hit the refusal — same
   pre-existing gap `endorser-with-pack` already had. Cheap follow-up if wanted, not the actual bug.

## Round 59 (2 Sep 2026) — measurement ledger core built (audit #9, phase 1 of 2)

No ASK_DESIGN doc — backend-only, additive, nothing on any screen changes. Built while the user was
mid-user-testing on their own running instance (confirmed live: new files kept appearing under
`tenants/default/media/` during this work) — deliberately built and verified against the disposable
`contractcheck` tenant and the spare `studio-verify` port (8010), never touching `default` or port 8000.

1. **`api/actuals.py`** — the flat per-tenant ledger agreed in `ASK_DESIGN_46_REPLY.md`: `add()`
   (metric/value/geography/period/source/date/note, all the "offered, sourced, never silent" refusals
   `set_som`/`set_benchmark` already model — no metric, non-numeric value, malformed period, or missing
   source all refused with a reason), `list_entries()` (filtered, most-recent-first), `match()` (exact
   `metric+geography+period`, no fallback ladder — deliberately not guessing one on behalf of consumers
   that don't exist yet), `remove()`, `metrics()`. Registered as `tenancy.KINDS` entry `"actuals"`.
2. **Routes**: `GET /actuals` (filtered list, read-only), `POST /actuals` (add), `POST /actuals-remove`.
   All in `main.py` right after `/media-market-share`, same request/response shape convention as the
   rest of the file (`payload: dict` in, `(record, error)` tuple out, 400 with `{detail}` on refusal).
3. **One real bug found and fixed before it shipped anywhere**: `_now()` is second-resolution, so two
   entries added in the same second tie on it — `list_entries`'s sort is stable, so a plain
   `sort(key=at, reverse=True)` left the OLDER of two same-second entries looking most-recent, silently
   inverting `match()`'s "latest correction wins" guarantee. Caught by a same-second duplicate-key test
   against `contractcheck`, fixed with an explicit append-index tiebreaker, re-verified.
4. Verified: full module test suite green against `contractcheck` (refusals, geography normalisation
   Maharashtra==MH, filtering, the same-second tiebreak, `match()` None-on-miss, `remove()`); `py_compile`
   clean on `main.py`/`actuals.py`/`tenancy.py`; live on `studio-verify:8010` — server started with no
   import errors, `GET /health` 200, `GET /actuals` 200 `{"entries":[],"metrics":[]}` against the (real,
   untouched) `default` tenant. `contractcheck/actuals/` wiped back to empty after; diffed the full
   tenant tree before and after — the only changes present are the user's own live media generations.

**Not done — phase 2, next round**: `mediaplan.esov()`'s `set_som`/`c["som"]` and `socialplan`'s
`set_benchmark`/`d["benchmark"]` still read their own one-off fields, not this ledger. Migrating them
needs one real decision phase 1 deliberately left open: `esov()` has no geography dimension today at
all (SOM is one flat value per brand), while the social benchmark is one flat value per PLAN regardless
of a cell's own geography — so "migrate" has to define what `match()`'s exact geography key should be
for each (`national` is the obvious default for both, preserving today's behaviour exactly) before
touching two already-verified-live features. Do this as its own round, with live verification after,
same as every other repoint in this project.

## Round 60 (2 Sep 2026) — first real user-testing feedback on video generation + POSM; two root-caused and fixed, one partial, one major gap found

Backend-only, no ASK_DESIGN doc yet. Three parallel Explore agents traced four reported bugs to their
actual code paths before any fix was attempted — every claim below is file:line grounded, not guessed.

1. **Pack drift on Scene 3/5 — fixed.** `library.shot_references()` (`library.py`) only ever assembled
   `cast`+`plate` as image references for `/scene-still`; a signed-off `pack` asset was never included
   despite the module's own docstring claiming it was ("image and video work pulls the signed-off pack
   shot... as a reference image" — true only for the unrelated POSM cutout path). Added `want_pack`/
   `pack_id` params to `shot_references()`; `/scene-still` now auto-detects a shot's own description for
   product keywords (pack/carton/tetra/FSSAI/pour/bottle/label) and attaches the real signed-off pack
   photo as a reference image, not just a text description. Verified: the user's exact named file
   (`heritage-daily-health-pack-shot.jpg`) is already their most-recently-signed-off pack asset, so
   `reference_url('pack')` already resolves to it — zero UI change needed for this to start working.
   Keyword regex verified against the actual 5 scene texts: fires on Scene 3 and 5 only, not 1/2/4.
   `pack_used` added to the response alongside the existing `plate_used`, same "answerable from the
   response" convention. Verified live on `studio-verify:8010`: server starts clean, `/continuity-status`
   (the one other caller of `shot_references`) unaffected by the new params.
2. **Scene 2 wardrobe — fixed.** `/scene-still`'s prompt hard-coded "identical clothing down to colour
   and detail" UNCONDITIONALLY whenever a cast reference was used — this is why the 5:45am bedroom shot
   came back in the exam-hall uniform: the fixed clause always won over whatever the shot's own
   description implied, the same "words fighting words" failure this codebase had already named for
   POSM once. Reworded: face/hair/skin/body/age still lock unconditionally (identity), but clothing now
   follows the new shot's own description when it says anything about it, defaulting to the reference
   only when it doesn't.
3. **Scene 4 spatial orientation — partial, real gap remains.** `continuity.py` checks brightness/
   saturation and whether *a* reference was attached, never blocking/facing; there is no per-scene
   blocking data anywhere and no code ever passes an earlier scene's own approved still as a reference
   for a later scene in the same setting (the API already supports arbitrary `reference_urls` — nothing
   in the frontend ever sends a sibling frame through it). Added a text instruction to the plate-reuse
   branch ("keep people in the same seats/positions and facing the same direction... unless this shot's
   own description calls for it") as a mitigation, but a `plate` is a static empty-location photo with no
   people in it, so it cannot itself carry blocking — this is a prompt nudge, not a guarantee. **Real fix
   needs a Design ask**: either a per-scene "reference this other frame" picker (the backend capability
   for this already exists, unused), or a structured per-scene location/continuity tag Design would need
   to add to the Shoot Board data model.
4. **POSM key visual — the missing "assemble" step, built.** Root cause: `posm.py` was already rewritten
   once (documented in its own `posm_skill/references/failures.md`) around "generate isolated asset
   layers, assemble downstream in a design tool" — correctly stopped the single-prompt hallucination.
   But **no assembly step existed anywhere** — not in `posm.py`, `main.py`, `composite.py` (pure
   ffmpeg/video, zero image-layering or text-rendering), or the frontend. `produceAdaptations()` just
   displayed the raw, isolated hero cutout as the "finished" poster for every format. `/posm-image`'s own
   response text had already been saying what was missing all along: *"mask it out of the white and
   place it on the flat brand-colour field with the pack, the type and the brand block."*
   Built `api/keyvisual.py` — a real Pillow compositor, not another prompt: white-key alpha extraction on
   the hero cutout (soft-feathered, no white fringe), a flat-colour OR AI-generated photographic backdrop
   (user's explicit call after I flagged the tension with the skill's own flat-field research — some
   routes genuinely need an environment, e.g. a green backdrop or a home kitchen; generating the backdrop
   as its own subject-free image and compositing in code is what avoids repeating the documented
   photo-background failure, rather than which background type is "correct"), a pack card, headline text
   rendered with real typography (Pillow's own bundled scalable font — no brand font FILE exists anywhere
   in this codebase yet, `brandprofile.py`'s own `fonts` field docstring says as much; `KEYVISUAL_FONT_PATH`
   is the override point for whenever one is uploaded — natural next step is a `font` kind in `library.py`
   alongside `pack`/`logo`), sized via `posm.cap_fraction()` (the real trade-practice minimum, already
   computed, never used until now), and the real logo. Two new routes: `POST /posm-backdrop` (generates
   the subject-free environment layer) and `POST /posm-assemble` (`{hero_url, format, headline,
   type_position, backdrop_url|field_hex, pack_url?, logo_url?}` → composited PNG; pack/logo default to
   the brand's signed-off/on-file assets when not given explicitly).
   **Two real layout bugs found and fixed via actual visual inspection** (rendered synthetic test
   composites and viewed the PNGs, not just checked for exceptions): (1) the pack card was anchored to
   the canvas corner, which for `type-locked-base` sat directly inside the dedicated headline band and
   overlapped the text — re-anchored to the hero's own box instead; (2) very wide "violent-band" formats
   (a 12:1 shelf strip) still forced a full hero into a 130px-tall canvas, overlapping the logo and text —
   `posm.reflow()` already names exactly which formats cannot carry a photographic hero at all
   (`dropped_layers()`'s own tier rule), and the compositor simply wasn't reading a rule the codebase had
   already computed; now drops to a logo/text/pack minimal layout on those formats, matching the existing
   spec instead of fighting it.
   Verified: `py_compile` clean; three composites rendered against synthetic stand-in assets (a disposable
   tenant, cleaned up after) and visually inspected after each fix — flat-field base layout, AI-backdrop
   beside layout, and the violent-band minimal layout all correct on the second pass; live on
   `studio-verify:8010` — both new routes correctly reject malformed input (missing hero, unknown format,
   missing backdrop brief) with no server errors, confirmed via real HTTP calls, without writing into the
   live `default` tenant.
   **Not done / honestly rough**: no real brand font file (falls back to Pillow's generic bundled face —
   cosmetically fine, not the brand's actual display type); pack compositing places the source photo in a
   card rather than a true silhouette cutout (no segmentation model is a dependency; a bad auto-cutout
   would be worse than an honest card); this is backend-only — nothing in `app.dc.html` calls
   `/posm-assemble` yet, so wiring "generate" through to a real assembled preview on screen is a Design
   ask, not a further backend gap.

## Round 60 continued — two generation lanes, tied to production method, not style preference

User pushed back with a reference photo (four real people naturally composed in an environment, holding
product) showing the cutout+compositor approach is the wrong tool for group/occasion key visuals — it
needs the same identity-pinning mechanism frame generation already uses (`image_from_reference` with
real cast photos), not a flat field with one cutout on it. Separately, user named a real physical
constraint: hand-painted/large-format POS (wall paintings, hoardings painted at scale) needs flat spot
colours a painter can reproduce, not photographic art — asked for two lanes exposed as buttons.

1. **`posm.production_mode(fmt)` — new, in `posm.py`.** Found the constraint was ALREADY on file and
   unread: `FORMATS["wall-paint"]["substrate"]` = `"hand-painted, flat spot colours"` with an explicit
   `trap` note ("no photograph, no gradient, no soft shadow") — the same fact `bleed_safe()`'s own
   `"paint" in sub` check already keys off, generalised into a lane decision. Returns `{mode: "paintable"
   | "rich", why}`; a caller override always wins, this is only the default nobody already chose.
2. **`/posm-image` now reads it.** `mode` (explicit or auto from format) forces the `vector` style
   register — rewritten to be explicit ("bold flat shapes, hard edges, no gradient... reproducible by a
   sign painter or a screen print") — regardless of what `style` was passed; a photograph is not a style
   choice on a substrate that cannot hold one. Response now reports `mode`/`mode_why`.
3. **`/posm-backdrop` now refuses a paintable format outright** (409, names the format and the reason,
   points at the flat-field alternative) rather than silently generating a photographic backdrop nothing
   can produce at scale.
4. **`POST /posm-scene` — new, the integrated-scene lane.** One generation call, everything baked in —
   people, environment, product, headline AND logo together — the opposite choice from
   `/posm-image`+`/posm-assemble` on purpose, per the user's explicit call after I flagged the risk
   (AI-drawn text/logo is exactly the failure `posm.py` was rewritten away from once; they chose it
   anyway, so it ships with the risk visible in the response rather than hidden). Reuses
   `library.get()`/`reference_url()` for cast/pack references, same as everywhere else; `cast_ids` lets
   several named library entries stand for several different real people (Gemini caps total references
   at three, shared with the pack — logo is described in text, not spent as a fourth reference image,
   a visible tradeoff favouring identity/pack fidelity over logo fidelity). Refuses on a paintable format
   (409, same reasoning as `/posm-backdrop`).
   **Real, current gap surfaced, not hidden**: checked the library directly — **zero signed-off cast or
   actor photos exist on this account right now.** Every person in a generated scene is hallucinated
   until real photos are uploaded and signed off under Library → Cast, same prerequisite `/cast-reference`
   already has for film. `/posm-scene`'s response carries `has_cast:false` and says so explicitly rather
   than implying the scene used a real reference when it didn't.
   Verified live on `studio-verify:8010`: `production_mode()` correct for wall-paint (paintable) vs.
   poster-a4/dealer-board (rich); both new/changed routes correctly refuse a paintable-format photographic
   request (409, specific reason) and an empty scene brief (400) with no server errors — no real
   generation call made (would cost real API credits; the refusal/validation paths are what's new here,
   the generation call itself reuses `gemini.image_from_reference`/`creative.image_from_reference`
   already proven working in `/scene-still` and the original `/posm-image`).

## Round 61 (2 Sep 2026) — ASK_DESIGN_56 sent: three frontend gaps behind round-60's backend work

Doc: `ASK_DESIGN_56.md`, folder `ask-design-round59/` (frontend base unchanged since round 58 —
`sha256: 2b5d71db9bcc…`, no merge needed, nothing touched `app.dc.html` in rounds 59–60). Sent, not yet
answered/adopted.

Triggered by live testing: user hit `/posm-image`'s `person-in-benefit` 409 refusal and found no way to
act on it from the POSM screen (Library's cast/actor upload only exists in a completely separate Memory
tab, unlike Video Studio's inline cast-lock). Three asks, in ship order:
1. **Inline cast/pack/logo upload in POSM** — render an uploader directly from a 409's
   `gate.blocks`/`gate.asset_blocks`, using the existing unchanged `POST /library-add` (multipart:
   `kind`, `files`, ...) → `POST /library-sign` (`{id, on:true}`) → retry. Flagged real dead data found
   while checking: `kind:"actor"` items `take-1`/`take-2` (13 Aug) are literal 70-byte 1×1 pixel PNG
   stubs, not real photos — not cleaned up from this ask, the user has "Remove" already.
2. **Sibling-frame reference for continuity** (the Scene 4 orientation gap from round 60) — `/scene-still`
   already accepts a `reference_urls` ARRAY, but `generateFrame` has only ever sent the singular
   `reference_url` (just the cast). Ask: add a "match this to another shot" picker, switch that one call
   site to the array form (`[castRefUrl, siblingUrl].filter(Boolean)`) when a sibling is chosen. No
   backend change — confirmed by reading the actual current `generateFrame` code before writing the ask,
   not assumed.
3. **Wire `/posm-assemble` + `/posm-scene` + the paintable/rich mode switch** into `produceAdaptations()`,
   replacing "show the raw hero cut-out as the finished tile" with a real composited or integrated-scene
   image. Full contracts for all three routes given verbatim (payload/response shapes), per
   [[design-contracts-need-shapes-not-names]].

## Round 62 (2 Sep 2026) — ASK_DESIGN_56 adopted, one real bug caught and fixed before shipping

Design's reply arrived as `handover.md` (a 2474-line cumulative log — the actual new content is its last
section, "Round 53 — the three POSM/frame gaps from ASK_DESIGN_56"; the rest is every prior round's
report concatenated) plus `app.dc.html` at the OPUS root. Base confirmed as my round-58/61 file
(`sha256 2b5d71db9bcc…`) adopted whole, LF-clean. Diffed before touching anything: 12 hunks, all pure
additions except one cosmetic whitespace join (two statements landed on one line — harmless).
`tools/checkfe.py` clean (843/843 `sc-if`, 335/335 `sc-for`, 2766/2766 `<div>`, 747 class members, all 4
revert sentinels present).

**Items 1 (inline gate uploader) and 2 (sibling-frame reference) adopted exactly as sent** — both match
ASK_DESIGN_56 precisely, verified by reading the actual diff, not just trusting the report.

**Item 3 had a real bug, caught before going live**: Design explicitly flagged uncertainty about the
hero-type → lane split (`/posm-assemble` vs `/posm-scene`) and asked me to confirm. Traced it against
`posm.HERO_TYPES` and `/posm-image` server-side (`main.py` ~5190) rather than guessing: `person-in-benefit`/
`endorser-with-pack` were routed to `/posm-scene`, but `/posm-image` **already** identity-pins those two
via a signed cast/actor reference before the lane-split code even runs — sending them to `/posm-scene`
threw away that correctly-referenced cutout and regenerated from scratch with no reference at all,
losing real identity fidelity and wasting a generation call. Meanwhile `occasion` ("a relationship, not
just an event" — several real people together) is the hero type that actually needs `/posm-scene`, and
it wasn't in Design's list at all, silently defaulting to the wrong lane. Fixed:
`const sceneLane = (kv.hero || '') === 'occasion';` — one line, both halves of the correction. Re-ran
checkfe after — clean. Wrote `ASK_DESIGN_56_REPLY.md` explaining the correction with the same rigor
Design used asking the question, so it's not re-guessed next round.

Not verified live — same standing limitation Design themselves named: POSM needs a real approved
brief/route to exercise, not available this round either. Structural + server-side trace only.

Live file: `api/frontend/app.dc.html`, prior version kept at
`app.dc.html.bak-pre-round59-adopt`. Flagged, not built: `/posm-scene` still only ever sends one implicit
cast reference (no `cast_ids`), so a multi-person `occasion` piece identity-pins at most one person —
natural follow-up, not part of this ask.

## Round 63 (2 Sep 2026) — stale server process found; a second real pack-gate false positive, root-caused

**Stale server**: the user's live testing was hitting `uvicorn main:app --host 127.0.0.1 --port 8020` with
**no `--reload` flag**, running continuously since 2026-09-01 12:41 — before all of today's work (rounds
59-62: pack/wardrobe/orientation fixes, the whole POSM compositor, ASK_DESIGN_56's adoption). Explains a
"Not assembled — Not Found" (the new routes didn't exist in that process's memory) and a fully-baked
photorealistic scene with baked-in text (the pre-round-58 behavior `cutout_prompt()` has forbidden since
round 58). I don't have permission to kill an arbitrary process from here (correctly blocked by the auto
mode classifier) — gave the user the exact restart command with `--reload` added this time.

**Second real bug, same failure class as round 58's pack-gate fix**: after restart, a drafted "occasion"
route ("The moment of use... the pack present but not the subject") still tripped
`posm.looks_like_pack()`'s false-positive refusal. Traced to `producers.py:344` (`key_visual()`):
`"hero": hero if hero in posm.HERO_TYPES else ""` is an **exact-string match** against the model's own
freely-generated text — "Occasion" vs "occasion", or trailing whitespace, silently drops a real hero type
to `""` with **zero logging**, so it was invisible until traced by hand. Once `hero_type` reads as
unrecognized downstream, the pack-word bypass doesn't apply, and the route's own legitimate "pack present
but not subject" description trips the refusal — round 58 closed one entry point into this exact failure
class (threading `hero_type` frontend→backend at all); this was a second, different entry point (the
threading works, but the value it carries can be silently wrong) that survived it.
Fixed: normalise (`lower()`, whitespace/underscores→hyphen) before the membership check — verified against
realistic model-output variants (`"Occasion"`, `"occasion "`, `"person in benefit"`, `"ENDORSER-WITH-PACK"`
all now match correctly; a genuinely unrecognized string still safely falls back to `""`, preserving the
existing safety behaviour). `py_compile` clean, server starts clean on `studio-verify:8010`.
**Caveat for the user**: this fixes future route generations — the specific "moment of use" card already
on screen was drafted before the fix and still carries the old dropped-to-empty `hero`; regenerating routes
(or a fresh "Develop other routes") is needed to get a card with the corrected value.

## Round 64 (2 Sep 2026) — the POSM asset panel: surfaced up front, not discovered after a refusal

User's own framing: "post facto, figuring out what was missed is always seen as poor UI and frustrating
experience." Built directly in `app.dc.html` (not routed through Design this time, given session pace) —
a new "Assets for this piece" panel appearing immediately once a route is picked, before format
selection, instead of only surfacing gaps after a failed render.

1. **`POST /library-adopt` — new backend route.** The missing half of `library.add()`'s own `source`
   param, which has said since it was written "if a generated asset is ever admitted deliberately, it is
   visible as such." Takes a freshly-generated media URL, downloads it (reuses `keyvisual._resolve_bytes`),
   saves it into the library under a given kind with `source:'generated'`, signs it off in the same call.
   This is what turns "generate a draft" into "use it" without a download-then-reupload round trip.
2. **`/posm-image` gained a `cast_id` override**, matching the `pack_id` pattern already on `/scene-still`.
   **Found and fixed a real pre-existing bug while touching this code**: the cast/actor fallback loop had
   a stray unconditional `break` that exited after checking only `"cast"`, never falling back to `"actor"`
   when cast came up empty — invisible until traced by hand, same silent-failure shape as the two other
   POSM bugs found this session.
3. **Frontend panel, four asset lanes**, shown right after a route is selected:
   - **Pack shot / Logo** — a picker over existing signed-off items + inline upload, reusing the exact
     add→sign-off flow the gate uploader (ASK_DESIGN_56 item 1) already shipped.
   - **Model/cast** (only shown for `person-in-benefit`/`endorser-with-pack` routes) — picker + an
     "AI draft" button (reuses Video's `/cast-reference`, seeded from the chosen route's own description)
     + a required "Use this — sign it in" approval step before a draft becomes usable. Deliberately not
     silent: the risk this exists to manage (a hallucinated person, same class as round 58's safety-filter
     incident) is named on screen next to the draft, not hidden behind convenience.
   - **Location/backdrop** — free-text brief + "AI draft" (`/posm-backdrop`), used directly since backdrop
     carries no gate of its own; no adopt step needed.
   Choices thread into `produceAdaptations`'s existing calls: `cast_id`/`pack_id` into the hero/scene
   calls, `logo_url` (resolved from the picked item's own URL — `/posm-assemble` takes a URL, not an id)
   and `backdrop_url` into `/posm-assemble`.
4. **One real bug caught before shipping, via live network inspection, not just checkfe**: the cast/
   location preview images were written as `<img src="{{ posmCastCard.draftUrl }}">` gated by `sc-if` —
   but an `<img>` fetches its `src` the instant it's in the DOM regardless of whether the surrounding
   `sc-if` is true, so with no draft yet, the browser requested the LITERAL unsubstituted string
   `{{ posmCastCard.draftUrl }}` as a URL (a real 404, confirmed in the network log, not `checkfe`-visible
   since it's a runtime-only failure). Fixed the same way this file already solves it elsewhere
   (`frameImg`): build the `<img>` as a real element (or `null`) in the JS bag, reference it as a bare
   `{{ }}` node, never as a template string inside a `src` attribute.
   Verified live on `studio-verify:8010`: `checkfe.py` clean throughout (853/853 `sc-if`, 338/338 `sc-for`,
   2785/2785 `<div>`), `py_compile` clean on all five touched backend files, and the fresh page load's
   network log confirmed clean (no literal-`{{}}` request) after the fix — the earlier 404s were real,
   reproduced, and gone on the next check, not assumed fixed.
   **Not verified**: the actual AI-draft/adopt round trip end-to-end (needs a real approved route + real
   API credits, same standing limitation as every POSM round this session) and the full click-path through
   Execution → POS (couldn't reliably reach it via scripted clicks without visual feedback in this
   environment) — structural and static verification only for the panel itself.

## Round 65 (2 Sep 2026) — the shared "studio shot" primitive: photoshoot angles + combined shots

User's own framing, generalizing the asset panel further: a proper photoshoot for the model (multiple
angles so different POS formats aren't all force-cropped from one static shot), a pack-shot compositor,
and the ability to COMBINE model+pack into consumption/usage shots — explicitly meant to be reusable by
frame regeneration too, not POSM-only.

1. **`POST /studio-shot` — new shared backend primitive.** One route, not three: takes any combination
   of `{cast_id, pack_id, plate_id}` (locked library references) + a free-text `action` + an optional
   `angle` hint + `mode` (`'cutout'` isolated-on-white, feeds `/posm-assemble` like today's hero cutout;
   `'scene'` a complete styled photographic moment, for a styled pack shot or consumption shot that IS
   the finished visual). Refuses with a clear 400 if zero references are given — deliberately not this
   route's job to hallucinate a subject; that's `/posm-image`/`/posm-backdrop`. Named directly in its own
   docstring as reusable by `/scene-still` later — a shared building block, not a POSM-only feature.
   Verified live: correct 400s for no-action, no-references, and an invalid id (resolves to no refs,
   same refusal) — no server errors.
2. **Model photoshoot** — three standard angle slots (full body / three-quarter / tight crop) in the
   Cast card, each independently regenerable, shot FROM the locked cast reference via `/studio-shot`
   (`mode:'cutout'`) rather than from scratch. Framed explicitly against the real gap this closes:
   `posm.reflow()`'s own text already says a "wider" format "re-crop[s] the hero cut-out — a full figure
   becomes upper body" and a "violent" one drops the hero because "nothing croppable survives" — one
   static shot was always going to fail some formats; three angles gives each format's own band a shot
   that actually fits it. (Auto-mapping which angle feeds which format by band is the next increment,
   not built this round — today's per-format hero selection still uses the single hero cutout;
   the angle slots are generated and ready, not yet wired into `produceAdaptations`'s format loop.)
3. **"Studio shot" gallery** — the open-ended case (styled pack shots, consumption shots), shown once
   either a model or a pack is locked. Checkboxes choose which locked references to combine, a free-text
   action field, results accumulate in a gallery (not a single slot, since these are open-ended rather
   than a fixed set). Honesty built in on screen, not just in the docstring: the card's own copy warns
   "a combined shot is the hardest case for fidelity; expect to redo one occasionally" — set that
   expectation up front rather than let a bad first result read as broken.
4. **Verified**: `py_compile` clean; `checkfe.py` clean throughout (860/860 `sc-if`, 340/340 `sc-for`,
   2795/2795 `<div>`); live network check on `studio-verify:8010` confirmed **no repeat** of round 64's
   literal-`{{}}`-as-image-src bug — all new previews built as real JS elements via the same `previewImg()`
   helper from round 64, checked specifically because that failure mode is invisible to `checkfe` and was
   only caught by network inspection last time.
   **Not verified**: the actual generation round trip (needs real API credits + a real approved route,
   standing limitation all session) and per-format angle auto-selection (not built yet, see #2).

## Round 66 (2 Sep 2026) — angle→format auto-mapping built; ASK_DESIGN_57 sent

1. **Angle→format auto-mapping, built.** `/posm-adapt` already returned `reflow.band` per format (no
   backend change needed) — `produceAdaptations` now maps `wider→tight`, `taller→fullbody`, `near→threeq`
   and uses that photoshoot angle's URL as the format's `hero_url` when it's been shot, falling back to
   the shared hero cut-out otherwise. Verified: `checkfe.py` clean, live server starts clean.
2. **ASK_DESIGN_57 sent** — doc + `ask-design-round60/` (sha `2272f038399c…`). Since I built rounds
   64–66's entire POSM asset panel / photoshoot / studio-shot system directly in `app.dc.html` without a
   round-trip, the doc's primary job is telling Design what changed under them (so their next diff reads
   as intentional, not something to chase) before asking for anything new. Two real asks: (1) reuse the
   same locked-reference-combination idea in frame regeneration — `/scene-still` already auto-attaches
   pack/cast, so this is an affordance gap (an explicit "include pack" toggle per scene, or routing a
   product-interaction beat through `/studio-shot` instead) more than a backend gap; (2) an optional
   polish pass on the panels built at live-testing pace. One stretch idea flagged, not scoped: picking a
   "Studio shot" gallery result directly as a format's finished master, bypassing compositing entirely.

## Round 67 (2 Sep 2026) — ASK_DESIGN_57 adopted clean, no corrections needed

Base confirmed `2272f038399c` (round 66), adopted whole. Diffed before touching anything: 4 hunks, all
pure additions, zero overlap with anything else. `checkfe.py` clean, matching Design's own reported
counts exactly (861/861 `sc-if`, 340/340 `sc-for`, 2795/2795 `<div>`) — first round in a while needing
**no correction on this side**.

Built exactly item 1's lightweight shape, deliberately over the fuller `/studio-shot` reroute: an
"Include the locked pack" checkbox per scene card (`sc.hasPackLocked` reads the SAME `pm.packChoice`
POSM's asset panel already sets — confirmed one shared piece of state, not a duplicate), sending
`include_pack:true` explicitly on `generateFrame`. This maps onto `/scene-still`'s existing contract with
**zero backend changes** — `want_pack = payload.get("include_pack")` already treats an explicit `true` as
an override over the keyword heuristic, exactly as designed weeks ago. Verified live on
`studio-verify:8010`: clean load, no console errors.

Design explicitly verified all of round 64–66's work survived first (grepped directly, not assumed) and
left the fuller consumption-shot routing and the optional polish pass both explicitly open rather than
guessing scope nobody asked for.

## Round 68 (2 Sep 2026) — the studio generalized: FMCG "pack" gets a category-agnostic "product" sibling

User's ask: the whole photoshoot studio should work for a fashion/apparel shoot, not just FMCG. Checked
what was already category-agnostic before building anything: the model's three angle presets
(full-body/three-quarter/tight-crop), `mode` (cutout/scene), free-text `action`, and cast/plate handling
all already generalize with zero change — a lookbook shoot wants exactly those framings too. The one
genuinely FMCG-specific piece was "pack."

1. **New library kind `"product"`** — `library.py`, deliberately a second kind rather than widening
   `pack`'s own wording: `pack` still means shelf packaging specifically everywhere the studio already
   reads it (the POSM pack-gate, `_PACK_WORDS`), so a fashion brand's garment was never meant to satisfy
   a check written for a milk carton. Added to `MEDIA_KINDS` too. Confirmed live: `GET /library` picked
   it up automatically — the Ground Truth upload screen's kind-chip picker already reads `library.KINDS`
   generically, so it gained a "Product shot" option with **zero frontend change**.
2. **`/studio-shot` accepts `product_id`** alongside `pack_id`, generalized role-text ("the exact
   product — same colours, materials, shape and proportions" — no "label" wording, works for a jacket
   as well as a carton).
3. **`/posm-assemble` and `/posm-scene` also accept `product_id`** — resolved into the same composited
   pack-card slot / reference list respectively, so the whole pipeline is consistent, not just the new
   primitive. **Caught one real gap before shipping**: `/posm-scene`'s role-description text only checked
   `"pack" in kinds`, so a `product` reference would have been attached as an image but silently dropped
   from the "reproduce faithfully" instruction — fixed to cover both kinds.
4. **Frontend**: a "Product" card mirrors Pack shot exactly in the assets panel, **hidden entirely until
   at least one product-kind asset exists** — an FMCG-only account (Heritage, today) never sees a lane
   it has no use for. "Include the product" toggle added to the Studio Shot card alongside model/pack.
   `productChoice` threaded into both `/posm-assemble` and `/posm-scene` calls in `produceAdaptations`.
   Verified: `checkfe.py` clean (864/864 `sc-if`, 341/341 `sc-for`, 2798/2798 `<div>`); live load on
   `studio-verify:8010` clean, no console errors; backend confirmed live (`product_id` in `/studio-shot`'s
   own refusal text, correct resolution/refusal for a fake id).

## Round 69 (2 Sep 2026) — root cause of "both providers refused": real library references never resolved

User hit this live: a Studio Shot using the real signed-off pack shot failed with "Both image providers
refused — check credits", a misleading message (there's no actual `render-log.txt` file — that text
points at stderr console output nobody had visibility into). Reproduced the exact call on
`studio-verify` and read the real stderr, which named the actual failure precisely.

**Root cause, two related bugs**: `gemini.local_path()` only ever recognized `/media/...` paths (this
app's own generated output) — a real library asset (`/library-file/pack/...`, what `library.get()`
always returns) matched nothing, so `_as_base64()` silently returned `None` for it with **zero error
printed**, `image_from_reference()` read that as "no usable reference" and returned `None` cleanly, and
the caller fell through to fal — which failed loudly for an unrelated reason (fal's servers do the
fetching themselves; a relative path is meaningless off this machine) — and *that* error was the only
one visible, misattributing the whole failure to fal/credits when the real bug was upstream in Gemini's
resolver never being reached with usable data. This is not new-code-only: every prior round's "verified
live" claims for the endorser-with-pack/person-in-benefit reference path used `library.reference_url()`
the same way — meaning **this bug likely also affected those**, just never surfaced because those tests
happened not to need the fallback path or got lucky with what "no usable reference" degraded to.

**Fixed**: `gemini.local_path()` now also resolves `/library-file/<kind>/<file>` via `library.local_path()`
(mirrors `keyvisual._resolve_bytes()`'s already-correct handling of the same prefix — that module had it
right, `gemini.py` didn't). `creative.py` gained `_fal_ref()` — passes real `http(s)`/`data:` refs
through unchanged, base64-encodes anything local (media OR library) into a `data:` URI fal can actually
use; logs a count when references get dropped instead of silently sending an unusable path.

**Verified for real, not just structurally**: reproduced the exact failing call before the fix (confirmed
the precise stderr trace above), reproduced it again after — **200 OK**, and inspected the actual
generated image: pack label, "25 years," colours and the fine-print compliance text all faithfully
reproduced from the real reference photo, with the requested splash and wavy milk. Sent the file to the
user as proof rather than asserting success from a status code alone.

**Also fixed, same session, unrelated root cause**: `500x500.png` (a real Heritage logo image) had been
misfiled under the "pack" kind since 31 Aug — not a bug, pre-existing bad data the user kept running into
via the Logo card correctly reporting "nothing signed off." Recategorized it into "logo" properly
(moved the file, updated the manifest row) rather than duplicating it — `library.add()`'s sha256 dedup
correctly refused to store the same bytes twice under a different kind, which is why a naive "just
re-upload it as logo" attempt returned the original pack-kind row unchanged.

## Round 70 (2 Sep 2026) — the real Key Visual defect: hero generation never referenced the pack at all

User compared Key Visual's output directly against Studio Shot's and correctly read it as a real quality
gap, not a style preference: the "hero" was a blurry, unbranded cluster of jars; the real pack only
appeared as a small disconnected corner card. Root-caused precisely rather than guessing a fix:

**`/posm-image` only ever attached a reference for cast (`person-in-benefit`/`endorser-with-pack`) —
never a pack, for ANY hero type.** Checked against `posm.HERO_TYPES`'s own stated `needs` field: three
of six hero types were silently hallucinating the product from text alone — `endorser-with-pack` (needs
cast AND the pack held), `range-array` ("every pack as a library reference"), `demonstration` (needs the
mechanism/product to actually show). `person-in-benefit` and `metaphor-object` were correctly
reference-free (by design, not by accident).

**Fixed, hero-type-aware**: `/posm-image` now attaches pack references matching each type's own stated
need — one pack for `endorser-with-pack`/`demonstration`, every signed-off pack (or an explicit
`pack_ids` list) for `range-array`, up to the 3-reference cap. Explicit `cast_id`/`pack_id`/`pack_ids`
always override the default. Response now reports `pack_used` so `/posm-assemble`'s corner card
(next round's frontend follow-up) can skip itself once the hero already carries the pack faithfully.

**Verified live with real generations, and the evidence was mixed until a second real fix**:
1. `range-array` first attempt (2 real packs, generic identical role text: "one of the real packs...")
   → 200 OK, structurally correct (two distinct pouch shapes, right proportions) but **both labels came
   back as generic smiley-icon art, neither matching either real pack**. A genuine finding, not hidden:
   multiple simultaneous product references don't hold fine label detail as reliably as one does.
2. Root-caused that specifically: every pack reference carried the *identical* generic sentence, giving
   the model nothing to tell them apart by. Fixed: each reference now named individually (its own
   `library` item name, "the real '<name>' pack... distinct from any other pack reference here").
3. Re-ran the same test — **dramatic improvement**: both packs now carry the real Heritage logo, correct
   product names ("Daily Health Toned Milk," "25 years of Heritage" — near-exact match to the real
   reference), consistent branding. Fine-print nutrition/regulatory text remains imperfect — a separate,
   known AI-text limitation (same reason headlines are composited, not generated), not something this
   fix was meant to solve or claims to.

Also confirmed live: `endorser-with-pack` with a deliberately invalid `pack_id` correctly 409s on the
pre-existing cast requirement (unaffected by this change — gates still enforce correctly).

**Cost/process note**: this round spent three real generation calls (one pack+splash proof, two
range-array iterations) — justified given it directly resolved the user's own side-by-side comparison,
but worth naming since most of this project's verification has been structural/dry-run. `py_compile`
clean throughout.

## Round 71 (2 Sep 2026) — round 70's fix wasn't actually reachable from the UI; wired it, plus the
corner-card follow-up in the same pass

User caught it directly: "this is because there is no input field for POS/Key visual before rendering."
Checked and confirmed — the asset panel's pack picker (`p.packChoice`) has existed since round 64, but
`heroBody` (the actual `/posm-image` call `produceAdaptations` sends) only ever included `cast_id`, never
`pack_id`. Round 70's entire hero-type-aware fix was real, backend-correct, and proven via three direct
API calls — but genuinely unreachable by clicking "Render" in the real app, because nothing sent the
picker's value. Fixed: `heroBody.pack_id = p.packChoice`, deliberately **not** sent when `hero_type ===
'range-array'` — that picker only ever holds one choice, and the backend's own auto-gather-every-pack
default (proven live last round) is strictly better for that specific type than narrowing it to one.

**Closed the deferred corner-card follow-up in the same pass**, since it's the same code path: found
that just omitting `pack_id` from `/posm-assemble` would NOT have skipped the card — the route already
falls back to the default signed-off pack when nothing explicit is given, so silence means "add the
default," not "add nothing." Added a real `skip_pack` flag to `/posm-assemble` for this specific case
(hero already carries the pack — `heroD.pack_used` — AND this format tile is using the shared hero, not
a photoshoot angle shot, which never carries the pack regardless of what the shared hero did).

Verified: `py_compile` and `checkfe.py` both clean (864/864 `sc-if`, 341/341 `sc-for`); live check on
`studio-verify:8010` confirms `skip_pack` parses correctly and existing validation is unaffected.

**Why:** the user asked for one tracked inventory rather than being the one who remembers. Keep this
current after every round; strike an item only when verified in the loaded page or against a live route.
Related: [[user-testing-round-2-open-items]] (folded in here), [[browser-verification-available]],
[[design-handovers-merge-never-replace]].

## Round 72 (2 Sep 2026) — root cause of the truncated Key Visual headline: `assemble()` drew off-canvas
text with no fit-check, silently

User reported round 71's fix didn't help: "studio shot is taking the right inputs... while the main POS
render is still not upto the mark," with a screenshot showing a visibly cut headline on the Poster A3
tile. First ruled out the CSS layer empirically (`img.style.aspectRatio = '5:7'` — colon syntax — is
invalid and the browser silently drops it, verified live via `javascript_tool`: `rawPropertyValueAfterSet`
comes back `""`, computed style stays `auto`; `objectFit:'cover'` therefore does nothing either, since it
needs a constrained box to crop against). So the display layer wasn't cropping anything — the PNG itself
had to already be wrong.

Reproduced directly against `keyvisual.assemble()` with a real pack+logo from the library and an
11-word headline at `poster-a3`/`type-locked-base`: the wrapped headline needs 4 lines at the format's
mandated cap height, the type zone only holds ~2.6, and `assemble()` had no check for that — it just kept
drawing downward past the zone and off the bottom of the canvas, silently dropping the tail of the line.
Confirms `posm.adaptation()`'s own docstring warning ("silently shipping nine words onto a gondola
header") was already known as a risk, but the `words_allowed`/`uses_short_line` gate that guards against
it lives in a *different* function (`/posm-adapt`) and nothing enforces it at the point that actually
draws pixels — `/posm-assemble` takes whatever headline string it's given and draws it regardless of fit.

Fixed in `keyvisual.py`'s `assemble()`: computes `total_h` vs the zone's own height before drawing, and
raises a clear `ValueError` ("wraps to N lines... does not fit the type band... write a shorter version
... or choose a bigger piece") instead of drawing overflow off-canvas. No frontend change needed — the
"STEP 3: the pieces" tile already has a designed failure path for this (`pi.assembleFailedWhy`, wired to
`/posm-assemble`'s existing exception handler) that was never exercised because nothing upstream ever
failed loudly before. Verified live on `studio-verify:8010` (stopped and restarted to pick up the backend
edit — a stale server previously running old code masked the fix on the first curl test): the 11-word
headline now returns a clean 409-shaped refusal with the exact message above; a 6-word headline at the
same format still assembles normally.

**Why:** cap height is a print-legibility floor, not a style choice (`posm.cap_fraction`'s own docstring)
— shrinking the font to force-fit would defeat the reason the module exists. Refusing with the exact
word/line count and the two real options (shorten the line, or use a bigger piece) matches how every
other length-driven gate in this codebase already behaves. Related: [[app-dc-html-is-lf-not-crlf]]
(no frontend edit this round, so N/A here, but keep in mind next time this tile changes),
[[browser-verification-available]].

## Round 73 (2 Sep 2026) — headline art made genuinely bold/multi-script; real cast/location/pack
references wired into video's cast-lock, before rendering

Two user asks in one turn. First: "headline needs to be art as well... bold and stylised... readable
from a distance" — round 72's fix only stopped the overflow; `keyvisual._font()` still fell back to
Pillow's own thin bundled default, and Heritage's own brief names Telugu/Kannada/Tamil/Hindi as core
markets, so a single Latin display font would've rendered boxes for non-Latin headlines. Asked and got
explicit permission (file downloads are gated) to bundle Noto Sans Bold — Latin, Devanagari, Telugu,
Kannada, Tamil, ~4.6MB total, OFL license — into `api/assets/fonts/`. `_font(size, text)` now detects
the dominant script by Unicode range and selects that script's face, set to its heaviest named variable
instance ('Black', Pillow 12.3 supports `set_variation_by_name` on these). Verified live: real Telugu
glyphs render correctly, and the bolder face's extra width made round 72's fit-guard trigger MORE often
on the same test headline (6 words → 3 lines, was 2) — correctly, not a regression: the thin default was
giving false headroom a genuinely bold face doesn't have.

Second ask, mid-turn: "there should be a button below each of the departments or before rendering... to
input location, character, pack shot." Investigated video's actual reference pipeline and found the
exact same gap round 70/71 fixed for POSM, one layer deeper: `/cast-reference` (the "Lock location and
cast" step every single frame is gated on) was **pure text-to-image, always** — a signed-off cast/actor
photo or location plate sat completely unread even when one existed, because there was no id parameter
to send one. `library.shot_references()` only had explicit-override for `pack_id`; `cast`/`plate` always
silently took "most recently signed off" with no way to name a specific one when a film has more than
one cast take or more than one location on file. Library check found this isn't hypothetical: exactly
one signed-off cast item exists, two signed-off packs, and **zero** plates — location had no real
reference material and no way to add one before this round.

Fixed: `library.shot_references()` gained `cast_id`/`plate_id`, mirroring `pack_id` exactly.
`/cast-reference` rewritten to try image-to-image (via the same `gemini.image_from_reference`/
`creative.image_from_reference` path POSM and `/scene-still` already use) when a `cast_id`/`plate_id`
resolves to a real signed-off item, falling back to the original pure-text render when neither is given
— nobody with nothing uploaded yet is blocked. `/scene-still` threads the same two ids through so a
later per-scene override is possible (not wired to the frontend yet — scope was the lock step, the one
thing gating every frame). Frontend: new "Real references (optional)" panel added to the Scripting
screen, directly above "Lock location and cast" — three pickers (cast/actor, location plate, pack),
each a real `/library` dropdown + inline upload-and-sign-off, same `posmAssetOptions`/`pickPosmAsset`/
`uploadPosmAsset` pattern POSM's own panel already proved, reimplemented as `videoAssetOptions`/
`pickVideoAsset`/`uploadVideoAsset` rather than coupled to `posm()` state. Pack choice also threads into
`generateFrame`'s existing `include_pack` toggle as an explicit `pack_id`, closing the same "toggle says
yes/no but never which one" gap `pack_id` already closed for POSM.

Verified live end-to-end on `studio-verify:8010`, not just structurally: wrote a full script, saw the
panel render with the REAL library contents (the one signed-off cast, "nothing signed off yet" for
plate, both real packs listed), picked the cast option, clicked "Lock location and cast", and confirmed
via the network response — `{"from_reference":true,"cast_used":true}` — and the actual generated image
(a real mustard-kurta portrait matching the reference, not hallucinated) that the real photo was used
end-to-end, not just accepted and ignored.

**Why:** the user has now caught this exact "backend capable, no input to reach it" pattern three times
this session (POSM pack picker round 70/71, this round's cast-reference). Check every reference-pulling
route for an explicit-id override before assuming "most recently signed off" is good enough, the moment
more than one item of a kind could plausibly exist. Related: [[design-asks-need-exact-files-and-instructions]],
[[browser-verification-available]].

## Round 74 (2 Sep 2026) — same turn's live test found the real, deeper ask: use a Studio Shot AS the
Key Visual hero, not just reference it

User tested round 72/73 live and reported three things in one message: (1) the headline-fit refusal
correctly fired but looked alarming shown inline under a live-looking tile — actually working as
designed, not a bug; (2) the /posm-image hero itself was absurd — a schoolgirl "walking home from
school" while simultaneously holding a milk glass AND the pack, the model's own creative choice in that
route's `desc` (drafted by `producers.key_visual()`), not a code defect; (3) the real, actionable one —
"did not get an input field for choosing studio shot, it has taken nothing from location, cast and the
studio shot." Investigated and confirmed: Studio Shot (built round 65) and Key Visual (`/posm-image`)
had run as two completely disconnected lanes the entire session, despite the user saying more than once
that Studio Shot's own output was better. There was no way to actually USE an already-generated Studio
Shot as the hero — only to look at it separately.

Fixed by connecting them rather than building a third thing: `pm.heroFromShot` (a studio shot's URL, or
'' for the normal route). Each studio shot in the existing gallery gets a "Use as this route's hero"
button; `draftStudioShot` now records `packUsed` at creation (`!!(body.pack_id || body.product_id)`)
rather than parsing it back out of `refs_used`'s prose later. `produceAdaptations()` branches: with a
shot chosen, `/posm-image` is skipped entirely and `heroD` is built directly from the shot (carrying its
real `pack_used`, so `/posm-assemble`'s existing `skip_pack` logic still fires correctly and no redundant
corner card gets added). A banner states plainly what's happening ("This route's hero is the studio
shot marked below — /posm-image is skipped") with a one-click way back to the normal route.

Verified live end-to-end on `studio-verify:8010`, not structurally: developed real KV routes, picked
"Product as hero," generated a Studio Shot ("a glass of milk beside the pack with a gentle milk splash"),
marked it as the hero, rendered Poster A3 — confirmed via the network log that `/posm-image` genuinely
did not fire (`posm-adapt` → `posm-assemble` directly) — and the resulting piece is a real, coherent,
well-composed Key Visual: the actual studio shot (real pack, real splash, a believable kitchen scene),
a bold Noto Sans headline that fit cleanly, the real logo, no assembly failure. Night-and-day versus the
hallucinated schoolgirl render from the same session that started this round.

**Why:** the user compared Studio Shot to Key Visual output quality unprompted, more than once, across
this whole session — that repetition was the signal this needed connecting, not two parallel features
each doing half the job. When two features in this app produce comparable output from the same
underlying assets, check whether the better one can simply feed the other before building anything new.
Related: [[browser-verification-available]], [[design-asks-need-exact-files-and-instructions]].

## Round 75 (2–3 Sep 2026) — the compositor rebuilt to the skill's nine-layer stack; SEVEN defects, one
of them a competitor's brand on the artwork

User asked for web research on how a senior AD builds POSM, then compositor changes. The research
answer contradicted both the web consensus AND the user's own suggested fix, and `posm_skill/SKILL.md`
says why. Web sources (Smashing, learnui.design) recommend a **scrim** — translucent gradient behind
type — which is also what the user proposed (vignette / contrasting colour). The skill explicitly
refuses it: *"Any technique that drops a translucent band over a full-bleed image to make room for a
headline is a symptom of building the wrong thing... A line dropped onto a full-bleed image inside a
translucent slab is not a layout; it is a subtitle."* Backed by 13 real Indian FMCG pieces in
`references/exhibits/`, nine built as flat-colour field + masked cut-outs; layer 1 is "Flat brand
colour. **Never a photograph.**" So the fix was structural, not a contrast treatment. **Told the user
their suggested fix was wrong and why — they took it.**

Seven defects found and fixed:
1. **White keyed to transparent** — `_key_white_to_alpha` ran on every hero; correct for a cut-out on
   white, catastrophic for a scene photo where white is real (milk, splash, a white label). Now gated by
   `hero_is_cutout`, AND rewritten to flood-fill **only border-connected** white, so interior white
   survives everywhere. That second half also fixed the logo rendering as a white box with its wordmark
   eaten out — visible on every piece the module had ever made.
2. **Studio shot kept adding a model + backdrop (5 user iterations)** — `mode:'scene'` injected
   `_IMG_STYLES['real']`, which literally ends "…dawn dairy-farm setting **with real people**". The
   user's "no human, no backdrop" was fighting the style string. Replaced with setting-free registers
   plus an explicit closed-frame clause. Same correction `/posm-image` already carried in comments.
3. **Route says child, model drew a mother** — the whole route `desc` was passed as a prompt, including
   "Left out: the breakfast table, **the mother**". Image models don't negate. `producers.key_visual()`
   now returns a positive-only `subject` (plus `line_emphasis`), and `hero_subject()` strips negative
   clauses defensively for older routes.
4. **Location ignored the route** — same bug; `desc` saying "no scene, just the object" was fed to a
   backdrop generator, which made a street. Location now uses the typed brief only; a route describes
   the hero, never the place.
5. **A COMPETITOR'S BRAND on the artwork** — caught live mid-verification, the worst defect of the
   session: subject "…standing beside a carton of milk" returned a child next to an **Amul** pack, a
   competitor named in Heritage's own profile. Fixed three ways: the producers prompt forbids naming
   packaging in `subject`; `hero_subject()` strips packaging clauses via `posm._PACK_WORDS`; and a
   shared `_NO_PACKAGING` clause is appended to every generation route with no real pack reference
   attached. The pack is ALWAYS composited from the library.
6. **Photoshoot angles unusable** — rendered but nothing could select one as the piece's hero. Added
   "Use as hero", and `pickHeroShot(url, isCutout, hasPack)` now records which KIND of image it is so
   the compositor keys (or doesn't) correctly.
7. **Headline not art** — white-on-bright-sky every time, because `field_rgb` was hardcoded
   `(128,128,128)` when a backdrop existed and mid-grey scores 0.502 against a `> 0.55` test, so the
   light colour won unconditionally. Now measured off the composited canvas (`_avg_rgb`). Plus
   multi-weight setting (skill: "**Never one uniform size**") and a device (rule/highlight box) — the
   skill's own checklist lists "a headline floating alone on a field" as a defect.

**Layers built:** the compositor implemented ~5 of 9. Added field division (hard split — a backdrop
photo is now a bounded panel, never full-bleed and never hosting type), field graphics (glow behind the
hero), type devices, base band, and mandatories. Mandatories are only printed when real strings are
supplied — `brandprofile.mandatories` holds a CHECKLIST ("FSSAI mark"), not printable copy, and
typesetting that verbatim would be the "every word is supplied, never generated" failure; the route now
returns `mandatories_outstanding` instead. Field colour prefers `brandprofile.palette` hex and reports
`field_source` honestly when falling back (this brand has colour NAMES but no hex on file).

**One regression I introduced and caught in the same pass:** reserving the base band shrank the type
zone while multi-weight grew the text, so "Ahead by breakfast" — three words — started refusing on A3.
Root cause was ordering: the hero took a fixed 70% and type squeezed into the remainder. Reversed it —
the type zone is reserved first from reading distance, the hero is the layer that flexes. Verified short
lines fit, genuinely long ones still refuse.

Verified live throughout, not structurally: real renders inspected by eye at every step; the final piece
is a proper POS layout (flat Heritage-green field, bounded photo panel, real pack cut-out, multi-weight
underlined headline, cornered logo, base band with tagline + FSSAI). `checkfe.py` clean (871/871 sc-if,
344/344 sc-for), backend compiles, LF preserved.

**Why:** CLAUDE.md's own advice paid off exactly as written — "check whether the code is actually
enforcing what the matching SKILL.md already specifies; more than once the gap was an unenforced rule
already written down." Six of these seven were rules the repo had already written and never enforced.
Read the skill BEFORE proposing craft changes here, and be willing to contradict both the web and the
user when the cited exhibits disagree. Related: [[prefer-cited-estimates-over-blocking]],
[[browser-verification-available]], [[check-skill-md-before-craft-changes]].

## Round 76 (3 Sep 2026) — the five gaps against a real agency KV process, all built

User found an article on how agencies develop a Key Visual and asked what was missing vs. our POS
skill. Mapped its five phases against `SKILL.md` + all five `references/*.md` + the code. **Framing
that matters: the article describes a PHOTOGRAPHIC-COMPOSITE KV process** (its Phase 4 is entirely
Photoshop masking, perspective matching, light grading) — our skill deliberately rejects that as the
*default* for Indian FMCG POS ("almost none of these are photographs"), so Phase 4's craft belongs to
the minority photographic build, not the main line. Said so rather than treating the article as the
standard. Then built all five gaps the user asked for:

1. **Print-ready output** — the biggest one. `canvas_px` said it outright: "a preview render, not a
   print file". Added `dpi` mode (real trim size from the format's own mm: A3 → 3508×4961 at 300dpi),
   `_with_bleed_and_marks` (applies `posm.bleed_safe`'s millimetres, which had been computed since it
   was written with nothing ever using them for a file — 3mm bleed flooded with the field colour, plus
   3mm corner crop marks outside it), CMYK TIFF export, and `POST /posm-print`. ~25MB, ~5s. CMYK is
   Pillow's un-profiled conversion and the response SAYS so — usable to quote and proof from, not a
   colour-managed separation. A format with no `mm` on file (`shelf-branding`, `wall-paint`) refuses
   rather than inventing a sheet size, consistent with "refuse rather than guess".
2. **Surfaced the discarded findings** — `/posm-adapt` calls `posm.kit()`, which computes the crop
   gate, occlusion warnings, two-sided-piece warnings and the short-line block; the frontend read
   `formats` and `unknown` and threw `findings` away entirely. Now rendered in STEP 3, severity-coded.
   The frontend also now sends `hero`, without which the crop gate had no opinion to give.
3. **Contact shadow** — the skill's layer 3 is "the subject, masked out of its background, hard-edged,
   **shadowed to seat it**"; no shadow was ever drawn, so every hero floated. Soft ellipse under the
   subject's real alpha bbox (not its image box, which is mostly transparent). Cut-outs only — a scene
   panel carries its own ground.
4. **Scamps** — `keyvisual.scamp()`/`scamp_set()` + `POST /posm-scamps`. Block layouts, pure Pillow,
   ~10ms for all five. The step this product skipped: comparing two layouts previously cost two image
   generations, so nobody compared. Picking a scamp writes the same `layoutOf` the dropdown does.
5. **Mood board, done the only honest way** — `palette_from()` measures the brand's real colours off
   its signed-off logo/pack by quantising (drops near-white, near-black and anything with no hue), and
   `POST /posm-palette` returns them as candidates. This closes a gap that had been silently degrading
   every render: `brandprofile.colours` holds NAMES ("Deep Forest", "Cream", "Ghee gold") and `palette`
   — the field that holds hexes — is empty, so every piece fell back to a neutral stand-in. Measured
   correctly: `#2D9A31` (Heritage green, 18.2% of the logo) and `#E63338` (the logo red). The panel
   also prints the declared-but-hexless names so the gap is visible. Nothing is written back to the
   profile — `library.py`'s rule is that facts enter by a person's action, never by inference.
   Composition: hero now sits off-centre (0.38 bias) when it shares the frame with the pack card, so
   the two make a diagonal instead of a stack; centred when alone.

**Bug found and fixed during verification:** the white-key flood fill used a fixed tolerance
(`threshold - 24`), generous enough for a JPEG-softened plate — and that generosity ate translucent
subjects, flood-filling straight through a glass of milk (~235) and leaving visibly chewed edges on a
real piece. Now the cut is measured from the image's own border (median of edge pixels, robust to a
subject touching an edge) and sits just under the actual plate brightness. Verified on the hard case:
white pack, white milk, glass and a white clock face all survive; only the backdrop goes.

Verified live end-to-end through the UI, not structurally: palette panel reads real swatches and names
the declared-but-hexless colours; picking a swatch sets the field and redraws scamps; scamps render in
the brand green with the active layout ticked; findings appear in STEP 3 (incl. the crop gate firing on
an `occasion` hero across a 12:1 strip and a wobbler); print export returns
`3508×4961px · 300dpi · CMYK · 3mm bleed + crop marks` with a working download link. `checkfe.py` clean
(880/880 sc-if, 348/348 sc-for), backend compiles, LF preserved.

**Why:** the user is now bringing outside process references and asking for a gap analysis rather than
a fix — answer by reading the repo's own skill fully first, state where the reference does NOT apply to
this medium, and only then build. Related: [[check-skill-md-before-craft-changes]],
[[browser-verification-available]].

## Round 77 (3 Sep 2026) — the craft layer: matte, composition, shadow, type, and an automated squint

User said the green piece was "still far from where I'd like it" and asked for thorough web research,
thinking like a senior AD, before building. Researched six angles (edge/matte, optical vs mathematical
centre, display tracking, contact shadow, Gestalt/squint, WCAG contrast) and then measured the actual
failing piece rather than theorising — which found the decisive cause in one number.

**The measurement that mattered:** the hero image was 1792×2400 but the keyed subject occupied only
49% of the height and 43% of the AREA. `assemble()` fitted the IMAGE to the hero box, so the subject
rendered at roughly half its allocated size and the rest of the poster was void. Mundane, decisive, and
invisible without measuring. Fixed by cropping to the alpha bbox before fitting.

**The upstream insight — stop cutting out on white.** Both matte failures had one shared cause: we
asked for subjects isolated on WHITE then keyed white. Half a dairy brand's subjects ARE white (milk,
glass, splash, white pack panel, school shirt), so the key ate them; and white contamination on every
anti-aliased edge showed as a pale halo on the green field. Chroma keying exists precisely because a
backdrop the subject does not contain makes the matte solvable. `posm.CUTOUT_BACKDROP = "#808080"` now,
in both `cutout_prompt` and `/studio-shot`. Verified with a real generation: pack, milk and glass all
survive with clean edges and no halo — dramatically better than any white-plate cutout.

Built, in order:
1. **Mid-grey backdrop** (above), plus an anti-reflection clause after a real render came back with a
   glossy mirrored surface whose broken tones survived the key as grey debris under the subject.
2. **`_key_white_to_alpha` → `_key_backdrop_to_alpha`** — the plate colour is now MEASURED from the
   frame border (median per channel), so the same code keys grey, legacy white, or a chroma green.
   Tolerance adapts to the plate's own noise (90th-percentile border deviation): a fixed ±26 ate the
   white ring inside the Heritage logo, because at that width the ring counted as plate and the fill
   reached it through gaps in the swoosh.
3. **Defringe + decontaminate** — contract the matte 1px to drop the contaminated ring, then solve the
   backdrop colour out of the remaining partial pixels (`F = (C − (1−a)·B)/a`, Adobe's "Remove White
   Matte"), done in `ImageMath` since there is no numpy. Note: Pillow 10.3 renamed `ImageMath.eval` to
   `unsafe_eval` — bound via `getattr` rather than pinning.
4. **Composition** — fit the subject not the file; pack sized to the skill's own "15–30% of height"
   (was 16% of WIDTH) and now OVERLAPPING the hero, since proximity is the Gestalt mechanism that makes
   two shapes read as one group; optical centre (46%, not 50%) for both hero and type block. The pack
   is a real cut-out now, not a white card — the card only existed because keying couldn't be trusted.
5. **Two-part shadow** — ambient occlusion (dark, tight, sharp, at the contact line — what actually
   grounds an object) plus a softer directional cast shadow, from a single module-level `LIGHT_DIR` so
   a kit of eleven pieces shares one light. One medium-soft blob was neither of the two.
6. **Type** — negative tracking scaled to size (display type at 110–170px reads loose at default
   spacing), 1.15 leading, and `_draw_tracked` positions each glyph at the KERNED prefix advance so
   tracking is applied without discarding the font's kern pairs.
7. **WCAG contrast, as a floor not a chooser** — `contrast_ratio()` implements the real gamma-corrected
   formula. Important judgement call: picking purely by highest ratio set the dairy poster in charcoal
   (4.5:1) over knockout white (3.6:1) and lost the category's look while both cleared the 3:1 floor.
   So the CONVENTION decides (knockout on a mid-to-dark field, dark ink on light) and the ratio
   VERIFIES it; only a genuine sub-3:1 failure switches ink, and then the field is reported as the
   problem. Measurably better: white knockout also improved squint dominance from ×1.2 to ×1.55.
8. **Automated squint test** — `squint()` shrinks to 48px, blurs, and measures contrast index (mush
   detection) plus per-zone visual mass (is there a lead, or are hero and type competing?). The skill
   has asked a human to do this since it was written. Reported via a new `report` dict on `assemble()`,
   surfaced per piece in the UI as "The craft read". **Advisory, never enforced** — a range array is
   *supposed* to have no single dominant element, and the module doesn't get to overrule the route.

**Wrote the six missing rules back into `posm_skill/references/key-visual.md`** as a new "Craft" section
plus four new checklist items, so the skill stops trailing the code — the user explicitly asked for this.

Verified live throughout: real grey-backdrop generation keyed clean; final piece passes contrast
(3.81:1) and squint (hero leads ×1.55); craft report flows through `/posm-assemble`; UI renders with no
console errors. `checkfe.py` clean (883/883 sc-if, 349/349 sc-for), backend compiles, LF preserved.

**Why:** when output is "structurally right but still wrong", measure the artefact before theorising —
one number (43% area) explained more than all six research threads. And prefer the upstream fix: three
downstream matte patches were unnecessary once the backdrop stopped being white. Related:
[[check-skill-md-before-craft-changes]], [[browser-verification-available]].

## Round 78 (3 Sep 2026) — user's worst output yet; three defects, then vector artwork + drawn scamps

User sent four screenshots (route → scamp → studio shot → final piece) and was rightly angry: the
final poster was a cream field with the headline crammed at top and the studio shot's **grey backdrop
sitting in the middle as a rectangle**. Three defects, all mine:

1. **Hero not keyed.** I classified heroes by how they were GENERATED — studio shots are made in
   `mode:'scene'`, so the frontend flagged them `isCutout=false` and the compositor never keyed them.
   The user's shot was a pack on a seamless grey sweep, so the sweep landed on the artwork. Fixed with
   `keyvisual.looks_like_cutout()`: sample the frame border, key if ≥88% of it is one flat colour.
   **Measure the picture, never trust the provenance label.** Verified: studio sweep → keyed; real
   kitchen scene → not; child-in-a-room → not.
2. **Cream field.** No palette had been picked, so it fell back to a neutral. For a brand whose field
   is Deep Forest that is not a safe default, it is wrong artwork. `/posm-assemble` now measures the
   dominant colour off the signed-off logo/pack when no palette is declared (`#2D9A31`) and says in
   `field_source` that it was measured rather than declared.
3. **The route was never used again — the user's own bigger point.** Their route read "a mother,
   already dressed and calm before dawn, mid-motion setting a filled glass down" and the piece had no
   person in it, because the Studio Shot box was free text with no link to the route. Now: picking a
   route pre-fills the studio brief from its `subject`; the route's hero brief stays visible above the
   box while shooting; and if the route's hero is person-led (`person-in-benefit`, `endorser-with-pack`,
   `occasion`) while the chosen hero shot carries no cast reference, it says so instead of shipping.

**A dead fallback found while verifying** (worth remembering — it explains months of "both providers
refused"): the fal text-to-image endpoint was `fal-ai/imagen4/ultra` at all SEVEN call sites, and fal
answers `Application "imagen4" not found`. The real path carries `/preview/`. Invisible because the
fallback only runs when Google has already failed — and the user's Google credits were depleted at
exactly this moment, which is how it finally surfaced. Replaced with `creative.text_to_image()`, an
ordered CHAIN (`imagen4/preview/ultra` → `nano-banana-2` → `flux-2`) that returns which endpoint served
the image, so a provider rename degrades instead of silently removing the safety net.

Then the three things the user asked for:
- **`posm.RENDER_INPUTS`** — all 18 inputs to a piece declared in one place (Strategy / Route / Ground
  truth / Design / Format), each with its legitimate `source` and what actually happens when missing.
  Served by `GET /posm-input-spec`. The list exists because "was this input used?" was unanswerable.
- **Drawn scamps** — `posm.scamp_prompt()` + upgraded `/posm-scamps`: a pencil sketch of the ROUTE'S
  OWN SCENE with the headline hand-lettered into the type zone, one per layout. The user sent a
  reference pencil drawing to make the point: boxes are honest about geometry and useless for the
  decision they serve, because whether the picture and the words hold together cannot be judged from
  two rectangles. Hand lettering is deliberate — nobody mistakes it for final typography. Block
  diagrams stay as the instant/no-key fallback.
- **`keyvisual.artwork_svg()` + `/posm-artwork`** — the piece as an EDITABLE VECTOR document: named
  layers matching the nine-layer stack (Illustrator reads `data-name`), live `<text>` that can be
  retyped and rekerned, photographs embedded and masked inside vector frames, geometry in real
  millimetres at trim size, bleed/safe guides on a hideable layer. **The PNG is now a preview of this,
  not the deliverable** — a key visual is a master adapted eleven times, and if adapting means
  regenerating, the kit cannot stay coherent. Verified in-browser: A3 viewBox in mm, all layers
  present, live text laid out with real weight hierarchy ("Ahead" 148mm wide vs "by breakfast" at
  42mm), 2 embedded masked images.

Verified live throughout; `checkfe.py` clean (887/887 sc-if), backend compiles, LF preserved.

**Why:** I had verified every craft change against pack-only heroes, which is exactly the case where a
person/route mismatch is invisible — that is why three of these survived four rounds of my own testing.
**Test the case the user's own route describes, not the convenient one.** Related:
[[measure-the-artefact-before-theorising]], [[check-skill-md-before-craft-changes]].

## Pending — provider-failure notification (queued, not started; user said "next session after 3:10pm")

User asked what happens on a Google credits refill, and separately said generation failures should
surface as a real notification instead of degrading silently. Investigated (no code changed) and found:

- **Refill needs no reset.** `gemini.py`'s only sticky failure cache (`_QUOTA_SPENT`, 15min cooldown,
  `gemini.py:58-72`) is scoped to VIDEO (Veo) only — confirmed `image()`/`image_from_reference()` never
  touch it. The next image call after refilling just works.
- **Every failure reason collapses to `None`.** `gemini.py:165-179` (`_interaction`) treats a 429
  credits-depleted, a content rejection, and a network timeout identically — one stderr line, `None`
  returned. No caller can tell the user WHY.
- **13 error messages point at `render-log.txt`, which no launcher ever creates.** Grepped for it —
  nothing redirects stderr to a file by that name anywhere in the repo. Every one of those messages has
  been pointing at a phantom file.
- **Round 78's own `/posm-scamps` is the concrete repro.** It correctly marks each fallback scamp
  `drawn:false` in the response (`main.py:5938-5947`), but `loadScamps` in the frontend never reads that
  flag — only checks `!r.ok`. Five failed generations render as five silent grey boxes indistinguishable
  from a real scamp. This is what the user would hit again right now if credits ran out mid-session.
- **No persistent status surface anywhere.** `/health` only checks whether an env var is SET, not
  whether the account behind it has money.

**Agreed 5-point plan, not yet built:**
1. Classify the failure at the source (`_interaction` already has status+body — return a reason:
   `credits_depleted` / `rate_limited` / `no_key` / `content_policy` / `transient`).
2. One in-memory place holding current provider status, cleared the moment a call next succeeds.
3. A real status surface (extend `/health` or add one) so the frontend shows a visible banner on
   generation screens, not a toast that only fires if the right action happens to trigger it.
4. Never let a degraded fallback look like success — read the `drawn:false` flag already emitted and
   say so on the tile; apply the same discipline anywhere else a route silently substitutes a lesser
   artifact.
5. Fix or remove the render-log.txt references.

**Why:** the user paused before building ("think, don't build anything yet") — this is analysis awaiting
a go-ahead, not a fix in progress. Pick up here next session rather than re-investigating.
Related: [[studio-work-inventory]].

## Pending — round-78 features tested live; 5 findings, one likely root-caused (queued, session ended on
token limit before any fix was made — "look at it when you come back")

User ran the full new flow (sketch → cast → studio shot → location → final render) with a real route
("a child walking to school" / line "Har roz shakti") and sent five screenshots. Nothing below has been
fixed yet — investigate and verify before touching code, per this session's own discipline.

**1. Sketches need in-place editing.** The 5 drawn scamps (pic 1) worked — genuinely good pencil
drawings of the route's own scene, hand-lettered headline, all five laid out for comparison. Ask: a way
to refine/iterate a specific sketch (not just accept one of five fixed outputs) so composition gets
settled here, before it becomes expensive to change later.

**2. The chosen sketch should drive every other department.** Cast, location and studio shot are each
drafted independently from route text; none of them is conditioned on the SPECIFIC scamp the user
picked. Ask: once a scamp is chosen, it becomes the visual reference for cast/location/studio-shot
generation, not just another independent draw from the same route text.

**3. Two real cast bugs, not a UX ask:**
   - `draftPosmCast`'s AI draft returned an adult man in a plaid shirt for a route whose hero is a
     CHILD walking to school (pic 2) — a "basic miss" per the user. Worth checking whether
     `draftPosmCast` ever picked up the `kv.subject` fix (`hero_subject()`, round 78) the way
     `heroBody`/`studioAction` did, or whether it's still drafting from something too generic to know
     the hero is a child.
   - **Photoshoot angles regenerate a DIFFERENT person each time** instead of the same locked cast at a
     different angle — `draftModelAngle` sends `cast_id:pm.castChoice` to `/studio-shot` in `cutout`
     mode, which should hold identity via the reference image; user says each angle click drew a
     different model entirely. Needs a live repro with logging on what `refs`/`roles` actually reach
     `image_from_reference` — possibly the reference isn't surviving the round trip, or the model is
     just not respecting it at `cutout` mode/this size.

**4. Location should also seed from the route.** Currently `draftPosmLocation` deliberately does NOT
fall back to the route (a round-78 change, reasoning: "the route describes the hero, not the place").
User is now saying that reasoning was too strict — they want location pre-filled/drawn from the
selected route (and per #2, ideally from the chosen sketch) rather than always starting from an empty
typed brief. **This reverses part of round 78's `draftPosmLocation` change — revisit that reasoning,
don't just re-add the old fallback blindly.**

**5. The final render silently discarded the chosen studio shot — likely root cause identified, NOT yet
verified.** Pic 3 (studio shot: the single chosen child + pack + glass, neutral backdrop, marked
"Using as this route's hero") was praised as the actually-correct composition — user's stated
expectation for the final render was just "add pic 4's street background behind it and set the
headline." What pic 5 actually shows is a completely different scene: a 4-person family group (not
the girl from pic 3 at all) against a street, with hand-drawn-looking lowercase headline styling that
doesn't match this session's Noto Sans Black compositor treatment at all.

**Hypothesis, code-located but not confirmed:** `produceAdaptations`' `sceneLane` branch
(`sceneLane = (kv.hero || '') === 'occasion'`) calls `/posm-scene` — the OTHER lane, which bakes hero +
environment + headline into ONE fresh generation and never reads `p.heroFromShot` at all. If this
route's hero type is `occasion` (plausible for "a child walking to school" — a relationship/moment, the
one type `posm.HERO_TYPES` documents as needing `/posm-scene`), then picking a studio shot as hero
(round 74's whole feature) is silently ignored for this route: the scene lane always regenerates
everything from scratch, including a mismatched cast and AI-hand-lettered type, regardless of what was
built in pic 2/pic 3. This would explain every symptom in pic 5 at once — wrong people, wrong type
treatment, background present (scene lane generates its own).

**If confirmed, the fix is likely:** when `p.heroFromShot` is set, skip the scene-lane branch entirely
and route through `/posm-assemble` instead (composite the chosen hero + the chosen location backdrop +
real set type), even for `occasion`-type routes — because "use this shot as the hero" is an explicit
statement that the hero question is already answered; the scene lane exists for when it isn't. Verify
this route's actual `hero` value before assuming, and check whether `/posm-assemble` can take a
`backdrop_url` alongside a hero that already has its own micro-background, or whether that needs its
own small design decision (hero cut-out further keyed against the grey backdrop, THEN composited over
the location plate — should already work if `hero_is_cutout` detection classifies the studio shot as a
cutout, which it should per `looks_like_cutout()`).

**Why:** the user tested the full round-74/77/78 pipeline together for the first time and found it
does mostly work (sketches, studio shot) but breaks at the exact seam between "a hero I already chose"
and "the occasion lane that was built before that choice existed" — a real integration gap between two
features built in different rounds, not a fresh defect in either one alone. Related:
[[test-the-case-the-route-describes]], [[studio-work-inventory]].

## Pending — the POSM screen's target flow, proposed by the user (queued, nothing built — session ended
on token limit immediately after this)

User's own diagnosis of finding #5 above: the render has no explicit, user-controlled list of what
goes INTO a piece — it infers/guesses (hero source, whether to skip pack, which lane to use), and that
guessing is why pieces silently diverge from what was actually built up on screen. Their fix is
structural, not a patch: **a linear, interlinked sequence where each step's OUTPUT is the next step's
INPUT, ending in an explicit checklist the render call is built from — never inferred.**

Proposed sequence, verbatim intent (this is a SPEC for next session, not yet designed against the real
code):

1. Idea platform (existing, upstream)
2. Develop route(s)
3. Edit a selected route — before locking it in
4. Select a route — locks it
5. Develop sketch — scamps generated FROM the locked route (round 78's drawn scamps)
6. Select the sketch — pick one of the set
7. Edit the selected sketch — round-78-message ask #1, not yet built: refine the CHOSEN scamp rather
   than only regenerating a fresh batch of five
8. Select assets for the piece — pack shot, logo (ground truth, ties to `posm.RENDER_INPUTS`)
9. Generate a hero/characters — driven by the selected route AND the selected sketch (not route text
   alone — the sketch is a stronger, chosen-and-approved spec of what the hero actually looks like)
10. Select a hero/characters — from what step 9 produced
11. Select an angle — photoshoot angle, from the SAME locked identity (fixes finding #3's angle-drift
    bug by construction: angle selection is downstream of a single chosen hero, not a fresh draw)
12. Generate a location — also driven by route + sketch (fixes finding #4 the same way as step 9)
13. Edit a location — refine the generated backdrop
14. Generate a studio shot — combine hero + pack + location per the sketch's own composition (this
    step already works well per the user — pic 3 in the prior message)
15. **The checklist.** Explicitly select what goes INTO the key visual — hero, pack, logo, location,
    headline, support line, mandatories, etc. — as a real list of on/off inclusions the person sets,
    not something the renderer decides by hero-type branching or silent fallback. THIS is named as the
    fix for finding #5: had `heroFromShot` been a checklist item rather than a flag one code path
    reads and another (`sceneLane`) ignores, the studio shot could not have been silently dropped.
16. Select a layout — informed by the sketch already chosen at step 6/7
17. Choose a treatment (style register)
18. Render — must derive itself from the route AND the sketch, incorporate every checklist item from
    step 15 explicitly (no inference), and produce the vector/layered "Illustrator-level" artwork
    (round 78's `artwork_svg`/`/posm-artwork`) as the actual output, not a flattened PNG.

**Also requested:** on the POSM screen's opening state (where the prompt guide currently sits), add a
direct-brief shortcut — type a full POSM brief and run the whole flow from that text alone, skipping
Idea Platform / Strategy / Plan entirely for cases where that upstream stack doesn't exist yet or isn't
wanted for a one-off piece.

**Not yet done:** no design or code work against this spec. Next session: map these 18 steps against
what already exists (routes, scamps, assets panel, cast/angle, location, studio shot, `RENDER_INPUTS`,
`artwork_svg` all exist in some form already) versus what's net-new (step-gating/linking the screen so
each step is genuinely unlocked by the previous one's output, the checklist UI itself, the sketch-edit
capability, the direct-brief entry point) before writing any code — this is a real information
architecture change to the POSM screen, not a small patch.

**Why:** treat this as the user's own root-cause fix for finding #5, not a separate feature request —
build the checklist-driven flow before attempting further point-fixes to the inference logic it's meant
to replace. Related: [[test-the-case-the-route-describes]], [[studio-work-inventory]].

## Round 79 (3 Sep 2026) — step 15 of the user's flow built and wired: an explicit checklist replaces
render-time inference; the sceneLane bug confirmed AND a second bypass found

"Please start." First confirmed the round-78 hypothesis by reading the actual code (not re-guessing):
`sceneLane = (kv.hero || '') === 'occasion'` at the top of the per-format render loop NEVER checked
`p.heroFromShot` — an `occasion` route always called `/posm-scene` fresh regardless of any hero the
user had explicitly locked. **Found a second, independent bypass in the same read**: even in the
non-scene branch, the band→angle auto-mapping (`BAND_ANGLE`) would silently substitute a DIFFERENT
photoshoot-angle image for a specific format tile whenever that format's re-flow band matched an
available angle slot — regardless of whether the user had explicitly picked a different hero via "Use
as hero". This second bug is the more likely explanation for the "photoshoot angle" mislabel in the
user's pic 5: `heroD.provider` is set ONCE from the global `heroFromShotCutout` flag, so if the
person's actual last "Use as hero" click landed on an angle card (even just testing it) rather than the
studio shot, that silently became the locked choice — a single implicit "last click wins" flag with no
confirmation point, exactly the class of bug the user's own proposed checklist step is meant to close.

**Fixed both bypasses**, each gated on `!p.heroFromShot` — an explicit hero lock now wins over both the
occasion-lane branch and the per-format angle substitution, for every hero type, unconditionally.

**Built the checklist** (step 15 of the user's 18-step flow) as a real, always-visible panel — "What
goes into this piece" — sitting between the assets panel and STEP 2/Formats, gated on a route being
chosen:
- **Hero**: current choice always summarised in words ("Not chosen — a fresh hero will be generated…"
  or the specific studio-shot/angle label), with EVERY available studio shot and photoshoot angle shown
  as a single unified thumbnail strip to pick from — replacing the scattered "Use as hero" buttons on
  separate cards as the thing that actually decides render behaviour. A "Clear" link returns to fresh
  generation explicitly.
- **Pack card**: three-way `kvIncludePack` ('auto'/'yes'/'no', cycled by one button) — 'auto' preserves
  the exact previous inference (skip only when the shared hero already carries the pack), 'yes'/'no'
  are the person overriding it outright. Replaces the render loop reading `heroD.pack_used` as the only
  signal.
- **Location background**: `kvIncludeLocation`, a real checkbox that DEFAULTS OFF even when a location
  has been drafted — was previously automatic the instant `p.locDraft.url` existed, with no way to
  compare a flat field against the backdrop once drafted. A draft is now a candidate, not a commitment.
- **Logo**: shown for visibility (name of the currently picked item); still set in the Assets panel
  above, not duplicated here.

Render-body construction in `produceAdaptations` now reads all three directly (`p.kvIncludePack`,
`p.kvIncludeLocation`) instead of the mix of `heroD.pack_used` inference and "if a draft exists, use
it" that caused finding #5.

**Two template-syntax mistakes caught before verification, same class as earlier rounds**: an inline
ternary inside `{{ }}` (`border:2px solid {{ x }} ? 'a' : 'b'`) doesn't work in this templating engine —
precomputed the colour in JS instead, per the standing lesson from round 74. Also removed a stray empty
`sc-if` left over from an abandoned else-branch attempt.

Verified live, not just structurally — this was the highest-stakes change of the session, so proved the
full chain rather than trusting checkfe.py alone: patched `window.fetch` in the live page to capture
the actual `/posm-assemble` request body. Cycled Pack to "Always include", rendered, and confirmed the
captured body has `pack_id` present and NO `skip_pack` — exactly what the checklist state should
produce — and the server's own response echoed `pack_used:true`. No console errors. `checkfe.py` clean
(891/891 sc-if, 350/350 sc-for), LF preserved.

**Not done this round** (from the 18-step spec): sketch-editing (step 7), sketch-as-reference for
cast/location generation (steps 9/12), the cast-draft/angle-identity bugs from the prior message
(finding #3), location auto-seeding from the route (finding #4), and the direct-brief shortcut. The
checklist was the highest-leverage single piece — it's what makes finding #5 structurally impossible to
repeat, and it's the anchor the rest of the flow's step-gating will attach to.

**Why:** two real bugs (occasion-lane bypass, band-angle bypass) both existed independently and both
matched the user's single symptom — resist stopping at the first plausible cause once one is found;
keep reading if the code has more than one place doing the same kind of thing. And when a fix is
"make this a checklist instead of an inference", prove it by capturing the actual outgoing request, not
by reading the code and asserting it's right. Related: [[test-the-case-the-route-describes]],
[[browser-verification-available]].

## Round 80 (2026-09-03) — the 9-point flow-gap build

User gave a word-by-word match of the built POSM pipeline against their proposed 18-step flow (Idea
platform → Develop Route → edit route → select → develop sketch → edit sketch → select assets →
generate hero/characters → select hero → select angle → generate location → edit location → studio
shot → checklist → layout → treatment → render, based on route+sketch, illustrator-level). Gaps found
and their priority: route editing (critical), sketch editing as a revision not a redraw (important),
hero/character prompt conditioning (critical — "we have seen misses on this before"), multi-candidate
hero selection (very critical), angle as a firm decision (important), studio-shot editing beyond
re-promoting, checklist completeness + a late layout step (both critical), sketch as the render's
locked layout ground truth an art director can tally back against (important), and — once all of this
existed — a direct-brief shortcut on the opening screen. User: "All needs to be done."

Built all nine, backend then frontend, verified live (not just endpoint tests — see
[[browser-verification-available]]):

- **Route editing**: new "What's in frame" field on the chosen route (`subjectOverride`, three-valued
  null/string like `line` already is). `effectivePosmSubject(kv)` is now the SINGLE place every
  downstream call reads from — cast draft, scamp subject, studio-shot pre-fill, the fresh-hero
  render — so a correction here actually reaches the render, not just the card that shows it.
- **Hero/character conditioning** (`posm.hero_type_brief`): `HERO_TYPES[hero_type]["what"]` — the
  actual casting instruction ("the consumer visibly carrying the result", "a known face... holds or
  presents the pack") — is now spliced into both `cutout_prompt` (`/posm-image`) and `/cast-reference`'s
  prompt. Before this, `hero_type` was resolved and gated on server-side but the words describing WHAT
  it means never reached the model — the actual root cause of the child/adult and identity misses.
- **Multi-candidate hero selection**: `/posm-image` and `/cast-reference` both take `n` (capped at 4)
  and return `images:[]` alongside the single `image_url`. Frontend: `castCandidates` (was `castDraft`,
  singular) — three drafts shown side by side, "Use #N" per candidate, not one draft silently
  overwritten by every "redo".
- **Sketch editing**: `/posm-scamps` takes `only` (regenerate ONE type_position) + `adjust` (an art
  director's note folded into `posm.scamp_prompt` as a revision clause) — splices one result back into
  the existing grid rather than redrawing the set. Verified live: 5 sketches drawn, all 5 carry their
  own "Change something…" + "Redraw this one" control.
- **Studio-shot editing**: `/studio-shot` takes `base_image_url` — the prior shot becomes one more
  locked reference ("keep this identical except what the note changes") instead of every "edit" meaning
  discard-and-redraft-from-text. Frontend: "Adjust the most recent shot" note, auto-replaces the hero if
  the adjusted shot was the one in use.
- **Checklist completeness**: support line and declared mandatories (`GET /posm-mandatories`, new route)
  are now real checklist inputs wired into `/posm-assemble`'s `ab` payload and `exportArtwork` — both
  were ALWAYS sent empty before this (`support_line:''`, `mandatories:[]`), which is why every render's
  `mandatories_outstanding` always listed everything declared as still missing regardless of the truth.
  Logo upgraded from a read-only name to a real include/exclude toggle.
- **Late layout step**: the same `setKvLayout`/`layoutOpts` control the route card already offered is
  now ALSO offered inside the checklist, right before Treatment — one state, two decision points, per
  the user's own sequencing (layout named as its own late step, not just an early one).
- **Sketch as locked layout ground truth**: `keyvisual.scamp()` now returns `type_pct` (the actual
  hero/type split fraction, e.g. 0.30) alongside the image, and `keyvisual.assemble()` takes the same
  `type_pct` and uses the identical formula — so a render's split is provably the one an art director
  approved on the sketch, not just visually similar. Also fixed a real drift bug found while unifying
  this: `scamp()`'s margin was 0.05, `assemble()`'s was 0.04 — same category of bug as the round-77
  scene/cutout misclassification, a "looks the same" formula that silently wasn't. Threaded through
  `/posm-assemble` and `/posm-print`; `/posm-artwork`'s separate SVG geometry path is NOT yet unified —
  flagged as a follow-up, not claimed done. Checklist now shows the locked sketch's thumbnail next to
  "Locked to this sketch's own split" once a scamp (not the plain dropdown) sets the layout — confirmed
  live.
- **Direct-brief shortcut**: the existing `kvBrief` override (already functional cold — `_exec_ctx`
  tolerates zero house/platform) reframed with a prominent callout when `posmNoStands` is true, inviting
  "skip Idea Platform, Strategy and Plan — describe the piece directly" instead of reading as a buried
  optional field.

**Live verification** (server restarted fresh, real browser session, not endpoint-only): picked a real
route → confirmed "What's in frame" renders and posm-mandatories fires; clicked Sketch the layout →
5 real drawn scamps returned, each carrying a working adjust control; picked a scamp → checklist's
"Locked to this sketch's own split" thumbnail appeared, confirming the type_pct/scampUrl plumbing works
end to end. Cast-candidate and studio-shot-adjust flows were verified by code review (identical
reference-passing pattern to the already-live-verified paths) rather than triggered live, for time —
named honestly rather than claimed as tested.

**Known follow-up, not built this round**: `/posm-artwork`'s vector SVG export has its own independent
type-zone geometry (`keyvisual.artwork_svg`) that was not unified with `scamp()`/`assemble()`'s
`type_pct` — the PNG comp and print export are provably WYSIWYG against the sketch now; the editable
artwork export is not yet. `/posm-artwork` silently ignores the `type_pct` the frontend now sends it.

## Round 81 (2026-09-03) — the studio-shot pivot (B, C, D, E)

Continuation of round 80's flow-gap work, after the user reached a bigger decision through discussion:
the Pillow compositor (`keyvisual.assemble()`'s layout geometry — flat field, hero box, pack corner
card) lost the user's trust after two days of refusals/mismatches, and the studio shot itself was
visibly working well including AI-baked headline text. Decision: studio shot becomes the KV generator;
elements get isolated from the approved shot and recomposed into new layouts via reference-conditioned
generation (not the compositor); real type goes back on at the end via a narrow, separate function.
Retired `/posm-image` (A3, already logged in round 80's continuation). Built the rest as phases B/C/D/E:

- **B — sketch as a real generation input**: `/studio-shot` and `/cast-reference` both take `sketch_url`
  now — the approved scamp, framed explicitly as "layout only, ignore the pencil/monochrome/paper
  texture" (a real risk named before building, since a reference image's visual register tends to leak
  into a generation otherwise). Assets (cast, studio shot, treatment) now gate behind the sketch step
  having actually run (`pm.scamps.length > 0`), not just a route being picked — "once we choose the
  sketch then the assets department comes in."
- **C — isolate elements**: not segmentation (this app can't cut a subject out of a real photo) — the
  same `base_image_url` reference mechanism from round 80's "Adjust this shot", pointed at `mode='cutout'`
  with an isolation-specific role text instead of an adjustment one. `/studio-shot` now tells apart three
  distinct jobs explicitly (`recompose` / isolate / adjust) rather than inferring intent, because a
  wrong-intent prompt is a real failure mode here.
- **D — regenerate new shapes**: `recompose=True` + `base_image_url` (master, style anchor) +
  `extra_refs` (the isolated elements, capped at 3 total references) composes banner/square shapes
  fresh, explicitly with no text yet (the scene-mode "no on-screen text" clause already in `/studio-shot`
  covers this for free). Iteration via the same per-shape note+redo pattern as adjust.
- **E — set the line, narrowly**: new `keyvisual.type_over_photo()` + `/posm-typeset` — reuses
  `assemble()`'s real type machinery verbatim (script-aware bold type, measured-contrast WCAG ink
  choice, the overflow refusal, the base band) but drops everything about layout geometry that assumed
  separately-composited layers. `produceAdaptations`'s per-tile render now branches on the format's own
  reflow band: near-band crops the master directly through `/posm-typeset`; wider/taller uses the
  matching new shape from D (falls back to the master, flagged, if that shape wasn't generated yet);
  violent-band keeps the old `/posm-assemble` flat minimal treatment unchanged, since no photograph
  survives that band regardless of how it's produced.

**Two real bugs found by actually rendering, not just reading code** — both fixed and re-verified with a
second real generation, not assumed fixed:
1. A `recompose` call's prompt told the model "no packaging of any kind" one sentence after telling it
   to faithfully reproduce a pack reference — the packaging refusal only checked `pack_id`/`product_id`,
   never `recompose`. Fixed: skip it when `recompose` is true.
2. The first real end-to-end render (screenshot in [studio-work-inventory]) showed the headline set
   squarely across the pack's own label — `/posm-typeset` reserves its type zone from canvas geometry
   alone, no idea what's actually in the photo there. Fixed at the source rather than patched after the
   fact: `/studio-shot` now takes `type_position` and, in scene mode, tells the model to leave that zone
   "visually clear and uncluttered... real type will be added there afterward." Re-rendered on a fresh
   shot: pack/glass/splash composed cleanly above the line, headline lands on the plain table, contrast
   3.78:1, clears the WCAG floor. Screenshotted both the broken and the fixed version rather than
   asserting the fix worked.

**Also found and fixed while testing**: the scamp card's own click target changed shape in round 80's
markup edit (an inner `onClick` div nested inside a now-non-clickable outer border div) — a naive
`closest('div')` walk from a child element can land on the wrong ancestor if intermediate wrapper divs
also happen to carry `cursor:pointer` from inherited styles; direct `img.parentElement` was reliable.
Not a shipped bug (the real onClick handler was always correctly wired), but worth remembering as a
test-authoring trap, not a code trap.

**Structural bug caught and fixed before any live testing**: reordering B3's assets-gate `sc-if` swept
the palette AND the sketch panel itself inside `posmAssetsUnlocked` — a real deadlock (sketching was
the only way to satisfy the gate that hid the sketch panel). Caught immediately on first live click
("Sketch the layout" button simply wasn't there), fixed by moving the gate to open after the sketch
panel's own closing div instead of before the palette. Fixed via a Python line-range script rather than
repeated Edit-tool string-matching, after several string-match attempts failed against this exact block
for reasons that were never fully diagnosed (likely a subtle escaping difference between the Grep-tool
render of the text and the file's actual bytes) — noted as a pattern worth trying earlier next time a
large multi-line Edit keeps failing to match text that Read confirms is present verbatim.

**Live-verified end to end, real generation calls, not just code review**: B (sketch_url confirmed in
both `/cast-reference` and `/studio-shot` request payloads and prompts), C (both isolate calls
succeeded, correct role text, correct fallback provider behaviour), D (recompose call hit exactly 3
refs, correct role text, real image back), E (both the broken and fixed renders, screenshotted).
**Code-reviewed but not click-tested**: D3's per-tile band routing (near/wider/taller/violent dispatch)
and the violent-band `/posm-assemble` path, since reaching every band in one session would have meant
generating a full format spread — the dispatch logic itself is a straightforward, deterministic branch
on an already-correct `pi.band` value, named honestly as the lower-confidence piece rather than claimed
equally verified.

**Known follow-up, not built**: `/posm-artwork`'s vector SVG export still has its own independent
geometry, unrelated to any of this round's work — a pre-existing gap, unchanged.

## Round 82 (2026-09-03) — isolation reliability, cast/location as fail-proof fallbacks, whole-portal wiring audit

**Isolation revamp**: split into 4 elements (text, pack, characters, background — renamed from 'cast' to
avoid colliding with the unrelated `castChoice`/cast-draft mechanism), each with the same "Adjust — keep
everything else the same" chained-refinement pattern already proven on shapes. New `/studio-shot` flag
`keep_same` tells apart "isolate ONE thing from a busy scene" (discard everything else) from "refine
this already-isolated element" (keep what's there) — conflating the two was why pack isolation took the
user 5 rounds: each retry got the ISOLATE framing (discard everything) instead of a real incremental fix.

**Cast and location made explicitly optional, fail-proof fallbacks, not primary inputs**: cast draft
card now shows for every hero type, not just person-in-benefit/endorser-with-pack — copy changes to
explain it's a fallback ("the studio shot will hallucinate a person from the route and sketch on its own")
when not required. Location gets the same "Include the location" click-to-include checkbox pattern
already used for pack/product, wired via a new `plate_url` param on `/studio-shot` (raw URL, not
library-gated, mirroring `sketch_url`) — closes the gap found live two rounds ago where a drafted
backdrop was previewed and never actually reached generation.

**Two more real bugs found and fixed while building this, live-tested each time**:
- Same packaging-contradiction bug, third occurrence: `keep_same` calls needed the same skip as
  `recompose`/scene-adjust — fixed in the same condition.
- (No new bug beyond that this round — the `keep_same` framing fix and `plate_url` addition both
  verified correct on the first real test.)

**Whole-portal wiring audit** (5 parallel Explore agents, one per area, hunting the same pattern:
something captured in one screen that never reaches the generation call a reasonable person would
expect it to inform) — full findings written up and delivered to the user directly; not duplicating the
detail here, but the headline gaps, roughly by severity:
- **Video studio**: the entire "Cut, grade & sound" tab (grade, ambience, music, foley) is structurally
  unreachable — `cut.start()` (the manifest bootstrap) is never called anywhere except its own route, so
  `hasCutManifest` is permanently false. Also: cast/plate references never reach `/produce-video`'s
  actual render when no storyboard frame exists (falls to captionless text-to-video); `characters` sheet
  text reaches voice casting but not the picture prompt; nothing gates Production on frames existing.
- **Sales enabler**: the whole tab is disconnected from its own backend producer — `/sales-element` only
  saves brief text, `/sales-generate` (fully built, plan/house-grounded) is never called from the UI at
  all, and the frontend's own toast ("no producer wired") is factually wrong.
- **Library/brand-profile cross-cutting**: `fonts`/`dos` brand-profile fields captured but never read by
  `voice_block()`; fal-fallback paths on `/posm-image` and (live) `/activation-element-image` drop all
  references on failover to a blind hallucination; `/posm-image`'s pack lookup rejects `product`-kind
  assets other sibling routes accept; no fallback to a signed-off library logo when brand-profile's own
  logo is unset.
- **Social producer**: reference-library chips are permanently empty (`REF_LIBRARY=[]`, no loader) and
  uploaded reference images never leave local state — `/scene-still` never receives them regardless.
- **Onground**: `idea.risk` never reaches element generation; no library reference fallback for element
  renders the way Social/POSM have.
- **Briefs/Strategy/Plan**: five brief fields (comm objective, competitive context, deliverables, budget,
  timeline) never reach `strategy._brief_text()`'s prompt; NeedScope analysis and SMP defence/unlocks
  have no canon path at all; the Briefs tab's own "Save" button silently deletes the Current/Desired
  belief fields an auto-save had just populated correctly (nesting mismatch); the Governance plan layer
  is captured but read by nothing downstream.
- **PR**: standby crisis statements, written specifically to be retrieved under pressure, are never
  offered when an incident actually opens — `open_incident` always starts with a blank statement.
- Ruled out (checked, no gap): PR release/messages, Media tab (no generation step to lose a capture
  from), continuity checks (correctly read-only by design), dialogue/voice/music-style wiring.

None of the portal-wide findings were fixed this round — reported to the user as a punch list, prioritization pending.

## Round 83 (2026-09-04) — backend quality audit added to the Portal Wiring Audit

Five more parallel Explore audits, different lens from round 82's (capture-then-dropped): security,
data integrity/concurrency, error handling, logic-bugs/drifted-duplication, performance/provider-cost.
All findings appended to the SAME artifact (https://claude.ai/code/artifact/777fa9b9-004c-4ef0-8b1a-e6445336c586),
republished to the same URL. Nothing fixed yet — still a punch list, now much fuller. Headline findings:

- **Security (real, high-severity)**: `gemini.local_path()` has an unrestricted local-file-read fallback
  (unlike its sibling `library.local_path()`, which correctly checks the path stays under its root) —
  reachable via `reference_url` on `/cast-reference`/`/scene-still`, meaning a request could get the
  server's own `.env` read and its bytes shipped to Google's API. Separately, `library.add()` has no
  file-type/extension allowlist (unlike `/brand-logo`, which does) and uploads get served back inline
  with no safe `media_type` — a real stored-XSS path. Also a blind SSRF (no host/IP denylist on the same
  reference-URL fetch).
- **Data integrity**: the entire asset library isn't tenant-scoped at all (`library.py` never imports
  `tenancy` — the one store in the whole app that doesn't) — every tenant shares the same signed-off
  packs, logos, cast refs, and locked legal/FSSAI copy. Plus a systemic read-modify-write race across
  every domain store (no lock, no version check) — two concurrent library sign-offs or messaging-house
  edits silently overwrite each other.
- **Error handling**: the fal-fallback-drops-references bug (`/posm-image`, `/activation-element-image`)
  was found INDEPENDENTLY by two separate audits a day apart — strong signal it's real and worth fixing
  first. Also: `prompts.py`'s `spine_block()` silently swallows any exception and returns "" — one
  malformed house/plan document makes every subsequent generation for that brand lose its core message,
  RTBs and avoid-list with zero logging.
- **Logic/drift**: `keyvisual.assemble()`'s hero-drawing gate only checks aspect-ratio band, never the
  format's own tier system — its own comment claims it enforces `posm.TIERS`'s drop-hero rule but never
  actually calls `dropped_layers()`/`tier_for()`. Wobbler, unipole, entry-arch and others get a full
  photographic hero the format's own spec sheet says must be dropped. Also: `/posm-assemble` never
  resolves `pack_id` to a URL (assigns the raw id string as if it were one) — silently ships with no
  pack while still reporting `pack_used: true`.
- **Performance/cost**: film production's `scenes` array has no length cap before becoming one paid Veo
  call per segment — every sibling generation route in the same file caps its own fan-out, this one
  doesn't. A malformed/oversized request could trigger unbounded paid video renders.

Next session: still awaiting the user's prioritization across both parts of the audit (round 82's wiring
gaps + round 83's backend quality findings) before building any fixes.

## Round 84 (2026-09-04) — 4 live-testing defects from screenshots, all fixed

User tested POSM live and reported 4 defects verbatim. All 4 addressed; 1 fully live-verified end to
end, the other 3 code-verified (checkfe + py_compile + server restart) but not run through a real paid
generation call — deliberately, to avoid spending fal/Google credits just to eyeball a label or a prompt
string when the source change was already traced line-by-line.

1. **"No direct briefing path"** — real gap, not copy: `producers.stands_on()` always let a platform/
   house beat anything typed in the box, silently, with no way to override it. Added `force_typed`
   kwarg to `stands_on()`/`key_visual()` (`api/producers.py`), wired through `/posm-keyvisual` via a new
   `ignore_platform` payload field (`api/main.py:5170`), and added a real checkbox next to the brief
   textarea ("Set the platform above aside for this piece…") that sets `pm.ignore_platform` and gates
   `body.ignore_platform` in `developKv` (`app.dc.html`). **Live-verified**: with "The Head Start"
   platform attached, checked the box, typed an override brief, got routes genuinely built from the
   typed text (not the platform), with the resolved source correctly reading "typed here — the idea
   platform and house were set aside for this piece".
2. **Cast models generated but invisible / can't match to final** — `posmAssetCard` (Pack/Product/Logo/
   Cast) now returns a `selectedImg` thumbnail alongside the dropdown; cast drafts get numbered names
   ("AI-drafted cast #2") instead of all sharing one identical name. Fixed a temporal-dead-zone bug I
   introduced while doing this (`previewImg` was referenced before its `const` declaration) before it
   shipped. Code/checkfe-verified only this round.
3. **"Raz"→"Roz" spelling drift survives adjustments** — diagnosed as a hard limit, not a fixable bug:
   baked AI-drawn lettering can't be reliably spelling-corrected by re-asking. Added a "Strip text
   instead" quick-preset next to the master shot's adjust box (`presetStripText` in `app.dc.html`) that
   prefills "remove all text and lettering… keep everything else the same", pointing at the real fix
   already in the app (`/posm-typeset` sets the real line as actual type once the base has no baked
   text). Explanatory copy added inline. Not live-tested against a real generation.
4. **Isolation "still not isolating well", esp. text; rename "Pack, splash, Glass" → "Pack shot"** —
   label rename done (`ELEMENT_KINDS` in `app.dc.html`). Root-caused the text-isolation failure by
   reading `/studio-shot`'s prompt assembly (`api/main.py`, the `mode=='cutout'` block): it
   unconditionally appended "No text, lettering, logos or watermarks" to EVERY cutout call, including
   isolating the headline text ELEMENT_KINDS entry itself — directly contradicting the action text
   ("isolate: just the headline text") in the same prompt. Added an explicit `isolate_kind` field
   (frontend sends `kind` from `ELEMENT_KINDS` through `isolateElement`/`adjustElement`; backend reads
   `payload.get("isolate_kind")`) so cutout mode can branch: `isolate_kind=='text'` gets a typographic-
   reproduction framing ("flat, crisp typographic reproduction, not a photograph... only the text")
   instead of the photographic "no text" refusal. Not live-tested against a real generation — the test
   tenant's asset library is empty, so reaching the studio-shot generate button needs signed-off pack/
   cast assets first, and triggering it purely to eyeball this would spend real fal/Google credits.

Files touched: `api/producers.py` (`stands_on`, `key_visual`), `api/main.py` (`/posm-keyvisual`,
`/studio-shot`), `api/frontend/app.dc.html` (multiple: see above). All checkfe.py + py_compile clean,
server restarted, item 1 browser-verified live end to end.

## Round 85 (2026-09-04) — isolation preview, layered-artwork answer, hero-drop-tier fix, custom sizes

Follow-on same day, after round 84's live-testing fixes. Covers: (1) isolation blocks now preload the
source shot, (2) answered whether POSM output is a real editable/print file, (3) fixed a confirmed,
tested hero-drop bug across all three render paths, (4) added custom-dimension format support end to
end. Items 1 and 4 are **live-verified in the browser**; the hero-drop-tier fix is **verified with real
Pillow calls against the real functions** (zero API cost — pure local compositing, no fal/Google spend)
rather than through a live generation.

1. **Isolation blocks showed nothing until already isolated once** — all 4 element blocks
   (text/pack/characters/background) now preload the locked hero shot as a fallback preview, labeled
   "Source shot — not isolated yet" (`posmIsolate.elements` in `app.dc.html`). Live-verified.

2. **Print/layered-file question, answered (no code needed)** — the app already produces a real layered
   SVG via `/posm-artwork` (`keyvisual.artwork_svg`) with named layers and live `<text>`, built to open
   in Illustrator/Affinity/Inkscape/CorelDRAW, plus a separate 300dpi CMYK TIFF via `/posm-print`
   (`keyvisual.assemble_print`) with bleed/crop marks. Both already wired into the UI per rendered piece
   (`exportArtwork`/`exportPrint` in `app.dc.html`, buttons "⬇ Editable artwork (SVG, layered)" / "⬇
   Print artwork (300dpi CMYK)"). Nothing to build — the user didn't know the buttons were there.

3. **Hero-drop-tier bug, confirmed and fixed in all three render paths.** Root cause: `keyvisual.py`'s
   raster `assemble()` gated the photographic hero only on `posm.reflow(fmt)`'s aspect-delta "violent"
   band — never on `posm.tier_for(fmt)`/`dropped_layers(fmt)`, the format-specific (not shape-specific)
   authority for which layers a substrate can carry. The two disagree on ~8 formats: Wobbler, Unipole,
   Hoarding, Backing sheet, Bunting, Tin plate, Entry arch, Shelf/rack branding all have a tier saying
   "drop the hero" but a mild aspect band that never triggered the old gate — so they were rendering a
   full photographic hero their own spec sheet says they can't carry. Fixed by checking
   `"hero" not in dropped_layers(fmt)` in addition to the band check; also gated the headline/type layer
   on `"type" not in dropped` so dropping the hero on `mark-only` formats (Wobbler/Unipole/Entry-arch)
   doesn't leave orphaned floating text with nothing to anchor it. **Found and fixed the same gap a
   THIRD time**: `artwork_svg()` (the Illustrator-layered export) had NO gate at all, not even the old
   aspect-band check — so the "Editable artwork" export was the worst-affected of the three paths.
   `assemble_print()` needed no separate fix — it calls `assemble()` internally and inherited the fix
   for free. Verified with a synthetic cutout image and real `posm.dropped_layers()`/`assemble()`/
   `artwork_svg()` calls (no server, no API spend) across wobbler/unipole/bunting/tin-plate/hoarding/
   backing-sheet/entry-arch/poster-a3/standee/dealer-board — hero and type presence now exactly matches
   each format's tier in every case.

4. **Custom-dimension format support, built end to end.** User wanted arbitrary L×B sizes (e.g. "3:2,
   2:1, 1:2, 1:5") for the "New layouts" banner/square panel — investigation found that panel
   (`/studio-shot` `recompose=true`) asks the image PROVIDER directly for a new ratio, and both Gemini
   and FAL silently coerce anything outside `{1:1, 16:9, 9:16, 4:3, 3:4}` to 16:9. The named POS-format
   catalog (`keyvisual.assemble()`), by contrast, never asks the provider for a new ratio at all — it
   generates once at the 3:4 master and re-flows in Pillow to the format's real pixel canvas, so it has
   no such ceiling and already produces the layered/print exports above. Routed custom sizes through
   THAT pipeline instead: `posm.custom_format(w, h)` registers an idempotent synthetic `FORMATS` entry
   (`mm=None` so print/artwork export correctly refuse until real dimensions exist; `tier` inferred from
   `aspect_delta` bands since there's no real substrate to hand-curate one against), `posm.resolve_format`
   is the one shared resolver `/posm-assemble`, `/posm-artwork`, `/posm-print` all now call instead of
   three copies of `if fmt not in posm.FORMATS`, and a new `/posm-custom-format` route lets the frontend
   register one on demand. Frontend: a "Need a size not in the list?" box under "Choose formats" (STEP 2)
   takes a ratio, calls the new route, and merges the result into the format list exactly like a named
   one. **Live-verified**: typed "1:5", got `custom-1x5` registered server-side, appeared in the format
   list as "Custom 1×5" and in the collapsed summary ("1 format selected — Custom 1×5 ▾"). Also
   confirmed live in the same test that named formats and unknown-format errors still resolve correctly.

Not done / explicitly declined this round: a font-style prompt hint (item 6 from round 84's follow-ups)
— user said "understood, we will live with it," so this was deliberately NOT built. The cross-portal
wiring/backend-quality audit (rounds 82–83) remains untouched — user said to tackle it separately.

Files touched: `api/posm.py` (`custom_format`, `resolve_format`), `api/keyvisual.py` (`assemble`,
`artwork_svg` — hero/type tier gating), `api/main.py` (`/posm-assemble`, `/posm-artwork`, `/posm-print`,
new `/posm-custom-format`), `api/frontend/app.dc.html` (isolation preview fallback, custom-size UI).
checkfe.py + py_compile clean throughout, server restarted, items 1 and 4 browser-verified live, item 3
verified with direct Pillow/posm calls (no server needed, zero API spend).

## Round 86 (2026-09-04) — live-test feedback on round 85: 2nd text-isolation contradiction found, hero-choice wiring fixed

Same day, user tried the round-85 fixes live (4 screenshots). Studio shot generation and the Square
new-layout recompose both worked well. Two real findings:

1. **Text isolation still returned the whole scene on round 1** — re-read `/studio-shot`'s full cutout
   prompt and found a SECOND contradiction the round-85 `isolate_kind` fix missed: the unconditional
   "Isolated on a plain flat mid-grey..." block continued straight into "studio lighting... the subject
   FLOATS... cast shadow... reflection... mirrored floor" — all physical-object/3D-photography language
   — immediately before the new typography-only instruction that says the opposite. Split the block:
   the flat-grey-backdrop sentence stays for every kind (still the right key colour for text too), but
   the studio-lighting/floating/shadow sentence is now gated `if isolate_kind != "text"`, so a text
   isolation call no longer tells the model both "this is a physical object under studio lights" and
   "this is flat typography, not a photograph" in the same prompt. **Not yet re-tested against a real
   generation** (same cost reasoning as round 85) — genuinely uncertain whether this closes the gap or
   whether image-editing models are just unreliable at this specific task (flattening baked photographic
   text into isolated typography, as opposed to segmenting a real object) regardless of prompt wording.
   If round 2 still fails, the honest fallback is to stop relying on this path for text specifically and
   lean fully on the already-built "Strip text" → real-typeset route instead of continuing to iterate
   prompt wording against a possible hard capability ceiling.

2. **"What goes into this piece" HERO field never offered the New-layout (banner/square) shapes, and —
   worse — silently ignored an explicit HERO choice anyway for wider/taller-band formats.** Two related
   bugs: (a) `heroChoices` in `app.dc.html` only ever mapped `pm.studioShots`/`pm.modelShots`, never
   `pm.posmShapes` — so a well-generated Square recompose had no way to become a piece's chosen hero.
   Fixed by adding a third `.forEach` over `this.NEW_SHAPES`/`pm.posmShapes`, same `pickHeroShot`
   mechanism. (b) Independent of whether it was choosable, `produceAdaptations` already had a DIFFERENT
   bug: for any format landing in the "wider" or "taller" reflow band, it always silently substituted
   `posmShapes.banner`/`.square` for whatever `p.heroFromShot` actually was — directly contradicting the
   checklist panel's own stated promise ("the render uses exactly this, not whatever was last clicked on
   the panels above"). Fixed by checking whether `heroFromShot` already points at one of the posmShapes
   URLs (an explicit New-layout pick) and honoring that over the automatic substitution; the automatic
   default still applies when the user hasn't touched the New-layout hero choice, preserving the
   original "a wider/taller format looks better from a differently-shaped photo than a straight crop"
   reasoning for the common case. Not yet live-verified (would need a real posmShapes entry from a paid
   generation to observe) — verified by code inspection and checkfe.py only.

Files touched: `api/main.py` (`/studio-shot` cutout prompt), `api/frontend/app.dc.html`
(`heroChoices`, `produceAdaptations`). checkfe.py + py_compile clean, server restarted.

## Round 87 (2026-09-04) — Onground/Activation producer, first pass: 3 real bugs found and fixed

User moved to the third producer (Onground activation) for the first time this week. Idea generation
worked; picking an idea worked. Three real defects reported and fixed, one **live-verified end to end**
(cost: one idea-generation text call, no image spend), two code-verified only.

1. **"Develop" did nothing on any execution element — confirmed and fixed, live.** `developElement`
   (`app.dc.html`) called `/activation-element`, which genuinely returns a generated `{brief, note}` —
   but the frontend handler discarded the response entirely: no `setState`, ever, on success OR
   failure. A card could not visibly change from "not started" no matter what the server answered. Also
   found: its failure-path toast ("No producer is wired for onground artwork yet") was stale copy left
   over from before `/activation-element-image` (the render route) existed — untrue by the time a
   person could even see it, since render already worked. Fixed to write `d.brief` into `og.elements[k]`
   on success (flips the card to "briefed" and the button to "Develop", matching the render pattern
   already used elsewhere), added a busy label ("Developing…"), and replaced the toast with the
   server's own message either way. **Live-verified**: generated activation ideas, chose "The Dawn-Glass
   Board," clicked "Develop" on the Stall element — status flipped "not started" → "briefed", button
   flipped "Develop from the idea" → "Develop", confirming the write-back actually lands.

2. **Stall render "not in any key visual driven" / reads generic — two real causes, both fixed, not yet
   re-tested against a real generation.**
   - Frontend: `renderElement` sourced `kv_url` from `kv.image_url` on the CHOSEN POSM ROUTE OPTION — a
     text-only treatment description from `/posm-keyvisual` that never carries a picture. `kv_url` was
     therefore silently empty on every call regardless of whether a real key visual existed. Fixed to
     read `this.posm().heroFromShot` instead — the actual locked/rendered master image, same field the
     POS Material screen itself renders from.
   - Backend: `/activation-element-image`'s prompt had NO brand grounding at all — no name, no palette,
     no mandatories, nothing from `brandprofile`, unlike essentially every sibling generation route in
     this app. This is what "random generation" actually meant: not that grounding was refused on
     purpose, just never wired for this one route. Added a brand-context paragraph (name, category,
     tone, palette hex values, hero product, mandatories, avoid-list) pulled from `brandprofile.resolve()`
     into the prompt. Also fixed a dishonesty bug found while reading the same function: the `note` field
     always claimed "the key visual as a reference" for `reference`-role elements even when no `kv_url`
     was supplied or the reference call silently fell through to a plain text render — `used_kv` is now
     tracked from whether the reference path actually produced the final image, not from whether one was
     merely offered, and `note` is built from that ground truth for both `source` and `reference` roles.
   - Not live-tested: needs a real rendered POSM hero + a real activation-element generation call to
     observe, both real spend. FAL's branch of this same route still never attempts a reference-based
     call at all (only Google's does) — a smaller, separate gap already named in the round-83 audit's
     "fal-fallback-drops-references" finding; left alone per the user's "audit separately" instruction.

Files touched: `api/main.py` (`/activation-element-image`), `api/frontend/app.dc.html`
(`developElement`, `renderElement`, `ogElements`). checkfe.py + py_compile clean, server restarted,
item 1 browser-verified live end to end, item 2 code-verified only.

## Round 88 (2026-09-04) — Onground Inputs panel + per-element sizes, built and browser-verified

User asked (after confirming the plan first) for an Inputs panel above the execution elements — pick a
KV/pack/promoter once, reused by every element's render — plus real size/type options for Stall, Van,
Truck and Leave Behind instead of a flat 4:3 default. Built and **live-verified** end to end.

- **Backend**: `producers.OG_ELEMENT_SIZES` — real `(key, label, ratio)` options for the 4 elements that
  are an actual physical object with a footprint (Stall: 3×3/6×3, Van: side/back, Truck: side/back,
  Leave Behind: flyer/sachet); all ratios checked against `posm.RENDER_RATIOS` so none silently coerce.
  `/activation-element-image` now accepts `cast_id`/`pack_id`/`product_id` (same locked-reference
  fidelity mechanism `/studio-shot` already gives POSM — resolved via `library.get()`, signed-off only)
  and `size_key` (picks the format's real ratio); the prompt now lists every locked reference generically
  ("reference image N shows...") instead of only ever handling a single `kv_url`; the `note`/`used_kv`
  honesty fix from round 87 was generalized to track any reference actually used, not just the KV.
- **Frontend**: a new "Inputs" panel (gated on an idea being chosen) with Key visual / Pack shot / Model-
  promoter / Product dropdowns, reading the SAME signed-off library POSM already uses
  (`posmAssetOptions`) — no second asset catalog. Each Stall/Van/Truck/Leave-Behind card gets an inline
  size dropdown (`OG_ELEMENT_SIZES` JS mirror of the Python table — noted to keep in sync). Wired into
  `renderElement`'s request body (`kv_url` from the picked override or `heroFromShot`, `pack_id`/
  `cast_id`/`product_id`, `size_key`).
- **Caught and fixed before shipping**: the template engine doesn't support inline ternaries or `!`
  negation inside `{{ }}` — two labels and two `disabled` bindings were written that way and had to be
  precomputed as plain JS values in the render bag instead. Worth remembering for any future template
  work in this file.
- **Live-verified**: generated fresh activation ideas, chose one, confirmed live — Key visual correctly
  showed "No key visual rendered yet" (none existed this session), Pack shot correctly listed the real
  signed-off packs ("Heritage milk.avif", "heritage daily health pack shot.jpg"), Model/promoter
  correctly listed real cast drafts ("AI-drafted cast #1"–"#8"), the Product field correctly stayed
  hidden (no product-kind assets exist), and the Stall card's size dropdown rendered inline
  ("3×3 ft — single-promoter counter" / "6×3 ft — two-sided, room for a queue"). No new console errors.

Files touched: `api/producers.py` (`OG_ELEMENT_SIZES`), `api/main.py`
(`/activation-element-image` — multi-reference support, size_key), `api/frontend/app.dc.html`
(`OG_ELEMENT_SIZES` JS mirror, `ogInputs` bag, Inputs panel markup, per-element size dropdown,
`renderElement`). checkfe.py + py_compile clean, server restarted, browser-verified live.

## Round 89 (2026-09-04) — real tooling installed, 4 of the round-83 security findings actually fixed

Context: user is deploying to `themarketing-studio.com` for a login-gated beta. Agreed to reprioritize
the round-83 audit's SECURITY findings ahead of "later" given imminent internet exposure, and to add
real tooling (ruff, pytest, pip-audit) rather than rely on LLM-read-only auditing going forward.

**Tooling added** (`api/requirements-dev.txt`, `api/ruff.toml`, `api/tests/test_posm.py`):
- `ruff` (config tuned to security/bug rule families only — E/F/B/S/SIM/C4/RUF/ASYNC/DTZ; import-sort
  and pyupgrade-style noise deliberately excluded so the 20 findings worth reading don't drown in 340
  that aren't). First full run: 363 issues; safe autofix applied (125, mechanical — import order etc.),
  compiled + re-verified this session's own recent edits survived the pass intact.
- Manually triaged the bug/security-relevant categories by hand: `B023` (loop-variable capture, 5
  findings) — verified all 5 are false positives, closures used immediately within the same iteration,
  never escape. `S110`/`S112` (bare except, 19 findings) — mostly deliberate and already commented
  ("never let X stop Y"); the one real, previously-unlogged gap was `prompts.py`'s `spine_block()`,
  fixed (see below). The security-specific "S" rules (S324 md5, S310 urlopen, S603/S607 subprocess) —
  all reviewed individually and confirmed false positives/already-safe (list-form subprocess calls,
  hardcoded API constants, non-cryptographic hash use) — no NEW security bugs surfaced beyond what the
  round-83 audit + this round's manual fixes already found, which is a useful cross-check in itself.
- `pytest` — first real test suite this project has ever had, `api/tests/test_posm.py`, 17 tests
  covering the pure logic in `posm.py`/`producers.py` (hero/type tier-dropping per format, custom-format
  ratio/tier inference, `stands_on`'s force_typed override, `OG_ELEMENT_SIZES` ratio safety). Formalizes
  exactly the manual zero-cost verification already done live earlier this session. One test itself
  had a wrong assumption when first written (checked `FORMATS[key]["ratio"]` against the provider-safe
  set, which isn't the right invariant for the custom-format/Pillow-reflow pipeline — that pipeline
  never asks the provider for the custom ratio at all) — caught by the test failing, fixed to check
  `canvas_px()`'s actual proportions instead. All 17 pass.
- `pip-audit` — clean on `requirements.txt`. Full venv scan found 2 CVEs: `pip` itself (upgraded,
  zero risk, done) and `cryptography` 49.0.0 (a PKCS7/Bleichenbacher oracle — this app never does
  PKCS7 decryption; `cryptography` is only a transitive dep of `pdfminer.six` for PDF parsing — low
  real relevance, left un-upgraded rather than force a major-version bump with no regression-testing
  capacity this session; flagged for a deliberate call later).

**4 real security fixes, all zero-cost-verified with direct function calls (no server, no paid API
spend) plus a full server restart + smoke test with no new console errors:**

1. **`gemini.local_path()` arbitrary local-file read, closed.** Used to accept ANY existing path on
   disk (`if os.path.exists(s): return s`) — reachable via `reference_url`-shaped fields and
   `_resolve_media()`'s fallback in main.py — meaning a caller could read the server's own `.env` (or
   anything else the process can read) and have it shipped to Google's API as an "image" reference.
   Fixed to require containment under `MEDIA_DIR`, the same pattern `library.local_path()` already
   used. Verified: `../.env`, `../../.env`, and an absolute path outside media dir all correctly
   return `None`; a real file inside media dir still resolves.
2. **Blind SSRF in the same function's http(s) fetch, closed.** `_as_base64()`'s `httpx.get(s, ...)`
   had no host check — could reach `169.254.169.254` (cloud metadata) or any private-network address.
   Added `_is_public_http_url()` (resolves the hostname, refuses private/loopback/link-local/reserved/
   multicast ranges) as a pre-check, and turned off `follow_redirects` so a URL that passes the check
   can't be redirected to a private address afterward. Verified against 127.0.0.1, localhost,
   169.254.169.254, 192.168.x, 10.x, a bad scheme, and a malformed string — all correctly refused; a
   real public domain still resolves correctly.
3. **`library.add()` had no file-type allowlist — stored-XSS path, closed.** An upload's extension was
   kept verbatim with no check, and `/library-file/<kind>/<name>` serves it back via `FileResponse`,
   which sets Content-Type by guessing from that same extension — `evil.html` would be served as
   `text/html` at this app's own origin. Added a real allowlist (images/video/audio/documents;
   deliberately excludes `.svg` unlike `/brand-logo`'s own list, since this function's callers include
   less-trusted kinds like `research`/`brandbook`), exempted the `copy` kind (text, no real file behind
   it). Also fixed one call site (`/composite-upload`) that never wrapped `library.add()` in a
   try/except at all — would have turned a clean rejection into an unhandled 500. Verified: `.html`/
   `.svg`/`.js`/`.php`/`.exe` all refused under a real kind; `.jpg`/`.pdf`/`.mp4`/`.csv` all still
   accepted; a `copy`-kind note whose text happens to end in something extension-shaped is correctly
   exempt.
4. **`prompts.py`'s `spine_block()` silent failure, given a trace.** The exact round-83 finding: a
   real exception reading the house/plan (malformed document, anything) returned `""` with zero
   logging — indistinguishable from the normal "no house adopted yet" case, silently dropping every
   subsequent generation's core message/RTBs/avoid-list for that brand with nothing pointing at why.
   Added `print(..., file=sys.stderr)` matching this codebase's own existing diagnostics convention
   (`creative.py`'s `[creative] ...` pattern, captured to `render-log.txt` in deployment) — the return
   value and control flow are unchanged, so no caller's behavior changes; the failure is just findable
   now instead of invisible.

**Not done / deliberately deferred this round:** `library.py`'s missing tenant-scoping (every tenant
currently shares the same signed-off assets — a real data-integrity gap, but lower urgency than the
directly-exploitable findings above for a single-tenant beta) and the rest of the round-82/83 audit
(data integrity broadly, error handling broadly, logic/drift, performance/cost) — next in line, in
that priority order, per the "fix in risk order" framework agreed this round.

Files touched: `api/gemini.py` (`local_path`, `_is_public_http_url`, `_as_base64`), `api/library.py`
(`add` — `_SAFE_UPLOAD_EXT`), `api/main.py` (`/composite-upload` error handling), `api/prompts.py`
(`spine_block` logging). New: `api/requirements-dev.txt`, `api/ruff.toml`, `api/tests/test_posm.py`.
py_compile clean on every touched file, pytest 17/17 passing, server restarted and smoke-tested live
with no new console errors.

## Round 90 (2026-09-04) — Portal Wiring Audit + Tab-by-Tab findings: 8 real fixes, all zero-cost-verified

User: "against these findings now fix the portal wiring and other QA related issues you had faced in
your audit" — first pass through the combined punch list (round 82/83's Portal Wiring Audit,
https://claude.ai/code/artifact/777fa9b9-004c-4ef0-8b1a-e6445336c586, ~30 findings across wiring,
security, data integrity, error handling, logic/drift, performance; plus this week's new PR sign-off
finding from the Tab-by-Tab doc). Picked the highest-value, most-contained items first rather than
attempting all 30 in one pass — the rest is a prioritized remainder, below.

1. **`library.py` tenant-scoping — the round-89-agreed #1 priority, done.** `library.py` was the one
   store in the whole app that hardcoded its own directory instead of asking `tenancy` — every tenant on
   a deployment shared the same signed-off packs, logos, cast refs and locked legal/FSSAI copy. Added
   `"library"` to `tenancy.KINDS`; `library.py` now resolves `_dir()`/`_manifest()` through
   `tenancy.dir("library")` per-call (matching `brandprofile._dir()`'s established pattern) instead of a
   module-level constant, with a one-time non-destructive `_migrate_legacy()` that moves the old shared
   `api/library/` into the active tenant's own directory, never overwriting, same rule
   `tenancy.migrate()` already uses. **Real production data was live during this fix** — a real uvicorn
   process on :8000 with active browser connections. Snapshotted `api/library/` to `library.bak-pre-
   tenant-scope` first ([[synthetic-dicts-write-real-tenant-files]]-adjacent caution, applied to a real
   migration this time, not a test fixture). The migration itself hit a genuine race — the live server's
   own first attempt at the new code moved `manifest.json` but errored partway through the binary
   subdirectories (almost certainly a transient file lock from the live process serving a request at
   that exact moment), silently swallowed by `_load()`'s own `except (OSError, ValueError)` catching the
   migration's exception too — a real, now-known latent sharp edge in this design worth flagging if it
   recurs. Completed the move by hand and verified byte-for-byte: all 13 real items (11 signed-off)
   present, sha256-identical to the pre-migration backup, `local_path()` resolving correctly on a fresh
   process. **The live :8000 server was left showing library as empty** (its in-memory old code can no
   longer find files at the old path) until restarted — this is the normal "backend edits need a
   restart" behaviour, not new breakage, but flagged to the user immediately since it was visible in
   their active session.
2. **Fal-fallback reference drop, fixed — the bug two separate audits found independently and called
   "worth fixing first."** `/posm-image` and `/activation-element-image` both called plain
   `text_to_image` on Google-fails-fall-back-to-fal, silently discarding every cast/pack/key-visual
   reference collected earlier while the response still reported the reference as used. Both now try
   `creative.image_from_reference()` first when references exist, matching the Google branch immediately
   above each; only fall through to a blind text render when there's genuinely nothing to hold onto.
3. **`/posm-assemble` never resolved `pack_id` to a URL — fixed.** Assigned the raw manifest id string
   directly as if it were already a URL; `_open_image()` silently failed to decode it and the piece
   shipped with no pack layer while `pack_used: true` still reported success. Now resolves via
   `library.get(pid)["url"]` like every other `pack_id` call site in the file; `pack_used` (already
   `bool(pack_url)`) is correct for free once `pack_url` itself is honest.
4. **Unbounded paid video-render cost — fixed.** `/produce-video`'s `scenes` array had no cap anywhere
   before becoming one paid Veo call per segment (~$0.05–0.40/s) — every sibling generation route caps
   its own fan-out, this one didn't. Added a 24-scene cap, refused with a clear 400 rather than silently
   truncated, matching this app's "offer/refuse, never silently apply" convention.
5. **Brief "Save" button data-loss bug — fixed on both sides, the one genuinely user-facing bug in this
   batch.** Confirmed live in the audit: the IMC builder's visible Save button nested the draft one level
   deeper than `briefstore.canonicalise()` unnests (`fields.draft.cb_ca_db_da.shift_from` — two levels —
   vs. the auto-save's `fields.cb_ca_db_da.shift_from` — one level), so `canonicalise()` silently
   extracted nothing for Current/Desired belief on that save, and `briefstore.put()` **replaced** `canon`
   outright rather than merging — deleting fields a prior, correctly-shaped save had already written.
   Fixed both halves: `saveImcBrief` in `app.dc.html` now spreads the draft (`{...d, ...}`) instead of
   wrapping it in a `draft:` key, matching the auto-save's shape; `briefstore.put()` now merges the newly
   canonicalised fields onto whatever canon already exists instead of replacing it wholesale — a save
   only ever adds/updates a field it actually found something for this time, never blanks one just
   because this particular payload didn't repeat it. The merge fix is the defense-in-depth half: it
   protects every future screen from the same shape-mismatch failure class, not just this one button.
   Verified directly against `briefstore.put()` on the disposable `devtest` tenant: an auto-save-shaped
   payload correctly populates `currentBelief`/`desiredBelief`/`needscopeAnalysis`/`smpDefence`; a second,
   deliberately-partial save (omitting `smp_defence`) correctly keeps the first save's value instead of
   deleting it. Cleaned up after.
6. **Five brief fields + NeedScope/SMP had no path to the House, or had no canon path at all — both
   fixed.** `strategy._brief_text()`'s `keep` tuple omitted `commObjective`/`competition`/`deliverables`/
   `budget`/`timeline` — real, correctly-saved fields on every brief format that the House (the only
   place a brief becomes prompt text) never saw. Added all five to `keep`. Separately, NeedScope analysis
   and the SMP defence/unlocks tables — two of the most distinctive parts of the brand-brief skill's own
   output — had no `briefstore.ALIASES` entry at all, so no screen's save could ever produce them in
   canon regardless of shape. Added `needscopeAnalysis`/`smpDefence`/`smpUnlocks` to `CANON`/`ALIASES`
   (mapped to the draft's own `needscope`/`smp_defence`/`smp_unlocks` keys, flattened by the existing
   `_flatten()`) and to `strategy._brief_text()`'s `keep`. **Deliberately left `execution.brief_for()`/
   `brief_from()` unchanged** — its own comment states a considered, narrow three-field contract
   (mandatories/tone/business-objective, explicitly NOT audience or message) for every execution kind;
   the audit's "dropped a second time" framing doesn't distinguish an oversight from a documented design
   choice, and expanding a deliberately-scoped contract touching every producer in the app is a bigger,
   riskier change than the House-only fix — flagged rather than silently expanded. Verified directly:
   `strategy._brief_text()` against a synthetic house correctly surfaces all five plus the two new canon
   fields in the generated text.
7. **Onground idea "risk" now reaches element generation.** `/activation-element`'s idea-text
   construction (what/venue/who/where/when/how/capture/access) never included the risk callout every
   idea card shows. Added as a "Risk to design around" line, same framing `access` already gets.
8. **PR: two real fixes, one from the wiring audit, one a new finding surfaced re-reading the same
   code this round.** (a) `open_incident()` always started with a blank statement, never matching
   against the standby list this module's own docstring says exists to be "retrieved under pressure
   rather than composed." Added `pr._match_standby()` (word-overlap between the incident's
   category/summary and each standby statement's own `situation` text) — offered via a new
   `standby_match` field on `crisis_status()` and folded into the "no statement drafted" finding's `why`
   text; nothing writes it into `inc["statement"]` automatically, same "offer, never silently adopt" rule
   `set_notice` already follows elsewhere in this module. (b) `sign()`'s only gate on Legal/CEO signing
   was "has QA set the risk class" — Legal and CEO unlocked SIMULTANEOUSLY once QA acted, contradicting
   the module's own stated QA→Legal→CEO order (this was the flow-diagram finding added to the Tab-by-Tab
   doc's Revision 4 this week, not from the original Portal Wiring Audit). Added an explicit
   Legal-before-CEO check. Both verified directly on a disposable crisis sheet (`devtest` tenant):
   standby match correctly offered without auto-adopting; CEO correctly refused before Legal signs,
   correctly allowed after. Cleaned up after.

## Round 91 (2026-09-04) — provenance + "What it has made": built and verified live end to end

Follow-on from the Memory-tab discussion this round: user found AI-drafted cast sitting in "Ground
truth" despite the screen's own promise that "nothing generated is ever admitted here," then caught a
real inconsistency in my own reasoning (briefs are just as often AI-drafted-and-auto-saved as cast
images are) — which reframed the whole ask from "fix one screen" to "one consistent provenance concept,
applied everywhere." User then asked for cast/take approval visibility, provenance vs. upload
distinction, a "What it's made"-vs-"Ground truth" placement rule, and a naming convention — in that
order — then said "do the scoping and build plan before you start." Used `EnterPlanMode`: one Explore
agent to enumerate every generation route (15 found) and the exact current frontend code, one Plan
agent to pressure-test the design before writing code. The Plan agent caught 3 real bugs in the first
draft: a multi-candidate-approval bug (one ledger row per generation call would retire every unpicked
candidate the moment one was approved), a route that would 404 the instant a library file moved into a
subfolder (`{kind}/{fname}` doesn't cross `/` boundaries), and a redundant `origin` field duplicating
what `briefstore.py`'s existing `source` field already tracked. All three fixed before any code was
written — see the approved plan at the top of this round for the full reasoning.

**Built, in dependency order, each piece verified before the next:**

1. **`library.py` — uploads and adopted-AI content physically separated, migration run on real data.**
   `library/<kind>/uploaded/` vs `library/<kind>/tms-approved/`, decided once at write time from
   `source`. Fixed `GET /library-file/{kind}/{fname}` → `{rel:path}` FIRST (same pattern
   `/renders`/`/media`/`/edits` already use) — the 2-segment route would have 404'd every existing
   reference the instant a bucketed path existed. Migrated the 13 real rows (5 upload, 8 generated) with
   a one-shot script: copy, verify sha256 against the manifest's own stored digest, update the manifest,
   only then delete the old flat copies — snapshotted first (`library.bak-pre-bucket-split`). Hit and
   recovered from the exact same live-server race the tenant-scoping migration hit two rounds ago (the
   :8000 process serving a request mid-copy) — completed cleanly on retry, verified byte-for-byte again
   after.
2. **`made.py` — new per-tenant ledger**, same shape as `actuals.py` (atomic writes, same-second
   append-index tiebreak copied deliberately, no locking — accepted explicitly in the docstring, same
   reasoning `actuals.py` uses). One row per candidate, not per call — the bug the Plan agent caught.
   `record()`/`approve()`/`list_entries()`/`remove()`/`kinds()`. `"made"` added to `tenancy.KINDS`.
3. **`made.record()` wired into all 15 generation routes** (`/posm-image`, `/posm-backdrop`,
   `/studio-shot`, `/posm-scene`, `/posm-assemble`, `/posm-scamps`, `/posm-typeset`, `/posm-artwork`,
   `/posm-print`, `/activation-element-image`, `/cast-reference`, `/scene-still`, `/produce-video`,
   `/rescore`, `/cut-sound`) via a shared `_record_made()`/`_made_brand_project()` helper in `main.py` —
   best-effort, swallows its own exceptions so a ledger-write failure can never fail the generation
   response someone is waiting on. `/brand-brief-draft` references the brief it already saves via
   `briefstore.put()` rather than creating a redundant untracked row.
4. **`/library-adopt` rebuilt as the real approve action.** No more `sign` default that could go either
   way (closes the round-83 audit's dormant "library-adopt defaults to signing off AI content" finding
   for good — there's no in-between state left to default) — approval and sign-off are now the same act.
   Writes into `tms-approved/`, named with a fixed tag (`library.APPROVED_LABEL`, computed from `source`)
   instead of the old naming-habit counter, and calls `made.approve()` when a `made_id` is given.
5. **`briefstore.origin()`** — a derived classifier ("drafted" vs. "reviewed"), not a new field, per the
   Plan agent's catch: `source` already carries this distinction correctly, a second field would just be
   a second home for one decision. Exposed through `snapshot()`, which dropped `source` entirely before.
6. **Frontend**: Ground Truth cards now show a real "TMS Generated · Approved" badge computed from
   `item.source`; "What it has made" rebuilt against a new `GET /made` route (`loadMade()`, mirroring
   `loadBriefs()`'s own pattern) instead of the 16-item client-only `s.created` — filter chips extended
   (`All/Brief/Post/Video/POSM/Onground/Campaign`), a `madeMeta()` table maps every one of the 15 kinds
   to a tag/colour/category, and pending `cast_reference` rows get an inline "Add to Ground Truth" button
   (`approveMadeItem`) — the one kind with an unambiguous library `kind` to become; other kinds keep
   whatever adopt path they already had (e.g. POSM's own asset panel). `s.created`/`addCreated()`
   deliberately NOT fully retired — kept powering the Home dashboard's own instant "just made" echo
   widget, a narrower, already-accurate use of it; `createdHistory` in the History screen now only
   supplies Post/Campaign rows (the two categories nothing server-side tracks yet), so a produced film or
   brief draft doesn't appear twice from both the old and new sources.

**Verified live end to end** on the user's real :8000 server (restarted to pick up the change): Ground
Truth screen loads all 13 items via their new bucketed paths (confirmed 200s in the network log, not
404s), all 8 adopted cast items show the new provenance badge correctly, the 2 real uploads correctly
show none, "Awaiting sign-off" now correctly contains only the 2 pre-existing upload stubs (`take-1`/
`take-2`, still not cleaned up — a standing trivial cleanup item), "What it has made" loads from
`/made?include_approved=false` (200, confirmed empty — honest, since no generation has run against
`default` yet this session) with the new filter chips and empty-state copy rendering correctly. Backend
pieces additionally verified directly (zero API cost) on the disposable `devtest` tenant: full
record→approve flow (signed, bucketed, named, ledger row hidden and cross-referenced), multi-candidate
approval (approving one of three leaves the other two pending), same-second tiebreak, `origin()`
classification. `pytest` 26/26 (9 new tests in `api/tests/test_made.py`), `checkfe.py` clean throughout.

Files touched: `api/library.py` (`_bucket`, `add`, `APPROVED_LABEL`), `api/tenancy.py` (`KINDS`),
`api/main.py` (`/library-file` route shape, `/library-adopt`, new `/made`, `_record_made`/
`_made_brand_project`, 15 generation routes), `api/briefstore.py` (`origin`, `snapshot`),
`api/frontend/app.dc.html` (Ground Truth badge, `loadMade`/`approveMadeItem`/`MADE_META`/`madeMeta`,
History screen rebuild). New: `api/made.py`, `api/tests/test_made.py`. Migration snapshot kept at
`api/tenants/default/library.bak-pre-bucket-split/`, matching this project's `.bak` convention.

**Not done — explicitly out of scope this round, not forgotten:** PR/Sales draft-auto-save (only
`/brand-brief-draft` was confirmed to have the silent-auto-save-before-review shape this round; PR/Sales
routes turned out to be rule-based, not model-calling, per the Explore agent's research — no `origin`-
style gap there to fix); the two pre-existing `take-1`/`take-2` dead stub uploads (trivial Remove click,
never actioned); a fuller per-kind "approve" UI for made-ledger kinds beyond `cast_reference` (POSM/
Onground renders still get promoted through their own existing panels, not this screen — a real UI
build, not a backend gap).

**Not done this round — the prioritized remainder**, roughly in the order to tackle next: `voice_block()`
never reading `fonts`/`dos` brand fields (cross-cutting, every text generation); the systemic read-
modify-write race across every domain store (needs a real locking/revision-check design, not a per-
module patch); the Video Studio findings (Cut/grade/sound tab structurally unreachable — `POST /cut`
never called anywhere; cast/plate not reaching `/produce-video` when no storyboard frame exists;
character-sheet text reaching voice casting but not the picture prompt) — larger feature-wiring changes,
each needs its own care; Sales enabler's whole tab disconnected from the real `/sales-generate` producer;
Social's reference library permanently empty (`REF_LIBRARY = []`, no loader, uploads never sent as
FormData); the remaining Data integrity/dormant findings (`library-adopt` defaulting `sign=True`,
per-tenant dirs cached at process start); Logic/drift cleanup items (pack/product treated inconsistently
in `shot_references()`, two drifted pack-word lists); Performance items 2 and 3 (blocking N+1 disk I/O,
repeated re-fetch patterns) — lower urgency, batchable together later. None of these were silently
dropped — each has a reason it's not in this round (bigger blast radius, needs a design decision, or
genuinely lower priority) rather than being missed.

Files touched: `api/tenancy.py` (`KINDS`), `api/library.py` (`_dir`/`_manifest`/`_migrate_legacy`),
`api/main.py` (`/posm-image`, `/activation-element-image`, `/posm-assemble`, `/produce-video`,
`/activation-element`), `api/briefstore.py` (`CANON`, `ALIASES`, `put`), `api/strategy.py`
(`_brief_text`), `api/pr.py` (`sign`, `_match_standby`, `crisis_status`), `api/frontend/app.dc.html`
(`saveImcBrief`). New: `api/library.bak-pre-tenant-scope/` (pre-migration snapshot, kept per this
project's `.bak` convention). py_compile clean on every touched `.py` file, pytest 17/17 passing,
checkfe.py clean (918/918 `sc-if`, 360/360 `sc-for`, 2937/2937 `<div>`). Every fix in this round verified
directly against the real functions on the disposable `devtest` tenant (zero API spend, cleaned up
after) except items 2–4, which are provider-call routes verified by code trace + compile only, same
"needs real API spend to observe" caveat this project has used consistently all session. **The user's
live :8000 server needs a restart to pick up any of this.**

## Round 92 (5 Sep 2026) — user picked items 1,2,3,4,7 from round 91's remainder (5-6 excluded, user
deleting the two dead takes themselves); 1/2/3 fully closed this round, both with live verification

1. **`learning.py` tenant-scoping — done, same shape as `library.py`'s round-90 fix.** Added `"learning"`
   to `tenancy.KINDS`; replaced `LEARNING_DIR`/`DECISIONS`/`TEMPLATES`/`EXAMPLES` module constants with
   `_dir()`/`_migrate_legacy()` functions. Real data (`decisions.jsonl` 9 rows, `examples.jsonl` 9 rows)
   migrated live from the old shared `api/learning/` into `api/tenants/default/learning/`, verified
   byte-identical. Backup at `api/learning.bak-pre-tenant-scope/`. Verified via pytest on the disposable
   `pytest-tenant` (write/read round trip) and confirmed zero remaining references to the old constants.
2. **`voice_block()` now reads `fonts`/`dos` — done.** Two brand-profile fields declared since round 4
   (`palette`/`fonts`/`dos`) but never folded into the one paragraph every text-generation call reads.
   Added `DO:` (from `dos`) beside the existing `NEVER DO:` (avoid), and `TYPE PAIRING:` (from `fonts`)
   beside `BRAND PALETTE:` — both gated on presence, no blank line when absent. Verified directly
   (synthetic dict, both presence/absence), live on the real server (Social Studio correctly reports
   "Not on file yet: fonts, dos" when absent, confirming the code path is live, not just unit-tested),
   and via pytest.
3. **Item 1 (POSM's round-86 fixes) — both halves now live-tested, not just built. Conclusive result on
   each, in opposite directions.**
   - **Text isolation (the 2nd fix, prompt contradiction removed for `isolate_kind:'text'`): confirmed
     code-correct, confirmed insufficient.** Live network inspection of the actual `/studio-shot` request
     showed the contradictory "studio lighting/subject floats/cast shadow/mirrored floor" block is
     correctly absent for `isolate_kind=='text'` — the round-86 prompt fix shipped correctly. But the
     underlying image-editing model (Gemini) still does not comply: downloaded and visually inspected the
     actual output — it returned the full original reference scene (glass + pack), not isolated
     typography. **This is a genuine model-capability ceiling, not a remaining code bug** — exactly the
     fallback round 86 itself already named. Recommendation, not yet actioned: stop relying on isolation
     for text specifically; the already-built "Strip text" → real-typeset route is the reliable path for
     type, same as the rest of POSM's own "an image model never touches the words" design.
   - **Hero-choice wiring (the wider `heroChoices` array, round 86's fix for a render silently discarding
     an explicitly-picked hero) — confirmed working, end to end, by direct visual comparison.** Generated
     a "New Layout" banner shape, explicitly picked it as hero via the "What goes into this piece" →
     Hero strip (`app.dc.html:6120-6129`, backed by `heroChoices`'s third `.forEach` over
     `pm.posmShapes`/`NEW_SHAPES` at `app.dc.html:18327-18333` — confirmed present and correctly built,
     not just claimed), rendered a format that keeps the hero (Poster A3), and downloaded both the chosen
     banner source image and the final rendered piece: **the final piece unambiguously reproduces the
     banner's exact composition** (same pack fold pattern, same nutrition-panel micro-text, same glass
     position/shadow) — not the previously-locked "Studio shot 1" (downloaded separately for comparison;
     visibly different pack render and composition). The explicit hero choice survives to the final piece.
     **One real, useful side-finding surfaced by this test, not a bug**: `/posm-adapt`'s own reflow
     response for "violent"-delta formats (e.g. shelf-strip/talker, a 12:1 crop) explicitly lists `"hero"`
     in its `dropped` layers — these formats intentionally drop whatever hero was chosen, always, per
     `posm.reflow()`'s existing tier logic. Tested shelf-strip first and initially misread the resulting
     hero-less composite as a wiring failure; re-reading `/posm-adapt`'s response clarified this is by
     design, then re-tested with a hero-preserving format (Poster A3) to get the real answer above.
   Real media generated live during this test (kept, not cleaned up — these are legitimate generation
   artifacts, not synthetic test fixtures): `frame-3aca92de7a.jpg`/`frame-b4fbba8976.jpg`/
   `frame-926e74cca1.jpg` (studio shots + banner), `kv-8444731e3c.png`/`kv-8614e9850a.png`/
   `kv-type-c18f26f816.png` (assembled/typeset composites) under `tenants/default/media/`.

**Still open from the user's picked set**: item 4 (the systemic read-modify-write race across domain
stores — needs a locking/revision-counter design, not started this round) and item 7 (Social Studio's
permanently empty reference library — needs a real loader + a real multipart upload handler, not started
this round). Item 5 (Video Studio's unreachable Cut tab + cast/plate wiring) and item 6 (Sales enabler's
disconnected `/sales-generate`) explicitly excluded by the user this round. The two dead `take-1`/`take-2`
stub uploads: user is deleting these themselves, not this session's job.

4. **Item 7 (Social's empty reference library) — done, and turned out to affect Video too.**
   Investigating `REF_LIBRARY = []` found the gap was narrower than it looked in one direction and
   wider in another. Narrower: `inputsContext()` (the function that actually builds the prompt clause)
   already correctly folds `s.inputs.refs`/`s.inputs.uploads` into text and is called from both
   `generateSocial()` and Video's script writer — the "Draw on these reference assets" mechanism was
   never dead code, just starved, because nothing ever populated the chip list it reads from. Wider:
   the exact same markup/state (`refLibrary`, `handleStudioUpload`, `REF_LIBRARY`) is shared verbatim
   by **both** Social's and Video's "Inputs to guide generation" panel (`app.dc.html:1934`/`5390`) — this
   was never Social-specific, it just hadn't been checked against Video too.
   Fixed: `refLibrary` now reads `s.library.items` (the real per-tenant asset store — same one POSM's
   asset panel and Ground Truth already read), filtered to `signed_off` only, matching Ground Truth's own
   "not real until signed" rule. Video already loaded `s.library` on screen entry (`go()`); Social had no
   equivalent single entry point (`xTab` gets set to `'social'` from several different call sites) so the
   load is hooked into `componentDidUpdate`'s existing tab-change detector instead — fires exactly once
   per switch into the Social tab, regardless of which button caused it. The dead `REF_LIBRARY = []` class
   property is removed.
   **Verified live** on the real server: Social's panel now shows the account's 11 real signed-off items
   (1 logo, 2 packs, 8 AI-drafted-cast) instead of "No asset library is connected" — confirmed a chip
   click correctly toggles on (navy background) and the attached-count updates from 0→1; Video's own
   identical panel re-checked immediately after and shows the same 11 items with no regression.
   **Not done, flagged as a separate, larger gap**: `handleStudioUpload`'s "Upload images / clips" button
   still only records a chosen file's name+kind client-side and never sends the actual bytes anywhere —
   the prompt clause names the file ("Draw on X.jpg") but no model ever sees X.jpg. Fixing that properly
   means either a real multipart upload into `library.py` (mirroring POSM's pattern) or an honest copy
   change describing the limitation; bigger than this round's scope, not attempted.

Files touched: `api/tenancy.py` (`KINDS`), `api/learning.py` (full tenant-scoping rewrite),
`api/brandprofile.py` (`voice_block`), `api/tests/test_made.py` (4 new tests, now 30/30),
`api/frontend/app.dc.html` (`REF_LIBRARY` removed, `refLibrary` reads `s.library.items`,
`componentDidUpdate` loads it on entry to the Social tab). `checkfe.py` clean (921/921 `sc-if`, 360/360
`sc-for`, 2940/2940 `<div>`, 818 class members) both before and after the frontend edit.

## Round 92 continued — "Priority geography" built on the Plan screen, a genuinely new feature

User's own ask, not from the audit's remainder list: a state → urban/rural → town-class → cities
picker on the Plan tab, multi-row across as many states/units as wanted, rolling up to a reachable
population — "to identify the media plan focus, investment allocation and languages for the execution
elements." Researched first (three parallel agents: current Plan-tab/`geo.py` code, India geo-demographic
data-source landscape, real Census 2011 state population figures), presented a design back to the user
with explicit changes to their own spec before building, got a "yes, go ahead" plus one explicit addition
("multiple Add row... for each state and for multiple states").

**Real changes made to the user's own spec, agreed before building:**
1. "Metro" is a **named list of 8 cities** (Mumbai/Delhi/Kolkata/Chennai/Bengaluru/Hyderabad/Pune/
   Ahmedabad), not a population threshold — matches actual Indian ad-industry usage (and the 74th
   Constitutional Amendment's own definition), not a fourth numeric tier.
2. **Rural and "the rest of urban" cannot offer individual cities** — only a real Tier-1 seeded city list
   (`geo.py`'s existing `_SEED`, ~99 cities ≥5 lakh) gets a picker; everything below that is one honest
   state-level aggregate, never a fabricated small-town list (same "declare the gap" discipline
   `SEED_GAP` already models).
3. Population rollup dedupes by **geography unit** (state+stratum+town-class+city), not by row — two
   rows naming the same unit two ways cannot double-count.
4. NCCS/SEC classification confirmed genuinely unavailable free-of-cost anywhere (only inside MRUC/
   BARC/Kantar/CMIE paid instruments) — flagged as a procurement decision for the user's own team, not
   built. State-level age/gender (Census 2011 male/female + population 0-6) is now seeded and stored,
   but no UI column was built for it this round — kept the scope to what the user actually asked to see
   working, not everything "buildable now."

**Built:**
- `geo.py`: `METRO_CITIES` (named 8), `URBAN_RURAL` (all 36 states/UTs — total/rural/urban/male/female/
  pop_0_6, Census 2011, sourced via census2011.co.in cross-checked against Wikipedia's PCA-cited
  compilation; every derivation the 2014 AP/Telangana split and 2019 J&K/Ladakh split needed is
  documented inline, including the one real ~19-person J&K rural+urban rounding mismatch and the two
  disagreeing Manipur totals in real circulation), `state_population`/`town_class_cities`/
  `town_class_breakdown`/`town_classes`, wired into `/geo-status`'s existing response.
- `plan.py`: `geography` as a new top-level plan field (same tier as `balance`, deliberately NOT an 8th
  `LAYERS` entry — every real layer shares one AI-drafts/steering-note/Generate mechanism and geography
  has none of that, it's a deterministic picker). `set_geography()` (whole-list replace, invalid states
  dropped not refused, row-level dedup) and `geography_reach()` (unit-level dedup rollup, per-state
  breakdown + %, `geo.language_gaps()` surfaced directly for selected states, Census 2011 caveat, a
  `data_quality_flag` for the (unhit, in practice) case where a state's seeded cities exceed its own
  urban total). Wired into `plan.status()`'s existing response.
- `main.py`: `POST /plan-geography` (mirrors `/plan-balance`'s exact shape).
- `app.dc.html`: new always-visible "Priority geography" card, positioned above the layer-rail (not
  inside it — informs every layer below rather than living behind one tab), state/urban-rural/town-class
  selects + toggleable city chips + aggregate-figure display for non-city-level rows, "+ Add row" (any
  number of rows, any mix of states), debounced auto-save (`/plan-geography`, 400ms, same pattern as
  `editPlanCell`), live rollup card (total reach, per-state chips, language-gap banner, caveat).
- `api/tests/test_geo_plan.py` — 14 new tests (town-class arithmetic sums to the real urban total for
  all 36 states with zero data-quality flags; Metro is confirmed a named list not a threshold; `set_geography`
  dedup/invalid-state/rural-shape behavior; `geography_reach`'s unit-level dedup across rows, aggregate
  bands, per-state share, language-gap surfacing, zero-rows case). All 27 tests pass (13 pre-existing +
  14 new) on the disposable `pytest-tenant`, cleaned up after.

**One real bug caught and fixed via live testing, not caught by any static check**: `geoHasLangGaps` was
already a bag key owned by Social's own older `/geo-cities` picker (`app.dc.html` ~line 20963) — this
app has one flat bag namespace across every screen, so the Plan screen's own `geoHasLangGaps` was
silently being overwritten by Social's (empty, on this screen) version, and the language-gap banner
never rendered despite the backend correctly returning the gap every time (confirmed directly via curl
before touching the frontend). Renamed to `pGeoHasLangGaps`/`pGeoLangGapText`, re-verified live. Grepped
every other new key first to rule out further hidden collisions — only this one hit.

**Verified live end-to-end** on the real `:8000` server (restarted for the backend changes): opened a
real 7-layer Heritage plan, added two rows (Maharashtra/urban/metro/Mumbai+Pune, Goa/rural), confirmed
correct population math at every step (single-city selection, multi-city, rest-of-urban and rural
aggregates, cross-row dedup), correct per-state % shares, the Konkani language gap for Goa appearing and
disappearing correctly as rows were added/removed, state persisting correctly across a full page
reload, and row removal correctly recomputing the total. `checkfe.py` clean throughout (932/932 `sc-if`,
364/364 `sc-for`, 2957/2957 `<div>`, 828 class members).

**Not done, explicitly out of scope this round**: a UI column for the seeded state-level age/gender data
(present in `geo.py`, unused in the picker); full 15-59/60+ age bands (no clean free cross-state source
found — would need per-state C-13/C-14 single-year-age tables from censusindia.gov.in, a real future
import); NCCS/SEC-by-geography (genuinely no free source exists — a procurement decision, not a backend
gap); using the population rollup to suggest a channel-weight split by state (ties into the existing
`balance` mechanism, flagged as a natural phase 2, not requested yet).

## Round 92 continued — three more user-requested items: direct producer access, Execution reads Plan's
## geography, language threaded into every producer prompt

User asked for a broader evolution of Plan/Execution beyond the geography feature itself: (1) give every
key producer (Social/Onground/Video/Sales enabler) the same "jump straight there, no plan needed first"
entry POSM and PR already have; (2) connect the new Priority Geography to other tabs. Researched both
before building (three parallel Explore agents: current nav mechanics, every existing geography
touchpoint app-wide) and also scoped a fourth, bigger item (a real approval hierarchy — org chart, named
levels, user database with email/phone, a real authorization gate, future email/SMS notifications) which
is DESIGNED but not yet built — see its own write-up below.

**Item 2, corrected scope from research.** The framing going in ("POSM and PR have it, others don't") was
half wrong: Video, PR, and Sales enabler already have direct top-level nav entry (Video and Sales enabler
even have Home shortcut buttons already, same pattern as POSM's `goPosmShortcut`). The real gaps were
narrower — **Onground activation had zero direct-entry route at all**, and **Social had a button but its
own code comment admitted the zero-context render was never hardened like POSM's**. Findings from
building both:
1. **Onground — done.** Built `goOngroundShortcut` (`app.dc.html`, mirrors `goPosmShortcut` exactly:
   `screen:'exec', xTab:'onground'`, using Onground's own existing preloads `loadOgStandsOn`/
   `ensureAssetLib` rather than POSM's `loadPosmFormats`). New 5th Home card ("Onground activation"),
   same row as Sales enabler/Video/Media/Campaigns. **Verified live with zero plan context bound**: the
   screen already renders correctly — "no plan open", "Nothing is briefed yet... Open a plan first" all
   correct, idea panel correctly shows the platform-derived idea text. `og()`'s own state getter already
   returns full safe defaults (`this.state.og || {idea:'', ..., chosenIdea:null}`) regardless of context,
   same defensive pattern POSM's `xIsPosm` branch already used — so **no additional hardening was
   actually needed**, the missing entry route was the whole gap.
2. **Social — audited, found already correct, no fix needed.** Live-tested the existing `goSocial`/
   `goExecIdea` shortcut with zero plan context: renders cleanly, same quality bar as Onground/POSM — "no
   plan open" correctly shown, reference-library panel (this session's earlier fix) renders correctly,
   `generateSocial()`'s own code already guards every context-dependent read (`execId` optional,
   requires a typed objective when no brief is bound). **The code comment flagging this as unverified/
   weaker than POSM's appears stale** — either already fixed by other work this session or was never as
   broken as the comment suggested. Reported honestly rather than inventing a fix for a bug that could
   not be reproduced live.

**Item 3 phase A — done, and the technical finding underneath it mattered more than the fix itself.**
A prior Explore agent had already found: every existing geography touchpoint in this app (brand profile's
`states`, Social Plan's per-cell picker, PR's `region`) is a single-hop, screen-local dead end — nothing
propagates geography from one document to another anywhere in the codebase, and `mediaplan.py` (the
Media tab) has no geography dimension at all. Worse: `execution.brief_from()` — the one function that
carries a plan forward into a producer — **structurally could not reach** the new `p["geography"]` field,
because `plan.py` deliberately keeps geography outside the `LAYERS`/`REFS` row-lookup mechanism that
function reads through (no row id, doesn't fit the `_row()` contract).
1. **`execution.py`**: `brief_from()` now calls `plan_mod.geography_reach(p)` directly and attaches it as
   `brief["geography"]` when there are rows — additive/absence-tolerant, same contract as `platform`/
   `campaign`/`house` (which are also special-cased outside `REFS` for the same structural reason).
   Computed fresh every time a brief is built, never cached, matching `geography_reach`'s own discipline.
2. **`app.dc.html`**: "Briefed from the plan" chip grid gets 0-2 new rows when `e.brief.geography` exists
   — "Priority geography" (state list + Indian-formatted reach total, Census-2011-labeled) and, only when
   real, "Language gap" (kept OUT of the existing six rows' "value || 'not set'" fallback deliberately —
   an absent language gap is a *good* state, not an orange warning to match).
3. **`prompts.py`**: `_execution_block()` — the ONE server-side function that builds the "spine" every
   producer's `/complete` call reads when it passes an `execution` id (Social, Video's script writer, and
   any future producer using the same mechanism) — now reads `b.get("geography")` from the execution's
   own stored brief and adds two instruction lines: the priority states (asking for their own idiom, not
   generic national copy) and, when a language gap exists, an explicit **"LANGUAGE GAP, SAY SO"**
   instruction — the model must state plainly that a piece is written in a language the audience may not
   speak first, not silently write around the gap. This is the single, central injection point for every
   current and future producer that routes through `/complete` with an execution id — not duplicated
   per-producer.
4. **6 new tests** (`test_geo_plan.py`, now 17 total in that file / 47 in the whole suite): confirm
   `_execution_block` names priority states and asks for their idiom, states the language gap plainly
   with the actual gap text present, and — the negative case — omits both lines entirely when a plan has
   no geography set (guards against always-on boilerplate).
5. **Verified live, full chain, real data**: created a real execution off the test Heritage plan (both via
   direct API call and through the actual UI form) targeting the plan's `geography` (Maharashtra, Mumbai
   + Pune selected) — the "Priority geography" chip renders exactly as designed: "Maharashtra —
   1,55,66,831 reached (Census 2011)" under "plan · geography". **One pre-existing, unrelated observation
   surfaced along the way, not caused by this change and not fixed**: the six original brief chips (Who/
   Where/When/Measure/Message) rendered "not set" for this freshly-briefed execution, while the new
   geography row (which uses different, direct display logic, not `execRowText()`) rendered correctly —
   worth a look in a future round, flagged rather than silently left unmentioned.
   Also surfaced live, unrelated to this task: **the frontend never re-fetches `/executions?plan=` for a
   plan being reopened** — `state.execs` is populated only by `createExecution()` in the same session, so
   an execution created via direct API call (or from an earlier session) is invisible to the UI until the
   in-session picker creates its own. Noted, not fixed — out of scope for this round.

**Not started yet — item 1, the approval hierarchy (expanded scope, designed not built).** User expanded
this well beyond the original "freeze edits while pending" idea: a real user database (email, phone,
manager/org-chart relationship, soft-deactivate not delete), a per-brand `approval_hierarchy` (ordered
levels, each with a title + primary/backup real user, not free text), a document `status`/
`pending_approval` gate enforced against the REAL logged-in session (finally connecting the existing but
totally disconnected `User`/session/`auth.py` system to a live route, for the first time — narrowly, just
this one surface, not all ~150 routes), an audit log of every approval action, and — flagged explicitly
by the user as a later phase needing its own provider decision (SendGrid/SES, Twilio, etc.) — real email/
SMS notifications for pending tasks/approvals/reviews. Grounded in real research before proposing: confirmed
`domain.py` already has a numeric 1-3 level chain (Draft→Pending→Approved→Live) with a `Role` enum but
NO named titles and NO per-brand configuration; `models.py User` has a flat `role` string, no manager/
hierarchy field, no role-change history; `brandprofile.py` has nothing hierarchy-shaped today; the closest
prior art for NAMED (not just numeric) approval roles is PR's `SIGNOFF_ROLES` (qa/legal/ceo, hardcoded,
sequential/conditional). This design was agreed in principle but not yet built — next round's work,
pending the user's final go-ahead on the extended scope.

**Parked, no work this round, user's own words**: Media tab geography-awareness (item 3 phase B) and
channel-weight-by-state suggestion (phase C) both still phase 2 as previously agreed; further evolution
of the Media and Sales enabler tabs — user said explicitly this is for a later date.

Files touched: `api/frontend/app.dc.html` (`goOngroundShortcut`, new Home card, `geoRows92`/language-gap
chip logic), `api/execution.py` (`brief_from` geography attachment), `api/prompts.py`
(`_execution_block` geography/language-gap instructions), `api/tests/test_geo_plan.py` (+6 tests, 47
total in the suite, all passing). `checkfe.py` clean throughout (932/932 `sc-if`, 364/364 `sc-for`,
2961/2961 `<div>`, 829 class members).

## Round 92 continued — approval hierarchy built (item 1), a scoped-down v1 of the designed feature

Built under real time pressure (session near its budget limit) — scoped deliberately smaller than the
full design discussed with the user (no notification delivery, no dedicated People admin screen, no
per-user session-cookie enforcement), but every piece that shipped is real, tested, and live-verified,
not a stub.

**What shipped:**
1. **`models.py`/`database.py`** — `User` gains `email`, `phone`, `manager_id` (self-FK, org-chart view
   only), `active` (soft-deactivate, never delete). Migration follows the exact existing pattern
   (`_add_missing_columns`, `PRAGMA table_info` + `ALTER TABLE`) — verified live against the REAL
   existing `heritage.db`, not a fresh one: server restart correctly backfilled all 4 real seeded users
   (puneet/ravi/meera/ananya) with real dev-seed email/phone and a manager chain (puneet→ravi→meera→
   ananya), no data loss.
2. **`people.py`** — new, thin: `list_users`/`get`/`snapshot`/`org_chart`/`set_contact`/`set_active`.
   Deliberately does NOT resolve approval gating from `manager_id` — a gate needs an explicit allow-list
   it can check in one lookup, not an inferred reporting-line graph that could silently change shape.
3. **`brandprofile.py`** — new `approval_hierarchy` field: ordered list of `{level, title,
   primary_user_id, backup_user_id}`, whole-list replace (`set_approval_hierarchy`), same "resend the
   set" shape as `plan.set_geography`. Real named titles (what `domain.py`'s `Role` enum never had),
   per-brand ("5 or sometimes more," the user's own words), not a fixed 1-3 count.
4. **`plan.py`** — the actual gate: `status` (draft/pending_approval/approved), `pending_approval`,
   `approval_log`. `submit_for_approval`/`approve`/`reject`, `is_locked()`. **The identity check is
   real but not session-cookie-enforced** — `approve`/`reject` take the acting user's real id and check
   it against that level's actual primary/backup assignment (wrong id → refused, with the real person's
   name in the refusal), not free-text honesty. Stops short of requiring an actual login only because
   nothing in the live product requires signing in today (the session system exists, per CLAUDE.md, and
   has simply never gated a product route) — wiring `current_user` in here instead of a passed id is the
   documented next step once sign-in is a real gate on the app itself.
5. **`main.py`** — `_locked_refusal()` shared helper, applied to `/plan-row`, `/plan-balance`,
   `/plan-geography` (409 while pending). New routes: `/plan-submit-approval`, `/plan-approve`,
   `/plan-reject`, `/people`, `/brand-approval-hierarchy`.
6. **`app.dc.html`** — compact "Approval" panel on the Plan screen: hierarchy editor (title + real
   primary/backup pickers from `/people`), Submit button (disabled with no hierarchy defined),
   pending banner + "acting as" picker + Approve/Reject, reversed audit log. **Deliberately placed on
   Plan rather than Brand setup** — a brand-level setting living on the wrong screen for now, for
   expedience under time pressure; a real future move, said so in the code comment rather than left
   implicit.
7. **8 new tests** (`test_geo_plan.py`, now 23 in that file / 53 in the suite): refuses submit with no
   hierarchy, locks at level 1 on submit, refuses the wrong user by id, accepts the documented BACKUP
   (not just primary) and advances levels correctly, fully approves and unlocks at the last level with a
   complete audit log, rejection requires a reason and correctly unlocks back to draft.
8. **Verified live, full chain, real HTTP calls against the real running server** (not just unit tests):
   set a real 2-level hierarchy on the real Heritage Foods brand profile (Brand Manager → CMO, real
   user ids) → submitted the test plan → confirmed `/plan-balance` correctly refused with 409 while
   pending → confirmed the WRONG approver (ananya, a level-2 person) was correctly refused with 403
   naming her by her real name → confirmed the CORRECT level-1 approver (ravi) advanced it to level 2 →
   confirmed the level-2 approver (ananya) fully approved it → confirmed edits worked again immediately
   after. Frontend re-verified after: hierarchy editor renders real people in both pickers, "✓ Approved —
   fully cleared" and the reverse-chronological audit log both render correctly.
   **One real bug found and fixed during this test, not caused by the new code**: the test plan's own
   `brand` field was `"heritage"` while the real brand profile's name is `"Heritage Foods"` — `main.py`'s
   existing `brandprofile.load(x) or brandprofile.by_name(x)` lookup (used identically in ~8 other places
   in this file already) requires an exact case-insensitive name match, so the mismatch silently returned
   an empty hierarchy and a misleading "no hierarchy defined" refusal. Not a defect in the new approval
   code — a pre-existing data-entry quirk in this session's own earlier test plan — fixed by correcting
   the plan's `brand` field directly (this plan has been scratch/test data all session, not real user
   work). Worth knowing generally: any plan whose `brand` string doesn't exactly match a profile's `name`
   silently can't resolve brand-level data this way, anywhere this lookup pattern is used.

## Round 92 continued — real bug found via user's own live testing: Video's idea platform never loaded

User tested the direct-entry claims themselves (per this round's own item 2 work) and caught something the
earlier research agent's pass missed: entering Video from Home showed "The idea platform: none written"
even though a real, adopted platform existed with its own genuine video-specific expression written
("A boy sits the state exam calm..." — confirmed via `/idea-platform`, `adopted:true`). **Sales enabler's
"I can't find anything" turned out NOT to be a bug** — that producer has no idea-platform panel at all,
structurally: 7 trade channels × 5 elements each (retailer pitch, counter kit, incentive slab...), a
different model from Social/POSM/Onground/Video, verified live by loading it.

Root cause for Video: `go('video')` (what the Home card and top-nav both call) never called
`loadGrounding()` — `resolvedPlatform()`'s fallback path reads `this.grounding().platform`, so with
grounding never fetched, both the primary (`ideaUsable()`) and fallback path came up empty regardless of
what actually existed server-side. Social/POSM/Onground's own direct-entry functions all already call
`loadGrounding()`; Video's generic screen-switch path was the one that didn't. One-line fix
(`app.dc.html`'s `go()` dispatch table). Verified live: reloaded, re-entered Video from Home, "The idea
platform" now correctly shows "The Head Start — Resolved from model, so the film is written against it."
`checkfe.py` clean (938/938 `sc-if`, 369/369 `sc-for`, 2973/2973 `<div>`).

This is the second time this session a producer's "already correct" claim from an earlier pass turned out
wrong once actually exercised with real data end-to-end (the first was the geography language-gap banner
namespace collision) — worth remembering: a nav-entry existing is not the same claim as "the screen it
lands on actually has what it needs loaded."

## Round 92 continued — Social brought to POSM's "set the platform aside" standard (pilot, before the
## other three)

User's own live testing of the direct-entry work above surfaced a design question: all four producers show
a "Prompt guide ▾" at the very top of the screen, disconnected from the actual input it's meant to help
with, and only POSM has a REAL override (a checkbox that genuinely replaces the platform's line server-side,
not just visually). Agreed a target structure across all four (11 numbered steps, user's own table) and
agreed to pilot it on Social alone first, live-test, then roll out to POSM/Onground/Video.

**Real architecture finding that shaped the build**: `producers.stands_on()` already supports `kind="social"`
internally (checked its own dict — `social` was already in the medium-lookup table) but nothing ever called
it for social; Social's generation goes through the shared `/complete` → `prompts.system_for()` pipeline
instead of POSM's dedicated route, and that shared pipeline had no way to skip the house/platform grounding
it injects unconditionally. Making Social's checkbox real (not cosmetic) meant extending the shared pipeline
itself — the same "one central place, every producer benefits" pattern as the geography/language work.

**Built:**
1. **`main.py`**: new generic `POST /producer-stands-on` — any `kind`, resolves house/platform via the
   existing `_exec_ctx()`, calls `producers.stands_on(kind, house, platform, typed, force_typed=...)`. One
   route, reusable by Video later too, rather than a Social-specific one-off.
2. **`prompts.py`**: `system_for()` gains `force_typed` — skips `spine_block()` only (the house's core/RTB/
   medium messaging) when true, never `_execution_block()` (the plan's own audience/channel/occasion/measure/
   message stay binding regardless — exactly what every producer's own "cannot override" notice already
   promises on screen). `complete.py`/`main.py`'s `/complete` route thread it through.
3. **`app.dc.html`**: Social gets a new card between "Inputs to guide generation" and its existing objective
   box — "STEP 1 The message" label, a real quote (`/producer-stands-on`'s resolved text + source, fetched
   on tab entry via `loadSocialStandsOn`), a green "no platform yet, and that's fine" reassurance when
   nothing resolves, and the override checkbox (`socialForceTyped`) — same visual language as POSM's. Wired
   into `generateSocial()`: checked-and-empty is refused (matching `stands_on`'s own "a deliberate override,
   not a silent fallback" stance) rather than quietly falling back to the brief; checked-and-typed excludes
   the brief-grounding clause client-side AND sends `force_typed:true` to `/complete` server-side.
4. **Deliberately NOT done this pass**: moving the shared "Prompt guide ▾"/"cannot override" block down to
   sit right above the input (the other half of the agreed target structure). That block is one shared
   instance covering Social/POSM/Onground at once — repositioning it safely means touching all three
   simultaneously, which breaks the "Social only, isolate for live testing" request. Deferred to the round
   that does POSM/Onground/Video together.

**Verified live**: real quote renders correctly ("THE IDEA PLATFORM, EXPRESSED FOR SOCIAL" — the platform's
actual social-specific expression, not a generic line); checkbox toggles; a real end-to-end generation with
the checkbox checked and a typed objective succeeded (real API call — `ANTHROPIC_API_KEY` is live on this
server, so this cost real credits, unlike most of this session's zero-cost verification). Confirmed the
actual mechanism at zero additional cost via a direct Python check: `system_for(msgs, force_typed=False)`
includes the "THE STRATEGY ALREADY DECIDED" block (13,249 chars); `force_typed=True` excludes it entirely
(2,880 chars) — the skip is real, not a UI-only toggle. `checkfe.py` clean (940/940 `sc-if`, 369/369
`sc-for`, 2979/2979 `<div>`, 844 class members), full test suite still 53/53.

**Next, once the user has live-tested Social**: same treatment for POSM (already has it, just needs the
shared guide moved down), Onground (needs the reassurance-copy + checkbox it's missing, plus the guide
move), and a separate product decision for Video (no free-text field exists there at all today — the
guide's target position needs deciding against a category-picker, not a textarea).

**Two real findings from the user's own live test, both fixed:**
1. **Label**: "STEP 1: The message" renamed to "STEP 1: Create a post" — clearer, no functional change.
2. **A real accuracy bug, not a copy nit.** The green "Written against 'The Head Start'" summary line
   comes from an older, separate function (`socialGrounding()`) that predates `force_typed` entirely —
   it just checks "is a platform currently adopted" and names it, with zero awareness that force_typed
   can now genuinely exclude that platform from the actual prompt. Result: check the box, type your own
   brief, generate — and the summary still credited the platform it was just told to set aside, directly
   contradicting what had actually happened. Fixed by capturing `socialPostsForceTyped` at generate-time
   (both the success and fallback paths) — not read from the live checkbox, so it stays correct even if
   the checkbox is toggled again without regenerating — and having `socialGrounding()` check it first:
   "Written from your own brief — the platform was set aside for this piece." Verified live: generated
   with the checkbox checked, confirmed this exact sentence renders and the stale "Written against"
   sentence is gone (the platform's name still legitimately appears elsewhere on screen, in "What this
   producer is given" — that's correct, unrelated to this banner). `checkfe.py` clean throughout.

**Explicitly not built this round, scope cut for time, not silently dropped**: a dedicated People/org-
chart admin screen (today: `/people` + `/brand-approval-hierarchy` exist and work, reachable only via
the compact inline editor on Plan); real email/SMS/WhatsApp notification delivery (needs the user's own
provider decision — SendGrid/SES, Twilio, etc. — flagged from the start as its own later phase); session-
cookie-enforced identity on the approve action (works today via a passed `user_id` checked against a
real assignment, not a logged-in session — see point 4 above for why); `strategy.py` houses getting the
same freeze (only `plan.py` got it this round — houses are the OTHER store named as actively multi-
editor in the original item-4 research, and would reuse the exact same `is_locked`/`submit_for_approval`
shape, a contained follow-up).

**Two more real bugs, found from the user's own live screenshots, both fixed (5 Sep):**

1. **The "Checking what grounds these posts…" bug was not a timing race — it was six separate entry
   points into Social, and three had never been wired.** `grep -n "xTab:'social'"` found 4 assignment
   sites; only `openSocialExec`/`goExecIdea` (both dashboard shortcuts) had `loadGrounding()` +
   `loadSocialStandsOn()` on them. Fixed the other two: `activate('post')` (the Home "Launcher" quick-
   create modal) and `openPostsFromCampaign`. But the user's own report ("PIC 1 — I just opened the tab —
   below it said checking what grounds these posts") didn't match either of those paths — it matched a
   sixth: the plain **"Execution" nav tab / Home toolkit card**, which calls the generic `go('exec')`
   handler (`app.dc.html` ~9887). That handler has a per-screen preload dispatch table (`if (screen ===
   'video') this.loadGrounding()`, etc.) and had **no branch for `'exec'` at all** — it lands on whatever
   `xTab` is already in state (often 'social', via `xTab()`'s own fallback-to-first-tab) without ever
   calling either loader. Fixed by adding an `exec` branch that mirrors `xGoTab`'s existing per-tab
   dispatch exactly (`loadGrounding()` always, plus the tab-specific loader — `loadPosmFormats`/
   `loadOgStandsOn()`+`ensureAssetLib()`/`loadSocialStandsOn()`). **Verified live**: reloaded, clicked
   "Execution" from Home cold (no prior tab visit), and where before the fix "The idea platform" card
   showed "none written" and the bottom banner stuck on "Checking…", after the fix it correctly shows
   "The Head Start" and "Written against 'The Head Start'." with no stall.

2. **STEP 1's "no idea platform/house" copy was a second, independent bug** — genuinely contradicting the
   bottom banner in the user's own screenshots, not a wording nitpick. `socNoStandsOn` (STEP 1's box) was
   computed purely from `s.socialStandsOn` (platform/house existence) with **no awareness of whether an
   execution/plan is bound** (`xBriefed`, i.e. `!!this.currentExec()`) — so its copy claimed "Describe the
   objective below... it becomes the **whole brief** for these posts — nothing else is required first"
   even when a plan WAS already bound and its audience/channel/etc. legitimately governed the piece —
   exactly the contradiction the user's PIC 2/3 showed ("no idea platform or house behind this" directly
   above "Written against the 9 channels in the plan"). Split the condition in two: `socNoStandsOn` now
   means neither platform/house nor a plan (copy unchanged, it's accurate there); new `socNoStandsOnBriefed`
   means no platform/house but a plan IS bound, with new copy: "No idea platform or house behind this yet —
   but this piece is briefed from the plan below. Its audience, channel, occasion, measure and message
   still apply. Describe the objective below to add to that brief, not replace it." Confirmed the "What
   this producer is given" checkbox the user also flagged (PIC 4, unchecking it only hid the "Briefed from
   the plan" panel) is a pre-existing, correctly-scoped display toggle (`xShowEnvelope: inputs.brief`) —
   not part of this bug, doesn't touch `currentExec()` at all. Not yet live-tested against an actual
   no-platform-but-briefed brand (this brand has a real idea platform, "The Head Start", so the exact
   three-way condition split couldn't be triggered in this session's test brand) — verified by full code
   trace + `checkfe.py` clean instead; flag to the user to specifically re-check this exact combination
   (plan chosen, no idea platform) next.
   `checkfe.py` clean throughout both fixes (941/941 `sc-if`, 369/369 `sc-for`, 2980/2980 `<div>`, 844
   class members).

3. **Unified the two "turn the platform off" controls the user found sitting side by side, one real and
   one decorative.** "What this producer is given" 's "The idea platform" card checkbox never did anything
   beyond toggling a separate, unused display card (`xShowPlatform`) — only STEP 1's own checkbox actually
   sent `force_typed`. User's explicit call after being shown both options: unify them, and make the top
   card's checkbox the single source of truth (option 1 of 2 offered), removing STEP 1's separate inline
   checkbox entirely. Built: on Social, when the server-resolved `socialStandsOn` has real content, the
   idea-platform card's `on`/`toggle` are driven by `!s.socialForceTyped`/`onToggleSocialForceTyped`
   instead of the old decorative `inputs.idea`/`toggleInput('idea')` — gated on `s.socialStandsOn` (what
   STEP 1 actually shows), not the frontend's own `ideaUsable()` (the locally-adopted-in-Strategy check) —
   the two disagree exactly in this test brand's own state (platform resolved server-side "from model" via
   `rp`, with no local Strategy `ip.line` written), which was the first draft's bug, caught before shipping
   by testing live rather than trusting the code read. STEP 1's box now has 4 MECE states instead of 2:
   real quote shown / real quote available but deliberately set aside (new copy, does not claim "no
   platform" when one exists) / no plan+no platform / plan-bound+no platform (previous round's fix).
   **Verified live end-to-end**, both directions: unchecked the card → STEP 1 correctly swapped from the
   real quote to "The idea platform is set aside for this piece — turned off above", card's own state pill
   correctly read "set aside"; re-checked it → both reverted to showing the real quote. Confirmed **not**
   yet unified for POSM/Onground/Video (only Social has the real override built at all so far, per the
   user's own "do Social first" instruction) — `toggleInput('idea')`'s old decorative behavior is
   untouched there. One known, unchanged, pre-existing quirk worth remembering: the bottom "Written
   against..." banner (`socialGrounding()`) does NOT update live when this checkbox is toggled — it only
   flips to the force-typed wording after an actual Generate click, by design from the prior round
   (`socialPostsForceTyped` is captured at generate-time, not read live) — so immediately after toggling
   "set aside" but before generating, the banner can still name the platform. This is a pre-existing,
   separate mechanism, not a new bug from this change — flag it if the user notices and asks about it
   again. `checkfe.py` clean (942/942 `sc-if`, 369/369 `sc-for`, 2981/2981 `<div>`, 844 class members).

4. Rolled the same treatment out to POSM, Onground and Video, after redoing the target-structure
   table against actual code (not the original plan) and getting the user's sign-off on two open
   decisions first: (a) reposition the shared "Prompt guide" now, across all four, not defer it - it had
   never actually moved from the top of the tab despite being the original ask; (b) give Video a real
   free-text field rather than leaving it category-cards-only.
   - Prompt guide repositioned: removed from its old shared top-of-tab spot (Social/POSM/Onground)
     and Video's own top-of-tab spot; re-rendered once per producer, right after the quote/override and
     right before the free-text box it guides. Same pgExec/pgVideo data, markup duplicated 4x rather
     than shared, since each now sits in a different structural position.
   - POSM had the exact same contradiction bug Social's fix addressed - its no-platform copy said "it
     becomes the whole brief... nothing else required first," which would lie the same way against a
     bound-but-platform-less execution. Split into posmNoStands/posmNoStandsBriefed, added
     posmStandsAside, unified its separate checkbox into "The idea platform" card (same standsFor-keyed
     IIFE now covers both social and posm; POSM's actual backend override mechanism -
     pm.ignore_platform to /posm-keyvisual's own spine walk - was untouched, only the frontend control's
     location moved).
   - Onground had no reassurance copy at all when nothing grounds it (the box just showed nothing) -
     added ogNoStands/ogNoStandsBriefed, matching Social/POSM's copy. No override checkbox added here
     by design: onground's textarea is always mandatory and always what's used (confirmed via its own
     code comment - "an empty box is refused... this gives somebody something to write FROM without
     writing it for them"), so there is no silent-override bug for a checkbox to fix, unlike POSM/Social.
   - Video got a real free-text field for the first time - new videoBrief state, onVideoBrief,
     a /producer-stands-on call (loadVideoStandsOn, kind:'video' - already supported server-side,
     producers.py's own medium dict already had "video":"tv", just never called with it before) and
     onToggleVideoForceTyped, wired into generateVideo(): threads force_typed through
     this.complete(prompt, {force_typed}), injects the resolved platform's video-specific line
     additively when not set aside, and refuses the same way generateSocial does if set aside with
     nothing typed. Deliberately did NOT make "What this film is given"'s cards toggleable/unified the way
     Social/POSM's were - a prior round's own comment on vInputCards states this was already a
     considered decision ("a film is not an execution envelope pointing at plan rows, so each card is a
     state and a way to change it rather than a switch"); Video's new checkbox lives in its own quote box
     instead, same shape as Social's original (pre-unification) design.
   - Verified live, all three: POSM's quote/reassurance/Prompt-guide position confirmed, its "idea
     platform" card toggling correctly swaps the quote for "set aside" and back. Onground's quote plus
     repositioned guide confirmed (its own pgExec correctly resolves onground-specific "cannot
     override" text - the occasion/measure/proof obligation, not POSM's format/ratio/mandatories).
     Video's real quote ("THE IDEA PLATFORM, EXPRESSED FOR VIDEO" - a real, platform-specific line, not
     generic) confirmed rendering, its own pgVideo guide confirming video-specific "cannot override"
     text (beat plan roles / clip lengths / endframe clear space), and the new checkbox confirmed
     swapping the quote for the "set aside" message live. No actual /complete generation call was
     triggered for Video during verification (real API cost) - the prompt-construction change itself was
     verified by code trace only, same standing limitation as every other generation-route change this
     session.
   - Explicitly deferred, not done this round: Video's "Briefed from the plan" chips (target-table row
     3) - video has no execution-binding concept at all today (no "Brief it" flow exists for it the way
     Social/POSM/Onground have), so building this is a materially larger feature (giving video a real
     plan/channel binding), not a copy/wiring fix - scoped out rather than rushed. Row 4b's "partial" note
     on Video's own asset panel was not investigated this round. Also NOT audited: Video has 6 separate
     screen:'video' entry points in code and only the generic go('video') dispatcher was wired to call
     the new loadVideoStandsOn() - the other 5 (Launcher's video mode, goVideoTab, openVideoFromCampaign,
     and two more) may have the same "nothing loaded" gap Social's own 6-entry-point audit found and fixed
     earlier this round; flagged in the code as a comment, not fixed, since a full audit is its own task.
   - checkfe.py clean throughout all three (965/965 sc-if, 373/373 sc-for, 3025/3025 div, 847
     class members).

5. Five more issues from the user's own live testing of the round-4 rollout, investigated individually
   (not assumed) before fixing:
   - CONFIRMED REAL BUG, fixed: Onground's "Generate ideas for me" button never sent the typed idea box
     content to the server at all - `generateOgIdeas()`'s body only ever carried house/brief/platform.
     `/activation-idea` already has a `steer` param built for exactly this (steers fresh generation
     without switching into "sharpen this idea" mode, which is a separate typed-idea code path) - and its
     own backend prompt already injects it as "THE PERSON ASKING ADDS" - it just was never wired from the
     frontend. One-line fix: send `body.steer = og().idea.trim()` when present.
   - CONFIRMED REAL INCONSISTENCY, fixed: Video's "What this film is given" card for the idea platform
     looked exactly like Social/POSM's now-real toggle (same checkbox-shaped dot) but was still the OLD
     decorative, non-clickable design from a prior round - a live user tried to uncheck it and couldn't,
     right next to a separate checkbox below that DID work. Unified it the same way Social/POSM's cards
     were unified this round (gated on `s.videoStandsOn` availability, driving `videoForceTyped`), and
     removed the now-redundant separate checkbox from the Phase 1 quote box.
   - CONFIRMED REAL INCONSISTENCY, fixed - but scoped honestly: Onground's own idea-platform card had the
     exact same "looks real, does nothing" problem, but unlike Social/POSM/Video there is genuinely no
     server-side override to unify with (the textarea is always mandatory and always used). Rather than
     leaving it decorative, gave it one real, honestly-described effect: toggling it now hides/shows the
     reference quote only, with copy that says explicitly "this never changes what gets generated" -
     new `ogHideStands` state, `onToggleOgHideStands`, `ogStandsHidden` bag key.
   - CONFIRMED REAL GAP, fixed: Social's rework mechanism regenerated every post to act on feedback about
     one - costs more and gives blunter feedback than adjusting the one post that's wrong. Added a
     per-post "Adjust - keep everything else the same" note + button on every post card (matching POSM's
     own established per-asset pattern), keyed by the post's own unique `id` rather than its `platform`
     (several posts can share one platform value - "three per platform, doing three different jobs" - so
     a platform-keyed dict, which is what the EXISTING bulk `reworkPosts` uses, silently drops the other
     posts sharing that platform; the new per-post path avoids that class of bug by construction). New
     `adjustPost(id)`, `onSocialAdjustNote(id)`, `socialAdjustNotes`/`socialAdjustingId` state.
   - INVESTIGATED, NOT a bug - flagged back to the user rather than silently changed: POSM's key-visual
     routes all showed the platform's own tagline ("Ahead by breakfast") under "Where the line goes" even
     on a Ganeshotsav-themed key visual, which read as stale/wrong. Traced to `producers.key_visual()`'s
     own spine walk (`main.py`'s `/posm-keyvisual` route) - the LINE is deliberately spine-derived and
     held constant across all routes unless the override checkbox is explicitly checked (a brand's
     mandatory tagline is meant to be consistent, not vary per creative route) - while the VISUAL
     description each route carries does vary with the typed brief. Working as designed, not a bug, but a
     real point of confusion since nothing on screen says the LINE specifically (not just the visual
     theme) is what the checkbox controls. Did not change generation behavior; flagged to the user to
     confirm this is the intended behavior or if the line should also flex per-occasion (a real product
     decision, not a copy fix).
   - `checkfe.py` clean throughout (966/966 sc-if, 373/373 sc-for, 3028/3028 div, 850 class members).

6. Live-tested the round-5 fixes; three more items, each investigated/decided before touching code:
   - Onground's typed-prompt fix (item 5's `steer`) CONFIRMED working live: user typed a Ganeshotsav
     sampling brief, "Generate ideas for me" correctly rephrased it and returned Ganeshotsav-specific
     pandal/RWA/modern-trade ideas (not the old generic office/RWA set).
   - Video's card unification CONFIRMED working live both directions ("does the job well").
   - New, real finding: Social's mandatory brand line ("Pure Doodh Ki Shakti — the strength of pure
     milk") appeared on a Janmashtami contest-winner shoutout post where it read as unwanted. Traced:
     it's the brand's own configured Mandatory ("what must appear on every piece" in Brand Profile), so
     this was working as configured, not a bug — but also surfaced that `brandprofile.voice_block()`
     (where Mandatories get injected) is only ever called from `prompts.system_for()`, which only
     Social's and Video's `/complete`-based generation goes through — POSM's and Onground's own prompt
     builders (`producers.key_visual()`, `producers.activation_ideas()`, both via the bare `_ask()`/
     `jsonout.ask_json()` path) never included Mandatories at all, a pre-existing inconsistency, not
     something this round changed.
   - User's decision: make Mandatories skippable specifically when none of the plan/idea/brief trio
     applies to a piece (a fully freeform, typed-only piece) — and, when asked whether compliance items
     (FSSAI mark) should stay forced separately from marketing lines (the tagline) given both currently
     live in the same list, explicitly chose to skip the whole list together rather than split it. Built:
     `brandprofile.voice_block(..., skip_mandatories=False)` (docstring states plainly this is
     all-or-nothing and may drop a regulatory line, not just a tagline — a deliberate, informed choice,
     not an oversight) → threaded through `prompts.system_for()` → `complete.py`'s `complete()` →
     `main.py`'s `/complete` route → `generateSocial()`/`generateVideo()`, each computing their own
     `noTrio` (no bound execution/plan, no linked brief, and idea platform either absent or set aside).
     Verified at zero API cost via direct Python: `system_for(force_typed=True, skip_mandatories=True)`
     excludes "MANDATORY ON EVERY PIECE" entirely; `skip_mandatories=False` includes it — confirms the
     skip is real, not cosmetic. Not yet threaded into `reworkPosts`/`adjustPost` (the rework paths don't
     even pass `force_typed` today, a separate pre-existing gap) — scoped out, not silently dropped.
   - Onground's "hidden"/"Reference hidden" wording (this round's own deliberate choice, made to avoid
     implying a real override that doesn't exist there) — user, after seeing it live, explicitly chose
     consistency over precision: renamed to "set aside" everywhere, keeping only the explicit "this never
     changes what gets generated" clause as the substantive difference from the other three producers'
     copy.
   - STILL OPEN, not built: user asked for a per-idea "Adjust" button on Onground's generated idea cards
     (matching Social's post-level and POSM's asset-level pattern). Investigated before building: the
     existing "Sharpen the idea" flow already lets you pick one of the 3 cards (which fills its summary
     into the top textarea) and refine JUST that text — but going through `producers.sharpen_idea()`,
     which returns a plain refined string, not the same rich structured card (what/who/where/when/how/
     capture/access/risk) the 3 generated options have. A true in-place per-card "Adjust" matching
     Social/POSM's shape would need a NEW backend function to refine one structured idea while preserving
     its shape — not a trivial frontend-only addition like the other two Adjust buttons were. Not built
     yet — flagged back to the user rather than guessing which of the two very different shapes they want.
   - `checkfe.py` clean (966/966 sc-if, 373/373 sc-for, 3028/3028 div, 850 class members) after the
     wording rename; unchanged after the mandatories work (no new sc-if/markup, backend + a few JS lines
     only).

7. Built the per-idea Onground Adjust (user's explicit "go ahead"), then started the deferred list:
   - New `producers.adjust_activation_idea(idea, note, house, exec_brief, platform, plan)` — the
     structured-card twin of `sharpen_idea`, same venues-aware prompt shape as `activation_ideas`, but
     revises ONE existing idea dict per a note and returns the same what/who/where/when/how/capture/
     access/risk shape (plus `id`/`source`/`stands_on` carried over, `venue_label`/`venue_trap`
     re-derived only if the venue itself changed) rather than collapsing to a plain string. New route
     `POST /activation-idea-adjust`. Frontend: `onOgAdjustNote`/`adjustOgIdea`, a note+button per idea
     card (same "Adjust — keep everything else the same" pattern as Social/POSM), keyed by the idea's own
     `id` (`og1`/`og2`/`og3` — `activation_ideas()` already assigns these, confirmed by reading its
     output shape before assuming an index-based key was needed).
     **Verified live end-to-end at real API cost** (unavoidable — the refusal-path branches were checked
     free via direct Python first): generated 3 Ganeshotsav RWA ideas, typed "make the capture a QR code
     scan instead of a logged sign-up sheet" on "The Dawn Glass Board" card, clicked Adjust — the card's
     Capture field updated to describe the QR flow while name/venue/who/where/when/how/risk stayed the
     original text. Confirms the shape-preservation actually works, not just the route wiring.
   - Video's six-entry-point grounding audit (deferred item, now done) — `grep -n "screen:'video'"` found
     the same class of gap Social's audit found earlier: 6 direct `setState({screen:'video',...})` sites
     that bypass `go()`'s dispatch table (the only place `loadGrounding`/`loadVideoStandsOn` were wired).
     Fixed all 6: `activate('video')`'s Launcher branch, `goVideoTab`, `handoffShots`, `openApprovedRef`,
     `openVideoFromCampaign`, and `ideaGoTo`'s video branch. Not live-tested individually (six low-risk,
     identical two-line additions) — `checkfe.py` clean throughout.
   - Threaded `force_typed`/`skip_mandatories` into `reworkPosts`/`adjustPost` (previously neither Social
     rework path sent either flag at all, confirmed by reading the code before this round claimed it was
     "not yet threaded" — now fixed). Added a shared `socialNoTrio()` method (the same no-plan/no-brief/
     no-idea-applies check `generateSocial` computed inline) so all three call sites — generate, bulk
     rework, per-post adjust — compute it fresh and identically rather than duplicating or drifting.
   - `checkfe.py` clean throughout (967/967 sc-if, 373/373 sc-for, 3030/3030 div, 853 class members).
     Fresh server restart confirmed picking up all backend changes (producers.py/main.py/complete.py/
     prompts.py/brandprofile.py) — `preview_start` with `reused:false` gave a clean process, not a stale
     hot-reload.

## Round 92, continued (7 Sep): architecture review, then public landing page + real login enforcement

Spent a session segment on a pure architecture/product-strategy review (no code): multi-company/multi-
brand/multi-user readiness, how brand info actually flows to each producer, and a full technical +
business-model assessment, published as an Artifact ("Scale-Up Blueprint" — link in that conversation,
not repeated here since Artifacts aren't filesystem paths). Key evidenced findings from that review,
useful to remember even without re-reading the artifact:
- `STUDIO_TENANT` resolves once per PROCESS (`tenancy.py`), not per-request — one deployment = one company.
- Brand isolation within a tenant is a filtered `brand` string field, not structural like tenant scoping;
  the "active brand" fallback in `brandprofile.resolve()`/`set_active()` is a single global flag, shared
  by every concurrent user — a real correctness risk under concurrent multi-brand use, not just a speed one.
- Of 274 total routes, only ~10 required login (`current_user`) before this round's fix below.
- `producers.py` (POSM/Onground) never calls `brandprofile.voice_block()`/`resolve()` at all — confirmed
  via grep — so brand facts not also captured in the House (avoid-list, mandatories, competitors, price
  tier) never reach POSM/Onground prompts, unlike Social/Video which get the full brand block via
  `system_for()`.
- `complete.py`'s `/complete` route (Social/Video's path) has NO try/except around the Anthropic call and
  no global exception handler anywhere in the app — a rate-limit/timeout/overload error propagates as a
  raw failure, no retry/backoff. POSM/Onground's `jsonout.ask_json()` path is more resilient (catches and
  degrades to placeholder) but still has zero retry for provider-side errors specifically (only retries
  on "JSON didn't parse").
- Single uvicorn worker, sync Anthropic client everywhere (0 uses of AsyncAnthropic), no task queue, no
  CDN/object storage for generated media, no persistent disk in the one `render.yaml` deploy config on
  file — sized for one team at a time, not concurrent multi-tenant traffic.

**Then, acted on directly** (the user's own instruction: "the current portal... should be accessible
only after the authorised login" + "a page which opens up once you have opened themarketing-studio.com"):

- **New `api/static/landing.html`** — a real public marketing/features page (hero, the 5-step spine,
  feature grid, the 4 producers, the approval-hierarchy visual, closing CTA), on-brand with the app's
  own palette (`#17325E` navy / `#F7F5F1` paper / Epilogue font). Served at `/`.
- **Studio moved from `/` to `/app`** — same `index()` function, new path.
- **`RequireLoginMiddleware` added** (`main.py`, right after CORS) — the direct fix for the ~10-of-274
  gap the architecture review had just found. Default-deny: every route needs a valid `studio_session`
  cookie (validated directly against the `Session`/`User` SQL tables via a fresh `SessionLocal()`, the
  same check `current_user` already did) EXCEPT an explicit allowlist (`/`, `/app`, `/health`, `/login`,
  `/logout`, `/me`, `/support.js`, `/image-slot.js`, `/docs`, `/redoc`, `/openapi.json`, `/assets/*`,
  `/static/*`). HTML navigations without a session redirect to `/app`, whose own pre-existing
  `checkSession()`/`authOut` gate takes over; API-style calls get the standard `{"detail":...}` 401 shape.
- **A false alarm caught and corrected during verification, worth remembering as a tooling lesson**:
  `get_page_text` showed full Home-screen content even when signed out, which first read as "the
  frontend's login gate doesn't actually block anything." Didn't trust that — checked properly instead:
  the `authOut` overlay IS a genuine `position:fixed; inset:0; z-index:900` full-viewport gate (confirmed
  via `getComputedStyle`, not assumed) — `get_page_text` simply extracts all DOM text regardless of
  z-index/visual stacking, so it cannot be used to judge whether a modal/overlay gate is actually
  working. **New lesson for the memory system**: for anything that gates content behind a fixed-position
  overlay (modals, auth gates, paywalls), verify via computed style / `read_page` accessibility semantics
  or a screenshot — never via `get_page_text` alone, which is blind to visual stacking.
- Confirmed the full real flow: created a real session row for `puneet` directly in the DB, confirmed
  the gate correctly disappeared and the studio unlocked, then deleted that test session. 4 real user
  accounts already existed (`puneet`, `ravi`, `meera`, `ananya` — the same approval-hierarchy people from
  earlier this session) — login itself wasn't rebuilt, only actually enforced for the first time.
- **Not done / explicitly scoped out**: `/brand-brief-builder` and `/builder` (standalone intake UIs)
  were NOT added to the public allowlist — they now require login too, by default-deny, since it wasn't
  clear whether they're meant for external non-studio-user intake. Flag to the user if that's wrong.
  `/docs`/`/redoc`/`/openapi.json` left public (dev convenience, exposes route shapes not tenant data) —
  a judgment call, not a settled decision — worth a second look before any real production deploy.
- `py_compile` clean on `main.py`. `app.dc.html` untouched this round (no `checkfe.py` needed).
