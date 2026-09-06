# The Marketing Studio — the working document for Claude Design

**This replaces every previous handover.** `DESIGN_HANDOVER_STRATEGY.md`,
`DESIGN_HANDOVER_2026-08.md`, `BACKEND_ANSWER_TO_DESIGN.md`, `CLAUDE_DESIGN_HANDOVER.md`,
`SOCIAL_VIDEO_STUDIO_BRIEF.md` and `IMC_BRIEF_FRONTEND_BRIEF.md` are history — kept for the record, not
for reference. If something in one of them contradicts this file, this file is right.

It is meant to be edited rather than superseded. Add to it; don't write a seventh.

**File you edit:** `api/frontend/app.dc.html` — 662KB, 8,353 lines, one Design Component.
**Do not change:** anything in `api/*.py`. Every contract below is **LIVE and tested** unless marked
otherwise.

Jump to what you need: [§7 asks](#7-what-i-need-from-you) · [§8 do not undo](#8-things-not-to-undo) ·
[§4 tooling](#4-tooling-you-may-find-useful)

---

## 1. What I changed inside your file

Two edits, both covered by a test that asserts your file is otherwise byte-identical.

**`demoStrategy` now defaults to `false`** — the prop default and the `??` fallback. Your empty states
were designed; they should be what a dead server shows. Left on, a partly-failing server would show
someone a fabricated half-finished house indistinguishable from their own work. Flip it in the tweak
panel whenever you're reviewing.

**25 comment banners in the logic**, in your existing style:

```js
  // ===== VIDEO: script writing =====
```

They're split anchors for the tooling in §4. Nothing else moved.

---

## 2. How this file works

A single `.dc.html`: `class Component extends DCLogic`, served by FastAPI with React and a
`window.claude.complete()` bridge injected ahead of `support.js`.

### The bag

The template contains **no expressions**. `renderVals()` returns one flat object — now ~650 keys, up
from 233 — and the markup only interpolates from it. Every colour, label, boolean and handler is computed
in JS first.

```js
const rows = (s.things || []).map(t => ({
  ...t,
  badgeBg: t.ok ? '#EAF6EC' : '#FBE3E1',   // colours are computed, never chosen in markup
  open: this.openThing(t.id),               // handlers are pre-bound
}));
return { things: rows, hasThings: rows.length > 0, noThings: rows.length === 0 };
```

You split four areas out already — `bagStrategy`, `bagPlan`, `bagExec`, `bagSales`, spread in with
`...this.bagArea(s)`. **Keep doing that for anything new.** It's the pattern that stopped the file's
growth becoming a problem, and `checkfe` now verifies every `bagX` is both defined and spread.

### The three primitives

```html
<sc-if value="{{ hasThings }}" hint-placeholder-val="{{ false }}"> … </sc-if>

<sc-for list="{{ things }}" as="t" hint-placeholder-count="4">
  <div onClick="{{ t.open }}" style="background:{{ t.badgeBg }};">{{ t.name }}</div>
</sc-for>
```

Rules that bite if ignored:

- **No `&&`, no ternaries, no `.map()` in markup.** `{{ a || b }}` will not work. Compute it.
- **Booleans need their own key.** There is no `unless`; pair `hasX` with `noX`.
- **`sc-if` and `sc-for` must balance.** Currently `sc-if` 237/237, `sc-for` 133/133, `div` 1116/1116.
- **Loop aliases are scoped** — `as="t"` then `{{ t.field }}`. Nesting works.
- **Styles are inline.** No class system beyond `.hf-scroll` and two keyframes.
- **Unicode is inconsistent** — some strings hold a literal `—`, others an escape. Match the line you're
  editing. (This is where I broke eight literals once; see §4.)
- React is available for what markup can't express (`React.createElement('audio', …)`) — used 22 times.
  Prefer markup.

---

## 3. Brand system — non-negotiable

From `brand-book.html`, verified against the book's own WCAG table.

| Token | Hex | Role | In file |
|---|---|---|---|
| Navy | `#17325E` | Primary. Type, dark grounds, buttons, body | 467 |
| Signal Orange | `#F0561E` | **Accent, rationed** | 27 |
| System Mid | `#2E5EA6` | UI layers, gradients, links | 47 |
| System Light | `#9DB8E0` | Backgrounds, dividers | 5 |
| Paper | `#F7F5F1` | Ground. Preferred over white | 75 |
| Line | `#DDD9D1` · `#C9CEDA` | Borders, warm and cool | — |
| Slate | `#6B7280` | Secondary text, captions | 311 |

- **Orange is not a text colour** — 3.19:1 on paper, large-text only, never running copy. It marks *the
  live layer, the thing currently running*, which is what the mark itself means.
- **Type is Epilogue**, 400/500/600/700, from Google Fonts.
- **Status colours stay green/amber/red** (`#259821` `#E8A93C` `#C0392B`) — the client's explicit
  decision. Interface signals, not brand expression; the palette has no equivalents.
- **The logo is artwork, never live type.** `api/frontend/assets/` holds `logo-primary.svg`,
  `logo-stacked.svg`, `logo-stacked-notagline.svg`, `monogram.svg`, `glyph.svg`, `app-icon.svg` and
  reversed variants. Minimums: primary 180px wide, stacked 110px, monogram 64px.
- **Heritage's own kit is separate and must not be swept into the studio's.** `Deep Forest` and `Cream`
  belong to the client's brand and appear inside client-facing artefacts. I overwrote them once during
  the rebrand; they're restored and should stay.
- Everything works offline apart from the font — no CDNs, no remote images. **One exception exists and
  should go:** see §9.

The header is 84px and the client identity now sits in the Home hero gutter. That resolved the old
open question about the stacked lockup; nothing further needed.

---

## 4. Tooling you may find useful

There is no Node here, so these are Python. Run them from the repo root.

```bash
python tools/checkfe.py        # before any commit that touches app.dc.html
python tools/partials.py status # what the file divides into, and how big
python tools/test_tools.py     # 18 tests proving both tools still work
```

### `checkfe.py` — the check that was missing

I once flattened newline escapes in this file and broke eight string literals. The tag-balance and
binding checks I was running all passed, because neither looked at JavaScript. You found it.

`checkfe` is not a parser. It's a scanner that is certain about:

- **Unterminated string literals** — a `'` or `"` cannot cross a line break, which is exactly what
  mangled escapes produce. The one that matters.
- **Bracket balance**, ignoring anything quoted, commented, templated or in a regex. A naive brace count
  here is meaningless: the markup is full of `{{ }}`, the logic full of `${}`.
- `sc-if` / `sc-for` / `<div>` pairing.
- Duplicate class members — the later one silently wins. (Checked: currently 376 declared, 0 duplicates.)
- `bagX()` spread but never defined, or defined and never spread.

Exit 0 means every check passed. It does **not** prove the file runs — nothing here can. Its own tests
feed it each defect and require it to report them, so green means something.

### `partials.py` — split for review, join byte-identically

Cuts the file into **59 parts** on the comment banners it already has:

```
markup :  ^  <!-- ===== NAME ===== -->     (exactly two spaces of indent)
logic  :  ^  // ===== NAME =====           (inside the data-dc-script block only)
```

No sentinels inserted, nothing modified, no markers to delete by accident. Deeper-indented banners like
`    <!-- ==== STEP: SCRIPTING ==== -->` stay put as sub-sections.

```bash
python tools/partials.py split   # -> api/frontend/parts/  (gitignored)
python tools/partials.py join    # parts/ -> app.dc.html
python tools/partials.py verify  # round-trip, changes nothing
```

The round trip is byte-identical and tested on the real file every run. `join` refuses outright if a part
is missing or emptied. **If you ever want to work on one screen in isolation**, `split`, edit the part,
`join`, then `checkfe` — that's the whole workflow. `app.dc.html` remains the single source of truth;
`parts/` is a review aid.

### On splitting `renderVals()` — for you, not me

`renderVals()` is 1,059 lines and the largest part by far. It looks like the obvious next target. I
measured it before touching it:

> **142 locals are set up before the `return {`, and 112 are referenced inside it.** `s` alone appears
> 263 times; `im` 19, `lrn` 17, `cp` 12, `dc` 12, `prod` 11, `th` 10.

Move a slice of that literal into a new `bagX(s)` and every one of those references breaks — at
**runtime**, not parse time. The syntax stays perfectly valid, so `checkfe` would go green on a broken
file. That's precisely the failure it exists to prevent, so I stopped.

You can do it safely because you can load the screen. The recipe:

1. Take one area's keys out of the return into `bagArea(s)`.
2. Move the locals only that area uses in with them.
3. For locals shared with other areas — `s`, `im`, `lrn`, `cp`, `dc`, `prod`, `th` — pass what's needed
   as arguments, or promote the derivation to a small method called from both.
4. Spread it back: `...this.bagArea(s)`.
5. `python tools/checkfe.py`, then load the screen.

**Not urgent.** Your four `bagX` methods already mean new areas don't touch the monolith, so retro-
splitting is tidiness rather than capacity. Worth doing next time you're in there anyway.

---

## 5. The spine

```
Brief ──▶ Messaging house ──┬──▶ Communication plan ──┐
                            │    (who · where · when)  ├──▶ Executions
                            └──▶ Idea platform ────────┘    social · video · POSM
                                 (the idea, optional)        activation · media · incentive

                            Sales enabler — the trade sheet, briefed from the whole
                            route to market at once, not from one audience row
```

**It is a fork, not a chain.** The plan decides who, where and when. The platform decides the idea. Both
descend from the house; an execution inherits from both. That's why the platform lives in Strategy and
not in Plan.

Three things shape every screen here:

**One layer at a time, and choosing is the product.** Nothing is generated in one go. Each layer offers
genuinely different options, a person chooses, and the layers below are written *against that choice*. If
the UI makes "generate everything" easy the tool stops working, because nothing was ever decided — only
written. The server refuses out-of-order calls.

**Findings are the substance, not decoration.** Every document returns `findings[]` with a `level`. Some
are `blocking`. They are the review, not validation errors for a toast.

**Staleness crosses documents.** Change a pillar and every plan layer, execution and platform expression
written against it goes stale *by name*. This is the one thing chat cannot do and the reason these live in
a portal. It is the payoff — show it.

---

## 6. LIVE contracts

Everything here is implemented and tested. Empty-state note: `houses/ plans/ platforms/ trade/
executions/` are all empty on a fresh install and `demoStrategy` is now off, so **the empty states are
day one** — and the half-finished states are where these screens will spend their life.

### 6.1 Messaging house — screens `strategy`, `house`

Eight layers: `core → emotional | functional → rtb_emotional | rtb_functional → proof → culture → medium`

```
GET  /houses                       -> { houses[], layers[], culture_kinds[], media[], caveat, downloads }
POST /house-new     { brand, brief }
GET  /house/{id}
POST /house-generate { id, layer, note, replace }     // 400 if out of order
POST /house-choose   { id, layer, options[] }
POST /house-option   { id, layer, text, note, tag }          // add
POST /house-option   { id, layer, option, text, note, tag }   // EDIT — upsert
POST /house-option   { id, layer, drop }
GET  /house-prompt/{id}/{layer}    -> { prompt }
GET  /house-docx/{id}[?mode=worksheet]
```

**Editing the text re-sources the option to `user`.** That's what makes your amber panel work end to end:
rewriting a model line in your own words clears the unsourced finding, because the claim is now theirs.
Editing only the note or tag leaves `source` alone — tidying a rationale is not authorship.

`media` now includes **`trade`**, so all six execution kinds resolve a message.

### 6.2 Communication plan — screens `plans`, `plan`

| Layer | Columns |
|---|---|
| `objectives` | level · statement · measure · by_when |
| `audiences` | audience · rank · believes_now · pillar |
| `channels` | channel · role · job · measure · side · share · owner · lead |
| `balance` | *(a number)* |
| `phases` | phase · window · occasion · channels · hands_over |
| `measures` | role · leading · lagging · would_tell_us_it_failed |
| `governance` | who · speaks_on · boundary · decides_changes |

```
GET  /plans                        -> { plans[], layers[], roles{}, sides[], default_brand_share, caveat, downloads }
POST /plan-new  { brand, house }
GET  /plan/{id}
POST /plan-generate { id, layer, note, replace }
POST /plan-row  { id, layer, row{...} }        // adds; with row.id present, UPSERTS
POST /plan-row  { id, layer, drop }
POST /plan-balance { id, brand_share, reason, basis }   // basis "year" | "window"
GET  /plan-prompt/{id}/{layer}
GET  /plan-docx/{id}[?mode=worksheet]
```

`status.house_evidence` gives `{emotional:[sourced,total], functional:[sourced,total]}` — show it beside
the channels table, because it decides which channels may be given proof work.

### 6.3 Idea platform — in the Strategy tab, beside the house

**Optional.** A platform is not a big concept: the difference is a *mechanic*, a repeatable device that
generates the next execution. *"Celebrate the mothers of India"* is a sentiment — one film, then repeats.
*"Every pack carries the name of the dairy that filled it"* is a mechanic — a film, a pack change, a shelf
strip, a promoter who can point at something, a trade argument about provenance.

```
GET  /platforms?house=             -> { sets[], expressions{}, min_media, min_platforms, optional, why }
GET  /platforms-for/{house_id}     -> { set, status, ready, blocked_because, basis }
POST /platform-new       { house, brand }
POST /platform-generate  { id, build_on?, n?, note? }
POST /platform-item      { id, name, idea, mechanic, territory, proof, rtb, why, expressions{} }
POST /platform-item      { id, item, ... }   // edit
POST /platform-item      { id, drop }
POST /platform-express   { id, item, kind, text }
POST /platform-choose    { id, item }
GET  /platform-prompt/{id}?build_on=
```

**Two iteration modes, and they are different buttons.** *More options* — three fresh bets, given
everything already on the table and required to go elsewhere; they must differ on the **bet** (which
pillar leads, which proof is dramatised, which cultural code, who the protagonist is). *Build on this*
(`build_on`) — developments of one platform, keeping its idea recognisable. **Neither replaces anything.**

**Write-your-own should be the first card**, as in the house. `source: user` — the author is the evidence.
The machine's value here is the five tests, not the ideas.

`status.platforms[].tests` gives five structs, each `{ok, detail, …}`, plus `passes` / `of`:

| key | checks | level when it fails |
|---|---|---|
| `media` | expressed in ≥3 of 5 media | open |
| `mechanic` | a mechanic, not a sentiment | **blocking** |
| `avoid` | doesn't collide with the house's avoid list | open |
| `proof` | dramatises a **sourced** RTB | **blocking** if it names an unsourced one |
| `neutral` | not film-only | open |

`avoid` is word-overlap, so it's worded as a question — *"may collide with 'Never show milk being wasted'
— check it, this is a hint rather than a verdict."* **Keep that register.** A heuristic presented as a
verdict gets ignored, and then the real findings do too.

Expressions cover `video`, `social`, `posm`, `activation`, `incentive` — one honest sentence about what
the idea *becomes* there. **`media` is absent on purpose:** a media plan allocates, it doesn't speak.

### 6.4 Execution envelope — one shape, six producers

```
POST /execution-new      { plan, kind, audience, channel, occasion, measure, message }
GET  /executions?plan=&kind=  -> { executions[], summary{by_kind, stale, blocked, total} }
GET  /execution/{id}
GET  /execution-options/{plan_id}/{kind}
     -> { audiences[], channels[], occasions[], measures[], measures_by_role{}, messages[], producer }
POST /execution-rebrief  { id }
POST /execution-status   { id, status }   // briefed -> made -> approved -> shipped
POST /execution-produce  { id }
GET  /producers/{kind} · GET /producers
```

Six kinds: `social · video · posm · activation · media · incentive`. **`media` reports
`message_required: false`** — your call, and right: a media plan allocates weight and money.

`messages` contains only the house's chosen lines **tagged with this kind's medium**. An empty array is a
real answer, and the 400 says so rather than offering the core line truncated.

The **pillar is inherited** from the audience and cannot be chosen. **Role/measure disagreement is
refused at brief time**, not warned about.

An execution inherits `brief.platform = {id, name, idea, mechanic, expression}` where `expression` is its
own kind's line — the glimpse of the idea and the producer's input. Show it as a header strip.

**`/execution-rebrief` can return 409 and you must surface it.** If the plan has moved somewhere the
execution cannot legally be briefed from, there is nothing to re-brief *to*; the 409 carries the reason
and the current status. A 200 there leaves a stale badge that never clears with no way to find out why.

**`/execution-produce` returns 409 with the findings** when anything blocking stands.

Producers you assumed, now built:

```
POST /posm-keyvisual     { brief, execution? } -> { options:[{id,name,desc}], note }
POST /activation-idea    { idea, execution? }  -> { idea, note }
POST /activation-element { element, brief, idea, execution? } -> { brief, note }
```

`/posm-keyvisual` always returns usable routes; `note` says whether they were generated or are the
declared treatment angles, so a quiet degradation isn't mistaken for a considered answer.
`/activation-idea` returns **400 on an empty box** — it sharpens an idea, it does not supply one. Pass
`execution` and all three are grounded in that brief, including the house's avoid list.

### 6.5 Sales enabler — its own contract

Separate from the envelope, as you argued: a trade channel is not briefed from one audience row. Channel
conflict is the central risk and it's invisible unless every channel sits in one view.

```
GET  /trade                    -> { sheets[], channels[], roles{}, levers[], sell_through{}, states[] }
POST /trade-new  { brand, plan, house }
GET  /trade/{id}
POST /sales-channel { id, channel, role, share_now, behaviour, baseline, target, lever,
                      cost_per_unit, payback, leakage, control, residual_risk,
                      sell_through, receives_money, effective_price, owner }
POST /sales-element { id, channel, element, brief, status }
POST /sales-generate { id, channel, element, note }
GET  /sales-prompt/{id}/{channel}?element=
```

**Your channel keys and all 29 element keys are matched exactly** — `trad, wholesale, modern, ecomm,
qcomm, loyalty` — so your rail count and mine can't disagree. **`/sales-element` works without a sheet
id**: your build posts `{channel, element, brief}`, and an id-less call lands on the most recent sheet or
opens one. Passing `id` always wins, so move to ids whenever you like and I'll delete the bridge.

Writing a brief promotes `not started → briefed`; clearing it goes back.

What it enforces:

- **"Visibility" is blocking, not a warning.** Also engagement, excitement, awareness, presence,
  mindshare, buzz, activation, push, focus, support, momentum. A behaviour needs a baseline and a target.
- **Primary-only sell-through is always blocking**, and gates the pitch card: `card`, `pitch` or `scheme`
  marked `agreed` against a primary-only scheme returns 400.
- **`status.reconciliation`** — the effective-price strip: `points[]` sorted by price, `missing[]` with the
  reason each is unplotted, `collisions[]`, `spread`. A q-comm or e-comm price under traditional retail is
  blocking, with the gap named.
- **Channels sort by share of volume descending**, unknown shares last.

Two changes from your six: **loyalty is typed `scope: "lever"`**, because it runs *through* general trade
and q-commerce rather than beside them — given its own room its cost never lands against the behaviour it
buys. Your tab is unaffected, but a loyalty programme naming no channels is now blocking, so that tab
wants a line of copy. And **two channels have no screen yet** — see §7.

### 6.6 Findings and overrides — everywhere

```
POST /finding-override { doc:"house"|"plan", id, finding, reason, who }
POST /finding-override { doc, id, finding, clear:true }
```

Findings carry `key` and `can_override`; an overridden one carries `overridden:{reason,who,at}`.
`status.blocking` holds only overrides still in force, `status.overridden` counts the rest, and the
finding is **never removed from `findings`**.

Empty reason → 400. One-word reason → 400.

**Design for this:** the key hashes `level|layer|detail`, so an override attaches to one exact sentence.
When *"0 of 2 RTBs sourced"* becomes *"1 of 2"*, that's a different key and the finding arrives
**un-overridden**. Somebody who accepted the risk at nothing-sourced has not accepted it at one-of-two.
Don't cache the override client-side across a refetch — the expiry is the feature.

### 6.7 Documents out to Word

```
GET /house-docx/{id}[?mode=worksheet]      GET /plan-docx/{id}[?mode=worksheet]
```

**`record`** — what was decided, for circulating. Every chosen line with its source in words (*"from the
brief"*, *"from the signed library"*, *"written here"*, *"MODEL SUGGESTION — traces to nothing in the
brief or library"*), culture tags so `avoid` reads as an instruction not to do something, and unchosen
options in an **"Also considered, and not chosen"** appendix.

**`worksheet`** — the same content to think in. Per layer: **the question** → what's chosen → what was
rejected (inline, because you need it at the moment you're deciding) → **three ruled rows to write in** →
a prompt asking where the new line came from. Plan worksheets add three blank rows **inside the same
table**, so what you write lines up with what's there.

**Both print their own findings.** The export is where the pretence usually happens — blocking findings
stay on screen and a clean Word file goes to the client. And **empty is not zero in print**: `owner
unknown`, `no measure set`, `no date set`, `share unknown`, `failure not named`, `no occasion named`.

`GET /houses` and `GET /plans` return `caveat` + `downloads`. Render the caveat **before** the
start-a-house / start-a-plan action:

```json
{ "headline": "This house lives here, not in the Word file.", "points": ["…4 lines…"], "worksheet": "…" }
```

It says everything is editable, rewriting a model line makes it yours, downloads come in two modes — **and
the download cannot come back in.** Re-import isn't built and is honestly limited: a plan re-imports
cleanly because its layers are Word tables; a house can only ever be *"replace the chosen line, marked
`user`"*, because a Word file can carry the chosen text but not which of five options it was.

### 6.8 Video, social, library, learning, compositor

Unchanged and working. The contracts that matter:

- `POST /scene-still { scene_no, prompt, ratio, characters, seed }` → `{ image_url }`
- `POST /produce-video { scenes, aspect, duration, music, voice, model, note }` → one joined film, plus
  `detail`, `shots`, `seconds`, `audio` — **show those next to the player.**
- `POST /voice-plan`, `/voice-preview`, `/voice-check`, `/voices` — the picker renders the **backend's**
  answer, never the local pick.
- `/library`, `/library-add`, `/library-sign`, `/library-remove` — 12 kinds; nothing generated is ever
  admitted.
- `/learning`, `/learning-context`, `/learning-decision`, `/rescore`
- `/composite`, `/edits`, `/edit-master`
- `/brand-brief`, `/brand-brief-draft`, `/brief-docx`, `/video-script-docx`, `/production-bible-docx`
- `/import-doc` — round-trip in, with `how: "structure" | "interpreted"`

**Every call your file makes now has a route.** I checked both directions.

---

## 7. What I need from you

In priority order.

1. **Wire the four download buttons** — `record` and `worksheet` on both house and plan. `grep` for
   `house-docx|plan-docx` in your file returns **0**, so the whole feature is unreachable.
2. **Render the caveat** from `status.caveat` on the Strategy and Plan index screens.
3. **The idea platform sub-tab** in Strategy — cards with name, idea, mechanic, five test badges; *More
   options* and *Build on this* as separate buttons; five expression boxes; one chosen; write-your-own
   first. Plus the platform strip on the execution header.
4. **Point the override button at `/finding-override`.** It currently writes to client state, which is
   the dismissal rule 8 forbids wearing a reason box.
5. **Two trade tabs** — `own_retail` and `home_delivery` — and a line of copy on the Loyalty tab saying
   it's a lever. Heritage is a daily dairy business with milk booths and subscription; a subscription is
   one decision honoured for months, which is the best retention economics in the whole route to market.
   A trade sheet without it is missing its best channel. Both are live in the backend and raised as
   findings; `outstanding` counts only screened channels so your rail stays honest until you add them.
6. **A live-action shots screen.** Seven routes still have no UI, and this has survived three handovers:
   `/shots`, `/shot-attach`, `/shot-sign`, `/shot-still`, `/shot-recompose`, `/shot-remove`,
   `/composite-upload`. The Compositor works, but the path that gets a **signed** green-screen take into
   a film doesn't exist. `shots.py` returns only signed shots for exactly that reason — the gate is
   protecting a door nobody can reach.

---

## 8. Things not to undo

Each of these was a real bug or a real decision.

1. **The voice picker renders the backend's answer**, not the local pick.
2. **Frames carry a staleness badge.** A still rendered for a 4s beat sitting in an 8s slot is wrong.
3. **A scene whose words can't be spoken says so in red** on the Shoot Board.
4. **Scene counts are a range, not a number** (`sceneRange()`), from duration against Veo's beats.
5. **Nothing the model cannot do is implied to be doable.** No "training" language on the Learning screen.
6. **The pillars in the house diagram never stack above 620px.** A collapsed pair reads as one pillar
   supporting the other, which is a strategic claim made by accident.
7. **Never show a declared split without the actual one.** A single bar is the version of that chart that
   lets a plan lie to itself. Print `basis` verbatim — *"spend unknown — computed on channel count"* is a
   materially weaker claim than a weighted one.
8. **Blocking findings are not dismissible.** Resolved, or overridden with a recorded reason. Never an ✕.
9. **Empty is not zero.** A rate never judged shows *"not judged yet"*, never `0%`. An unknown owner shows
   *"owner unknown"*, never blank — blanks read as settled.
10. **An override never removes a finding from the list.** Annotated and counted, never hidden.
11. **`/execution-rebrief`'s 409 must be shown.** Swallowing it leaves a permanent stale badge with no
    explanation.
12. **`payback unknown` must look different from a number**, and never be dressed to resemble one.
13. **Never interpolate a missing effective price.** An invented marker makes the whole strip unreadable
    because nobody can tell which are real. Plot nothing and say why.
14. **Primary sell-through is amber, always** — even when the rest of the row is fine.
15. **"More options" and "Build on this" are different buttons.** Collapsing them into one "regenerate"
    destroys the exploration record, which is most of what that layer is for.
16. **The `avoid` collision reads as a question, not a verdict.** It's word-overlap. A heuristic dressed
    as certainty gets ignored, and takes the real findings with it.

---

## 9. One fragility worth fixing

Line 33 loads SheetJS from a CDN:

```html
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
```

Every other asset is local and the portal runs from a `.bat` on a laptop, so spreadsheet export silently
stops working offline. Worth vendoring into `api/frontend/`.

---

## 10. Testing

```bash
Start Heritage Studio.bat        # no --reload; restart after any Python change
python tools/checkfe.py          # before every commit touching app.dc.html
python tools/test_tools.py       # 18 tests
```

A house takes about eight decisions to fill, a plan seven, a platform set three or four, a trade sheet
eight channels. **Design the half-finished state** — it's where all of this actually lives.

---

# 11. Contract fix — `options`, `chosen` and `rows` are arrays

**Live now. No frontend change needed — you built this correctly and I returned the wrong shape.**

`status.layers[]` returned counts where you read arrays:

```js
const rawOpts = L.options || …           // got the integer 4
const nOpt = (ls.options || []).length   // (4).length -> undefined -> falsy
```

So the option panel had nothing to map and the rail said *"nothing offered yet"* — while the findings,
which counted the node directly, said *"4 options generated"*. A layer with work in it claiming to be
empty, which reads as data loss.

Now:

| field | shape |
|---|---|
| `status.layers[].options` | the option objects — `{id, text, note, source, tag, added}` |
| `status.layers[].chosen` | the chosen ids |
| `status.layers[].rows` *(plan)* | the actual rows |
| `n_options` · `n_chosen` · `n_rows` | counts, if you want them cheaply |

**Also removed:** the finding *"N options generated, none chosen"*. The rail says it, the cards show it,
and the counts carry it — as a finding it was duplication arriving as a band above the layer somebody was
working in. Findings are for things a person must act on, not for narrating the screen back to them.

My documentation caused this. §6.1 described the node's list of options and the status layer's `options`
with the same word and two different shapes. Fixed above.

---

# 12. Studio Settings — brand and category

**This is the new work.** Everything the studio generates is now grounded in a brand profile
(`GET /brands`), and the profile is backend-only — there is no screen. Four profiles exist; switching
between them needs a `curl`. That is the gap.

## Why this matters more than a settings form usually does

The studio has to answer *"make something pure"* for a milk brand and *"make something that holds"* for a
cement brand without being told which is which. That only works if it knows what the **category competes
on**. Purity is not a Heritage fact — it is the axis of the entire dairy category, the thing every
reason-to-believe argues on and every demo dramatises. Cement's axis is consistent strength. Apparel's is
fit and fabric. Beauty's is efficacy without irritation.

Capture the axis and the studio adapts to the category. Miss it and every output is competent and
generic — which is the one failure that would make the product feel ordinary.

So this screen is not configuration. **It is the input that decides whether the product is any good.**

## The design principle: every field says what it buys

Do not build a long form. Build a form that explains itself — because a field somebody skips is worse
than a field that does not exist. It silently degrades every output downstream and nobody knows why.

Each field carries a one-line *what this buys you*, and the screen shows a **readiness state** rather
than a completeness percentage:

> **Ready to ground copy.** Not ready for the proof gate — add at least two substantiated claims.
> Not ready for a trade plan — name this category's channels.

Readiness beats a progress bar because it names the capability that is missing rather than the boxes.

## The fields, in the order they should be asked

`*` marks the minimum five. With those the model produces category-true, legally-safe, provable work.
Everything else improves it.

### A · Identity

| field | what it buys |
|---|---|
| `name` * | every prompt and every document header |
| `hero_product` | what a film or a pack shot is actually of |
| `category` * | the category frame — what is credible, what is regulated |
| `market` * | occasions, idiom, retail, currency. Prevents generic-global copy |
| `languages` | which languages a script may mix |

### B · The claim space — the *"make something pure"* group

| field | what it buys |
|---|---|
| `category_axis` * | **the most valuable field on the screen.** What this category competes on, in a phrase. Drives every RTB, every demo proposition, every platform mechanic |
| `claims[]` * | `{claim, evidence, verified_by}` — **the proof gate reads this.** Without two substantiated claims every RTB returns flagged unsourced and no execution can be given proof work |
| `substantiation_standard` | what proof this category demands — lab report, BIS certificate, clinical study, none |
| `regulator` | FSSAI · Drugs and Cosmetics Act with CDSCO · BIS · ASCI · Legal Metrology. Decides what may be said |
| `forbidden_words[]` * | *cures · permanent · fairness · guaranteed.* Hard vocabulary bans, checked rather than hoped for |
| `words_we_own[]` | the phrases that make copy sound like this brand rather than the category |
| `mandatories[]` | what must appear on every piece |

### C · The buying situation

| field | what it buys |
|---|---|
| `purchase_cycle` | daily · impulse · replenishment · seasonal · considered · once-in-a-lifetime. Drives phasing **and** the brand/activation split |
| `decider` / `payer` / `user` | three fields, deliberately. In cement the mason decides and the homeowner pays — miss that and the plan is aimed at the wrong person |
| `switch_trigger` | what actually makes somebody change brand |
| `occasions[]` | the real purchase occasions, not the calendar's |
| `price_tier` | mass · mid · premium. Changes both tone and channel |

### D · Route to market — this is what fixes the trade sheet

| field | what it buys |
|---|---|
| `channels[]` | `{name, role, share_now, intermediary, what_they_earn}`. **Five of the eight FMCG channels are wrong outside FMCG** — a cement brand has dealers and sub-dealers, not kirana and dark stores. This field replaces the hardcoded list |
| `influencers_at_purchase[]` | mason · pharmacist · salon · dealer · the platform's algorithm |

### E · Competitive frame

| field | what it buys |
|---|---|
| `competitors[]` | becomes `{name, owns}` — knowing what each has already claimed is what stops us claiming it back |
| `default_belief` | the category belief we are arguing with. Feeds the plan's `believes_now` and the whole current-to-desired shift |
| `unbranded_alternative` | loose milk, the local tailor, the mason's usual bag. Often the real competitor in India |

### F · Craft and codes

| field | what it buys |
|---|---|
| `tone` | voice on every asset |
| `visual_codes[]` | pack cues, colour, iconography — what makes a frame recognisable |
| `never_show[]` | *milk being wasted · unsafe site practice · before-and-after implying a medical outcome.* Enforced at ideation, where it is cheap |
| `colours{}` | the client's palette, kept separate from the studio's |

## What the screen needs

- **A brand switcher**, in the header or in Settings. `GET /brands` lists them, `POST /brand-active {id}`
  switches. Exactly one active — the studio has to know which brand it is working on.
- **Grouped panels A to F**, collapsed by default except A and B. B is where the value is.
- **The readiness strip** above, rendered from `status.readiness`.
- **`claims[]` as repeatable rows**, not a textarea — three columns, `{claim, evidence, verified_by}`.
  An empty evidence cell is a finding, because a claim with no evidence is exactly what the proof gate
  exists to catch.
- **`channels[]` as repeatable rows** too. Seed from a category default where one exists and let the
  author edit — never lock them.
- **`GET /brands` returns `voice` per brand** — the exact text a generator is told. Put it behind a quiet
  *what the model is told about this brand* link. A tool that grounds itself invisibly is asking to be
  trusted rather than checked, and this is the screen where seeing it matters most.
- **Empty is not zero, again.** An unfilled field says what it costs — *"no category axis: RTBs will
  argue on nothing in particular"* — never a blank.

## What I will build before you start

1. The fields above on `brandprofile.py`, with `claims[]` and `channels[]` as structured rows.
2. `voice_block()` extended to render them in order of authority, so the axis and the claim space reach
   every generator.
3. `status.readiness` — the capability list, so the strip has something real to render.
4. The proof gate reading `claims[]`, so a substantiated claim genuinely clears an unsourced RTB.
5. `sales.CHANNELS` falling back to `profile.channels[]` when the profile has them — the taxonomy fix.
6. Filled seeds for all four brands — dairy, apparel, beauty, cement — so you design against real
   content rather than lorem.

Contracts land in this document before you build. Nothing here changes an endpoint you already call.
