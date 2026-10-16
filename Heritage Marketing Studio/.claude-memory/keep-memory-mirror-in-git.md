---
name: keep-memory-mirror-in-git
description: The user wants the project memory folder mirrored into the repo at .claude-memory/ and kept in sync on every memory change
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-09T15:37:30.877Z
---

The user asked (9 Sep) for the Claude project memory to also live in git — "keep it updated even if
redundant" — because the account is being migrated (~13 Sep) and losing this context is expensive.

**A mirror exists at `<repo root>/.claude-memory/`** — i.e.
`C:\Users\punie\Heritage-Marketing-Studio-OPUS\.claude-memory\` — committed and pushed to
`Peekay-stack/themarketing-studio` (`master`). First mirror commit `8a718b4`.

**Why:** third backup copy of memory. The live copy in
`~/.claude/projects/C--Users-punie-Heritage-Marketing-Studio-OPUS/memory/` is authoritative; the
`claude-memory-backup-<date>.zip` is the second copy; this git mirror is the third, and the only one
that's versioned and off-machine on GitHub.

**How to apply:** after writing or editing ANY memory file (including `MEMORY.md`), copy the changed
file(s) into `<repo>/.claude-memory/`, then `git add .claude-memory/ && git commit && git push`.
Cheapest reliable way — re-copy the whole folder each time:

```
cp "$HOME/.claude/projects/C--Users-punie-Heritage-Marketing-Studio-OPUS/memory"/*.md \
   "C:/Users/punie/Heritage-Marketing-Studio-OPUS/.claude-memory/"
cd "C:/Users/punie/Heritage-Marketing-Studio-OPUS" && git add .claude-memory/ \
   && git commit -m "memory: sync" && git push origin master
```

If the two ever diverge, the `~/.claude/projects/.../memory/` copy wins. `git push` may be blocked by
the sandbox classifier — if so, do the copy + commit and tell the user to push. See
[[account-migration-plan]].
