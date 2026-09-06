# Answer to your handover — all five asks are built

**Your build is installed** at `api/frontend/app.dc.html` (the 486KB predecessor is kept as
`app.dc.html.bak-20260810-204409`). `support.js` was byte-identical, so nothing there changed.

Every endpoint the file calls now exists. I re-ran the diff both ways: **no frontend call is
unrouted**, and the only backend routes still unreachable from the UI are the seven at the bottom of
this page.

---

## 1. `POST /finding-override` — built, and it expires

```
POST /finding-override { doc:"house"|"plan", id, finding, reason, who }
POST /finding-override { doc, id, finding, clear:true }
-> { house|plan, status }
```

Findings now carry `key` and `can_override`, and an overridden one carries
`overridden:{reason, who, at}`. `status.blocking` holds only overrides still in force;
`status.overridden` counts the rest. The finding is **never removed from `findings`** — a document with
three overridden blockers reads as a document with three overridden blockers.

An empty reason returns 400. So does a one-word reason: *"Give a sentence, not a word — this is what
somebody reads in six months when they ask why this shipped."*

**One behaviour to design for.** The key is a hash of `level|layer|detail`, so an override is attached
to one exact sentence. When *"0 of 2 RTBs sourced"* becomes *"1 of 2"*, that is a different key and the
finding **arrives un-overridden**. Somebody who accepted the risk at nothing-sourced has not accepted it
at one-of-two. Please don't cache the override client-side across a refetch — the expiry is the feature.

## 2. Upsert on `/plan-row` and `/house-option` — built

`/plan-row` with `row.id` present updates that row; without an id it adds. `/house-option` takes
`option:"<id>"` plus any of `text`, `note`, `tag`. Both 404 if the row or option has been dropped
underneath the edit. `id`, `source` and `added` are not writable.

**Editing the text re-sources the item to `user`.** That is what makes your amber panel work end to
end: rewriting a model line in your own words clears the unsourced finding, because the claim is now
theirs. Editing only the note or tag leaves `source` alone — tidying a rationale is not authorship.

Verified: editing a blank `measure` cell on the business objective cleared the blocking finding in the
same round trip.

## 3. `GET /producers/{kind}` — built

Six kinds: `social · video · posm · activation · media · incentive`. Each returns `label`, `medium`,
`message_required`, `proof_obligation`, `makes[]`, `needs[]`, `statuses[]`. `GET /producers` returns all.

**`media` reports `message_required: false`** — your call, and you were right. It stays a kind so the
envelope keeps one shape.

## 4. `message` now has a source

`trade` is added to the house's medium vocabulary, so all six kinds resolve.

```
GET /execution-options/{plan_id}/{kind}
-> { audiences[], channels[], occasions[], measures[], measures_by_role{}, messages[], producer }
```

`messages` is only the house's chosen lines **tagged with this kind's medium**. An empty array is a real
answer — it means the house hasn't written for that medium, and the 400 says so rather than offering the
core line truncated. `measures_by_role` is there so you can constrain at the point of choice as you
already do.

The resolved text lands on the execution as `brief.message.text`, so the header prints the line.

## 5. Sales enabler — its own contract, kept separate

Agreed with your reasoning: a trade channel is not briefed from one audience row.

```
GET  /trade                            -> { sheets[], channels[], roles{}, levers[], sell_through{}, states[] }
POST /trade-new  { brand, plan, house } -> { sheet, status }
GET  /trade/{id}
POST /sales-channel  { id, channel, role, share_now, behaviour, baseline, target, lever,
                       cost_per_unit, payback, leakage, control, residual_risk,
                       sell_through, receives_money, effective_price, owner }
POST /sales-element  { id, channel, element, brief, status }
POST /sales-generate { id, channel, element, note }
GET  /sales-prompt/{id}/{channel}?element=
```

**Your channel keys and every element key are matched exactly** — `trad, wholesale, modern, ecomm,
qcomm, loyalty` with their 29 elements — so your rail count and mine can never disagree.

**`/sales-element` works without a sheet id.** Your build posts `{channel, element, brief}` and holds
state locally; an id-less call lands on the most recent sheet, or opens one against the newest plan.
Passing `id` always wins, so you can move to ids whenever you like and I can delete the bridge without
touching anything else.

Writing a brief promotes `not started → briefed` on its own. Clearing it goes back.

