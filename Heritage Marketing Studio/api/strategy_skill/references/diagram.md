# The one-page house

A messaging house is looked at far more often than it is read. Once the layers are decided, render a
single-page summary as a self-contained, **editable** HTML artifact. It has to survive being put on
a wall, pasted into a deck, screenshotted, printed in black and white, and rewritten by someone who
does not have you in the room.

`example-summary.html` is a worked example. Copy its **structure**, never its content.

## The shape, top to bottom

```
                    ROOF — a true triangular pediment
                    core message + platform line
                              |
        +---------------------+---------------------+
     PILLAR: EMOTIONAL                    PILLAR: FUNCTIONAL
        one message                          one message
        +---------------------+---------------------+
                              |
     OUTSTANDING FACTS — full width, if any
                              |
     LIFESTYLE & CODES — one chosen code per kind
                              |
     FOUNDATION — the hero demo proposition
                              |
     BASEMENT — platform · brand-model discipline · launch window
```

The summary is deliberately **not** the whole house. RTB reasoning, the full code lists, the
alternative demos and the channel adaptations all live in the long document. This page carries only
what someone must hold in their head, and it links to the rest.

## Zone by zone

**Roof.** An actual triangle — inline SVG polygon, so it prints. The core message is the largest
type on the page, one line. Platform and mass lines sit beneath in small caps-tracked type.

**Two pillars, and they are the structure.** Emotional left, functional right. **Matched pairs:**
each carries exactly the same furniture — a coloured capital, its label, an evidence badge, a
one-line gloss, and *one message*. Nothing else goes inside a pillar.

That symmetry is load-bearing. Put an extra block inside one pillar and it becomes visually heavier
while the other is left with dead space, and the pair stops reading as a pair.

- **Evidence badge**: `2 of 2 sourced` / `0 of 2 sourced`, counting the RTBs behind that message in
  the full house. This is the most important number on the page. A pillar whose reasons are all
  unverified is an assertion, and the summary is exactly what gets circulated and approved.
- **The pillars must never stack** except on a phone. Set the breakpoint at ~620px and shrink type
  before the grid breaks. A collapsed pair reads as "functional supports emotional", which is a
  strategic claim made by accident.

**Outstanding facts.** If any RTB is unverified, a full-width amber strip below both pillars names
what is missing and which pillar it sits on. Full width, not inside the pillar — see above.

**Lifestyle & codes.** Six boxes side by side, one per kind — occasion, ritual, code, idiom,
iconography, avoid — carrying **only the chosen code for each**. One line each. Render `avoid` on a
tinted ground: it is an instruction *not* to do something and must never be misread as a positive.

**Foundation.** The hero demo only, given room. Say what it proves and whether it is shootable now
or waiting on a fact. Supporting demos stay in the long document.

**Basement.** Three short items: the platform the brand stands on, the brand-model discipline
(NeedScope position or equivalent) including what it forbids, and the launch window with why.

## Editable

Every piece of text carries `contenteditable="true"`, with a quiet hover tint and a clear focus
ring. A strategist will rewrite a line in the room, and a diagram they cannot touch gets ignored.

Include two buttons: **Print / PDF**, and **Download edited copy** — a short inline script that
clones the document, strips the toolbar and the script itself, and saves it as a clean HTML file.

This is the one deliberate exception to "no scripts": editing that vanishes on refresh is worse than
no editing at all. Everything else holds — no CDN, no external fonts, no images, one file.

## Typography and colour

- One typeface. Size and weight carry hierarchy, not colour.
- The two pillar colours appear only a few times each. Used sparingly they mean something; used
  everywhere they are decoration.
- Test in greyscale. If the code kinds become indistinguishable, add letters or shapes.
- Nothing below 9px. This gets printed and projected.
- Print as **A4 landscape**. It is a short page now; A3 leaves it stranded in the middle of a sheet.

## What not to do

- No decorative house imagery — no roof tiles, no brick texture. A capital and a base on each pillar
  is structural; anything more is a costume.
- Nothing that appears only on hover; most people will meet this as a screenshot.
- Do not shrink a message to make a box fit. Reflow the box.
- Do not drop a code kind to save space. Cut the words inside it.
- Do not quietly remove the evidence badge or the outstanding-facts strip to make the page look
  finished. Once the channel detail is gone, those two are the only things left holding it honest.
