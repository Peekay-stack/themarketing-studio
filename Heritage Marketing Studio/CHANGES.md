# Change list — what differs from the original full studio

This is the authoritative list of everything changed to produce the current build.
Note: there is no saved pristine snapshot to run a byte-for-byte `diff` against (the folder
has no git history and was edited in place), so this is a verified, file-by-file account of
every edit — grouped so you can decide scope.

Legend: **NEW** = file added · **MOD** = existing file modified · **REPLACED** = swapped wholesale.

---

## A. Briefs — the change you asked for (merge 3 → one IMC Brief, skill-driven)

| File | Type | What |
|---|---|---|
| `api/brief_ai.py` | **NEW** | Runs the brand-brief skill: prompt + files → drafted brief (competitors, NeedScope pins, CB/CA, SMP). |
| `api/brief_skill/` (SKILL.md + 5 references) | **NEW** | The vendored brand-brief skill instructions used by `brief_ai.py`. |
| `api/brandbrief.py` | **MOD** | Folds the prompt + household data into the brief; used at Word-render time. |
| `api/main.py` → `POST /brand-brief-draft` | **NEW route** | Endpoint the IMC screen calls to draft the brief. |
| `api/static/brand-brief-builder.html` | **MOD** | Rebranded to "IMC Brief" + prompt + uploads + Draft-with-AI. NOTE: now **secondary** — the new frontend has its own IMC screen; this standalone page still exists at `/brand-brief-builder`. |

## B. Beyond briefs — came in with Claude Design's new frontend + its supporting endpoints

> This is the part that means "not only briefs changed." The whole frontend was replaced by
> Claude Design's new build, which reworked the **Video Studio** and added cross-app polish.

| File | Type | What |
|---|---|---|
| `api/frontend/app.dc.html` | **REPLACED** | Old Design build → Claude Design's new build. Briefs **and** Video Studio (now a gated 4-step pipeline: Scripting → Shoot Board → Production) reworked; Word-export buttons, prompt-guide dropdowns, toasts added across screens. |
| `api/frontend/support.js`, `image-slot.js`, `assets/` | **REPLACED** | Runtime files that ship with the new build. |
| `api/main.py` → `index()` | **MOD** | Injects React 18.3.1 + a `window.claude.complete` → `/complete` bridge (the new build needs both). |
| `api/main.py` → `POST /produce-video` | **MOD** | Now returns `{video_url}` and 501 without `FAL_KEY` (was `{url}` + mock). |
| `api/main.py` → `POST /scene-still` | **NEW route** | Storyboard frame image for the Video Studio. |
| `api/main.py` → `POST /brief-docx`, `POST /video-script-docx` | **NEW routes** | Word export for the guided brief and the film script. |
| `api/docs.py` | **NEW** | python-docx builders behind `/brief-docx` and `/video-script-docx`. |

## C. Run/packaging & docs (additive, no behaviour change)

| File | Type | What |
|---|---|---|
| `Start Heritage Studio.bat` | **NEW** | One double-click launcher (venv → deps → opens `.env` → runs). |
| `START HERE.txt`, `IMC_BRIEF_FRONTEND_BRIEF.md`, `CHANGES.md` | **NEW** | Docs. |

## D. Model default — reverted per your instruction

`api/complete.py` and `api/brief_ai.py` default back to **`claude-sonnet-4-6`** (matches the
original). Override anytime with `GEN_MODEL` in `.env`.

---

## E. Unchanged / preserved (verified — no edits)

Backend business logic and every non-brief route are as they were:

- `api/models.py`, `database.py`, `domain.py`, `schemas.py`, `catalog.py`, `generation.py`,
  `creative.py`, `heygen.py`, `prompts.py`, `research_parse.py`, `brief_schema.py` — **untouched**.
- Routes untouched: `/me`, `/users`, `/catalog`, `/platforms`, `/creative-models`,
  `/avatar-options`, `/briefs*`, `/deliverables*`, `/brief-schema`, `/complete`, `/brand-brief`,
  `/shot-still`, `/studio`, `/builder`, `/brand-brief-builder`.
- All screens present in the new frontend: home, briefs, social, video, campaigns, insights, history.
- `web/` (React dev frontend), `Dockerfile`, `DEPLOY.md`, `render.yaml`, run scripts — unchanged.

## The honest limitation

I have not executed this build (no Python/Node in my environment), so I can't behaviourally
confirm the Video/Social/Campaigns/Insights screens are identical to before — the frontend
changes there came from Claude Design's build. The backend logic for those is provably unchanged.
