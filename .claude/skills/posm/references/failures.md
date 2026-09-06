# How POS material fails

Read this before writing a prompt. The two exhibits below are real output from this studio, and between
them they contain every failure mode this skill exists to prevent.

---

## Exhibit A — `FAILURE-heritage-pure-milk-a3.jpg`

Requested as a **Poster (A3)**, 3:4, Google. What came back: a milk pouch centred on a flat blue field,
with a translucent dark box across the bottom third carrying three lines of white type.

Eight faults, in descending order of seriousness.

**1. It is a pack shot, not a poster.** There is no hero. The entire frame is the product on a gradient.
Compare any of the thirteen reference exhibits: every one has a person, an occasion, a metaphor or a
demonstration, *and* the pack. This piece has nothing to say beyond "here is a bag of milk", which the
shopper can already see on the shelf below it.

**This is not a prompt-quality problem.** The instruction that produced it said *"ONE subject, filling most
of the frame. Not a scene, not a situation, not two things next to each other."* The model obeyed
faithfully. A rule written for a shelf strip was being applied to a poster.

**2. The brand mark is hallucinated.** The oval lock-up reading *Heritage*, the ® symbol, the words *PURE
MILK* — all drawn by the image model. It is plausible and it is not the brand's. This is the single most
dangerous failure in the tool: the whole architecture exists to keep generated letterforms off POS, and here
they are, on the pack, in the one place nobody thought to check. A piece like this teaches a shopper a logo
that does not exist.

**3. The type is a subtitle, not a layout.** A translucent slab dropped over a finished image, spanning the
full width, hard-edged, unrelated to anything in the composition. In the references, type either sits in
genuinely reserved negative space (Pantene's upper third, Dabur Chyawanprash's top) or on a colour block
that is *part of the design* (Surf's base band, Mother Dairy's plinth). The difference is visible at a
glance and it is the difference between designed and generated.

**4. The plate clips the pack.** The red base band of the pouch is cut off by the top edge of the type box.
Nothing decided where the pack ended and where the type began, because those two decisions were made by
different systems that never compared notes.

**5. There is no brand block.** No logo lock-up anywhere. The only brand presence in the piece is the
invented lettering on the invented pack. Every single reference exhibit carries a real logo, usually
cornered.

**6. The tagline is unusable.** *PureDoodhKiShakti* is set at roughly a fifth of the line's cap height,
unstyled, orphaned directly beneath the last line, with its `#` stripped. At the 2.5m an A3 is read at, it
is invisible. A tagline is either set to be read or left off.

**7. There is no mandatory zone.** No FSSAI mark, no veg mark, no care line, no footnote. This is a dairy
product in India; the piece cannot go to print.

**8. Zero support.** No benefit, no proof, no reason to believe. Compare `dabur-honey-heart-health.jpg`,
which carries four benefit marks down its right edge and is stronger for them.

---

## Exhibit B — `FAILURE-heritage-2.jpg`

The same line, different layout key. Here the pack is rendered **accurately** — the real Heritage Foods
lock-up, *FOODS*, *Pure Milk*, *1 Litre*, the green veg dot. So the pack is not always wrong.

The composition is destroyed anyway, and worse than in Exhibit A: **the type plate lands directly across
the middle of the pack, covering its logo.** The logo ghosts through the translucent plate, so the piece
reads as two stacked pouches, or as one pouch with a box taped over its face. The single most valuable
element in the frame — the brand mark on the pack — is the one thing obscured.

### The deeper root cause: the wrong model of what a poster is

Before the mechanical explanation below, there is a structural one that subsumes it.

**Both exhibits assume the poster is a photograph.** Generate one full-bleed image, then find somewhere in
it to put words. Every symptom follows from that assumption:

- The translucent slab exists because there was **no flat colour zone** for type to live in, so the zone had
  to be faked as an overlay.
- The slab clips the pack because a photograph has no reserved regions — only subjects and background.
- The brand block is missing because a photograph has no corner set aside for artwork.
- The pack had to be *generated* because a photograph must contain everything it shows.

Real POS material is **a flat colour field with cut-out elements placed on it.** On a flat field, none of
these problems arise: type sits on the field, the pack is a masked layer that cannot be clipped, the logo
has a corner, and nothing needs to be invented because each layer is sourced separately.

So the fix is not a better prompt or a smarter band-placement algorithm. It is to stop generating posters and
start generating **assets** — a subject isolated on white — and assemble them. See `key-visual.md`.

### The mechanical root cause

Exhibit B also shows a second, narrower defect worth understanding on its own terms, because it is what
happens whenever a system does try to reserve space inside a photograph.

