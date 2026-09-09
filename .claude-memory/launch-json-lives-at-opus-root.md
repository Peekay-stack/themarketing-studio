---
name: launch-json-lives-at-opus-root
description: "preview_start reads .claude/launch.json at the OPUS root, not the one inside \"Heritage Marketing Studio\"; a space in runtimeExecutable breaks it; and its paths resolve against the entry's own cwd of api"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8ceac62b-7222-47d3-9a92-41e0ce0e0317
  modified: 2026-08-26T14:20:03.858Z
---

There are two `.claude/launch.json` files. `preview_start` reads the one at the working-directory root
(`C:\Users\punie\Heritage-Marketing-Studio-OPUS\.claude\launch.json`) — **not** the one inside
`Heritage Marketing Studio\.claude\`. Editing the inner one has no effect.

A `runtimeExecutable` whose path contains a space (the project folder is "Heritage Marketing Studio")
fails to resolve — the error truncates the path at the space and reads as a missing interpreter. The
working form is `"runtimeExecutable": "cmd"` with `runtimeArgs: ["/c", ".venv\\Scripts\\python.exe",
"-m", "uvicorn", "main:app", "--port", "8000"]`, relying on the entry's `cwd`.

**The venv is at `api/.venv`, and that config is correct.** `runtimeArgs` resolve against the entry's
own `cwd`, which is `Heritage Marketing Studio/api` — so `.venv\Scripts\python.exe` means
`api/.venv/...`. Checking for `.venv` from the project root finds nothing and looks like a dead
config; it is not. Verify with `ls api/.venv/Scripts/python.exe` before concluding the venv is missing,
and never create a second one at the project root.

There is a second entry, `studio-verify`, on port 8010. It exists because a server from another chat
often holds 8000 and `preview_stop` cannot stop another chat's process. Note that port 8000 serves
`app.dc.html` fresh from disk on every request but holds the Python modules it imported at startup —
so a frontend edit appears there immediately and a backend edit does not.

**Why:** four failed `preview_start` calls looked like a broken venv when the config being edited was
simply never read; later, a whole redundant venv got built at the wrong level for the same reason.

**How to apply:** editing a launch config here, open the root one first. Related:
[[browser-verification-available]], [[never-put-backslashes-through-a-heredoc]].
