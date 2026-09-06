# Adaptation

Turning one master into a kit. Four decisions per format: **re-flow, re-stack, drop-out, print spec.**

The governing principle: *the shopper must be able to tell these are the same campaign.* Every rule below
exists to protect that.

## Re-flow the layers — do not crop the artwork

Because the key visual is a **layer stack on a flat field** and not a bitmap, adaptation is not cropping.
It is **re-laying the same layers into a new canvas**: the field is redrawn at the new size, and the hero
cut-out, pack, type blocks, devices and base band are re-placed in it.

This is why the layer-stack model matters so much in practice. Cropping a finished poster into a 12:1 strip
destroys it. Re-flowing the same six layers into a 12:1 canvas is trivial — the field just gets wider, the
cut-out gets smaller and moves, the headline goes to one line. Nothing is lost and nothing drifts, because
every piece is built from **the same assets** rather than from the same picture.

A design tool's resize function does most of this mechanically. Check every result: automatic re-flow gets
the field and the type right and routinely mis-scales cut-outs.

**What still gets cropped:** the hero cut-out's own framing. A full-figure subject becomes head-and-pack on
a small format. That is a crop of one asset, not of the artwork.

Work out the **aspect delta** — target ratio ÷ master ratio, master 3:4 (0.75) — to decide how hard the
re-flow is and whether the hero survives it at all.

| delta | what it means | what to do |
|---|---|---|
| 0.7 – 1.4 | Near-square to moderately different | **Straight re-flow.** Every layer keeps its role. Poster A3/A4/A2, dangler, round dangler, wobbler, tent card, bunting, chiller door, chiller side, stall backdrop, bus shelter. |
| 1.4 – 2.5 | Notably wider | **Re-flow, and re-crop the hero cut-out.** A full-figure subject becomes upper-body. Type usually goes from stacked to beside. Backing sheet, dealer board, auto-back, hoarding, unipole. |
| 0.4 – 0.7 | Notably taller | **Re-flow, and the field gains height.** Use the extra height for the brand block and the type, not for a stretched hero. Standee, stall standee. |
| > 2.5 or < 0.4 | Violent | **Re-flow with the hero dropped or reduced to a motif.** Shelf strip (12:1), gondola header (4:1), stall fascia (5:1), chiller canopy (3:1), dealer-board-large (8:3), table skirt (12:5), wall paint. |

**Never stretch, and never letterbox with brand colour and call it an adaptation.** A distorted pack is the
worst outcome available, because the shape on the wall no longer matches the shape in the hand — which
defeats the only job POSM has.

## The violent formats are not a problem any more

Under a bitmap model, a 12:1 shelf strip out of a 3:4 master was a crisis: nothing croppable, so the piece
needed its own render and the "one key visual" promise had a hole in it at exactly the format that matters
most in general trade.

Under the layer model it is routine. A shelf strip is **the same field colour, the same logo, the same
typeface, three or four words, and optionally the pack cut-out repeated small as a motif.** Every one of
those is an asset the master already has. Nothing is re-rendered and nothing drifts.

The hero cut-out is the only layer that may not survive, and dropping a layer is a decision, not a failure —
that is what the ladder below is for.

## The drop-out ladder

What leaves, in order, as the piece gets smaller or further away. **Fixed order, not per-piece taste** —
that consistency is what makes eleven pieces look like one campaign.

```
1. field                  ← never dropped; it is the piece
2. mandatory fine print   ← never dropped on print; only on environmental where it does not apply
3. brand block            ← never dropped, on anything, ever
4. pack cut-out           ← never dropped except where the piece is not about a product (arch, fascia)
5. line                   ← dropped only at product-only sizes
6. support + devices      ← FIRST to go: benefit marks, NEW flash, care box
7. field graphics         ← SECOND to go: streaks, waves, doodles, patterns
8. secondary cut-outs     ← THIRD to go: extra packs, props, second figures
9. hero cut-out           ← FOURTH to go, leaving field + pack + line + brand block
```

Read from the bottom up: as the piece shrinks, support goes, then the field graphics, then any secondary
cut-outs, then the hero itself. **Fixed order, not per-piece taste** — that consistency is what makes eleven
pieces look like one campaign, and it is enforceable precisely because every piece is the same layer set.

Four tiers in practice:

**Full** — everything. Poster A2/A3, standee, dealer board, stall backdrop, bus shelter, chiller side.

**Reduced** — drop support; tighten the hero to head-and-pack or to the metaphor object alone. Poster A4,
dangler, round dangler, tent card, chiller door, auto-back.

**Minimal** — drop the hero entirely. Pack + line + brand block on a brand colour field. Shelf strip,
backing sheet, gondola header, chiller canopy, bunting, tin plate.

