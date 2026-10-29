# Film builder: consolidated plan after two localhost tests (29 Oct 2026)

Status: **PLAN ONLY. Nothing in sections 3-5 is built.** This replaces the need to read three documents: it merges `FILM_LOCALHOST_FINDINGS.md` (rounds 1 and 2), `FILM_BORING_FIX_PLAN.md` (the boring-film diagnosis and slices) and the pending B1-B4. Evidence level per line: *seen* (film or saved data), *code* (source), *inferred*.

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
- **Next, if you agree:** add a `stake` field to the concept route (cards, refine, tests) and put the limb rule in a stronger form with an example; then re-run the 2 concept calls (about $0.1). The writer change stays as it is.
