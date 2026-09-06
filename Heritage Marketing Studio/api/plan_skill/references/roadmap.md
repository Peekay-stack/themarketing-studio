# The plan on a page

A roadmap gets circulated, argued with and half-remembered. It has to answer *who, where, when* at a
glance and admit what is not settled. Render it as a self-contained, **editable** HTML artifact.

Match the house diagram's construction — one file, no CDN, no external fonts, no images,
`contenteditable` throughout, a **Print / PDF** button and a **Download edited copy** button that
strips the toolbar and the script from the saved file. Print as **A4 landscape**.

## The shape, top to bottom

```
  OBJECTIVES LADDER      business -> marketing -> communication
  ------------------------------------------------------------------
  AUDIENCES              in priority order, one pillar each
  ------------------------------------------------------------------
  CHANNEL ROLES          channel | role | job | measure | B/A
  ------------------------------------------------------------------
  SPLIT METER            declared vs actual, side by side
  ------------------------------------------------------------------
  PHASES                 a horizontal timeline, each tied to an occasion
  ------------------------------------------------------------------
  BLOCKERS               what is not settled and who owns it
```

## Zone by zone

**Objectives ladder.** Three stacked rows, visibly a chain — an arrow or a rule connecting them. The
business objective carries a number and a date. If a level does not trace to the one above, mark that
link broken rather than drawing it.

**Audiences.** One card each, in rank order, with the rank shown as a numeral. Each card carries the
audience, the belief to shift, and **its one pillar**, colour-coded to the pillar colours used in the
house diagram so the two documents read as one system. If any audience shows more than one pillar,
the plan is wrong — do not render it as valid.

**Channel roles.** A table, one row per channel:

| Channel | Role | Job | Measure | Brand / Activation |

- The **lead channel** is marked — a filled tag, not a bold word.
- **Role and measure must agree.** A reach channel measured on conversion is the classic misallocation
  and should be flagged in the row itself, not silently rendered.
- A channel with the **proof** role whose pillar is unverified gets an amber row and appears in
  blockers. This is the plan's most important check.

**Split meter.** Two horizontal bars, same scale, stacked: **declared** above, **actual** below,
each divided brand/activation with the percentages on the bars. Show the delta as a number when they
differ, and state the basis underneath — `weighted by planned spend` or `spend unknown — computed on
channel count`. If the author moved off 60/40, their one-line reason sits beside the meter.

Two bars, not one. A single bar showing only the declared split is the version of this chart that
lets a plan lie to itself.

**Phases.** A horizontal band per phase across a shared time axis: name, window, **the occasion it
serves**, the channels live in it, and what it hands to the next phase. Label the axis with real
months. A phase with no named occasion is drawn with a dashed border and flagged.

**Blockers.** A closing strip, not a footnote. Every unverified pillar with proof work against it,
every channel with no owner or no budget, every broken ladder link, every phase without an occasion,
and the declared/actual gap if there is one. Each with who has to resolve it.

If the strip is empty, say so explicitly — *"nothing outstanding"* — so an empty strip reads as
checked rather than forgotten.

## Colour and type

- One typeface. Size and weight carry hierarchy.
- **Reuse the house's pillar colours** for emotional and functional wherever they appear. Consistency
  across the two documents is what makes the spine visible.
- Amber is reserved for *unresolved*, never for emphasis. If everything is amber, nothing is.
- Test in greyscale — a split meter that depends on colour alone is useless printed. Label the
  segments.
- Nothing below 9px.

## What not to do

- No Gantt chart for its own sake. If a phase has no dependencies, do not draw dependency arrows.
- No invented budgets to make the meter balance. `unknown` is a legitimate value and a useful one.
- Do not drop the blockers strip to make the page look finished. It is the only part of a roadmap
  that reliably saves anyone money.
- Do not show the declared split without the actual one.
