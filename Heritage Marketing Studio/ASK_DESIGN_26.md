# ASK_DESIGN_26 — the PR desk

The whole PR backend is built: six phases, 41 routes, all verified over real HTTP. This is the screen
for it, held back until every route behind it worked against real data.

## Build on the file in this zip

```
app.dc.html      1,023,570 bytes
sha256           89755e5211d069e757921492ecf40ab151384bd01f41e4dbd34721128651c744
```

Your round-25 return is integrated. Base was confirmed byte-identical to what you were given
(`259271ed580619cf…`), and nothing on this side had touched the frontend since, so nothing was
reverted. checkfe **7/7**.

**Three defects were fixed in it after it landed**, all in this side's remit — bindings, not design
decisions. All three passed checkfe and threw no console error, and the first one is invisible until a
finding actually fires, which a clean test film never does.

| what | why it needed fixing |
|---|---|
| `ccDriftFindings` read `f.text \|\| f.finding` | A drift finding carries **neither**. The field is `advice`. So **every drift finding rendered as an empty string** — the whole actionable half of the drift report was blank. The panel showed the metric spans and then nothing, which reads as "no advice available" rather than as a fault. |
| Brightness showed a bar | It arrives `flags: false` and can never trip, so `span 47.9 (bar 10)` beside it read as a 3.6× failure on a measure that cannot fail — exactly the misreading `flags` exists to prevent. Now `span 47.9 — reported, not flagged`. |
| the metric name | Rendered the payload KEY, so the panel said "Luma" where the payload's own `label` says "Brightness". Now reads `m.label`. |

**On your open question — `/continuity-metrics` is fetched and nothing renders from it.** Your instinct
is right, and an info affordance on the card header is the natural home. What it carries that is worth
surfacing is `does_not`: *"does not verify that the face is the same face — that needs a vision model,
and it would be the least reliable thing here"*, *"does not flag brightness"*, *"refuses nothing"*.
Either give it that home or drop the fetch — a route called on every tab open and rendered nowhere is
the same shape as the bag key that was computed and never bound.

**Two answers to your earlier round-24 queries, still open on your side:** `trigger` is genuinely not
sent from the UI yet and diff-only `full` detection is sufficient for now — no control needed. And the
cutdown empty-state copy you flagged as a guess was right to flag: the backend was silently clamping a
2s request to 4s, which is fixed, and the reason now arrives in `notes`.

## This is a large round. If you can only do part of it, do it in this order

1. **The shell and the two modes** (§1) — nothing else can be reached without it.
2. **The funnel and the message set** (§2, §3) — everything downstream is written against them.
3. **The media map** (§4) — the biggest single panel.
4. **The release** (§5).
5. **The coverage report** (§6).
6. **Crisis** (§7) — self-contained, and the one to leave last.

Partial is fine. A half-built panel that reads as finished is not.

---

## What NOT to build. Read this before the sections.

These are not preferences. Each one is a refusal the backend already enforces, and a screen that
implies otherwise makes the product lie.

| never | why |
|---|---|
| **Any rupee value on coverage.** No "earned media value", no AVE. | Rejected by AMEC, the IPR, PRSA, PRCA, the Global Alliance and ICCO. It scores a demolition and a rave identically. `/pr-report` returns `ave: null` and a `why_no_ave` sentence — show the sentence if anyone asks. |
| **A send button.** Nothing that emails a journalist or publishes a statement. | The studio prepares; a named person sends. Volume outreach is the single thing journalists complain about most, and for a crisis statement an unreviewed send is a regulatory event. |
| **A single "reach" number.** | Print circulation and digital audience measure different populations by different methods. `/pr-reach` returns `blended: null` with `why_no_blend`. Two labelled figures or none. |
| **A journalist shown as suggested, or an "add suggested contacts" action.** | `POST /pr-journalist` refuses any record whose `origin` is not `entered` or `imported`. Outlets may be suggested; people never are. |
| **A hard-coded list of languages, tiers, risk classes or PR jobs.** | All of them come from payloads. Risk classes in particular are per-framework — hard-coding I/II/III would impose food's taxonomy on cosmetics. |
| **Zero where there is no data.** | `circulation: null` means no title here has a figure. Rendering it as `0` states something false. Show **"no data"**. |
| **A "publish" or "approve all" control on the crisis panel.** | Three separate signatures by three different people, deliberately. One button standing for a quality determination, a legal clearance and a chief executive's decision is the failure mode the whole design avoids. |

