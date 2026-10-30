---
name: project-copies-use-the-opus-folder
description: "The machine holds several OLD copies of the Studio project, each with its own run-local.bat; only `C:\\Users\\punie\\Heritage-Marketing-Studio-OPUS\\Heritage Marketing Studio` is current. A page 'missing a feature' on localhost usually means the wrong copy or a stale server on port 8000."
metadata:
  node_type: memory
  type: reference
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-27T15:49:14.407Z
---

**Current project:** `C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\` (git root is the parent `Heritage-Marketing-Studio-OPUS\`; remote `Peekay-stack/themarketing-studio`). Its launcher: `...\Heritage Marketing Studio\run-local.bat` (uvicorn on port 8000, `--reload`).

**Old copies that also have a `run-local.bat` and serve an OLD frontend:** `C:\Users\punie\Heritage-Marketing-Studio-FULL297`, `...FULL-297v2`, `C:\Users\punie\Heritage_Marketing_Studio_FULL`, `_FULL_1/2/3/4`, `C:\Users\punie\Heritage Mkt Studio 1707\...`.

**Symptoms and checks (28 Oct):** the owner ran "the batch file" and the new coverage UI was missing — they had started a different copy. Diagnose in this order: (1) `curl http://localhost:8000/app | grep -c <a new symbol>`; (2) list listeners on 8000 (`Get-NetTCPConnection -LocalPort 8000`) and the process command line/cwd; (3) the app serves the frontend live from disk, so a stale page = another server or a cache (hard-reload); backend edits need a restart (no hot reload). Only one server can own port 8000; the preview server I start is stopped by the app after ~30 min, so for the owner's testing tell them to run the batch file from the exact folder. See [[launch-json-lives-at-opus-root]], [[reload-the-page-after-every-frontend-edit]].
