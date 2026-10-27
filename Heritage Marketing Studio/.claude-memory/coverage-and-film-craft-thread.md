---
name: coverage-and-film-craft-thread
description: "The 27-28 Oct 2026 thread in one place: shots-within-a-scene (coverage) built on branch `coverage` (unmerged), what the owner found on localhost, their verdict that the first film was mechanically fine but creatively wrong, and the general film-craft framework (director/cinematographer/editor/QC) that replaces the narrow fixes. Read with next-session-handoff."
metadata:
  node_type: memory
  type: project
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-27T15:48:57.890Z
---

Entry point: [[next-session-handoff]]. Dated detail: [[video-edit-consolidated-build-list]]. Plans in the repo: `VIDEO_COVERAGE_PLAN.md`, `COVERAGE_LOCALHOST_TEST.md`, `VIDEO_CRAFT_FRAMEWORK.md`.

## What "coverage" is (owner-confirmed definition)
A **scene** = a place + people + an action. A **shot** = one camera angle of it. Cutting between 2-4 angles inside a scene gives camera movement and a multi-camera feel (reference film ~1.5 s/shot; ours was 4-8 s). A **take** = another attempt at the SAME shot (not an angle) — takes/re-roll is the NEXT build after coverage, then B4 location plates (wide shots invent the room without a signed plate).

## Design (all on branch `coverage`, tested, NOT on master)
- **Design B:** `row.shots` = the EXTRA angles; the scene's own row is shot 1 (master, so approved frames stay valid). A scene's TOTAL seconds never change — coverage only subdivides them (`filmvoice.split_shot_seconds`: whole seconds, shots >= 2 s, <= 8 s, master keeps the rest and stays the longest, last extras dropped + reported when the scene is too short; 4 s holds 2 shots, 6 s -> 3, 8 s -> 4). Frames at `sceneFrames["<idx>.<k>"]`. Extra shots never inherit the master's camera/size/title/desc and carry no spoken words; the scene's line is placed over the WHOLE scene window by the render's existing merge-by-scene-number.
- **Planner** `filmcut.plan_by_scene` expands scenes with shots (single source of truth for every caller); segments carry `shot_k/shots_n/scene_last`; shots after the first are `continues` so roles stay one per scene. Sign-off (`brand`) scene is ONE shot unless `row.signoff_shots` opt-in; then the pack-hero treatment (locked hold + "closing product shot") goes on the LAST shot only.
- **Render** returns `shot_clips` (one record per shot) and holds back a coverage shot with no frame (never text-to-video); messages say "scene 2, shot 3"; cap 48 shots.
- **`POST /scene-shots`** (`sceneshots.py`, reuses `/complete`): a proposal only; camera-POSITION sentence required (sizes alone gave near-copies), objects keep their state, no words/text, wide shots only with a locked location, product hero only for a pack scene, backstops + warnings. **`anglecheck.py`** (96x54 grey correlation vs the master, >= 0.95 = near-copy; verified on the real Step 0 frames) and `/scene-still` returns `angle_check`.
- **Frontend:** Storyboard card "Coverage" strip (Break into shots -> proposal -> Accept/Ask again/Discard -> editable shot tiles, Allow shots on the sign-off), Shoot Board thumbnail strip per scene, counters/hand-over gate count all frames, warning when a scene's shots no longer fit its seconds, cost/time line, cutdowns strip shots, `startCutFromFilm` maps clips by scene (fixed an old misalignment), `settledFrames()` (no permanent spinner), `sceneSecs()=max(4,tc)`.

## Step 0 findings that shaped it (27 Oct)
Omni floor is 3 s (ask 2 -> 3.01 s: generate 3, trim). Close-up/detail frames made from a master HOLD pack/faces/outfit/kitchen; "over-the-shoulder"/"medium" came back as near-copies; a wide invented a different kitchen. `gemini.video` silently fell back to text-to-video when handed a raw file path (a different pack appeared).

## The owner's verdict (28 Oct) — the important part
First real film (`film-20d0ebce67-scored.mp4`, 30.0 s, 14 shots, cut every 2 s, ended on the clean pack) was **mechanically right and creatively wrong**: six drinking shots for 12 s (script had ALREADY shown scene 2 -> 3 as one moment at two scales; the logline "poured glass by glass, months ago" means TIME PASSING, a montage of different days, not angles on one gulp); a shoulder shot "adds nothing"; no pace (a tender Calm film got Fast); a master frame that was two panels of the CAST-LOCK CHARACTER SHEET pasted together (reference bleed); a trouser with legs of unequal length (video stage); milk drops on a face. Root cause (mine): `/scene-shots` asked for the MAXIMUM extras every scene, with no purpose test, no whole-film view, no flow review, no frame review before spend. **Owner's rule: extra shots are for a cinematic feel and must not take away from the story, the entertainment value or the core messaging.** Then: "think like a director + cinematographer + editor combined and deliver the film end to end… frame the logic for ANY other development."

## The framework (design only; `VIDEO_CRAFT_FRAMEWORK.md`)
Five ordered decisions — Director (beat map: purpose, intensity, time-mode, turn + message carrier; repetition = ONE beat; time passing = montage) -> Cinematographer (shot plan: every extra shot has a job + why, ZERO is valid, distinct angle, difficulty flags, pace budget) -> Editor (length follows intensity, cut-rate band, no repetition, transitions on action/match, sound lands on its picture, end on the message carrier) -> QC gates before spend (panel/collage seam, unexpected people, anatomy, hero object, near-copy; ADVISORY) -> render. Pace presets: Calm ~2-2.5 shots/10 s (<=1 extra/scene, scene >= 6 s), Standard 2.5-3.5 (<=2), Fast 3.5-5 (<=3). Brand/category/language-agnostic; proven on a CORPUS of >= 4 different films with director's answer keys. Build order: 1 jobs+Pace+Skip, 2 Flow review, 3 Frame check, 4 beat map + writer rules (+montage), 5 sound/transition notes; then re-direct the Heritage film end to end as corpus case 1. **Awaiting the owner's 5 decisions** (listed in the framework §12 and in the handoff).

## What the owner's film data looks like (for the acceptance test)
`api/tenants/default/filmscripts/063785d77c.json`: logline above; VO "One glass at a time." (English) + two Telugu mother lines; 6 scenes (tc 0-4, 4-10, 10-16, 16-20, 20-26, 26-30); cast lock = a multi-panel character sheet (`/media/still-11a46034de.jpg`); look/wardrobe/camera fields empty; sound plan "warm solo bansuri and soft strings"; dept notes say the memory scenes 2-3 should read as time passing with a warmer light, the hem scene is the emotional turn, "one glass at a time" lands with a beat of silence before it.
