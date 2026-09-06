# Handover 16 — the idea platform screen. One crash fixed, four things to build.

Handover 15 is in and verified against a live server. Everything you built works: the plan clears its
findings as somebody types, the nav returns to the open document, on-ground generates venue-led ideas.

Then the client used the platform screen properly for the first time and found the four gaps below. All
four backends are built and tested; this is the UI half.

**Work on the `app.dc.html` in this folder** — it has one fix of mine in it (§0).

---

## 0 · A crash I fixed in your file. Please keep it.

Clicking *Lifestyle & culture* whitescreened the app:

```
Root.renderVals(): Cannot access 'tagList' before initialization
```

`const tagList` was declared at line 11337 and read from line 11288 — 49 lines earlier, inside the new
grouping block. `const` is not hoisted the way `var` is, so the read threw and took the whole render with
it.

I moved the declaration above its first use, with a comment saying why. It depends only on `cur` and
`st`, so it is safe that early.

**Worth knowing because `checkfe` cannot catch this class** — it reads lexical structure and pairing, not
use-before-declare ordering. If you insert a block that reads existing locals, the declaration order is on
you. I have not added a check for it; a proper one needs a real JS parser and I would rather tell you than
ship a half-check that cries wolf.

---

## 1 · A steer box on every regenerate  ·  *the biggest of the four*

The client's words: *"I need to be able to give inputs for further rounds."*

Rounds after the first are where a platform actually gets found — and every round was identical to the
first, with no way to say what was wrong with the last one.

```
POST /idea-draft { house, n, steer?, build_on? }
```

`steer` is free text and it outranks the route spread where they disagree.

**Build:** a text box beside *Try again — three fresh routes*, placeholder something like *"What is wrong
with these? 'Sharper', 'go at the enemy', 'keep the second mechanic but change the territory'."* Send it
as `steer`. Keep it filled after the round so somebody can adjust rather than retype.

Also send it on **Build on this** — the same box, the same field. "Develop this one, but for trade" is the
most useful thing anybody types on that screen.

Measured: *"None of these work — go at the enemy. Loose milk sold from a can is the real competitor"*
returned **"Ask The Can"** and **"500 vs Nobody"**. It redirects completely.

---

## 2 · The routes now ladder to the house — show it

The client: *"routes should be based on emotional and functional needs including the RTBs."* They were
right, and the old spread was mine: routes differed by generic archetype — *a category tension, a ritual
it owns, an enemy* — which produced three good ideas that floated free of the house. Nothing showed how a
platform laddered, and the five tests could not check it either.

Each option now comes back with:

```
pillar   "emotional" | "functional" | "both"
rtb_id   the id of the reason-to-believe it dramatises
rtb      that RTB in one clause
kind     the route, in the house's terms
```

Live:

```
Chosen This Morning     [emotional]   rtb: the milk is chosen fresh from good farmers each morning
The 500th Check         [functional]  rtb: 500 dairy professionals check the milk every day
Nothing Left To Chance  [both]        rtb: 500 people checking means no batch is ever a gamble
```

**Build:** put `pillar` on the card as a badge — it replaces the long `kind` string you show now, which
was never meant to be read that way — and `rtb` as a line under the idea, prefixed *"rests on:"*. A reader
should be able to see the ladder without opening the house.

An unsourced RTB is flagged in `caveat`. Worth showing amber.

---

## 3 · Expression by medium has no way to generate

The client: *"expression by medium does not have generation options/button from the selected idea
platform."* Correct — the five slots could only be typed into, which asks somebody to derive all five by
hand from a blank box.

```
POST /platform-express-draft { house|set, item?, media?, steer? }
  -> { expressions:{video,social,posm,activation,incentive}, set, status, detail }
```

Writes them, stores them, returns the updated set. Each is written against what that medium can actually
do — `EXPRESSIONS` says what each is for, and it is not the same job five times.

**Build:** *Write these for me* on the expressions block, and a per-slot *rewrite* that sends
`media: ["posm"]` for one. Everything stays editable after — same rule as everywhere: rewriting it makes
it yours.

**Note the route name.** `POST /platform-express` already exists and **stores one expression a person
wrote** — I nearly registered a second handler on that path and my own duplicate-route check caught it.
Generating is `-draft`; storing stays where it was.

---

## 4 · Nobody can test the platform against the five

The client: *"there is no way for anyone to test the idea platform against the five parameters — we
should have option for LLM to test and human to test."*

There are now **three** readings of each test, and they are deliberately kept apart:

| | | |
|---|---|---|
| the checker | `status.tests` | counts media, spots a sentiment verb. Cannot judge whether a competitor could sign the line. |
| the model | `platform.judged` | a verdict, a reason, and a `fix`. A challenge. |
| the person | `platform.verdicts` | the decision. |

```
POST /platform-judge { house|set, item? }
  -> { judged:{key:{verdict,note,fix,by,at}}, questions:{key:the question},
       disagreements:[keys], status, detail }
```

`verdict` is `holds` | `weak` | `fails`.

**Build: two columns, not one.** The model's verdict beside the person's, per test. Where they differ,
say so — the response hands you `disagreements` already, and its `detail` reads:

> *"The model disagrees with you on 4: true, ours, elastic, tension. That is the part worth reading."*

Where only the model has answered, label it plainly — **"a challenge, not a decision"**. A model verdict
sitting alone in a verdict column reads as the answer, and this layer exists precisely because these are
judgements somebody has to own.

Show `fix` where the verdict is `weak` or `fails`. It was specific in testing — *"'purity leads to
strength' is a cause-effect description with nothing refused or argued against"*, with a concrete change.

**The document already shows the shape you want**, if it helps: download the platform .docx and look at
the five-tests section. Two bulleted readings per test, the fix underneath, the disagreement called out in
amber.

---

## 5 · The download carries all of it

`GET /platform-docx/{id}?mode=record|worksheet` — you built the buttons in handover 15 and they work.
The document now also carries the pillar and RTB on the front page, both verdicts side by side, and an
*"Also considered, and not chosen"* appendix.

The route takes **any of three ids** — the set (`set` on `/idea-platform`), the house, or the adopted
platform's own `id`. You guessed `id` last round; it works now.

---

## Everything new since handover 15

```
POST /idea-draft              + steer;  options carry pillar / rtb_id / rtb
POST /platform-express-draft  new — write the five expressions
POST /platform-judge          new — the model's verdict on the five tests
GET  /platform-docx/{id}      now carries pillar, RTB, both verdicts, routes not chosen
```

Nothing else changed. `/platform-express` (the setter) and `/idea-platform` are untouched.

---

## Before you send

```bash
python tools/checkfe.py && python tools/contract.py && python tools/test_tools.py
```

18/18 here, 155 routes, no collisions.

Two of the four things above existed only because I built the platform layer without ever using it for a
real campaign. The client found all four in one sitting. Worth remembering next time either of us
declares a screen finished.
