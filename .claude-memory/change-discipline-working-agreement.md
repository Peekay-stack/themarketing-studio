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
- 21 Sep: prove the risky generation step on the owner's REAL example before building anything around it. The pack
  designer got a full backend, its own store, a panel and 35 passing tests; the owner's first real try (the
  real Nourish+ pack attached) came back as a generic white pouch, and it was dropped. Tests on the decision
  side (which images are attached, what the prompt says) say nothing about whether the model's output is any
  good. For a feature whose whole value is image fidelity, show that fidelity first: one prompt, the real
  product photo, the owner's eyes -- ten minutes, before any wiring.
- 21 Sep: ask what real example the owner will try first, and do not merge two cases under one prompt. I designed for
  'a product with no pack shot' and one 'shape only, ignore the artwork' instruction; the owner's real product
  already had a clean photo and wanted 'in line with' it, which is the opposite instruction.
- 21 Sep: `grep -c $'\r'` in this shell is unreliable -- it returned the line count on a pure-LF file and led to a
  wrong 'file is CRLF' reading. Before concluding anything about line endings, count bytes with Python
  (`b.count(b'\r\n')`).
- 21 Sep: never infer a file's type from an item's display NAME. Two front-end places did (image vs video from the
  name's extension); it only worked because names were file names. Once names became editable, a plain rename
  would have broken the thumbnails -- read the type from the stored file.
- 21 Sep: an image model obeys the SCENE text as well as your wording. A scene that asked for 'the nutrition panel
  visible' got an invented table on a background jar even though the prompt said no printed facts, and a scene
  that pours from a pouch got a second drawn pouch. Fix upstream (tell the writer what NOT to describe) and
  add a narrow deterministic backstop on the scene text; do not expect one more wording line to win.
- 21 Sep: when a control 'does not work', reproduce it by driving the real page (real clicks, real keys, network
  stubbed) and read the server log for whether the request ever left the page, before theorising. 'Rename does
  not work' was 'Enter does nothing'. Every text box should save on Enter and cancel on Escape.
- 21 Sep: a shell heredoc turned regex word-boundary escapes (backslash-b) into invisible backspace bytes in a new
  module -- it compiled, and only a SyntaxWarning on a neighbouring escape gave it away. Write any file that
  contains backslashes with the Write tool, never a heredoc, and check `b.count(bytes([8]))` and `python -W
  error -m py_compile` afterwards.
- 22 Sep: "get to a stage where you can live deploy" is the owner delegating the remaining per-item decisions (ship
  with known limits, keep an option, style a fix) once the substance -- the trial proof -- is in hand; it is
  not the same as silence, and proceeding through the working agreement's normal gates (tests, smoke, push,
  live gate) still applied. Distinguish it from a genuinely open creative question (there is a right test to
  run, not a taste call the owner has to make).
- 22 Sep: a shell double-quoted -m commit message breaks the moment the message itself contains a double-quoted phrase
  (here, a literal \"on the side\") -- git then reads the rest of the message as separate pathspecs and
  refuses. Write any commit message with quotes, apostrophes or code fragments to a file and commit with `git
  commit -F <file>`, never inline with -m.
- 22 Sep: when a live screenshot shows something clipped or missing, reproduce it in the browser with the REAL content
  shape (actual-length brand name, every sibling element a real session would render) before trusting an old
  measurement's number -- a prior round's own comment estimated '1600px fits by 0px' for this exact nav, and a
  fresh in-browser measurement with real content found it still clipping at 1700px. Old arithmetic is not a
  substitute for measuring the current real thing.