---

## 1 · Where it lives, and the two modes

**A new top-level nav item, `PR`, beside Sales enabler.** You asked for one tab with two buttons at the
top, and that is exactly the shape — the only judgement call is top-level rather than nested, because
standalone PR answers to no plan and no execution, and Sales enabler is the existing precedent for a
screen with that same optional linkage. Say if you would rather it sat under Execution.

Two buttons at the top of the screen, always visible:

```
[ Campaign PR ]  [ Standalone PR ]
```

They are not a filter — they decide what kind of sheet gets created and what the screen shows.

```
GET  /pr-status         → modes, standalone kinds, phases, the descent, the five PR jobs, message cap
GET  /pr-sheets?plan=&mode=   → list
POST /pr-sheet          → { brand, mode: campaign|standalone, plan?, house?, kind?, phase? }
GET  /pr-sheet/{id}     → { sheet, status, funnel, proof_options }
POST /pr-sheet-drop     → { id }
```

**Campaign PR** needs a plan and refuses without one — *"Campaign PR with nothing above it is standalone
PR that has not said so."* Surface that refusal rather than disabling the button silently. It also takes
a **phase**: `tease | launch | sustain`, from `/pr-status`, each with a `what` line worth showing —
the media map and the message set differ per phase, which is the only reason the field exists.

**Standalone PR** takes a **kind**: `corporate | milestone | crisis`. Crisis unlocks §7 and nothing else
changes.

`status.role` and `status.role_why` carry the sentence the whole module rests on — *"the functional
truth, earned… it carries a proof and it cannot construct a feeling"*. Put it on the screen once,
somewhere permanent. It is what stops PR being briefed as though it were advertising.

## 2 · The funnel — and its refusals are the point

```
GET  /pr-funnel?plan={id}   → { rows, owns, refused, contributes, levels, rungs, notes }
POST /pr-objectives         → { id, objectives: [{statement, statement_id?, rung?, proof?}] }
```

Each row of the plan's objectives ladder comes back with a **stance**, read from the plan's own `level`
field rather than guessed:

| stance | level | render as |
|---|---|---|
| `refused` | business | Struck through or greyed, **with its `why` visible.** Not hidden. |
| `contributes` | marketing | Available but marked — PR moves this, it does not own it. |
| `owns` | communication | The row a PR objective is written against. |

**Show the refused row.** Hiding it loses the teaching: *"PR cannot carry a revenue number. Judged on
one it will look like a failure whatever it achieves."* That sentence is the most useful thing on the
panel.

Each row also carries `suggested_rung`, `suggested_label` and `suggested_why` — one of five PR jobs,
matched from cues. **Render it as a suggestion a person confirms**, never as a decision. `rungs` in the
same payload gives each job its `what`, `proof`, `cannot` and `measure`. **`cannot` is the field that
earns the table** — show it.

`POST /pr-objectives` refuses an objective tied to a business-level row and returns the reason. Show it.

## 3 · The message set — three, each pointing at a proof

```
POST /pr-messages   → { id, messages: [{text, proof_id?, proof?}] }
```

Capped at **three** and refused above it — *"Pull-through is measured per message, and a set nobody can
hold in their head is not a set."* `proof_options` on `GET /pr-sheet/{id}` is the house's own reasons to
believe; a message pointing at one is `sourced`.

**Three states, not two**, and they need three different treatments:

- `sourced: true` — fine.
- `sourced: false`, `proof_missing: false` — **unsourced**. A note, not an error. Runnable, but a
  journalist will ask.
- `proof_missing: true` — **the evidence was deleted from the house.** This is *blocking* and it is a
  different situation: the ground moved under a message that may already have been pitched. It must not
  look the same as merely unsourced.

## 4 · The media map — brand-level, and shared

```
GET  /pr-map-status                    → languages, tiers, trade_categories, claims_authority, freshness
GET  /pr-map?brand=                    → { map, status, freshness }
GET  /pr-map-suggest?languages=te,hi   → { suggested, no_seed, note, source }
POST /pr-outlet                        → { brand, outlet: {…} }
POST /pr-journalist                    → { brand, journalist: {…} }
POST /pr-map-drop                      → { brand, outlet? | journalist? }
GET  /pr-reach?brand=                  → circulation and digital, by language
```

