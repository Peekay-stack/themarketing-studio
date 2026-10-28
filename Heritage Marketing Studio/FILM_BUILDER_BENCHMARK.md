# Film builder — change list and benchmark

Source: `git log` on branch `coverage`, `FILM_BUILDER_PLAN.md` build log, and a fresh run of every suite on the `coverage` head
`b89c102` (28 Oct 2026, before any S2 change). Each later slice is compared against the **Baseline** column.

## 1. What changed, slice by slice (the previous chat's work)

| Change | Commit | Date | Size | What it did | Verified | NOT verified |
|---|---|---|---|---|---|---|
| Stitch freeze fix (`filmcut.stitch`) | `a59aa4d` on `coverage`; **`b1519e6` on master (LIVE)** | 27-28 Oct | +126, 2 files | A joined film no longer shows ONE frame for seconds: the join is checked (`frozen_join`) and rebuilt with the concat filter if frozen | synthetic 5-clip case, smoke, selfcheck, live `/selfcheck` | the seven real Heritage clips (not on the deploy machine); a real signed-in live render |
| S0 foundations | `26e8624` | 28 Oct | +394/-5, 4 files | `takes.py`, `video_builder` film field, inert `only_shot` / `use_clips` render keys | `test_builder_s0.py` | — |
| S1a frame variants | `eb3c7b9` | 28 Oct | +319/-32, 4 files | Frame takes with history + choose; the Shots step; 15 wipe-sites now also clear the builder | tests + page driven with stubbed fetch | — |
| S1b clip takes | `08f683d` | 28 Oct | +371/-37, 7 files | Per-shot clip generate / re-roll / choose / recover through `only_shot`; found + fixed the `only_shot: 0` falsy bug (would have been a full paid render) | tests; one real Draft clip (scene-3 master, 6 s) | many real clips |
| S3 assemble + Promote to Final | `81928cd` | 28 Oct | +222/-19, 7 files | `use_clips` assemble is strict (400 naming the shot); real clip length wins; Draft+Final join in one film | tests; page driven with stubbed fetch | a real signed-in assemble; a paid Promote to Final |

Totals: 5 changes, **1,432 lines added, 93 removed**, 24 files touched (some repeatedly). Only the stitch fix is on master; S0-S3 are on `coverage` (pushed, not merged, not live).

## 2. Baseline (before S2) — the numbers every later slice must hold or improve

Run on `coverage` @ `b89c102`, `api/.venv/Scripts/python.exe`, `PYTHONUTF8=1`.

| Check | Baseline result |
|---|---|
| `tools/test_builder_s0.py` | ALL PASS (45 checks) |
| `tools/test_coverage_plan.py` | ALL PASS (79) — the golden snapshot must stay byte-identical |
| `tools/test_scene_shots.py` | ALL PASS (101) |
| `tools/test_omni_video.py` | ALL PASS (24) |
| `tools/test_videoprompt.py` | ALL PASS (33) |
| `tools/test_packqa.py` | ALL PASS (19) |
| `tools/test_stitch_freeze.py` | ALL PASS (13; real-clip case skipped here) |
| `tools/test_surfaces_wiring.py` | all cases behave |
| `tools/test_tools.py` | 18 passed, 0 failed (flaky once on S3, unexplained, 2 sightings) |
| `tools/checkfe.py` | all checks passed |
| `tools/partials.py verify` | byte-identical, 2,549,195 bytes through 72 parts |
| `api/selfcheck.py` | **1,473 cross-module calls, 0 problems** (master: 1,406) |
| `app.dc.html` line endings | LF only (0 CRLF) |

## 3. Film-quality benchmarks (the audience's test, not the pipeline's)

| Benchmark | Baseline |
|---|---|
| Heritage re-directed film (30 s Draft, 7 shots) | owner verdict: "okay, less repetitive, boring as hell" — **not fixed on purpose**; a RE-RUN from a script written under the new writer rules is the next film benchmark |
| Frozen-picture check on every produced film | 1-frame-per-second contact sheet + `frozen_join`; must pass before "works" |
| Omni cost | Draft ~ $0.034/s, Final ~ $0.101/s (measured 27 Oct); a 2 s shot is generated at 3 s |

## 4. S2 acceptance targets (set before building)

1. Every baseline row above still passes; selfcheck problems stay 0; `app.dc.html` stays LF-only.
2. A film with no trims and no reorder assembles **byte-for-byte the same request** as today (`test_builder_s0.py` unchanged and green).
3. Trim: the trimmed take file is never modified; the assembled film's length = the sum of kept windows (within 0.05 s); voice follows the kept picture.
4. Reorder (when built): frames, takes, trims, notes and captions all still belong to their scenes afterwards (an invariants test), in one atomic update.
5. Timeline total, preview and the assembled film agree.

