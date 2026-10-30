# Phase 5 (clip checks by a model) and the "one kitchen / slow hook" gap: plan (30 Oct 2026)

Status: **PLAN, written before building.** Branch `film-engagement-2` (worktree `C:\Users\punie\hms-fixes`). Evidence level per line: *seen* (frames, saved films, real model output), *code* (source), *inferred*.

## Part 1. Phase 5: the model's look at a clip (B1 on demand, B2b opt-in)

### What exists (code)
- **Free checks** on every clip (`takeqa.check_clip`, `/take-check`): plays, moves, black, long enough, repeat. No model, no cost.
- **"Look"** on a take (`/take-look`, `lookClipTake`): ONE model call on the clip's MIDDLE frame with the storyboard-frame brief (`framecheck.vision_prompt`): pasted panels, extra or missing people, wrong body, text, mismatch. Advisory chips on the take, never a block. `CLIP_LOOK_IDS` already includes `anatomy`.

### Why that is not enough (seen)
Round 1's broken clip was an arm that stretched across a face between about 2.3 s and 3.9 s of a 4 s shot; the pack smear was in the last second of the sign-off. A single middle frame can land between the two. A limb defect is a change over time, so the look needs several frames and a brief that is about CHANGE between them.

### Build
| # | Change | Layer | Size |
|---|---|---|---|
| P5.1 | `takeqa.frames_jpeg(exe, path, fractions)`: N frames (default 25 / 50 / 75 %), nothing written to disk | Backend | Small |
| P5.2 | `framecheck.vision_prompt(motion=True)` (the frames are in time order from ONE clip: limbs that stretch, split, merge or vanish, a hand or arm crossing a face, a pack that changes shape, size or label, a face that changes identity) and `framecheck.look_many(images, prompt)` (one call, several images) | Backend | Small |
| P5.3 | `/take-look` takes `frames` (default 1, so every existing caller is unchanged); the page's Look sends 3 | Backend + front end | Small |
| P5.4 | **"Look at all chosen clips"** on the Shots step: lists how many and the estimated cost, asks once (like the other paid batches), runs them one after another, stores the chips on each take, says how many were flagged. Opt-in only; nothing runs by itself | Front end | Small-medium |
| P5.5 | **Calibration on real clips before it is trusted** (paid, quoted first): the round-1 bad clips (arm, 2-4 s; pack smear, 26-28 s, cut from `film-275783e0e9-scored.mp4`) against good clips (round 2), through the new 3-frame look | Real calls | 4-6 calls |

Cost shape (code + the price table, not yet measured on this brief): a 640x360 Draft frame is about 300 image tokens, a 1280x720 Final frame about 1,200; three frames plus the brief and a short answer is roughly 1.5k-4.5k tokens in and 300 out: **about 1-3 cents a clip at `claude-opus-4-8` ($5 in / $25 out per million)**; a film of 12 shots about 12-36 cents. `FRAMECHECK_MODEL` can point it at a cheaper model if the calibration shows it is as good.

### Not in this phase (decided)
No automatic look after a render (it stays opt-in), no block on Approve, assemble or Promote, no change to the free checks.

## Part 2. The "one kitchen / slow hook" gap

### What the evidence says (seen + code)
1. **It is structural, not only the writer.** The film has ONE location: the Location line goes into the cast-and-location lock image AND into every frame's prompt as "Location: ...", and one location photo (plate) can be picked. The writer is told to "change the place" (`VISUAL_RULES`), but the machinery then tells every frame it is in the kitchen.
2. **The frames of the round-1 film show what that does.** Drawn with the film-wide kitchen line and the kitchen reference, scene 2 (the lab) came out as a real lab, scene 5 (a street through the window) worked, but scene 3 (the same lab hands testing curd and paneer) came out in the KITCHEN, counter, stove and calendar visible. A strong picture cue wins; a weak one reverts to the locked place.
3. **The director's `slow-hook` finding is two numbers** (scene 1 energy <= 1 and intensity <= 1), also on films whose opening IS the concept's chosen hook (the grandmother's drop on the steel plate). It is advice with no action.
4. `same-place` fires when the model tags 4+ neighbouring scenes with one place; it names no scene to change and has no button.

### Build
| # | Change | Layer | Size |
|---|---|---|---|
| G1 | **A scene can have its own place.** An optional `place` on a script row (a short location line): the writer is told to set it when a scene is NOT in the film's location and to leave it empty otherwise (and to NOT use it as an excuse to leave the locked location without a reason). A frame of that scene gets `Location: <its place>` INSTEAD of the film-wide line, and no location photo is attached; the fingerprint's `loc` part and the recipe include it, so editing a place marks the frame out of date with the right reason. Shown and editable on the scene card. It is a drawing choice like the shot size (so editing it does not send an approved script back to draft) | Front end (+ prompts) | Medium |
| G2 | **The findings get actions** (user-initiated, one model call each, replacing the scene as "Rewrite this scene" already does): on `slow-hook`, "Rewrite the opening on the concept's hook"; on `same-place`, "Rewrite scene N in a new place" for the middle scene of the run (never the first or the sign-off), giving it a `place`. The rewrite prompt takes an optional direction | Front end | Small-medium |
| G3 | **The `slow-hook` finding is told when the opening IS the concept's hook** (the read already says whether the hook was delivered in scene 1): the note says so ("the opening is the concept's chosen hook, a quiet one: make it faster only if you want") instead of the generic warning; the risk is unchanged | Backend | Small |
| G4 | **Proof on real images** (paid, quoted first): redraw round-1 scene 3 (the curd and paneer test) with its own `place` and compare with the kitchen-contaminated frame; same scene, same seed, same reference | Real calls | 2 images |

### What this does NOT do (stated)
- It does not make a second location photo or a second cast lock: the cast-and-location reference image is still one image that carries a place, so a scene in a different place leans on the prompt against that image. G4 measures how far that goes. If it is not far enough, the next step (not in this plan) is a cast-only reference or a per-place lock, which is a bigger build.
- It does not change how many places a film should have: a one-room film stays valid; this only stops the system from fighting a script that leaves the room.

## Order and cost
Phase 5 first (self-contained), then G1-G3, then the two paid trials (P5.5 about 4-6 cheap vision calls; G4 two images). I will quote each paid run before it starts. Every free step ends with the page checks, the Python tests and a wiring review like the two audits.

## Owner decisions needed
1. G1: per-scene `place` as built above, or keep one location per film and only improve the advice?
2. G2: a rewrite button that replaces the scene text (as "Rewrite this scene" does), or a proposal you accept first?
3. P5.4: is "Look at all chosen clips" shown on the Shots step next to the assemble button the right place?
