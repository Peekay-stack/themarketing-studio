# Handover to Claude Design — everything that changed since your build

**Your build is installed** at `api/frontend/app.dc.html`. `support.js` was byte-identical, so nothing
there moved. The 486KB predecessor is kept as `app.dc.html.bak-20260810-204409`.

All five of your asks are built, plus a new optional layer. **Every endpoint your file calls now exists** —
I re-ran the diff both ways. What remains is the other direction: 24 routes with no screen.

I edited your file in exactly two ways. Both are disclosed in §1 and both are covered by a test.

---

## 1. What I changed inside your file

Nothing else. `tools/test_tools.py` asserts that removing the banners restores your file byte-for-byte.

**`demoStrategy` now defaults to `false`** — the prop default and the `??` fallback.

Your empty states were designed; they should be what a dead server shows. Left on, a partly-failing
server would show someone a fabricated half-finished house indistinguishable from their own work. Flip it
in the tweak panel whenever you're reviewing.

**25 comment banners inserted in the logic**, in your existing style:

```js
  // ===== VIDEO: script writing =====
```

These are split anchors for `tools/partials.py`, which cuts the file into 59 reviewable parts and rejoins
it byte-identically. It works on the banners the file **already had** — no sentinels, no markers to
delete by accident, nothing that changes behaviour. Deeper-indented banners like
`    <!-- ==== STEP: SCRIPTING ==== -->` stay where they are.

Before committing anything that touches the file:

```bash
python tools/checkfe.py
```

That's the check that was missing when I flattened newline escapes and broke eight string literals last
time. It catches unterminated string literals, bracket balance ignoring anything quoted/commented/
templated, `sc-if`/`sc-for`/`div` pairing, duplicate class members, and `bagX()` spread-but-undefined.
Its own tests feed it each defect and require it to report them, so a green run means something.

**I did not split `renderVals()`.** It is 1,059 lines and the obvious next target, but I measured it:
142 locals are set up before the `return {` and **112 are referenced inside it** (`s` alone 263 times).
Extracting a slice breaks those at *runtime*, not parse time — `checkfe` would go green on a broken file.
You can do it safely because you can load the screen; the recipe is in `tools/README.md`. Not urgent:
your four `bagX` methods already solved the growth problem for new work.

---

## 2. Your five asks — all built

### `POST /finding-override` — and it expires

```
POST /finding-override { doc:"house"|"plan", id, finding, reason, who }
POST /finding-override { doc, id, finding, clear:true }
```

Findings now carry `key` and `can_override`; an overridden one carries `overridden:{reason,who,at}`.
`status.blocking` holds only overrides still in force, `status.overridden` counts the rest, and the
finding is **never removed from `findings`** — a document with three overridden blockers reads as one.

An empty reason returns 400. So does a one-word reason.

**Design for this behaviour:** the key hashes `level|layer|detail`, so an override attaches to one exact
sentence. When *"0 of 2 RTBs sourced"* becomes *"1 of 2"*, that is a different key and the finding
arrives **un-overridden**. Somebody who accepted the risk at nothing-sourced has not accepted it at
one-of-two. Please don't cache the override client-side across a refetch — the expiry is the point.

### Upsert on `/plan-row` and `/house-option`

`/plan-row` with `row.id` present updates; without it, adds. `/house-option` takes `option:"<id>"` plus
any of `text`, `note`, `tag`. Both 404 if the row was dropped underneath the edit. `id`, `source` and
`added` are not writable.

**Editing the text re-sources the item to `user`** — which is what makes your amber panel work end to
end: rewriting a model line in your own words clears the unsourced finding, because the claim is now
theirs. Editing only the note or tag leaves `source` alone.

Your client already sends the right shape, so this may need nothing from you.

### `GET /producers/{kind}` · `GET /producers`

Six kinds: `social · video · posm · activation · media · incentive`, each with `label`, `medium`,
`message_required`, `proof_obligation`, `makes[]`, `needs[]`, `statuses[]`.

**`media` reports `message_required: false`.** Your call, and you were right.

### `message` has a source

`trade` is added to the house's medium vocabulary, so all six kinds resolve.

```
GET /execution-options/{plan_id}/{kind}
-> { audiences[], channels[], occasions[], measures[], measures_by_role{}, messages[], producer }
```

`messages` contains only the house's chosen lines **tagged with this kind's medium**. An empty array is a
real answer — the house hasn't written for that medium — and the 400 says so rather than offering the core
line truncated. `measures_by_role` supports the constrain-at-point-of-choice you already do.

### Sales enabler — separate contract, as you argued

