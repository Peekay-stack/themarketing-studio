---
name: audit-sibling-entry-points-not-just-my-diff
description: "When asked for a forward/backward wiring audit, diff every SIBLING entry point of the same pipeline field-by-field, not only the lines I just changed — the 23 Oct audit missed the cutdown render path being frameless."
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-26T04:49:47.128Z
---

The owner's standing audit request ("blast radius, frontend/backend, backwards and forwards from the changed tab, wiring intact, staleness") means the WHOLE pipeline the changed thing sits in, not just my diff and its direct callers.

**Why:** 23 Oct I audited Builds 1-3 (pace, re-score, cutdown re-voice) and reported "no defects". On 26 Oct the owner rendered a real 20s Edit-room cutdown beside the 30s original: pack fidelity gone, continuity check inert, VO pause wrong, captions drifting, Telugu boxes. The cutdown render path (`renderCut`) had never been compared to the production one (`produceVideo`) — it sends no `frame_url` and no `sound_plan`, and the no-frame branch of `segment_prompt` carries no pack/cast/plate at all. I had even written an earlier memory line ("continuity via character sheet + look ref") that was never checked and was false. See [[video-editor-build-plan]].

**How to apply:** when a pipeline has two entry points to the same engine (production render vs cutdown render, produce vs rescore, first render vs revision), build the request bodies side by side and list every key one sends and the other doesn't; then check each missing key is read by the engine at all (grep the payload key inside the worker). Also look at the real OUTPUT (contact-sheet frames, silence detection) when the owner supplies a file, and never record an unverified claim about what reaches a generation step as fact.
