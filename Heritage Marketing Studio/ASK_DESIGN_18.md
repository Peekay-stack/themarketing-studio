# ASK_DESIGN_18 — the ladder, and the campaign layer

Backend is built, tested and on this base. **18/18 `test_tools`, 7/7 `checkfe`, `contract` clean, 165
routes, no method+path duplicates.** Nothing below is speculative; every response shape here was printed
from a real run against the Heritage house.

Three screens change. One is nearly free, one is a deletion, one is new.

---

## Why this exists — the problem it fixes

The messaging house holds eight layers of truths **sitting side by side with nothing joining them.**
Nothing says which functional fact licenses which emotional payoff. So a campaign gets briefed on a leap
that no layer records, and nobody can check it.

Heritage is the live case, and it is worth reading because it is not hypothetical:

- Every functional truth in the Heritage house is about **process** — daily checks, cold chain,
  500 professionals.
- The campaign that actually ran stands on **composition** — *"nutrition for a developing child"*, which
  laddered to *"learning matters more than winning."*
- **That truth is not in the house.** The work was built on a fact the strategy never recorded, and no
  part of the system noticed.

The fix is an edge: link a functional truth → a bridge → an emotional truth. That edge then makes three
of the idea platform's five hand-answered tests computable, which is why this round *removes* UI as well
as adding it.

---

## 1 · House screen — a 9th layer, and the ladder view

### 1a. The `bridge` layer (should be nearly free)

`LAYERS` now has **nine** entries. The new one sits between `rtb_functional` and `proof`:

```
id:    "bridge"
label: "Bridges (functional → emotional)"
asks:  "The step between a product fact and a feeling: what the fact MEANS for the buyer. Where a
        bridge divides, write the divisions after a colon — 'Complete nutrition for development:
        cognitive, physical, social'. …"
```

It comes back in `status().layers` with the same shape as every other layer, so the rail, the option
cards, generate, choose and add-option should all work untouched.

**The one thing to fix:** any copy that says **"8 of 8 layers decided"**. It is nine now. Please read the
count from `status().layers.length` rather than hardcoding, because this will happen again.

**Old houses are safe.** `strategy.load()` backfills the missing node in memory, so an existing house
opens with an empty bridge layer instead of throwing.

### 1b. The ladder view (new)

Three columns, and a click builds a path.

```
  FUNCTIONAL TRUTHS          BRIDGES                     EMOTIONAL TRUTHS
  (chosen options from       (chosen options from        (chosen options from
   rtb_functional +           bridge)                     emotional +
   functional)                                            rtb_emotional)

  ● 500 professionals ───┐
                         ├──● Nothing is left to chance ──● I never second-guess
  ● Unbroken cold chain ─┘                              ╲
                                                         ● I made that start possible
  ● Fortified, full cream ──● Nutrition for development:  ╱
                              cognitive, physical, social
```

Everything you need is already on `GET /house` → `status()`:

```jsonc
"ladders": [                      // hydrated — you do not resolve option ids yourself
  { "id": "a1b2c3d4",
    "f": { "id": "...", "layer": "rtb_functional", "text": "500 dairy professionals check…" },
    "bridges": [ { "id": "...", "text": "Complete nutrition for development: cognitive, physical, social",
                   "divides": ["cognitive","physical","social"] } ],
    "e": { "id": "...", "layer": "emotional", "text": "Strong kids, strong mornings…" },
    "axis": ["cognitive","physical","social"] }
],
"ladder_ends": { "from": ["rtb_functional","functional"], "to": ["emotional","rtb_emotional"],
                 "bridge": "bridge" },
"ladder_fragile": ["<emotional option id>", …]      // reached by ONE functional route only
```

`ladder_ends` tells you which options are legal at each end, so please only offer those — the backend
refuses anything else and you can avoid the round trip.

**To link or unlink:**

```jsonc
POST /house-ladder   { "id": "<house id>", "f": "<option id>", "e": "<option id>",
                       "b1": "<bridge option id>",   // optional
                       "b2": "<bridge option id>" }  // optional, second rung
POST /house-ladder   { "id": "<house id>", "drop": "<ladder id>" }
→ { "house": {…}, "status": {…}, "detail": "Path recorded — that feeling now has a fact under it." }
```

Errors come back **400 with a sentence to show**: *"That functional truth is not in this house."*,
*"That path is already recorded."*

**Two things worth showing in the UI:**

- **Badge the `ladder_fragile` emotional truths.** One functional route means a competitor matching that
  single fact takes the whole campaign with it. Amber, not red — it is a risk, not an error.
- **Show `divides` on a bridge chip.** A bridge that divides is what gives a campaign its grid, so the
  three little words are worth surfacing. A bridge with no divisions is fine; it just yields one column.

