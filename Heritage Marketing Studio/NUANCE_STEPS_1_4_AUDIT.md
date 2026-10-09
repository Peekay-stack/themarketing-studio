# Nuance layer, Steps 1 to 4: blast radius and wiring audit (9 Oct 2026)

Scope: what Steps 1 to 4 changed, from the brand profile screen (the changed tab) backwards to what feeds it and forwards to everything that reads it. Method: grep of every caller and sibling, the golden-prompt baseline run with answers applied, the page's own functions run on real answered data in the browser pane (model stubbed, sign-in covered by the stub recipe), and the real routes driven with the page-shaped body on a scratch tenant. Nothing real was written; the real tenant was diffed against a snapshot taken before Step 0 and is identical.

## Verdict
- **Wiring is intact.** Every path I could test works end to end (14 of 14 route checks and every page check I ran, 0 failures; 70 of 70 golden prompts unchanged for unanswered brands).
- **Nothing a user sees today has changed.** No brand has answered any new question on live yet, so no prompt differs from before.
- **The design has costs that start the moment a brand answers**, and one ordering risk before Step 5. They are findings 1 to 3 below, and they need decisions.

## What the four steps changed (footprint)
Backend: `brandprofile.py` (+304: 16 questions, groups, `nuance_lines`, `seed_answers`), new `brand_suggest.py` (+305), `main.py` (+27: one new route, one import, `suggest_groups` on two responses), `prompts.py` and `provocation_gen.py` (one line each: house-style fields blanked in provocation mode). Data: `api/seeds/answers/heritage-foods.json`. Page `app.dc.html` (+63, single-spot edits): `brandPreamble` filter, `asText` for rows, `suggestFrom` label, `white-space` on the suggestion box, the field-row context, the header button and its handler, two state resets. Tools and tests: golden baseline and compare tool, four new test files, the real-model report tool.

## Backwards: what feeds the changed screen
- The form is rendered from `brandprofile.SPEC`, so the 16 questions needed no page change. The page's existing Accept/Dismiss box now carries three sources: derived values (from the brief and house), the reviewed seed file, and model drafts.
- `derivable()` still pre-fills category, market, hero product and competitors from the brief, and master idea, positioning, avoid and claims from the house. The seed keys do not overlap those, so nothing conflicts.
- The model's drafts read the profile, the newest brief for the same brand name (exact match only, so a brief filed under a different name is not seen), and pasted context (the route accepts it; the page has no box for it yet). The drafts need the brand's states: with none listed, place notes are skipped and the reason is shown.
- The seed file is looked up by the slug of the brand name. A renamed brand loses its seed offer. It is tracked in git, is not excluded by `.dockerignore` (which has no JSON or seeds pattern), and the Dockerfile copies the whole folder, so it ships.
- **Unverified:** the live Heritage profile's `states` and `languages`. If empty, Heritage's place notes still show, but a place-notes draft for any brand that has none is skipped.

## Forwards: what reads the answers
`voice_block` is the single carrier. With Heritage's 15 answers accepted, the golden harness shows every surface that calls it gains the same 15 lines as pure insertions (nothing removed):

| Surface | Prompt before | After | Growth |
|---|---|---|---|
| Voice block (what the "model is told" panel shows) | 1,200 | 4,692 | +291% |
| Video system prompt | 4,721 | 8,213 | +73% |
| Social system prompt | 5,300 | 8,792 | +65% |
| POSM | 5,819 | 9,311 | +60% |
| Onground | 7,638 | 11,130 | +45% |
| Idea platform | 8,578 | 12,070 | +40% |
| Messaging house | 9,062 | 12,554 | +38% |
| Carousel | 10,453 | 13,945 | +33% |
| IMC plan | 13,018 | 16,510 | +26% |
| Sales enabler | 18,572 | 22,064 | +18% |
| Campaign draft | 3,923 | 7,415 | +89% |
| **Brief builder** | unchanged | unchanged | does not read the profile |
| **PR** | not captured | not captured | reads `brand_core` and states, not `voice_block` |