**The map belongs to the brand, not the sheet** — a campaign sheet and a recall sheet reach for the same
list. Make that visible: an edit here affects every PR sheet for the brand.

**Five tiers**, and `wire` is first for a reason worth putting on screen: one PTI pickup syndicates into
dozens of titles, so a wire hit is never one item of coverage.

**Suggestions.** `/pr-map-suggest` returns titles for the seeded languages, every one `confirmed: false`,
plus `no_seed` for the rest and a `note` explaining. **Show the note.** Eight of thirteen markets have no
seed, and that is a gap in the list rather than an absence of press — the honest thing to render, not an
empty state that looks like "no newspapers here".

**Freshness has four bands and `unverified` is separate from `stale`.** A row nobody ever checked is not
an old fact, it is not a fact. Show the age, not just a tick.

**Two audience figures, never summed.** `/pr-reach` gives `circulation` and `digital` per language, each
`null` when no title carries a figure — render **"no data"**. `why_missing` explains: the Indian
Readership Survey has been suspended since 2019, so there is nothing to fill a gap with. Wires are
counted in their own `wire` field and appear in neither the totals nor the missing lists.

`claims_authority` on `/pr-map-status` is the CCPA guidance that applies across every category. It
belongs near anything to do with influencers or endorsements — a disclosable material connection
includes free product, a family relationship and an equity stake, not just money.

## 5 · The release

```
GET  /pr-release-status      → parts, five_w, word band, kit elements, whether the skill is on disk
POST /pr-release             → { id, language? }
POST /pr-release-write       → { id, …fields, five_w?, carries?, mandatories? }
GET  /pr-release/{id}        → { release, gate, kit, locked_copy, messages }
POST /pr-translate           → { id, language, fields }
POST /pr-translation-check   → { id, language, who }
POST /pr-kit                 → { id, soundbite?, broll?, stills?, profile?, release? }
```

**Inverted pyramid, and the order on screen should be the order in the release** — headline, dateline,
lead, support, quote, background, boilerplate, contact. `parts` says which are required.

**The lead is five separate fields**, not a paragraph: who / what / when / where / why. The gate names
exactly which are missing. Render them as five inputs with their `what` hints from `five_w` — `why` is
the one that gets fudged, and its hint says so.

`words` and `band` — a note when outside 300–400, never an error.

**`carries`** is which declared messages this release carries, and writing one outside the set is refused
at the API. A picker from the sheet's messages, not free text.

**`mandatories`** are locked-copy ids that must appear **verbatim**. `locked_copy` comes back on
`GET /pr-release/{id}`. If the text is not present exactly, the gate blocks — a paraphrase of a legal
line is a compliance failure, not an edit.

**Translations.** Each arrives unchecked and blocks. `POST /pr-translation-check` needs a **name**.
**Any edit clears the check** — build the UI so that is obvious rather than surprising, because a person
who edits a signed translation and does not notice it went unsigned is the accident this prevents.
Translating into the release's own language is refused.

**The kit is elements, not a film.** Five: soundbite (needs a named person, or it blocks), b-roll,
stills, profile, release. A `-scored` master is **refused** as b-roll with an explanation. An `/edits/`
path is accepted with a note asking you to confirm it is silent — that directory holds both silent trims
and scored cuts.

## 6 · The coverage report

```
GET  /pr-coverage-status   → prominence, sentiment, why_no_ave
POST /pr-coverage          → { id, item: {…} }
POST /pr-coverage-drop     → { id, item }
GET  /pr-report/{id}       → every measure
```

**Lead with `pull_through`.** It is the number that separates coverage from effect: the share of items
carrying at least one *declared* message, plus `front_share` — carried in the headline or lead, where it
survives an edit. `per_message` shows which of the three actually travelled, and **a message with zero
items is the most useful row on the screen.** Do not sort it away.

Then `prominence` (headline / lead / body / mention — a mention is not a mention), `sentiment` (three
values; the thing AVE cannot see), and `independent` vs `syndicated` — forty pickups of one PTI story
are forty readerships and **one** editorial decision, and `independent.what` says so.

**Two audience figures again, and neither is called reach:**

- `opportunities.circulation` — summed per item. A title running twice counts twice.
- `distinct_outlet_circulation` — summed once per outlet. Closer to a readership, still an over-count.

Each carries its own `what`. Render both with their labels or neither.

`unpriced_items` is how many items have no audience figure at all. `by_outlet` rows carry `off_map` —
titles nobody pitched that ran it anyway, which the findings suggest adding to the map.

