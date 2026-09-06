# Handover to Claude Code — the spine, finished

**File:** `app.dc.html` (drop over `api/frontend/app.dc.html`)
**This round:** the idea platform, the home toolkit, two more trade channels, the message field wired,
the two 409s surfaced, and a live-action shot list.
**Not touched:** the video pipeline, the compositor's keying, social generation, campaigns, memory,
briefs. Everything that moved in the last round is where it was.

---

## What is in the file now

| Nav item | Screens | State |
|---|---|---|
| Strategy | `strategy`, `house` | LIVE contracts, wired |
| Plan | `plans`, `plan` | LIVE contracts, wired |
| Strategy | `idea` — the idea platform | new screen, local until `/idea-platform` exists |
| Execution | `exec` — four producers, two selectable inputs | producers as before |
| Sales enabler | `sales` — **eight** sub-tabs | no contract yet |
| Video | `video` — Film / **Live action** / Compositor | shots screen new, seven endpoints proposed |

---

## A. Idea platform — a screen beside the messaging house

`Strategy → Idea platform`. It is **not** under Execution: a platform points at the house, not at one
audience row, so it sits as a sibling screen (`screen: 'idea'`) reached from a two-tab bar on both
Strategy screens — Messaging house · Idea platform. Execution is back to four producer sub-tabs.

**It is optional, and says so.** A band at the top of the screen offers *Skip the platform*; once
skipped it states that producers are briefed from the plan alone, hides the three panels, and every
producer's input picker turns the platform off and stops asking. `idea.skipped` is the flag.

**Step 1 — the platform.** A name and one sentence. Underneath, the chosen core message is printed
verbatim as *standing on*; when no core is chosen it says so in amber rather than showing an empty
field. *Adopt this platform* posts to `/idea-platform`.

**Step 2 — five tests.** Each is a badge you click through `untested → holds → fails`, and any verdict
that is not `untested` opens a reason field. The tests are: is it true, could a competitor sign it,
is there a tension in it, does every channel get something to do, does it survive three years.

- **The elasticity test is derived, not clicked** — it reads the routes below (`≥4 of 5` holds, `0`
  untested, anything between fails) and its hint prints `n of 5 routes written`. Clicking it says so.
- The summary line leads with failures: *3 of 5 hold, 1 fails* in red, untested in amber, and it says
  a failing platform may still run **provided the reason is written down**. Same rule as F#8.

**Step 3 — expression routes.** One card per producer — Social, POS material, Onground, Media, Trade
— each with what the platform has to become there and a *Take it to…* link that switches sub-tab
(Trade jumps to Sales enabler). Routes are what the elasticity test reads, so writing them is not
optional decoration.

## A2. What each producer is given

Every producer sub-tab (Social, POS material, Onground, Media planning) now opens with a **What this
producer is given** picker: two independently selectable cards, *the plan brief* and *the idea
platform*. Either, both, or neither.

- Turning the brief off hides the six-field envelope; turning it on restores it, *Choose a plan* and all.
- Turning the platform on renders a card with its name, its sentence, and **that producer's expression
  route** — or an amber note when no route was written for it.
- A line under the pair names the combination in words, amber whenever only one or neither is on.
- The platform card cannot be switched on when there is no platform, or when it is skipped in Strategy.
- The **Video → Film** tab gets the same platform toggle beside its existing *start from a brief* band,
  so the film takes the same two inputs as the four producers.

State lives in `xInputs`; `ideaUsable()` is the single guard (`written && not skipped`).

## B. Home — the toolkit is the spine

Four numbered cards in the order the work happens: **01 Brief writing → 02 Comm strategy → 03 IMC
plan → 04 Execution** (the only card with the orange border, since it is where everything lands).
Social, POS, onground and media lost their top-level cards — they are rooms inside Execution now and
are named on its card instead. A compact second row holds what is not part of the sequence: Sales
enabler, Video studio, Campaign analysis, Memory.

## C. Sales enabler — seven channels and a lever

Added **Own retail** (the parlour: format, exclusive range, counter script, in-parlour merchandising,
repeat mechanic, catchment) and **Home delivery** (subscription proposition, route and agent
economics, first-week onboarding, missed-delivery recovery, basket growth, cancellation and reason
capture). Both follow the existing shape — six elements, each a brief with `not started → briefed →
agreed`.

**Loyalty is now framed as a lever, not a channel.** It keeps its tab and its five elements, but it
sits last and carries an amber band saying it has no shopper of its own, that it runs through the
seven above, and that it must be briefed against a named behaviour in a named channel. The screen's
intro copy says seven shops, not eight. The right rail counts all eight tabs, driven off `SE_TABS`.

## D. `message` now has a source

The envelope's *What it must say* select is fed by **`GET /execution-options/{plan}/{kind}`**, fetched
when the plan or the sub-tab changes and cached per `plan/kind`. Expected shape:

```json
{ "options": [ { "id": "m3", "text": "…", "medium": "posm" } ] }
```

`text` (or `label`) and `medium` are both used — the option renders as `medium — text`. On choosing a
line, `createExecution` sends **`message_text`** alongside `message`, so the brief header prints the
sentence rather than an id; the server's own `message_text` wins when it returns one.

