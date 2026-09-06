# Building the key visual

## A key visual is a layer stack, not a photograph

This is the single most important thing in this skill, and getting it wrong produces work that is
competent and does not look like POS material at all.

Indian FMCG point-of-sale is **flat-colour graphic design with cut-out photographic elements placed on
it.** It is assembled from separately-sourced layers. It is not a photograph with words on top.

Look at `exhibits/dabur-honey-stay-fit.jpg`. There is no photographic scene anywhere in it. There is a
white-and-yellow diagonal split of flat colour; a woman **masked out of her background** and placed on it;
a pack and a glass grouped as another cut-out; a headline inside a weighing-scale-shaped badge; a brand
name in a yellow highlight box; a base band; a footnote strip; a contact box. Nine of the thirteen
exhibits are built exactly this way.

The consequence for how you work:

> **You do not generate a poster. You generate assets, and then you lay them out.**

An image model's job is to produce a **subject isolated on plain white, ready to cut out.** That is a much
easier thing for it to do well than a finished composition, and it is what a real studio does — shoot on
white, mask, place.

It also means **"reserve empty space for the type" is a problem that should not exist.** You only need to
hold space open inside a photograph if that photograph has to be the entire poster. On a flat colour field,
the field *is* the space. Any technique that draws a translucent band over a full-bleed image to make room
for a headline is a symptom of building the wrong thing — see `failures.md`.

## The layer stack

Bottom to top. Not every piece has every layer, but the order never changes.

| # | layer | what it is |
|---|---|---|
| 1 | **field** | Flat brand colour. Or two colours divided by a straight, diagonal or curved edge. Or a brand pattern. **Never a photograph.** |
| 2 | **field graphics** | Optional, low contrast, brand-owned: light streaks, waves, doodles, splats, bokeh. Sits on the field, under everything else. |
| 3 | **hero cut-out** | The subject, masked out of its background, hard-edged, with a soft drop shadow to seat it on the field. |
| 4 | **pack cut-out** | The real pack, masked, with a shadow or reflection. From the library, never generated. |
| 5 | **type blocks** | Headline (usually multi-weight), support lines. Real editable type. |
| 6 | **devices** | Badges, roundels, NEW flashes, highlight boxes, underline rules — the things that make type read as POS rather than as a caption. |
| 7 | **brand block** | Logo lock-up as vector artwork, cornered. |
| 8 | **base band** | Flat colour strip carrying the tagline, then the footnote strip, then a care or contact box. |
| 9 | **mandatories** | Veg mark, FSSAI, licence number. Smallest, usually inside the base band. |

## The two constructions

**Layered graphic build — the default.** Everything above. Use it unless there is a specific reason not to.
Cheaper, faster, adapts across formats trivially, survives bad printing, and it is what the category looks
like. `dabur-honey-stay-fit.jpg`, `nivea-men-derma-control.jpg`, `nivea-creme-soft-milk.jpg`,
`pantene-sonakshi-broken-cycle.jpg`, `motherdairy-dosti-range.png`, `nandini-kmf-dealer-board.jpg`.

**Photographic build — the exception.** A real photographic scene occupying most of the frame, with a flat
band for type. Only correct when **the scene itself is the argument**: a demonstration whose mechanism has
to be visible (`surf-excel-matic-smart-shots.jpg`), a metaphor built as a real object
(`dabur-honey-heart-health.jpg`), or an occasion whose whole point is the moment
(`surf-excel-holi-daag-acche-hain.jpg`, `motherdairy-haldi-milk.jpg`).

Even these carry a **hard split** into a flat zone — Mother Dairy Haldi is photograph above, solid orange
below, and the photograph is never asked to host type. That split is the rule, not the decoration.

If you choose the photographic build, say why the scene is the argument. "It looks better" is not a reason;
it is how you end up with a stock photo and a caption.

## Field division

How the flat zones are made. This is most of what makes a piece read as designed rather than assembled.

