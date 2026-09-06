# Handover 14 — the backend for round 14 is in. Nine things on your side.

The client tested hard and found nine issues; I found seven more by reading the documents the studio had
actually produced. The backend half of all sixteen is done and verified. This is your half.

Work on the `app.dc.html` you have. **Nothing here needs a new base** — I have not touched the frontend
this round.

---

## First, the three that are actively producing wrong output

### 1 · Send `execution` with every `claude.complete` call  ·  *social is writing for the wrong audience*

The client set an execution's audience to *rival-pack buyer* and got copy written for loose-milk buyers.

Two causes. Yours is small: the social prompt reads `linkedBrief.audience` — the **source brief's**
general audience — when the audience that matters is on the **execution**, which you already hold as
`currentExec()`. Mine was worse: `/complete` had no idea which execution was open, so the spine offered
*all four* audiences from the plan with equal weight and the model picked whichever suited the line it
wanted to write. Nothing in the prompt was false; nothing made the briefed one win either.

**`/complete` now takes an optional `execution`:**

```js
window.claude.complete({ messages, execution: (this.currentExec() || {}).id })
```

That is the whole change. The spine then puts one block last, closest to your instruction:

```
THIS PIECE OF WORK, SPECIFICALLY
  WRITE FOR THIS AUDIENCE, AND NO OTHER: The 25–44 household milk buyer currently buying a rival pack…
  In this channel: Social (Reel/Short, mother POV)
  Serving the functional pillar — not the other one
```

**Measured, same prompt twice.** Without it: *"You check your milk every morning… do the boil test"* —
the loose-milk buyer's ritual, the reported bug. With it: that framing is gone entirely.

Please also drop `linkedBrief.audience` from the prompt text. Two things called "audience" is how this
happened, and the execution's is the right one.

### 2 · Apply the `/plan-row` response  ·  *the plan accuses people of things they have fixed*

Established by test: typing a measure **does** save, the backend **does** drop from 2 blocking findings
to 1, and the screen never hears about it.

```js
editPlanCell = (e) => {
  …
  if (this.state.plan) this.apiCall('/plan-row', { … });   // fire and forget
};
```

No `await`, response discarded. `addPlanRow` three lines below does it correctly. So the finding stays on
screen, the person does the only thing offered — overrides it with a reason — and now an override sits on
a finding that had already resolved itself.

Four asks:

1. **`await` it and apply the returned `status`.** The finding clears as you type.
2. **Debounce 400ms.** It currently POSTs once per keystroke — a 60-character measure is 60 requests.
3. **A quiet `saved` marker on the row.** Its absence is why the client asked for a Confirm button.
4. **Use the counts instead of filtering.** `status` now carries them, so nothing is derived twice:
   ```
   blocking_open: 1 · blocking_overridden: 1 · headline: "1 blocking · 1 overridden"
   ```
   The banner says *"2 BLOCKING FINDINGS — RESOLVE OR OVERRIDE"* on a document with one. Overridden
   findings should stay listed — an accepted risk should not vanish — but stop being *demanded*.

**On the Confirm button they asked for:** I would rather not. A Save button on an auto-saving form is a
lie. What is missing is evidence of saving and a way forward — so the marker above, plus **the same
"Next: <layer> →" control the house has**, on the plan's seven layers. If after both they still want an
explicit Confirm, add it.

### 3 · Nav should return to the open document  ·  *it looks like everything is lost*

Reported as *"I lose everything in the plan and nothing is visible in the house either."*

**Nothing is being lost.** I opened a plan (13 editable cells), went to Strategy, came back to Plan →
landed on the **list**. Re-opened it: 8 cells still populated. `goPlans` and `goStrategy` always set
`screen` to the list, so returning is indistinguishable from having lost the work.

Either return to the open document when there is one, or mark it in the list — *"Heritage · open"* —
so the way back is obvious.

---

## Then the producers

### 4 · POS material  ·  *three routes, and the line is now ON the piece*

**Send `n: 3`.** The backend has always supported it; the panel asks for one.

**The tagline is composited server-side now.** The client was right that POS without a bold line is not
POS, and I was half wrong to refuse. The model still never writes words — it holds the space open, and
`keyline.py` draws the line with a real font at the size the reading distance demands. Verified in
Devanagari: *आज सुबह जाँचा गया* with correct matras, which is exactly what an image model mangles.

`/posm-image` returns **two** urls now:

```
image_url  the piece WITH the line on it        <- show this
plate_url  the same picture without it          <- for artwork
typeset    true when the line was drawn
read_at_m, min_cap_height_pct                   <- why the type is that size
```

The sizing is the sign-industry rule — ~1 inch of cap height per 10 feet of viewing distance — so a
gondola header read at 4m needs **11.1%** cap height where a shelf strip read at 0.4m needs 4.5%. Worth
showing `read_at_m` beside the piece; it explains the type size without anyone having to trust it.

### 5 · On-ground  ·  *ideas now generate, and they are venue-led*

`POST /activation-idea` **with no typed idea now generates** rather than returning 400. The client
reversed the earlier gate deliberately.

```
POST /activation-idea { n:3, steer?, house?, platform? }
  -> { ideas:[…], count, venues:{…}, stands_on:{text,source} }
```

Each idea is eight fields, and they are the point — a vague idea cannot be written into them:

```
name · venue · venue_label · venue_trap
what · who · where · when · how · capture · access · risk
```

