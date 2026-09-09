---
name: scratchpad-py-files-shadow-real-modules
description: "Running a test script from the scratchpad silently imports stale module backups kept there, because Python puts the script's own directory on sys.path[0]"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8ceac62b-7222-47d3-9a92-41e0ce0e0317
  modified: 2026-08-24T16:22:34.635Z
---

Running `python <scratchpad>/test.py` puts **the script's directory** at `sys.path[0]`, ahead of
PYTHONPATH and cwd. The scratchpad has accumulated backup copies of `ideas.py`, `campaign.py`,
`strategy.py`, so `import ideas` inside a scratchpad test loaded a hours-old backup instead of the
live module — presenting as `AttributeError: module 'ideas' has no attribute 'claim_fact'` and an
`EXPRESSIONS` dict missing a key that was demonstrably in the file.

**Why:** it looks exactly like a stale bytecode cache or a bad edit. Clearing `__pycache__` and
re-reading the file both "confirmed" the code was correct, which sent the diagnosis in the wrong
direction twice. The tell is that the same import works when run from a different directory.

**How to apply:** keep module backups in `<scratchpad>/backups/`, never the scratchpad root, and when
a module looks impossibly out of date print `mod.__file__` from inside the failing process before
anything else. Related: [[synthetic-dicts-write-real-tenant-files]].
