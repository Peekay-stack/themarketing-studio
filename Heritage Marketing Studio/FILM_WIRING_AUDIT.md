# Video tab — wiring, blast-radius and staleness audit (28 Oct 2026)

Scope: **everything on branch `coverage` that is not on master** — 60+ commits from 27 Oct 14:22 to 28 Oct 15:26 (coverage + the five film-craft slices, the pipeline map, the film builder S0–S7 incl. take QC / chain / retention, the engagement levers). 56 files, +10.6k / −137 lines before this audit's own fixes. Live = master `b1519e6`.
Method: git diff mapped to code members; route-table diff master↔coverage; real-page runs with the network stubbed; a round-trip of every new persisted field through the real film store; a scan of the **real tenant** for every store that references generated files; a trial merge into master; the full suites. Nothing here was run in a signed-in session (I cannot sign in) and nothing real was deleted.

## 1. Verdict

| Question | Answer |
|---|---|
| Is the rest of the app wired correctly after these changes? | **Yes.** 30 screens load with content and **0 runtime errors** (all producer tabs, the four video sub-tabs, the film steps, Memory, approvals, campaigns, IMC…). 17 Python suites (574 checks), `test_tools` 18/18, selfcheck 1,498 calls / 0 problems, golden prompts 75 unchanged / 0 changed, `checkfe`, partials round-trip, smoke on the committed tree: all green. |
| Did I find defects? | **Yes, 3 real defects (all in code written this session or the day before) + 1 stale-text finding. All fixed and pinned by tests** — section 3. |
| Did anything outside the video tab change? | **No behaviour change.** Outside video code only additive `videoBuilder:null` resets and the autosave signature were touched (section 2). |
| Is it safe to merge to master? | **Not yet, by the owner's own rule** (localhost sign-off first). Mechanically: **2 conflicts, both from the stitch hotfix existing twice**; resolved by taking `coverage`'s version, the merged tree passed every suite (section 7). |
| What is still unverified? | A real signed-in assemble / purge / Promote to Final; a chained clip from the real engine; spend vs Google billing (section 6). |

## 2. Blast radius: what changed and who depends on it

| Area | Change | Depends on it / blast radius | Checked by |
|---|---|---|---|
| `app.dc.html` (31.4k lines, LF) | 98 hunks, +1,719 / −114. **All in video code**: `renderVals` bag (24), `frameBody`/`generateFrame`/`renderFrameResult`/`frameRecipe`/`frameIsStale` (coverage, signature now `(idx, k=0)`), `produceVideo`/`filmRenderBody`/`renderViaJob`, `startCutFromFilm`/`renderCut` (Edit room), the new Shots-step and craft panels | Storyboard, Shoot Board, Production, Edit room all read `sceneFrames` / `fullScript`; every frame render site | `checkfe` (471 template handlers reach the bag), 8 page-check suites, 30-screen smoke |
| Non-video members touched | `applyImport`, `setProducerBrandMode`, `setEngine`, `pickCastOption`, `openVideoFromCampaign`, `componentDidUpdate`: only an added `videoBuilder:null` in an existing reset, and `videoBuilder` in the autosave signature | Brand switch, engine switch, cast lock, campaign hand-off, autosave | Diff read line by line; `builder_state_leaks` |
| `main.py` (CRLF) | +10 routes: `/take-check`, `/take-look`, `/media-usage`, `/media-purge`, `/scene-shots`, `/film-direct`, `/film-review`, `/frame-check`, `/editor-notes`, `/pace-suggest`. `_produce_video_sync` gained 5 inert keys (`only_shot`, `use_clips`, `chain_from`, `chain_from_at`, `chain_beats`) | Every caller of `/produce-video` (3 callers of `renderViaJob`: the clip take, the full render / assemble, the cutdown render): none sends the new keys except the builder's own calls | route-table diff (321 → 331, **0 removed, 0 duplicates**); selfcheck; the golden planner snapshot byte-identical |
| New modules | `takes.py`, `takeqa.py`, `mediapurge.py`, `sceneshots.py`, `flowreview.py`, `framecheck.py` | Pure / read-only except `mediapurge` (deletes on request) | 574 Python checks |
| `filmscript.py` | `video_builder`, `video_pace`, `video_beat_map` fields | Every film save/load | round-trip test (section 5) |
| `filmcut.py` (CRLF) | `trim_window`, `last_frame`, `frozen_join`, `_join_filter`, mixed-size join | Every stitch (a normal render too) | `test_stitch_freeze`, builder suites, real-clip regression |