**Render `capture` and `risk` prominently.** They are what the BTL research said separates activations
that move numbers from ones that photograph well: *a crowd is not a result*, and *unmanned is furniture*.
A live run gave three ideas across three venues (RWA, office complex, kirana), each answering its venue's
own trap.

```
POST /activation-elements { idea:{…} } -> { elements:[{key,label,spec,why}], keys, venue }
```

**Elements follow the idea, not a fixed four.** RWA returned `van, uniform, education, prop, capture,
leave_behind, permissions`; office complex returned `stall` instead of `van`. Render from `elements`.
`truck` and `permissions` are new.

**Develop now takes the chosen idea object**, which is the fix for *"brief it first"* appearing after an
idea had already been chosen:

```js
apiCall('/activation-element', { element:'education', idea: chosenIdeaObject })   // not a string
```

---

## Then the smaller ones

### 6 · Idea platform — the download and the way onward

```
GET /platform-docx/{set_id}?mode=record|worksheet
```

New. The one document in the spine that did not exist. Two buttons in the header, matching the house and
plan. The five tests print with the verdict **and the reason somebody wrote**, and a verdict with no
reason is flagged.

Also: after the five tests there is no way onward. STEP 3's *Take it to Social →* links may already do
this — please check before building it twice.

### 7 · Lifestyle & culture — group by kind, and label that dropdown

The reported problem: choosing "ritual" and pressing *Offer options* gives more occasions.

**The dropdown belongs to *Write your own*** — it tags the line the person writes and was never wired to
generation. It sits close enough to the generate button to read as a filter. **Please label it** — *"tag
your line"* — or move it.

Generation is now gap-aware on my side: it is told which kinds are already chosen and asked for the ones
that are not. Press *Offer options* twice and you fill gaps rather than repeating.

**Group the options by kind**, exactly as `medium` groups by medium — a heading and a count per kind, so
an empty kind is visible rather than inferred.

### 8 · Project names  ·  *two houses both called "Heritage"*

```
POST /project-name    { house|plan|platform, name }  -> { project, renamed:[…] }
GET  /project-suggest ?house=|plan=                  -> { project, project_source, why, already_named }
```

- **Ask once, at the brief.** Everything downstream inherits it — house from brief, plan and platform
  from house.
- **`houses()` and `plans()` now carry `project` and a ready-made `label`** — `"Heritage · Diwali
  same-day push"`. Use `label` on the cards.
- **`/project-suggest` is a suggestion and is never saved.** Show it with an Accept — a derived name
  written straight to disk is indistinguishable from one a person chose.
- Filenames already carry it: `Heritage_Diwali-same-day-push_messaging-house.docx`.

### 9 · The brand form opens with a wall of text

The client's words: *"Where do I enter the data? It should be like a form where clear information is
asked."* The screen works — 20 inputs render — but it opens with the readiness card carrying **three long
amber paragraphs** before you reach a single field.

Those paragraphs are my `why` text. It belongs **beside each field**, not stacked in front of the form.
Lead with the questions; attach the reason to the one it explains.

Also fixed on my side: the card listed **`category_axis`** — a variable name — under "the five that
matter". `readiness` now carries `core_fields` with real labels:

```
[x] Brand name   [x] Category   [ ] What the category competes on
[ ] What you can prove, and what proves it   [ ] Your real channels
```

---

## Everything new, in one list

```
POST /complete            + optional `execution`
GET  /shots               + `status` (by_stage); every row carries `stage`
POST /activation-idea     no typed idea -> generates; { ideas, venues, stands_on }
POST /activation-elements { idea } -> the element set for THAT idea
POST /activation-element  `idea` may be the whole object
POST /posm-image          + image_url (typeset) / plate_url / read_at_m / min_cap_height_pct
GET  /platform-docx/{id}  new
POST /project-name        new
GET  /project-suggest     new
GET  /brand-fields        + core_fields (labelled)
plan/house status         + blocking_open / blocking_overridden / headline / stranded
```

---

## Before you send

```bash
python tools/checkfe.py && python tools/contract.py && python tools/test_tools.py
```

18/18 here, 153 routes, no collisions.

Two of these were mine misleading you again — `/plan-row` returning a status nobody applied, and the
spine offering four audiences without naming one. If a call behaves oddly, send me the request and the
response rather than working around it; that has been the right call every time so far.

---

## Correction to §8 — the entry field, which I had not built

The client asked where the project is actually *entered*, and they were right to: I built the rename, the
suggestion and the inheritance, and never gave the brief anywhere to hold a name. `new_house` read
`brief["project"]` and nothing ever wrote it, so the chain began at step two and every house was unnamed.

Closed now, end to end:

```
POST /brief-save { …, project: "Diwali same-day push" }
  -> the brief holds it; snapshot() returns `project` and a ready-made `label`

POST /house-new  { brief: <id> }        -> the house inherits it, project_source: "inherited"
POST /house-new  { brief: <id>, project: "…" }  -> overrides it, project_source: "named"
```

Verified through the whole chain: brief → house → plan, and both cards read
`"Heritage · Diwali same-day push"`.

**What you need to build: one field on the brief screen.**

- Label it *Project* — *"What is this piece of work called? Everything you make from this brief inherits
  it."*
- Beside brand and title, not buried. It is the thing that will distinguish two campaigns for the same
  brand a month from now.
- Optional. A brief with no project still works; the cards just fall back to the brand.
- On the house/plan screens, show `label` and offer a rename via `POST /project-name` — the field itself
  is only asked for once.
