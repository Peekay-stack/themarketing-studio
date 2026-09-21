# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The Marketing Studio: a FastAPI backend (`api/`) serving a single-file Claude Design frontend
(`api/frontend/app.dc.html`) for a multi-tenant marketing ops product (briefs → creative generation →
approval → campaign/media planning → PR → POS/retail → measurement). A git repo — the root is the parent
`Heritage-Marketing-Studio-OPUS/` folder (remote `Peekay-stack/themarketing-studio`) and Render deploys the
committed `master`. The `.bak`/timestamped copies and `ASK_DESIGN_*.md` files are pre-git history.

## Running it

```bash
cd api
python -m venv .venv && .venv\Scripts\activate     # already exists at api/.venv — don't recreate it
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Or double-click `run-local.bat` from the project root. Open `http://localhost:8000` — this serves
`app.dc.html` live off disk (frontend edits show up on reload with no restart; **backend edits need a
server restart, it does not hot-reload on its own** despite `--reload` being set — verify this before
trusting a "the fix didn't work" result).

- `GET /health` — reports which API keys are visible to the process (no key values shown). Check this
  first when a feature falls back to placeholder content.
- `GET /docs` — full REST API (FastAPI auto-docs).
- `/studio` — the legacy pre-rewrite bundle, kept only for reference; nothing new goes here.
- `/brand-brief-builder`, `/builder` — standalone intake UIs, served from `api/static/`.
- No `ANTHROPIC_API_KEY` → the app still runs; AI features return the frontend's own placeholder copy.
  Optional keys: `FAL_KEY` (image/video via fal.ai), `HEYGEN_API_KEY` (avatar video).
- `STUDIO_TENANT` env var selects the tenant (defaults to `default`); `STUDIO_INSECURE_COOKIES=1` is
  used for local HTTP dev (see `.claude/launch.json` at the **OPUS root**, one level above this folder —
  not the `.claude/launch.json` inside this folder, which the preview tooling ignores).

### Verifying a fix
- Frontend (`app.dc.html`): edit → **reload the browser tab** before judging the result. A fix that
  "does nothing" is almost always a stale page still running the pre-edit bundle, not a logic error.
- Backend (`api/*.py`): edit → **restart uvicorn** before judging the result, same reasoning.
- Prefer loading the actual page in a browser over curl/endpoint checks alone once a screen has real UI
  behind it — several "verified" fixes turned out wrong under a live page after passing an endpoint test.

## Checks (no test suite — these are what stand in for one)

```bash
python tools/checkfe.py          # app.dc.html lexical sanity: run before every edit to that file lands
python tools/partials.py status  # what app.dc.html's ~59 logical sections are and how big
python tools/partials.py verify  # byte-identical split/join round-trip check, changes nothing
python tools/test_tools.py       # tests the tools above against the real file
py_compile api/main.py           # cheapest sanity check after editing the backend monolith
```
`checkfe.py` is a lexical scanner (unterminated strings, bracket balance ignoring quotes/comments/
regex, `sc-if`/`sc-for`/`<div>` pairing, duplicate class members, `bagX()` methods spread-but-undefined
or defined-but-unspread). It is not a parser and does not prove the file runs — only a loaded browser
page does that. Exit 0 is necessary, not sufficient.

## Architecture

**`api/main.py` is a single ~6,100-line FastAPI app** with ~150+ routes covering every product surface
(briefs, social/video generation, campaigns, activation, media planning, PR, POS/retail, measurement,
library assets, film production pipeline). It imports one Python module per domain area rather than
using FastAPI routers — `strategy.py`, `plan.py`, `campaign.py`, `ideas.py`, `pr.py`, `posm.py`,
`sales.py`, `mediaplan.py`, `execution.py`, `media.py`, `geo.py`, `filmcut.py`/`filmaudio.py`/
`filmvoice.py`/`cut.py`/`continuity.py`/`gemini.py` (video pipeline), `docs.py` (docx export),
`activation.py`, `shelf.py`, `producers.py`, `composite.py`, `shots.py`. When adding an endpoint, follow
the existing pattern: thin route in `main.py`, logic in the matching domain module.

**Two frontends, one is legacy:**
- `api/frontend/app.dc.html` — the real, actively-developed UI. A single Claude Design "Design
  Component" file (markup + a `data-dc-script` JS block), ~15k lines, edited by both this backend work
  and by Claude Design (external design tool) in alternating handover rounds. **This file is LF-only —
  Design normalized it deliberately.** Writing it with plain Python `open(path,'w')` on Windows
  reconverts the whole file to CRLF and destroys the ability to diff Design's next handover against
  it. Use the Edit tool (leaves line endings alone), or open Python files with `newline=''` and verify
  `content.count(b'\r\n') == 0` after any write.
