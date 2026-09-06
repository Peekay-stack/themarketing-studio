---
name: messaging-house
description: Build a messaging house from a brand brief — core message, emotional and functional messages, RTBs for each, demo propositions, a lifestyle-and-culture layer, and the message adapted per medium. Works one layer at a time: offers a spread of real options, the user chooses, and the layers below are written against that choice. Use when asked to build a messaging house, message architecture, messaging framework, communication strategy or message pyramid.
---

# Messaging house

Turn a brand brief into a **messaging house**: one core message, and every layer beneath it that an
execution needs in order to be on-strategy without being briefed again.

This is **not** a document you produce in one go. Do one layer at a time, offer options that differ
on the strategic bet, and stop and ask the user to choose before writing the layer below. The value
is in the choosing.

## The house

```
                    CORE MESSAGE
                          |
        +-----------------+-----------------+
   EMOTIONAL                            FUNCTIONAL
   what it means to them                what it actually does
        |                                     |
   EMOTIONAL RTBs                       FUNCTIONAL RTBs
   why the feeling is earned            why the claim is true
        +-----------------+-----------------+
                          |
              PROOF / DEMO PROPOSITIONS
        what can be shown, demonstrated or measured
                          |
              LIFESTYLE & CULTURE
   occasions · rituals · codes · idiom · iconography · avoid
                          |
              MESSAGE BY MEDIUM
   digital · social · TV · OOH · POSM · on-ground
```

## How to run it

1. **Read the brief.** If none is given, ask for one — or ask the five questions you actually need:
   what is sold, to whom, what they believe now, what should change, and what makes it true.
2. **One layer at a time, in the order above.** Never skip ahead. A layer written before its parent
   is decided is a guess dressed as a strategy.
3. **Offer 4–6 options** per layer. They must differ on **what is being claimed and to whom**, not
   on wording. Three phrasings of one idea is one option — say so rather than padding to four.
4. **Number them, give each a one-line rationale**, and stop. Ask which the user wants, and say they
   can pick more than one, edit one, or write their own.
5. **Write the next layer against the choice.** Quote the chosen line at the top so the thread is
   visible.
6. **If a choice above changes later, say plainly what below it is now invalid** and offer to redo
   those layers. Do not quietly leave stale work in place.

## Layer rules

**Core message.** One line. The proposition made sayable. If a competitor could say it with their
name swapped in, it has failed — say so and try again.

**Emotional vs functional.** Two readings of the *same* core message, not two messages. The
emotional is what the buyer feels is true about themselves; the functional is what the product
demonstrably does.

**RTBs.** One set for each. A functional RTB is a fact about the product, process or sourcing. An
emotional RTB is why the feeling is *earned* — a behaviour, a heritage, a consistency over time.
**Every message needs at least two.** One is an assertion; none is a slogan.

**Proof and demo propositions.** What can actually be shown: the pour, the side-by-side, the farm at
4am, the seal. This is where most houses are thinnest, so push here.

**Lifestyle and culture.** The signs the brand owns and repeats. Give a spread across all six, and
tag each one:

- **occasion** — the moments that cue the category. Ask when people actually reach for this.
- **ritual** — the repeated small acts around use. The most ownable and least copied.
- **code** — visual and material signs: objects, textures, light, materials.
- **idiom** — the words people really use, in the language they use them in. Do not translate a
  phrase that works better untranslated.
- **iconography** — recurring images the brand can own across every medium.
- **avoid** — codes that read wrong for this brand or culture. State these plainly; they save more
  work than the positive list.

**Message by medium.** The same message re-expressed for what each medium can do. Not a truncation.
A 6-second bumper, a shelf strip and a promoter's opening line are different acts of communication.
Name the occasion each one serves.

## Discipline — enforce these on yourself

1. **Proof before claim.** No message survives without two RTBs. If they are not there, say the
   claim cannot be supported rather than inventing support.
2. **Mark your sources.** Tag every RTB and proof point `[brief]` when it traces to something the
   user gave you, and `[unverified]` when it does not. Never present an invented fact as evidence.
   This is the single most important rule here.
3. **Occasion or purpose.** Every medium adaptation names the moment it is for.
4. **Verbatim copy.** Claims, mandatories and campaign lock-ups are placed exactly as written and
   never paraphrased or improved.
5. **Thin brief, thin house.** If the input is sparse, produce fewer options and mark what is
   missing. A confident house built on nothing is the worst possible output, because it is the one
   nobody checks.

## Style

Write the way a strategist briefs a room, not the way a deck reads. Short declaratives. No
"leveraging", no "resonates with", no "in today's fast-paced world". A line a promoter can repeat
from memory beats a line that scans well on a slide.

## Output

Give the user **both**, every time a layer is decided:

**A working table** — editable, copy-pasteable:

| Layer | Chosen | Source | Note |
|---|---|---|---|
| Core message | … | [brief] | why this bet |

**A one-page house diagram** — once the two pillars and at least one layer below them are
decided, render the house as a self-contained, editable HTML artifact. The shape is specified in
`references/diagram.md`, with a worked example in `references/example-summary.html`:

- a true triangular **roof** carrying the core message and the platform line
- **two matched pillars, side by side** — emotional and functional — each with an **evidence
  counter** (`2 of 2 sourced`) and exactly ONE message. Nothing else goes inside a pillar, and they
  never stack except on a phone: a collapsed pair reads as one pillar supporting the other, which is
  a strategic claim made by accident
- a full-width **outstanding facts** strip below both, if any RTB is unverified
- **lifestyle & codes** as six boxes, the one chosen code per kind, `avoid` tinted apart
- the **hero demo** as the foundation
- a **basement**: platform, brand-model discipline, launch window

The summary is not the whole house. RTB reasoning, full code lists, alternative demos and the
channel adaptations stay in the long document; this page carries only what someone has to hold in
their head. Every text element is editable, with a button to save a clean copy.

At the end, offer: a one-page summary, a `.docx` or `.pptx` version, or a JSON block for pasting
into another system.
