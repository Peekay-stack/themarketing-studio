# Film builder: consolidated plan after two localhost tests (29 Oct 2026)

Status (end of 29 Oct): **Phases 1-4 are BUILT** on branch `film-engagement-2` (not merged, not live): see sections 9-12 for what was built, what the real model calls showed, and the blast-radius audit. **Phase 5 (optional vision checks) is NOT built**, and sections 3-5 below are the plan as written in the morning. This replaces the need to read three documents: it merges `FILM_LOCALHOST_FINDINGS.md` (rounds 1 and 2), `FILM_BORING_FIX_PLAN.md` (the boring-film diagnosis and slices) and the pending B1-B4. Evidence level per line: *seen* (film or saved data), *code* (source), *inferred*.

## 1. Where things stand

| Group | Items | State |
|---|---|---|
| Round 1 fixes A1-A8 (stale-frame banner/reasons/re-render, filmable concepts, kept decline reason, re-time note, cast-lock wording) | 8 | **Built** on branch `coverage-fixes` (worktree `C:\Users\punie\hms-fixes`), pushed, **not merged, not live. The owner has not tested them**: round 2 ran on `coverage`. Only the A5 prompt has had no real model call. |
| Rendered-film quality B1-B4 | 4 | **Pending**, decided below |
| Boring film (round 2 verdict) | W1-W6 | **Diagnosed, not built** |
| Round 2 loose ends | Shots-step timing, English line, picture 3 | **Open questions** |

## 2. What the two rounds say together (the evidence the plan rests on)

| Pattern | Round 1 | Round 2 | Reading |
|---|---|---|---|
| Frames stale after department notes | yes | yes | Real, repeated. Batch 1 addresses it. |
| Limb / smear defect in a clip | yes (arm across face; smeared pack) | **no** | One film only. That script had no such action in round 2, so this is NOT proof it is gone. |
| Film holds attention | concept good, flow review "medium" | **"boring"** | The generator can produce a clean but dull film. The checks all passed. |
| Rules that exist but are ignored by the writer | scene-5 decline, split-screen turn | VO spine, new place, sign-off payoff | The writer skips prose rules; nothing checks delivery. |
| Ending | smeared pack, walks away | near-still pack, silent tail | The sign-off master is weak both times. |

## 3. Decisions on B1-B4 given the new evidence

| # | Original idea | Recommendation | Why |
|---|---|---|---|
| **B1** Model reads 3 frames of a clip for limb/smear | **Build as an on-demand button** (extend Look), after a 3-call calibration; never automatic | Only a vision read can see a stretched arm; but it defected once in two films and costs one model call per clip. |
| **B2** QC after every normal render | **Split.** (a) FREE checks run automatically after a render: frozen stretch, near-still shots, silent tail, spoken-word count. (b) the vision check becomes an opt-in "Check all clips" with the cost shown | The free half would have caught the round 2 ending and costs nothing; the vision half is B1 at scale. |
| **B3** No arm/hand across a face, no hands at the lens on key shots | **Build now, together with the concept change** | The new "visible reversal" and the earlier "hook = a visible action" rules push the writer toward exactly the risky action that broke round 1. |
| **B4** Keep the pack sharp on the sign-off master | **Build now, folded into the ending slice** | Round 1 smeared; round 2 near-still. One problem: the sign-off master. |

## 4. The consolidated build, in order

Every step is additive (older saved films keep working), small enough to ship alone, and checked before the next. IDs: **C** = new here.

### Phase 1: free checks, no model call (front end + ffmpeg)
| # | Change | Layer | Size |
|---|---|---|---|
| C1 | **Delivery checks** in the "Before you approve" panel: spoken words vs target, silent scenes, silent sign-off, concept VO carried (length only; the concept VO is English even in a Telugu film) | Front end | Small |
| C2 | **Post-render report** beside the version (B2a): frozen stretch, near-still shots, silent tail, word count. Uses the motion measure I ran by hand on round 2 (per-second step, identical frames) | Backend (ffmpeg) + front end | Medium |