- `api/static/index.html` — the old bundle, served at `/studio`, kept for reference only.
- The project root also has several `app.dc.*.html` / `app.dc.MERGED-r*.html` copies — these are
  point-in-time snapshots from the handover process, not alternate live files. The one that matters at
  runtime is always `api/frontend/app.dc.html`.

**Design handover workflow** (`ASK_DESIGN_NN.md` files, `Design_Handover_NN.zip`, `ask-design-roundNN/`
folders, `handover.md`): Claude Design receives a copy of `app.dc.html`, edits it, and hands back a new
version. Their copy is always based on whatever was last sent to them, which is often stale by the time
they reply. **Never drop their returned file in whole** — diff it against the current
`api/frontend/app.dc.html` first (their edits and this session's edits essentially never overlap in
practice, so the diff reads cleanly), take whichever side has the larger delta as the base, and
re-apply the other side's edits on top with anchored find/replace. Run `tools/checkfe.py` after, then
verify live in a browser. Tell Design explicitly which file to base their *next* round on.

**Multi-tenancy** (`tenancy.py`): one deployment can host several companies/brands. Every domain store
(`briefs`, `brands`, `houses`, `plans`, `shots`, `cuts`, `pr`, `pr_map`, `media_ci`, …) is scoped under
`api/tenants/<tenant>/<kind>/...`, resolved through `tenancy.dir("kind")` rather than each module
building its own path. The active tenant comes from the `STUDIO_TENANT` env var (falls back to
`default`) — this is a deliberately simple placeholder, not real per-request auth. Store modules
(`ideas.save()`, `campaign.save()`, `strategy.save()`, etc.) take a plain dict and write straight to
disk keyed by whatever `id` is on it — **there is nothing that distinguishes a test fixture from a real
document**. A throwaway dict passed to `.save()` during manual testing creates a real file under
`api/tenants/<tenant>/...` that then shows up in live listings. Snapshot `api/tenants/` before the
*first* manual test of a session (not just the ones that look like writes), and clean up anything a test
created.

**Auth/approval** (`auth.py`, `domain.py`, `models.py`): a real login system exists — `POST /login`
(httpOnly `studio_session` cookie, PBKDF2-HMAC-SHA256 password hashing), `POST /logout`, `current_user`
dependency — plus a full multi-level approval state machine in `domain.py` (Draft → Pending →
Approved → Live, with a flexible 1–3 level approval chain keyed off campaign objective/budget, and a
publish gate). **This system is not wired to the product's live routes** — the ~150 routes the frontend
actually calls have no `require_auth` on them yet; only the dead `/briefs`/`/users`/`/me` SQL-backed
routes are gated. The live product's data model (`tenancy.py`'s JSON stores) has no identity concept at
all. Check `MEMORY.md` → `studio-work-inventory` (or ask the user) before assuming auth is enforced
anywhere beyond the login/logout routes themselves.

**`*_skill/` directories** (`brief_skill/`, `posm_skill/`, `plan_skill/`, `sales_skill/`,
`strategy_skill/`, `pr_skill/`, `ideas_skill/`): each pairs a `SKILL.md` (domain knowledge / drafting
guidance an LLM should follow for that area — e.g. POS key-visual composition rules) with the Python
module of the same domain name. When a generation route in that domain produces bad output, check
whether the code is actually enforcing what the matching `SKILL.md` already specifies — more than once
the gap was an unenforced rule already written down in the skill, not a missing rule.

**`.bak*` files next to live modules** (e.g. `campaign.py.bak-pre-join`, `main.py.bak-pre-derive`,
`brandprofile.py.bak-pre-kit`) are manual pre-change snapshots the user/prior sessions created before a
risky edit — reference points, not code that runs. Don't import from them; don't treat their presence
as a sign the "real" file is broken.

## Known environment gotchas

