---
name: design-handovers-merge-never-replace
description: "Claude Design's app.dc.html handovers are based on a stale copy — always merge their delta onto the OPUS file, never drop theirs in whole."
metadata: 
  node_type: memory
  type: project
  originSessionId: 27396459-a562-47a1-a61d-312c29b2c1b0
  modified: 2026-08-13T04:26:00.068Z
---

Claude Design builds `app.dc.html` from whatever copy they last received, so their handover **lags any
edit made in OPUS since**. Their READ_ME will say "drop it in whole" and it will be wrong.

On 2026-08-13, handover 6 (the next-layer button) was based on a copy taken before that morning's logo
fix. Dropping it in whole would have silently reinstated a bug that had already survived three rounds.

**How to handle every handover:**

1. Diff their file against the OPUS `api/frontend/app.dc.html` first — `difflib.SequenceMatcher` on
   lines, printing changed blocks with the first line of each. Design's edits and mine have never
   overlapped, so the diff reads clean and it is obvious which blocks are whose.
2. Take **their** file as the base when their delta is larger (it usually is), then re-apply my edits on
   top with an anchored find/replace script that asserts exactly one match per anchor and writes nothing
   if any assertion fails.
3. Run `tools/checkfe.py` — the class-member count is the cheapest proof a method landed.
4. Verify in the browser, not just the checks.

Tell Design in every reply which file to base the next handover on. They will otherwise use the one they
sent. Better still, hand them an anchored patch spec (see `PATCH_logo_for_design.md`) and let them
re-apply — it avoids an 800KB transfer that gets pasted and truncated, and it is safe now that the result
can be verified in a browser.

Related: [[browser-verification-available]]
