# Nuance layer: plan v2 (8 Oct 2026, DRAFT for the owner's approval; nothing built)

Follows `BRAND_AGNOSTIC_AUDIT_OTHER_SURFACES.md` and `VIDEO_BRAND_AGNOSTIC_AUDIT.md`. v2 replaces v1 (a separate "Nuance Read") after the owner's 8 Oct answers.

## Owner's decisions so far
1. Nuance is per brand x line x audience x place, never per category family (dairy is family; ice cream or a dairy beverage can be family OR individual; high-protein is an individual; cement can be family with a man leading, or an individual man). The model must pick this up when a brand or category comes in.
2. Hand-written content is welcome as experiment; the model must learn nuance itself from brand, category, geography and audience.
3. Dated Indian benchmarks stay as sourced estimates. India only for now, with a key for a second market.
4. **No new "Nuance" section.** Capture everything the dairy-level prompts need as **questions and answers in the brand profile**. The same audience answers are asked at the **Brief** (where the audience is named) and carry forward into the Plan and the producers.
5. The model may draw on **uploaded research and web research**.
6. Yes to an owner-run live seed for Heritage before any dairy text is removed.
7. Audience level: on the **Plan's audience rows**, not the messaging house.

## The design in one paragraph
The profile form already is a question-and-answer list (`brandprofile.SPEC`: 29 questions, each with `ask`, `why`, `unlocks`, `derives_from`; the page renders it from data and already has Accept/Dismiss for suggested answers). We add the questions the dairy-level prompts silently depend on. For each, the model can **suggest** an answer (from the profile, uploaded research and later web research, tagged with its basis); the person accepts, edits or leaves it empty. **A suggestion is never used in generation; only an answered question is.** That one rule replaces v1's "approved read" and its extra store, history, hash and section. Each answered question then becomes a labelled constraint line in `voice_block` (the way the category-aware half already works), and the module-specific machinery (Sales channels, Onground venues, POSM formats) selects from the answers instead of from fixed lists.

## What the dairy-level prompts depend on, as questions
Each row says what it replaces in code today. "New" means not yet in `SPEC`. Group names become new `unlocks` groups so the form stays tiered (core first, the rest behind the break).

| Group | Question (plain words) | Status | Replaces today's... |
|---|---|---|---|
| **How the product is shown** | When someone uses it, what do they physically do with it (pour, apply, wear, install, eat)? | new | Carousel rule "handled like a small pack of milk", "pouring" patterns in `packscene` |
| | What must be visible in a photograph for it to look real and right? | new | "describe enough visible milk in the glass" |
| | Does a pack, bottle or label normally appear in the work: always / only when in use / rarely / not a packed product? | new | `packscene` rules, "no packaging in frame", Social pack rules |
| | What kind of imagery does the category use (food-lifestyle, product-led, fashion editorial, documentary)? | new | hardcoded food-photography prompt, "Indian storybook" animation |
| **Who buys and uses it** | Is it bought for a household or for one person? Who leads? | new (brand default; overridden per audience) | `decider/payer/user` kept; unit and lead added |
| | Product lines: each line with who uses it, how it is bought, where sold, how it is used | new (rows) | the single `hero_product` |
| **Where it is sold and met** | Routes to market, with a rough share of sales each | new (rows; extends `channels`) | fixed `sales.CHANNELS` (kirana, wholesale, q-comm...) |
| | Where do people meet the brand in person? | new (list) | the fixed 11 `producers.VENUES` |
| | Typical trade margin and credit terms in this category | new (sourced estimate) | ROI and listing-cost tables in `sales.py` |
| **Proof and marks** | Which marks, licence numbers or declarations must appear on pack and in print? | new | POSM "Veg mark, FSSAI, licence number" band |
| | What is the worst public event in this category (recall, failed test, adverse reaction) and who acts? | new | the dairy recall framework in `pr.py` |
| **Place** | For each state it sells in: how people there buy, use and talk about it; language register; local festivals and seasons | new (rows keyed by state) | "Pongal/Sankranti" texture, "write for the place's own idiom" |
| | Language mix for copy and voice-over | new | "English + Hinglish" |
| **Look and sound of the work** | Who and where do we show (people, homes, sites, shops)? | new | "Authentic Indian family setting", "real Indian location" |
| | What does the brand sound like (music, voice accent, pace)? | new | "Gentle Indian flute", Telugu-accented default voice, dairy music prompt |
| **Occasions** | Calendar moments that matter, by place | extends `entry_points` | stray Diwali/Sankranti examples |

