---
name: wardrobe-fixed-manually-in-shootboard
description: "User is fine handling wardrobe/scene-specific continuity by editing script visual text or Shoot Board department notes before rendering — don't over-build automatic detection for this."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-02T05:51:41.981Z
---

After the round-60 wardrobe fix (softening `/scene-still`'s unconditional "identical clothing" clause,
see [[studio-work-inventory]]), the user confirmed they're comfortable handling any remaining
wardrobe/continuity mismatches manually: editing a scene's own `visual` text directly in the script
table, or the relevant Shoot Board department note, before regenerating that frame.

**Why:** there is no per-scene wardrobe field in the data model (only one global "Wardrobe & Styling"
department note per film) — building real per-scene structured wardrobe would be a data-model + Design
change. The user explicitly said this level of manual correction (editing the scene's own description
text, which is directly editable and persists, per [[reload-the-page-after-every-frontend-edit]]-style
UI mechanics) is an acceptable workflow rather than something worth automating further right now.

**How to apply:** don't propose building automatic per-scene wardrobe detection/enforcement unless the
user raises it again. If a similar continuity gap comes up (e.g. props, accessories), the same "edit the
scene's own visual text, or the department note, before regenerating" answer likely applies — point to
that UI path first rather than assuming a backend fix is wanted.
