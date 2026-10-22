---
name: nested-sc-for-leaves-ghost-chips
description: A sc-for nested inside another sc-for in app.dc.html renders ghost placeholder items alongside the real ones; build the inner list as a React element instead.
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-22T12:11:21.590Z
---

In `app.dc.html` (Claude Design dc-runtime), a `<sc-for>` placed **inside another `<sc-for>`** renders its `hint-placeholder-count` skeleton items **in addition to** the real list — they do not get cleared, so you get double (e.g. a 6-chip tonality row showed 12 chips: 6 styled+clickable, 6 inline plain-text ghosts with no onClick). The outer sc-for clears its own placeholders fine; only the nested one ghosts.

**Why:** found 22 Oct building the per-line TONE picker inside the `voiceLines` sc-for (`615b69b`). The ghost chips were `display:inline`, no onClick, narrower — visible to the user.

**How to apply:** for a small FIXED inner list (a fixed set of chips/buttons per row), build it as a **React element in the bag** instead of a nested sc-for — `React.createElement('span', {...}, LIST.map(x => React.createElement('span', { key, onClick: handler, style }, label)))` — and render it with a single `{{ l.thing }}` hole. Same pattern already used for inline players (`React.createElement('video'/'audio', …)`). Keep top-level sc-fors (inside an `sc-if`, not inside another sc-for) as normal — those are fine. Related: [[design-contracts-need-shapes-not-names]].
