---
name: reference-ad-framework-and-log
description: "START HERE for the owner's reference-ads learning log (Oct 2026 on). Where the log, framework and meters live, how to add the next ad, the current state (15 entries, 9 patterns, 31 candidates, 16 open owner questions) and the hard-won measurement lessons."
metadata:
  node_type: memory
  type: project
  originSessionId: 188571ea-55a9-4350-b9a0-481c7a9d13b2
  modified: 2026-10-30T07:28:06.293Z
---

The owner (30 Oct 2026, repeated) sends YouTube ad links one or a few at a time and says "next one for the learning log". Each is read with the SAME framework, logged, compared with our builder's rules, and the owner "will answer queries at the end". Standing instruction: **keep this log in app memory, keep it accessible, and keep updating it as the owner adds campaigns.**

## Where everything lives (kept identical in two places)
- **Memory folder (the always-available copy):** `ad-learning-log.md` (the log), `ad-reference-framework.md` (the 9-question framework + read protocol), `ad-measure-tools.md` (the browser meters + how to read them). All mirrored to `<repo>/.claude-memory/` on branch `coverage` (see [[keep-memory-mirror-in-git]]).
- **Repo copy (worktree `C:\Users\punie\hms-fixes`, branch `film-engagement-2`, not merged):** `Heritage Marketing Studio/AD_LEARNING_LOG.md`, `AD_REFERENCE_FRAMEWORK.md`, `tools/adlab/{measure_ad_all.js, measure_ad.js, measure_ad_seek.js}`. If the two ever differ, the one with the higher entry number is newer; re-copy it over the other.
- Files in memory carry a frontmatter block; the repo copies do not.

## How to add the next ad (the procedure)
1. `mcp__ccd_view__show_pane preview`; open a FRESH FOREGROUND tab (`tabs_create foreground:true`) and check `document.hidden` is false; navigate to the video URL only (drop `&list=...`).
2. Paste `ad-measure-tools.md` -> the one-paste meter; read cuts / audio per second / luma with the read-snippets there; verify the frame count (about 24 a second) and report `hidden`.
3. Take stills (seek, wait 2 s, zoom region [0,50,800,490] scale ~0.35; the seek lands ~0.25 s late; for dark films add `style.filter='brightness(2.4)'`). About 12-20 stills.
4. Write the entry (fact sheet; audience verdict; the nine-question table with evidence tags; "Our system on this ad" table). Evidence levels: MEASURED / SEEN / READ / INFERRED / OWNER-REPORTED / NOT JUDGED. **I cannot hear: never judge voice, music genre or lyrics beyond captions; sound is measured only.**
5. Update the log by splicing: new entry before `## Side by side`; a new row in the side-by-side table (after the last ad's row) and the index (after the last `| 0NN |` row); re-write `## Patterns` if counts change; edit the candidate rows (support counts "for / against / status") and append new candidates after the last `| C.. |` row; append new owner questions as `| Q.. |` rows at the very end under `## Open questions for the owner`. Questions are asked ONLY there (the owner answers at the end). Use PowerShell string replace (no Python on this machine); build the text in files with the Write tool (never shell strings: backticks/backslashes).
6. Copy the repo log to the memory copy (re-add the frontmatter), commit explicit files on `film-engagement-2`, copy the memory folder to `.claude-memory/` and push `coverage`. Update this note's STATE block.

## STATE (30 Oct 2026, after entry 015)
Log entries: 001 Cadbury, 002 Flipkart (PARTIAL, needs a full read), 003 Oral-B, 004 Surf Excel, 005/006 Good Knight (Fastcard, Low Smoke Coil), 007 IPL on Set Max, 008/010 CRED (Bappi Lahiri, Dravid), 009 Fevi Kwik "fish", 011/012 Mother Dairy (25 s ad, 4-min film), 013 Sting, 014 Tata Sky, 015 Uninor. Repo head `film-engagement-2` (see the log's git history). 9 patterns, 31 candidate changes (C1-C31), 16 open owner questions (Q1-Q16). Nothing in the builder has been changed off the ads: changes go through the owner after patterns exist (Q9: at about six ads offer to write a proposals PLAN, not code; we are past that: offer it).

Headlines so far: shots under 2 s are normal in the fast ads; pace is often a curve; one place can carry a film; quiet two-handers hold at 1-4.4 shots/10 s; films end on a held card of 2.2-7 s; **the two dairy films (closest to Heritage: grandmother, ice cream, milk) are cut at Standard-to-Fast, not Calm**; only 015 (a single 31 s take) is Calm. Brand timing: C17 fits 11 of 14 (brand early when the product is in the story's world from the first picture). None of the references is Telugu or a heritage register.

## Measurement lessons (hard-won, 30 Oct)
- Browser pane must be DISPLAYED and the tab visible (`document.hidden` false); unfocused window or hidden tab -> picture meter ~1 frame/s with a false "cut" every second, seeks ~1/s; the sound meter still works. A fresh foreground tab fixes it.
- Cuts: hard cuts only (change >= max(22, 8 x median)); in DARK films use local peaks >= 15 and say "estimated"; cards, fades, dissolves are not cuts; low-res uploads: use the seek meter.
- YouTube auto-captions: good for gist (legible Hindi/English often), unreliable as a script; never quote as the script.
- Seeks land ~0.25 s late; a screenshot right after a seek can be stale/black: wait ~2 s, and verify brightness with the canvas.
- The `MEMORY.md` index must stay under ~17 KB (it was compacted once on 30 Oct): keep one short line per entry.

Related: [[judge-the-film-not-the-pipeline]], [[film-engagement-2-plan]], [[render-holds-signoff-locked-still]].
