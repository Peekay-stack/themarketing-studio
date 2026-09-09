---
name: memory-system-not-claudemd-for-continuity
description: "User wants cross-session continuity ('don't restart from zero every morning') — that's the auto-memory system, not CLAUDE.md."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-03T08:03:45.256Z
---

The user's actual goal when they asked for "a memory so I don't restart from 0 every morning" is
served by the **auto-memory system** (`memory/*.md` + `MEMORY.md` index), not by `CLAUDE.md`.
`CLAUDE.md` (in `Heritage Marketing Studio/CLAUDE.md`) is static codebase/architecture reference —
commands, module layout, known gotchas — and should only change when the codebase structure itself
changes. Evolving state (what's done, what's open, decisions made, corrections received) belongs in
memory files, especially [[studio-work-inventory]], which already functions as the running status
log across rounds.

**Why:** on 2026-09-02 the user asked me to "give a solution" for cross-session memory, apparently
unaware `MEMORY.md` is already auto-loaded every session and already tracks exactly this (11 entries,
oldest from mid-August). Proposing to build a new mechanism, or folding evolving state into
`CLAUDE.md`, would duplicate what already works and split the source of truth.

**How to apply:** when asked about session continuity/"picking up where we left off," point to
`MEMORY.md` + [[studio-work-inventory]] rather than editing `CLAUDE.md`. At the start of a new session,
check `MEMORY.md` and [[studio-work-inventory]] before assuming work status, and proactively give the
user a short "here's where things stand" recap without being asked, since that's the behavior they're
after.

**Explicit standing instruction (2026-09-03): save to memory every time a session ends, not just
"substantive" ones.** Before wrapping up — whether the session shipped a fix, only investigated, or was
cut short mid-task — write current state into [[studio-work-inventory]] (or a new memory file if the
topic doesn't fit there): what was done, what's still open, and any plan the user approved but didn't
have built yet (e.g. the round-78 provider-notification plan, queued for "next session"). Do this
unprompted; don't wait for the user to ask or for a natural end-of-round moment.
