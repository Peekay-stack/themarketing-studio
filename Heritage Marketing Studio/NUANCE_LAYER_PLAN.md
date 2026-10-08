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

## Phases (each a separate commit; local then live)
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