**Per audience** (asked at the Brief where `targetAudience` is written, then carried on each Plan audience row and each execution): household or one person; who leads; who decides, pays and uses; age and life stage; which product line it is for. Today the Brief's `targetAudience` is free text and the Plan's audience rows (`audience, rank, believes_now, pillar`) are generated from it by the model, so there is no structured link. Adding structured columns links them.

Existing answers stay and are used as they are: category, category axis, market, purchase cycle, decider/payer/user, channels, cheap alternative, price tier, regulator, claims, competitors, tone, mandatories, avoid, states, languages, entry points, notes, packs.

## How an answer reaches a prompt
- **Brand-level answers** become labelled lines in `voice_block` ("HOW IT IS HANDLED AND SHOWN:", "WHAT MUST BE VISIBLE:", "PLACE, Telangana:", ...), so every one of the ~15 call sites gets them without per-module edits. Lines must never start with `TONE:` or `MANDATORY ON EVERY PIECE:` (the page edits those lines by prefix).
- **Audience answers** reach the producers through the execution block that already says "WRITE FOR THIS AUDIENCE, AND NO OTHER".
- **Selectors:** Sales shows only the channels in the routes answer; Onground offers only the meeting points answered; POSM takes its mandatory band from the marks answer; the dairy recall text stays as a sourced reference the PR answer cites.
- **Provocation mode** demotes the "how it is shown" and "look" answers the way it already demotes TONE and the tagline.

## How the model "learns" (the suggestion step)
- A new route drafts suggestions for the unanswered questions from: the profile, the brief, uploaded research (already ingestible), competitor evidence, and later web research.
- Each suggestion carries its **basis** (profile, uploaded research, web with source, model knowledge) and what the model could not know.
- The owner's family/individual examples become the acceptance test. The hand-written experimental answers for the four categories are used only as shape examples inside the suggestion prompt, always from a different category than the brand's, so they cannot leak into creative.
- **Web research is a new capability.** The backend has no web search today. It needs the API's web search tool (availability and cost on this account unverified), citations stored with the suggestion, and the same timeout care as `/research-ingest`. Planned as its own phase after the core.

## Phases (summary only; the Build plan at the end of this file is the working version)
0. **Questions and rendering.** Add the questions to `SPEC` in groups; fold the answers into `voice_block` as constraint lines. No selector changes yet. Heritage's answers are filled by the owner-run seed from today's dairy text.
1. **Prove it.** Suggest answers for Sthir, Kumkum and Loomwell and the owner's family/individual cases; the owner judges. **Needs real model calls and the owner's go-ahead.** Check that Heritage's prompts, rebuilt from its answers, contain every dairy-level behaviour in the table (a checklist test).
2. **Wire the rest of the call sites**, including Brief (`brief_ai` reads no profile today) and PR (reads `brand_core` directly).
3. **Retire the hardcoded content**, one surface per commit, probe-checked with all four brands. The dairy text comes out only after Heritage's answers are on live.
4. **Audience answers:** Brief form, `briefstore.CANON`, new Plan audience columns, execution block.
5. **Selectors:** Sales channels, Onground venues and POSM formats driven by the answers; new archetypes (dealer point, site, store, pharmacy, salon). Sales has fixed screens (`SE_TABS`), so cement dealer credit and apparel own-store channels need a screen change and a Design handover.
6. **Web research suggestions.**
7. **Guard:** grow the probe into a test that no surface carries another brand's markers.

