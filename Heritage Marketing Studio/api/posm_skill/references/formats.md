# Formats

Real dimensions, real reading distances. These are **sensible Indian retail defaults** — a vendor's spec
sheet or a measured bay always wins. State which you are using: `[vendor]` or `[assumed]`.

Reading distance is the number that drives everything: it sets the minimum cap height (≈8.3mm of capital
height per metre of viewing distance), and it decides how much can survive on the piece at all.

## Flat print

| key | label | mm (w × h) | ratio | read at | sides | substrate | the trap |
|---|---|---|---|---|---|---|---|
| `poster-a4` | Poster A4 | 210 × 297 | 5:7 | 1.5 m | 1 | 130gsm art paper | Read close, so it gets over-filled. It is still a poster, not a leaflet. |
| `poster-a3` | Poster A3 | 297 × 420 | 5:7 | 2.5 m | 1 | 130gsm art paper | The default everyone orders. Gets pasted at whatever height there is space, so the top and bottom 10% are unreliable. |
| `poster-a2` | Poster A2 | 420 × 594 | 5:7 | 3.5 m | 1 | 170gsm art paper | Big enough that a soft master shows. |
| `dangler` | Dangler | 200 × 250 | 4:5 | 1.5 m | **2** | 300gsm board, matt lam | **It spins.** A blank back means half of all encounters are with a white rectangle. |
| `dangler-round` | Round dangler | 200 dia | 1:1 | 1.5 m | **2** | 300gsm board, die-cut | Circular crop — anything in the corners of the master is gone. |
| `shelf-strip` | Shelf strip / talker | 900 × 75 | **12:1** | 0.4 m | 1 | 250gsm, adhesive back | Extreme letterbox. No hero survives; this is a re-render, not a crop. Three or four words maximum. |
| `shelf-strip-short` | Short shelf strip | 600 × 70 | 8.5:1 | 0.4 m | 1 | 250gsm, adhesive back | As above. Fits a single bay rather than a run. |
| `wobbler` | Wobbler | 100 × 100 | 1:1 | 1.0 m | 1 | 300gsm board + plastic spring | Tiny. Type has to be larger than looks sane. Usually `product-only`. |
| `backing-sheet` | Backing sheet | 900 × 450 | 2:1 | 0.6 m | 1 | 170gsm, or vinyl on board | **Product stands in front of the lower half.** Everything that must be read goes in the top half. |
| `gondola-header` | Gondola / aisle header | 1200 × 300 | 4:1 | 4.0 m | 1 | 3mm sunboard or ACP | Read across an aisle. Silhouette and one short line only. |
| `dealer-board` | Dealer board | 1220 × 610 (4×2 ft) | 2:1 | 6.0 m | 1 | ACP or 3mm flex | **Co-branded.** Needs a variable field for the retailer's name, address, phone and GSTIN — see `nandini-kmf-dealer-board.jpg`. That field is typically 30–40% of the board. |
| `dealer-board-large` | Large dealer board | 2440 × 915 (8×3 ft) | 8:3 | 10 m | 1 | flex on frame, or ACP | As above, plus: at 10 m the brand mark and one line is the whole content. |
| `standee` | Roll-up standee | 600 × 1800 | 1:3 | 4.0 m | 1 | vinyl on roll-up cassette | The bottom 200mm sits in the cassette and the top curls. Nothing important in either. |
| `tent-card` | Tent card | 100 × 150 | 2:3 | 0.5 m | **2** | 300gsm board, creased | Counter-top, handled. Both faces are seen; they can differ (offer on one, brand on the other). |
| `bunting` | Bunting flag | 200 × 280 | 5:7 | 3.0 m | **2** | 250gsm board, strung | Repeats along a string, so it is a pattern before it is a message. Brand mark and one word. |
| `tin-plate` | Tin plate / sign board | 300 × 450 | 2:3 | 3.0 m | 1 | powder-coated tin | Durable, outdoor, stays up for years — so no dated offer, no seasonal line. Limited colour reproduction. |

## Environmental

