# Film craft framework — director, cinematographer, editor

Status: **DESIGN, nothing built from it yet.** Written 28 Oct 2026 for the owner's review. It supersedes the narrower "flow director" slices in
`video-edit-consolidated-build-list` (memory). Coverage itself (shots within a scene, branch `coverage`) is built and works mechanically; this
framework is the *judgement* layer that decides whether a shot, a cut or a frame deserves to exist. Brand-agnostic by construction (§7).

## 1. The principle (the owner's rule)

Extra shots exist for a **cinematic feel**. Nothing may be rendered that **takes away from the story, the film's entertainment value or its core
messaging**. A film is judged as a viewer watches it, not as a pipeline ran. The system must therefore think in three roles, in this order:

1. **Director** — what is this film about, what must the viewer feel and learn, and in which beats.
2. **Cinematographer** — the fewest shots that tell each beat, each with a job.
3. **Editor** — the order, length and rhythm of those shots, and where the sound lands.

…and a fourth gate, **Quality control**, that stops anything unfit being rendered (every render costs real money and a viewer's attention).

## 2. What the first coverage film proved (evidence, not opinion)

The mechanics worked (30.0 s, cuts where planned, ended on the pack) and the film still failed the owner's test:
- six drinking shots for 12 s — the script had *already* shown one moment at two scales (scenes 2→3) and coverage tripled it; the logline meant
  *time passing* ("glass by glass, months ago"), not one gulp from six angles → **no beat map, no repetition rule, no story reading**;
- a shoulder shot that "adds nothing" → **no per-shot job**;
- 14 shots in 30 s, a cut every 2 s through an unhurried, tender film → **no pace; the default asked for the MAXIMUM extras per scene**;
- a master frame that was two panels of a character sheet pasted together, a trouser with two legs of different length, milk drops on a face →
  **no quality gate before spend**.

Requirement that follows: encode the *thinking*, as rules a program can check plus judgements a model must justify, so it holds for any film.

## 3. The framework: five decisions in order

| # | Role | Decides | Output (stored on the film) | Mostly |
|---|---|---|---|---|
| 1 | Director | the **beat map** | per scene: purpose, intensity 0-3, time-mode, message-carrier, must-show objects | model, with deterministic checks |
| 2 | Cinematographer | the **shot plan** | per scene: 0..N extra shots, each with `job` + `why` | model proposes, rules gate |
| 3 | Editor | the **cut** | per shot: length, keep/skip, transition; the sound landing | rules + model review |
| 4 | QC | **gates** before any spend | per frame / per plan: pass or named issue | deterministic first, vision model second |
| 5 | Render | the film | `shot_clips`, notes | existing pipeline |

A person can overrule any decision; every automatic decision shows its reason (the owner's standing rule: "offer, never silently apply").

## 4. The rules (each one is checkable)

### 4.1 Director — the beat map
- **D1 One beat per scene.** Each scene gets a one-line *purpose* ("surprise at the short hem", "the memory that explains it") and an *intensity* (0 quiet … 3 payoff).
- **D2 Time-mode.** Each scene is `continuous`, `flashback`/`flash-forward`, or `montage` (time passing by repetition). A cut between modes is a *transition event* the editor must honour (a soft cut, a match, a light/colour change).
- **D3 Repetition = one beat.** Consecutive scenes whose main action matches (same subject + verb + object) are **one beat shown at two scales**, not two beats. The beat gets *one* coverage budget, and the second scene is its own coverage. *(Heritage scenes 2→3.)*
- **D4 Find the turn and the message carrier.** Exactly one scene is the *turn* (the change/payoff) and one is the *message carrier* (the shot where the core line / hero object lands; usually the sign-off). Both get the longest holds and the best frames.
- **D5 Time passing is a montage, not coverage.** When the story says repetition over time, the treatment is *variations on days* (light, clothing, glass level, small changes), never more angles on one moment.
- **D6 Hero object continuity.** The brand's hero object (pack, product, key prop) is declared once and tracked: where it must appear, and that it keeps its shape/state.

### 4.2 Cinematographer — the shot plan
- **C1 Every extra shot has a *job*,** one of: `establish` (place/scale), `reveal` (detail → context or context → detail), `reaction` (a face takes it in), `insert` (an object that carries the story), `pov`, `payoff-hold`, `match` (sets up a cut to the next scene). A shot with no job is not proposed.
- **C2 New-information test.** A shot must show something the master and its neighbours do not (a face, a hand, an object, a place, a change). If the honest answer is "the same thing closer", return **no extra shot** — zero is a valid, good answer.
- **C3 Distinct-angle test.** Different in distance *and* in side or height from every other shot of the beat (measured by `anglecheck` after rendering; stated as a camera-position sentence before).
- **C4 Difficulty flags.** Some pictures are reliably wrong for generators; the plan avoids or simplifies them: two legs/feet in motion, crowds, interlocking hands, readable text, a character sheet used as a reference. A flagged shot needs a safer composition (one subject, one limb, static).
- **C5 Object state.** Every object keeps the state it had in the master unless the shot's action changes it.
- **C6 Motivated movement.** Camera movement serves the job (push-in on realisation, locked-off on the payoff) and respects the hold rules for the pack/sign-off.
- **C7 Pace sets the budget** (table §6): how many extras per scene, minimum scene length for extras, target average shot length.
- **C8 Look consistent.** Camera/lens/grade notes of the film apply to every shot (existing B1 camera block).

### 4.3 Editor — the cut
- **E1 Length follows intensity.** Hold longest on the turn and the message carrier; tighter in build-up; never the same length for ten shots in a row.
- **E2 Cut rate has a target per pace** (shots per 10 s, §6); outside the band the review says so.
- **E3 No repetition.** No two neighbouring shots with the same subject+action; no more than two neighbours of the same size; no scene whose shots a viewer would read as "the same thing again".
- **E4 Transitions.** Prefer cuts on action or on a matched shape (a glass lowering ↔ a hem pressed down); flag flashback/time cuts that have no marker.
- **E5 Sound lands on the picture that carries it.** A spoken line starts on or just before the shot it belongs to and does not run past its scene; a beat of silence before the message line; music lifts on the turn (existing `music_on_turn`).
- **E6 End on the message carrier,** held ≥ 2 s, clean (existing sign-off rules).
- **E7 Fit.** Shots must fit the scene's real seconds (existing drop-fit warning); nothing is planned that the planner will drop.
- **E8 Nothing is rendered that failed a gate** (§4.4) unless the person says so.

### 4.4 Quality control — gates before spend
- **Q1 Panel/collage** (deterministic): a frame with hard full-height vertical seams or repeated panels is rejected (reference-sheet bleed).
- **Q2 Unexpected people/objects** (vision check): people not in the scene's cast list, text, logos, duplicates.
- **Q3 Anatomy** (vision check): limb count/length, hands, feet, faces.
- **Q4 Hero object** (existing `packqa` + vision): present when the shot needs it, correct shape and label.
- **Q5 Near-copy** (existing `anglecheck`).
- **Q6 Plan gates:** budget exceeded, repetition, shot dropped by the planner, no job, sign-off not last.
- **Q7 Render gates:** length equals chosen length, dropped-shot notes, voice windows inside scenes.
Gates are **advisory by default** (a person decides), and the Production pre-flight lists them; a person can mark a gate "accepted".

## 5. Data model additions (all optional; films without them behave as today)
- Film: `pace` ∈ calm|standard|fast (default by tone/brief, shown to the person), `beat_map` (scene → {purpose, intensity, time_mode, carrier}), `review` (last flow review).
- Shot (`row.shots[k]`): `job`, `why` (one line), `skip` (kept but not rendered or counted), `purpose_tags`.
- Frame: `checks: [{id, verdict, note}]` from §4.4, stored beside the frame.
- Everything old keeps working: golden tests (existing) must stay byte-identical for films with none of these fields.

## 6. Pace presets (numbers to be tuned on real films; starting point)

| Pace | Feel | Avg shot | Max extras / scene | Extras only if scene ≥ | Shots per 10 s | 30 s film ≈ |
|---|---|---|---|---|---|---|
| **Calm** | tender, emotional, premium | 4–5 s | 1 | 6 s (or the turn) | 2–2.5 | 6–8 shots |
| **Standard** | brand story, balanced | 3–4 s | 2 | 6 s | 2.5–3.5 | 8–10 |
| **Fast** | energetic, youth, performance | 2–3 s | 3 | 4 s | 3.5–5 | 11–14 |

Chosen from the brief's tone with a visible default, changeable in one click. (The Heritage film is **Calm**: "tender, unhurried" — it got Fast.)

**As built (slice 1, 28 Oct 2026):** `sceneshots.PACE_TABLE` / `budget(secs, pace, role, signoff)`. The "(or the turn)" exception is applied to the **hook and the turn** (the opening and the turning point may be covered even when short); the frontend can only name the hook (scene 1) and any scene the writer tagged, so an untagged turn is not yet exempt. An opted-in sign-off is judged by its seconds, not the pace minimum. Pace is stored per film (`video_pace`); with none chosen the server's tone read (`POST /pace-suggest`) is the default, and with neither it is Standard. A shot must carry a **job** and a one-line **why** or it is left out; zero extra shots is a valid answer. A person can **Skip** any shot: it stays in the script but is neither rendered nor counted.

**As built (slice 2, 28 Oct 2026):** `flowreview.py` + `POST /film-review` + the "Flow review" panel above the storyboard. Measured facts (no model): shots, average length, cuts per 10 s against the pace band, the longest same-size run, five-in-a-row same length, extras with no job, scenes over their pace budget or not fitting their seconds, an opted-in sign-off that does not end on the product hero. One model call (the whole cut in order, the logline, message, tone, pace and the planner's scene roles) returns the beats (repetition = one beat; `time_passing` read from MEANING), the turn and the message carrier, a keep / cut / merge verdict with a reason for EVERY extra shot, and cross-scene notes. Backstops: a shot the review did not mention is kept (never cut by silence); a cut with no reason is kept; the closing product shot is never cut; **the pace budget is a rule** (a scene never keeps more extras than its pace allows; the surplus is cut by job priority with that reason; the review's own turn scene may be covered even when short). Apply = "Skip the N marked shots" (reversible per shot). The review is advisory and not saved. A text review cannot see a picture: scene-5's shoulder shot (a visual defect) and the collage frame are slice 3's.

Real run on the rejected Heritage film (Calm, one Claude call, `tools/engine_trials/flow_review_real.py`): 15 shots in 32 s (4.7 per 10 s vs Calm 2-2.5) -> flagged; scenes 2+3 named ONE beat shown at two scales and time passing read as true; turn = scene 4; 5 shots marked -> 10 shots left (answer key: about 9; the remaining one is the scene-5 shot the text cannot judge).

**As built (slice 3, 28 Oct 2026):** `framecheck.py` + `POST /frame-check` + a Frame check panel above the storyboard, a chip on the frame, and a Pre-flight line. A model looks at one rendered frame beside what the shot should show (and the film's cast note) and names only real defects: `collage` (pasted panels / wrong scale), `extra-people`, `missing-people`, `anatomy`, `text`, `mismatch`, `other`. One model call per frame (about 2.4k tokens in, 0.1k out measured); on demand, never automatic; results live on the frame (`checks`, `checkedUrl`, `checkAccepted`) so they save with the film and a re-render (new url) drops them. Advisory: the pre-flight line never blocks, "Accept" says "seen, keep going".

**Deviation from section 4.4 (Q1 was meant to be a deterministic seam rule first): measured, and dropped.** On the 15 frames of the rejected film a hard-vertical-seam rule and a column-correlation rule were both tried. The real collage (scene 5's master) joins cream wall to cream wall, so its seam is no harder than the ordinary vertical edges every kitchen frame has (60-90 % of rows step in almost every frame); neither rule separated it from the 14 good frames, so no pixel rule is shipped (a rule that misses the defect it exists for is worse than none). Q1 is the vision check.

Real run on the 15 frames of the rejected film (`tools/engine_trials/frame_check_real.py`, 36k tokens in / 1.6k out in all): the scene-5 master is flagged as two pasted panels at different scales (the owner's PIC 4); the scene-5 shoulder frame is flagged as not showing the described action (PIC 5); two frames are flagged on the needle / thread join and one on a glass that should be empty; the scene-1 foot detail (the owner's two-different-legs picture, seen in the video) passed as a still: leg defects that only appear while the clip moves belong to the render-stage check, not this one.

**As built (slice 4, 28 Oct 2026):** `filmdirect.py` + `POST /film-direct` + a "Director's read" panel above the flow review; the map is saved with the film (`video_beat_map`). One model call reads the whole script and returns, per scene, a purpose, an intensity 0-3, a time mode (continuous / flashback / flash-forward / montage), the marker that tells the viewer the time changed, a beat id and whether the hero object shows, plus the turn, the message carrier, `time_passing` and a one-line summary. Backstops: every scene gets exactly one entry, intensity clamped, time-mode synonyms read, beats renumbered and only NEIGHBOURS may share one, a turn or carrier that is not a real scene is replaced (carrier -> the sign-off). Program-made findings: unmarked time jumps, a flat film, a turn that is not the strongest scene, a message scene without the hero object, one beat shown at two scales. **Two findings are RULES enforced elsewhere with no model:** D5 a scene inside a MONTAGE gets no extra angles, D3 the second scene of a one-beat group is its closer view and gets none. They apply in `/scene-shots` (returns none with the reason, the model is not called), in `/film-review` (the budget is zero; a surplus shot is cut with "No extra angles here: ...") and on the Coverage strip. The beat map also reaches both prompts as "THE DIRECTOR'S READ" (given, not redone). The writer's `VISUAL_RULES` gained: one beat per scene, say the time whenever it differs from the scene before, time passing by repetition = visibly different days.

Real run on the rejected Heritage film (`tools/engine_trials/film_direct_real.py`): turn = scene 4, carrier = scene 6, time passing true, scenes 2+3 ONE beat (flashback, marker named), hero object named; the no-coverage rule then removes extra angles from scene 3. Matches the answer key.

## 7. Brand- and category-agnostic by construction
- **Inputs only from the film's own data:** logline, scenes, spoken lines, the brief's proposition / core message, brand profile (hero object, "pack in scene"), cast/location/look notes, sound plan, duration, aspect, tone. **No brand words in any prompt or rule.**
- **Language-agnostic:** judgements use meaning, not keywords; the deterministic repetition check compares normalised subject/verb/object from the model's own beat map, not English regex.
- **Works for the other film kinds:** provocation/no-people films (jobs like `insert`, `reveal` on objects), live-action scenes (skipped as today), 9:16 and 16:9, product-demo explainers (`mechanism` beats), montage/lifestyle (`montage` time-mode), testimonial/talking-head (few shots, long holds).
- **Proof = a corpus, not one film:** §9.

## 8. Where each rule lives (blast radius in one table)

| Rule family | Lives in | Change |
|---|---|---|
| D1-D6 beat map | new `filmdirect.py` + route `POST /film-direct`; reads `/complete` writer context | new; stored on the film; the writer's rules (`VISUAL_RULES`) gain "one beat per scene, say the time-mode" |
| C1-C8 shot plan | `sceneshots.py` (+ `/scene-shots`) | prompt, schema (`job`, `why`), "zero is valid", whole-script + beat map as context, pace budget, validation |
| E1-E8 cut | new `flowreview.py` + route `POST /film-review`; planner honours `skip` (`filmcut.plan_by_scene`) | review = deterministic stats + one model call; skip flag in planner (golden stays identical) |
| Q1-Q7 gates | new `framecheck.py` (+ existing `packqa`, `anglecheck`), route `POST /frame-check`; render notes | deterministic seam detector, vision check, pre-flight list |
| Frontend | `app.dc.html` | Pace chip; job/why on tiles; Skip switch; "Review the flow" panel; frame-check chips; pre-flight lines |
| Render | `main._produce_video_sync` | honour `skip`; notes; no behaviour change otherwise |
Nothing in the voice, music, captions, Edit room or cutdown paths changes except through the existing `shot_clips` and scene-level invariants.

## 9. How we prove it works on ANY film
1. **Offline, deterministic (no model):** golden tests for the planner (unchanged), pace budgets, repetition/size-neighbour/fit checks, the seam detector on synthetic collages and the real bad frame from the Heritage film, `skip` handling.
2. **A corpus of ≥ 4 different films** (stored as fixtures, brand-neutral): an emotional family story (Heritage), a product-demo explainer (a durability test), a fast lifestyle/fashion montage, a testimonial. For each: a hand-written "director's answer key" (which shots a good director keeps/cuts, the pace, the turn, the carrier). The review and proposer are scored against it: **must flag the known flaws, must not cut the essential shots.**
3. **Real runs** (model + a Draft render) on each film; the owner watches. Metrics logged per film: shots, avg shot length, shots per 10 s, longest run of one subject, shots without a job (target 0), final shot carries the message, gates failed.
4. **Regression:** every later change re-runs the corpus.

## 10. Build order (each slice shippable on its own, local first, branch `coverage`)
1. **Shot plan with jobs + pace + Skip** (C1-C2, C7, `skip`, whole-script context). Stops over-shooting at the source.
2. **Flow review** (D3, D4, E1-E3, E6-E7). One button; keep/cut/merge with reasons; "Apply" sets `skip`.
3. **Frame check** (Q1-Q4 gates, pre-flight). Stops bad frames reaching a render.
4. **Beat map + writer rules** (D1-D6, time-mode, montage treatment). Fixes it at the story stage.
5. **Editor's sound and transition notes** (E4-E5).
Then: the Heritage film re-directed end to end as the first corpus case; takes/re-roll; location plates.

## 11. Worked example — the Heritage film under these rules
Beat map: 1 *surprise* (continuous, i1) → 2+3 *the memory* (flashback, one beat at two scales, i1; D3, **and** the logline asks for D5 time-passing) → 4 *the turn: realisation as she lets the hem down* (i3, carrier of the emotion) → 5 *payoff: it fits now* (i2) → 6 *message carrier* (i3, the pack + "one glass at a time"). Pace: **Calm**.
Verdicts: scene 1 detail (hem) keep — `insert`; scenes 2/3 extras cut — fail C2/E3, and the memory is better shown as D5 variations; scene 4 face shot keep — `reaction`; scene 5 shoulder shot cut — fail C2; scene 6 pack hold keep — E6. Frame gates: scene 5 master fails Q1, scene 1 detail fails Q3 at the video stage. Result ≈ 9 shots, avg ~3.3 s.

## 12. Decisions needed from the owner
1. **Pace defaults** (§6): are these the right starting numbers, and should the default come from the brief's tone with a one-click override?
2. **Gates are advisory** (a person can accept), never blocking — agreed?
3. **The corpus:** which 3 other film kinds from your real work should I use besides the Heritage story (I propose: a product-demo explainer, a fast lifestyle montage, a testimonial)?
4. **Montage treatment** (time passing by repetition with variation) as part of slice 4 — agreed that it is a treatment, not more coverage?
5. Build order in §10 — agreed?
