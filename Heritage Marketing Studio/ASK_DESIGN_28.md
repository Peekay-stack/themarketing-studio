# Ask Design — round 28

**Base:** `app.dc.html` in the attached zip, sha256 `447cc147…4153cdd60`. This is byte-identical to the
file you returned in round 27 and confirmed synced, so if your working copy is untouched since then you
can work in place — the zip is only here so there is no ambiguity about which file is the base. **I have
made no frontend edits this round.** Every change below is yours.

**Size:** small. One change matters; three are consequences of it. There is no new screen in this round.

---

## What moved on the backend

Media planning stopped being an Execution producer and became its own top-level tab. That was a
deliberate landing of a question that had been parked since 20 Aug, and the reasoning is on the wire
rather than in a document — `GET /producers` now returns `retired`, and the `media` entry there says why
in full.

The short version: a producer makes one thing that says something. A media plan is orthogonal to that —
it decides how much each producer *gets*. The tell was already in the frontend: this screen has to
special-case `media` in six places to make it fit beside Social, starting with skipping the message load
and exempting it from the proof requirement. `message_required: false` was the first sign. A producer
that cannot carry a message is not one.

Retirement was done **non-destructively**, the same way `strategy.H_LAYERS` keeps the retired medium
layer:

- `MANIFEST.media` still exists, now carrying `retired: true`. Executions already stored against it
  still load and still resolve their label — verified against a real stored one (`82a9a272f5`).
- `execution.live_kinds()` is the offered set, served as `/producers`.`live`.
- `execution.RETIRED_KINDS.media` records the destination and the reason.

---

## 1. The change that matters — `X_TABS` still shows the retired sub-tab

`app.dc.html:11756`:

```js
X_TABS = [
  ['social','Social','social'],
  ['posm','POS material','posm'],
  ['onground','Onground activation','activation'],
  ['media','Media planning','media'],      // ← retired on the server, still on screen
];
```

Right now the server has retired it and the screen still offers it. That is two homes for one decision,
which is the exact failure the retirement exists to prevent — and it is worse than either state alone,
because someone can still build a media plan in a place that no longer owns media plans.

**Filter it, don't rebuild it.** You already have the pattern, at line 13884:

```js
const H_LIVE = liveIds ? this.H_LAYERS.filter(([k]) => liveIds.indexOf(k) >= 0) : this.H_LAYERS;
```

Do the same thing here — keep `X_TABS` as the local table it is, and filter it against the live kinds
from `/producers`:

```js
const liveKinds = (this.producers?.live || []).map(p => p.kind);
const X_LIVE = liveKinds.length ? this.X_TABS.filter(([,,kind]) => liveKinds.indexOf(kind) >= 0)
                                : this.X_TABS;
```

Then read `X_LIVE` at the three sites that use `X_TABS` today: `xKindFor` (12274), `xTabs` (13242), and
the initial-tab pick.

Two reasons to filter rather than build from `live`:

- **`live` is not the tab strip.** The entry's third element is the producer `kind`, and it does not
  always equal the tab slug — `['onground', …, 'activation']`. Three live kinds also have no entry here
  at all, on purpose: `video` has its own studio, `incentive` routes to the trade tab, `pr` has its own
  home. Building the strip from `live` would put all three into the Execution envelope.
- **Order and labels are yours.** They are a screen decision, not a server one. The server's job is only
  to say what is still offered.

The `liveKinds.length ?` guard matters: on a failed or slow `/producers` the fallback must be the full
local table, never an empty strip. Same shape as the `liveIds ?` guard on `H_LIVE`.

## 2. Tell the reader where it went

Someone who used the Media planning sub-tab last week will look for it. Finding nothing is worse than
finding a sentence.

`/producers`.`retired` is a map of `kind → { label, went, why, also }`, written to be rendered. One
line where the tab used to sit, or a note at the foot of the strip, is enough:

> **Media plan** moved to the Media tab — its own top-level screen, not a producer. *Why →*

Reuse whatever disclosure you already use for `RETIRED_TESTS` / the retired house layer; this is the
same shape and the same purpose. `why` and `also` are long-form and can hide behind the toggle.

## 3. `EXPRESSION_GO.media` becomes a dead link

Line 11998:

```js
incentive:['sales','Take it to the trade'], media:['media','Take it to the media plan'] };
```

