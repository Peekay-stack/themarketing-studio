---
name: round31-queue
description: "The consolidated task list / A-B test / experiment board pulling together every open item from Carousel's brand-grounding work, the Image and Video Engine Playbook, and the Format Signal Study — check this before scoping any next round of work"
metadata:
  node_type: memory
  type: reference
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-09-24T07:54:38.761Z
---

**LIVE DOCUMENT**: [Round 31 Queue](https://claude.ai/artifact/UpSArgACG53yWTUCPVwFSV)

Built 25 Sep by consolidating every still-open item across three research threads into one operational
board: [[brand-grounding-modes-project]] (Carousel, Rounds 21-30), [[image-gen-engine-research]] (the
Image and Video Engine Playbook artifact), and [[cross-category-format-study]] (the Format Signal Study
artifact). 25 items total, sorted into three buckets, not just one flat list:

- **Task list (15)** — nothing blocked on an experiment. 4 small items are genuinely ready to build now
  (headline-safe negative space beyond the CTA, a defensive no-typography style cue, fixing the writer's
  own few-shot inconsistency, and Video's narrowly-scoped negative_prompt wiring). The rest need scoping
  first, including the two biggest builds (still-image compositing, a generate-verify-retry loop) which
  stay in this bucket since nothing blocks scoping them, just sizing them.
- **A/B tests (3)** — Kling 3.0 vs Veo 3.1 on a multi-shot same-character sequence (tests Kling's claimed
  strength against this project's known weakness); current CTA wording vs a further revision (Round 29's
  fix reduced but didn't eliminate oversizing — is wording at its ceiling?); composited vs fully-prompted
  CTA, once a compositing prototype exists.
- **Experiments (5)** — three Carousel defects that only have one confirmed data point each and need more
  before they're treated as systemic (the cast-ticked-unselected unreliability, the slide-1 child→adult
  override, the invented-product defect); plus two quick video-pipeline checks (does Seedance's
  region-level editing actually work on a label, and does a storyboard→video ratio mismatch silently
  distort the way Round 22 found for stills).

Update the artifact directly as items move (same URL, republish with `url` set) rather than tracking
progress only in chat — this is meant to be the actual working board for whatever gets picked up next,
not a one-off summary. Update the three source documents' own findings first if something here turns out
to be wrong; this board should always agree with them, not drift from them.
