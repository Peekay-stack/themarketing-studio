---
name: pending-work-list
description: "The consolidated 'what's next' list, built 23 Sep 2026 when the user paused Carousel work to move on — start here for the next session"
metadata: 
  node_type: memory
  type: project
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-09-23T14:28:35.100Z
---

**PICK UP HERE for the next session.** Built 23 Sep 2026 (end of Round 30) at the user's explicit
request: "we will start tomorrow... build your memory... and keep this list handy." Carousel work
(Rounds 21-30, see [[brand-grounding-modes-project]] and `BRAND_GROUNDING_TESTING_LOG.md`) is
deliberately paused, not abandoned — the user said "I think we have spent enough time perfecting
carousel... now let's look at the other pending list." Several Carousel threads remain genuinely open
(per-slide cast control, the "cast ticked, no person selected" unreliability, a one-instance
invented-product defect, and whether the CTA pack-oversizing fix from Round 29 fully held) — pick those
back up only if the user raises Carousel again specifically.

This list is compiled from memory, not re-verified against current code — several source entries are
11+ days old ([[studio-work-inventory]], last touched 11 Sep). Verify against the real code before
starting any item, per the memory system's own standing discipline (a memory is a point-in-time claim,
not live state).

## Backend/infrastructure gaps (larger items)

1. **Measurement ledger, phase 2.** `api/actuals.py`'s core is built and tested (round 59 of
   [[studio-work-inventory]]) — refusals, filtering, `match()`, the same-second tiebreak. Not done:
   `mediaplan.esov()`'s SOM field and `socialplan`'s benchmark field still write to their own one-off
   spots instead of through the ledger. One real design decision was left open before this can finish:
   what geography key each should use when repointed (`esov()` has no geography dimension today at all;
   the social benchmark is one flat value per plan). `national` was the obvious default noted at the
   time, preserving today's behaviour exactly.

2. **Video plan-binding ("Briefed from the plan" chips).** Deferred multiple times across rounds as "a
   materially larger feature" — Video has no execution-binding concept today the way Social/POSM/
   Onground do (no "Brief it" flow exists for it at all). Scope this with the user before building:
   whether it needs the full audience/channel/occasion/measure/message picker the three producers get,
   or a lighter version.

3. **Multi-brand concurrency risk.** `brandprofile.resolve()`'s "active brand" fallback is a single
   global flag (`set_active()`), shared by every concurrent user/session, not per-request or per-user.
   Flagged in the 7 Sep architecture review as a real correctness risk under concurrent multi-brand use,
   not just a speed one. Matters more as soon as more than one person uses the tool at the same time.

4. **Beta deploy, Phase 4** — backups, spend caps, rate limits. See [[beta-deploy-plan]]. Still open
   since the beta went live (10 Sep).

## Brand-grounding follow-ups (things the grounding-modes project didn't reach)

5. **POSM/Onground never call `brandprofile.voice_block()`.** Confirmed via grep in the 7 Sep
   architecture review: Social and Video get the full brand block (Brand Core, avoid-list, mandatories,
   competitors, price tier) via `system_for()`; POSM's and Onground's own prompt builders
   (`producers.key_visual()`, `producers.activation_ideas()`) never call it at all. See
   [[brand-core-brand-key-thread]] for the Brand Core half of this specifically.

6. **Brand-character's reference image not wired into image generation.** Per
   [[brand-character-skill-thread]]: `character.for_prompt(brand)`'s TEXT is wired into generation
   (Social/carousel/Video script, POSM/Onground via `producers._ctx()`), but the character's actual
   signed-off reference PHOTO still isn't threaded into `/scene-still` or `/posm-image`. Also still open
   from that thread: candidate/audition image-gen, and the Sujatha brief (v2, unapproved, no images).

## Producer parity

7. **PR and Sales-enabler producers.** Confirmed intentional, not yet started: per
   [[pr-sales-enabler-producer-roadmap]], both are counted as producers on the marketing page for what
   they already output, but aren't yet at Video/Social/POSM/Onground's structural parity. Bringing them
   there is fulfilling stated intent, not new scope.

8. **Two specific open items from [[studio-save-audit-doc]]** (Revision 2): Video's script/
   department-card doc-layer gap, and Sales-enabler channel economics.

## Suggested starting point

No hard ranking was given by the user. My own read, offered as a starting suggestion only: item 1
(measurement ledger phase 2) or item 5 (POSM/Onground brand-voice gap) are the most concretely scoped
if the user wants another find-and-fix round similar in shape to today's Carousel work — both have a
clear, narrow root cause already traced. Confirm with the user before assuming either is "the" next
task; they may have something else in mind entirely.