## 3. Defects found and fixed

| # | Defect | How it was found | Impact before the fix | Fix | Pinned by |
|---|---|---|---|---|---|
| 1 | **The storage purge could delete a clip a saved Edit-room cut plays.** The server only protected what saved *films* use; the Edit room's `cuts` store names every beat's `clip_url`. | Scanned the real tenant for every store referencing generated files: `cuts` names **6 clips of your real film**; a dry run showed all 6 would have been removed | A later "Remove unchosen" could break a saved cut of your film (silently, until you opened it) | `mediapurge.in_use` also reads the cuts folder (`also_dirs`); the route passes it; the skip reason names it. Dry run on the real data now removes **0 of the 6** | `test_mediapurge` (3 new checks), real-tenant dry run |
| 2 | **Chain continued from the end of the *file*, not from what was on screen.** A trim, or a 2 s shot cut from the engine's 3 s minimum clip, means the file's last frame was never shown. Two of my own slices (S2a trim × S4a chain) interacted. | Reasoning about the interaction of slices, then confirmed in the code (`last_frame` took the file's end) | Every short chained shot started ~1 s *after* the previous picture; a trimmed clip continued from a cut-off moment | `chain_from_at` (backend `last_frame(at)`; frontend `chainAt()` uses the same rule as the preview player: trim start + the shorter of the window and the planned seconds); the take records `chain_at`; a change of trim marks the chained take "older clip" | `test_builder_s4` (+10), `builder_chain` (+7) |
| 3 | **Per-film transient state leaked between films.** The Continue ticks, the compare mode and the open preview survived a new objective, a brand-mode switch, an image-engine change and a cast re-lock (the builder was wiped, they were not) and could act on the next film's shots. | Drove each wipe path on the real page and read what survived | A stale compare auto-playing, or a pre-ticked Continue, on a different film | One choke point in `componentDidUpdate` (it tracks `_hadBuilder` itself: **this app's wrapper calls it with no arguments**, my first attempt failed for that reason) + the film loader | `builder_state_leaks` (8) |
| 4 | **Stale text.** "29 Oct" written in 12 files and 12 memory lines (today is 28 Oct; system clock and every commit agree); "nothing built" headers on the plan and the map; the plan's decisions section unanswered; a code comment saying trims/budget "come later"; three "Not in this slice" lines naming slices that are built | grep + reading | Misleads the next reader/session | All corrected; the handoff memory rewritten | grep shows 0 remaining |

## 4. Wiring map

**Backward — what feeds the Shots tab:**

| Upstream | What the tab takes from it | Wiring | Status |
|---|---|---|---|
| Concept (`generateVideo`) | `videoConcept`, now with hook / surprise / turn / memorable | Saved whole; handed to the script writer only when present | Clean (older films unchanged: tested) |
| Script (`fullScript`) | rows, `tc`, shots, `no`, `match_no` | Frame keys are positions; reorder re-keys frames + all five builder maps + sound plan + `match_no` in one `setState` | Clean (18-check invariants incl. exact round trip) |
| Approve + cast lock + engine/style | `castRefUrl`, `sceneFrames` | ~15 sites wipe `videoBuilder` when these change (now also the transients) | Clean after fix 3 |
| Frames (`/scene-still`) | each render is a *take*; `sceneFrames[key]` mirrors the chosen one | S1a; nothing downstream changed | Clean |
| Craft panels (pace, director's read, shot plan, flow review, frame check, editor's notes) | Skip, the shot list, boredom risk | Advisory; cleared by a scene move (order-derived) | Clean |

