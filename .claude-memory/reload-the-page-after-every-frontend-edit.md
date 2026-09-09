---
name: reload-the-page-after-every-frontend-edit
description: A frontend fix that appears not to work is usually a stale page — the browser keeps running the pre-edit bundle until you reload
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8ceac62b-7222-47d3-9a92-41e0ce0e0317
  modified: 2026-08-25T06:24:09.946Z
---

Editing `app.dc.html` does not change what the open tab is running. The page must be reloaded, or the
browser keeps executing the bundle it loaded before the edit.

This cost three full test cycles on the PR crisis panel: a fix to read `signoff` instead of
`signatures` was correct from the first attempt, but every check said the banner never fired — because
the page was still running the pre-fix code. Adding a temporary in-code debug hook was what finally
forced a reload, which is the only reason it started passing.

**Why:** it looks exactly like a logic error, and it survives reasoning — the code reads correctly, the
API returns the right shape, and the branch "should" fire. The tell is that instrumentation makes the
problem disappear.

**How to apply:** reload after every frontend edit before drawing any conclusion, and treat "the fix
looks right but does nothing" as a stale-bundle symptom first. Same shape as
[[launch-json-lives-at-opus-root]]'s stale-server trap and
[[scratchpad-py-files-shadow-real-modules]].