Check: both must fire on the round 2 film's saved data and render (13 words, silent sign-off, near-still last 6 s).

### Phase 2: writer and concept prompts (prompt, one real call each to check)
| # | Change | Layer | Size |
|---|---|---|---|
| C3 | Full-script writer: carry the concept VO in order; the sign-off scene speaks its payoff **and moves** (B4); the pack stays sharp, not a defocused foreground (B4); **no arm or hand crossing a face (B3)**; a "quick cuts" beat is marked as a sequence scene. Only the `writeFullScript` prompt is touched, **not** the shared `VISUAL_RULES` (it feeds three prompts) | Prompt | Small |
| C4 | Concept prompt: a `stake` field, a turn that is a visible reversal (not "gently stops"), at least one high-energy beat, plus B3 | Prompt | Small |
| C5 | Same B3 sentence in the shot planner and the single-scene rewrite | Prompt | Tiny |

### Phase 3: director's read and planner (backend prompt + front end)
| # | Change | Layer | Size |
|---|---|---|---|
| C6 | **Concept-delivery check**: per hook / surprise / turn / memorable / beat, which scene delivers it or `missing` / `flattened`; new finding `concept-flattened`; new per-scene `sequence` flag (different quick actions in one moment, NOT the existing `montage` = time passing, which bans extra angles) | `filmdirect.py` + front end | Medium |
| C7 | A `sequence` scene proposes its own coverage as text (different actions, short shots, within `max_extras`); no frames until the owner draws them | `sceneshots.py` + front end | Medium |

### Phase 4: make the warning hard to miss (front end)
| # | Change | Layer | Size |
|---|---|---|---|
| C8 | Approve stays allowed, but when risk is high, or a flattened beat / voice-floor finding exists, **Approve script** asks one confirm listing them (same pattern as the A4 confirm) | Front end | Small |

### Phase 5: optional, on the owner's word
| # | Change | Layer | Size |
|---|---|---|---|
| C9 | **B1 on demand**: Look reads three frames of a clip for stretched limbs and a smeared pack. Calibrate first on 2-3 cheap vision calls (the two round 1 bad clips against good ones) so it does not cry wolf | Backend + front end | Medium |
| C10 | **B2b opt-in** "Check all clips" using C9, with the cost shown first | Front end | Small |

## 5. Proof: not one film, not one test
The owner's point after round 1 was that one test is not evidence. So the proof for Phases 2-3 runs the writer and the director's read on **three saved concepts**: the round 1 film (Heritage, school-boy), the round 2 film (grandmother) and one different category in Independent mode. For each I measure the same numbers before and after (spoken words, silent scenes, sign-off line, flattened beats, scenes per place). Model calls only, no image or video spend. I report all three, including any where it does not improve.

## 6. Branch, merge and cost
- Branch `film-engagement-2` in the `hms-fixes` worktree, off `coverage-fixes` (`8495974` or later). Linear history, one merge later. The known `coverage` / `coverage-fixes` merge conflicts stay rehearsed, not resolved; every edit in `app.dc.html` stays small and reload-checked.
- **Not touched:** the backend system prompt (golden prompts stay pinned), the shared `VISUAL_RULES` text, the provocation writer, anything that draws frames or clips.
- Model calls (each costs cents; **I quote before each run**): writer ×3, director's read ×3, planner ×3, concept ×3-6. Phase 5 adds 2-3 small vision calls for calibration. No render or frame spend anywhere in Phases 1-4.
- Blast radius to sweep before each phase: `VISUAL_RULES` users (3 prompts and `tools/test_video_agnostic.py`), every reader of `video_beat_map` (director's panel, Before you approve, flow review, editor's notes), `sceneshots.validate` callers, the saved-film shape, `takes.py` field whitelisting.
- Tests: a page check per front-end step (real page, network and model stubbed), Python tests for the ffmpeg and director changes, then selfcheck, golden prompts and smoke on the committed tree, as in batch 1.