**The colon matters and is worth a hint in the field.** Divisions are **declared, never inferred from
prose** — I tried parsing them and it was confidently wrong in both directions (given *"nutrition for
cognitive, physical and social development"* a comma split loses `cognitive` into the lead-in and returns
`social development` with the noun attached). The axis decides a whole campaign grid, so it asks instead
of guessing. `"…development: cognitive, physical, social"` works; a bare `"cognitive, physical, social"`
works; prose returns nothing and a finding says so.

### 1c. Five new findings

All computed, all arriving in the existing `findings` array with `layer: "bridge"`. No new UI needed —
they render wherever findings already render. For reference:

| level | when |
|---|---|
| blocking | a chosen emotional truth has no functional route — unlicensed |
| blocking | a path points at options that have been deleted |
| open | a chosen functional truth ladders up to nothing — a spec-sheet line |
| open | an emotional truth reached by one route only — fragile |
| open | a bridge that does not divide — no proof axis, so every execution repeats |

---

## 2 · Idea platform — five test columns become two

**This is a deletion. Please remove three, do not hide them.**

`ideas.JUDGED` now has **two** keys: `ours` and `durable`. The other three are **absorbed, not dropped** —
that distinction matters because the questions were good and the answers are now structural:

| retired | where it went |
|---|---|
| `true` — *"does it stand on something in the house?"* | **Computed.** A platform bound to a ladder path stands on something by construction. |
| `elastic` — *"does every channel get something to do?"* | **The campaign's role table**, which names what each medium *does* rather than asking whether it has anything. |
| `tension` — *"is something being resolved?"* | **Moved down to the campaign.** `insight` is a required field there. A platform lasts years and does not itself argue; a campaign does. |

`GET /idea-platform` now carries `retired_tests` — a `{key: where_it_went}` map — if you want a one-line
explanation for anyone who remembers five columns.

**What to change in `app.dc.html`:**

- The hardcoded test array at **~line 9692**: remove the `true`, `tension` and `elastic` rows.
- All the `elastic` special-casing — **~9713** (the toast), **~9721** (derived verdict from route count),
  **~10875–10877** (`cursor: default`, the *"n of 5 routes written"* hint). This removes complexity
  rather than adding it: `elastic` was the one test that was never clickable.
- **~11097**: the routes-panel copy that says *"this is also what the elasticity test is reading"* — no
  longer true.
- Anything that says **"five tests"** or **"n of 5"**.

Please render the columns from the response's `questions` object rather than the local array, so the next
change to this set is a backend change only.

**A person's existing verdicts are safe.** `verdicts` is stored unfiltered, so a retired answer stays in
the file even though the column is gone. Only the *model's* reading of a question nobody asks any more
falls away.

---

## 3 · Campaign panel — new, under the adopted platform

A campaign is the **time-bound** expression of a platform: one route up the ladder, one tension, one
resolution, between two dates. Stored as a child of the platform, so it cannot orphan itself.

It only exists once a platform is adopted. `POST /campaign` returns 400 with the sentence to show
otherwise.

### The fields

| field | control | notes |
|---|---|---|
| `name` | text | **required.** The two or three words a room repeats. |
| `insight` | textarea | **required.** The tension. Hint: *"Not a demographic. 'Mothers 25–40' is an audience; 'she feels the pressure of his growth more than anyone' is an insight."* |
| `resolution` | textarea | What the work tells them. *"Learning matters more than winning."* |
| `shape` | 4-way picker | `frame` · `device` · `rule` · `act` — descriptions in `status().shapes` |
| `frame` | text | The device itself. For `frame`, contains a slot: `"{X} ki Shakti, Pure Doodh Se"` |
| `slots[]` | repeater | `[{text, lang}]` — the conjugations. **`lang` is the point:** localisation, not translation. Heritage runs `Seekhne` (hi) and `ప్యూర్ పాల` (te) off one frame. |
| `ladder` | picker | A ladder id from the house. Prefilled from the platform's own `ladder`. |
| `roles{}` | table, prefilled | one row per medium — see below |
| `from` / `to` | dates | |

**The four shapes matter.** Do not build a form that assumes `frame`. A sentence with a slot is one shape
of four — Amul's topical girl is a **device**, *"Daag Acche Hain"* is a **rule**, *"Meet Your Farmer"* is
an **act**. A tool that only knows frames will force every brand into a fill-in-the-blank and produce
mad-libs. `status().shapes` carries a sentence explaining each; please show it on the picker.

### The roles table

Eight media: the house's seven plus **`influencer`** (a role no owned medium can play). Prefilled from
`status().role_defaults`:

