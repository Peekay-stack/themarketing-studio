---
name: prefer-cited-estimates-over-blocking
description: "When official data is stale, they want a cited estimate used — not a refusal to produce a number."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8ceac62b-7222-47d3-9a92-41e0ce0e0317
  modified: 2026-08-25T15:18:30.573Z
---

When the only official source is badly out of date, use a published estimate and label it, rather than
refusing to give a figure. On 2026-08-25, told directly: "you can take the latest estimates for the
current population estimate using wikipedia or some such source" — after I had established that Census
2011 is still India's only completed count (Census 2027 enumerates 1 March 2027).

**Why:** the studio's refusal discipline exists to stop *invented* numbers, not to stop *sourced* ones.
Refusing to size a market because the census is old makes the tool useless for the actual job; an
estimate with its publisher and year attached is honest and usable. The failure they care about is a
number nobody can trace, not a number that carries a caveat.

**How to apply:** keep the provenance machinery and relax the refusal. Give the figure a basis field
naming publisher and year, keep bases from being mixed in one ranking, and say what the caveat is —
then hand over the number. Reserve a hard refusal for figures with no source at all (an AVE, an
invented GRP, a scraped commercial spend). See [[synthetic-dicts-write-real-tenant-files]] for the
adjacent discipline on test data.