**Mark-only** — pack silhouette and brand block, no line. Wobbler, small bunting, and anything read beyond
30 m where a line is wasted.

## Re-stacking the line

The line does not survive a crop unchanged. Two things change with the format:

**Its position.** The master's layout key is re-chosen per format, guided by what the piece's own geometry
and occlusion allow — see the layout table in `key-visual.md` and the traps column in `formats.md`. Common
re-stacks: `type-over-top` on the master becomes `type-locked-base` on a standee (the top curls), and
becomes `type-beside` on a header (there is width and no height).

**Its length.** Word count is a function of reading distance, and it is not negotiable:

| read at | words |
|---|---|
| ≤ 0.6 m | 9–12, and a support line is possible |
| 1.0 – 2.5 m | 6–9 |
| 3.0 – 6.0 m | 3–6 |
| 8 – 30 m | ≤ 4 |
| > 30 m | 0–2, brand mark carries it |

So a nine-word poster line needs a three-word version for the gondola header. **Write the short version
from the same proposition, do not truncate the long one** — a truncated line usually loses the verb and
becomes a label. Offer both, and say which format uses which.

Cap height comes from the same place: ≈8.3mm per metre of viewing distance, as a fraction of the piece's
printed height. A shelf strip at 0.4m needs ~3.3mm caps on a 75mm-tall piece — 4.4% of its height. A
gondola header at 4m needs ~33mm caps on a 300mm piece — 11%. That is why the same line cannot simply be
scaled.

## Physical rules that override layout

These beat any aesthetic decision, because they are about the piece's actual situation in a shop.

**Both sides, or die-cut.** Danglers, round danglers, tent cards, bunting and entry arches are seen from
two directions. Specify side B explicitly. It may be a simplified version — brand block and line, no
hero — but it may not be blank. A spinning dangler with a white back is broken half the time.

**Occlusion.** Something physical stands in front of these, so nothing that must be read goes there:

| format | what is in front | keep clear |
|---|---|---|
| `backing-sheet` | product on the shelf | lower half |
| `stall-table` | legs, stock, crowd | lower two-thirds |
| `stall-backdrop` | promoters and shoppers | lower third |
| `standee` | the roll-up cassette | bottom 200mm, plus top 100mm (it curls) |
| `chiller-door` | the handle, the hinge, the stock behind glass | die-cut the handle; leave a clear viewing window |
| `poster-a3` | whatever it gets pasted over or under | outer 10% top and bottom |
| `auto-back` | road dirt, the bumper | lower quarter |

**Bleed and safe area.** 3mm bleed on anything under A2, 5mm on larger flat print, 25mm on flex and vinyl.
Safe area is 5mm inside the trim for print, 50mm for flex on a frame — the frame eats the edge. Nothing
important in the bleed, and no brand mark closer to the trim than its own cap height.

**Substrate limits.** Flex and hand-painted work cannot hold gradients or shadow detail. Tin plate has a
restricted palette. Flexo on adhesive stock loses fine tonal steps. Where the substrate cannot carry the
master's finish, the adaptation is `type-only` with a flattened pack — say so rather than sending artwork
the printer will approximate.

## The adaptation sheet

One per format. Everything a studio needs and nothing it has to guess:

```
FORMAT      dealer-board · 1220 × 610mm · 2:1 · read at 6m · 1 side · ACP  [assumed — confirm with vendor]
SOURCE      re-flow of master layers (delta 2.67 — wider; hero re-cropped)
FIELD       Deep Forest, hard horizontal split with the retailer band below
HERO        cut-out re-cropped to upper body only, placed right
PACK        cut-out, lower right of the upper zone
TIER        full
LAYOUT      type-beside — line left, hero and pack right
LINE        "Pure milk is where strength begins"  (6 words, fits 3–6 at 6m)
CAP HEIGHT  50mm minimum (8.3 × 6m), = 8.2% of piece height
DROPPED     support icons (4 benefit marks) — no room beside the retailer field
RETAILER    variable field, lower band, 1220 × 200mm: shop name, address, phone, GSTIN
CLEAR       outer 50mm (frame), retailer band
MANDATORY   FSSAI mark + veg mark, bottom left of the retailer band
MISSING     the retailer's GSTIN and the exact board size the fabricator uses
```

## Checks before handing over a kit

1. **Put every piece side by side.** Do they read as one campaign? If two differ in the hero's face, the
   pack angle or the background colour, something was re-rendered from the brief.
2. **Is every two-sided format specified on both sides?**
3. **Does anything important sit where a body, a leg or a cassette goes?**
4. **Does every line fit its distance's word count**, with the short versions written rather than truncated?
5. **Is the smallest piece still recognisably this brand?** A wobbler with no brand block is a sticker.
6. **Is every assumed dimension marked `[assumed]`**, with what needs measuring and who measures it?