## 5. After S2a (trim) — measured against the baseline

| Check | Baseline | After S2a |
|---|---|---|
| `test_builder_s0` | 45 pass | 45 pass |
| `test_builder_s2` (new) | - | 20 pass |
| `test_coverage_plan` / `scene_shots` / `omni` / `videoprompt` / `packqa` / `stitch_freeze` | 79 / 101 / 24 / 33 / 19 / 13 | 79 / 101 / 24 / 33 / 19 / 13 |
| `test_surfaces_wiring`, `test_tools` | behave, 18/0 | behave, 18/0 |
| `checkfe`, `partials verify` | pass, 2,549,195 B | pass, 2,554,606 B |
| `selfcheck` | 1,473 / 0 problems | 1,476 / 0 problems |
| `app.dc.html` CRLF | 0 | 0 |
| Size of the change | - | +47/-3 in `main.py` + `filmcut.py` (CRLF kept), +63/-6 in `app.dc.html`, +1 test file |

Acceptance targets met so far: 1 (baseline holds), 2 (no trims = same request: pinned in `test_builder_s2`), 3 (source file untouched, length = window within a frame or two). Targets 4 and 5 (reorder invariants; timeline = preview = assembled film) wait for S2b-S2d.

## 6. After S2b + S2c (reorder) — measured against the baseline

| Check | Baseline | After S2a | After S2b+S2c |
|---|---|---|---|
| Python suites (s0, s2, coverage_plan, scene_shots, omni, videoprompt, packqa, stitch_freeze) | 45 / - / 79 / 101 / 24 / 33 / 19 / 13 | + s2 = 20 | unchanged (backend not touched) |
| `test_surfaces_wiring`, `test_tools` | behave, 18/0 | same | same |
| `checkfe`, `partials verify` | pass, 2,549,195 B | pass, 2,554,606 B | pass, 2,562,979 B |
| `selfcheck` | 1,473 / 0 | 1,476 / 0 | 1,476 / 0 |
| `app.dc.html` CRLF | 0 | 0 | 0 |
| Page invariants (`tools/page_checks/builder_reorder_invariants.js`) | - | - | **18 / 18 pass** |
| Size of the change | - | +47/-3 backend, +63/-6 frontend | +93/-2 frontend only, +1 page-check file |

Acceptance target 4 (reorder invariants: frames, takes, trims, notes and captions follow their scenes, atomically, with an invariants test) is MET by the page test (and the exact round trip). Captions: they are derived from each row's timecode at render, and the two swapped rows' timecodes are re-laid. Target 5 (timeline = preview = assembled film) waits for S2d.

## 7. After S2d (preview) — S2 complete

| Check | Baseline | After S2a | After S2b+S2c | After S2d |
|---|---|---|---|---|
| Python suites | 45 / - / 79 / 101 / 24 / 33 / 19 / 13 | + s2 = 20 | unchanged | unchanged |
| `test_surfaces_wiring`, `test_tools` | behave, 18/0 | same | same | same |
| `checkfe`, `partials verify` (bytes) | pass, 2,549,195 | 2,554,606 | 2,562,979 | pass, 2,569,574 |
| `selfcheck` | 1,473 / 0 | 1,476 / 0 | 1,476 / 0 | 1,476 / 0 |
| `app.dc.html` CRLF | 0 | 0 | 0 | 0 |
| Page checks | - | - | reorder invariants 18 / 18 | + sequence preview 14 / 14, + one real-playback run |
| Size of the change | - | +47/-3 backend, +63/-6 frontend | +93/-2 frontend | +57/-1 frontend, +1 page-check file |

**S2 acceptance targets:** 1 baseline holds: MET. 2 no trims and no reorder = the same request: MET (pinned in `test_builder_s2`). 3 trim leaves the take untouched and the length is the window: MET. 4 reorder invariants: MET (page test, exact round trip). 5 timeline = preview = assembled film: preview = Timeline is MET and asserted; preview = assembled film is MET by the same length rule and by one real playback of the preview, but a real signed-in assemble has NOT been compared (the server can re-time scenes by dialogue at render).

## 8. After S5 (take QC)