**Forward — what consumes the tab's output:**

| Downstream | What it receives | Wiring | Status |
|---|---|---|---|
| `/produce-video` (assemble: `use_clips`) | exactly the chosen clips (+ trim, chain ignored) | Strict (400 naming the shot if one is missing); same stitch, voice, music, mix | Clean |
| Production versions list / `silentMaster` / `prodShotClips` | the assembled film's record | **Same result-handling code as a normal render** (differs only in note and quality label) | Clean |
| Edit room (`startCutFromFilm`, cutdowns, rework, re-score) | `shot_clips` | Same shape; trimmed pieces appear as `trim-*.mp4` | Clean |
| Saved cuts (`cuts` store) | per-beat `clip_url` | Now **protected from the purge** (fix 1) | Fixed |
| Voice windows / captions | each scene's real picture and `tc` | Server re-times by dialogue at render; the page's Timeline / preview use the script's `tc` | **Known difference**: preview/Timeline can differ from the assembled film by that re-timing |
| Film save / autosave | `video_builder`, `video_concept`, `video_beat_map` | Autosave is identity-based on `videoBuilder`; every builder change makes a new object | Clean (round trip below) |
| Made ledger | every scene still, every produced film | A purge leaves ledger rows without their file | Disclosed in the confirm; deliberate |
| Hand-over gate, doc export, library saves | `sceneFrames` | Unchanged contract | Clean (suites) |

## 5. Verified clean (evidence)

| Check | Result |
|---|---|
| Route table master → coverage | 321 → 331; 10 added, **0 removed, 0 duplicates** (also 0 duplicates on the merged tree) |
| Auth on the new routes, unauthenticated | `/media-usage`, `/media-purge`, `/take-check`, `/take-look`, `/produce-video` all **401** |
| Job de-duplication ("identical single-shot request joins the running job") | Keyed on a hash of the **whole** payload, so requests differing only in `chain_from` / `chain_from_at` / `chain_beats` are different jobs |
| Persistence round trip through the real film store (temp folder) | concept's 4 fields, beat map + engagement, take mode / `chain_from` / `chain_at`, `check_accepted` + checks, multi-part beats, trim, budget cap, chosen clip/frame, a frame take's check: **all survive** |
| Backward compatibility of saved films | an older film (no builder, a concept without the 4 fields) loads unchanged; a take saved before chain/checks existed gets safe defaults; a junk builder is cleaned, not stored |
| 30 screens in the real page | all render with content, **0 `error` / `unhandledrejection` events** |
| Page-check suites, run **together in one session** on the final code | reorder 18, preview 14, take QC 19, chain 28, budget/storage 29, state leaks 8, pre-approve 11, concept fields 17 = **144 pass** |
| Python suites | builder s0 45, s2 20, s4 28, take QC 26, purge 23, coverage plan 79, scene shots 101, omni 24, videoprompt 33, packqa 19, stitch freeze 13, film direct 51, flow review 61, frame check 25, film edit 26 = **574**; `test_tools` 18/18; surfaces wiring all behave |
| Backend prompts | `golden_prompts --compare golden_step5`: **75 unchanged, 0 changed** |
| Disk | real tenant media untouched: **665 files before and after** (every delete test ran in temp folders) |

## 6. Staleness register

