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

## One-paragraph state
The video ENGINE switch is **LIVE and done** (Gemini Omni path + 429 limiter + Kling fallback + prompt compiler + advisory pack-shape check; master `811fd16`, live `/selfcheck` ok; fal's Veo deprecation on 17 Nov is no longer a risk). **Shots within a scene ("coverage")** is built, tested and click-tested by the owner on localhost, but lives ONLY on branch **`coverage`** (19 commits ahead of master, **NOT merged, NOT on the portal** — owner rule: localhost first, merge only after their sign-off). The owner's verdict on the first real coverage film (28 Oct): **mechanically fine, creatively wrong** (over-shot, repetitive, no story judgement, bad frames reached the render). They then told me to **think like a director + cinematographer + editor and frame the logic for ANY film, not just this one** -> I wrote **`VIDEO_CRAFT_FRAMEWORK.md`** (design only). **Nothing from it is built. I am waiting for the owner's 5 decisions.**

## What to do first tomorrow (in order)
1. **Do not build anything yet.** Open with a 3-line recap and ask for the 5 decisions in `VIDEO_CRAFT_FRAMEWORK.md` §12: (1) pace presets Calm/Standard/Fast numbers + default from the brief's tone with one-click override, (2) QC gates are ADVISORY (person can accept), (3) which 3 other film kinds for the proof corpus (I propose product-demo explainer, fast lifestyle montage, testimonial), (4) "time passing" = a MONTAGE treatment not more coverage, (5) the build order. The owner answers in short messages ("go ahead with step N" is their go signal; they like "tell me first").
2. When they confirm: build **slice 1 "shot plan with jobs + Pace + Skip"** on branch `coverage` (see the framework §10): `/scene-shots` may return ZERO extras, each shot has `job` + `why`, whole-script + logline + VO + brief proposition as context, film-level `pace` caps extras, per-shot `skip` (kept, not rendered/counted; planner honours it; golden must stay identical), UI chips + Skip switch. Then slice 2 **Flow review** (`POST /film-review`), slice 3 **Frame check** (`framecheck.py`: deterministic panel/collage seam detector + vision check; pre-flight), slice 4 beat map + writer rules (+ montage), slice 5 sound/transition notes.
3. **Acceptance test they will care about:** run the flow review on THEIR film (`film-20d0ebce67-scored.mp4`, data `api/tenants/default/filmscripts/063785d77c.json`): it must flag scenes 2-3 repetition (one beat at two scales, and the logline means time-passing), the scene-5 shoulder shot (adds nothing), scene-1 hem-leg artifact, scene-5 master collage, and land near ~9 shots. Then **re-direct that film end to end** (storyboard -> frames -> render) as corpus case 1 and deliver it.
4. Still owed to the owner from the older list (ask which they want next): the **small fix** "Generate all frames skips a scene's extra shots when they were added after the loop passed that scene"; the rest of the localhost script (steps 10-14: Production hand-over, Edit room, a 20 s cutdown, rework carry-through); **merge `coverage` to master** as separate commits + live checks ONLY after their localhost sign-off.
5. Then (their order, 26-27 Oct): takes + single-shot re-roll (B5 part 2), wide+tight location plates (B4, moved up because wide shots invent the room), the Edit-room cutdown-fidelity build A1-A7 (decision D1 still open; recommend reuse original clips/frames for surviving scenes), C1/C2 extras. Parked: Remotion (skills downloaded, NOT installed).

## State of the repo / live
- Repo root for git: `C:\Users\punie\Heritage-Marketing-Studio-OPUS\` ; app folder **`Heritage Marketing Studio\`** (use EXACTLY this folder — see [[project-copies-use-the-opus-folder]]). Branch now: **`coverage`** (never switch it silently: the owner's local server serves the working tree). `origin/coverage` is pushed (head `70785b3`). Master head `811fd16` = what is live (selfcheck ok).
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