| Check | Baseline | After S2d | After S5 |
|---|---|---|---|
| Python suites (s0, s2, coverage_plan, scene_shots, omni, videoprompt, packqa, stitch_freeze) | 45 / - / 79 / 101 / 24 / 33 / 19 / 13 | + s2 = 20 | unchanged; **+ takeqa = 26** |
| `test_surfaces_wiring`, `test_tools` | behave, 18/0 | same | same |
| `checkfe`, `partials verify` (bytes) | pass, 2,549,195 | 2,569,574 | pass, 2,576,404 |
| `selfcheck` | 1,473 / 0 | 1,476 / 0 | 1,492 / 0 (the new routes' calls) |
| `app.dc.html` CRLF | 0 | 0 | 0 (`main.py` CRLF kept; `takes.py`, `takeqa.py` LF) |
| Page checks | - | reorder 18, preview 14 | + take QC 19 |
| Size of the change | - | +57/-1 frontend | +74/-2 frontend, +56 `main.py`, +2/-2 `takes.py`, +86 `takeqa.py`, 2 test files, 1 calibration script |

**Detection benchmark (the new one):** 37 real clips from 6 engines measured (29 of them are the test's regression set): **0 false alarms** on still / black / unreadable; synthetic known-bad: frozen 4/4 flagged, black flagged, fade-in-from-black flagged as a dark frame, short flagged; repeats: same-frame pairs flagged (first-frame difference 1-8), different angles/scenes not flagged (56+). Thresholds and the evidence are in the plan's S5 entry and `tools/engine_trials/takeqa_calibration.py`.

## 9. After S4a (chain continuity)

| Check | Baseline | After S5 | After S4a |
|---|---|---|---|
| Python suites (s0, s2, takeqa, coverage_plan, scene_shots, omni, videoprompt, packqa, stitch_freeze) | 45 / - / - / 79 / 101 / 24 / 33 / 19 / 13 | + s2 20, takeqa 26 | unchanged; **+ builder_s4 = 18** |
| `test_surfaces_wiring`, `test_tools` | behave, 18/0 | same | same |
| `checkfe`, `partials verify` (bytes) | pass, 2,549,195 | 2,576,404 | pass, 2,580,391 |
| `selfcheck` | 1,473 / 0 | 1,492 / 0 | 1,496 / 0 |
| `app.dc.html` CRLF | 0 | 0 | 0 (`main.py`, `filmcut.py` CRLF kept) |
| Page checks | - | reorder 18, preview 14, take QC 19 | + chain 21 |
| Golden / inert | golden snapshot | identical | identical (`test_coverage_plan` unchanged; a single-shot render with no chain keys is pinned as before in `test_builder_s4`) |
| Size of the change | - | +74/-2 frontend, +86 takeqa | +43/-7 frontend, +62/-6 `main.py`, +14 `filmcut.py`, +1 `takes.py`, 2 test files |

**Not measured yet (needs a paid run):** whether a chained clip from the real engine is a smoother join than two separately animated frames, and whether identity and the pack hold when a clip starts from a video's last frame. The code paths are proven; the visual result is not.

## 10. After S7 (budget, batches, retention)

| Check | Baseline | After S4a | After S7 |
|---|---|---|---|
| Python suites (s0, s2, s4, takeqa, coverage_plan, scene_shots, omni, videoprompt, packqa, stitch_freeze) | 45 / - / - / - / 79 / 101 / 24 / 33 / 19 / 13 | + s2 20, s4 18, takeqa 26 | unchanged; **+ mediapurge = 20** |
| `test_surfaces_wiring`, `test_tools` | behave, 18/0 | same | same |
| `checkfe`, `partials verify` (bytes) | pass, 2,549,195 | 2,580,391 | pass, 2,593,060 |
| `selfcheck` | 1,473 / 0 | 1,496 / 0 | 1,498 / 0 |
| `app.dc.html` CRLF | 0 | 0 | 0 (`main.py` CRLF kept, `mediapurge.py` LF) |
| Page checks | - | reorder 18, preview 14, take QC 19, chain 21 | + budget/storage 29 |
| Size of the change | - | +43/-7 frontend | +124/-8 frontend, +21 `main.py`, +129 `mediapurge.py`, 2 test files |

**Disk benchmark (local tenant, measured before building):** media folder 648 MB in 665 files: frame 404 MB (418), still 141 MB (148), kv 122 MB (31), shot 6.7 MB (21 clips), bed 3.0 MB, vo 0.9 MB. A video clip averages about 0.3 MB; a frame about 1 MB. At that rate the 10 GB live disk holds roughly 10,000 frames, so frame variants (up to three per press, files never deleted before S7) are the thing to watch.

**Safety benchmark (retention):** 20 checks including hostile names (traversal, other folders, full URLs, voice/music/key-visual/trim/cast files), everything a saved film uses kept even when named, dry run by default, a string "false" is still a dry run, the 500-file cap. Nothing in the real tenant was deleted during testing.
