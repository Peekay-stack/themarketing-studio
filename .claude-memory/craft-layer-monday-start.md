---
name: craft-layer-monday-start
description: "START HERE for the film craft layer: Phase A (W0 brief, scorecard, W1 concept lines, W3 director's read, W10 learning capture) is BUILT on film-engagement-2 behind a flag, off by default, awaiting the owner's localhost test on three briefs. Branch state, how to switch it on, what is left (Phases B-D), open decisions."
metadata:
  node_type: memory
  type: project
  originSessionId: 188571ea-55a9-4350-b9a0-481c7a9d13b2
  modified: 2026-11-03T13:15:44.827Z
---

Plan: [[film-craft-layer-plan]] (repo `Heritage Marketing Studio/FILM_CRAFT_LAYER_PLAN.md`). Evidence: [[ad-learning-log]] ([[reference-ad-framework-and-log]]; purpose "when ads become magical").

## Status, Tue 3 Nov 2026: PHASE A BUILT, NOT MERGED, NOT LIVE
The owner said "hi.. let's start" and approved: Phase A = yes; check vendor data-use terms = yes; GitHub repo private = yes. Built in the worktree `C:\Users\punie\hms-fixes`, branch `film-engagement-2`:
- `1a82bc4` **W0 craft brief**: `api/craft_skill/SKILL.md` + `api/craft.py` (`for_prompt`) wired into `prompts.system_for(..., craft=)` -> `complete.complete` -> `/complete` (`craft: true` in payload). Needs BOTH the server env `CRAFT_BRIEF=1` AND the request flag; otherwise prompts byte-identical (75 goldens unchanged). Test `tools/test_craft_brief.py`.
- `bc23848` **Scorecard** `POST /film-score` (`api/filmscore.py`; 7 tests message/hook/moment/dramatised/device/performance/original, 0-3 + reason, strongest, weakest, one suggestion; unknown is None not 0; advice only, saves nothing). Test `tools/test_film_score.py`.
- `498234d` **W1 page**: "Craft mode" checkbox next to Generate (state `craftOn`, localStorage `tms.craft`, default off); concept prompt asks 5 extra lines (message, move, device, line, cast_idea) only when on; shown on route cards; fed to the script writer (`craftWriterText`); `craft:true` only on the concept and script calls (NOT on judging calls); "Craft scorecard" row in "Before you approve". The concept dict is stored whole, so the new fields round-trip with no `filmscript.FIELDS` change.
- `725dfb9` **W3**: `/film-direct` in craft mode (flag + server switch) adds two questions (one message, a memorable device) -> quiet craft notes; `slow-hook` and `same-place` become `quiet` notes that do not count toward risk; page shows quiet ones as "A note:" and never as the first finding. Test `tools/test_film_direct_craft.py`.
- `ecdba9f` **W10**: `/learning-decision` now keeps `meta` (bounded 4000 chars) with the approved example; page sends `filmDecisionMeta()` (craft_score, craft_lines, entertain) with film approve/reject; nothing sent when there is nothing. Test `tools/test_learning_meta.py` (throw-away `STUDIO_DATA_DIR`).
- Checks run: python tests above + `test_film_direct`, `test_videoprompt` pass; goldens 75 unchanged; `tools/checkfe.py` ok; page check `tools/page_checks/film_craft_mode.js` 29/29 on the real page (server on 8010, stubbed network) and `film_concept_fields`, `film_pre_approve`, `film_concept_delivery` still pass. To run a page check: copy it to `api/frontend/assets/_pc/`, open `/app`, `eval(await (await fetch('/assets/_pc/<f>.js')).text())`, then delete `_pc`.
- Pre-existing failures NOT mine (clean branch head): `test_sound_plan` (11), `test_voice_chirp_routing` (4).
- **Git push**: the first three commits reached origin; `725dfb9` and `ecdba9f` were committed locally and the push failed/hung on GitHub auth ("Authentication failed" for Peekay-stack/themarketing-studio). Re-push once credentials work.

## How the owner tests it (nothing runs until switched on)
1. Start the studio from the worktree with `CRAFT_BRIEF=1` (e.g. `set CRAFT_BRIEF=1` before uvicorn); the key is in the OPUS `api/.env`.
2. Tick "Craft mode" on the Film screen, run THREE real briefs (a dairy one + two other categories), compare routes with what the same brief gave before; run "Score the film" and the Director's read.
3. The owner decides; a slice they dislike is switched off by its flag. No merge without sign-off.

## Vendor data-use findings (3 Nov; report to the owner, sources in the transcript)
Anthropic: no training on customer content. Google TTS stateless/no logging, Gemini paid not used to improve products. ElevenLabs: trains on inputs/outputs unless opted out in the account "Data use" menu (ACTION: opt out). fal: retains request I/O 90 days (header `X-Fal-Store-IO: 0` disables); policy silent on training (ACTION: check the header in code, ask fal for a written statement). Kling/Omni terms not verified.

## Still to do
- Owner localhost test of Phase A (three briefs); log the result in `AD_LEARNING_LOG.md`.
- Phases B-D of the plan (sound/voice, casting, jingle trials ...) wait for the owner; paid calls need a quote first.
- Open decisions: jingle trial language (Telugu/Hindi/English), the two other test briefs, Tata Sky 014 reason; older: place trial, 3-frame look calibration (~$0.15-0.25), Approve-confirm wording, English VO in Telugu film, `coverage-fixes` batch 1 testing.
- Free small checks C19, C20, C22, C40, C42 (see the plan) are still open.
- Run Python with `C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api\.venv\Scripts\python.exe -I` (worktree has no venv). Page file is LF; `main.py`, `filmdirect.py` are CRLF (patch with CRLF-aware scripts); `git add` explicit files only ([[git-add-explicit-files-never-directories]]).