The layout key is used **twice, independently**: once as a phrase in the image prompt asking the model to
reserve space, and once as a fixed band rectangle when the type is drawn on afterwards. Nothing checks that
the model actually reserved anything. Exhibit B's band sits mid-frame — the `type-only` position, whose
whole definition is *"type doing the whole job, pack as a small lock-up"* — while the render placed the pack
centred and large, exactly where the band was going to go.

So:

> **Reserved space is not reserved unless the render is checked.** A composition instruction the provider
> ignored is indistinguishable, downstream, from one that was honoured — and the type gets drawn into the
> subject either way.

Two consequences for how you work:

- **Look at the render before setting type on it.** Is the zone actually empty? If the pack, the hero or a
  bright gradient crosses it, re-render — do not set the line on top and hope.
- **The band and the composition must be decided together, from one source.** If the layout key says the
  type occupies the middle 40%, the render prompt must place the pack small and low, and that must be
  verified rather than requested.

---

## Exhibit C — `FAILURE-canva-photographic-build-1.png` and `-2.png`

The instructive near-miss. These came from a design tool rather than a raw image model, and they fix most of
what is wrong with A and B: correct legible type in a real font, a genuine flat green band for the headline,
a brand block locked at the base, a support badge for the claim, a proper structure top to bottom.

**And they still do not look like POS material.** They look like a good photograph with a headline above it.

The reason is the one in the section above. The brief asked for a *photographic hero* — a real scene, lit,
with depth — so that is what was built, and a photographic scene occupying two-thirds of a poster produces
an editorial page, not a shelf piece. Set either of these beside `dabur-honey-stay-fit.jpg` or
`nivea-men-derma-control.jpg` and the difference is instant: the exhibits are **cut-outs floating on flat
colour**, these are **photographs in a frame**.

Three further faults worth naming, because they recur:

**The logo is invented.** No brand kit was connected, so a plausible crest was generated. `-1` additionally
carries a garbled line reading *"PURE DOODH A YDG LTD"*. A design tool removes the garbled-letterform risk
for type you supply; it does not stop it inventing a brand mark you did not supply.

**Material and palette drift.** `-2` renders the vessels in **brass rather than steel** and the milk
**cream-yellow rather than white**, against an amber field instead of the specified Deep Forest. A yellow
pour from brass reads as buttermilk or ghee. Template-based generation gets structure right and approximates
specifics — so the specifics have to be supplied as assets, not as adjectives.

**One of four candidates came back as an unfilled template**, complete with *"123 Anywhere St, Any City, ST
12345"* and *"www.reallygreatsite.com"*. Always look at every candidate.

**The lesson is not "the tool was wrong."** The tool did what it was asked. The ask was wrong, and it was
wrong in exactly the way A and B were wrong: it treated the poster as a photograph.

---

## The other failures, in a list

Things that go wrong that are not visible in these two exhibits.

**The incoherent kit.** Eleven pieces generated separately from the same brief. Different lighting, pack
angle, background, model. The most expensive failure in POSM, and invisible in any single piece — you only
see it when the pieces are laid side by side, which is why that is a required check.

**The line that does not fit the piece.** A nine-word poster headline scaled down onto a gondola header read
at four metres. Legible in a preview, mush in the aisle. Word count follows reading distance, and the short
version is *written*, not truncated.

**The blank back.** A dangler printed one side. It spins; half its life is a white rectangle.

**The occluded line.** A backing sheet with the proposition across its lower half, where the product stands.
A table skirt with the mechanic across the part covered by legs and stock. The artwork is correct and the
message does not exist.

**The unsourced claim.** A percentage or a *No. 1* on the piece with no footnote. POS is the artefact that
gets photographed and complained about, and it is the one that is physically hardest to recall — it is
already pasted on nine thousand walls.

**The invented dimension.** A shelf-branding spec built on an assumed bay width. Bays differ by chain and by
store; the print run is wasted at scale rather than one piece at a time.

**The offer on a permanent substrate.** A dated price flash on a tin plate or a painted wall, both of which
stay up for years.

**The stretched crop.** A 4:5 master pulled to 2:1. The pack's proportions change, so the shape on the wall
no longer matches the shape in the hand — which defeats the only job POSM has.

---

## The two-metre squint

The fastest single test, and it catches most of the above. Shrink the piece to thumbnail size and look at it
for two seconds — roughly what a shopper at two metres gives it.

What should survive: **one shape, one colour contrast, the brand, and — if the piece is large enough — a
readable line.**

Exhibit A at thumbnail size is a blue rectangle with a white blob and a dark bar. Nothing survives, because
nothing was ever there.
