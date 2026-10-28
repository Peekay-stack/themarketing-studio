---
name: flow-higgsfield-research-and-trials
description: "Owner asked (28-29 Oct 2026) for a Google Flow / Higgsfield-style tool to stitch the film. Research on how both work, the replicability verdict, and the two paid trials (Omni extend, Kling elements) with measured results. Read before planning the 'Film builder'."
metadata:
  node_type: memory
  type: project
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-28T05:51:03.059Z
---

**Ask:** "we need to build something like a google flow or higgsfield to stitch the film together" -> "understand the mechanism and see if it is possible to replicate it... deep research first" -> "run the two trials". **NOTHING IS BUILT; the owner has not yet approved a plan.** Their rule: plan + blast radius + wiring first, "go ahead with step N".

## How they work (public docs, not hands-on)
- **Flow:** Ingredients (reference images), Frames to Video (start+end image), Extend (continues from the last ~24 frames; Veo clips only; an extended clip can't then Insert/Remove/camera-edit), Jump to (Gemini writes + generates the next shot), **Scenebuilder = a thin timeline** (add clip to scene, drag to reorder, trim handles, preview, download; ONE scene per project and it resets when you leave), Edit/Refine on Gemini Omni Flash (<=10 s segment of an upload <=60 s, 3 conversational turns).
- **Higgsfield:** an orchestration layer over 15-30+ third-party models (Kling, Veo, Sora, Seedance, Wan...), Elements (saved characters/locations/props), Hero Frame First (still then animate = OUR pipeline), camera rig (sensor/lens/focal/aperture + moves, speed ramps), multi-shot (6 shots/12 s in v2), AI Director breaks a script into shots, genre presets for pacing, Forward/Backward Extend, clips to 30 s in v4.
- **Verdict:** neither is a model; both = asset library + per-shot generation with variations + a continuity mechanism + a thin timeline. We already have frame-first, references, shot plan/director, pace, frame check, stitch/mix. MISSING: clip-level objects, TAKES + selection, timeline (reorder/trim/skip/preview), extend/continue, camera presets. AI films render as ONE monolithic job (`/produce-video`); `/shot-take` and `/shot-select` exist only for live-action shots.

## Trial 1 - Gemini Omni EXTEND (29 Oct; scripts `tools/engine_trials/flow_trial_omni_extend.py`, `flow_trial_omni_cost.py`; outputs `Downloads\engine-trial\flow_trials\omni\`)
- **Works** with `previous_interaction_id` (default store=true; interaction id is the response's root `id`). Each extension returns the WHOLE cumulative video (4 -> 8 -> 11 s); the new part is what you cut from the end.
- **Cost, from the API's own usage block:** a 4 s clip = 7,724 output video tokens (~1,930/s). An extension of +4 s = the SAME 7,724 output tokens (only the new seconds are output) PLUS the previous video as INPUT (6,805 video tokens for 4 s of history). So history is re-read as input each time: cost grows slowly with length. Latency ~50-70 s per extension vs ~20 s per fresh clip.
- **Continuity:** identity, saree, light and scene held across the seam (adult woman, 3 clips); motion continues. A **jump-cut inside an extension worked** (cut to a close-up of the trousers/hand, same light) = Flow's Jump to.
- **Versus our current chain** (animate the LAST FRAME of clip 1): in this test both kept identity; extension keeps motion continuous, the chain restarts from a still pose. Modest difference.
- **BLOCKER: extension of a clip with a CHILD was refused twice by the safety filter** ("harmful content") even with innocuous wording, though the original child clips generate fine. So extend cannot be relied on for the boy scenes; the last-frame chain remains the universal fallback.
- Other limits: append at the END only (no prepend/mid-clip edit); the stored interaction retention is not documented, so keep our own clip files and treat ids as perishable.

## Trial 2 - Kling 3.0 ELEMENTS on fal (script `flow_trial_kling_elements.py` + a scratch k4; outputs `...\flow_trials\kling\`)
- `elements` need `frontal_image_url` AND `reference_image_urls` (or a `video_url`) - frontal alone is rejected by the schema.
- **text-to-video pro with elements: the call was ACCEPTED but identity was NOT held** (boy came back a different, light-skinned brown-haired boy; wide shot too small; mother only loosely similar) - elements appear to be ignored on t2v.
- **image-to-video pro with elements (frontal + 2 references), start frame with NO face:** a face appeared mid-clip and matched the reference woman (bun, bindi, teal saree with cream border). So elements work on i2v and are useful for shots where a face must appear that the start frame lacks. Not a replacement for frame-first.
- **Slow:** 2-4 min per 3-4 s clip on fal (Omni ~20-50 s). fal's listed rates (reported, not measured by us): Kling 3.0 Pro $0.112/s no audio, $0.168/s with audio, $0.336/s with elements + audio.
- Spend this round: Omni ~47 s of 360p output (~$1.6 at our measured $0.034/s; blocked calls may or may not have been billed); Kling 4 clips, 13 s total (check the fal dashboard for the exact charge; cannot exceed ~$4.4 even at the top listed rate).

## What this means for a Film builder (proposal pending the owner's OK)
First slice (my recommendation): per-shot clip objects + TAKES + choose a take + timeline (reorder/trim/skip/preview in-browser from clip URLs) + assemble via the existing stitch (with the frozen-join fix) and mix; Draft-then-Final per shot. Continuity options per shot: fresh from its frame (default), last-frame chain, Omni extend (adults only, optional), Kling elements on i2v (optional). Camera presets = prompt wording + movement_class only (no deterministic camera control on Omni/Kling). Open decisions for the owner: first slice scope, replace vs sit beside the Film tab's one-button render, Draft-then-Final cost model. Related: [[coverage-and-film-craft-thread]], [[video-edit-consolidated-build-list]], [[verify-rendered-film-moves]].

## THE PLAN IS WRITTEN (29 Oct): `FILM_BUILDER_PLAN.md` in the repo root (commit on `coverage`). NOTHING BUILT; awaiting the owner's answers to its section 12 (8 decisions) and their go.
Shape: a Film step "Builder" (per-shot cards, TAKES, choose, trim, reorder, picture-only preview, assemble) that feeds the EXISTING pipeline through two inert payload keys on `_produce_video_sync` (`only_shot`, `use_clips`), so prompts/engines/stitch/mix cannot drift; data = one optional film field `video_builder` {takes, chosen, trim, budget}. Slices (suggested order S0 -> S1 -> S3 -> S2 -> S5 -> S4 -> S7 -> S6 -> S8): S0 foundations (no UI), S1 takes (core), S2 timeline/trim/reorder, S3 assemble + Draft->Final, S4 chain/extend continuity (extend auto-falls-back to chain on child safety refusals), S5 take QC, S6 camera presets (prompt steering only), S7 budget/batches/retention (no media cleanup exists today; local media is 646 MB), S8 Kling elements (optional). Localhost first; owner click-through script per slice; the stitch hotfix to master is a pending owner decision.