| device | where it works | exhibit |
|---|---|---|
| **hard horizontal split** | The safest. Photograph or hero above, flat colour below carrying type and pack. | `motherdairy-haldi-milk.jpg` |
| **diagonal split** | Creates two type-safe zones out of one frame with energy. Excellent on portrait formats. | `dabur-honey-stay-fit.jpg` |
| **curved split** | Softer, warmer, more premium than a diagonal. Needs width to read as intentional. | `surf-excel-matic-sanath.jpg` |
| **single flat field** | One colour, everything floated on it. The most POS-looking of all, and the most forgiving in adaptation. | `motherdairy-dosti-range.png` |
| **brand pattern field** | A brand-owned repeating graphic. Makes a fragment recognisable with no logo in it. | `nivea-creme-soft-milk.jpg` |
| **radiating streaks / glow** | Behind the hero, to lift it off the field and imply energy. | `dabur-chyawanprash-100-illnesses.jpg` |

## Type devices

Type on POS is not set on a background; it is **built**. This vocabulary is most of the difference between
a piece that looks like POS and one that looks like a slide.

- **Multi-weight headline.** One word or phrase very large, the rest smaller. Never one uniform size.
  Pantene bolds two words *inside* the sentence rather than adding a second type size.
- **Shaped badge containing type.** Dabur's weighing-scale holding *"WANT TO STAY FIT?"*. A roundel, a
  seal, a starburst, an object shape relevant to the claim.
- **Highlight box behind a word.** *"DABUR HONEY"* in a yellow box inside a longer line.
- **NEW flash.** Rounded rectangle or roundel, high contrast, one word. Almost every launch piece has one.
- **Underline or rule as emphasis.** Nivea's *"UNDERARMS"*.
- **Stroked or outlined type** where the field behind it varies.
- **Base band tagline**, locked, always the same position across the kit.
- **Footnote strip**, smallest type on the piece, substantiating any claim above it.
- **Care/contact box** in a contrasting colour, cornered — Dabur's maroon block.

Cap the support items at four. `dabur-honey-heart-health.jpg` runs exactly four and is at the ceiling.

## Craft: the six things that separate a comp from artwork

The layer stack says *what* is on the piece. These say whether it was *made* properly. Every one of
them was found by looking at real output that was structurally correct and still looked wrong.

**1. Cut out on mid-grey, never on white.** A matte is solved by separating subject from backdrop, so
the backdrop must be a colour the subject does not contain — and in dairy half the subjects are white
or near-white: milk, a glass of it, a splash, a white pack panel, a school shirt. Keying white out of
those punches holes through the product. White also contaminates every anti-aliased edge, so the
subject arrives on the field wearing a pale halo. Mid-grey (`#808080`) fixes both, and it is the same
reasoning that makes chroma-key backdrops green rather than white.

**2. Defringe and decontaminate the matte.** An anti-aliased edge pixel is a MIX of subject and
backdrop and therefore literally contains the backdrop's colour; moved to a new field it shows as a
halo. Contract the matte by a pixel to drop the worst ring, then solve the backdrop colour out of what
remains (`C = a·F + (1−a)·B`, so `F = (C − (1−a)·B) / a`). Photoshop ships this as Defringe and Remove
White Matte; it is not optional polish.

**3. Fit the subject, not the file.** A generated cut-out carries a wide transparent margin — measured
on a real one, the subject filled 43% of the image area. Fit the image and the subject renders at half
the size the layout allocated, and the piece looks empty. Crop to the alpha bounding box first.

**4. Two shadows, one light.** A shadow that grounds an object is two elements: **ambient occlusion**,
very dark and tight exactly at the contact line, and a **cast shadow**, broader and softer, thrown away
from the light. Occlusion is what actually seats the object; the cast shadow is what carries direction.
One medium-soft blob is neither. And the light direction is a KIT-level constant — a shadow that
changes angle from poster to dangler makes eleven pieces look like eleven jobs, which is the same
failure the governing rule exists to prevent.

