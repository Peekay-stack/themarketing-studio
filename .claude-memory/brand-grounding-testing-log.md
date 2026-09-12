---
name: brand-grounding-testing-log
description: "A standing log the user wants kept — every round of their testing feedback on the Grounded/Independent toggle, paired with what was found and fixed, appended after every round"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-12T06:54:34.807Z
---

**File**: `Heritage Marketing Studio/BRAND_GROUNDING_TESTING_LOG.md` (repo root of the studio project).

**The instruction (12 Sep 2026):** the user asked for a prompt-by-prompt log of their user-testing
feedback on the brand-grounding-modes toggle (see [[brand-grounding-modes-project]]) starting from
their first bug report, paired with the solution applied after each round — and to **keep updating it
after every subsequent round of feedback**, not just write it once.

**How to apply:** whenever the user reports a bug/issue with this feature (or any follow-on testing
round on it), after fixing it:
1. Append a new `## Round N` section to `BRAND_GROUNDING_TESTING_LOG.md` — never rewrite or renumber
   past entries, only add.
2. Each entry: the feedback verbatim (quote it, including screenshot descriptions where relevant), the
   root cause(s) found, and what was actually fixed — same level of detail as the existing entries.
3. This is a testing-feedback log specifically — distinct from `BRAND_GROUNDING_MODES_PLAN.md` (the
   build plan) and [[brand-grounding-modes-project]] (the build-status memory). Don't fold one into
   the other.

Three rounds logged so far as of 12 Sep: Round 1 (toggle not reaching the IMC skill's own drafting
path — `brief_ai.py`'s brand-invention fallback; General→Independent rename); Round 2 (collapsed four
separate per-tab toggles into one master toggle after live testing showed two disagreeing pills read
as broken; added an "Independent work" row to the header's brand dropdown); Round 3 (Grounded mode
never auto-filled the IMC screen's Brand/Category fields from the active profile — fixed on screen
entry, on switching back to Grounded, and on switching to a different active brand).
