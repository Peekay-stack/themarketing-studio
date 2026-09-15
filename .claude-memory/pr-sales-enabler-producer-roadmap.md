---
name: pr-sales-enabler-producer-roadmap
description: "PR and Sales enablers are deliberately counted as producers on the marketing page (landing.html) even though not yet built to Video/Social/POSM/Onground's level of capability — confirmed roadmap intent, not a copy overclaim"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-15T06:07:00.749Z
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

**15 Sep, live-tested per [[brand-grounding-modes-project]] Round 5:** confirmed Sales enabler's parity
gap extends to the Grounded/Independent toggle too — its one wired frontend action (`/sales-element`)
is pure manual record-keeping, no AI, so the toggle is currently a no-op there (nothing to leak,
nothing to clear). The real generation route (`/sales-generate`) already exists server-side and already
pulls brand facts unconditionally, no `brand_mode` param — same shape as the `/brand-brief-draft` gap
Round 1 fixed — but has zero frontend caller, so it's a latent trap rather than a live bug. Whoever
wires a real "Develop with AI" action here needs to thread `brand_mode` through both the payload and
`sales.prompt_for()` as part of that build, not as a follow-up fix.
