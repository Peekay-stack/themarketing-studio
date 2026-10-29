---
name: film-engagement-2-plan
description: 29 Oct plan to fix the 'boring film' verdict (consolidated with B1-B4), branch film-engagement-2; Phases 1-3 BUILT and real-model checked, Phases 4-5 not built
metadata:
  type: project
---

The owner's second localhost test (29 Oct) said the grandmother film was **boring**. Diagnosis: the concept's one lively beat (quick-cut ritual) became one static shot, the concept VO spine never reached the script (13 spoken words vs a voice budget of 32), one kitchen throughout, silent near-still pack ending. Our own director's read only said medium risk. The writer rules already existed in prose and were ignored; nothing checked delivery.

**Plan:** `Heritage Marketing Studio/FILM_CONSOLIDATED_PLAN.md` (merges B1-B4 + the boring fix; detail in `FILM_BORING_FIX_PLAN.md`). Branch `film-engagement-2` (worktree `C:\Users\punie\hms-fixes`, off `coverage-fixes`), pushed, NOT merged, NOT live.

**Phase 1 BUILT 29 Oct (no model calls):** C1 free 'Delivery' row in Before-you-approve (`af13f39`); C2 `api/filmqc.py` + `POST /film-qc` free 'Render check' (`8b5a27f`).

**Phase 2 BUILT + checked on 6 real calls (`b7a8903`, `8e6801c`):** writer carries the concept voiceover and gives the sign-off speech+motion (real finding: the old 'STRICT SPEECH BUDGET... say less' note was why the voiceover got cut); limb-safety rule in writer/rewrite/planner/concept; concept routes now have a real `stake` field (6 of 6 real routes filled it). Concept voiceover words carried: school hem 9->18, grandmother 13->20, milk moustache 28->30. Still one kitchen; new scripts had 4 scenes (control 5).

**Phase 3 BUILT + checked on 6 real calls (`7161065` + a follow-up):** director's read checks each concept promise (delivered/flattened/missing, concept findings listed first), flags a scene as a RUN of quick actions, planner covers it one shot per action (even when pace would hold it as one). Real result: it caught the grandmother's flattened quick-cuts beat and the milk-moustache film's never-staged split screen; the model called the grandmother's 'surprise' DELIVERED (my earlier 'never filmed' claim was too strong). Same-scene findings count once for risk. Also fixed: Before-you-approve never showed a real read's first finding.

**Not built (waiting on the owner's go):** Phase 4 Approve confirm (C8), Phase 5 optional vision checks (B1 on demand, B2b opt-in), and what no phase touches yet: one-kitchen / slow-hook findings still fire on every film; the 4-scene count; English voiceover lines inside a Telugu film (owner question). Each prompt phase needs one real model call to check, quoted first; proof is on THREE saved concepts, not one.

**Open owner questions:** where attention dropped; English narration line in the Telugu film intended?; picture 3 request or comment?; step-bar screenshot before a render (Shots-step question); confirm on Approve or warning only; test batch 1 (`coverage-fixes`) on port 8001.

**Why:** [[localhost-test-findings-28-oct]], [[judge-the-film-not-the-pipeline]]. **How to apply:** do not claim the boring fix is done; Phase 1 only measures, it does not change what the writer produces.