## 7. Done means
- Mechanics: on each of the three concepts the script keeps at least half of the voice budget (`voBudget`, 32 words for 30 s; it is a deliberately sparse budget, so half is the floor, not 70%), the sign-off speaks and moves, a flattened beat is listed by the director's read, and the post-render report flags a near-still or silent ending.
- Real test (the one that counts): the owner merges or runs the build, makes a **new** film, and says whether it holds attention. My checks only prove the mechanics.

## 8. Needed from the owner
1. **Go-ahead** on the order (Phase 1 first) and on the B1-B4 recommendations in section 3.
2. **Test batch 1.** Run `coverage-fixes` (on port 8001, so your `coverage` localhost is undisturbed) on a new film and confirm the stale-frame banner works. Everything above builds on that branch.
3. Where did attention drop: the start, the middle or the pack end?
4. Is the English narration line in the Telugu film intended?
5. Picture 3 (voice and music in production details): a change request, or a comment?
6. A screenshot of the step bar **before** a render, for the Shots-step question.
7. C8: a confirm on Approve, or a pure warning?
8. OK for the 2-3 vision calibration calls in Phase 5, when we get there.

## 9. Phase 2 status (29 Oct): prompt rules BUILT (commit `b7a8903`) and checked with 6 REAL model calls
Model `claude-opus-4-8` (the server default), the exact prompts the page builds, no house or learning context (so locations in the concept runs, e.g. "Bengaluru" and "Chennai" for Heritage, are an artefact of that, not of the rules). Cost by token estimate about $0.3-0.5 (the exact figure is on the Anthropic usage page). One sample per case: direction, not statistics.

**Finding that changed the diagnosis:** the writer prompt carries "STRICT SPEECH BUDGET: a hard limit… NO MORE than 32 words… say less… cut every word that is not doing work". The concept voiceover (37 words in the school-hem film) was often over that limit, so the writer cut it by instruction, it did not simply ignore it. The new text says the budget is what the voiceover is spent on, and sits after the budget note.

| Case | Concept VO | Saved script (your run) | Same prompt WITHOUT the new rules (control, today) | NEW prompt |
|---|---|---|---|---|
| School hem | 37 words | 9 spoken words | not run | **18**, sign-off speaks, 1 silent scene |
| Milk moustache | 32 | 28 | not run | **30**, sign-off speaks, 1 silent scene (no regression) |
| Grandmother | 26 | 13, silent sign-off | 9, sign-off speaks, 1 silent scene | **20**, no silent scene, sign-off speaks and the push-in holds the pack sharp; the quick-cuts beat now names smelling, boiling and holding to the light as three actions |

- **Writer (C3): works in direction, not fully.** The voiceover reaches the script more (9-13 to 18-20 words) but no film carries it whole (about half to three quarters of it). No limb-across-face action appeared in the four new scripts. The sign-off spoke in the control too, so that rule is not what separates old from new (the saved film's silent sign-off was one run's luck).
- **Watch:** the new scripts all have 4 scenes (the control had 5, your saved runs 6, 6 and 5). The prompt allows 4 to 7 and says one per beat is natural, so this may be noise, but fewer scenes is less variety.
- **Watch:** the new rule makes the model speak the English concept voiceover lines inside the Telugu film ("For fifty years she checked every drop."). That is open question 4 (English narration line) in a stronger form: decide if English lines in a Telugu film are wanted.
- **Same place:** the grandmother film is still all in one kitchen; nothing in Phase 2 targets this (Phase 3).
- **Concept (C4): mostly NOT working.** The "stake" rule was largely ignored: in 6 routes the rationale line gave a brand or market reason, not a stake, (one borderline). **My choice not to add a separate `stake` field was wrong**; the real run says a field is needed. The limb rule was broken in the concept itself: Heritage route 2's memorable moment is a packet pressed against an old woman's cheek. That also sets a conflict to settle, since the writer is told to deliver the concept's memorable moment AND to avoid hands at a face. The turn lines were mostly visible actions (5 of 6), which the older prompt also tended to produce, so I cannot credit the new rule.
- **Phase 3 follows in section 10.**
- **Concept fix (built after the owner's go, same day):** a real `stake` field on every route (asked for in the JSON, shown first on the route card and under the chosen concept, re-sent on a refine so it is kept, told to the script writer as "what the film must make the viewer feel" and NOT listed among the scenes to deliver), a stronger limb rule with examples (a packet or hand pressed to a cheek, a hand wiping the mouth, a finger at the lens) aimed at the four moments, and a line in the writer that a concept moment needing such an action keeps the moment and changes the framing. Older concepts without a stake are unchanged. 21 page checks pass.
- **Real re-run of the 2 concept calls (2 calls, about $0.1):** the stake field came back filled on **6 of 6 routes** with a real human stake (a daughter's exam bus; a grandfather risking being wrong about a lifetime's habit; two siblings fighting over the first glass; a father fearing his house will not outlast him; a young mason's first slab; a builder spending his savings), one of them light (the siblings' "household crown"). **No route's four moments touched a face with a hand or object** (the earlier packet-to-the-cheek moment did not recur). The turns were visible reversals by a person or an object in 6 of 6 (the grandfather pulls his hand back from his own vendor's can; the customer grabs a bag; the father hands over the brush). One sample per case: direction, not proof. The rationale lines are still marketing reasons, as expected, since the stake now lives in its own field.

