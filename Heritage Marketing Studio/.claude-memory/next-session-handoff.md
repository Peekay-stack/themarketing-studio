---
name: next-session-handoff
description: "START HERE (rewritten 28 Oct 2026 evening after the whole-branch wiring audit). Exact state: what is LIVE on master, what is built-but-UNMERGED on branch `coverage` (coverage + craft + the whole film builder S0-S7 + take QC + chain + retention + engagement levers), what the owner must still decide, the ordered next actions, constraints, gotchas, where everything is."
metadata:
  node_type: memory
  type: project
  originSessionId: 188571ea-55a9-4350-b9a0-481c7a9d13b2
  modified: 2026-10-28T10:15:01.546Z
---

**Read this first, then [[flow-higgsfield-research-and-trials]] (the dated BUILD LOG of the film builder, newest at the bottom), `FILM_WIRING_AUDIT.md` in the app folder (the audit of the whole branch), [[change-discipline-working-agreement]], and the lessons [[judge-the-film-not-the-pipeline]], [[git-add-explicit-files-never-directories]], [[project-copies-use-the-opus-folder]].** TODAY'S DATE comes from `date` (it was 28 Oct 2026); earlier notes wrongly said "29 Oct" and were corrected.

## State in one paragraph
**LIVE = master `b1519e6`**: the video engine switch (Omni) + the stitch freeze hotfix (a frozen join). **Everything else is on branch `coverage` (pushed, NOT merged, NOT live; owner rule: localhost first, merge only after their sign-off):** shot coverage + the five film-craft slices (27 Oct); the Film pipeline map; the **film builder** = a new Film step **Shots** (frame variants, clip takes, choose, assemble from chosen clips, Promote to Final, trim, reorder shots/scenes, picture-only preview, take QC, chain continuity, budget cap, x3 + compare, storage retention); and the **engagement levers**: a "Before you approve" panel and the concept routes' hook/surprise/turn/memorable fields. ~65 commits, +11k lines. Local server serves the working tree, so `coverage` must stay checked out.

## What the owner still has to do / decide
- **Click through on localhost** (`FILM_BUILDER_LOCALHOST_TEST.md`, one section per slice; run `run-local.bat` from the exact app folder) and react: S1-S7, the pre-approve panel, the concept fields. Nothing has been checked in a REAL signed-in session (I cannot sign in).
- **Lever #7 (single-person cast references):** needs a paid ~12-image trial; I must QUOTE the cost first. Not built.
- **Optional, not built:** S6 camera presets, S8 Kling elements, S4b Omni extend (deferred: modest gain, refused for child clips).
- **Open from the owner earlier:** compare my Omni $/s estimate with the Google billing page once (the cap is an ESTIMATE); do NOT run the storage purge on LIVE; merge only after sign-off.
- Owner's standing verdict on the re-directed Heritage film: "okay, less repetitive, boring as hell"; do NOT fix or re-render it; a RE-RUN must start from a script written under the new writer rules (and now the concept's hook/surprise/turn/memorable).

## The 28 Oct wiring audit (details in `FILM_WIRING_AUDIT.md`): 3 real defects + stale text found and FIXED
1. **Purge could break a saved Edit-room cut** (the `cuts` store names each beat's `clip_url`; the real tenant's cut named 6 clips): the server now also protects anything saved cuts mention. 2. **Chain continued from the END OF THE FILE** (not what was on screen: a trim, or a 2 s shot cut from a 3 s clip): now `chain_from_at` = the clip's USED end. 3. **Per-film transient state leaked** (Continue ticks, compare mode, open preview survived a wipe/new film): one choke point in `componentDidUpdate` + the loader. Plus: **stale text** (wrong dates, "nothing built" headers, comments). Everything else checked clean: routes (10 added, 0 removed, 0 duplicates, all behind login), persistence round-trips incl. old films, 30 screens render with 0 errors, 7 page-check suites (140+ checks) pass in one session.

