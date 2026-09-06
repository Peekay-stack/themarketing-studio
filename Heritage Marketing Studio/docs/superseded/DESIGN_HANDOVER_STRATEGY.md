# Handover to Claude Design — the strategy spine and the first execution

**File to edit:** `api/frontend/app.dc.html`
**Do not change:** anything in `api/*.py`. Contracts marked **LIVE** below are implemented and
tested. Contracts marked **PROPOSED** are not built yet — tell me if the shape is wrong and I will
change the backend before you build against it, the same way you did with `/composite`.

---

## What this is for

The portal is getting the strategy layer it has never had. The spine, end to end:

> **Brief → Comm strategy (Messaging house) → IMC plan → Executions**
> *social · video · POSM · sales & trade incentives · activations · media plan*

Two new authored documents (house, plan), and then a **single shared shape for every execution** so
we build the envelope once rather than six bespoke screens.

The house and plan are **skill-led**, exactly as the IMC Brief already is: the reasoning lives in a
vendored skill (`api/strategy_skill/`, `api/plan_skill/`) that the server runs. The client never
writes strategy prompts — it asks for a layer and renders what comes back.

---

## Read this first: three things that shape every screen here

**1. One layer at a time, and choosing is the product.** Neither document is generated in one go.
Each layer offers several genuinely different options, a person chooses, and the layers below are
written *against that choice*. If the UI makes "generate everything" easy, the tool stops working —
because nothing was ever decided, only written. The generate action is **per layer** and the server
refuses out-of-order calls.

**2. Findings are the point, not decoration.** Both documents return a `findings` array with a
`level`. Some are `blocking`. These are not validation errors to tuck into a toast — they are the
substance of the review. The most important one in the whole system:

> *"POSM is given proof work against the functional pillar, which has 0 of 2 reasons-to-believe
> sourced. There is nothing to prove with. Move it to reach, or hold it until the facts exist."*

**3. Staleness crosses documents.** Change a pillar in the house and every plan layer written
against it goes stale, by name. This is the one thing chat cannot do and the reason these live in
the portal. Show it clearly — it is the payoff.

---

## A. Comm strategy — the messaging house  ·  **LIVE**

Eight layers, in order. Each holds a list of text `options`; `chosen` is a list of option ids.

```
core -> emotional | functional -> rtb_emotional | rtb_functional
     -> proof -> culture -> medium
```

```
GET  /houses                      -> { houses[], layers[], culture_kinds[], media[] }
POST /house-new    { brand, brief } -> { house, status }
GET  /house/{id}                  -> { house, status }
POST /house-generate { id, layer, note, replace } -> { house, status }   // 400 if out of order
POST /house-choose  { id, layer, options[] }      -> { house, status }
POST /house-option  { id, layer, text, note, tag } -> add by hand
POST /house-option  { id, layer, drop }            -> remove
GET  /house-prompt/{id}/{layer}   -> { prompt }    // exactly what would be sent
```

`status.layers[]` gives per layer: `options`, `chosen`, `ready`, `blocked_because`, `stale`, `asks`.

**What the screen needs**

- A layer rail showing the eight layers with their state: how many options, how many chosen,
  `waiting on a parent`, or `stale`. This rail is the document's table of contents and its progress.
- The working layer as **option cards**: the text, a one-line rationale (`note`), a `source` tag, and
  a tag for culture/medium layers. Multi-select — more than one option can be chosen.
- `source` is `brief | library | user | model`. **A chosen `model` item is flagged in findings as
  unsourced.** Design that as a state a person resolves, not a warning they dismiss.
- **Add-your-own is a first-class action, not a fallback.** A strategist will type their own line, and
  a hand-written option counts as sourced because they are the evidence.
- `GET /house-prompt` exists so the prompt is inspectable. Put it behind a quiet "what was sent"
  affordance. A strategy tool that cannot show its own instructions is asking to be trusted rather
  than checked.
- The **culture layer** has six kinds (`occasion, ritual, code, idiom, iconography, avoid`) carried on
  each option's `tag`. `avoid` needs distinguishing — it is an instruction *not* to do something.

**The one-page house diagram already exists and is approved.** `api/strategy_skill/references/`
holds `diagram.md` (the spec) and `example-summary.html` (the built, signed-off artefact). Reuse that
layout for any in-portal summary or export. Do not redesign it.

---

## B. IMC plan  ·  **LIVE**

Seven layers, and they are **tables, not prose**. `status.layers[].cols` gives the columns.

| Layer | Columns |
|---|---|
| `objectives` | level · statement · measure · by_when |
| `audiences` | audience · rank · believes_now · pillar |
| `channels` | channel · role · job · measure · side · share · owner · lead |
| `balance` | *(a number, not rows)* |
| `phases` | phase · window · occasion · channels · hands_over |
| `measures` | role · leading · lagging · would_tell_us_it_failed |
| `governance` | who · speaks_on · boundary · decides_changes |

```
GET  /plans                       -> { plans[], layers[], roles{}, sides[], default_brand_share }
POST /plan-new  { brand, house }  -> { plan, status }
GET  /plan/{id}                   -> { plan, status }
POST /plan-generate { id, layer, note, replace } -> 400 if out of order
POST /plan-row  { id, layer, row{...} }  -> add one row
POST /plan-row  { id, layer, drop }      -> remove one row
POST /plan-balance { id, brand_share, reason, basis } -> basis is "year" | "window"
GET  /plan-prompt/{id}/{layer}    -> { prompt }
```