- **`.claude/launch.json` at the OPUS root** (`C:\Users\punie\Heritage-Marketing-Studio-OPUS\.claude\`,
  one directory above this project) is what `preview_start` actually reads — the copy inside this
  folder's own `.claude/` is inert for that tool. Its `studio` entry runs
  `.venv\Scripts\python.exe -m uvicorn main:app --port 8000` with `cwd` set to `Heritage Marketing
  Studio/api`, so paths resolve against `api/`, not the OPUS root.
- Never run a scratch/manual test script from inside a scratchpad directory that has accumulated old
  `.py` backups (e.g. copies of `ideas.py`/`campaign.py`) — Python puts the script's own directory at
  `sys.path[0]`, ahead of the real project, so `import ideas` silently loads the stale backup instead of
  the live module. If a module looks impossibly out of date, print `mod.__file__` before anything else.

## Working agreement for every change (agreed with the owner, 19 Sep 2026)

This section is the standing process for any code change here, whether it starts from a bug, feedback or
a new ask. It exists because ~8 of 15 grounding-test rounds were the same rule missing from a sibling
place, and because for two weeks the deployed code was not the code that had been tested. **It is
living: when we learn something new, add it under "Lessons" below with the date -- do not wait to be asked.**

**0. Start from a clean baseline.** Deploy = the committed tree, nothing else. Never leave app code
uncommitted across sessions (commit it, or put it on a branch). If the tree is dirty with someone else's
intent, resolve that first -- a minimal diff is impossible to see against a dirty tree.

**1. Sweep the blast radius BEFORE changing anything.** For the function, field or pattern being changed:
find every caller and consumer across BOTH backend and frontend, and every *sibling* that does the same
thing (grep the symbol, the pattern, and the mistake itself). Ask "where else does this same bug sit?"
The list goes in the plan. Search by symbol/pattern -- do not re-read whole files (`app.dc.html` is 25k lines).
Check what differs between local and live data (live has only the seeded brand; the dev tenant has dummies).

**2. Plan, then implement.** State: the change / why / blast radius (callers + siblings found) / what I will
NOT touch / how it will be verified (local and live) / how to roll back. Size it: *small* (copy, label)
= one line + a quick search; *medium* (logic in one place) = full sweep + local test; *large* (prompts,
data, cross-cutting, anything that changes behaviour users rely on) = written plan and the owner's
approval before building. If the root cause needs a wider change than asked for, STOP and ask -- do not
widen quietly. Design choices are the owner's; ask, do not assume.

**3. Keep everything else the same.** Minimal diff. No drive-by edits, no reformatting, no renames,
no "while I'm here". A fix and a refactor are separate commits. Every changed line must map to a line in
the plan; check `git diff --stat` before committing. `app.dc.html` stays LF-only (0 CRLF).

**4. Verify locally, against the shape live actually has.** `python tools/checkfe.py` (front end),
`python api/selfcheck.py` (call signatures), `python tools/smoke.py` (boots the COMMITTED tree -- run it
before every push), plus a targeted test of the change with live-shaped data (empty overrides, only the
seeded brand), not the dev tenant's dummies. Restart uvicorn after backend edits; reload after front-end edits.

**5. Deploy, then verify live -- and only then hand it over for testing.** Push, wait for the Render
deploy to be `live`, then: `curl https://themarketing-studio.com/selfcheck` (must be `ok:true` and the
`commit` must match what was pushed); scan Render logs since the deploy time for new 5xx/tracebacks;
run whatever use case can be checked without a login. Say plainly what live checking could NOT cover
(login-only routes, real data, real model output) -- never imply a full live pass. Do not use the
owner's credentials or session; do not write test data into the live tenant unless the owner agrees.

**6. Hand over honestly:** what changed, what was verified where (local / live), what was NOT verified.

**7. Record once.** The testing log holds the full entry; the commit message is a few lines; memory gets a
short pointer. Do not write the same account three times.

### Environment gotchas (rediscovered too often)
- Use the venv interpreter `api/.venv/Scripts/python.exe`; plain `python` is not on PATH. Set `PYTHONUTF8=1`
  (the console is cp1252 and crashes on ₹, →, —).
- The shell tool eats one backslash level even in a quoted heredoc: build `\u` escapes with `chr(92)`.
- Local `api/tenants/` is dev data (dummy brands: Kumkum, Loomwell, Parle G, Sthir). Live data is on the
  Render disk `/data` and is a different, smaller set; `.dockerignore` keeps tenants out of the image.
- Git bash `cat` of files with no trailing newline runs their contents together -- delimit ids explicitly.

### Lessons (append new ones, dated)
- 19 Sep: a fix that passed locally only because the dev tenant had a Parle G brand file that live lacks --
  always test with live-shaped data.
- 19 Sep: 60 cross-module calls in the committed tree did not match their functions because backend
  modules were left uncommitted while `main.py` was committed; `selfcheck.py`/`smoke.py` now guard this.
- 19 Sep: an AI-call fallback (`return {}` after a parse failure) hid a failure for two days -- every
  fallback must log why, and output cut off by `max_tokens` must be detected, not silently accepted.
- 19 Sep: a control's label must say what the code does. "Not used in these posts" still let the server attach a
  pack (it decided from the post's own words), and a pack the person PICKED was ignored when those words were
  missing. An explicit choice must always beat a heuristic; when a heuristic is kept, name it in the label
  ("Automatic"). `tools/test_pack_choice.py` pins the matrix.
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
