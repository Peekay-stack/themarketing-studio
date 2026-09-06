# The channel grid on one page

A trade plan is read by a sales director who will look for two things: what am I being asked to do,
and where does this collide with something else. Build for those two questions.

Same construction as the other one-pagers in this system: a single self-contained HTML file, no CDN,
no external fonts, no images, `contenteditable` on every text element, a **Print / PDF** button and a
**Download edited copy** button that strips the toolbar and the script from the saved file. Print
**A3 landscape** — this one is wider than the others and there is no honest way to shrink it.

## The shape

```
  HEADER            brand · the trade message, or "no trade message in the house"
  ---------------------------------------------------------------------------
  CHANNEL GRID      one row per channel:
                    channel | share now | role | behaviour bought | lever
                            | cost per unit | leakage control | sell-through
  ---------------------------------------------------------------------------
  EFFECTIVE PRICE   the reconciliation strip — every channel, same axis
  ---------------------------------------------------------------------------
  CALENDAR          occasions, with trade lead time shown ahead of each
  ---------------------------------------------------------------------------
  BLOCKERS          unknown shares, invented numbers, primary-only schemes,
                    unpriced collisions, schemes with no control
```

## The channel grid

One row per channel — **all of them, including the ones getting nothing.** A channel with no money is
a decision, and an empty row records it. Dropping the row hides it.

- **Share now** before anything else. It is the number that makes the rest arguable, and it is the one
  most often missing. If unknown, the cell reads `share unknown` and the row is flagged.
- **Behaviour bought** in the retailer's or distributor's words, with a baseline and a target.
  "Visibility" must not be renderable — if the field contains it, flag the row.
- **Cost per unit** of the behaviour, net of scheme. `payback unknown` is a legitimate value and must
  be visually distinct from a number, never dressed to look like one.
- **Sell-through** as a three-state badge: primary · secondary · tertiary. **Primary is amber, always.**
- **Leakage control** named in the row. An empty cell here is a blocker, not a blank.

Sort by share of volume descending, not alphabetically and not by how interesting the channel is. The
biggest channel goes first even when it is the least exciting — especially then.

## The effective-price reconciliation strip

**This is the part nobody draws and the reason the page exists.**

One horizontal axis of consumer price. Every channel plotted on it as a marker showing the effective
price a shopper pays after all schemes, promos and platform discounts. Label each with the channel and
the price.

Then the judgement, written out: where two channels sit far apart, say whether it matters. A gap
between own retail and general trade may be deliberate. A quick-commerce price below the kirana who
stocks you daily is a decision to stop being stocked, and it should be impossible to look at this
strip and not see it.

If the effective price cannot be computed for a channel, plot nothing and say why. An invented price
here is worse than a gap, because the whole strip is then unreliable and nobody can tell which marker
is real.

## The calendar

Occasions from the IMC plan, with **trade lead time drawn ahead of each one** — the trade has to be
stocked before consumers are told. A campaign date with no stocking runway in front of it is the most
common way a good plan fails in market, and drawing the runway makes it obvious.

## Blockers

A closing strip, never a footnote: unknown shares, any number marked unverified, primary-only schemes,
unpriced or unresolved collisions, and schemes with no leakage control. Each with who resolves it.

If empty, say *"nothing outstanding"* — so an empty strip reads as checked, not forgotten.

## Colour and type

- One typeface. Colour marks **state** — amber for unresolved, primary-only, unknown — never emphasis.
- Do not colour-code channels decoratively. Six channel colours competing with amber state markers
  makes the state markers invisible, which is the one thing on this page that must not happen.
- Test in greyscale; the price strip must still read.
- Nothing below 9px.

## What not to do

- No pie chart of channel share. A row with a number is clearer and takes a quarter of the space.
- No "opportunity" column. Every trade plan has one and it is where invented numbers live.
- Do not average colliding prices into a single "average realisation". The collision is the finding.
- Do not omit a channel to make the grid fit. Cut the words in the cells.
