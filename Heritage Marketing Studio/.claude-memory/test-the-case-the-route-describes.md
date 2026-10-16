---
name: test-the-case-the-route-describes
description: "Verify against the case the user's own content describes, not the convenient one — and never classify an artefact by how it was generated when you can measure what it is"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-03T07:46:21.999Z
---

Three POSM defects survived four consecutive rounds of my own live verification because every time I
tested, I used a **pack-only hero**. The user's actual route was person-led ("a mother, already dressed
and calm before dawn, mid-motion setting a filled glass down"), and every one of the three failures is
invisible unless a person is involved:

- the hero/route mismatch (a pack shot cannot contradict a route about a mother if you never test a
  route about a mother),
- the route's subject never reaching the studio brief,
- the person-led hero types needing a cast reference.

**Pick the test case from the user's own content** — their chosen route, their headline, their assets —
not from whatever is quickest to set up. "It rendered fine" against a convenient fixture is not
evidence about their path.

**Second rule from the same round: never classify an artefact by how it was generated.** Heroes were
flagged as cut-out or scene based on the `mode` the generation call used. A studio shot made in "scene"
mode was in fact a pack on a seamless grey sweep — a cut-out by any visual definition — so it was
composited unkeyed and its backdrop landed on the poster as a grey rectangle. The label was right about
the API call and wrong about the picture. `keyvisual.looks_like_cutout()` now measures the frame border
instead. Provenance is a hint; the artefact is the fact.

Related: [[measure-the-artefact-before-theorising]], [[browser-verification-available]],
[[studio-work-inventory]].