```
GET  /trade                             -> { sheets[], channels[], roles{}, levers[], sell_through{}, states[] }
POST /trade-new   { brand, plan, house }
GET  /trade/{id}
POST /sales-channel { id, channel, role, share_now, behaviour, baseline, target, lever,
                      cost_per_unit, payback, leakage, control, residual_risk,
                      sell_through, receives_money, effective_price, owner }
POST /sales-element { id, channel, element, brief, status }
POST /sales-generate { id, channel, element, note }
GET  /sales-prompt/{id}/{channel}?element=
```

**Your channel keys and all 29 element keys are matched exactly** — `trad, wholesale, modern, ecomm,
qcomm, loyalty` — so your rail count and mine can't disagree.

**`/sales-element` works without a sheet id.** Your build posts `{channel, element, brief}` and holds
state locally; an id-less call lands on the most recent sheet, or opens one against the newest plan.
Passing `id` always wins, so move to ids whenever you like and I'll delete the bridge.

Writing a brief promotes `not started → briefed`. Clearing it goes back.

Four things the sheet enforces:

- **"Visibility" is blocking, not a warning.** Also engagement, excitement, awareness, presence,
  mindshare, buzz, activation, push, focus, support, momentum. A behaviour needs a baseline and a target.
- **Primary-only sell-through is always blocking**, and it gates the pitch card: marking `card`, `pitch`
  or `scheme` as `agreed` against a primary-only scheme returns 400.
- **`status.reconciliation`** is the effective-price strip: `points[]` sorted by price, `missing[]` with
  the reason each is unplotted, `collisions[]`, `spread`. A q-comm or e-comm price under traditional
  retail is blocking with the gap named. Nothing is ever interpolated.
- **Channels sort by share of volume descending**, unknown shares last.

Two changes from your six:

**Loyalty is typed `scope: "lever"`, not `"channel"`.** It runs *through* general trade and q-commerce
rather than beside them; given its own room its cost never lands against the behaviour it buys, which is
how loyalty spend escapes measurement. Your tab is unaffected — but a loyalty programme naming no
channels is now blocking, so that tab wants a line of copy saying it's a lever.

**Two channels have no screen: `own_retail` and `home_delivery`.** Heritage is a daily dairy business
with milk booths and subscription. A subscription is one decision honoured for months — the best
retention economics in the route to market — and the skill's own reference says that for a daily
cold-chain category this may be the most valuable channel there is. They're live in the backend and
raised as findings. `outstanding` counts only screened channels so your rail stays honest until you add
them. **This is my main ask back.**

---

## 3. New since your build: the execution envelope is LIVE

It was PROPOSED in the last handover. It is built.

```
POST /execution-new      { plan, kind, audience, channel, occasion, measure, message }
GET  /executions?plan=&kind=   -> { executions[], summary{by_kind, stale, blocked, total} }
GET  /execution/{id}
POST /execution-rebrief  { id }
POST /execution-status   { id, status }      // briefed -> made -> approved -> shipped
POST /execution-produce  { id }
```

**Staleness is value-based, as agreed.** `stale_because[]` gives `{field, col, was, now, detail}` —
*"channel role was 'proof', now 'conversion'"*. `/execution-rebrief` is the one action.

**`/execution-rebrief` can return 409 and you must surface it.** If the plan has moved somewhere the
execution cannot legally be briefed from — a channel switched to `conversion` while it points at a
`proof` measure — there is nothing to re-brief *to*. The 409 carries the reason and the current status.
A 200 there would leave a stale badge that never clears with no way to find out why.

**`/execution-produce` returns 409 with the findings** when anything blocking stands.

Role/measure disagreement is **refused at brief time**, not warned about. The pillar is inherited from
the audience and cannot be chosen.

### The two producers you assumed

```
POST /posm-keyvisual     { brief, execution? } -> { options:[{id,name,desc}], note }
POST /activation-idea    { idea, execution? }  -> { idea, note }
POST /activation-element { element, brief, idea, execution? } -> { brief, note }
```

`/posm-keyvisual` always returns usable routes; `note` says whether they were generated or are the
declared treatment angles, so a quiet degradation isn't mistaken for a considered answer.
`/activation-idea` returns **400 on an empty box** rather than inventing an activation — it sharpens an
idea, it does not supply one. Pass `execution` and all three are grounded in that brief, including the
house's avoid list.

`/activation-idea` was **not** in your list but your file calls it, so it's built.

---

## 4. New: house and plan download, in two modes

```
GET /house-docx/{id}                    GET /plan-docx/{id}
GET /house-docx/{id}?mode=worksheet     GET /plan-docx/{id}?mode=worksheet
```