## Tests / checks (all green at the end of 28 Oct on `coverage`)
`api/.venv/Scripts/python.exe` with `PYTHONUTF8=1`: `tools/test_builder_s0|s2|s4.py`, `test_takeqa.py`, `test_mediapurge.py`, `test_coverage_plan.py` (golden), `test_scene_shots.py`, `test_omni_video.py`, `test_videoprompt.py`, `test_packqa.py`, `test_stitch_freeze.py`, `test_surfaces_wiring.py`, `test_tools.py`, `checkfe.py`, `partials.py verify`, `api/selfcheck.py` (~1500 calls, 0 problems), `tools/smoke.py` (boots the COMMITTED tree), `tools/golden_prompts.py --compare tools/golden_step5` (75 unchanged). **Page checks** (`tools/page_checks/*.js`, run in the browser pane against the real page with the network stubbed; there is NO JS engine for unit tests): builder_reorder_invariants, builder_sequence_preview, builder_take_qa, builder_chain, builder_budget_storage, builder_state_leaks, film_pre_approve, film_concept_fields.

## Owner working agreements that matter (do not relearn)
Localhost first, live only after sign-off. **Plans before large builds** (blast radius, forward/backward wiring), then "go ahead". Report honestly incl. what was NOT verified. **Think like the audience, not the pipeline.** Quote any paid run first; never guess a price (label official / measured / reported). Explicit `git add <files>`, never a directory (~290 dirty local-tenant files + a dirty `CLAUDE.md` that is not mine).

## Gotchas (new + still true)
- **Shell heredocs eat backslashes** (bit me again on 28 Oct): write any file/patch with backslashes via the Write tool or Edit, never a heredoc. Patch scripts: assert anchors before writing, keep each file's line ending (`main.py`, `filmcut.py`, `filmvoice.py`, `filmaudio.py` are CRLF; `app.dc.html`, `takes.py`, the new modules are LF).
- The app's `.env` key (Anthropic/Google) loads only after `import main`; `complete.has_key()` is False before that. Backend `/complete` is brand-grounded: a cement prompt in grounded mode is refused for the Heritage tenant (use `brand_mode="general"`).
- **The wrapper calls `componentDidUpdate()` with NO arguments**: track previous values yourself (like `_seen`, `_hadBuilder`). `sc.state !== sc.logic.state` (use `logic`).
- Browser pane: `javascript_exec` times out at 45 s (start long runs in the background, poll `window.__x`); the page instance is found by walking the React fiber; screenshots can come back blank (use DOM text); stop the preview server so the owner's `run-local.bat` can use :8000. To run the page checks together, copy them to `api/frontend/assets/_pc/` (served), fetch + `(0,eval)` each, then DELETE the folder.
- Media is mostly IMAGES (frame-* 404 MB, still-* 141 MB of 648 MB local; clips are tiny). The `made` ledger references every frame: a purge leaves its entries without files (the confirm says so).
- `gemini.video` accepts only media-folder paths or data URIs; an unreadable frame path silently falls back to text-to-video (coverage holds such a shot back). Omni min clip 3 s, 7 req/min.

## Where things are
Docs (app folder): `FILM_BUILDER_PLAN.md` (+ build log), `FILM_BUILDER_BENCHMARK.md` (before/after tables), `FILM_BUILDER_LOCALHOST_TEST.md`, `FILM_PIPELINE_MAP.md`, `FILM_ENGAGEMENT_PLAN.md`, `FILM_WIRING_AUDIT.md`, `VIDEO_COVERAGE_PLAN.md`, `VIDEO_CRAFT_FRAMEWORK.md`. Code: `api/takes.py` (builder state), `takeqa.py` (clip checks), `mediapurge.py` (retention), `sceneshots.py`, `flowreview.py`, `framecheck.py`, `filmcut.py` (`trim_window`, `last_frame`), `main.py` (`/take-check`, `/take-look`, `/media-usage`, `/media-purge`, the `only_shot` / `use_clips` / `chain_from` / `chain_from_at` / `chain_beats` render keys), `app.dc.html` (`shotsBoard`, `clipLayer`, `assembleStrip`, `seqPlayer`, `storageStrip`, `preApprovePanel`, `entertainLines`). Media outside the repo: `C:\Users\punie\Downloads\engine-trial\`. Render logs: the claude.ai Render connector (`ToolSearch select:mcp__2edd1d5f-d2e4-4489-a310-3e413b7a9532__list_logs`), service `srv-dagfb76k1f9s73cmr8og`, workspace `tea-dageqc8u01pc73fi55c0` (the project `render` MCP is DNS-dead; its log search was also 503 once).
