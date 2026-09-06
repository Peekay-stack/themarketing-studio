# Handover 17 — round 16 is in and working. Five gaps, all in one method.

Everything in handover 16 works. I ran all four in the live page, not just against the endpoints: the
steer box reaches both motions and stays filled, the pillar badges render colour-coded with the RTB under
them, *Write these for me* filled all five slots, and the two-column strip came back with the amber
banner and your **"THE MODEL — A CHALLENGE, NOT A DECISION"** label. That last one is exactly right.

Then I found five things by loading the screen rather than reading it. Four of them are in `loadIdea`.

**Work on the `app.dc.html` you sent** — I have not touched the frontend this round.

---

## 0 · First, a bug that was mine, and it made your `loadIdea` dead code

`GET /idea-platform` needs `?house=` or `?id=` to resolve anything. Your `loadIdea` correctly calls a bare
`apiGet('/idea-platform')` — which resolved *nothing*, returned `exists: false`, and hit your early
`return`. **Hydration had never run once**, for any of us, since the screen was built.

So: adopt a platform, navigate away, come back — name blank, line blank, five test notes blank, while all
of it sat safely on disk. Same "everything I did is gone" the plan screen was reported for, reached a
different way, and neither of us saw it because we both always arrived with a house already in state.

Fixed. A bare GET now falls back to the most recently updated set — which is the one somebody was just
working on — and says which route it took:

```
resolved_by : "id" | "house" | "latest"
```

Verified in the page: the name field came back reading *Purity leads to strength* and all five test notes
were populated, straight off a reload. Your code was right; it was being answered with nothing.

**Still worth sending `?house=` when you have one.** `latest` is a good guess, not a fact, and with
several brands in one tenant a guess can open the wrong document.

---

## 1 · `loadIdea` drops four things the server now hands it

The GET now returns these. Nothing reads them, so the screen still looks unasked:

```js
this.setState({ idea: { ...cur,
  id: got.id, name: got.name, line: got.line, tests: got.tests, routes: got.routes,   // you have these
  judged:            got.judged            || {},     // the model's five verdicts
  judgeQuestions:    got.questions         || {},
  judgeDisagreements:got.disagreements     || [],     // computed server-side now
  expressions:       got.expressions       || {},     // the five, as generated or typed
  pillar:            got.pillar            || '',
  rtb:               got.rtb               || '',
  houseId:           got.house             || cur.houseId,
} });
```

**Measured, on a reload after the model had judged all five:** server returned five verdicts, the screen
showed none, and the button still read *"Ask the model to test this"* rather than *"Re-run"* — so it read
as never asked. Same for the expressions: five stored, five boxes empty.

`got.house` is the one that surprised me. The house dropdown came back on *"No house — the platform
stands on its own"* for a platform that argues from Heritage, and because `ideaStands()` reads
`state.house`, **Try again refused to run at all** until I picked the house again by hand.

`disagreements` and `questions` are computed and returned in one place now, so the screen, the document
and the judge route cannot disagree about what disagreeing means.

## 2 · `weak` renders identical to `untested`

`VERDICT_STYLE` has `untested`, `holds`, `fails`. The model returns **four** verdicts — `holds`, `weak`,
`fails` — and your fallback `VERDICT_STYLE[mv] || VERDICT_STYLE.untested` catches `weak`.

Computed style, live: a `weak` badge and an `untested` badge both come back `rgb(107, 114, 128)`.

So the model's middle verdict — a criticism, with a `fix` attached — is the same grey as *nobody has
answered yet*. Those are opposite states. `weak` was much the most common verdict in testing (four of
five on a real platform), so it is not an edge case. It wants its own amber, alongside the `fix` you
already render.

## 3 · Picking a route throws the ladder away

`ideaPickOption` copies `name` and `line`. So `pillar`, `rtb`, `rtb_id` and `mechanic` — the four fields
you just built the badges *out of* — are gone from state by the time anyone adopts. Captured from the
live adopt body:

```
house, plan, name, line, tests, routes, source, skipped, brief
```

No pillar. No rtb. No mechanic. A route chosen *for* its pillar loses the pillar on being chosen.

The backend now accepts and stores all four on `/idea-platform`, and holds anything already stored when a
key is absent, so this is one line in `ideaPickOption` and four keys in `adoptIdea`:

```js
pillar: o.pillar || '', rtb: o.rtb || '', rtb_id: o.rtb_id || '', mechanic: o.mechanic || ''
```

`mechanic` matters most of the three. It is the field that separates a platform from a slogan, the
document prints it as *"The repeatable device"*, and both the expression writer and the model's check
prompt on it. It has been arriving empty on every adoption since the screen was built.

