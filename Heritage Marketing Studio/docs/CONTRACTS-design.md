# Contracts — what the UI sends, what it reads

Everything here is what `app.dc.html` actually does today. Where two shapes are listed, both are
tolerated; where a key is marked *optional*, its absence renders a stated empty state rather than a
blank.

---

## `POST /brief-save`

**Sent** (from the brief editor, and from the IMC footer):

```json
{
  "id": "a1b2c3",
  "brief_id": "a1b2c3",
  "brand": "Heritage Foods",
  "title": "Pure Milk — Diwali comms brief",
  "format": "Communications",
  "fields": {
    "status": "Approved",
    "proposition": "…",
    "audience": "…",
    "tone": "…",
    "objective": "…",
    "…": "every other field of the open brief, verbatim"
  }
}
```

- `id` and `brief_id` carry the **same value** and are both null on a first save. Sent together
  deliberately: `/brand-brief-draft` returns `brief_id`, the save route upserted on `id`.
- `fields.status` is `Draft` | `Pending` | `Approved`, set by which button was pressed.
- IMC saves use `format: "IMC"` and put the whole draft object under `fields.draft`, with
  `proposition`/`objective` mirrored to the top of `fields` so pickers can summarise it.

**Read back:** `id` or `brief_id` (either), stored as the upsert key for the next save. Anything else in
the response is ignored. Non-200: `detail` is shown verbatim, nothing on screen changes.

---

## `GET /brief-list`

**Read.** Accepts `{"briefs": [...]}`, `{"items": [...]}`, or a bare array.

Per row, all optional except that a row with none of the title keys renders as *Untitled brief*:

```json
{
  "id": "a1b2c3",
  "brand": "Heritage Foods",
  "title": "Pure Milk — Diwali comms brief",
  "format": "Communications",
  "status": "Approved",
  "updated": "2026-08-12 14:02",
  "fields": { "proposition": "…", "audience": "…", "tone": "…", "objective": "…" }
}
```

Tolerated aliases: `brief_id` for `id`; `brief` for `fields`; `created` or `at` for `updated`;
`smp`, `bigIdea` or `messages` for `fields.proposition`; `commObjective` or `businessObjective` for
`fields.objective`.

`format` drives the two-letter tag and its colour. Known: Communications, Digital, IMC, Media,
Packaging, Product development, PR. Anything else gets its first two letters in grey — no crash, no
lie.

**Unreachable** (404, 501, network) is a first-class state: the picker says the library could not be
reached and shows nothing. There is no client-side sample list.

---

## `GET /learning` — the two keys the Memory panel reads

Everything else on this payload is as before. New reads:

```json
{
  "brands": [
    { "name": "Heritage Foods", "briefs": 3, "active": true, "profile_id": "fbf6b87808" }
  ],
  "briefs": [
    {
      "id": "a1b2c3",
      "brand": "Heritage Foods",
      "title": "Pure Milk — Diwali comms brief",
      "format": "Communications",
      "status": "Approved",
      "updated": "2026-08-12 14:02",
      "no_profile": false,
      "fields": { "proposition": "…" }
    }
  ]
}
```

- `brands[].active` — renders *working on this*. Without it no row can be marked.
- `brands[].briefs` (or `count`) — the count; `0` or missing renders amber *no briefs yet*.
- `briefs[]` — same row shape as `/brief-list`, same aliases.
- `briefs[].no_profile: true` — renders the amber ungrounded warning on that row. `noProfile` also
  accepted.

---

## `GET /brands`

**Read.** Accepts `{"brands": [...]}` or a bare array. Optionally `{"voice": {"<brand name>": "…"}}` at
the top level — or `voice` on each brand object; both are read, the per-brand key wins.

```json
{
  "brands": [
    {
      "id": "fbf6b87808",
      "name": "Heritage Foods",
      "category": "Dairy — milk, curd, and value-added dairy",
      "market": "India, strongest across South India…",
      "master_idea": "Pure Doodh Ki Shakti — the strength of pure milk",
      "positioning": "The purest everyday milk for families who will not compromise",
      "active": true,
      "voice": "BRAND: Heritage Foods\nCATEGORY: …"
    }
  ]
}
```