| Item | State | Action |
|---|---|---|
| Dates "29 Oct" in 12 repo files + memory | **Fixed** (28 Oct) | — |
| `FILM_BUILDER_PLAN.md` / `FILM_PIPELINE_MAP.md` "nothing built" status lines | **Fixed** (status now says what is built, with the audit pointer) | — |
| Plan §12 decisions | **Fixed**: marked as taken from the owner's go-aheads; confirm if any should change | Owner to confirm |
| `app.dc.html` comment "trims, budget come later" | **Fixed** | — |
| `FILM_BUILDER_LOCALHOST_TEST.md` "Not in this slice" naming built slices | **Fixed** | — |
| `budget.spent_usd`, a take's `sig`, `interaction_id`, modes `extend` / `elements` | **Reserved / never written** — documented in the `takes.py` header so nobody mistakes them for live behaviour. Not removed (removal would change the stored shape for no gain). | Revisit at S4b / S8 |
| Next-session handoff + `MEMORY.md` START HERE bullet | **Rewritten** (they described an older branch head and an unresolved hotfix) | — |
| A frame/clip's "out of date" mechanism | Two mechanisms coexist: frame recipe fingerprints (frames) and `frame` / `chain_from` / `chain_at` comparison (clips). The plan's single `sig` was never implemented | Acceptable; documented |
| Live server | Master `b1519e6` — **does not have any of this**, so nothing live is stale or at risk | — |
| Owner's local server | Serves the working tree: **`coverage` must stay checked out**; backend edits need a restart (the audit's backend fixes included) | Restart `run-local.bat` |

## 7. Merge rehearsal (throwaway worktree, nothing pushed)

| Step | Result |
|---|---|
| `git merge coverage` into master | **2 conflicts**: `api/filmcut.py` and `tools/test_stitch_freeze.py` (add/add) — the stitch hotfix is on master as an *earlier copy* (`b1519e6`) of what `coverage` extended (mixed-size joins) |
| Resolution | Take `coverage`'s version of **both** files (it is a strict superset of the hotfix) |
| After resolving | All 13 Python suites + `checkfe` + selfcheck (1,498 / 0) + smoke **pass on the merged tree**; no duplicate routes. (`test_tools`' "every route registered once" needs the tracked-out `.venv`, so it cannot run in a worktree: environment, not a defect.) |

## 8. Residual risks and what is NOT verified

| Risk | Why it remains | Mitigation |
|---|---|---|
| No real signed-in session | I cannot sign in; the new routes are behind login | Owner's localhost click-through (`FILM_BUILDER_LOCALHOST_TEST.md`) |
| A chained clip from the **real engine** is unproven | No paid run yet; only the code path and the extraction are tested | One Draft pair ≈ $0.10–0.25, quote first |
| Spend is an **estimate** (not reconciled with Google billing) | The API's usage block gives tokens, not dollars | Compare the billing page once |
| Purge leaves **Made-ledger entries without their files**; `chain-*.jpg` frames and `trim-*.mp4` assemble pieces accumulate (never purge candidates) | By design (ledger is a record; trim pieces may be in a produced film). Small files | Disclosed in the confirm; revisit if disk matters |
| Preview / Timeline vs the assembled film | Server re-times scenes by dialogue at render | Click-through step 7 of the preview section |
| `/take-look` costs money and has no per-user rate limit | Same as every model route; behind login | Acceptable |
| Reorder side effects | A matched-scene frame may show "out of date"; a pending shot proposal for a moved scene is orphaned | Documented in the plan |
| `test_tools` was flaky twice earlier in the project | Unexplained; **0 sightings during this audit** | Watch |
| `CLAUDE.md` is modified but not by this work | Pre-existing dirty file | Left out of every commit |

## 9. What the audit changed (this commit)

`mediapurge.py` + `main.py` (cuts protection), `filmcut.py` + `main.py` + `takes.py` (chain at the used end), `app.dc.html` (chain-at, transient-state choke point, comment), tests (`test_mediapurge` +3, `test_builder_s4` +10, `builder_chain` +7, new `builder_state_leaks` 8, `film_concept_fields` made order-independent), the date and status corrections, the handoff memory, and this report.
