---
name: pr-sales-enabler-producer-roadmap
description: "PR and Sales enablers are deliberately counted as producers on the marketing page (landing.html) even though not yet built to Video/Social/POSM/Onground's level of capability — confirmed roadmap intent, not a copy overclaim"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-07T10:41:49.417Z
---

The public homepage (`api/static/landing.html`) lists six producers — Social, POSM, Onground, Video, PR,
Sales enablers — as equivalent. I flagged this as a possible overclaim (PR and Sales enablers don't
currently go through the same shared producer envelope as the other four — no idea-platform-bound single
execution, no `stands_on`/`force_typed` mechanism). User confirmed this is intentional, not a mistake.

**Why:** PR and Sales enablers already produce genuinely usable output for their respective fields (press
statements/release material for PR, trade decks/pitch material for Sales) — that's the bar for counting as
a producer on the marketing page, not structural parity with the other four. They are explicitly not yet
fully built, and the stated intent is to bring them up to Video Studio's level of capability over time.

**How to apply:** don't treat PR/Sales enablers' current structural gap (no shared producer envelope, no
per-piece idea-platform binding) as a bug to silently fix or as a reason to walk back "six producers" on
the landing page — it's accurate to the roadmap. If asked to bring them toward parity with
Social/POSM/Onground/Video (four-toggle grounding model, per-piece Adjust, prompt-guide-in-STEP1-position,
etc. — see this session's round-93 work), treat that as fulfilling already-stated intent, not new scope
being invented. See [[studio-work-inventory]] for the round-93 producer-parity work these two are meant to
eventually match.