## Blast-radius sweep (8 Oct; method: grep of every caller and sibling plus code read; nothing run against a model; live data not checked)
Still true from v1 and unchanged:
- `voice_block` has about 15 prompt call sites in 11 modules, and nine `main.py` routes return it. Paths that bypass it: `pr.py` (reads `brand_core` directly), `brief_ai.py` (imports `brandprofile` nowhere), and `brandbrief`/`socialplan`/`mediaplan`/`pr` read states and languages only.
- The page splices the same voice text into about 10 client-built prompts (`brandPreamble`) and edits it by line prefix.
- **`brandprofile.resolve()` falls back** to the only or active profile when a name does not match exactly, the known cause of cross-brand leaks. A brand-level answer reaches generation through the resolved profile, so a fallback attaches another brand's answers. The audience columns key by id and the profile lookup needs a "matched or fell back" signal.
- No staleness signature includes the profile today (`strategy.signature`, `ideas.platform_signature`, `plan.house_fingerprint`, `execution.stale_because`). Changed answers will not flag anything stale; that matches how the profile behaves now.
- Geo inputs are mostly empty: in the dev tenant only Heritage has `states` and `languages`. **The live Heritage profile is unverified** and the owner should check "Where it actually sells" on the live profile screen.
- The page hardcodes "Heritage" in export filenames and titles (`downloadScriptWord`, `downloadProductionBible`, `downloadBriefWord`), gives every brand a Telugu-accented default voice (`state.production.voice`, `voiceAccent`), says "could be any dairy brand" in `socialGrounding`, and has "Gentle Indian flute" in `musicChips`. All Phase 3 page edits.
- `app.dc.html` edits need the merge-never-replace discipline, `checkfe.py`, `partials.py verify`, a reload and a real-page check; the file stays LF-only.
- Live ordering: the owner-run seed on live comes BEFORE the dairy text is removed. Never seed Heritage from code at startup (that puts a brand back in code).
- A full suggestion in one model call can approach the Cloudflare timeout that already produced a 524 on a large brief: suggest per group, and detect `max_tokens` truncation.
- Tests that pin text we remove: `tools/test_pack_choice.py`, `test_video_agnostic.py`, `test_provocation_gen.py`, `test_provocation_complete.py`, `api/tests/test_made.py`.
- New routes are protected by default (`RequireLoginMiddleware`); Word exports carry the brand name and logo, not the voice text.

Changed by v2 (shrinks):
- **No separate store, no `tenancy.KINDS` addition, no history or hash, no `bfNuance*` state in five places, no new section.** Answers live in the profile record via `put()`, which already merges only whitelisted fields; new fields go in `FIELDS`/`LIST_FIELDS`/`ROW_FIELDS`. The page renders `text`, `textarea`, `list`, `choice` and `rows` questions from `SPEC` with no change (rows render as plain cells; only the `claims` rows carry special proof wording).
- **New cost:** the profile grows from 29 to about 45 questions. Mitigation: tiered display (core first), suggestions pre-filled so the person confirms rather than types, and group completeness chips (already exist).
- `/brands` and every save route return the whole record plus voice on each call. New answers add to that payload. Keep answers short, and keep long suggestions out of the record (suggestions are not stored).

New from the audience step (Phase 4):
- Plan audience columns are iterated by `execution.stale_because`, so adding columns changes what counts as drifted (good, but must be tested), and they also touch `docs.py`'s plan export, the Plan screen table and the audiences prompt in `plan.py`. Also `briefstore.CANON` and the Brief screen for the questions at the point the audience is named.

## Open items for the owner
1. **Product line representation: DECIDED (8 Oct), option a.** A "Product lines" rows question on the profile; a Plan audience row names the line it is for.
2. Confirm the question list above, or strike or add questions, before it is built.
3. Verify the live Heritage `states` and `languages`.
4. Go-ahead for the Phase 1 real-model test.

---

# BUILD PLAN (8 Oct 2026): the working version, in the order of the agreed working agreement

Assumptions: the question table above stands as drafted unless the owner strikes or adds (item 2 is still open); product lines = option a (decided); web research is a late step; every step is its own commit, verified locally then live, and independently revertible. Sizes: S small, M medium, L large.