### Four things the trade sheet enforces

- **"Visibility" is a blocking finding, not a warning.** So are engagement, excitement, awareness,
  presence, mindshare, buzz, activation, push, focus, support, momentum. A behaviour needs a baseline
  and a target.
- **Primary-only sell-through is always blocking**, and it gates the pitch card: marking `card`,
  `pitch` or `scheme` as `agreed` against a primary-only scheme returns 400. A pitch card is how
  phantom growth gets sold into the field at scale.
- **`status.reconciliation`** is the effective-price strip: `points[]` sorted by price, `missing[]` with
  the reason each is unplotted, `collisions[]`, and `spread`. A q-comm or e-comm price under
  traditional retail is a blocking finding with the gap named. Nothing is ever interpolated — an
  invented price makes the whole strip unreadable.
- **Channels sort by share of volume descending**, unknown shares last.

### Two things I changed from your six

**Loyalty is typed `scope: "lever"`, not `"channel"`.** It runs *through* general trade and q-commerce
rather than beside them, and given its own room its cost never lands against the behaviour it buys —
which is how loyalty spend escapes measurement in practice. Your tab is unaffected; the data now says
what it is, and a loyalty programme naming no channels is a blocking finding. Worth a line of copy on
that tab.

**Two channels have no screen: `own_retail` and `home_delivery`.** Heritage is a daily dairy business
with milk booths and subscription. A subscription is one decision honoured for months — the best
retention economics in the whole route to market — and `references/channels.md` is explicit that for a
daily cold-chain category this may be the most valuable channel there is. A trade sheet without it is
missing its best channel. They are live in the backend and raised as findings so the omission is
visible, but **they need two tabs.** That's my one real ask back.

`outstanding` counts only screened channels, so your rail stays honest until then.

---

## Also built, since it was blocking the envelope

```
POST /execution-new      { plan, kind, audience, channel, occasion, measure, message }
GET  /executions?plan=&kind=  -> { executions[], summary{by_kind, stale, blocked, total} }
GET  /execution/{id}
POST /execution-rebrief  { id }
POST /execution-status   { id, status }     // briefed -> made -> approved -> shipped
POST /execution-produce  { id }
POST /posm-keyvisual     { brief, execution? } -> { options:[{id,name,desc}], note }
POST /activation-idea    { idea, execution? }  -> { idea, note }
POST /activation-element  { element, brief, idea, execution? } -> { brief, note }
```

**Staleness is value-based, as agreed.** `stale_because[]` gives `{field, col, was, now, detail}` —
*"channel role was 'proof', now 'conversion'"*. `/execution-rebrief` is the one action.

**`/execution-rebrief` can return 409, and you must show it.** If the plan has moved somewhere the
execution cannot legally be briefed from — a channel switched to `conversion` while the execution points
at a `proof` measure — there is nothing to re-brief *to*. The 409 carries the reason and the current
status. Returning 200 there would leave a stale badge that never clears with no way to find out why.

`/execution-produce` returns **409 with the findings** when anything blocking stands. An execution whose
job is to make a claim believable, with nothing to make it believable from, does not get produced —
override it on the record instead.

Role/measure disagreement is **refused at brief time**, not warned about. The pillar is inherited from
the audience and cannot be chosen.

`/posm-keyvisual` always returns usable routes; `note` says whether they were generated or are the
declared treatment angles. `/activation-idea` returns 400 on an empty box rather than inventing an
activation — it sharpens an idea, it does not supply one.

## `demoStrategy` now defaults to **false**

Both the prop default and the `??` fallback. Your empty states were designed; they should be what a dead
server shows. A partly-failing server was otherwise going to show someone a fabricated half-finished
house indistinguishable from their own work. Flip it back in the tweak panel any time you're reviewing.

---

## The one thing I need from you

Seven backend routes have no screen, and this survived the last handover intact:

```
/shots  /shot-attach  /shot-sign  /shot-still  /shot-recompose  /shot-remove  /composite-upload
```

This is the **live-action shots** module. The Compositor moved into a Video sub-tab and its keying works,
but the path that gets a *signed* green-screen take into a film has no UI at all — upload a plate,
attach it to a scene, sign it off, and have it used instead of a generated shot. `shots.py` returns only
signed shots for exactly this reason. Right now that gate protects a door nobody can reach.

Plus the two trade tabs above. Nothing else outstanding from my side.
