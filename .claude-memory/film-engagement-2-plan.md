---
name: film-engagement-2-plan
description: 29 Oct plan to fix the 'boring film' verdict (consolidated with B1-B4), branch film-engagement-2; Phases 1-4 BUILT (2-3 real-model checked), audited TWICE (head 69daddb); Phase 5 not built
metadata:
  type: project
---

The owner's second localhost test (29 Oct) said the grandmother film was **boring**. Diagnosis: the concept's one lively beat (quick-cut ritual) became one static shot, the concept VO spine never reached the script (13 spoken words vs a voice budget of 32), one kitchen throughout, silent near-still pack ending. Our own director's read only said medium risk. The writer rules already existed in prose and were ignored; nothing checked delivery.

**Plan:** `Heritage Marketing Studio/FILM_CONSOLIDATED_PLAN.md` (merges B1-B4 + the boring fix; detail in `FILM_BORING_FIX_PLAN.md`). Branch `film-engagement-2` (worktree `C:\Users\punie\hms-fixes`, off `coverage-fixes`), pushed, NOT merged, NOT live.

**Phase 1 BUILT 29 Oct (no model calls):** C1 free 'Delivery' row in Before-you-approve (`af13f39`); C2 `api/filmqc.py` + `POST /film-qc` free 'Render check' (`8b5a27f`).

**Phase 2 BUILT + checked on 6 real calls (`b7a8903`, `8e6801c`):** writer carries the concept voiceover and gives the sign-off speech+motion (real finding: the old 'STRICT SPEECH BUDGET... say less' note was why the voiceover got cut); limb-safety rule in writer/rewrite/planner/concept; concept routes now have a real `stake` field (6 of 6 real routes filled it). Concept voiceover words carried: school hem 9->18, grandmother 13->20, milk moustache 28->30. Still one kitchen; new scripts had 4 scenes (control 5).

**Phase 3 BUILT + checked on 6 real calls (`7161065` + a follow-up):** director's read checks each concept promise (delivered/flattened/missing, concept findings listed first), flags a scene as a RUN of quick actions, planner covers it one shot per action (even when pace would hold it as one). Real result: it caught the grandmother's flattened quick-cuts beat and the milk-moustache film's never-staged split screen; the model called the grandmother's 'surprise' DELIVERED (my earlier 'never filmed' claim was too strong). Same-scene findings count once for risk. Also fixed: Before-you-approve never showed a real read's first finding.

**Phase 4 BUILT (`1689ce8`):** Approve script asks ONCE when a fresh high-risk read, a flattened/missing concept promise, a high flow review or a thin/silent script (free Delivery row) is found; no = stays draft, yes = approves; never blocks.

**29 Oct blast-radius audit (section 12 of the plan):** found + fixed the flow review cutting the planner's shots for a run of quick actions (`flowreview.budgets` now honours the run exemption), the rework prompt lacking the limb rule, and two leftover-state fields; verified saved-film round trip (new test), the 3 real saved films rendering all four Film steps, static checks, all test suites, selfcheck, smoke, trial merge to master (only the 2 known stitch conflicts). `test_exemplar_wording.py` fails in the worktree only because it needs an untracked brand file from the owner's folder.

**Second audit, A1-A8 + B1-B4 (`69daddb`, plan section 12c):** found + fixed (1) the sign-off conflict: the render step ALREADY holds the sign-off pack shot locked and still on purpose, so my writer rule asking it to 'move' with 'a slow push-in' fought it, and my Render check called every held sign-off a fault (both fixed; see [[render-holds-signoff-locked-still]]); (2) 'Re-render out-of-date' had no finally, so a throwing frame locked both bulk buttons; (3) 'Check again' on a render used today's timecodes, not the film's first report windows. Verified: A-batch frame recipe identical to pre-batch code on the 3 real saved films (92 recipes), new Phase 3 shots not counted stale until drawn, fingerprint survives save/load/take copy. B1 and the model half of B2 are NOT built (nothing half-wired); B3 limb rule is in writer, scene rewrite, whole-script rework, planner, concept (NOT the provocation concept route, the Edit-room cutdown re-script, or department drafts); B4 = script-level only because the render already locks the pack.

**Test status at the tip:** 17 page-check suites pass (run them one or two at a time: the browser tool times out at 45 s, and the builder_* suites need a freshly reloaded page); 44 of 48 python test files pass; the 4 that do not are NOT from this work: test_exemplar_wording (needs an untracked Parle-G brand file that lives only in the owner's folder) and test_tools (no api/.venv in the worktree) fail only in the worktree; test_sound_plan and test_voice_chirp_routing ALREADY FAIL on the untouched `coverage` branch (worth a separate look; not yet checked on master).

**How the real-model checks were run (so they can be repeated):** the worktree has no .env; a script reads the key from the main tree's api/.env into os.environ (never print it), puts the worktree api on sys.path, then calls the real routes directly (main.film_direct, main.scene_shots, completion.complete) with the page's own prompts; the page was driven with a throwaway local server on :8765 (a scratchpad sink.py) that served the saved film JSON and received captured prompts. Model: claude-opus-4-8 (GEN_MODEL default), $5/$25 per M tokens; a call costs about 10 cents. Nothing under the owner's tenants folder was written (checked by file times).

**Not built (waiting on the owner's go):** Phase 4 Approve confirm (C8), Phase 5 optional vision checks (B1 on demand, B2b opt-in), and what no phase touches yet: one-kitchen / slow-hook findings still fire on every film; the 4-scene count; English voiceover lines inside a Telugu film (owner question). Each prompt phase needs one real model call to check, quoted first; proof is on THREE saved concepts, not one.

**Open owner questions:** where attention dropped; English narration line in the Telugu film intended?; picture 3 request or comment?; step-bar screenshot before a render (Shots-step question); confirm on Approve or warning only; test batch 1 (`coverage-fixes`) on port 8001.

**Why:** [[localhost-test-findings-28-oct]], [[judge-the-film-not-the-pipeline]]. **How to apply:** do not claim the boring fix is done; Phase 1 only measures, it does not change what the writer produces.