## 10. Phase 3 status (29 Oct): built (commit `7161065`, tuned after the real calls) and checked with 6 REAL model calls
Built: the director's read takes the concept and checks each promise (hook, surprise, turn, memorable moment, every beat) as delivered / flattened / missing, lists the flattened and missing ones first, and flags a scene that is a RUN of different quick actions (with the actions in order); the shot planner covers such a scene with one shot per action even when the film's pace would hold it as one; the page shows "promises kept: x of y" and marks run scenes in "Before you approve", the Director's read and on the scene card. Also fixed: "Before you approve" never showed the first finding of a real read (the server keeps findings at the top level). 37 Python and 15 page checks (stubbed model), older suites, selfcheck and smoke pass.

Real calls: the director's read on your three saved scripts and on the new grandmother script from Phase 2 (4 calls), and the shot planner on scene 2 of the saved and of the new grandmother script (2 calls). About $0.4 by token estimate. One sample each.

| Read | Result |
|---|---|
| Grandmother, your saved script | **Caught it.** Beat 2 flagged flattened ("pitched as quick cuts of three tests; script delivers them in a single medium shot"); scene 2 flagged as a run with its three actions; 7 of 8 promises kept. Risk high (also weak turn, slow hook, one kitchen). |
| Grandmother, the NEW Phase 2 script | 8 of 8 kept; scene 2 still flagged as a run (smell, boil, light) so the planner covers it. Risk medium (slow hook, one kitchen: Phase 2 did not touch those). |
| Milk moustache (round 1), saved | Correctly found that the pitched split screen was never staged (turn, memorable moment and beat 3 all flattened), and marked the lab scene as a run (milk, curd, paneer). |
| School hem, saved | Beat 3 flagged flattened (a detail of the pitched beat was dropped). An older concept, so only its 4 beats were checked. |

- **Not as I predicted:** the model called the grandmother's surprise (a lifetime of tests) DELIVERED on your saved script, noting it was compressed into one 6 s beat. Reading the script text, scene 2 does name smelling, boiling and holding to the light, so the lost thing was the cutting, not the content. **My earlier statement that the surprise "was never filmed" was too strong.**
- **Planner on the saved scene 2 (6 s):** returned two extra shots with different actions (smelling; watching the pot) while the master keeps the light test: the intended result. **On the new scene 2 (9 s):** two extra shots, the boil and the light test, again different actions. Both times the model gave the size as "none" (the server fell back to medium) so the shots were all medium: **fixed in the prompt** (a real size, varied, detail or close for an action on an object; a unit test checks the wording; not re-run on a model).
- **Over-counting fixed:** the milk-moustache film listed ONE root cause (the split screen) as three findings and so scored risk "high". Findings on the same scene now count once towards the risk (all are still listed).
- **Watch (limb rule):** the new scene 2 plan has the light-test shot with "her raised forearm soft in the foreground": close to the arm-in-front-of-the-subject pattern that broke round 1. The planner prompt forbids an arm or hand crossing a face, and this is not that, but it is the kind of framing to look at in the Shots step.
- **Phase 4 follows in section 11.**
- **Limits:** one sample per case; the director's read agrees with my own reading of these four scripts but I have not checked it against anyone else's judgement. "Delivered" for the new script means the script names the three actions, not that the film will cut them: the planner and the frames still have to do it.

