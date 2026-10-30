---
name: craft-layer-monday-start
description: "START HERE for Monday 2 Nov 2026 (after the weekly limit refreshes): the agreed craft-layer plan (W0-W10), the exact first slice (Phase A), preconditions and the owner's 5 pending decisions, the free small checks that can be done before then, branch state and how to resume."
metadata:
  node_type: memory
  type: project
  originSessionId: 188571ea-55a9-4350-b9a0-481c7a9d13b2
  modified: 2026-10-30T13:02:08.983Z
---

Written Fri 30 Oct 2026 night. The owner said: "build the work in your memory, we will start on Monday with this when the weekly limit is refreshed; in the meanwhile we will pick up some small stuff tomorrow or Monday morning." **Nothing of the craft layer is built.** Full plan: [[film-craft-layer-plan]] (repo copy `Heritage Marketing Studio/FILM_CRAFT_LAYER_PLAN.md`). Evidence and the owner's answers: [[ad-learning-log]] (read [[reference-ad-framework-and-log]] first; the purpose is "when ads become magical").

## State of the ground (verify with `git status` / `git log` before touching anything)
- Worktree `C:\Users\punie\hms-fixes`, branch `film-engagement-2` (pushed, NOT merged, NOT live; plan commit `521c6ac`, log work up to `2b32cf3`). The OPUS tree `C:\Users\punie\Heritage-Marketing-Studio-OPUS` is on `coverage` (memory mirror `.claude-memory/` is pushed from there). LIVE = master `b1519e6`. No merge without the owner's sign-off.
- Run Python via `C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api\.venv\Scripts\python.exe` (system `python` is a Store shim; `py` is 3.14). The worktree has no `.venv` and no `api/.env`; the key lives in the OPUS `api/.env` (read it in-process, never print it; do not copy it into the worktree). `main.film_direct(payload)` can be called in-process without a login (see the 30 Oct director's-read run: `tools/adlab/director_reads_30oct.json`, runner pattern `run_dr.py` in the scratchpad: chdir to the worktree `api`, `-I`, insert the api path).
- The page `api/frontend/app.dc.html` is 31,798 lines, LF only: patch with LF-aware scripts; design handovers are always stale: merge, never replace. Writer rules ~line 15,966 (`VISUAL_RULES`), director call ~16,174 (`/film-direct` body, concept promises), concept lever #2 ~18,795 (`CONCEPT_FOUR`, `conceptFour`), writer prompt ~18,843, `soundPlan` 59 references.

## The owner's 5 pending decisions (ask FIRST on Monday; none answered yet)
1. Approve Phase A (W0, W1, W3, W10) as the first slice, behind a flag, on three real briefs?
2. May I check each vendor's data-use terms (Anthropic, Google, ElevenLabs, fal)?
3. Is GitHub `Peekay-stack/themarketing-studio` private?
4. Which language for the jingle trial (Telugu / Hindi / English)?
5. Which two real briefs besides a dairy one for the test (a different category)?
Also still open from before: Q1 for Tata Sky (014) blank; the owner's 3 decisions from the 30 Oct film work (keep the per-scene place? rewrite buttons replace directly? hold non-last shots of an opted-in sign-off?); the two paid trials (3-frame look calibration about $0.15-0.25; place trial 2 images, price unknown); the Approve-confirm wording untested in a real dialog; English VO in a Telugu film?; the owner testing `coverage-fixes` batch 1.

## Phase A, step by step (when the owner says go)
Rules: flag OFF by default; advice only; every new field optional and absent on old films; quote any paid call; explicit `git add`; sweep blast radius per the working agreement ([[change-discipline-working-agreement]]).
0. Baseline: run the suite as green-first (see the test list in [[next-session-handoff]] plus `tools/test_film_direct.py`, `test_film_concept_delivery.py`, `test_film_saved_roundtrip.py`, `tools/golden_prompts.py --compare tools/golden_step5` = 75 unchanged) and the 7+ page checks in `tools/page_checks` so any later change is attributable.
1. **W0 craft brief:** write `craft_skill/SKILL.md` (about a dozen proposition MOVES, the owner's six reasons, jingle craft, sound layering, an originality guard; NO ad named, no scene copied) following the character-skill pattern; a small `craft.py` `for_prompt()`; wire into `prompts.system_for(..., film=True)` behind a flag (env/tenant). With the flag OFF the 75 goldens must be unchanged; add goldens for ON.
2. **Scorecard:** one model call `/film-score` (message clarity, memorable device, proposition dramatised, performance and casting idea, originality, each 0-3 + one line), run on request only, advice only; calibrate on the reconstructed scripts in `director_reads_30oct.json`.
3. **W1 concept fields:** extend `CONCEPT_FOUR` and the concept JSON the writer requests with `message`, `move`, `device`, `line`, `cast_idea` (routes must differ in MOVE); show on the route card; add the fields to `filmscript.FIELDS` and the roundtrip test; keep them OUT of any picture fingerprint (treat like `SCENE_EXTRAS`).
4. **W3 director's read:** in `filmdirect.py` make `slow-hook` and `same-place` quiet notes (or fire only with `flat-energy`/`no-change`), add the message + device checks to `build_prompt`; update `test_film_direct.py` and `test_film_concept_delivery.py`.
5. **W10 capture:** wire the owner's approve/reject and the scorecard result into `learning.record` / `keep_example` for film approvals (brand-scoped).
6. Verify: Python tests, page checks on the real page (network stubbed), a wiring review like `FILM_WIRING_AUDIT.md`, then the OWNER runs three real briefs on localhost (a dairy one + two others); compare scorecards before/after; log the result in `AD_LEARNING_LOG.md`. A slice the owner does not like is switched off by its flag.

## Free small checks that can be done tomorrow or Monday morning (no spend; each answers a plan "to check")
- C19: run `takeqa.check_clip` logic on a deliberately dark look (mean 25-45 of 255) and see how close the black check (BLACK_MEAN 15, DARK_FRAME 12) is; propose a fix only if a night scene could be flagged.
- C22: does `takeqa` "barely moves" (span under 2.0) flag a deliberate held reaction shot? (test with a still-ish clip).
- C20: compare the sign-off hold length in the render (main.py endframe branch / composite) with the ads' 2.2-7 s end cards.
- C42: read `soundplan.py` / `filmaudio.py` for what exists: is the `sounds` list written automatically per scene, how rich is the sfx library, can music cut out and return?
- C40: what each voice engine in `filmvoice.py` does with `emotion` per line (ElevenLabs stability/style presets; Chirp only voice + pace; Gemini TTS?): write down what can be directed per line.
- Memory hygiene: keep `MEMORY.md` under ~17 KB; keep `ad-learning-log.md` identical to the repo copy.
- New ads from the owner: use the procedure in [[reference-ad-framework-and-log]] (magic row FIRST).