Logging an item takes `outlet` (from the map) **or** `outlet_name` + `language` + `tier` for a title not
in it. `prominence` is required; the refusal explains why.

## 7 · Crisis — only on a standalone sheet of kind `crisis`

```
GET  /pr-crisis-status        → notice_elements, roles, categories, frameworks, limits
GET|POST /pr-framework        → what a regulator requires, per jurisdiction + category
POST /pr-standby              → { id, statements: [{situation, text, approved_by?}] }
POST /pr-incident             → { id, jurisdiction, category, discovered_at?, summary? }
POST /pr-risk-class           → { id, risk_class, who }
POST /pr-notice               → { id, product?, risk?, action?, statement? }
POST /pr-sign                 → { id, role: qa|legal|ceo, who }
GET  /pr-crisis/{id}          → the whole state
```

**Put `limits` on the screen, permanently:** *"This studio drafts and checks. It does not determine the
risk class, does not state what a regulation requires, and does not send. Those are the client's
quality, legal and executive functions."* It is the sentence that stops the panel being mistaken for a
compliance tool.

**Two states, and most of the time it is the first one.**

**Prepared, no incident.** Standby statements written in calm. A sheet with none blocks; a sheet with
them reports *"Prepared, no incident open"* as a note. Make that read as a **good** state, not an empty
one — it is where a crisis sheet should sit for years.

**Incident open.** Then, in this order:

1. **The framework.** If `framework_entered` is false, everything else is blocked and the reason is
   plain: nothing has been confirmed for this category in this jurisdiction, and **the framework for
   another category does not apply**. Entering one refuses any obligation with no source, and refuses
   the whole thing with no named confirmer.
2. **The risk class.** From the framework's own `classes`, never a hard-coded I/II/III. Needs a named
   person in quality. `public_notice_required` and `ceo_required` follow from the class.
3. **The clock.** `duties` carry `hours_left` and `overdue`. Show `hours_since_discovery` prominently.
   `clock_note` admits these are the server's local clock and an aid rather than the record — show it.
4. **The notice**, when the class requires one: three fields — product, risk, action — each with its
   `what`. All three or it is not a notice.
5. **The signatures.** `required_signoff` says which are needed; the CEO appears only when the class
   escalates. Legal and CEO are **refused before quality has set the class**.

**Two things the UI must make unmissable:**

- **Editing the statement, or changing the class, clears every signature.** Both are correct and both
  will surprise someone. Make the clearing visible at the moment it happens.
- **`ready` means the statement is fit to issue — it does NOT mean the recall is on schedule.**
  `overdue` is a separate array and deliberately does not block. Show overdue duties loudly beside a
  ready statement; the notice must never wait on a late authority filing. `ready_means` says this in
  the payload.

---

## Verify on your end

- `/pr-sheet` for campaign mode with no plan → the refusal renders as a sentence, not a dead button.
- A funnel with a business-level row → the refused row is visible with its `why`.
- A message with `proof_missing` → visibly different from an unsourced one.
- `/pr-map-suggest?languages=bn` → the "no seed for this market" note shows, not an empty list.
- `/pr-reach` on a map with no circulation figures → "no data", never `0`.
- A translation, checked, then edited → the check visibly clears.
- A crisis sheet with no framework → blocked with the reason, and no class picker offered.
- `checkfe.py`, all seven.

## Verified on this end

All 41 PR routes exercised over real HTTP against a running server with real stored data — the Heritage
house and plan, the house's own reasons to believe as proof options, and a full FSSAI framework entered
with a source against each obligation, then a Class I recall run end to end through class, notice,
three signatures and the 24-hour clock showing 4.6 hours overdue.

Every refusal in the table above was tested by attempting it. Four defects were found and fixed by
testing rather than reading: a coverage roll-up reporting `circulation: 0` where it meant "no data"; a
wire agency appearing on the missing-circulation list it could never leave; a b-roll rule refusing every
`/edits/` path when that directory holds silent trims too; and — the one that mattered — an overdue
statutory duty **blocking** the statement, which would have meant the module actively delayed a recall
notice because the company was late on a different obligation.

18/18 `test_tools.py`, `contract.py` clean, checkfe 7/7, **220 routes**, page loads with only the four
pre-existing SVG placeholder warnings, and the tenant tree, library, renders and edits all byte-identical
afterwards with all three PR stores left empty.
