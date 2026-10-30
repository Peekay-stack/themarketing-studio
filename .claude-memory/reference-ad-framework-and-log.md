---
name: reference-ad-framework-and-log
description: "30 Oct: the owner's reference-ads thread. A common framework for reading real ads, an append-only learning log (Cadbury logged, Flipkart partial), and a free in-browser measuring tool; plus the measurement lessons."
metadata:
  node_type: memory
  type: project
  originSessionId: 188571ea-55a9-4350-b9a0-481c7a9d13b2
  modified: 2026-10-30T06:26:11.936Z
---

The owner will share real ads that work; for each we ask the same nine questions in builder order (concept, script, shoot board, shots, sound design, music, voice-over, casting, location, plus brand/CTA), compare with our rules (CONFIRMS / CONTRADICTS / EXTENDS / OUTSIDE), and only then consider a change.

**Files (branch `film-engagement-2`, commits `51b85e4`, `8e770ff`, pushed, not merged):** `Heritage Marketing Studio/AD_REFERENCE_FRAMEWORK.md` (ground rules, fact sheet, the questions, protocol), `AD_LEARNING_LOG.md` (index, entries, patterns, side-by-side table, candidate changes C1-C12), `tools/adlab/measure_ad.js` (paste inline into a YouTube watch page).

**State:** Entry 001 Cadbury (e7JATezA1nY) and Entry 003 Oral-B (o9GOkHJTKwY, 20 s, 16 shots, 8 per 10 s, voice-led, known face) fully logged, with a side-by-side table; Entry 002 Flipkart (ppCZ9h_aACw) PARTIAL (needs the full read). Nothing is changed in the builder off the ads yet; candidates C1-C12, five of them at 2 of 3 (sub-2 s shots, same-place, slow-hook by cut rate, carrier classification, silence note, brand-in-first-2 s). Needs a third ad to become a pattern. Owner questions open: what made Cadbury a reference; is a music-led film in scope. Our director's read on the Cadbury shot list not run (about 7 cents, quote first).

**Update 30 Oct (commit `3444138`):** Entry 004 Surf Excel "Puddlewar" (6o6JJIkamVY) logged: slow, picture-led, brand only at 84 %, a 20 dB sound drop under the written tagline, a story coda after the card. With 3 ads, two PATTERNS (visible reversal + stake; one place that never feels like one place) and C4 (what carries the message decides the film's grammar). Three earlier two-ad agreements split (brand in first 2 s, continuous sound, top-of-Fast cut rate). Candidates now C1-C16. **Measurement lesson:** on a 320x240 upload `measure_ad.js` got only 24 frames and fake once-a-second cuts; fallback `tools/adlab/measure_ad_seek.js` (seek every 0.1 s, verify candidates by eye); report shot counts as estimates unless verified. The sound meter was still trusted.

**Update 30 Oct, later (commit `ef5e264`):** Entry 005 Good Knight Fastcard (bon3PB8clIE, a private re-upload; ad = 35 s inside a 42.6 s file) logged: three calm long shots for 11 s then a burst (about 11 per 10 s), 20 dB sound range, near silence under a 1.3 s white end card, brand legible only at 87 %. Log now holds 4 full entries + 002 partial, **5 patterns** (reversal+stake; one place many scales; very short shots normal; pace is a curve; a film's grammar follows what carries the message) and candidates C1-C16. **The owner said (30 Oct): "I will answer your queries in the end - keep asking - consolidate them"; so all questions live ONCE in the log's section "Open questions for the owner" (Q1-Q9, answers recorded as OWNER-REPORTED); add new questions there, not at the end of each entry.** Next: keep reading ads they send; at about 6 ads offer to write a proposals plan (Q9).

**Rules:** evidence levels MEASURED / SEEN / READ / INFERRED / OWNER-REPORTED / NOT JUDGED. I cannot hear: never judge voice, music genre or lyrics; sound is measured only. One ad is a hypothesis, three agreeing ads a pattern, the owner decides, the log is append-only.

**Why:** the owner wants our film rules tested against real ads rather than only our own films ([[judge-the-film-not-the-pipeline]]).

**How to apply (measurement lessons):** (1) the Browser pane must be DISPLAYED (`mcp__ccd_view__show_pane preview`) or the page draws 0 frames and audio reads -180 dB; (2) switch YouTube autoplay off or the tab moves to another video; (3) YouTube's CSP blocks fetching local scripts, so paste the tool inline; (4) the on-page captions are auto-generated and garbled in Hindi, never quote them as the script; (5) the auto cut rule misses cuts in high-motion footage, so there is a `cutsProbable` grade to verify by eye; (6) text with backticks/backslashes goes through the Write tool, not shell strings.
