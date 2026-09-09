# .claude-memory — mirror of Claude Code's project memory

This folder is a **redundant copy** of Claude Code's per-project memory for this repo. The live
memory Claude reads and writes is at:

    C:\Users\punie\.claude\projects\C--Users-punie-Heritage-Marketing-Studio-OPUS\memory\

That location is outside the repo, so it isn't versioned or pushed to GitHub on its own. It is
backed up separately in `C:\Users\punie\claude-memory-backup-<date>.zip` (see
`account-migration-plan.md`). This mirror is a third copy — in git, versioned, on GitHub — kept
because the Claude account is being migrated and losing this context would be expensive.

**`MEMORY.md`** is the index (one line per note, loaded into context each session).
**`studio-work-inventory.md`** is the main running log of product work.

Kept in sync manually: whenever Claude updates a memory file, it also copies the change here and
commits. If the two diverge, the `~/.claude/projects/.../memory/` copy is authoritative.