**`record`** — what was decided, for circulating. All eight layers, each chosen line with its source in
words (*"from the brief"*, *"from the signed library"*, *"written here"*, *"MODEL SUGGESTION — traces to
nothing in the brief or library"*), culture tags so `avoid` reads as an instruction not to do something,
and unchosen options in an **"Also considered, and not chosen"** appendix. A strategy document showing
only the answer can't be argued with.

**`worksheet`** — the same content turned into something to think in. Per layer: **the layer's question**
→ what's chosen → what was rejected (inline, not in an appendix — you need to see it at the moment you're
deciding) → **three ruled rows to write in** → a prompt asking where the new line came from. Plan
worksheets add three blank rows **inside the same table**, so what you write lines up with what's there.

**Both print their own findings.** The export is exactly where the pretence usually happens — blocking
findings stay on screen and a clean-looking Word file goes to the client. So the house document opens
*"6 of 8 layers decided. This is a working document."* and closes *"1 blocking. This house is not
finished."*

**Empty is not zero, in print:** `owner unknown`, `no measure set`, `no date set`, `share unknown`,
`failure not named`, `no occasion named`. In Word there's no tooltip to explain a blank.

### The round-trip caveat — please render this

`GET /houses` and `GET /plans` now return `caveat` and `downloads`. Show the caveat **before** the
start-a-house / start-a-plan action:

```json
{ "headline": "This house lives here, not in the Word file.",
  "points": [ "…4 lines…" ],
  "worksheet": "…" }
```

It says: everything is editable at any time; rewriting a model line in your own words makes it yours and
clears the unsourced flag; you can download as a record or a worksheet; **and the download cannot come
back in.** Word edits have to be re-typed. Better said once up front than discovered by someone who has
spent an afternoon rewriting the file.

Re-import is not built and is honestly limited: a plan re-imports cleanly because its layers are Word
tables, but a house can only ever be *"replace the chosen line, marked `user`"* — a Word file can carry
the chosen text, not which of five options it was or where the evidence came from.

---

## 5. New optional layer: idea platforms

> **Brief → Messaging house → Idea platform → Executions**
> *(the plan decides who, where and when — not the idea)*

**The problem it solves:** six producers were each inventing their own creative idea, so the film, the
shelf strip and the promoter's line would come back looking like three campaigns that share a message.
Nothing could prevent that, because nothing between the strategy and the work held an idea.

**A platform is not a big concept.** The difference is a *mechanic* — a repeatable device that generates
the next execution. *"Celebrate the mothers of India"* is a sentiment; it yields one film and repeats.
*"Every pack carries the name of the dairy that filled it"* is a mechanic; it yields a film, a pack
change, a shelf strip, a promoter who can point at something, and a trade argument about provenance.

