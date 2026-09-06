# ASK_DESIGN_43 — four from user testing, and a house screen that discards edits

**Base: `b9722338`, 1,472,076 bytes / 1,469,885 characters.** Your round 42 merged with my social
importer and the join. Both lineages verified present; the region split you held meant 29 hunks applied
with zero failures.

Round 42 confirmed here: checkfe **8/8**, test_tools 18/18, parse probe clean, and — for the first time
in this sequence — **the console is completely empty**. Your `wheelPaths` / `pinCircles` fix closed the
last four attribute holes.

**`fallbackSocial` was the most valuable find in ten rounds.** Three fully-written posts with an
invented statistic, returned on any tenant whenever the model failed, presented as the studio's own
output. That is precisely what the brief importer's refusal exists to prevent, two screens away, and I
had swept that path in round 34 without looking at this one. Verified: it returns empty strings and a
reason now, and the only surviving mention of "3,00,000+ farmer families" is the comment recording the
fix. Both prompt leaks gone too — my round-37 sweep grepped for `You are` and missed a `Context:` and an
`infer sensibly`, the same shape as your `Follow …` miss.

Your two review passes are the round's real lesson: the one-shot spent before it had data, then its
mirror image with `brands: []`. **A flag must distinguish "no" from "not yet", and a default value is
not an answer.**

## Where this round comes from

A user-testing pass on `b9722338` produced five items. **Item 4 is done** — `/pr-message-suggest`, §5
below, so you can build against it. The other four are here, and §1 is the one I would start with.

## 1. The house summary invites edits and throws them away

**This is a defect, not a request, and it is on the document everything else descends from.**

`buildHouseSummary()` already builds the single-screen view a person needs: core, the emotional message
and its RTBs, the functional message and its RTBs, proof, culture — the chosen set as one diagram with
sourced counts per pillar. It is good.

`openSummary` writes it into a **pop-up** via `window.open`. In that pop-up:

- **11 fields carry `contenteditable="true"`**
- **0 save paths** — no `fetch`, no `postMessage`, no `opener`, nothing pointing at `/house-option`

So a person retypes their core message there, closes the window, and the edit is gone. Same family as
the media panel's "Save the media plan", and worse placed: the house is what the plan, the platform,
every producer and the PR desk all descend from.

### What the user actually asked for, and why it is this screen

Verbatim: *"if there can be a screen (not a layer) where i see the selected layers in a visual form and
editable to make adjustments for reconciliation purpose"* — laid out **core → functional message + its
RTB → bridge → emotional message + its RTB**, with the bridge options generated.

They opened by asking to **merge** the message and RTB layers to reduce the count. I argued against it
and they agreed, so the store is unchanged and there is no migration. The reasoning, in case it is
useful to you:

- `LADDER_FROM = ("rtb_functional", "functional")` and `LADDER_TO = ("emotional", "rtb_emotional")`
  exist deliberately — *"the rung a person starts from is their judgement, not ours: some ladders start
  at the hard fact and some at the claim built on it."* Merging removes that.
- One RTB can support several messages and one message can rest on several RTBs. A merged layer forces
  a 1:1 that is not true.
- Four houses in the store would need migrating for a gain that a screen gives free.

**Their reconciliation problem is real and it is a placement problem.** The three-column many-to-many
canvas they sketched already exists — `hLadderCols`, and its columns already co-locate message and RTB
(`f` is `rtb_functional` + `functional`, `e` is `emotional` + `rtb_emotional`). It is gated behind
`hIsBridge`, so it is **layer 6 of 8**: you walk five rails each showing one layer alone, then arrive at
"Bridges" and only there meet the view that reconciles them. That is why they struggled, and it is why
a screen beats a layer.

### What I would ask for

**Promote the one-pager into a real screen, and make its editing real.** The layers stay as they are and
become where you edit *one thing deliberately*; the screen is where you *read the house and reconcile
it*.

Everything needed exists:

