---
name: measure-the-artefact-before-theorising
description: "When generated output is structurally correct but still looks wrong, measure the actual artefact first — and prefer the upstream fix over patching downstream symptoms"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-03T06:13:03.568Z
---

When the user says output is "still far from where I'd like it" and it is already structurally correct,
**measure the artefact before researching or theorising about craft.**

In the POSM compositor (round 77), a poster looked empty and no amount of design theory explained it.
One measurement did: the hero image was 1792×2400 but the keyed subject occupied only **49% of the
height and 43% of the area**, and `assemble()` was fitting the IMAGE to the layout box rather than the
SUBJECT. Everything else in the piece was correct; the subject was simply rendering at half its
allocated size. A one-line fix (crop to the alpha bounding box first), invisible without measuring.

Useful things to measure on a generated image: subject bbox vs canvas, proportion of semi-transparent
pixels (2.1% means the matte is effectively binary — glass and hair need far more), mean colour behind
a text zone, contrast ratio, and visual mass per zone at thumbnail scale.

**Prefer the upstream fix.** The same round had two separate matte defects — a key eating white
subjects, and pale halos on every edge — and both had one cause: cut-outs were being generated on a
WHITE backdrop and then white was keyed out. Changing the generation prompt to a mid-grey backdrop
(`posm.CUTOUT_BACKDROP`) fixed both at source and made two planned downstream patches unnecessary.
Chroma keying is green for exactly this reason: the backdrop must be a colour the subject does not
contain.

**How to apply:** before proposing craft changes, write a short script that prints numbers about the
failing artefact. Then ask what produced those numbers, and whether the cause sits upstream of where
the symptom appears.

Related: [[check-skill-md-before-craft-changes]], [[studio-work-inventory]],
[[browser-verification-available]].