## 11. Phase 4 status (29 Oct): the confirm on Approve BUILT (front end only, no model call)
**Approve script** now asks ONCE, listing what the checks found, when any of these holds: (a) the director's read matches the script as it is now and is high risk, or lists a concept promise as flattened or left out (the first three are quoted, then a count); (b) the flow review matches the script and is high risk; (c) the free Delivery row found a thin script, a dropped concept voiceover or a silent sign-off. It never asks for a clean script, a medium read, a read made for an older version of the script, silent scenes that may be meant to breathe, or a wordless film's lack of speech. **Answering no leaves the script a draft; answering yes approves; a host with no confirm just approves.** The "Before you approve" footnote says so. Code: `approvalConcerns()` and `approveScript` in `app.dc.html`. Checks: 15 new page checks (`tools/page_checks/film_approve_confirm.js`); the two older checks that call `approveScript` now answer the confirm and assert it was asked (`film_pre_approve.js`, `film_delivery_checks.js`); every other film suite passes. Not verified: how it feels in a real session (a native browser dialog; the host here cannot show one).
**Owner decision taken:** I built the confirm (the plan's option), not a pure warning; the panel still never blocks. If you would rather have a warning only, it is one line to remove.


## 12. Blast-radius audit of everything built on 29 Oct (both branches), and what it found
Method: the full diff of both branches (`coverage...film-engagement-2`: 25 files, no stray or tenant files), every consumer of every changed function and field traced backwards and forwards (backend routes, front-end panels, saved films, other tabs, the flow review, the Edit room), the project's own static checks, every test suite at the tip, and the real saved films driven through all four Film steps.

**Defects found and fixed in the audit**
1. **The flow review would have cut the shots the planner made for a run of quick actions.** The planner (Phase 3) exempts a scene read as a run from the pace minimum, but `flowreview.budgets` did not know about it, so a 5 s run scene at Standard pace had a budget of 0 and the review marked its extra shot "cut: over the pace budget" (and listed it as over budget). Fixed: `flowreview.budgets` / `stats` take the run scenes and give them the same exemption, `/film-review` passes them. Tests: both directions (without the flag the shot is cut as before, with it the shot is kept).
2. **The whole-script rework (a note from the person) wrote pictures with no limb rule.** It now gets the limb rule (not the speech rules: the person's note governs speech). Test added.
3. **Two pieces of leftover state:** the re-timing note and the re-render counter are now also cleared when a film is loaded, not only when the script is emptied.
4. **Stale documents:** the plan headers still said "plan only, nothing built"; the findings doc said the concept rule had no real-model check. Corrected.

**Checked and found sound (no change needed)**
- *Saved films, backwards and forwards:* a new test saves the stake, the director's read (promises, sequence flags, actions, findings) and a frame's `parts` through the real film store (temp folder) and reads them back unchanged; an older film (none of those fields) loads with nothing invented and every reader tolerates it. The three real saved films (school hem, milk moustache, grandmother) load into the page and render the Scripting, Shoot Board, Shots and Production steps with no `undefined`, `NaN`, `[object Object]` or unrendered `{{ }}`, and no script errors (only the expected 401s for media, since nothing is signed in here).
- *Staleness of the read:* every way the concept can change (new concept, refine, picking another route) already empties the script and the director's read together, and nothing edits a concept in place, so a read can never describe a different concept than the script in front of you. A read for an older version of the script is ignored by the Approve confirm and flagged in the panels (they compare the script's signature). The post-render report is keyed to the film's URL, so a re-scored film never shows an old report.
- *Staleness of frames:* the A1-A4 fingerprints do not include anything Phases 1-4 changed (the concept, the speech rules, the director's read), so none of them can make a frame look out of date.
- *Auth and routes:* `/film-qc` is not in the public list (needs a signed-in session) and resolves its file through the tenant-aware renders lookup (a path that tries to leave the folder is a not-found); the contract and static checks (`checkfe`, `contract`) pass, including "every template hole reaches the bag" for the new panels.
- *Other tabs and producers:* only the Film tab's code paths changed. The shared `VISUAL_RULES` text is byte-for-byte as before, the backend system prompts are unchanged (golden prompts: 75 unchanged), the provocation writer and a wordless film get no speech rules, and the Edit room's editor notes only gained an extra marker line in the director's-read text they read, and the flow review gained that marker plus the run exemption of defect 1.
- *Real tenant data:* the real model calls ran from the worktree or read-only from the owner's folder; nothing under the owner's `tenants/` was written (checked by file times), and the owner's `coverage` localhost on :8000 was never touched.
- *Merge forecast:* `coverage` is an ancestor of `film-engagement-2` (fast-forward). A trial merge of the branch into `master` (`b1519e6`) shows exactly the two conflicts already known (`api/filmcut.py`, `tools/test_stitch_freeze.py`, from the stitch hotfix) and none from today's files.

**Known limits, not defects**
- A native browser confirm cannot be shown by the test host, so the Approve confirm's wording is untested in a real window.
- "Check again" on a render uses the CURRENT scene timecodes as the scene windows; if the script's timings changed after the render, the per-scene attribution could be off by a few seconds (the frozen-stretch and silent-tail checks do not depend on it).
- `test_exemplar_wording.py` fails in the worktree only because it needs an untracked brand file that exists in the owner's folder; with that file present it passes on this code.
- The director's read sees what the script says, not what will be cut: a run of quick actions named in one scene is "delivered" until the planner and frames do their part.


### 12b. Coverage of the audit by item (added after the owner asked whether A1-A8, B1-B4 and P1-P4 were all covered)
**A1-A8 (batch 1, branch `coverage-fixes`)**: re-checked item by item. A1-A4 and A6-A8 by the 32-check suite (`film_stale_frames.js`, passes) plus a real-data pass; A5 on 12 real concept routes (no split screen, montage or overlay in any moment). New in this pass: **(a) backwards:** the frame recipe the A-batch refactored (dept notes moved into `frameCrew`) was compared with the pre-batch code on the three real saved films (92 recipes: as saved, with the department notes cleared, with a Location line, with a look note and camera notes, and with extra shots on scene 2): **identical in all 92**, so frames drawn by the old build are not flagged stale by the new one; **(b) forwards:** two extra shots accepted on a real film's scene 2 (as the Phase 3 planner proposes them) are not counted as out of date while they have no frame (7 slots, 5 drawn, 5 stale), and a department note written afterwards stales exactly the drawn frames. A film's frames drawn before the A-batch carry no fingerprint, so they say "an earlier version of the script or the look" until re-drawn (known, by design).
**B1-B4**: **B1 NOT built** (Phase 5, optional). **B2 split:** the free half is built (the Render check, C2: barely moves, frozen, silent tail; checked on one real film); the model-based half is NOT built (Phase 5). **B3 built** (limb rule in the writer, the single-scene rewrite, the whole-script rework, the shot planner and the concept prompt; no limb-across-face action in 4 new scripts or 12 concept routes by reading, but that is the SCRIPT: no clip was rendered, so the defect itself is not proven gone). **B4 built at the script level only, and CORRECTED by the second audit (section 12c):** the writer is told the pack stays sharp and in the same place; the render step ALREADY locks the sign-off pack shot still and keeps the pack's size and position (an older fix for a pack that grew), so a picture-level lock existed before today and was not changed. My first wording asked the sign-off to "move" with "a slow push-in", which fought that hold: fixed.
**P1-P4**: every phase's code, tests and wiring are in sections 9-12 above; Phase 2 and 3 were checked on real model calls, Phase 1's report on one real film, Phase 4 (front end only) with a stubbed confirm.

### 12c. Second audit: A1-A8 and B1-B4 item by item, backwards and forwards (29 Oct, evening)
**Found and fixed**
1. **The sign-off conflict (B4 / Phase 1 / Phase 2).** The render path (`main.py`, the endframe branch) deliberately holds the sign-off pack shot "locked and still" with the pack at the same size and place (added earlier for a pack that grew through the clip). Two things I built today fought it: (a) the writer rule asked the sign-off scene to "move", suggesting "a slow push-in" (the real model took the suggestion: "Slow push-in holds the pack sharp"), which would have put `Camera: slow push-in` and `the camera does not push in` in one render prompt; (b) the Render check reported every held sign-off as "barely moves, add a movement". Fixed: the writer rule now says the camera holds still on the pack, life comes from what is in the frame beside it (a hand takes or pours, a glass fills), the pack stays sharp and in place, and the scene's camera cell reads as a locked-off hold; the Render check is told which scene is the sign-off and reports its stillness as the deliberate hold, with ways to lift a flat ending. This also explains the round-2 "near-still ending": it was the sign-off hold plus no spoken line, not a render fault.
2. **A1:** the out-of-date re-render had no `finally`, so a frame that threw would leave both bulk buttons locked until a reload (the existing "Generate all frames" has the same pattern, left alone). Fixed and tested.
3. **B2 (Render check):** "Check again" used the script's CURRENT timecodes as the scene windows, so a later timing edit could shift them. A re-check now reuses the windows of the film's first report.

**Checked and sound (evidence in brackets)**
- **A1 re-render only stale:** `frameSlots` / `frameIsStale` / `generateFrame` / `frameTotal` consumers all share one definition, so the Storyboard, Shoot Board, Shots step and Production pre-flight agree; both bulk buttons exclude each other through `framesBatch`; the new Phase 3 shots with no frame are not counted until drawn; a re-drawn master stales its extra angle with the reason "the shot it is matched to" (`film_audit_wiring.js`, 11 checks).
- **A2 banner:** placed in the Storyboard, the Shoot Board and the Shots step; 40 draws over 12 stale frames take well under 1.5 s.
- **A3 reasons:** the fingerprint (`parts`) travels with the frame through `sceneFrames`, the save, the load (`settledFrames` keeps every field), the builder's take copy (`takeOfEntry` / `entryOfTake`) and the backend whitelist (`takes.py`), proved by a store round trip; frames drawn before it say "an earlier version of the script or the look".
- **Recipe compatibility (A-batch refactor):** 92 recipes on three real saved films, identical to the pre-batch code.
- **A4 confirms:** only when no frame is drawn yet and the four department notes are empty (draw), or frames exist (draft a department note); both fall through when the host cannot confirm; independent of the Phase 4 Approve confirm.
- **A5:** 12 real concept routes with no split screen, montage or overlay. **A6:** the declined reason is keyed to the scene's number and picture, cleared when a new proposal comes back, and disappears by itself when the picture changes. **A7:** the note is set only by the voice plan, cleared on dismiss, when the script is emptied and now when a film loads. **A8:** the hint names a button that exists ("✦ Lock location and cast") and no other string points at the wrong tab (the remaining "Live action" mentions are the tab's own name).
- **B2 (Render check):** every source of the shown film (`produceVideo`, re-score) and every reset is covered by the URL key; the route needs a login and finds files through the tenant-aware lookup.
- **B3 (limb rule):** present in the full-script writer (and so in a provocation film's writer), the single-scene rewrite, the whole-script rework, the shot planner and the concept prompt. **Not covered, by decision or by reach:** the provocation concept route (left alone as agreed), the cutdown re-script prompt in the Edit room, and the department drafts (they write direction, not pictures).
- **B1 and B2's model half:** not built, nothing half-wired (no route, no button, no state): Phase 5 would add them whole.

**Known limits:** the Render check cannot say whether a held sign-off is too long, only that it is held; frames and clips were not rendered, so the limb and pack defects themselves are not proven gone, only the instructions and the checks around them.
