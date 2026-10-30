---
name: reference-ad-framework-and-log
description: "30 Oct: the owner's reference-ads thread. A common framework for reading real ads, an append-only learning log (Cadbury logged, Flipkart partial), and a free in-browser measuring tool; plus the measurement lessons."
metadata:
  node_type: memory
  type: project
  originSessionId: 188571ea-55a9-4350-b9a0-481c7a9d13b2
  modified: 2026-10-30T06:01:13.594Z
---

The owner will share real ads that work; for each we ask the same nine questions in builder order (concept, script, shoot board, shots, sound design, music, voice-over, casting, location, plus brand/CTA), compare with our rules (CONFIRMS / CONTRADICTS / EXTENDS / OUTSIDE), and only then consider a change.

**Files (branch `film-engagement-2`, commit `51b85e4`, pushed, not merged):** `Heritage Marketing Studio/AD_REFERENCE_FRAMEWORK.md` (ground rules, fact sheet, the questions, protocol), `AD_LEARNING_LOG.md` (index, entries, patterns, candidate changes C1-C7), `tools/adlab/measure_ad.js` (paste inline into a YouTube watch page).

**State:** Entry 001 Cadbury (e7JATezA1nY) fully logged; Entry 002 Flipkart (ppCZ9h_aACw) PARTIAL (needs the full read). Nothing is changed in the builder off one ad; candidates C1-C7 are hypotheses with support count 1. Owner questions open: what made Cadbury a reference; is a music-led film in scope. Our director's read on the Cadbury shot list not run (about 7 cents, quote first).

**Rules:** evidence levels MEASURED / SEEN / READ / INFERRED / OWNER-REPORTED / NOT JUDGED. I cannot hear: never judge voice, music genre or lyrics; sound is measured only. One ad is a hypothesis, three agreeing ads a pattern, the owner decides, the log is append-only.

**Why:** the owner wants our film rules tested against real ads rather than only our own films ([[judge-the-film-not-the-pipeline]]).

**How to apply (measurement lessons):** (1) the Browser pane must be DISPLAYED (`mcp__ccd_view__show_pane preview`) or the page draws 0 frames and audio reads -180 dB; (2) switch YouTube autoplay off or the tab moves to another video; (3) YouTube's CSP blocks fetching local scripts, so paste the tool inline; (4) the on-page captions are auto-generated and garbled in Hindi, never quote them as the script; (5) the auto cut rule misses cuts in high-motion footage, so there is a `cutsProbable` grade to verify by eye; (6) text with backticks/backslashes goes through the Write tool, not shell strings.
