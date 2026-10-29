---
name: film-engagement-2-plan
description: 29 Oct plan to fix the 'boring film' verdict (consolidated with B1-B4), branch film-engagement-2; Phase 1 (free checks C1 + C2) BUILT, Phases 2-5 not built
metadata:
  type: project
---

The owner's second localhost test (29 Oct) said the grandmother film was **boring**. Diagnosis: the concept's one lively beat (quick-cut ritual) became one static shot, the concept VO spine never reached the script (13 spoken words vs a voice budget of 32), one kitchen throughout, silent near-still pack ending. Our own director's read only said medium risk. The writer rules already existed in prose and were ignored; nothing checked delivery.

**Plan:** `Heritage Marketing Studio/FILM_CONSOLIDATED_PLAN.md` (merges B1-B4 + the boring fix; detail in `FILM_BORING_FIX_PLAN.md`). Branch `film-engagement-2` (worktree `C:\Users\punie\hms-fixes`, off `coverage-fixes`), pushed, NOT merged, NOT live.

**Phase 1 BUILT 29 Oct (no model calls):** C1 = free "Delivery" row in the Before-you-approve panel (spoken words vs `voBudget`, floor = HALF of it because the budget is deliberately sparse; silent sign-off; dropped concept VO; wordless film skipped), commit `af13f39`. C2 = `api/filmqc.py` + `POST /film-qc` + a "Render check" panel under the film (barely-moves scene, frozen stretch, silent tail; ffmpeg only, auto after a render and on demand), commit `8b5a27f`. Calibrated on the real round-2 mp4: scene 5 motion 0.16, silent tail 1.7 s. Checks: 15 + 12 new page checks, 21 Python tests, all earlier suites, selfcheck 1501/0, golden 75 unchanged.

**Not built (waiting on the owner's go):** Phase 2 prompts (C3 writer: carry VO, sign-off speaks and moves, no arm across face = B3, pack sharp = B4; C4 concept stake; C5), Phase 3 director's concept-delivery + sequence flag + planner (C6, C7), Phase 4 Approve confirm (C8), Phase 5 optional vision checks (B1 on demand, B2b opt-in). Each prompt phase needs one real model call to check, quoted first; proof is on THREE saved concepts, not one.

**Open owner questions:** where attention dropped; English narration line in the Telugu film intended?; picture 3 request or comment?; step-bar screenshot before a render (Shots-step question); confirm on Approve or warning only; test batch 1 (`coverage-fixes`) on port 8001.

**Why:** [[localhost-test-findings-28-oct]], [[judge-the-film-not-the-pipeline]]. **How to apply:** do not claim the boring fix is done; Phase 1 only measures, it does not change what the writer produces.