**5. Type is set at display size, so track it in.** Spacing that reads correctly at 16px reads loose at
150px. Display type takes slight NEGATIVE tracking and tighter leading (~1.15), not the defaults.
Kerning must survive whatever tracking is applied — losing the font's kern pairs to gain tracking is a
worse trade at this size.

**6. Contrast has a number.** WCAG's floor for large text is **3:1** (relative luminance, gamma
corrected). Use the convention — knockout white on a mid-to-dark field, dark ink on a light one — and
use the ratio to VERIFY it rather than to choose it; picking purely by highest ratio sets a dairy
poster in charcoal and loses the category's look while both options clear the floor. If the
conventional ink fails 3:1, the field colour is the problem. Do not reach for a slab behind the words.

**And squint at it.** Shrink the finished piece to a thumbnail and blur it. If no single element leads,
there is no hierarchy; if it flattens to one tone, it is mush and it will fail at two metres too. This
is the cheapest check in the document and the easiest to skip.

## Generating the assets

Three separate jobs. Only the first involves an image model.

### 1. The hero cut-out

Prompt for an **isolated subject on plain mid-grey** (see craft rule 1 above), not a composition:

> [subject, described physically]. Isolated on a plain pure white background. The entire subject is
> visible with clear space around it. Even, soft, directional studio lighting. Sharp focus throughout,
> deep depth of field, no background blur. No environment, no set, no props, no furniture, no floor line,
> no cast shadow on the background. Nothing cropped by the frame edge. Photorealistic. Absolutely no text,
> lettering, logos, watermarks, borders or branding of any kind anywhere in the image, including on any
> object or garment in frame.

Then remove the background. Canva has a background remover; any design tool will mask it.

**Why white and not the brand colour:** a subject generated already sitting on Deep Forest green cannot be
lifted off it cleanly, and the green in the render will not match the brand's green. Generate on white,
mask, place on the real colour.

**Why "no floor line":** a horizon or surface edge in the asset is a second element that has to be masked
out, and models put one in by default. Say it explicitly.

### 2. The pack cut-out

From the library. **Never generated** — see the pack rule in `SKILL.md`. If the library has no pack, the
piece is blocked at artwork stage, not at render stage, which means the field and the hero can proceed
while the pack shot is being sourced.

### 3. Field, devices and type

Made in the design tool. Not generated, not prompted. The palette comes from the brand profile or the
house's stated colour code; the typeface comes from the brand. A model inventing either produces a piece
that is off-brand in the two most visible ways.

## Specifying the key visual

Write out every layer. A layer you leave vague is one somebody else decides by default.

**field** — which division device, which colours, which zone carries type.
**hero** — which of the six types below, what is in frame, what is deliberately left out, and the cut-out
brief. Name the crop of the subject (head-and-shoulders / three-quarter / full figure), because that decides
which adaptations are possible.
**pack** — which pack, angle, size as a percentage of frame height, position. Lower third, 15–30% of height,
front-facing and level, overlapping the hero slightly so the two read as one group rather than two pasted
layers.
**type blocks** — the exact words, the weight hierarchy, and which device each sits in. Taken from the
platform's POSM expression, the house's POSM message, or the house's core — in that order of authority.
Never newly written here.
**brand block** — logo lock-up, which corner. Top for pieces read at distance, bottom for pieces read close.
**support** — up to four, three words or fewer each.
**base band** — tagline, footnote, care box.
**mandatories** — everything statutory, and the footnote for every claim.

## The six hero types

Pick one deliberately and say why. **Check the crop gate first** (below) — it eliminates options before
merit does.

**1. person-in-benefit** — the consumer visibly carrying the result. `pantene-sonakshi-broken-cycle.jpg`,
`nivea-creme-soft-milk.jpg`, `nivea-men-derma-control.jpg`. The person *is* the proof. Strongest where the
benefit photographs — hair, skin, a clean shirt. Fatal where it does not: a photograph cannot show immunity
or digestion, and a smiling face standing in for an invisible benefit is the most generic POS piece there
is. *Needs:* casting and usage rights.

