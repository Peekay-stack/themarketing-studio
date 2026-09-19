---
name: change-discipline-working-agreement
description: "Standing process for EVERY code change (agreed with the owner 19 Sep 2026, applies to all future work, any project): sweep blast radius first, plan, keep everything else the same, verify local then live, only then hand over. Living doc -- append lessons when we learn them."
metadata:
  type: feedback
---

The owner asked for this after ~8 of 15 grounding-test rounds turned out to be the same rule missing from a
sibling place, and after live returned HTTP 500s for a day because the deployed `main.py` was newer than the
deployed modules (60 mismatched calls found by `api/selfcheck.py`). Full text lives in the project's
`Heritage Marketing Studio/CLAUDE.md` ("Working agreement for every change") -- keep the two in step.

**The rules (short form):**
0. Deploy = the committed tree only. Never leave app code uncommitted across sessions; start each change from a
   clean baseline (commit or branch pending work first).
1. BEFORE changing anything, sweep the blast radius across BOTH backend and frontend: every caller/consumer of what
   is changing AND every sibling that does the same thing ("where else does this same bug sit?"). Search by
   symbol/pattern, don't re-read big files. Note what differs between local and live data.
2. Plan then implement: change / why / blast radius / what I will NOT touch / verification / rollback. Small =
   one line + quick search; medium = full sweep + local test; large = written plan + owner approval first. If the
   root cause needs a wider change than asked, STOP and ask. Design choices are the owner's.
3. Keep everything else the same: minimal diff, no drive-by edits or reformatting, fix and refactor in separate
   commits, every diff line maps to the plan, check `git diff --stat` before committing.
4. Verify locally against the shape live has: `tools/checkfe.py`, `api/selfcheck.py`, `tools/smoke.py` (boots the
   COMMITTED tree -- run before every push), and a targeted test with live-shaped data.
5. Deploy, then verify live BEFORE handing over: Render deploy `live`, `GET /selfcheck` ok + commit matches, scan
   logs since deploy for new 5xx, run any use case checkable without login. State what live checking could NOT
   cover. Never use the owner's credentials/session; no test data in the live tenant without asking.
6. Hand over honestly: what changed, verified where, NOT verified.
7. Record once: log = full entry, commit message = few lines, memory = pointer. Don't write it three times.

**Why the live limit exists:** I cannot log in to live (won't handle credentials), so login-only routes, real brand
data and real model output are checked by the owner. Anonymous checks (deploy status, served bundle, /selfcheck,
logs) are read-only and safe; anything that writes to live (toggling Independent persists server-side, creating
briefs, LLM calls that cost money) needs the owner's agreement.

**Lessons (append new ones, dated -- do not wait to be asked):**
- 19 Sep: test with live-shaped data (live has only the seeded Heritage brand; dev tenant has 4 dummy brands).
- 19 Sep: a static call-signature audit + a smoke test of the committed tree would have caught the 60 broken calls.
- 19 Sep: every AI-call fallback must log why; detect output cut off by max_tokens instead of accepting it.
