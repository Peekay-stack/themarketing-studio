---
name: next-session-handoff
description: "START HERE (rewritten end of 28 Oct 2026 for the next session). Exact state: what is LIVE on master, what is built-but-UNMERGED on branch `coverage`, the owner's verdict on the first coverage film, the film-craft framework awaiting 5 decisions, the ordered next actions, constraints, gotchas, file locations."
metadata:
  node_type: memory
  type: project
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-27T15:49:46.812Z
---

**Read this first, then [[coverage-and-film-craft-thread]] (the full state of the current thread), [[video-edit-consolidated-build-list]] (dated log of everything), [[change-discipline-working-agreement]], and the three lessons [[judge-the-film-not-the-pipeline]], [[git-add-explicit-files-never-directories]], [[project-copies-use-the-opus-folder]].**

## One-paragraph state (updated 28 Oct, late)
The video ENGINE switch is **LIVE and done** (master `811fd16`). **Coverage (shots within a scene) AND film-craft slices 1-3 are built, tested and committed on branch `coverage`** (head `5a14522`, pushed; **NOT merged, NOT on the portal** — owner rule: localhost first, merge only after their sign-off). The owner approved the whole craft framework ("all five fine, go ahead with slice 1", "you can build tomorrow now"), so the next work is NOT waiting on decisions. Built: **slice 1** shot plan with job + why + Pace (Calm/Standard/Fast) + Skip; **slice 2** Flow review (`/film-review`); **slice 3** Frame check (`/frame-check`, vision). Full detail + real-run results in [[coverage-and-film-craft-thread]] (BUILD LOG at the bottom).

## What to do next (in order)
1. **Slice 4 — beat map + writer rules** (framework D1-D6, section 8): a `filmdirect` step / the script writer's rules ("one beat per scene, say the time-mode", montage treatment for time-passing, hero-object continuity). **Slice 5 — sound/transition notes** (E4-E5).
2. **Re-direct the owner's Heritage film end to end** (`api/tenants/default/filmscripts/063785d77c.json`; storyboard -> frames -> Draft render) using slices 1-3 and deliver it for their eyes; then the >= 4-film corpus (add a product-demo explainer, a fast lifestyle montage, a testimonial, each with a hand-written answer key; score the review + proposer against them). Real model runs on the owner's film are cheap and safe (`tools/engine_trials/flow_review_real.py`, `frame_check_real.py` write nothing).
3. Owed small items: "Generate all frames skips a scene's extra shots when added after the loop passed that scene"; a render-stage check for leg/limb defects that only show in the MOVING clip (frame check passes them as stills); the Production hand-over/Edit-room/20 s cutdown/rework localhost steps; **merge `coverage` to master** as separate commits + live checks ONLY after the owner signs off on localhost. Tell the owner what to click: Pace bar under "Camera & lens", Skip on shot cards, "Review the flow" and "Check the frames" panels above the storyboard.
4. Then (their order): takes/re-roll (B5 part 2), B4 wide+tight location plates, the Edit-room cutdown-fidelity build A1-A7 (D1 open), C1/C2 extras. Remotion parked.

## State of the repo / live
- Repo root for git: `C:\Users\punie\Heritage-Marketing-Studio-OPUS\` ; app folder **`Heritage Marketing Studio\`** (use EXACTLY this folder — see [[project-copies-use-the-opus-folder]]). Branch now: **`coverage`** (never switch it silently: the owner's local server serves the working tree). `origin/coverage` is pushed (head `5a14522`). Master head `811fd16` = what is live (selfcheck ok).
- Working tree also holds a lot of UNCOMMITTED local dev-tenant data (`api/tenants/...`, ~290 files), `CLAUDE.md` modified, untracked `api/static/test_wheel_chart.pdf`, build scripts one level up. **Never `git add` a directory** ([[git-add-explicit-files-never-directories]]).
- Live portal = master. Nothing coverage-related is on it. The Omni engine path IS on it (a real Draft render through the portal login was never done by me — I cannot sign in; the owner can).

## Tests / checks (all green at end of day on `coverage`)
`api/.venv/Scripts/python.exe` with `PYTHONUTF8=1`: `tools/test_coverage_plan.py` (golden equivalence + invariants + render route + sign-off opt-in), `tools/test_scene_shots.py` (62+), `tools/test_omni_video.py` (24), `tools/test_videoprompt.py` (33), `tools/test_packqa.py` (22), `api/selfcheck.py` (1427 calls, 0 problems), `tools/test_surfaces_wiring.py`, `tools/test_tools.py` (18), `tools/checkfe.py`, `tools/smoke.py` (boots the COMMITTED tree). The **golden snapshot** `tools/golden/coverage_golden.json` (written from the unmodified code) must always stay byte-identical for films with no shots.

## Owner working agreements that matter (do not relearn)
- **Localhost first, live only after their sign-off.** They click through on `http://localhost:8000/app` and send screenshots; I verify in the pane with stubbed network + read server logs. I cannot sign in.
- They want **plans before large builds**, blast radius + forward/backward wiring, then "go ahead with step N". Report honestly incl. what was NOT verified. Own mistakes plainly.
- **Think like the audience, not the pipeline** ([[judge-the-film-not-the-pipeline]]).
- Shots exist for **cinematic feel without hurting story, entertainment or core messaging**.
- The local server: the **preview server I start gets stopped by the app after ~30 min** (that caused "couldn't render" + a stuck spinner earlier). Backend edits need a restart; frontend is served live from disk (hard-reload). Tell the owner to run `run-local.bat` from the exact folder for a durable server; only one server per port 8000.

