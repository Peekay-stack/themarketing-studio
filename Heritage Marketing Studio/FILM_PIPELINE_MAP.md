# Film generation — the whole process, concept to render, and the plan for the Shots tab

Status: **Map written 28 Oct 2026; the Shots-tab plan (Part 3) and the proposed process (Part 4) were then built as slices S0-S7 on branch `coverage`** (see `FILM_BUILDER_PLAN.md` build log, `FILM_ENGAGEMENT_PLAN.md`, and the audit `FILM_WIRING_AUDIT.md`); Parts 1-2 describe the process as it was when the map was written. Written from a read of the code (frontend `app.dc.html`, backend `main.py`, `prompts.py`, `filmcut.py`, `filmvoice.py`, `filmaudio.py`, `gemini.py`, `creative.py`) and of what we built on branch `coverage`. Where a step is one of the new craft layers (pace, director's read, flow review, frame check, editor's notes) it is marked **[craft]**. It replaces nothing in `FILM_BUILDER_PLAN.md`; Part 3 here updates that plan in the light of the map.

How to read each stage: **Person** = what the human does · **System** = what runs (function / route) · **Why** = the reason it exists (mostly lessons the code comments record) · **Output** = what is kept · **Cost** · **Guards** = what stops it going wrong.

---

## Part 1 — The process, stage by stage

The Film tab is a four-step wizard (Brief → Scripting → Shoot Board → Production) with an Edit room after it. Underneath there are about fourteen real stages.