That first element is a tab slug, and once §1 lands the `media` slug has nowhere to go. **The row itself
stays** — `media` is still a live platform *expression* on the server (`media.EXPRESSIONS`), and "what
the platform demands of the schedule — a shape, not a spend" is a real line to write at platform stage.
Only its hand-off target is gone.

The honest interim: keep the row, drop the button, and say why in its place — *"this hands to the Media
tab, which is being built."* Please do **not** point it at a producer to keep the button alive; a button
that goes to the wrong screen is the failure we just spent a round removing. I will give you the real
target with the Media tab.

## 4. The six special-cases can go — but not the render path

With `media` off the strip, the branches that exist only to make it fit are dead code:

- `12357` — `if (kind === 'media' || kind === 'idea') return;` (skips the message load)
- `12395` — `&& kind !== 'media'` (exempts it from the proof requirement)
- `13044` — `const isMedia = kind === 'media';`
- `13317` — `xIsMedia: tab === 'media'`
- `13236` — the `media` envelope copy
- `12690`–onward — the `// ---------- media planning ----------` panel, and its template at `4731`–`4767`

**Your call on how far to go, and I'd suggest not far.** Deleting them is tempting and I don't think it
is right yet: a media execution stored last week must still open and still render, which is the whole
point of keeping `MANIFEST.media`. If any of those branches is on the path that renders a *stored* one,
leaving it costs nothing but a few unreachable lines, and removing it silently destroys access to real
saved work. If you can tell cleanly which are reachable only from the strip, drop those and keep the
rest with a one-line comment pointing at `RETIRED_KINDS`. If you can't tell cheaply, leave all six — I
would rather carry dead code for a round than lose a stored plan.

The safest check: open a stored media execution from history **after** §1 lands, and confirm it still
renders with its label. If it does, whatever you removed was genuinely unreachable.

## 5. Do not touch `FORMATS.media`

Line 6458:

```js
{ id:'media', tag:'ME', name:'Media', tint:'#D6DEEC', fg:'#2E5EA6', desc:'Channel mix, reach & frequency goals, budgets and flighting.' },
```

This is the **document generator**, not the Execution producer — a one-off media brief document, same
family as the IMC Brief and the Packaging brief. It is unaffected and stays exactly as it is. Same for
its two dependents: `7385` (`businessObjective`) and `9924` (`builderHasImport`).

I'm flagging it because the word `media` now appears in three unrelated namespaces in this file —
producer kind, platform expression, document format — and only the first is retired. Worth a comment
wherever you touch one, so the next round doesn't have to re-derive which is which.

---

## New endpoints (nothing to build against them this round)

Listed so you know they exist; the screens that consume them are a later round.

| Endpoint | Returns |
|---|---|
| `GET /producers` | now also `live`, `retired`, `statuses` |
| `GET /media-status` | what the media desk can and cannot do yet |
| `GET /media-strategy?plan=<id>` | the derived strategy — read-only, `derived: true` on the payload |

`/media-strategy` is worth a look even though it isn't yours yet, because it sets the constraint the
Media tab will be built under: **it stores nothing.** Roles, sides and the brand/activation split are
decisions the *plan* already made, and the media screen reads them so there is one place they are true.
When you build that screen, `derived: true` means it must not offer an edit — there will be a route back
to the Plan layer instead. The tab owns weight, money, flighting and the calendar; it does not own any
question the plan already asked.

Also on the wire now, and relevant to the Plan screen you already have: `plan.BRAND_SHARE_BASIS`, the
citation behind the default 60/40 (Binet & Field, ~1,000 IPA cases) together with the dispute against it
(Ehrenberg-Bass). It ships in `/media-strategy`.`split`.`basis_of_default` and in `/plan-status`. And
`balance` now carries a **`declared`** flag — a 60 someone chose and a 60 nobody touched used to be the
same record, which is the kind of thing that reads as a decision on a screen when it isn't one. If the
Plan screen says "60% brand declared" anywhere, it should now only say *declared* when `declared` is
true.

---

## Not this round

The **Media tab itself** — strategy, competitive intelligence, weight, flighting, the campaign manager,
the calendar. I'm building the backend for it now, starting with competitive intelligence. You'll get it
as a proper screen ask with the shapes settled, not as a sketch.

## What to send back

`app.dc.html` and your handover note. Please call out anything in §4 you decided to leave, and why — the
reachability question there is a real judgement call and I'd rather have your reasoning than guess at it
next round.
