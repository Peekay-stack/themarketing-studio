---
name: posm
description: Build a POS key visual and adopt it across every format a retail kit needs — posters, danglers, shelf strips, wobblers, backing sheets, dealer boards, chiller branding, activation stalls and out-of-home. Use when asked for POS material, POSM, in-shop branding, retail visibility, a shelf strip, a dangler, a dealer board, trade branding, a visibility kit, or when a settled idea platform has to become something a printer can produce.
---

# POS material

Point-of-sale is the only medium where the brand and the purchase are in the same room. It is also the
one most often made badly, because it looks easy: a picture, a line, a logo. The failure is never in the
individual piece. It is that **eleven pieces get made separately and arrive looking like eleven brands.**

So this skill has one governing rule, and everything else follows from it:

> **One key visual, adopted. Never eleven generations of the same brief.**

A kit is coherent because every piece is demonstrably the same picture, re-cropped and re-stacked for its
own size and reading distance. If a poster and a dangler are two separate renders, they will differ in
lighting, in pack angle, in the model's face, in the colour of the background — and the shopper who sees
both reads two campaigns. That coherence is not a nice-to-have; it is the entire reason POSM works as a
system rather than as decoration.

## The sequence

```
Brief → Messaging house → Idea platform → KEY VISUAL → adaptations → print spec
                                            ▲
                              this is the artefact everything else derives from
```

The key visual is a *deliverable in its own right*, approved on its own, before any format exists. Skipping
to "give me a dangler" is how the incoherent kit happens. If someone asks for a single format, build the
key visual first and then adopt it — say that you are doing so, in one line.

## A key visual is a layer stack, not a photograph

This is the correction that matters most. Getting it wrong produces work that is competent and does not
look like POS material at all.

Indian FMCG point-of-sale is **flat-colour graphic design with cut-out photographic elements placed on it.**
It is assembled from separately-sourced layers. It is **not a photograph with words on top.** Thirteen real
pieces sit in `references/exhibits/`, read layer by layer in **`references/exhibits.md`**, and nine of them
are built exactly this way.

The stack, bottom to top:

| # | layer | what it is |
|---|---|---|
| 1 | **field** | Flat brand colour, or two colours split by a straight/diagonal/curved edge, or a brand pattern. **Never a photograph.** |
| 2 | **field graphics** | Optional and low contrast: streaks, waves, doodles, splats. |
| 3 | **hero cut-out** | The subject, masked out of its background, hard-edged, shadowed to seat it. |
| 4 | **pack cut-out** | The real pack, masked. From the library, never generated. |
| 5 | **type blocks** | Headline in a weight hierarchy, plus support lines. Real editable type. |
| 6 | **devices** | Badges, roundels, NEW flashes, highlight boxes, underline rules. |
| 7 | **brand block** | Logo lock-up as vector artwork, cornered. |
| 8 | **base band** | Flat strip: tagline, footnote strip, care or contact box. |
| 9 | **mandatories** | Veg mark, FSSAI, licence number. Smallest, in the base band. |

Two things follow, and they change how you work:

> **You do not generate a poster. You generate assets — a subject isolated on plain white, ready to cut
> out — and then you lay them out.**

That is a far easier job for an image model than a finished composition, and it is what a real studio does:
shoot on white, mask, place.

> **"Reserve empty space for the type" is a problem that should not exist.**

You only need to hold space open inside a photograph if that photograph has to be the whole poster. On a
flat colour field, the field *is* the space. Any technique that drops a translucent band over a full-bleed
image to make room for a headline is a symptom of building the wrong thing.

**The pack is never the hero.** It is always present and never the subject. A frame that is entirely the
pack on a gradient is a pack shot — useful for a listing, useless as POS.

There is a minority **photographic build** for cases where the scene itself is the argument — a visible
demonstration, a metaphor made as a real object, an occasion. Even those carry a hard split into a flat
zone, and the photograph is never asked to host type.

Read `references/failures.md` before writing a single prompt. Full construction, the two builds, the field
and type device vocabulary, the six hero types and the cut-out prompts:
**`references/key-visual.md`**.

## The pack must be the real pack

**Refuse to render a master key visual without a signed-off pack shot in the library.** Not a warning — a
refusal, naming what to upload and where.

The reasoning is specific to this medium. POSM's job at shelf is recognition: the shopper matches what is
on the poster to what is in their hand. A generated pack is always subtly wrong — the proportions, the cap,
the label geometry — and *the model draws brand lettering onto it*, which is the one thing that must never
be generated. A piece with an invented pack is not a comp with a flaw; it is a piece that teaches the
shopper the wrong shape, and if it reaches a printer it is money spent making the brand harder to find.

The pack is composited from the library reference, never described in words. Same for the logo.

## Type is set, never generated

Image models approximate letterforms. In Latin they produce something that looks like text until you read
it; in Devanagari, Telugu and Kannada they produce something that is not writing — conjuncts break, matras
detach, and it is confidently wrong in a way nobody catches until it is printed.

So: **no word on the piece is ever generated.** Type is set in the design tool, as real editable text, on
the flat field. This applies to the line, the tagline, the support copy, the mandatories *and to any
lettering on the pack or on the subject's clothing* — which is exactly why the pack is composited rather
than described, and why the cut-out prompt forbids branding on any object in frame.

