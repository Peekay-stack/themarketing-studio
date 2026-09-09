---
name: account-migration-plan
description: "User's Claude account expires ~2026-09-13; plan and progress for carrying this project (code, memory, and the Claude Design workspace) to a new account/login"
metadata:
  node_type: memory
  type: project
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-08T06:18:13.673Z
---

**The account this session runs under expires around 2026-09-13.** The last 3-4 months of work on
Heritage Marketing Studio must survive the switch to a new login. See [[studio-work-inventory]] for the
product work itself — this file is the logistics of carrying it forward.

**Why this matters for continuity:** a fresh session (new process, possibly after the account already
switched) should know a migration is in flight and what's done vs. pending, rather than treating "carry
this to a new account" as a brand-new request. Three things have to travel: **the code**, **this memory
folder**, and **the Claude Design workspace**. The first is handled; the second is very likely fine but
unverified; the third is the real open risk.

---

## 1. Code — git repo + backup zips

### Done

- **Git repo** at `C:\Users\punie\Heritage-Marketing-Studio-OPUS` (the OPUS root — captures the app, all
  Design handover history, tenant data, skill zips together). Single branch `master`.
  - First commit `aec8daf7` (2026-09-06), 1,150 files.
  - **Checkpoint commit `241a8c5` made 2026-09-08** (pulled forward from the planned Wed 9th) — 26
    files, +5508/-124. Round 92/93 work (public `landing.html`, `RequireLoginMiddleware`, four-toggle
    grounding, Carousel, PR objectives) plus this session's brand-character backend (`api/character.py`,
    `character_skill/`, `tenancy` KIND, 12 routes in `main.py`) and `ASK_DESIGN_58/59/60`. Working tree
    clean after. `.env` confirmed excluded.
  - Local (repo-only) git identity: `Puneet <punietk@gmail.com>`.
  - `.gitignore` excludes `Heritage Marketing Studio/api/.env` (real live keys — Anthropic, HeyGen, Fal,
    Google, NVIDIA — never committed; `.env.example` is the safe template), plus `.venv/`,
    `node_modules/`, `__pycache__/`. Verified `.env` is ignored and no secret would be staged.
  - `.gitattributes` forces `*.html` to `eol=lf` (user's global git has `core.autocrlf=true`, which
    would otherwise convert `app.dc.html` to CRLF and break Design handover diffing —
    [[app-dc-html-is-lf-not-crlf]]).