## Where the questions go (exact shape, so nothing is guessed at build time)
Seeded into `brandprofile.py`, all optional (none `required`, so `CORE` and every existing brand's completeness are unchanged):
- `FIELDS` (+8): `product_in_use`, `pack_in_scene` (choice), `imagery_style`, `buying_unit` (choice: a household / one person / either), `worst_case`, `language_mix`, `people_setting`, `sound_world`.
- `LIST_FIELDS` (+3): `must_show`, `meeting_points`, `statutory_marks`.
- `ROW_FIELDS` (+5), each with `cols`: `lines` [line, who_uses, who_decides_pays, how_bought, where_sold, how_used]; `routes` [route, share_of_sales, who_buys_there]; `trade_terms` [term, value, source]; `place_notes` [state, how_people_buy_use, register, festivals_seasons, references]; `calendar_moments` [moment, when, where_it_matters].
- `SETUP_GROUPS` (+4 `unlocks` names): "How the product is shown", "Who buys it and where it is met", "Place and occasions", "Look and sound". `place_notes.state` is normalised to the `geo` state code in `put()` (unresolved kept, as `states` does).

## Step 0: baseline and preconditions (no code change) | S
- Owner: confirm the question table; check the live Heritage `states` and `languages`; say go or no-go for the real-model test (Step 4).
- Me: snapshot `api/tenants/` before the first manual test; capture the **golden prompts**: Heritage's and the three other dev brands' real prompts for every surface (the existing probe, extended to save text). These are the "before" for every later comparison.

## Step 1: the questions, stored and shown, nothing consumed yet | S-M
- Change: add the fields above to `FIELDS`/`LIST_FIELDS`/`ROW_FIELDS`/`SPEC`/`SETUP_GROUPS`; state-code normalisation in `put()`.
- Why first: it changes no output, because `voice_block` does not read the new fields yet.
- Not touched: `voice_block`, every producer, the page.
- Verify local: new `tools/test_nuance_questions.py` (round-trip save and load, rows keep their cols, unknown keys ignored, `setup_view` groups, `/brand-fields` shape); `voice_block` output **byte-identical** to the golden files for all four brands; then load the profile screen in the browser, confirm the new questions render, save and reload, and check the "needed answers" count is unchanged.
- Verify live: `/selfcheck` commit matches; the owner opens the profile screen and sees the new groups.
- Rollback: revert the commit (stored extra keys are ignored by `put()`).

## Step 2: answers become prompt lines | M
- Change: `voice_block` renders each answered question as one labelled line after the existing category-aware half, and a compact product-lines line. Per-state place notes appear as one short line per state (capped), with the full note pulled by a new `brandprofile.place_for(b, state_codes)` into `prompts._execution_block` and `producers._ctx` for the piece's priority geography. Lines are labelled so a provocation can demote the "house style" group (a `convention=False` option server-side; a prefix filter in `brandPreamble`).
- Rules: no line starts with `TONE:` or `MANDATORY ON EVERY PIECE:`; empty answers produce nothing.
- Not touched: the ~15 call sites (they inherit), any hardcoded dairy text yet.
- Verify local: tests that (a) a brand with no answers is byte-identical to golden, (b) answered questions appear exactly once, (c) `film=True`, `voice_block(None)` and the page's line surgery are unaffected, (d) General/Independent mode carries nothing, (e) a fallback-resolved profile does not leak another brand's answers; `selfcheck.py`; `smoke.py`; `checkfe.py` for the one `brandPreamble` edit; browser check of the "what the model is told" panel.
- Verify live: that panel for a brand with answers shows the new lines and a sane character count. **Not coverable live without a login: real model output.**
- Rollback: revert; no data change.

## Step 3: Heritage's answers, and the owner-run live seed | M
- Change: I draft Heritage's answers from the dairy text now in the code (the owner reviews every line). A login-protected import route fills only the EMPTY questions of a named brand from a reviewed JSON file, once. No Heritage text is placed in code paths.
- Verify local: import into the dev Heritage; the **Heritage checklist test** passes: rebuilt prompts contain every dairy-level behaviour in the table above (product handling, visible-milk rule, pack-in-use, kirana and route set, venue set, marks band, place texture, language mix, sound world, occasions).
- Verify live: the owner runs the import once, opens the panel, and sees the lines.
- Gate: nothing in Step 5 deploys to live until this has run on live.
- Rollback: the answers are ordinary editable profile fields.

## Step 4: suggestions, and the real-model test (gate) | M-L
- Change: `POST /brand-suggest` drafts answers for unanswered questions, one model call per group (Cloudflare timeout, truncation detected, failures logged and surfaced), returns `{value, basis, unknowns}` per question, **stores nothing**. One page change: a "Suggest answers" button per group that feeds the existing suggestion Accept/Dismiss. Rows suggestions need the existing `acceptSuggestion` checked for rows (a known unknown).
- Inputs: the profile, brief and house text, uploaded research (already ingestible), competitor evidence. The suggestion prompt carries category-agnostic instructions and never the brand's own category's examples.
- **Gate (owner go-ahead needed):** real model calls for Sthir, Kumkum, Loomwell and the owner's family-versus-individual cases (family milk; ice cream individual versus family; high-protein for a man and for a woman; cement family-led versus individual man). The owner judges. Nothing else proceeds until the suggestions are good enough, and the prompt (not the wiring) is what gets iterated.
- Rollback: revert.

## Step 5: retire the hardcoded content, one surface per commit | L (many small commits)
Order by risk, easiest first. Each commit: the hardcoded text is removed or reads the answers; an empty answer produces nothing (neutral), never dairy; the probe over all four dev brands must show no other brand's markers; the Heritage checklist must still pass; the matching test is updated in the same commit.
1. Carousel milk rules, `packscene` patterns, Social pack rules → product handling, must-show, pack-in-scene answers.
2. Idea and Campaign exemplars; Brief worked examples and template values; brief-format defaults → neutral wording.
3. Video: clip/still/animation/music prompts and the page defaults (Telugu-accented voice, Indian accent, "English + Hinglish", music chips) → imagery, people-and-setting, sound-world, language-mix answers.
4. POSM: the "Indian FMCG" opener, the mandatory band, the retail formats → marks and routes answers.
5. Onground: "in India" (four prompts), "real Indian location", leave-behind sizes → market from profile; meeting-points answer.
6. Page strings: export filenames and titles ("Heritage"), `socialGrounding`, sample data labels.
7. The seeded Heritage profile for new tenants → start empty.
- Live ordering: Step 3 must already be on live. After each deploy the owner checks one real generation for Heritage.

## Step 6: wire the paths that bypass `voice_block` | M
- `pr.py` (place, marks, worst-case into the release and crisis prompts; the recall framework text stays as a cited reference); `socialplan`/`mediaplan` use place notes; **Brief (`brief_ai.py`) gets the profile at all.** The last item changes Brief output for every brand and corrects the "Grounded" banner that today overclaims. **It is a behaviour change that needs the owner's explicit OK when we reach it.**

## Step 7: audience answers at the Brief, carried through | L
- Change: structured audience questions where `targetAudience` is written (household or one person; who leads; who decides, pays, uses; age and life stage; which product line); new columns on the Plan's audience rows; `briefstore.CANON`; the audiences prompt in `plan.py`; the execution block's "WRITE FOR THIS AUDIENCE" line; `execution.stale_because` (new columns join the drift check); the plan export in `docs.py`; the Plan screen table.
- Verify: with live-shaped data (empty overrides, only the seeded brand), an execution built from an audience row carries its answers into a producer prompt; an old plan with no new columns behaves as before.
- Page work: Brief screen and Plan screen edits; Design's next round must be based on ours (merge-never-replace).

## Step 8: selectors | L (partly a Design handover)
- Sales shows only the channels in the routes answer; Onground offers only the meeting points answered; new archetypes (dealer point, site, store, pharmacy, salon) with footfall and permission rows; Sales has fixed screens (`SE_TABS`), so cement dealer credit and apparel own-store channels need a screen change. Scope this step with the owner when reached.

## Step 9: web research suggestions | M
- Add the API's web search tool to the suggestion step, with sources stored beside each suggestion. Availability and cost on this account unverified; check first.

## Step 10: guard and record | S
- Fold the probe into `tools/` as a surfaces guard over the four brands (fails if any surface carries another brand's markers); add the lessons to `CLAUDE.md`; update memory and the testing log.

## Checks run on every step (the working agreement)
`py_compile`, `selfcheck.py` (call signatures), `smoke.py` (boots the committed tree), `checkfe.py` and `partials.py verify` for any page edit, the full test suite, a tenant-snapshot compare (tests must not leave real files), a browser check of the real page, push, wait for the Render deploy, `/selfcheck` commit match, Render log scan for 5xx. Said plainly after each: what live could not cover (login-gated screens, real model output).

## Order of work and what can wait
Steps 0 to 3 first (nothing visible changes except Heritage's panel); Step 4 is the gate; Step 5 then removes the hardcoding; Steps 6 to 8 add reach; 9 and 10 close. If time is short, stop after Step 5: every surface is then free of Heritage text and driven by answers.

## What I need from the owner, by step
- Step 0: the question table (strike or add), the live Heritage states and languages, go or no-go for Step 4.
- Step 3: review of Heritage's drafted answers; run the one-time import on live.
- Step 4: judge the real-model suggestions.
- Step 6: yes or no on grounding Brief in the profile.
- Step 8: scope for Sales and Onground channels.
