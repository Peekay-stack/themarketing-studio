# Deck Structure

The exact slide sequence `synthesis_render.py` builds from the linkages `synthesis.py` produces.

## 1. Title slide

- Deck title: "Cross-Source Research Synthesis" (or the brief's category/brand if one was given for
  context — this deck can run with or without a named brand, since it makes no brand recommendation).
- Subtitle: the list of source filenames, so the deck is self-documenting about its own evidence base
  without needing a separate methodology slide.
- Date.

## 2. Headline / executive read

One slide, one of two shapes depending on what was actually found:

- **A pattern was found**: state the single strongest reading in one or two sentences, plus its
  confidence level. This is the "if you read one slide, read this one" slide.
- **No single pattern was found**: say so directly — "The N sources reviewed do not converge on one
  cross-source pattern" — then name in one line each what the strongest independent, standalone findings
  were, so the slide still orients the reader even without a unifying story.

Never split the difference by writing a headline that sounds unified but isn't backed by the linkages
that follow — the headline must be a compressed version of what the linkage slides actually show, not an
aspiration for what they might have shown.

## 3. Linkage / competing-read slides (one each, 1–4 slides)

Each slide:

- **Title**: the linkage's one-line reading (the "implication" from `linkage-construction.md`), not a
  generic label like "Linkage 1."
- **Body**: the chain, shown as the claims that compose it in the order they build the case, each tagged
  with its confidence and its supporting source(s). Keep each claim to one line — this is a presentation
  slide, not the underlying claims table.
- **Confidence** shown plainly (high/medium/low), inherited from the weakest link the chain depends on —
  a chain is only as strong as its least-supported claim.

When there are multiple COMPETING reads rather than one chain, each gets its own slide, explicitly
labelled "Read A" / "Read B" etc. in the title, and the headline slide should have already flagged that
the deck presents more than one.

## 4. Considered, not used (only when the synthesis excluded something)

One slide, only included when `synthesize_research()`'s `considered_not_used` list is non-empty. A
simple two-column list: source filename, and the one-line reason it wasn't used. This is the same
transparency principle the brand brief's ingestion pipeline already follows — omit silently and a reader
has no way to know a file was even considered; name it and they can go check it themselves.

## 5. Caveats / sourcing

- Every filename that fed the deck, listed once more for a reader who skipped straight to the end.
- Any explicit "this data is simulated/dummy/illustrative" disclosure carried over from the source
  material itself (research_parse's Map phase already surfaces this when a source says so about itself —
  never drop that disclosure on the way into this deck).
- One line naming what to validate before this deck's read is treated as settled fact, if the underlying
  claims' confidence was anything other than uniformly high.

## Visual treatment

Kept deliberately plain — this deck earns trust through what it says, not through production values.
Each linkage slide may render its claim chain as a simple vertical list with a connecting line/arrow
between consecutive claims (python-pptx shapes), ending in the implication line set apart in a bordered
box. No charts are fabricated from numbers that were not already computed by `research_parse.py`'s
deterministic spreadsheet aggregation — if a chain would benefit from a chart, only build one from a real
`aggregates`/`trend` result already computed, never a chart illustrating a qualitative claim as if it
were measured data.