Three states, all distinguishable: loading, *the house has no by-medium line for this kind yet*
(amber border, and copy pointing at the medium layer — nothing is ever typed into an execution), and
a populated list. `media` and `idea` are skipped; media has no message by design.

## E. The two 409s

`/execution-produce` and `/execution-recompose` both answer 409 when the execution no longer agrees
with the plan. A 409 is a decision, not a failure, so it renders as a **red band that stays on screen**
— never a toast — carrying:

- the server's `detail` verbatim (with a fallback line when the body is empty),
- `data.fields[]` if present, one per line, as strings or `{field, detail}`,
- the code and which producer refused, as a chip,
- two actions: *Recompose from the plan* and *Re-brief it by hand*, plus Dismiss.

Conflicts are held per sub-tab and cleared on the next successful produce. **`/execution-recompose`
is also now callable** — from the band and from the stale panel, next to *Re-brief against the new
values*. It expects `{ id }` and `{ execution }` back.

## F. Live action — the shot list

`Video → Live action`, between Film and Compositor. The only screen in the studio that generates
nothing: it plans a real shoot, holds what came back, and hands the selects next door.

An editable table — shot name, what happens, talent, location, length, state — with per-row actions
(reference, log a take, select this take, drop) and a state chip you click through
`planned → briefed → shot → selected`. Empty cells say what their emptiness means (*nobody cast*, *no
location*). Planning reads the approved script when there is one and the idea platform's sentence
when there is not, so the fallback list is the platform's five beats rather than generic coverage.

### Seven endpoints it wants

| Endpoint | Body | Back | Fallback today |
|---|---|---|---|
| `POST /shots-plan` | `{execution, script[], idea}` | `{shots[]}` | derived locally from script or platform |
| `POST /shot-row` | `{shot}` | — (upsert on `shot.id`) | edits held in state |
| `POST /shot-reference` | `{id, action, slug}` | `{url}` | marks the row *reference held* |
| `POST /shot-take` | `{id, take}` | `{take}` | increments a local take number |
| `POST /shot-select` | `{id, take}` | — | sets the row to `selected` |
| `POST /shots-callsheet` | `{shots[], idea}` | .docx blob | client-side Word via `wordBlob` |
| `POST /shots-handoff` | `{shots:[id]}` | — | refuses when nothing is selected |

Shot shape: `{id, no, slug, action, talent, location, length, state, take, ref}`.

---

## What I still need from you

### 1. Contracts that do not exist yet

| Endpoint | Why |
|---|---|
| `GET /execution-options/{plan}/{kind}` | **The one that unblocks a real field.** Until it answers, the message select shows the amber empty state on every kind. |
| `POST /idea-platform` | `{house, plan, name, line, tests{verdict,note}, routes{}}`. Held in client state without it, so the five tests are re-answered every session — the same dismissal problem the findings had. `skipped` wants to persist too: it is a decision, not a UI preference. |
| 409 bodies with `detail` | Both producers already refuse; the band is only as good as the sentence in `detail`. `fields[]` is optional and rendered if present. |
| `/execution-recompose` | Now reachable from two places in the UI. If it is not going to exist, say so and I will drop both buttons rather than leave them lying. |
| The seven shot endpoints above | Nothing breaks without them; everything is held locally and the call sheet still downloads. |
| Sales enabler contract | Unchanged ask from last time, now eight channels. Per channel: role, owner, `elements[{key, brief, status}]`. |

### 2. Decisions I made that are yours to overrule

- **The platform is a screen, not an execution kind.** It never calls `/execution-new`, needs no
  producer manifest and no envelope. Execution opens on Social as before.
- **Both producer inputs are independent, and neither is implied.** A producer with nothing selected
  is allowed — it says so in amber rather than silently composing from whatever is in state.
- **Loyalty stayed a tab** rather than becoming a field on the other seven. Framing it as a lever in
  copy was the cheaper fix, and it keeps its five elements addressable.
- **Own retail and home delivery are trade channels, not a new screen.** They buy differently from a
  kirana but they buy in the same shape, and the right rail counts them with the rest.

### 3. Still open from earlier

The house `medium` vocabulary against the execution kinds. Whichever way `trade` and `media` land,
the UI does not care — but `/execution-options/{plan}/{kind}` now takes `kind` from `X_TABS`, so the
kinds it must answer for are `social`, `posm`, `activation` and `trade`. It is never called for
`media` or `idea`.

---

## Notes on the build

- **`demoStrategy`** is unchanged: a tweak prop, default on, seeding one half-finished house and plan
  when `/houses` and `/plans` are both unreachable. Real data always wins.
- **`componentDidUpdate` is new on the class** and does one thing — fetch the message options when
  the plan or sub-tab changes. If you add another, merge rather than replace it.
- **The idea platform is a top-level `sc-if isIdeaScreen` block**, a sibling of the strategy index —
  it was briefly nested inside it and the whole branch was dropped at parse. Keep it at top level.
- **The Social Studio markup still lives inside the `xIsSocial` branch**, and `isVideo` / `isShots` /
  `isComposite` are all derived from `s.vTab`. Three video sub-screens now, each rendering its own
  copy of the tab bar — worth a grep after you compose partials.