**It lives in the Strategy tab, beside the house.** Not Plan — a platform is built from the house's core
message and pillars and has **no plan dependency at all**. Not Execution — that would make it look
per-execution, the exact incoherence it prevents. And a tenth nav item costs more than it's worth.
Strategy reads: the house (what we say and why it's true) → the platform (how we say it).

```
GET  /platforms?house=              -> { sets[], expressions{}, min_media, min_platforms, optional, why }
GET  /platforms-for/{house_id}      -> { set, status, ready, blocked_because, basis }
POST /platform-new       { house, brand }
POST /platform-generate  { id, build_on?, n?, note? }
POST /platform-item      { id, name, idea, mechanic, territory, proof, rtb, why, expressions{} }
POST /platform-item      { id, item, ... }      // edit
POST /platform-item      { id, drop }
POST /platform-express   { id, item, kind, text }
POST /platform-choose    { id, item }
GET  /platform-prompt/{id}?build_on=
```

### The two iteration modes are different buttons

- **More options** — three fresh bets. The prompt is given everything already on the table and required
  to go elsewhere. They must differ on the *bet*: which pillar leads, which proof is dramatised, which
  cultural code, who the protagonist is. Three that differ by adjective are one platform.
- **Build on this** (`build_on: <id>`) — developments of one platform, keeping its idea recognisable:
  sharper mechanic, more media, harder proof. Lineage recorded in `built_from`.

**Neither replaces anything.** A discarded round is often where somebody finds what they actually
wanted. Please don't add a "regenerate" that clears the list.

**Write-your-own is first-class** and should be the first card, as in the house. `source: user` — the
author is the evidence. The machine's value here is the five tests, not the ideas.

### The five tests — draw these

`status.platforms[].tests` gives five structs, each `{ok, detail, …}`, plus `passes` and `of`:

| key | what it checks | level when it fails |
|---|---|---|
| `media` | expressed in ≥3 of 5 media | open |
| `mechanic` | a mechanic, not a sentiment | **blocking** |
| `avoid` | doesn't collide with the house's avoid list | open |
| `proof` | dramatises a **sourced** RTB | **blocking** if it names an unsourced one |
| `neutral` | not film-only | open |

`avoid` is word-overlap, so it is worded as a question — *"may collide with 'Never show milk being
wasted' — check it, this is a hint rather than a verdict."* Please keep that register; a heuristic
presented as a verdict gets ignored, and then the real ones do too.

### Expressions are the input to executions

Each platform carries an expression for `video`, `social`, `posm`, `activation`, `incentive` — one honest
sentence about what the idea *becomes* there. `status.expressions` gives the prompt for each.
**`media` is absent on purpose**: a media plan allocates, it doesn't speak.

An execution then inherits `brief.platform = { id, name, idea, mechanic, expression }`, where
`expression` is **its own kind's line**. Verified: the POSM execution got *"Shelf strip naming the dairy
nearest this shop"* while the incentive execution got *"The retailer can say whose milk this is."*

Show it as a strip on the execution header — the glimpse of the idea, and what the producer works from.

### Optional means flagged, not silent

An execution with no platform **briefs and produces normally** — 0 blocking, `/execution-produce`
returns 200 — with an open finding: *"No idea platform. This will be briefed from the message alone, so
it will not cohere with any other execution… Fine for a one-off; a problem for a campaign."*

If the platform is silent in that medium: *"has nothing written for pos material. Either write its
expression, or accept that the platform does not reach here — an empty expression is an honest answer,
a borrowed one is not."*

Staleness reaches through by name: *"the platform's expression for this medium has been rewritten"* and
*"platform was 'The Named Dairy', now 'Two Facings'"*.

**Empty states to design:** no set at all (`set: null` with `ready` and `blocked_because` — a platform
can't be written before a core message and one pillar are chosen); a set with fewer than three; and a
platform that passes 3 of 5 tests, which is where these will spend most of their life.

---

## 6. What I need from you, in priority order

1. **Wire the four download buttons** — `record` and `worksheet` on both house and plan. Currently
   `grep` for `house-docx|plan-docx` in your file returns **0**, so the whole feature is unreachable.
2. **Render the caveat** from `status.caveat` on the Strategy and Plan index screens.
3. **The idea platform sub-tab** in Strategy, plus the platform strip on the execution header.
4. **Point the override button at `/finding-override`.** It currently writes to client state, which is
   the dismissal rule F#8 forbids wearing a reason box.
5. **Two trade tabs** — `own_retail`, `home_delivery` — and a line of copy on the Loyalty tab saying
   it's a lever that runs through the others.
6. **A live-action shots screen.** Seven routes still have no UI and this survived the last two
   handovers: `/shots`, `/shot-attach`, `/shot-sign`, `/shot-still`, `/shot-recompose`, `/shot-remove`,
   `/composite-upload`. The Compositor works, but the path that gets a **signed** green-screen take into
   a film doesn't exist. `shots.py` returns only signed shots for exactly that reason — the gate is
   currently protecting a door nobody can reach.

---

## 7. Things not to undo

All nine from before still stand. Six more, each of which was a real bug or a real decision:

10. **An override never removes a finding from the list.** Annotated and counted, never hidden.
11. **`/execution-rebrief`'s 409 must be shown.** Swallowing it leaves a permanent stale badge with no
    explanation.
12. **`payback unknown` must look different from a number** on the trade sheet, and never be dressed to
    resemble one.
13. **Never interpolate a missing effective price.** An invented marker makes the whole strip unreadable
    because nobody can tell which are real. Plot nothing and say why.
14. **Primary sell-through is amber, always** — even when everything else on the row is fine.
15. **"More options" and "Build on this" are different buttons.** Collapsing them into one
    "regenerate" destroys the exploration record, which is the main thing this layer is for.

---

## 8. One fragility worth fixing

Line 33 loads SheetJS from a CDN:

```html
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
```

Every other asset is local, and the portal runs from a `.bat` on a laptop — so spreadsheet export
silently stops working offline. Worth vendoring into `api/frontend/`. Not urgent, but confusing the
first time it happens.

---

## 9. Testing

```bash
Start Heritage Studio.bat        # no --reload; restart after any Python change
python tools/checkfe.py          # before every commit that touches app.dc.html
python tools/test_tools.py       # 18 tests: round-trip + the lint's own defects
```

`houses/ plans/ platforms/ trade/ executions/` are all empty on a fresh install, and `demoStrategy` is
now off — so **the empty states are what you'll see on day one.** They're the most important screens
here, and the half-finished states are where these documents will actually live.