A key visual **applied to an object**, not cropped into a rectangle. Output for these is a panel-by-panel
spec plus a mock-up in situ; the mock-up is what gets approved, and the panels are what get printed.

| key | label | mm (w × h) | ratio | read at | notes and the trap |
|---|---|---|---|---|---|
| `chiller-door` | Chiller door decal | 600 × 1400 | 3:7 | 2.0 m | **The door is glass and product is visible behind it.** Either the decal is a frame around a clear window, or it is opaque and the shopper cannot see stock — which retailers refuse. Die-cut around the handle and the hinge. |
| `chiller-side` | Chiller side panel | 600 × 1400 | 3:7 | 3.0 m | Opaque, so this is the one that can carry the full visual. Often against a wall — check which side is visible before printing both. |
| `chiller-canopy` | Chiller header / canopy | 900 × 300 | 3:1 | 3.0 m | Above the unit, read across the shop. Brand block and one line. |
| `shelf-branding` | Shelf / rack branding | per bay | varies | 0.6 m | Must be measured, never assumed — bay widths differ by chain and by store. Ask for the bay dimension and the number of shelves. |
| `stall-backdrop` | Activation stall backdrop | 3000 × 2400 | 5:4 | 5.0 m | **People stand in front of the lower third.** Line and brand block in the upper half or they are behind a promoter all day. |
| `stall-fascia` | Stall fascia / canopy | 3000 × 600 | 5:1 | 8.0 m | Brand name and the line. Nothing else reads at 8 m. |
| `stall-table` | Table skirt | 1800 × 750 | 12:5 | 2.0 m | Legs, crowd and stock cross it. Treat as a pattern with a centred lock-up, not a layout. |
| `stall-standee` | Stall standee | 850 × 2000 | ~2:5 | 4.0 m | Flanks the stall. Can carry the mechanic or the offer, since a person is standing there to explain it. |
| `entry-arch` | Entry arch / gate | 4000 × 3000 | 4:3 | 15 m | **2** | Both sides — people walk under it and look back. Silhouette only. |

## Out-of-home

| key | label | mm (w × h) | ratio | read at | notes and the trap |
|---|---|---|---|---|---|
| `hoarding` | Hoarding | 6096 × 3048 (20×10 ft) | 2:1 | 30 m | Three-second read. **Seven words maximum.** The pack must work as a colour block, not as a label. |
| `bus-shelter` | Bus shelter panel | 1200 × 1800 | 2:3 | 3.0 m | The one OOH format with dwell time — people wait there. It can carry a claim, a footnote, even a mechanic. |
| `unipole` | Unipole | 12192 × 6096 (40×20 ft) | 2:1 | 80 m | Silhouette and brand mark. A line is optional and usually wasted. |
| `auto-back` | Auto-rickshaw back panel | 900 × 600 | 3:2 | 5.0 m | Moves, gets dirty, sits low in traffic. High contrast, no fine detail, nothing in the lower quarter. |
| `wall-paint` | Wall painting | varies (~2:1) | ~2:1 | 20 m | **Hand-painted.** Flat spot colours only — no photograph, no gradient, no soft shadow. This is `type-only` territory, and the pack becomes a simplified drawing. |

## Choosing what goes in a kit

A kit is a media decision, not a catalogue. Ask what the trade footprint actually is:

- **General trade / kirana** — tin plate, dealer board, poster A3, dangler, shelf strip, wall paint. No
  gondola header; there is no gondola.
- **Modern trade** — gondola header, backing sheet, shelf strip, wobbler, standee, dangler.
- **Chiller-led categories** (dairy, beverages, ice cream) — chiller door, side and canopy first; they are
  the brand's shelf.
- **Activation-led** — stall backdrop, fascia, table skirt, standee, plus a poster for the trailing weeks.
- **Launch** — add OOH only if there is a media plan behind it. A hoarding in a POSM kit with no plan is a
  line item, not a decision.

Say why each format is in, and name the ones you left out and why. A kit of eleven pieces where four had no
reason to exist is the most common way POSM money is wasted.