**2. endorser-with-pack** — a known face presenting the product. `dabur-chyawanprash-100-illnesses.jpg`,
`surf-excel-matic-sanath.jpg`, `dabur-honey-stay-fit.jpg`. Borrows credibility and buys stopping power.
Note the posture in all three: the endorser **holds or presents** the pack, and their eyeline or gesture
points at it. An endorser standing beside a product is a photograph of a famous person. *Needs:* signed
talent, a `cast` or `actor` library reference so likeness is pinned by image, and a territory-and-term check.

**3. metaphor-object** — the benefit made into a single object. `dabur-honey-heart-health.jpg`. **Strongest
at distance, cheapest to produce.** One shape, high contrast, no talent, no rights, and it reads as a
silhouette at four metres where a face does not. Use it when the benefit is invisible — which is exactly
when types 1 and 2 fail. Immunity becomes a shield; strength becomes something bearing weight; purity
becomes something untouched. *Needs:* a metaphor that is one object. If it takes two things to read, it is
not this type.

**4. occasion** — the moment of use or celebration. `surf-excel-holi-daag-acche-hain.jpg`,
`motherdairy-haldi-milk.jpg`. Sells **relevance rather than superiority**. Right for festival and seasonal
kits, and for categories where every functional claim is the same. Both exhibits carry a *relationship*,
not just an event. *Needs:* a real occasion with a date. "Family time" is not one.

**5. range-array** — the portfolio as the hero. `motherdairy-dosti-range.png`. Says *"we are a house"*, not
*"this is better"*. Only correct when **breadth is the message**. Wrong for any single-SKU push: it splits
attention across five shapes at the moment you needed one recognised. Note that the exhibit gives the array
a *reason to be a group* — cartoon limbs turn five SKUs into one idea. *Needs:* every pack as a library
reference, and a decision about which pack leads.

**6. product-in-use / demonstration** — the product doing its work. `surf-excel-matic-smart-shots.jpg`. The
only type that carries a functional claim without a person vouching for it. Needs the mechanism to be
*visually legible* — a vortex, a stain lifting, a coating. An invisible process staged as a glow is
decoration pretending to be a demonstration. *Needs:* a mechanism that shows, and a sourced RTB.

## The crop gate — apply this before comparing types on merit

The kit's aspect spread constrains the hero, and it eliminates options that are otherwise the strongest.

Ask: **can this hero survive a 12:1 strip and a 1:1 wobbler?**

A two-person occasion cannot. A full-figure endorser cannot. A single object can, and a cut-out fragment
can. If the kit needs the very wide and very small formats and your hero is a scene, either the hero
changes or those formats get their own separate treatment — decide which now, not at adaptation.

This is why the strategically strongest hero is often not the buildable one. Say so explicitly rather than
discovering it eleven sheets later.

## Before you offer it

1. **Is the field flat colour, and is the hero a cut-out on it?** If you have produced a photograph with a
   headline over it, you have produced the wrong thing.
2. **Is there a hero that is not the pack?** If the pack is the only subject, this is a pack shot.
3. **Is the pack the real pack, from the library?** If it was described in words, stop.
4. **Is any type inside a device** — a badge, a box, a flash, a rule? A headline floating alone on a field
   reads as a slide.
5. **Is there a base band with the tagline, a footnote and the mandatories?**
6. **Is there any generated lettering anywhere**, including on the subject's clothing or on any object?
7. **Squint at it as a thumbnail.** One shape, one contrast, the brand. If it becomes mush, it fails at two
   metres too.
8. **Does it pass the crop gate** at 12:1 and 1:1?
9. **Is the subject actually filling its box** — or is it a small thing floating in a large void because
   the file's transparent margin was fitted instead of the subject? (Craft rule 3.)
10. **Is the hero seated** — occlusion at the contact line, cast shadow going the same way as every
    other piece in the kit? (Craft rule 4.)
11. **Does the pack overlap the hero**, or are they two objects sharing a page? Proximity is what makes
    the eye read them as one group.
12. **Does the headline clear 3:1** against what is actually behind it, measured rather than assumed?
    (Craft rule 6.)