- The page splices the same voice text into its client-built prompts (Brief writer, Social, Video script and departments, IMC lead, analytics lead; about ten call sites), so those get the lines too.
- Provocation, film and Independent mode all behave (checked on the real answered text in the page): a provocation drops the tone and the three HOUSE STYLE lines and keeps the factual ones and the mandatories line; a normal film keeps its sign-off handling; an Independent piece carries nothing.
- `/brands` now returns 49 KB for the five dev brands (the voice is sent three times per brand). Fine today; it grows by about 10 KB per answered brand.
- Staleness: no signature includes the profile, so a changed answer flags nothing stale, the same as every other profile field.

## Wiring checks that passed
Page-shaped save through `/brand-fields` (lists as arrays, rows as arrays of dicts, empty product lines); the voice carries the lines in the save response, `/brands` (own, by-name and by-id maps), `/brand/{id}`, `/brand-active` and `/brand-save`; other brands' voices are untouched; the new-brand form shows no suggest groups; an old profile file without any new key still renders; a one-field save leaves every answer alone; groups update after a save. Page: `brandPreamble` on the real answered voice (normal, provocation, film, Independent); the button drafts five groups in order, names a failed group, and lets the others land; drafts show with their basis and unknowns; drafts reset on brand switch and on the new-brand form. Backend: full test suite, `selfcheck` (1,365 calls, 0 problems), `smoke`, `checkfe`, `partials verify`, `contract.py`. Live: commit `a42d8d6` matches, no app errors or tracebacks (the only 502s were during the instance swap).

## Findings, ranked
1. **Strategy surfaces receive production-craft lines they cannot use.** The messaging house, idea platform, campaign, IMC plan and sales prompts now carry "how it is used", "must be visible", "pack in the picture" and "house style", and grow 18 to 89%. That is cost and dilution, not a break. Place, moments, routes and buying unit are useful there; the rest is noise. *Recommended:* give `voice_block` a scope (creative or strategy) so strategy surfaces carry only the strategic subset. Decide before anyone accepts answers on live.
2. **A contradiction window until Step 5.** Non-dairy brands' prompts still contain dairy rules today (checked in the baseline): the cement brand's carousel has the pack-of-milk and glass-of-milk rules, POSM "Indian FMCG retail", Onground and Sales "kirana", ideas and Brief dairy and Parle/Heritage examples. If a cement brand accepts "mixed on site and laid by a mason", that sits beside "handle it like a small pack of milk". For Heritage the answers duplicate the hardcoded rules, which is redundant, not contradictory. *Recommended:* do not accept model drafts for a non-dairy brand into live work until Step 5 retires those rules. Only Heritage exists on live, so exposure today is nil.
3. **Stored and shown, but nothing acts on them yet.** Sales channels, activation venues and footfall, POSM mandatory band and formats, the deterministic pack logic in `packscene`, music and voice pickers, PR's recall text, `trade_terms` and `worst_case`. An answer such as "not a packed product" changes the prompt wording only; the code that attaches packs does not read it. That is Steps 5 to 8.
4. **The new model route is paid and uncapped.** One click is up to five calls with the studio's model; the page blocks a double-click, the server does not rate-limit, and there is no spend cap anywhere (the studio's Phase 4 is still open). It is login-gated.
5. **A pre-existing bug my screen makes more visible.** "Not this" is remembered across brand switches and the new-brand form for the whole session (`bfDismissed` is never reset). Dismiss a suggestion on one brand and the same question's suggestion is hidden on the next. Model drafts clear their own dismissals so they self-heal; the seed offer and the derived suggestions (claims, master idea) do not.
6. **Smaller:** two copies of `asText` in the page (I edited the wrong one first; a second edit was needed); rows columns show raw keys (`who_decides_pays`), as the existing pack-economics rows do; drafts are not stored, so a reload loses them and the next draft costs again; `contract.py` does not cover this form, so my round-trip test is its only coverage; running tests or `smoke` creates empty folders in the dev tenant (harmless, removed).