### Stage 1 — What the film is given (Brief)
- **Person:** picks a communication objective (e.g. Brand awareness) and, optionally, binds the film to a **plan brief** (an execution from the Plan), an **idea platform** (the brand's creative idea) and/or an approved **provocation** (a deliberate departure from category conventions). Can type extra direction, or set the platform aside (`force_typed`).
- **System:** `videoExec()` / `linkedBrief` / `videoStandsOn`; the screen shows "WHAT THIS FILM IS GIVEN" with each input's state.
- **Why:** a film should stand on a decision someone already made (audience, channel, idea), not on whatever the model invents. Three of these inputs are the "mandatories" the master prompt is built around.
- **Output:** the grounding that every later model call carries.
- **Guards:** `needBrand` refuses to run with no brand; Grounded vs Independent mode (Independent drops the brand's grounding); a brand preamble is required or the call is refused.

### Stage 2 — The concept: three routes
- **Person:** presses generate; reads three **genuinely different routes** (e.g. a human story, a craft/proof route…), picks one, or refines it with a note.
- **System:** `generateVideo` → `window.claude.complete` → `POST /complete` (`complete.py`: Claude, `GEN_MODEL`, with the system prompt built by `prompts.system_for(..., film=True)` = global master prompt + the brand's voice/mandatories/brand core + house, platform, plan, provocation). Output JSON: `{routes:[{name, logline, duration, scenes:[{title, desc}], vo}]}`.
- **Why:** three distinct routes stop the model giving three phrasings of one idea. Nothing is invented on failure: an empty concept says why instead of a fallback film (a past bug logged a fake film as work produced).
- **Output:** `videoConcept` (logline, beats, VO sketch), `conceptRoutes`, a script-version history.
- **Cost:** one Claude call. **Guards:** failure leaves the previous draft untouched; switching route invalidates everything downstream (script, frames, cast, cut) by design.

### Stage 3 — The full script
- **Person:** presses "write the full script"; edits the table (visual, camera, shot size, movement, dialogue/VO lines, supers, beat role); can rewrite one scene or rework the whole script; approves.
- **System:** `writeFullScript` builds a very large prompt: brand preamble + the concept + **how many scenes** (a range from duration, never fewer than the concept's beats, ceiling because "each shot renders separately and the shortest is 4 s") + `VISUAL_RULES` (one scene = one frame; no on-screen text in the visual; no repeating a moment; name age/clothes when they change; the pack is only "the pack"; vary framing; **[craft]** one beat per scene, say when time changes, time passing = visibly different days, **be entertaining**) + a required **pack-shot sign-off** + language rules (spoken lines in the native script, never romanised) + `learningContext` (approved past work as anchors, corrections as rules, **locked copy** that must appear verbatim).
- **Why:** each scene becomes ONE storyboard image and later ONE clip, so every rule exists because a past film broke it (a three-view scene came back as a collage; a pack described by colour came back in those colours; a padded script repeated scenes). The learning context is "retrieval into the prompt, not a changed model".
- **Output:** `fullScript` rows `{no, tc, visual, camera, shot_size, movement_class, audio:[{kind, speaker, text, emotion, pace, timing…}], dialogue, supr, beat_role}` + `scriptStatus`.
- **Cost:** one large Claude call (per script / rewrite). **Guards:** repeat detector (`hasScriptRepeats`); approval gate (nothing downstream unlocks before `scriptStatus='approved'`); timecodes re-timed from the words (scene length follows the dialogue, not a fixed grid).

### Stage 4 — Approve: cast, place and voices are derived
- **Person:** approves the script. (Nothing else is required here.)
- **System:** `approveScript` seeds a render seed, loads engines/styles/music styles, derives the **cast sheet** (`deriveCharacters`: one compact sheet of every recurring person: role, age, build, hair, skin tone, wardrobe colour) and the **location line** (`deriveLocationLine`: ≤40 words of what the camera sees, empty place only, no people, no product), and loads the **voice plan** (`/voice-plan`: who speaks what, in which voice, when; costs nothing).
- **Why:** identity cannot be carried by words — "however precise the description and however fixed the seed, text-to-image redraws a different person each call" — so the cast is turned into one compact sheet that rides with every frame, and the place is separated from the production plan (which is a document, not a description of what the camera sees).
- **Output:** `videoCharacters`, `videoLocationLine`, `voicePlan`, `videoSeed`. Skipped for no-people provocation films.

### Stage 5 — Shoot Board: the departments
- **Person:** reads and edits nine department notes: Cast, Location (the two "scripting" pre-decisions), DoP, Props, Wardrobe & Styling, Lighting, Music, Dialogue/VO, Sound. Sets the optional **look reference**, **wardrobe lock** (one costume held identical in every shot) and **camera & lens notes** (the film's technical spine); picks real library items (a cast photo, a location plate, a specific pack).
- **System:** `draftDept(id)` drafts each from the **approved script** ("base your plan strictly on this approved script" + the decisions already made, `decidedFacts`). The Music note's suggested style becomes Production's music mood unless the person set one.
- **Why:** these are the crew decisions that feed each frame (`deptNote`) and the soundtrack, drafted from the script so they never contradict it. A made-up default ("a young mother, late 20s") once contradicted the cast sheet, so a failed draft leaves the box empty rather than stock text.
- **Output:** `shoot{…}`, `videoLookRef`, `videoWardrobe`, `videoCamera`, picks. **Cost:** nine small Claude calls.

### Stage 6 — Lock the cast (the anchor image)
- **Person:** presses lock after the cast sheet and location line read right.
- **System:** `buildCastReference` → `POST /cast-reference` → **one reference image** of the film's cast (text-to-image, or image-to-image when a signed-off cast/plate from the library is picked), stored as `castRefUrl` with a signature (`castLockSig`) of what it was made from.
- **Why:** this is the single mechanism for consistency: render the cast ONCE as a picture and generate every later frame *from that picture*. (Known weak spot: the lock is often a multi-panel character sheet and the image model can paste its panels into a frame — the 28 Oct scene-5 collage.)
- **Cost:** one image. **Guards:** changing the image engine or the cast text invalidates the lock and every frame (the signature shows "out of date").

### Stage 7 — Storyboard frames (frame-first)
- **Person:** presses "generate all frames" or one frame at a time; adds a frame note ("pack front-on"); can match a frame to another scene's frame; re-renders.
- **System:** `generateFrame(idx, k)` builds the request (`frameBody`: scene visual + camera + location + department notes + film-wide note + this frame's own note, style, ratio, shot size, characters, wardrobe, camera notes, **reference = the cast lock** (+ a sibling frame for continuity, or the scene's master for an extra shot), pack/plate per the checkboxes) → `POST /scene-still` (Gemini image model first, fal fallback; a provocation's visual language overrides the generic look). The response carries `pack_check` (pack aspect by colour) and `angle_check` (is an extra shot a near-copy of its master).
- **Why:** the video engine animates the approved frame, so what you sign off is what you get, and the cast/pack stay identical shot to shot. Text-to-video would reinvent the people every call.
- **Output:** `sceneFrames["<idx>"]` (+ `"<idx>.<k>"` for extra shots) with a recipe fingerprint so the card can say **"out of date"** when the script, cast, look, camera or pack has moved on since.
- **Cost:** one image per frame. **Guards:** cast gate (lock first); stale detection; a frame saved as "rendering" restores as an empty slot, not a spinner. **Gap:** a re-render **overwrites** the frame — there is no frame history or choice among variants.

### Stage 8 — [craft] The craft layers (all advisory, all optional, all on branch `coverage`)
Run in the order the framework gives; each is a panel above the storyboard and each only advises.
1. **Film pace** (Calm / Standard / Fast; default read from the tone) — how many extra camera angles a scene may carry.
2. **Director's read** (`/film-direct`) — per scene: purpose, intensity, time-mode (continuous/flashback/montage), marker, beat group, place, energy, change; the turn and the message carrier; program-made findings (unmarked time jump, flat film, **boredom risk**: slow hook, same place, flat energy, no change, late peak). Two RULES with no model: no extra angles inside a montage or on the second scene of a one-beat group.
3. **Shot plan** (`/scene-shots`, "Break into shots") — zero or more extra angles per scene, each with a job and a reason, held to the pace budget; the director's turn may be covered even when short. A shot can be **skipped** (kept in the script, not rendered).
4. **Flow review** (`/film-review`) — an editor's pass over the whole cut: keep/cut/merge with a reason per extra shot, cross-scene notes, an honest "would a viewer stay?" and fixes; the pace budget is enforced as a rule.
5. **Frame check** (`/frame-check`, vision) — a model looks at each rendered frame before it is animated: pasted panels, extra/missing people, wrong anatomy, unwanted text, wrong picture.
6. **Editor's notes** (`/editor-notes`, no model) — music lifts on the director's turn, a beat of silence before the message line, lines fit scenes, time on the turn, end on the message, cut on the action; one-click fixes.
- **Why all of it:** the 28 Oct film was mechanically fine and creatively wrong (over-shot, repetitive, bad frames, **boring**). These encode the director/cinematographer/editor judgement as rules + honest model reads that hold for any film.

### Stage 9 — Hand over to Production (the gate)
- **Person:** presses hand-over.
- **System:** `handToProduction` refuses unless the script is approved, **every** frame (scene + active extra shots) is rendered, and none is out of date.
- **Why:** rendering video from a stale or missing frame wastes the expensive step.

### Stage 10 — Production settings and pre-flight
- **Person:** chooses aspect (16:9/9:16/1:1), duration (30/20/10 s), video engine and tier (**Draft** = Omni 360p, **Final** = Omni 720p; Kling via fal as the alternative), music mood/style/tempo/dynamics or a locked bed, music level, voices (cast per speaker, accent, per-line pace and timing), the **Sound design** plan (per-scene music state under/open/swell/out, duck depth, ending, carve, ambience/sounds from the library), loudness; reads the **pre-flight checklist** (script approved, frames current, aspect, duration, frame-check line) and the cost/time estimate (measured $/s × seconds).
- **System:** `/voice-plan`, `/sound-plan`, `/music-options`, `/engines`; estimate from `RATE` (Draft $0.034/s, Final $0.101/s measured; Kling reported by fal).
- **Why:** everything that shapes the final film but is not picture is decided here, and the estimate is shown before money is spent.

### Stage 11 — The render (one monolithic job)
`POST /produce-video` starts a background job (`_produce_video_sync`; polled by `/render-status`; in-memory, lost on a server restart). In order:
1. **Plan the shots** — `filmvoice.scene_seconds` re-times scenes from their words; `filmcut.plan_by_scene` turns scenes into segments (a scene needing more than 8 s becomes continuing beats; extra shots become `continues` segments; roles hook/world/mechanism/turn/brand/button assigned per scene; skipped shots dropped; the sign-off stays one shot unless opted in).
2. **Live-action substitution** — a scene with a signed-off live-action shot is trimmed into the timeline instead of generated.
3. **Per segment: prompt + generate** — `segment_prompt` (via `videoprompt`: ACTION / EXPRESSION / CAMERA / KEEP IDENTICAL / audio-off / no text, plus style, look, wardrobe, camera notes, the pack-hold rule on the closing shot) and `gemini.video` (Omni image-to-video from the frame, ≥3 s generated then trimmed, 7 requests/min limiter, four lanes) with fal Kling as fallback; an extra shot with no frame is **held back** (never drawn from words alone — it once produced a different pack).
4. **Collect** — failed shots are reported ("INCOMPLETE CUT — n of m shots…") with the true cause (credit wall vs per-minute quota vs safety block).
5. **Stitch** — `filmcut.stitch`: each clip trimmed to its beat (so picture and sound stay locked), joined, forced to the exact length; **[fix] a frozen-join check rebuilds with the concat filter**.
6. **Voice** — lines re-windowed onto each scene's *actual* picture position (clips are beat-snapped, so script timecodes drift); cast voices synthesised (Google Chirp/Gemini TTS; ElevenLabs child voices), per-line pace/timing honoured.
7. **Music** — a bed generated for the real length (Gemini's music model; fal fallback), or a locked bed.
8. **Mix** — `filmaudio.mix_timeline`: voice first, music ducked under it per the sound plan (lift in pauses, swell on the turn, ending), optional music-on-turn, loudness pass. The **silent master is kept** so music/voice can be changed later for the price of audio alone (`/rescore`).
9. **Record** — `shot_clips` (one record per shot: scene, shot, seconds, url, ok, provider, from_frame, role, continues) + the film URL + notes; logged to the "made" ledger.
- **Cost:** the dominant spend of the whole process (clips), plus voice and music. **Gap:** all-or-nothing — you cannot see, choose or re-roll one clip before the rest is paid for, and the clips are not kept as choosable objects.

### Stage 12 — After the render
- **Person:** watches the film in Production (versions list); opens the **Edit room**: cutdowns (20 s / 10 s), re-voice and re-mix, captions, reframe, end-card, grade, "rework the cut" (a note re-renders or only re-scores if the note is sound-only), import a finished film.
- **System:** `/cut*`, `/rescore`, `/cut-sound`, `/cut-grade`; cutdown rendering uses the per-shot clips (`startCutFromFilm`). Known gap: cutdowns today re-render frameless (the queued "cutdown fidelity" build).
- **Why:** finishing work happens on the picture that exists, layer by layer, without paying for new video.

---

## Part 2 — What the map tells us

1. **The pipeline is front-loaded with judgement and back-loaded with spend, and there is no choosing point between them.** Stages 1–9 are cheap, reversible and now well guarded. Stage 11 is expensive and irreversible: one run, one result. Everything Flow and Higgsfield do well sits in exactly that gap.
2. **Frames have the same problem in miniature.** A re-render overwrites the frame. Higgsfield's "hero frame first, grid of variants" is the cheap place to choose (images are cheap, clips are not). Takes therefore belong on **two layers per shot: frame takes and clip takes.**
3. **The renderer is already shot-shaped.** Segments, per-shot prompts, per-shot frames, per-shot `shot_clips`, voice re-windowing by scene — the monolith is a loop over shots wrapped in stitch/voice/music/mix. That is why the builder can be a thin layer (two inert payload keys), not a new pipeline.
4. **"Boring" is decided upstream.** The craft layers (stage 8) are where entertainment is checked; the builder is where it is finally *seen* (play the sequence before the final spend). The two should be on one screen.
5. **Sound is a separate layer by design** (silent master, `/rescore`), so a picture-only builder loses nothing: assembling from chosen takes feeds the same sound path.
6. **State lives in one place** (`fullScript`, `sceneFrames`, `video_*` fields saved with the film). The builder adds one more optional field rather than a parallel store.
7. **Known fragilities to design around:** in-memory render jobs (restart), frame keys by position (reorder), media never cleaned up (646 MB locally; 10 GB live), the rate limiter (7/min), child-clip safety blocks on extension.

---

## Part 3 — The plan for the Shots tab (v2, after the map)

### 3.1 What it is
A shot-centric workspace for the stretch from **approved frames to a chosen picture edit**: for every shot of the film, a **frame** (with variants) and a **clip** (with takes), a **timeline** of the chosen clips with sound context, a **preview** of the sequence, and **Assemble**. It does not replace Scripting, Shoot Board or Production; it sits between Shoot Board and Production as a new Film step named **Shots**, and the Film tab's one-button render stays.

### 3.2 Screen layout (top to bottom)
1. **Film header strip:** pace, director's-read boredom risk and the turn/message scenes, budget cap and "spent so far", engine + tier (Draft/Final), a Frame-check and Flow-review shortcut (the same panels, collapsed).
2. **Shot grid by scene** (the main area). One card per shot, grouped under its scene header (scene number, beat role, purpose from the director's read, seconds, the spoken line under it).
3. **Timeline strip** (pinned at the bottom): chosen clips in order as blocks sized by seconds, with trim handles, a marker for each scene boundary, the VO lines as chips over their scenes, the music state (under/open/swell/out) as a coloured band, the turn and message markers, and the total vs the film's slot.
4. **Preview player** (right or bottom sheet): picture-only playback of the whole sequence from the chosen clips and trims, seams marked, no render and no cost; a "play from this scene" control.
5. **Footer actions:** Generate missing (Draft), Promote chosen to Final, **Assemble film**, with the estimate shown on each.

### 3.3 The shot card (the unit of the whole tab)
```
┌ Scene 4 · shot 2  · REACTION · close · 2 s ·  Skip ┐
│ [FRAME layer]  ▢ variant A ▣ variant B  ▢ variant C │  <- frame takes (images), choose one; Frame-check chip
│ [CLIP  layer]  ▶ take 1 (Draft) ▣ take 2 ▢ take 3   │  <- clip takes, choose one; QC chips (frozen/black/short)
│ prompt preview (the compiled shot prompt, editable) │
│ continuity: ○ from frame  ○ chain from prev  ○ extend│  <- default "from frame"; extend only for adult shots
│ [Generate frame ×N] [Generate clip] [Re-roll]  ≈$0.10│
└ status · error text in the engine's own words ──────┘
```
- **States per layer:** none · queued (waiting for the engine's per-minute allowance) · rendering · done · error (with reason) · interrupted (server restarted) · out of date (the script/cast/camera moved on since this take was made).
- **Rules:** the clip layer is disabled until a frame is chosen (a shot never renders from words alone); choosing a different frame marks existing clip takes "from an older frame"; a skipped shot is dimmed and never rendered; every button shows its estimate; double-click cannot double-spend.

### 3.4 The loop the person actually does
1. Open Shots; the cards show the approved frames as the chosen frame (no re-spend).
2. (Optional, cheap) generate 2–3 frame variants for shots that matter; the frame check flags collages/anatomy; choose.
3. Generate **Draft** clips (one, several, or all missing — queued, capped by the budget); watch each; re-roll the weak ones; choose a take per shot.
4. Trim/skip/reorder on the timeline; play the sequence; read the flow/engagement notes against what you now *see*.
5. **Assemble** (voice, music, mix via the existing pipeline) → a normal film in Production and the Edit room.
6. **Promote to Final:** re-render only the chosen shots at 720p, assemble again.

### 3.5 How it plugs into the stages above
| Stage | Builder relationship |
|---|---|
| 3 Script / 4 derive | read-only: the shot list, seconds, VO lines, roles come from `fullScript` + `plan_by_scene`; reordering edits the script (one source of truth) |
| 6 Cast lock / 7 Frames | frames are reused as the chosen frame; "Generate frame variants" calls the same `/scene-still` with the same `frameBody` and keeps history; changing the lock/script marks takes out of date exactly as frames are today |
| 8 Craft layers | shown in context (risk chip, notes against the timeline); Skip and the shot plan feed the shot list; frame check runs on frame variants and (later) on a clip's middle frame |
| 9 Hand-over gate | unchanged; Shots can be entered once frames exist |
| 10 Production settings | tier/engine/budget shown, edited in one place (Production remains the home of voices/music/sound; Shots only displays them) |
| 11 Render | **Assemble = the same job** with `use_clips`; per-shot generation = the same `render(seg)` with `only_shot`; stitch/voice/music/mix unchanged |
| 12 Edit room | receives the same `shot_clips`; later, cutdowns reuse chosen takes |

### 3.6 Data (unchanged from `FILM_BUILDER_PLAN.md` §4, with one addition)
`video_builder = { frames: { "<scene>.<shot>": [FrameTake…] }, frame_chosen: {…}, takes: {…}, chosen: {…}, trim: {…}, budget: {…} }` — **frames** are the new layer (history of images per shot); the existing `sceneFrames[key]` always mirrors the chosen frame so everything that reads it today keeps working untouched.

### 3.7 Changes to the slice plan
Same slices, one reordering and one addition:
- **S0** foundations (unchanged). **S1a (new, small): frame variants + choose** — cheapest win, uses only the existing image route, makes the frame layer real before any video spend. **S1b:** clip takes (the original S1). **S3** assemble, **S2** timeline/trim/reorder, **S5** take QC, **S4** continuity, **S7** budget/batches/retention, **S6** presets, **S8** elements — as in the plan.
- The suggested order becomes **S0 → S1a → S1b → S3 → S2 → S5 → S4 → S7 → S6 → S8**.

### 3.8 What does not change / what it must never break
The Film tab's one-button render, every existing film (no builder data = identical behaviour; golden tests stay byte-identical), the Edit room's `shot_clips` contract, voice windows by scene, the Sound design plan, the approval and hand-over gates, the frozen-join guard, and the rule that nothing spends without an estimate and a click.

### 3.9 Open questions for the owner (replaces the plan's list where they overlap)
1. Frame variants in the first release (S1a) — yes (my recommendation) or only clips first?
2. Should the Shots step *replace* the Storyboard section in Scripting (one place for frames) or sit beside it and mirror it (my recommendation: mirror, then retire the old section once Shots is proven)?
3. Preview: picture only (my recommendation) or also a "with voice" preview (costs TTS)?
4. Everything else in `FILM_BUILDER_PLAN.md` §12 still stands (scope of the first release, branch, scene reorder, cost model, hotfix to master).

---

## Part 4 — The proposed process (what changes, stage by stage)

Principle: **decide on cheap things before paying for expensive ones, and put a choosing point in front of every spend.** The spend ladder is free text → images → Draft clips → Final clips; the proposed process makes sure everything that can be judged at one rung is judged before climbing to the next.

| # | Proposed stage | vs today | What happens |
|---|---|---|---|
| 1 | Brief | same | objective + plan brief / idea platform / provocation |
| 2 | Concept routes | **changed** | each route must also state its **hook** (the first 3 seconds), its **surprise**, its **turn** and one **moment worth remembering**, so entertainment is chosen at the idea, not rescued later |
| 3 | Full script | **changed** | writer rules include "be entertaining" (done); **Film pace** is chosen here; the **director's read runs on the draft** and shows boredom risk *before* approval (advisory, never blocking) |
| 4 | Approve + derive | same | cast sheet, location line, voice plan |
| 5 | **Plan the shots (text only)** | **moved earlier** | shot plan + flow review run on the *words*, before any frame is drawn; cuts are applied as Skip. "Plan before pixels": no image or clip is ever spent on a shot that will be cut |
| 6 | Shoot Board | same + **editor's notes** | departments, locks, look/wardrobe/camera; sound and rhythm notes (music on the real turn, silence before the message) need no pictures, so they are fixed here |
| 7 | Cast lock | **changed (to trial first)** | today the lock is one multi-panel character sheet, which is why panels leak into frames (the scene-5 collage). Proposal: one **single-person reference per character** (plus a place plate), fed to frames as separate references. A small trial decides it; the frame check is the backstop meanwhile |
| 8 | **Shots tab — frames** | **new** | per shot: 2–3 **frame variants**, frame check on each, choose one. The chosen frame is mirrored into `sceneFrames`, so everything that reads it today is untouched |
| 9 | **Shots tab — clips** | **new** | per shot: **Draft takes**, take checks (frozen / black / short / near-copy), re-roll, choose; continuity per shot (from frame, chain from previous, extend for adults) |
| 10 | **Shots tab — timeline + preview** | **new** | chosen clips on a timeline with trims, VO lines and music states shown over their scenes; picture-only preview; the engagement and flow notes are read against what you can now *see*; skip/reorder |
| 11 | Hand-over gate | same | script approved, chosen frames current, a chosen clip for every active shot (or a deliberate skip) |
| 12 | Production settings | same | aspect, duration, voices, music, sound plan, loudness; pre-flight with the frame-check and take-check lines |
| 13 | **Assemble** | **changed** | the existing render path fed the *chosen* clips (no generation): stitch with the frozen check, voice on the real picture, music, mix. The Film tab's one-button render still exists for people who want it |
| 14 | **Promote to Final** | **new** | re-render only the chosen shots at 720p as new takes, then assemble again |
| 15 | Edit room | same (later reuses chosen takes) | cutdowns, re-score, captions, reframe |

What this fixes in one line each: **boring** (hook and surprise at the idea; boredom risk at the draft; engagement read against the real picture), **repetitive / over-cut** (shots are planned and cut as text before any spend), **bad frames reaching a render** (variants + frame check + choose), **one bad clip re-renders everything** (takes and per-shot re-roll), **frozen or corrupt joins** (join guard + take checks), **spend surprises** (an estimate and a choosing point before every rung of the ladder).

What does not change: approval gates, Grounded/Independent modes, the department notes, the voice and sound design layers, the silent master, the Edit room contract, the Film tab's one-button render, and every existing film (no builder data = identical behaviour).
