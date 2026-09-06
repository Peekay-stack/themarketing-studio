---
name: pr
description: Plan and write earned media — PR objectives, the declared message set, a media map of outlets and journalists, press releases in text and video, and the measurement that separates coverage from effect. Use when asked for PR, public relations, a press release, a press note, media relations, a media list, a journalist list, earned media, a media kit, a video news release, a company profile for press, coverage measurement, share of voice, or a crisis or recall statement.
---

# Public relations

PR is the only medium where somebody else says it. That single fact decides everything below.

> **PR carries a proof. It cannot construct a feeling.**

That sentence is not a style preference — it is in the studio's own medium taxonomy, and it is the
constraint that separates a PR brief that works from one that reads like an advertisement nobody bought.
A film can make a mother feel something about a morning. A press release cannot. What a release can do
is get a checkable fact stated by a masthead the reader already trusts, so that when the film arrives,
the claim underneath it has already been verified by somebody with no reason to flatter the brand.

Everything that goes wrong in PR goes wrong by forgetting that. A release written like an ad. An
objective borrowed from the sales target. A "key message" with nothing under it. A media list of two
hundred addresses and no relationships.

## What the code already decides, and you must not re-litigate

`pr.py` owns the vocabulary, the arithmetic, the gates and the refusals. Your job is judgement. Do not
argue with these — they are checked, and a draft that violates one is rejected rather than improved:

- **The objectives funnel descends the plan's own ladder.** `business` objectives are refused outright,
  `marketing` contributes but never owns, `communication` is the row a PR objective is written against.
  You do not get to write a PR objective against a revenue number.
- **The message set is capped at three**, and each message points at a reason to believe from the house.
- **Locked copy is placed verbatim.** A claim, a mandatory, an FSSAI line — legal text is placed exactly
  as written. A paraphrase is a compliance failure, not an edit.
- **Outlets may be suggested. Journalists may not.** Never invent a reporter's name, beat or contact.
  If you do not have it from the person or a licensed import, say the record is missing.
- **No AVE.** Never price coverage as if it were advertising. Six global industry bodies reject it, and
  it scores a glowing review and a demolition identically.
- **Nothing sends itself.** You prepare; a named person sends.

## The sequence

```
Plan objectives ──► PR objectives ──► the message set ──► the media map ──► the release ──► coverage
   (level: business/marketing/communication)      │                            │
                                                  │                            └─ text + kit, per language
                                                  └─ what pull-through is measured against
```

The message set is the hinge. Everything downstream is written against it and everything upstream feeds
it, and it is the reason PR can be measured at all.

## Writing the release

Inverted pyramid, and the reason is mechanical: **an editor cuts from the bottom.** A release that
builds to its conclusion loses the conclusion first.

1. **Headline** — the news in the words a reader would use, not the words the company uses internally.
2. **Dateline** — place and date.
3. **Lead** — answers all five: who, what, when, where, why. The five are stored as separate fields
   because the gate checks them individually. `why` is the one that gets fudged: answer why a reader
   outside the company should care, never why the company is pleased.
4. **Support** — the numbers and the detail that back the lead.
5. **Quote** — a named person, with their role, saying something a human being would say out loud. If
   you would be embarrassed to read it aloud, it is a slogan wearing quotation marks. Test: could this
   sentence have been said by a competitor's CEO about their own company? If yes, it says nothing.
6. **Background** — context. Last, because it is the first thing cut.
7. **Boilerplate** — what the company is, in three sentences that never change.
8. **Contact** — a person who will answer today.

300 to 400 words is where a release gets read. Under is fine if nothing is missing; over about 400 it
gets skimmed, and what is below the quote is usually what should go.

**No adjectives in the lead.** "India's finest", "revolutionary", "state-of-the-art" — every one of them
tells a journalist this is marketing copy and can be deleted without loss. State what happened.

## The video release: elements, not a film

A newsroom cannot put an advertisement inside a bulletin. It needs pieces it can cut:

- a **soundbite** — one named person, 20 to 30 seconds, their own words;
- **b-roll** — clean footage of the process. **No music, no voice, no supers.** The studio's scored
  master is the finished film and is refused as b-roll by the code;
- **stills** at print resolution;
- a one-page **company profile**;
- the **release text**, in each language.

The most common failure is handing over the ad and calling it a video news release. It does not get used,
and nobody tells you why.

## Translation

A translation is not a rendering, it is a re-writing against the same proof. Two rules:

- **Never machine-final a claim.** A translated legal line has to be checked by a person who reads that
  script. The code will not let a translation ship without a named checker, and it clears the check
  every time the text is edited.
- **Say what will not survive.** Idiom, wordplay, a headline that works on a pun — flag it rather than
  translating it into something flat and pretending it is equivalent. In Devanagari or Telugu a
  generated headline is not writing at all; type is set by a person.

## Suggesting outlets

You may propose mastheads, editions and trade titles: those are public facts. Lead with the
**state-language press**, because that is where attitudes are actually formed for most readers and it is
the tier most brands under-serve — usually because nobody in the room reads it. In every Indian language
market the top two titles take more than half the readership, so a good list is short.

For each suggestion give the language, the tier, and one line on why it fits *this* objective. Do not
pad the list. Fifty outlets nobody has a relationship with is worse than eight who will read the email.

## Measuring it

Report, in this order:

1. **Message pull-through** — of the items that ran, how many carried one of the three declared
   messages. This is the number that separates coverage from effect.
2. **Prominence** — headline, lead, or paragraph fourteen. A mention is not a mention.
3. **Coverage and circulation by language**, as two separate figures. Print circulation and digital
   audience measure different populations; there is no combined total, and inventing one is worse than
   reporting neither.
4. **What is missing.** A title with no audited circulation has no defensible audience figure — the
   Indian Readership Survey has been suspended since 2019, so there is nothing to fill the gap with.

## Crisis and recall

The response machinery is not built yet, and until it is, **do not draft a recall statement from this
skill.** What you may do is help prepare: holding statements agreed in advance, a named spokesperson, a
fact base. Under pressure the right behaviour is retrieving approved language, not composing new claims.

Two things you must never do, in any category:

- **State what a regulation requires from memory.** The obligations are entered and confirmed by the
  client's legal team, with a source and a review date. Reciting FSSAI or CDSCO rules unaided is the
  most dangerous thing available here.
- **Infer the risk class.** Whether a recall is Class I is a QA and legal determination with legal
  consequences. Ask; never assume.

The product regulator differs by category — FSSAI for food, CDSCO for cosmetics, BIS for textiles and
cement — and beauty in particular has **no** codified recall procedure with a public-notice template the
way food does. Do not imply one exists.

## The one that applies to everything

**CCPA's Guidelines for Prevention of Misleading Advertisements and Endorsements, 2022** cover every
category the studio works in. Any material connection between an endorser and the brand must be
disclosed — and that means monetary payment, **free product**, a **family relationship**, or an **equity
stake**, not only cash. Penalties reach ₹10 lakh, ₹50 lakh for repeat violations, plus a one-to-three
year ban on the endorser.

So the line between an earned voice and a paid one is a legal line, not a taste one. An unpaid dietitian
who chooses to comment is earned. The moment anything of value changes hands it is an endorsement, it
belongs in the paid `influencer` medium, and it must say so.