| need | already there |
|---|---|
| the chosen set | `houseLayerData(k).picked`, `strategy._chosen_text(house, layer)` |
| the diagram | `buildHouseSummary()` |
| **writing an edit** | `POST /house-option` → `strategy.edit_option(house, layer_id, option_id, text)` |
| generated bridges | `draft_ladders(house, n)` — bridge is a rung, `BRIDGE_MAX_WORDS = 12` |
| the many-to-many paths | `ladders: [{id, f, b1, b2, e}]`, already stored |

The one thing I would hold you to: **the edit must go through `/house-option`**, the same route the
layer editor uses. A second writer for the same field is the failure this file has spent six rounds
paying down, and it would be especially bad here because the layer screen and this screen would then
disagree about what the house says.

If real editing is more than a round, **the honest interim is to remove `contenteditable` and label it a
view.** A read-only summary is worth having; one that discards edits is not.

### One content observation, theirs to decide

On a single screen this becomes visible immediately, which is the point of the screen. In their house:

- emotional RTB — *"A child raised on Heritage milk shows it in the small things…"*
- emotional message — *"When they grow up strong, everyone can see what we're made of."*

That RTB is not a proof; it is an observed consequence — **bridge work wearing an RTB label.** Part of
why the layers feel irreconcilable is that `rtb_emotional` and `bridge` overlap in meaning in practice.
That is a content decision for them, not a schema change, and the screen is what surfaces it.

## 2. The IMC brief has no readable output

**Reported as:** after approving, the screen shows a raw JSON dump — `{"brand": "Heritage", "category":
"Dairy", "prepared_for": …, "competitors": [...]}` in a navy block.

**What it actually is:** that block is `imcShowJson`, a deliberate "Preview JSON" toggle defaulting to
`false`. Approval does not switch it on. The finding is underneath — **the IMC brief has no rendered
on-screen output at all.** After generating and approving, what exists is the scattered form fields,
that toggle, and a `.docx` download. The JSON preview is the only consolidated view of the thing just
approved, which is why a person reached for it.

**The material exists.** `imcWordRows(d)` builds exactly the structure a rendered brief needs —
`[{k:'Brand', v:d.brand}, {h:'Competitive landscape'}, …]` — and only the Word export calls it. Two
mappings of one document is how the .docx and the screen start disagreeing about what the brief says.

So: the approved brief should be readable on the screen that approved it, from `imcWordRows` rather than
a second mapping. Keep the JSON toggle — quietly changing a debugging affordance is its own trap — it
just stops being the only way to read your own brief.

## 3. Expression by medium is asked for before the idea it expresses

Confirmed in the file:

| | |
|---|---|
| STEP 1 | The platform |
| STEP 2 | Two tests |
| **STEP 3** | **Expression by medium** |
| STEP 4 | The campaign — *"the territory, for years"* / *"Big idea — what this campaign does with it this season"* |

A person writes one expression per medium at step 3, then names the big idea those expressions express at
step 4. Same shape as your one-shot bug, one altitude up: **asked before the thing it depends on.**

Round 33 settled that the big idea sits on the campaign and the platform is the multi-year territory.
The expressions belong to the platform; what a season's expression *says* is downstream of the season's
idea. Two readings:

- **Swap 3 and 4** — the campaign and its big idea become step 3, expressions step 4. The dependency
  becomes the order.
- **Keep the position, gate the content** — expressions stay at 3 and say what they are missing until a
  big idea exists.

I lean to the swap; the second keeps a step a person cannot complete, which is what the plan's
blocked-layer copy exists to avoid rather than reproduce. The step numbers carry an argument, so the
call is yours.

## 4. The social campaigns panel needs a flow

**Reported as:** *"very confusing, we need to build a flow and clarity on it."* A sequencing problem, not
a defect list, which is why I am handing it over rather than patching it.

The server has a clear order and the screen does not read as one:

```
frame  →  benchmark        →  cells      →  verdict
what it is for,     what an action costs,   the geographies    runnable / too fine /
how much, how long  and where it came from  that hold money    impossible / reported
```

Each genuinely gates the next: no budget and no flight and the weekly threshold cannot be computed; no
benchmark and every feasibility figure divides by a number nobody chose (that form refuses to save
without a source, deliberately); no cells and there is nothing to judge. The verdict is the answer, and
it currently sits as one card among many rather than the end of a path.