- **Extra backup pair made 2026-09-08** (user asked to pull the Friday step forward), both at
  `C:\Users\punie\`, both **verified with a full CRC integrity test** (`zipfile.testzip()`):
  - `claude-memory-backup-2026-09-08.zip` — 102MB, 151 entries. Contains `MEMORY.md`, this rewritten
    plan, and `brand-character-skill-thread.md`.
  - `Heritage-Marketing-Studio-OPUS-backup-2026-09-08.zip` — 1.69GB, 11,145 entries. Contains `.env`,
    the full `.venv`, and the complete `.git/` (the 629MB packfile + `refs/heads/master` + the new
    checkpoint commit as loose objects) — the whole history restores from this zip alone.
  - **TOOLING LESSON — do not use `tar` to make .zip backups on this machine.** The first attempt used
    `tar -a -c -f x.zip`; the bsdtar build here produced archives that `tar -tf` lists fine but that
    Python's `zipfile` / Windows Explorer / 7-zip cannot read (one showed 23 of 12,374 entries, the
    other "not a zip file"). A backup only bsdtar can open is worthless. Both were rebuilt with a
    Python `zipfile` script (`ZIP_DEFLATED`, `allowZip64=True`) and re-verified. Always CRC-test a
    backup zip with a *different* tool than the one that wrote it.
  - The studio server (port 8000) could **not** be stopped by Claude (auto-mode classifier blocks
    `taskkill`, as this plan predicted). The Python zipper read `heritage.db` anyway without error;
    that file holds only re-seedable dev login accounts, so a mid-write copy is low stakes.
  - The Friday pair is still the one that moves; these are the safety net with today's work in.
- **Backup zips made 2026-09-06**, both at `C:\Users\punie\`:
  - `Heritage-Marketing-Studio-OPUS-backup-2026-09-06.zip` (~881MB — plain filesystem zip, does NOT
    respect `.gitignore`, so includes `.venv`/`.env`; intentional, so the new account can keep working
    with the same keys).
  - `claude-memory-backup-2026-09-06.zip` (~91MB) — zip of the whole
    `C:\Users\punie\.claude\projects\C--Users-punie-Heritage-Marketing-Studio-OPUS\` folder.
  - The running uvicorn preview had to be stopped first — `heritage.db` (SQLite) was locked and failed
    the first attempt.

### Pending — Fri 2026-09-11 (final pre-migration step), user runs these

The 2026-09-06 zips are a same-day safety net; the **Friday pair is what actually moves** to the new
account/machine. Steps, in order:

1. **Stop the studio preview server first** (uvicorn on port 8000/8020 etc.) — the SQLite `heritage.db`
   lock will otherwise fail the filesystem zip, same as on the 6th. Do NOT let Claude kill an arbitrary
   process; the user stops it.
2. Final `git add -A` + `git commit` in the OPUS root (message summarising changes since the 2026-09-08
   checkpoint — check `git log -1` and `git diff --stat HEAD` first).
3. Fresh filesystem zip → `C:\Users\punie\Heritage-Marketing-Studio-OPUS-backup-2026-09-11.zip`.
4. Fresh memory-folder zip → `C:\Users\punie\claude-memory-backup-2026-09-11.zip` (this must include
   this updated plan and the new `brand-character-skill-thread.md`).
5. Restart the preview server.

---

## 2. This memory folder

- **Path:** `C:\Users\punie\.claude\projects\C--Users-punie-Heritage-Marketing-Studio-OPUS\memory\`
- **Expectation:** the folder is keyed by **project folder path, not account identity** — so if the new
  login opens the same restored path, it should Just Work. **This is not verified.** Treat it as an
  open item, not a settled fact.
- **Mitigation:** captured in the `claude-memory-backup` zip (remade Friday). If the new account does
  NOT pick the folder up automatically, restoring the zip to the same path is the fallback.
- **Post-switch check:** on the new login, open the project and confirm `MEMORY.md` and the memory
  files load into context. If they don't, the folder path or the account's project index is the
  problem — restore from the zip.

---

## 3. Claude Design workspace — the real open risk

The frontend (`api/frontend/app.dc.html`) is built through **Claude Design**, an external tool, in
alternating handover rounds (`ASK_DESIGN_NN.md` out, a revised `app.dc.html` back — see
[[design-handovers-merge-never-replace]]). The migration plan did not cover this until now.

### What is already safe

The entire handover **paper trail** is in the git repo and both zips: every `ASK_DESIGN_*.md`
(through `_60`), `handover.md`, the `ask-design-round*/` folders, and every `app.dc.html` snapshot.
`app.dc.html` itself is a self-contained single file. Losing Design access would not lose the frontend
or its history.

### What is at risk — user must check BEFORE expiry

1. **Is the Claude Design workspace/canvas bound to the expiring account?** If yes: can it be
   shared with, or transferred to, the new login while the old account is still active? Do this while
   both are reachable — it may not be possible afterwards.
2. **ASK_DESIGN_60 is in flight** (Ground Truth "Brand characters" panel — written 2026-09-08, not yet
   adopted). Any round pending at switch-over has to be re-sent from the new account's Design
   workspace. Keep a note of which round is outstanding.
3. **Design-side-only state** (their canvas edit history, component structure beyond what serialises
   into `app.dc.html`) does not travel in the `.dc.html` file and is not backed up anywhere.

### Fallback if Design access is lost

The latest `app.dc.html` is in the repo. A new Design canvas can be **re-seeded from it** under the new
account (the `design` skill does exactly this). The file is kept; the in-canvas history is lost. The
handover workflow then resumes from the re-seeded canvas.

### Post-switch check

From the new login, confirm the Claude Design workspace opens and `app.dc.html` can still be sent
through a round. If not, execute the re-seed fallback and tell Design which `ASK_DESIGN_*` round to
base the next handover on.

---

## 4. Skills built from this project

- **Packaged / installed:** `posm` / `key-visual-generator` (project-scoped symlink + a standalone
  `key-visual-generator.zip`), and `brand-brief` (installed globally at `~/.claude/skills/brand-brief/`,
  identical to `api/brief_skill/`).
- **Internal only (SKILL.md + module pair, never packaged standalone):** `plan_skill`, `sales_skill`,
  `strategy_skill`, `pr_skill`, `ideas_skill`, and now **`character_skill`** (see
  [[brand-character-skill-thread.md]] — its backend is built, frontend pending via ASK_DESIGN_60).
  These live inside `api/` and travel with the git repo; packaging them as standalone Claude Skills is
  offered, not yet asked for.

---

## 5. Open items

- Verify (post-switch) the new login sees this memory folder — see §2.
- Verify (post-switch) the Claude Design workspace is reachable — see §3.
- Confirm the restored `.env` has the real keys back (deliberately git-excluded, included in the plain
  zip).
- Decide whether to package the six internal `*_skill/` modules as standalone Skills.
- Session-only `CronCreate` reminders were set for the checkpoint dates (job ids `4f77e2ad`,
  `69e86c0a`) — **do not assume they fired**; the user's own phone/calendar reminders are the reliable
  trigger. The 2026-09-08 checkpoint was done in-session, not via the cron.