## Where things are
- Docs in repo: `VIDEO_COVERAGE_PLAN.md` (the coverage plan + Step 0 results §11), `COVERAGE_LOCALHOST_TEST.md` (owner's click-through), **`VIDEO_CRAFT_FRAMEWORK.md`** (the new general logic).
- Code (branch `coverage`): `api/sceneshots.py`, `api/anglecheck.py`, `api/packqa.py`, `api/videoprompt.py`, `api/gemini.py` (Omni), `filmcut.plan_by_scene` (+`extra_shots`, `shot_view`), `filmvoice.split_shot_seconds`, `main.py` (`/scene-shots`, `_rows_for_planning`, `shot_clips`, sign-off opt-in), `app.dc.html` (`coverageStrip`, `shotTile`, `shotStrip`, `settledFrames`, `sceneSecs`, `shotsDropped`).
- Media (outside repo, local): `C:\Users\punie\Downloads\engine-trial\` — `coverage_step0\` (angle frames + stitched cuts), `coverage_step2\` (first coverage film), `coverage_step3\proposals.json`, `owner_film\film_sheet.jpg` (sheet of the owner's film); the owner's film `C:\Users\punie\Downloads\film-20d0ebce67-scored.mp4`. Trial scripts: `tools/engine_trials/` (committed).
- Artifacts: Engine playbook https://claude.ai/artifact/TQ4v3So79uCASppWBmkiNF · Video Engine Trial https://claude.ai/artifact/TwYR3GaERo9fmbkPhC4sK5 · build-list page https://claude.ai/artifact/3oiRZQU67HTaeEg8hfwg9A (stale vs this thread).
- Render logs: the project `render` MCP is DNS-dead; use the claude.ai Render connector (`ToolSearch select:mcp__2edd1d5f-d2e4-4489-a310-3e413b7a9532__list_logs`), service `srv-dagfb76k1f9s73cmr8og`, workspace `tea-dageqc8u01pc73fi55c0`.

## Gotchas (new + still true)
- Line endings (verified 28 Oct by byte count): **CRLF** = `main.py`, `filmaudio.py`, `filmvoice.py`, `filmcut.py`; **LF** = `gemini.py`, `creative.py`, `sceneshots.py`, `anglecheck.py`, `packqa.py`, `videoprompt.py`, `packscene.py`, `filmscript.py`, `continuity.py`, `app.dc.html`. Re-verify any other file with `b.count(b'\r\n')` vs `b.count(b'\n')` before patching. Patch scripts: normalise to LF, assert exact anchor counts BEFORE writing, write back in the file's own ending. **Write patch scripts to a file with the Write tool** (a shell heredoc eats backslashes/quotes; it failed 3 times this thread, incl. Windows paths with `\U`).
- `gemini.video` accepts only media-folder paths or data URIs; an unreadable frame path silently falls back to TEXT-TO-VIDEO (a different pack appears) — coverage now holds such a shot back instead.
- A frame saved as `status:'rendering'` used to restore as a permanent spinner — fixed by `settledFrames()`.
- Gemini image latency can spike to minutes (one scene frame took 3 m 20 s, still 200 OK).
- The cast-lock image is often a multi-panel CHARACTER SHEET; the image model can paste its panels into a frame (scene-5 collage) — the framework's Q1 gate exists for this.
- Omni: min clip 3 s (ask 2 -> 3.01 s), rate limit 8 req/min Tier 2 (limiter holds 7), no audio-off, prompts of "child drinks" blocked at 6-8 s in hand-written probes but NOT in studio renders (cause unknown).
- Never guess a price: label official / measured / reported.
- **Memory mirror:** the authoritative memory is this local folder; its git mirror (`Heritage Marketing Studio/.claude-memory/`) is committed on whatever branch is checked out (now `coverage`) — do NOT switch to master just to mirror (the owner's local server serves the working tree). It reaches master when `coverage` is merged.
