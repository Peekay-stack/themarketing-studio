---
name: localhost-test-findings-28-oct
description: The owner's FIRST localhost test of the Film tab on branch `coverage` (28 Oct 2026, evening): what worked, what went wrong (arm-in-motion defect, pack smear, every frame stale after department notes, silent re-timing), and the consolidated change list A1-A8 / B1-B5 awaiting their go-ahead. Start tomorrow from here.
metadata:
  node_type: memory
  type: project
  originSessionId: 188571ea-55a9-4350-b9a0-481c7a9d13b2
  modified: 2026-10-28T14:18:46.308Z
---

**Full detail: `FILM_LOCALHOST_FINDINGS.md` (repo, app folder).** The owner ran the whole Film flow on localhost (Heritage Foods film) and sent 16 screenshots + `C:\Users\punie\Downloads\film-275783e0e9-scored.mp4` (30.0 s, 640x360 Draft, no frozen stretch). I gave a reading of the pictures, judged the film from a contact sheet + enlarged frames + a motion check (no audio listened to), then a consolidated change list. **NOTHING of it is built; the owner has not answered yet.**

## What worked (do not re-test)
Concept hook/surprise/turn/remember lines; the script delivered the hook (scene 1) and surprise (scene 2); director's read / flow review / editor's notes; coverage shots; Slow/Steady/Fast + line-landing controls; the render (stitch fix held). The "Before you approve" panel was not seen only because the script was already approved.

## What went wrong
- **Scene 1 shot 2 (about 2-4 s): the forearm stretches across the face and ends in a stump, no hand.** It is the extra INSERT/DETAIL shot ("isolates the white film on his lip and sleeve"); the storyboard frame was fine, so it only breaks in MOTION. **Scene 6 master (about 27 s): the pack defocuses/swells in the near foreground and the label smears** (the boy walking away is SCRIPTED); then a clean pack hero.
- **After the department notes were drafted every frame went "out of date"** (the frame prompt includes DoP/lighting/props/wardrobe notes; by design) with NO bulk "re-render stale only" button (Generate all frames re-renders ALL), no banner where they work (the count shows only in Production pre-flight), no reason, no warning before it happens.
- **Scene timings silently changed** (0-5s... -> 0-4s...; scene 6 3 s -> 6 s) = the free voice plan re-timing by dialogue (`loadVoicePlan`, on approve / entering Shoot Board); which click triggered it was NOT traced.
- **The concept's turn was a split screen**, which the writer's one-scene-one-frame rule forbids, so it never reached the script. My own lever-#2 "hook = a visible action" rule pushes toward risky actions (arm across a face).
- The one-button render ran NO take checks (they only run on Shots-step clips, and never check anatomy).

## The change list (all NOT built; order = my recommendation)
**Batch 1 (A1-A4, front end):** A1 "Re-render out-of-date (n)" button (Storyboard + Shoot Board); A2 stale banner; A3 show the reason; A4 nudge before drawing frames while DoP/lighting/props/wardrobe are empty + confirm before drafting them when frames exist. **Batch 2 (B1+B2):** B1 extend `/take-look` to 3 frames (25/50/75 %) for limbs + pack smear; B2 QC after a normal render on every shot clip, listed beside the version; **calibrate first** on this film's two bad clips vs good ones (2-3 vision calls, cents: ASK FIRST). **Batch 3 (prompt rules, check each with one real model call):** A5 concept moments must be single-camera/single-frame filmable; B3 risky-action rule (no arm/hand across a face, no hands near the lens) in writer + shot planner + concept prompt; B4 keep the pack sharp / out of defocused foreground on the sign-off master. **Batch 4 (polish):** A6 keep the shot-plan decline reason on the card; A7 say when the voice plan re-times scenes; A8 verify the "Lock location and cast in Live action first" wording. **B5 (owner, no build):** Shots step -> x3 on scene 1 shot 2 and the scene 6 master -> Compare -> choose -> Look -> Assemble.

## UPDATE 29 Oct: batch 1 BUILT on a separate branch (not the owner's test branch)
The owner said they would run one more comprehensive test to confirm the issues are real; I built only what does NOT depend on one run's model output, in a WORKTREE `C:\Users\punie\hms-fixes` on branch **`coverage-fixes`** (commit `c0b06ac`, off `coverage` `a503b13`; pushed, NOT merged, NOT live; their localhost on `coverage` is untouched). **A1-A4, A5 (prompt only, no real model call yet), A6, A7 (trigger traced: `approveScript` -> `loadVoicePlan` overwrote the timecodes silently; now a dismissible note), A8 (wording was wrong: 'Live action' is a different tab).** Why-stale = a per-kind fingerprint (`parts`) stored on each frame + `takes.py`. 32 new page checks + all earlier suites pass; smoke passed. **STILL WAITING for the second test: B1-B4** (prompt rules + motion check; set them from defects that REPEAT). Merge `coverage-fixes` into `coverage` only when the owner chooses (it was cut from `coverage`, so it fast-forwards unless `coverage` moved). Details: `FILM_LOCALHOST_FINDINGS.md` section 5.

## Awaiting the owner
Go-ahead on the order; OK for the 2-3 calibration vision calls; whether B3/B4 also apply to the provocation writer (recommended no).

Related: [[next-session-handoff]], [[judge-the-film-not-the-pipeline]], [[verify-rendered-film-moves]], [[flow-higgsfield-research-and-trials]].
