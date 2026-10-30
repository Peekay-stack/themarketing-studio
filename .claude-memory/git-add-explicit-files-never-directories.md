---
name: git-add-explicit-files-never-directories
description: "In the Studio repo always `git add` named files, never `api` or `tools` or `.`: the working tree holds ~290 dirty local dev-tenant files (media, brands, briefs) that a directory add sweeps into the commit. Caught 28 Oct before pushing."
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-27T15:49:08.840Z
---

**Rule:** stage only files you changed, by exact path (`git add api/main.py api/sceneshots.py tools/test_x.py`). After staging run `git diff --cached --name-only` and refuse to commit anything under `api/tenants/`, `*.jpg`, `*.mp4`, `*.wav`, or files you did not author.

**Why:** on 28 Oct a commit made with `git add api tools` took in ~290 local dev-tenant files (media frames, brand JSON, briefs, platforms) — real user data that must never be committed or deployed. It was caught by reading `git show --stat` before pushing and undone with `git reset --soft HEAD~1 && git reset`, then recommitted with an explicit six-file list. The tree is permanently dirty (the owner works in it), so a directory add is never safe here.

**How to apply:** build the file list from what the task touched; commit with `git commit -F <file>` (message in a file); always `git show --stat HEAD` before `git push`. Related: [[change-discipline-working-agreement]] rule 3 (every diff line maps to the plan), [[synthetic-dicts-write-real-tenant-files]].
