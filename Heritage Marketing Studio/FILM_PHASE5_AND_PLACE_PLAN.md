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

## Status (30 Oct, built the same day as planned): everything free is BUILT; the two paid trials are NOT RUN
| # | State |
|---|---|
| P5.1-P5.3 | **Built** (`takeqa.frames_jpeg`, `framecheck.vision_prompt(frames=3)` / `look_many`, `/take-look` `frames`, the page's Look sends 3). A new issue id `drift` ("Changes between frames") exists only for a look at several frames. 15 new Python checks, 13 page checks. |
| P5.4 | **Built**: "Look at chosen clips (n) · about $x–$y" on the Shots step, one confirm, one clip after another, stops at the first failure, adds notes only. |
| G1 | **Built**: a scene's own `place` (writer rule + JSON field, script table input, card note "Drawn in: ...", frame prompt and fingerprint, location photo off for that scene, rewrite and shot planner told, director's read told). Frames of scenes with NO place hash and prompt exactly as before: **92 recipes and 92 fingerprints identical to the pre-change code on the three real saved films.** 33 page checks. |
| G2 | **Built**: "Rewrite the opening on the hook" and "Rewrite scene N in a new place" on the director's findings (only when pressed; a confirm on an approved script). |
| G3 | **Built**: a quiet opening that IS the concept's delivered hook says so ("a choice, not a miss"); the finding and the risk are unchanged. |
| P5.5 | **Prepared, NOT run** (needs your OK on the cost): `p55_calibrate.py`, 8 calls. |
| G4 | **Not run** (needs your OK; see the cost note). |

### What the free preview of the calibration clips showed (seen)
Frames the three-frame look would send, taken from single shots of the round-1 film (cut points found first, so every clip is ONE shot):
- **The arm** (scene 1, shot 2): in all three frames the forearm ends in a stump against the mouth and no hand is drawn. One middle frame would have caught this too.
- **The pack** (sign-off master): across the three frames the pack GROWS and slides to the front, ending large and out of focus. **A single middle frame shows a normal-looking pack; only the change across frames shows it.** This is the case the three-frame look is for. **Why it happened (code + saved film):** that scene was an opted-in sign-off (`signoff_shots: true`, with an extra "product" shot), and for an opted-in sign-off the render's locked-still hold goes on the LAST shot only (a deliberate rule, tested in `test_coverage_plan.py`); the master kept the script's own camera cell, which read "Close-up on the pack, gentle rack focus to the doorway behind". So the script asked for the focus to leave the pack. The Phase 2 writer rule that the sign-off's camera cell reads as a locked-off hold on the pack addresses that cause; the render rule is unchanged and still leaves the non-last shots of an opted-in sign-off free to move (an open design question for you).
- **A good clip** (the lab): clean in all three frames.
So the calibration asks the right question: does the model call the pack GROWTH and the arm a defect (with the page's brief), and leave the good clips alone.

### Wiring review of this batch (read from the code, then tested)
- **Where the film-wide Location still applies, on purpose:** the cast-and-location lock (`castRefBody`, `castSig`), the department prompts (`want location`) and the location-photo card say. A scene's own place changes only that scene's frame prompt, the fingerprint, the shot planner's context and the director's read.
- **`place` as a drawing choice (`SCENE_EXTRAS`):** stripped from the prompts built from the script (so a rework cannot lose it) and restored by `keepSceneExtras` while the scene's picture is unchanged, at BOTH of its callers (the whole-script rework and the review's Apply); editing it does not send an approved script back to draft; it is saved with the film (`full_script` is stored whole; a round-trip test covers it).
- **Staleness:** a changed place marks that scene's frame out of date with its own reason; a scene with no place hashes exactly as before (92 + 92 identical on the real films). The director's read is flagged out of date by a change of picture, not by a change of place (a place edit does not make a read stale; the frame banner does).
- **Not touched:** the backend frame, still and clip routes (the place travels inside the prompt text and the existing `use_plate` flag), the render prompts, the cast lock image, the Edit room (a cutdown is written from the script without the place; it is not drawn).
- **Phase 5:** `drift` is accepted only for a look at several frames; `/take-look` without `frames` is byte for byte the old single-frame call (test); the batch button shares the guard with the clip batch; no automatic look anywhere.
- **Known limit (G1):** the cast-and-location reference image is still one image that carries a place, so a scene in another place leans on its prompt against that image (the round-1 lab scene worked, the weaker curd-and-paneer scene did not). G4 measures this on real images and is not run.

## Owner decisions needed
1. G1: per-scene `place` as built above, or keep one location per film and only improve the advice?
2. G2: a rewrite button that replaces the scene text (as "Rewrite this scene" does), or a proposal you accept first?
3. P5.4: is "Look at all chosen clips" shown on the Shots step next to the assemble button the right place?
