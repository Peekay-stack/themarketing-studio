---
name: research-synthesis-deck
description: Produces a standalone cross-source synthesis presentation (.pptx) connecting patterns across several uploaded research files — spreadsheets, decks, docs, PDFs. Use when the user asks to synthesize research across multiple files, build a cross-source insight deck, find patterns across data sources, or connect findings from market data with qualitative research into one narrative. Distinct from the brand-brief skill: this produces no brand strategy, only an honest read of what the evidence does and doesn't say together.
---

# Research Synthesis Deck

Take a set of uploaded research files — market-share spreadsheets, household data, brand-health
trackers, qualitative decks, category reports, anything — and produce a short, standalone `.pptx` that
answers one question: **what does the evidence say when you read all these sources together, not one
at a time?**

## What this skill does NOT do

This is not a brand brief and not a strategy document. It makes no recommendation about what a brand
should do next — that is the brand-brief skill's job (see `brief_skill/`), and folding strategy in here
would blur the one thing this deck exists to be trustworthy about: a plain read of the evidence. Where a
finding obviously implies an action (the user's own worked example — "market share falling, awareness
falling, distribution holding, competition rising → dial up awareness"), name the implication as part of
describing the pattern, in the evidence's own terms — but do not build out a plan around it.

## The core discipline: patterns are found, never forced

This is the load-bearing rule for the whole deck, set by the person who asked for it: **sometimes the
data will not cohere into one clean story, and that is an acceptable answer.** A synthesis deck that
always finds a tidy narrative is not more useful than one that's honest about ambiguity — it is less
trustworthy, because a forced pattern reads exactly like a real one until someone acts on it.

Concretely:

- Never invent a causal link between two findings that only correlate, or that merely happen to share a
  document. "Awareness fell in Q2" and "share fell in Q2" appearing in the same tracker is not, by
  itself, evidence one caused the other — say they moved together, not that one drove the other, unless
  a source actually makes that claim.
- When two or more real chains are plausible, present the competing reads side by side rather than
  picking the one that sounds most finished.
- When nothing genuinely links across sources — each file says something true but unconnected to the
  others — say that plainly. A deck whose honest answer is "no single pattern, here is what each source
  says on its own" is a correct deliverable, not a failed one.
- Every claim in every linkage must trace to a real, cited source. A linkage deck with an uncited box in
  it is worse than a blank slide.

## High-level flow

1. **Reuse the ingestion pipeline's output, don't re-parse.** This skill's input is
   `research_parse.ingest_for_brief()`'s result — the same Map→Synthesize pipeline the brand brief uses
   (see `research_parse.py`, and the IMC ingestion thread in `BRAND_GROUNDING_TESTING_LOG.md`). Do not
   re-read raw files here; the claims list it produces (each with `supporting_sources`,
   `dissenting_sources`, `confidence`, and a `considered_not_used` list) is already the right input
   shape — cross-file-merged, already scored for relevance, already honest about what was excluded.
2. **Build linkages from the claims, not from the raw files.** Look across the synthesized claims for
   real chains: two or more claims that share a subject (a brand, a metric, a market) and move in a
   sequence or relationship that adds up to something. See `references/linkage-construction.md` for how
   to tell a real chain from a coincidence, and how to name the implication a chain points to.
3. **Decide the deck's shape based on what was actually found**, not before finding it:
   - One dominant, well-supported story → lead with it, one slide per link in the chain.
   - Several plausible but competing stories → present them side by side, named as competing reads, not
     as a single forced narrative.
   - No real cross-source pattern → say so on the headline slide, then give each source's standalone
     finding its own line rather than manufacturing a connection.
4. **Assemble the `.pptx`.** See `references/deck-structure.md` for the exact slide sequence and what
   each slide must and must not contain.
5. **Validate before delivery.** Every linkage slide cites its sources by filename. The caveats slide
   names anything explicitly flagged as simulated/dummy data by the underlying research (carry that
   forward — do not silently drop a source's own disclosure that its numbers are illustrative).

## Output contract

- Exactly one `.pptx` file.
- A title slide, a headline/executive-read slide, one slide per linkage or per competing-read (2–5
  slides depending on what was found), a "considered, not used" slide when the synthesis excluded
  anything, and a caveats/sourcing slide.
- Never more than 10 slides total — this is a synthesis, not a re-presentation of every source.
- Every substantive claim on every slide is traceable to a filename from the uploaded set.
- No brand recommendations, no campaign ideas, no creative platforms — those belong in the brand brief.

## Implementation handoff

- `references/linkage-construction.md` — how to build a causal or associative chain from synthesized
  claims, how to distinguish a real chain from a coincidence, and how to word the implication honestly
  (state what the evidence points to, not what should be done about it).
- `references/deck-structure.md` — the exact slide-by-slide contract the render step follows.
- The synthesis (LLM) step lives in `synthesis.py`; the `.pptx` assembly lives in `synthesis_render.py`
  — same split as the brand brief's `brief_ai.py` (reasoning) / `brief_render.py` (assembly).