```jsonc
"role_defaults": {
  "tv":         { "role": "emotional endpoint + the turn",
                  "why": "The only medium with time and narrative, so the only one that can RESOLVE a tension…" },
  "influencer": { "role": "emotional endpoint, third-party", "why": "…credibility, never construction…" },
  "on-ground":  { "role": "the bridge, experienced",  "why": "She does the thing, so the bridge stops being a claim…" },
  "social":     { "role": "the bridge, demonstrated", "why": "…" },
  "digital":    { "role": "the bridge, demonstrated, at high intent", "why": "…" },
  "posm":       { "role": "functional truth + emotional RECALL",
                  "why": "Two metres, two seconds. It cannot build emotion, only trigger emotion something else built…" },
  "ooh":        { "role": "one rung, chosen", "why": "Three seconds at distance. Pick the functional truth or the code, never both." },
  "trade":      { "role": "OFF the consumer ladder entirely",
                  "why": "The retailer has his own ladder: margin, rate of sale, working capital…" }
}
```

Editable, and the `why` belongs in a tooltip — it is the reasoning, and a role someone overrides having
read it is a decision rather than an accident.

### The grid

`GET /campaign-grid?house=…&id=…` → the campaign on a page. **Proof axis across, media down.** Computed,
never stored — the axis is read off the bridge, so the house decides the grid, not this screen.

```jsonc
"grid": { "axis": ["cognitive","physical","social"],
          "slots": ["Seekhne","Khelne","ప్యూర్ పాల"],
          "columns": 3, "media": 8, "cells": 24,
          "rows": [ { "medium": "tv", "role": "emotional endpoint + the turn",
                      "why": "…", "columns": ["cognitive","physical","social"] }, … ] }
```

**Cells hold nothing in this version** — the value is showing which combinations exist. An empty column
is a dimension nobody is proving; an empty row is a medium with nothing to do. Do not build cell editing
yet; if it turns out to be wanted, it needs a storage decision first.

When the bridge does not divide, `axis` is `[]` and `columns` is 1 — render one undivided column and show
the finding beside it.

### Requests

```jsonc
GET  /campaign                       // bare, resolves like every other platform route
GET  /campaign?house=…&id=…
POST /campaign  { "house": "…", "name": "…", "insight": "…", "resolution": "…",
                  "shape": "frame", "frame": "{X} ki Shakti, Pure Doodh Se",
                  "slots": [{"text":"Seekhne","lang":"hi"}, {"text":"ప్యూర్ పాల","lang":"te"}],
                  "ladder": "<ladder id>", "roles": {…}, "from": "2026-09-01", "to": "2026-12-31" }
POST /campaign  { "house": "…", "drop": "<campaign id>" }
```

`GET /campaign` **answers with no arguments** — it resolves by set, then house, then most recent. Please
call it bare on load. (The idea platform screen shipped a hydration path that never ran once because the
route demanded an id; this one does not have that failure mode, so please use it.)

Campaigns also ride along on `GET /idea-platform` as `campaigns[]`, so the platform card can show a count
without a second call.

### Findings

Six, in `status().findings` with `layer: "campaign"` and a `campaign` id. All verified firing:

```
[blocking] Thin names no ladder path — so nobody can say which fact licenses it…
[blocking] Thin ends before it starts.
[blocking] …stands on a ladder path that no longer resolves in the house
[open]     …states a tension and not what the work tells them
[open]     …is a frame with fewer than two slots filled — a frame not conjugated twice is a tagline
[open]     …gives no role to: trade
[open]     …tv and posm are given the same role — one is repeating the other
[open]     …has 1 slot(s) against a 3-part proof axis (cognitive, physical, social)
```

---

## What NOT to do

- **Do not store the proof axis or the grid.** Both are computed. A second copy of a house decision is
  this project's recurring bug — the SMP-vs-core split and the green-vs-blue clash are both that.
- **Do not add cell editing to the grid** without asking; it needs a storage decision.
- **Do not hide the three retired tests.** Remove them. A greyed-out column teaches people the form is
  theatre.
- **Do not build the campaign form assuming `frame`.** Four shapes.
- **Do not let a campaign invent a ladder path** the platform does not stand on. The picker should offer
  the platform's path and the house's other paths, and the finding fires if it names none.

## Questions back to me

1. Does the ladder want to live **inside the house screen as a 9th layer view**, or as its own tab? I
   built it as layer data so either works, but the three-column linking UI is not shaped like the other
   layers' option-card UI, and forcing it into that pattern may be wrong.
2. The campaign panel — **under the adopted platform on the Idea Platform screen**, or its own screen? It
   is a child of the platform in the data, which argues for the former, but it has nine fields and a grid.
3. Is `influencer` wanted in the **house's** medium layer too, or only as a campaign role? I kept it out
   of `strategy.MEDIA` deliberately to avoid churning a screen you just shipped.