- Exactly one row with `active: true` is assumed. Zero active renders no selection and the switcher
  shows every row as *Switch* — which is why a fresh install marking its seeded profile matters.
- `category` missing → amber *"No category set — outputs will be category-generic"*.
- `master_idea` falls back to `positioning` for the quoted line.
- `voice` missing → the *what the model is told* toggle is not rendered at all, rather than opening on
  an empty panel.

## `POST /brand-active`

**Sent:** `{ "id": "0fde8d4900" }`

**Read:** `brands[]` (or a bare array) if you return the new list — used directly, so the UI and the
server cannot disagree. If the response has no list, the flag is flipped locally on that id. Non-200:
`detail` shown, and the toast names the brand still active.

Side effect in the UI: the brief library is cleared and re-read, because a library belongs to a brand.

---

## `POST /plan-new` — one added, optional field

```json
{ "brand": "Heritage Foods", "house": "h_1a2b", "brief": "Objective: …\nProposition: …\nAudience: …\nTone: …" }
```

`brief` is sent only when one was pulled from the library, and **the call is retried without it on 400
or 422**. Keep it optional or ignore it; either way nothing breaks.

---

## NEW ASK — `POST /idea-draft`

Powers *Start the platform* on `Strategy → Idea platform`. Optional: without it the card holds the
sources and says the two fields are yours to write.

**Sent:**

```json
{
  "house": "h_1a2b",
  "core": "the chosen core message, verbatim, or \"\"",
  "brief": {
    "title": "Pure Milk — Diwali comms brief",
    "proposition": "…",
    "audience": "…",
    "objective": "…"
  }
}
```

`house` and `core` are null/empty when no house was chosen; `brief` is null when none was pulled. At
least one of the two is always present — the button refuses otherwise.

**Wanted back**, either shape:

```json
{ "name": "Prove It Yourself", "line": "We hand the proof to the person who doubts us…" }
```

```json
{ "idea": { "name": "…", "line": "…" } }
```

- `line` is the only key that matters; without it the response is treated as no route.
- `name` is optional — a missing name leaves whatever the author typed.
- One idea, not a list. If you would rather offer several options the way the house layers do, say so
  and I will build the option cards instead — but then it should return `{options:[{id,name,line,note,
  source}]}` and match the house's card contract exactly.

The drafted line is labelled a first line, not a decision: the five tests below it are what decide
whether it survives, and STEP 2's summary already leads with failures.

---

## `POST /idea-platform` — live, and now carries its source

Corrected: this route exists and the client posts to it on *Adopt this platform*, and reads the
platform back with `GET /idea-platform` on entering the tab (anything unsaved on screen wins, so a
fetch never overwrites a line somebody is mid-way through). The five tests are no longer client-only.

```json
{
  "house": "h_1a2b",
  "plan": "p_9f8e",
  "name": "Prove It Yourself",
  "line": "…",
  "tests": { "true": { "verdict": "holds", "note": "" }, "…": {} },
  "routes": { "social": "…", "posm": "…", "onground": "…", "media": "…", "trade": "…" },
  "source": "model",
  "skipped": false,
  "brief": "a1b2c3"
}
```

- **`source`** is `"model"` or `"user"`. It is `"model"` only while the adopted line is byte-identical to
  what `/idea-draft` returned — one edit to the name or the sentence and it becomes `"user"`. An
  unedited drafted line adopting as the author's would launder it past the sourcing discipline every
  house layer is held to, so your guard should keep flagging it.
- The screen says the same thing: an amber *"the model's line — edit it and it becomes yours"* chip sits
  beside *Standing on* whenever `source` would be `"model"`.
- **`skipped`** now rides along, so the decision persists rather than living as a UI preference.
- **`brief`** is the id of the brief the platform answers (its title when the row had no id), or null.

Read back on `GET /idea-platform`: `{name, line, tests, routes, skipped, source}` — accepted bare, or
under `idea` or `platform`. `source: "model"` is honoured, so a drafted line read back from the server
still shows as the model's until somebody edits it.
