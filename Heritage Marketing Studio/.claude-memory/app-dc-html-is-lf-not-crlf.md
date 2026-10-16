---
name: app-dc-html-is-lf-not-crlf
description: "Patching app.dc.html with Python on Windows silently rewrites all 15k lines to CRLF; Design's file is LF."
metadata: 
  node_type: memory
  type: project
  originSessionId: 8ceac62b-7222-47d3-9a92-41e0ce0e0317
  modified: 2026-08-25T15:54:37.999Z
---

`api/frontend/app.dc.html` is **LF**. Design normalised it deliberately and said so in their round-30
handover. Python's `open(path, 'w')` on Windows translates `\n` to `\r\n`, so any patch written that way
converts the entire file and turns the next Design diff into 15,000 changed lines with the real edits
buried in it. Confirmed 2026-08-25: my copy had 15,631 CRLF and 0 LF, theirs the reverse.

**Why it matters:** the only defence against Design's returns silently reverting a fix is diffing their
base against mine — see [[design-handovers-merge-never-replace]]. A whole-file line-ending change
destroys that diff, which is the one tool that catches the revert.

**How to apply:** prefer the Edit tool, which leaves endings alone. When patching with Python, open with
`newline=''` for both read and write. Verify after any write:
`b.count(b'\r\n')` must be 0. Diff with `.replace('\r\n','\n')` on both sides so a stray conversion
cannot hide content changes.