What is missing is not controls but **sequence made visible** — which step you are on, what it needs,
what it unlocks. The material is served: `blocking`, `findings`, `counts`, `what_this_cannot_do`, and now
`optimisation_note` and the level notes.

Two things to keep whatever the layout becomes:

- **The two pickers stay two.** Your round-40 reasoning holds: the strategic objective and the
  optimisation event share the words *reach* and *conversion* and mean different things, and the
  threshold counts the second.
- **The verdict must not become a score.** `reported` is a real state — arithmetic and explicitly *"not
  judged"* — because there is no defensible universal target frequency. A flow with a progress bar
  invites a pass/fail at the end, and this module refuses to give one.

Since your round 42 I have added one thing here: **"Or read a sheet"** in the cell form.
`POST /social-plan-import` turns a spreadsheet of geographies into *proposed* cells — every row
validated through `add_cell` itself against a scratch copy, so a refusal there is the refusal typing it
would have given, and an import cannot become the way around a validator. Unrecognised columns are named,
not dropped. Functional-first; it sits inside whatever flow you build.

## 5. Done on my side — `/pr-message-suggest`

The message panel offered an empty box and a proof picker, so a person with nothing typed declared
nothing — and the release, the plan and coverage all sit behind a declared set. Same block the objectives
had before `suggest_statement`.

`GET /pr-message-suggest?id=<sheet>`:

| field | type | meaning |
|---|---|---|
| `suggested[]` | list | `{text, proof_id, from, parts, already_declared}` |
| `parts` | object | `{claim, claim_layer, proof, proof_id, proof_layer}` — all strings |
| `cap` | int | `MESSAGE_MAX`, 3 |
| `proof_options` | list | the same options the picker already uses |
| `note` | string | why there is nothing, when there is nothing |
| `n_declared`, `writes_nothing` | int / bool | |

**Composes nothing.** A PR message is a claim; an RTB is why it is believable; the house holds both. A
proposal is one of the house's own messages verbatim, pointed at one of the house's own reasons to
believe, also verbatim. The pairing is the house's own — `rtb_functional` supports the functional
message, which is what those layers mean.

Live on the real sheet: functional paired with proof `7abfbdb0`, emotional with `d7531eaf`, and **the
core message offered with its proof honestly absent** rather than borrowed from one of the others.
`parts` is there so you can render the two halves rather than one sentence — same request as
`suggested_statement_parts`, same reason.

## 6. Two corrections, both trivial

**Your structural count says `sc-if` 730; the file is 732.** Harmless, except these numbers are a check
now: my merge arithmetic was base 723 + your +9 + my +6 = 738, which is what I measured, and I only got
there by reading your file rather than your number.

**`census.py` is in `tools/` now**, pasted from your handover and LF-normalised. I tested it rather than
only running it, and the result matters to you:

### census.py does not catch the bug it was written for

I removed the `/activation-kit` loader — reintroducing the exact `og.kit` bug — and **the output was
identical**. `kit` never appears.

The namespace regex needs `this.og().kit` inline. Real code is `const o = this.og();` then `o.kit` — the
accessor aliased to a local, which the regex cannot follow. There are five such aliases in the on-ground
code alone, and that pattern is the norm in this file rather than the exception.

Separately, all 13 top-level "orphans" it reports are false positives with one shared cause: the writer
regex is `[^}]{0,600}`, which stops at the first `}`, so `setState(s => ({ bfVals: {…}, bfDirty:true }))`
hides everything after the nested object. Hence `bfDirty`, `bfVoice` and `ladderDraftNote` appearing
despite being written six times each.

Neither is a reason to drop it — the discipline is right and the top-level section will earn its keep.
But it wants alias tracking and brace matching before either of us relies on it, and I would rather you
knew before it reports a clean file and we believe it.

## Still open

1. **`social_plan/546ae757a9.json`** — my test artefact, still listed. Deletion blocked on my side.
2. **Auth and tenancy (#6) and the measurement loop (#9)** — the audit's own next items, both Large. You
   asked for the audit's framing before questions; that is a document of its own and it comes after this.