## Decisions
- Scope `voice_block` for strategy surfaces? (finding 1; I recommend yes, before Step 5)
- Reset "Not this" on brand switch and new-brand form? (finding 5; a one-line, low-risk fix; I recommend yes)
- Hold model drafts for non-dairy brands out of live work until Step 5? (finding 2)
- Add a spend or rate guard on `/brand-suggest` now, or leave it to Phase 4? (finding 4)
- Add a "business or trade buyer" option to the buying-unit question (from the Step 4 run).

---

## Resolution (9 Oct): the owner took the recommendations on all five

1. **Strategy surfaces now carry only the strategic subset.** `voice_block(scope="strategy")` drops the five production-craft labels (`brandprofile.CRAFT_LINE_PREFIXES`). Strategy scope is used by the messaging house, platform ideation and judging, campaign drafting, the IMC plan, the sales sheet, the brief written server-side, and provocation ideation. **Left at the full set on purpose:** the two per-medium expression writers (platform and campaign `write_expressions`), because they feed the producers directly, plus Social, Video, Carousel, POSM, Onground and the cast. The page filters the same five labels for its own brief-writer, IMC-lead and analytics prompts (`brandPreamble(..., strategic)`), and a test fails if the page's list and the server's list drift. Measured with Heritage's 15 answers accepted: house +38% to +18%, idea platform +40% to +19%, campaign +89% to +41%, IMC plan +26% to +12%, sales +18% to +8%; every creative surface unchanged; an unanswered brand unchanged (70 of 70). The "what the model is told" panel still shows the full set.
2. **"Not this" is cleared on brand switch and on the new-brand form** (`bfDismissed`), checked in the real page.
3. **A visible caveat** sits in the button's note: until the studio's built-in dairy rules are removed from its prompts, answers for a non-dairy brand will sit beside them, so accept them only to test. **To remove when Step 5 completes.**
4. **A coarse hourly brake on `/brand-suggest`:** 20 group requests an hour per tenant (`SUGGEST_CALLS_PER_HOUR`), answered with a plain 429 and no model call; the page stops at the first refusal and says why. It is in this process's memory (a restart resets it), so it is a brake, not a spend cap.
5. **A fourth buying-unit option, "a business or trade buyer"**, with its own line ("write to a professional buying for the job or the business...") and the model's draft matched to it. The question wording was widened to say so. The strategy scope keeps this line.

Committed together, not separately, because the edits interleave in `brandprofile.py`, `app.dc.html` and the test files. Verified: full suite, golden 70 of 70, `selfcheck` 1,367 calls, `checkfe`, `partials verify`, the real page (scoped prompts on the real answered voice, the four options, the caveat, the 429 stop, both resets), and the tenant unchanged.

## Follow-up (9 Oct): the wider Heritage market, and the languages box

The owner widened Heritage's market (Karnataka, Tamil Nadu, Mumbai, Pune, Delhi NCR, Haryana) and found the languages list empty. Two gaps showed up and were fixed:

- **Place-note drafts now cover the states that have none yet.** `brand_suggest.uncovered_states` compares the listed states with the rows already answered and the rows in the reviewed starting answers (matched by real state, so a name and a code count the same, and a row naming only a state counts for nothing). The model is asked, and allowed to answer, only for the rest, and it is shown the notes already written. In the page, a place-notes draft combines with the starting rows when nothing is saved yet (one box, "from the reviewed answers file..., plus 5 places with no note yet, drafted by the model...") and is added to saved rows when there are some ("adds to the places you have"), never replacing them and never doubling a place. Before this, the starting answers hid the draft, so Karnataka, Tamil Nadu, Maharashtra, Delhi and Haryana could never have been drafted.
- **The languages box accepts names as well as codes** (`geo.resolve_language`): Telugu, Kannada, Tamil, Marathi, Hindi, English save as te, kn, ta, mr, hi, en, spellings such as Bangla or Oriya resolve, and anything else is kept in `languages_unresolved` rather than dropped. The question says so and shows an example. A test fails if `geo.LANGUAGE_NAMES` and `pr.LANGUAGES` disagree.

Not done, on purpose: Heritage's starting language mix still says "English with Hinglish where natural" (today's behaviour), to be changed once the owner confirms the languages. Cities such as Mumbai and Pune still do not resolve to their state in the states box (the same class of trap; a candidate next fix).