**A plan is bound to a house** (`plan.house`). Without one it still works, but a finding says the
proof gate cannot run — surface that, because it means any channel could be handed proof work it
cannot deliver.

**What the screen needs**

- **Editable tables**, one per layer, with the columns above. Add-a-row and delete-a-row inline.
- **`channels` is the most important table.** `role` is one of `reach · proof · conversion ·
  advocacy` — `status.roles` carries the definition of each, worth showing on hover. Exactly one row
  has `lead`. Findings will tell you when a role and its measure disagree; show that **in the row**,
  not only in a list.
- **The balance needs two bars, not one.** `status.balance` gives `brand_share` (declared), `actual`
  (`{brand, activation, basis}`), `default` (60) and `reason`. Draw declared above actual on the same
  scale, print the delta when they differ, and print the `basis` string verbatim — it may say
  *"spend unknown — computed on channel count"*, which is a materially weaker claim than a weighted
  one and must not be dressed up as equal.
- **The split is the author's to change.** A slider or a number, freely editable. Moving off 60 raises
  a finding asking for one sentence of reason — a prompt, never a block. `basis` matters: *70%
  activation during exam season* and *70% annually* are different decisions.
- `status.house_evidence` gives `{emotional: [sourced, total], functional: [sourced, total]}`. Show
  it near the channels table, because it is what decides which channels may be given proof work.

---

## C. The execution envelope  ·  **PROPOSED — your view wanted before I build**

Six executions are coming: **social, video, POSM, sales & trade incentives, activations, media
plan**. I do not want six bespoke engines, and I do not think you want six bespoke screens.

My proposal: every execution is briefed by the **same six fields**, taken from the plan.

```
POST /execution-new
{
  plan:      "<plan id>",
  kind:      "social" | "video" | "posm" | "incentive" | "activation" | "media",
  audience:  "<row id from plan.audiences>",     // who
  pillar:    "emotional" | "functional",         // inherited from that audience
  channel:   "<row id from plan.channels>",      // where, and its role
  occasion:  "<phase row id>",                   // when
  measure:   "<from plan.measures for that role>"
}
-> { execution: { id, kind, brief:{...}, status:"briefed", artefacts:[], stale:false } }

GET  /executions?plan=&kind=     -> { executions[], summary{} }
POST /execution-produce { id }   -> hands off to that kind's producer
POST /execution-status  { id, status }  // briefed -> made -> approved -> shipped
```

Three consequences worth confirming:

1. **One screen pattern for all six.** Kind-specific UI is the *producer* panel only; the brief
   header, status and staleness are shared. Video's existing pipeline gets retrofitted into this
   envelope rather than rewritten.
2. **Executions inherit staleness.** Change the pillar in the house and every execution carrying it
   flags — the same mechanism as the plan.
3. **The brief is a reference, not free text.** An execution points at plan rows by id, so it cannot
   drift from the plan. If it needs a field the plan does not have, that is a gap in the plan.

→ **Ask:** is that six-field brief the right envelope for a screen you would actually want to build
six times? If a producer needs something else — a format list, a budget, a territory — say so now and
I will add it to the contract before you start.

---

## D. The first slice  ·  **social**

Rather than build six, build **one** end to end and let the pattern prove itself.

Social is the right first slice: it is cheap, the Social Studio already exists, and it needs no
render budget to demonstrate. The path to show working:

> plan → brief a social execution from it → produce posts → status back on the plan

What that needs from you: the execution header (the six fields, read-only, pointing at plan rows),
the producer panel (largely the existing Social Studio), a status control, and the stale badge.

If that reads well, the other five are the same screen with a different producer.

---

## E. Enabling work I am doing in parallel

`app.dc.html` is 486KB / ~6,000 lines with a 233-key bag. Adding four sections makes every later one
slower, and I have already shipped one syntax error that no check caught.

So before these screens land I am:

- **splitting the bag into per-area methods** — `return { ...this.bagCore(s), ...this.bagStrategy(s) }`
- adding **sentinel-delimited partials** with a composer *and* a decomposer, so you can keep working
  in one file while the repo holds small ones. The split and join are mechanical and round-trip
  byte-identically.

Nothing about how you work changes. If you would rather I hold off, say so.

---

## F. Things not to undo

All five from the previous handover still stand — the voice picker renders the backend's answer,
frames keep their staleness badge, unspeakable scenes stay red, `sceneRange()` is untouched, and
there is no "training" language on the Learning screen.

Four more, each of which was a real bug once:

6. **The pillars in the house diagram never stack above 620px.** A collapsed pair reads as one pillar
   supporting the other, which is a strategic claim made by accident.
7. **Never show a declared split without the actual one.** A single bar is the version of that chart
   that lets a plan lie to itself.
8. **`blocking` findings are not dismissible.** They can be resolved or explicitly overridden with a
   recorded reason, never closed with an ✕.
9. **Empty is not the same as zero.** A rate that has never been judged shows *"not judged yet"*,
   never `0%`. An unknown owner shows *"owner unknown"*, never blank — blanks read as settled.

---

## G. Testing

```bash
Start Heritage Studio.bat     # no --reload; restart after any Python change
```

`houses/` and `plans/` are empty on a fresh install, so **design the empty states first** — that is
what the client sees on day one. A house takes about eight decisions to fill and a plan seven, so
please also design the *half-finished* state. It is where these screens will spend most of their life.