## 4 · Hand-typed expressions can persist now — one call, not five

You flagged this. `/platform-express` takes the whole map:

```
POST /platform-express { item, expressions:{ video, social, posm, activation, incentive } }
  -> { saved:true, item, set, status }
```

Debounce it like `/plan-row` and send the map, **not five per-slot calls**. Five separate saves is not a
tidiness question: each writes a whole copy of the set, so the last response to land wins carrying a
version that predates the other four, and four edits vanish. A key present with an empty value clears
that slot — deleting an expression means it.

It also resolves the set from `item` alone now (you hold the platform's id, not the set's), and the old
`{ id, item, kind, text }` shape still works for a single field losing focus.

---

## What changed underneath, and why it matters to you

### The fifth test was unanswerable

Your keys are `true, ours, tension, elastic, durable`. Mine were `true, ours, elastic, tension, repeat`.

Same five questions, and the fifth had a different key on each side — so every model verdict on *does it
survive three years?* was written under `repeat`, which no row reads. The fifth test silently had no model
column and could never register a disagreement, however far the two readings diverged.

Yours wins: your words are the ones a person answers. `JUDGED` is now keyed and **ordered** to match
`IDEA_TESTS`, so the document prints the five in the order the screen asks them. Anything already stored
under the old key is read through an alias rather than migrated.

### Adopting used to destroy the expressions

`adopt()` rebuilt the item from five empty expression slots and filled them only from `routes`. So:
generate the five, press Adopt, and four of them were gone. The two features were built a round apart and
only the later one wrote to those slots.

Now: stored value first, then any non-empty route, then anything the payload carries. **An empty route can
never blank an expression somebody wrote.** The routes block and the expressions block are two ways into
the same field and neither owns it.

Same rule everywhere in that function — a key the payload omits is *unchanged*, not blanked. That is what
had been emptying `mechanic` on every save.

### The model's reading survives an adopt, and says when it is stale

`judged` used to be destroyed by the next Adopt. It is kept now. Each verdict records the sentence it read,
so when the line is rewritten you get `judged_stale: true` and an open (never blocking) finding:

> *The model's reading of Purity leads to strength was written against an earlier version of the line. It
> is still worth reading, but ask it again before treating it as current.*

The document prints the same note in amber above the five. Kept rather than deleted because a superseded
challenge is still worth reading, and deleting it would be the tool deciding the argument.

### `house: null` used to judge a stranger's platform

`for_house("")` fell through to *every* set and took whichever file sorted first. Your body sends
`house: (this.state.house||{}).id || null` — correct, and on a screen with no house loaded that is `null`.
So `/platform-judge` would write the model's verdicts into an arbitrary brand's platform and answer 200.
Nothing would have looked broken.

Every platform route now resolves the same way — `set` → `house` → the set holding `item` → (reads only)
the most recent — and refuses rather than guessing when it writes.

### The steer is remembered

You keep it in state so the box stays filled between rounds, which is right. State does not survive a
reload, and the steer is the only record of why round four looks nothing like round one. It is stored on
the set and comes back as `steer` on the GET — so `ideaSteer: ip.steer` starts filled after a reload too.

---

## Everything that changed

```
GET  /idea-platform          answers with no arguments; + judged, questions, disagreements,
                             judged_stale, pillar, rtb, rtb_id, caveat, steer, house, resolved_by
POST /idea-platform          keeps expressions / judged / mechanic / pillar / rtb across an adopt;
                             accepts pillar, rtb_id, caveat
POST /platform-express       + expressions:{…} map, one save; resolves by set|house|item
POST /platform-judge         JUDGED keyed + ordered as IDEA_TESTS; refuses an unresolved set
POST /platform-express-draft one save instead of five; refuses an unresolved set
POST /idea-draft             remembers the steer on the set
GET  /platform-docx/{id}     five tests in the screen's order; the stale-reading note
```

`/idea-draft`'s option shape, `/platform-express`'s old single-field shape, and every other route are
unchanged.

---

## Before you send

```bash
python tools/checkfe.py && python tools/contract.py && python tools/test_tools.py
```

18/18 here, 157 routes, no collisions. Your file passes `checkfe` unchanged — none of the five above is a
class it can see, which is the same limit as the `tagList` crash last round.

One note on how these were found. All four of your builds passed at the endpoint level and all four
looked finished. Five defects were sitting in front of them, and every one needed the page open to see:
a dead hydration path, two colours that were the same colour, a copy that drops four fields, and a null
that resolved to a stranger's document. I would not have found any of them by reading the diff.