Because the field is flat colour, this needs no reserved-space trick. The type sits on the field the way it
does in every exhibit. **A line dropped onto a full-bleed image inside a translucent slab is not a layout;
it is a subtitle** — and it is what you are forced into when the hero is a photograph that fills the frame.

One practical consequence worth knowing: a design tool sets Devanagari, Telugu and Kannada correctly because
it uses a real font. This is not a compromise position — it is strictly better than any drawn-on-afterwards
approach, because the words stay editable and a copy change costs nothing.

**But "the letterforms are correct" is not the same as "the words are right."** A design tool asked to
generate a layout will also generate *copy* — inventing lines, extending a headline with a third line that
is not a word in any language, corrupting a badge by folding the headline into it. Correct type setting
nonsense is still nonsense on a printed piece.

So the rule is stronger than typography: **every word is supplied, never generated.** Pass the exact copy,
then read back every word on the output — headline, support, badge, base band, mandatory line — against what
you supplied. Anything you did not write is a defect regardless of how well it is set.

Reading distance sets the minimum cap height, not taste. One inch of capital height per ten feet of
viewing distance (United States Sign Council) — about 8.3mm of cap height per metre of distance. Every
format in `references/formats.md` carries the distance it is actually read at, so the type size follows
from the piece rather than from what looks right in a preview.

## Adopting across formats

Adaptation is **not regeneration**. It is four decisions per format:

1. **The crop** — which window of the master this piece is. Cropping is free and preserves identity
   perfectly, so it is always the first move.
2. **The re-stack** — where the line, brand block and support go in the new aspect. A 12:1 shelf strip
   cannot hold a stacked headline; a 1:3 standee cannot hold a wide one.
3. **The drop-out** — what leaves. Every element that does not survive the size goes, in a fixed order,
   until a wobbler is pack + logo and nothing else. Deciding this per piece by feel is how kits drift.
4. **The print spec** — bleed, safe area, substrate, sides, die-cut, and what physically occludes the
   artwork in situ.

Where the aspect change is too violent to crop — a shelf strip out of a 4:5 master — the piece is
re-rendered *from the master as a reference image*, so the hero stays the same person and the same pack.
Re-rendering from the brief is never correct; that is the incoherent kit again.

Thresholds, the drop-out ladder, and the occlusion rules: **`references/adaptation.md`**.

## Formats

`references/formats.md` carries the full table — real millimetres, real aspect ratios, reading distance,
number of printed sides, substrate and the trap in each. Three families:

- **Flat print** — posters A2/A3/A4, danglers (rectangular and round), shelf strips, wobblers, backing
  sheets, gondola headers, dealer boards, standees, tent cards, bunting, tin plates.
- **Environmental** — chiller doors, sides and canopies, shelf and rack branding, activation stall
  backdrops, fascias, table skirts and entry arches. These are a key visual *applied to an object*, which
  needs a panel-by-panel spec and a mock-up in situ, not a crop.
- **Out-of-home** — hoardings, bus shelters, unipoles, auto-rickshaw panels, wall paintings.

The dimensions are sensible Indian retail defaults and a vendor's spec always wins. State them as
defaults, and if someone gives you a real bay measurement or a printer's sheet, use theirs.

Two constraints that catch people out, both in the table:

**Some formats are printed on both sides.** A dangler spins. If side B is blank, half the shopper's
encounters with it are with a white rectangle. Either both sides carry artwork or the piece is die-cut so
there is no back.

**Some formats are physically obscured.** A backing sheet has product standing in front of its lower half.
A table skirt has legs and a crowd across it. A stall backdrop has people in its lower third. Artwork that
puts the line where a shopper's body goes has no line.

## What to produce

For a full kit, in this order:

1. **The key visual** — hero type and why it, the six slots each specified, the render prompt, what is
   deliberately reserved and where. Approve this before going on.
2. **A format list** with the reason each is in the kit. A kit is a media decision, not a catalogue dump —
   a brand with no modern-trade listing does not need a gondola header.
3. **One adaptation sheet per format** — crop, re-stack, drop-out, print spec, and the line as it appears
   at that size (a 12:1 strip may need three words where the poster has nine).
4. **What is missing** — every unresolved mandatory, every claim without a source, every dimension you
   assumed. Named, not smoothed over.

## Refuse rather than guess

Consistent with the rest of this studio: a piece that cannot be made honestly is not made.

- **No signed-off pack** → refuse the master render. Name the upload.
- **No idea platform, no house message, nothing typed** → refuse. Say what to settle first. POS is an
  expression of an idea and there is no idea yet.
- **An unsourced claim on the piece** → do not render it. A percentage, a "No. 1", a clinical claim or a
  comparison goes on POS only with its source and its footnote, because POS is the piece that gets
  photographed and complained about.
- **A dimension you do not know** → say what has to be measured and by whom. Do not invent a bay size.

Mark sources throughout: `[brief]`, `[house]`, `[platform]`, `[library]`, `[vendor]`, or `[assumed]` for
anything you supplied yourself.
