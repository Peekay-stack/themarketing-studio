# ASK_DESIGN_60 — Brand characters, in the Ground Truth room

**Base file**: `api/frontend/app.dc.html`, sha256 `f37998982400cf8db469…`, 23,910 lines. Diff against
whatever you last synced (ASK_DESIGN_58 was the last `app.dc.html` round; 59 was `landing.html` only)
before touching anything — same discipline as always. This file is **LF-only**; keep it that way.

## Context — the backend is already built and verified

`character_skill/SKILL.md` has existed since 7 Sep — the craft guidance for building a recurring,
brand-owned character (a castable face reused across producers until retired, the way a real brand
ambassador is used). This round wires it into the product. **All backend work is done, live and
tested against a disposable tenant** — this ask is the frontend only. No new backend routes are
needed; the twelve below already exist.

New store: `character.py`, tenant-scoped (`tenancy.KINDS` gained `"character"`). One JSON document per
character. The approved *reference frame* lands in the existing reference library as a `cast` item;
this store holds everything around it (pen portrait, visual brief, cast lock, the test record, the
approval).

## Where it goes

The **Ground Truth room** — `isLibrary` screen (`s.screen === 'library'`), the first of Memory's
three rooms. A new panel titled **"Brand characters"**, sitting **immediately after the "Briefs in
memory" card and before the `<!-- add -->` ("Add to the library") card** — i.e. insert between the
closing `</div>` of the briefs panel (~line 1319) and the `<!-- add -->` comment (~line 1321).

Same card language as "Briefs in memory": white card, `#DDD9D1` border, 16px radius, Epilogue 20px
title, a count chip, a one-line explanation. It is the third thing in this room that is ground truth
(uploaded assets, briefs, now characters).

## The character document — what a panel renders

```
{
  "id": "sujatha-ab12cd",
  "brand": "Heritage Foods",          // brand-scoped: never shown for, or usable by, another brand
  "name": "Sujatha",
  "segment": "Modern Traditionalist",
  "segment_source": "segmentation" | "pen-portrait" | "assumed",   // the honest label, test 1
  "scope_note": "Heritage Foods only. Does not cross brands, tenants or campaigns.",
  "state": "draft" | "candidate" | "audition" | "pressure" | "approved" | "retired",
  "version": 2,
  "supersedes": "",

  "pen_portrait": {
    "identity": { "Age": "42", "Lives": "...", "Household": "...", "Role at home": "..." },  // free key:value
    "background": "", "day_in_life": "", "head_goals": "", "heart_goal": "",
    "challenge": "", "context": ""
  },
  "hook": {
    "line": "The unhidden silver streak.",     // nameable in one clause
    "detail": "",
    "prop": "", "prop_load_bearing": false,
    "routes_considered": [ {"tag": "B", "line": "..."}, {"tag": "C", "line": "..."} ],
    "route_selected": "A",
    "route_confirmed": false                    // a person has to confirm the route
  },
  "visual_brief": {
    "type_line": "",                            // the casting Type — energy/presence in one phrase
    "look": "",                                 // age, build, hair, makeup, wardrobe palette, the one detail
    "region": "", "region_load_bearing": false,
    "setting": "", "light": "", "texture": "",
    "expression_range": [ {"expr": "Working neutral", "when": "Default."} ]
  },
  "cast_lock": {
    "never_changes": [ "square jaw", "the mole above the left eyebrow", "..." ],
    "changes_freely": [ "wardrobe", "hairstyle of the day", "setting", "..." ]
  },
  "prompt_craft": {
    "base_prompts": [ {"label": "...", "prompt": "...", "negative": "..."} ],
    "framings_proven": []                       // filled only after the pressure test passes
  },
  "audition":      { "spec": "", "negative": "", "run": false, "passed": null, "note": "" },
  "pressure_test": { "shots": [ {"label": "...", "done": false, "result": ""} ], "run_by": "" },
  "per_producer":  { "social": "", "pos": "", "video": "", "onground": "...", "pr": "..." },
  "hard_lines":    [ "Character, never testimonial. ...", "..." ],
  "open_items":    [ {"item": "The silver streak.", "note": "why it needs validation", "weight": 1} ],

  "tests": {                                    // the six, keyed; each is pass true / false / null (pending)
    "pen_portrait_labelled":     { "pass": null, "note": "" },
    "signature_hook":            { "pass": null, "note": "" },
    "specific_and_presentable":  { "pass": null, "note": "" },
    "holds_across_contexts":     { "pass": null, "note": "" },
    "character_not_testimonial": { "pass": null, "note": "" },
    "brand_scoped":              { "pass": null, "note": "" }
  },
  "reference": { "library_id": "", "candidates": [], "chosen": "" },   // library_id = the signed `cast` item
  "approval":  { "approved_by": "", "approved_date": "", "review_retire": "" },
  "created": "...", "updated": "..."
}
```

**`state` is computed by the backend on every save** — do not set it from the frontend, just render
it. It moves one step at a time: `draft` (portrait + brief written) → `candidate` (hook line +
confirmed route + Type line) → `audition` (turn generated) → `pressure` (multi-context test running)
→ `approved` → `retired`.

## Routes — all live, exact contracts

All are `POST` taking a JSON body unless marked `GET`. All return `{ "character": <the document> }`
on success (so the panel can re-render from one response), or `{ "detail": "<reason>" }` with a 400 /
404 on failure. `who` / `run_by` come from the panel (a text field or the signed-in user's name) —
there is no separate identity dependency.

| Route | Body | Notes |
|---|---|---|
| `GET /characters?brand=<name>` | — | → `{ "characters": [<summary>], "tests": [{"key","label"}] }`. `brand` blank = all. Summary row: `{id, name, brand, segment, segment_source, state, version, hook, route, route_confirmed, tests_passed, tests_total, reference_id, approved_by, updated}`. The `tests` array is the six keys with their human labels, in order — use it for the checklist UI. |
| `GET /character/{id}` | — | → `{ "character", "can_approve": bool, "missing": [<string>], "cast_lock_block": "<text>" }`. `missing` is the plain-language list of everything still blocking approval — render it as the checklist. `cast_lock_block` is the identity-only text a producer will consume; show it read-only on an approved character so a user can see what the producers get. |
| `POST /character-draft` | `{brand, seed, segment?, segment_source?}` | `seed` = a pen portrait or a segment description (free text). Drafts the whole document via the skill; returns a `draft`-state doc, nothing approved, all tests pending. This is the primary "new character" entry. |
| `POST /character-save` | `{character: <full document>}` | Create (blank `id`) or update. Every section is edited in place and sent back whole. Refuses without a `brand` and a `name`. |
| `POST /character-route` | `{id, tag, confirmed?}` | Select + confirm the hook route. `confirmed` defaults true. |
| `POST /character-test` | `{id, key, pass, note?}` | Record one of the six. `key` is one of the `tests` keys above; `pass` is `true` / `false` / `null`. |
| `POST /character-audition` | `{id, run?, passed?, note?}` | `run` defaults true; `passed` is `true`/`false`/`null`. |
| `POST /character-pressure` | `{id, index, done?, result?, run_by?}` | One pressure-test shot by array index. `done` defaults true. |
| `POST /character-reference` | `{id, library_id}` | Point the character at its signed-off `cast` library item. The picker should list `s.library.items` filtered to `kind === 'cast'` **and** `signed_off` — same "not ground truth until signed" rule the rest of this screen uses. |
| `POST /character-approve` | `{id, who}` | **Refused** (400, `{detail}`) unless `can_approve` is true — all six tests pass, the audition passed, ≥3 pressure shots done with a named runner, the route is confirmed, and a `reference.library_id` is set. `who` is required. On refusal, re-fetch `GET /character/{id}` (or read the `detail`) to show `missing`. |
| `POST /character-retire` | `{id, note?}` | Drops it out of what producers may cast. |
| `POST /character-remove` | `{id}` | → `{ "ok": true }`. Deletes the document; the library `cast` item is left untouched. |

## What the panel needs to do

**1. List.** The characters for the active brand (`GET /characters?brand=<activeBrand>`), approved
first. Each as a row/card showing: name, segment + its source tag, a **state pill**
(draft/candidate/audition/pressure/approved/retired — reuse the studio's existing state-pill colours:
grey for draft/candidate, amber while in test, green for approved, muted for retired), the **hook
line**, a **route badge** (`Route A` + a "confirmed" / "unconfirmed" marker), a **tests counter**
`n/6`, and the **reference-frame thumbnail** if `reference_id` resolves against `s.library.items`.
Empty state: a short line + the "Draft a character" action.

**2. Draft a character.** A small form — brand (prefilled to active), name (optional, the skill fills
it), and a textarea for the pen portrait or segment description — → `POST /character-draft` → open
the new document in the detail view.

**3. Detail / edit view.** The full document, section by section, matching the doc shape above. All
text fields editable, saved via `POST /character-save`. Specifically surface:
   - **Hook + routes** — the selected route, the confirm toggle (`POST /character-route`), and
     `routes_considered` shown as "roads not taken" (read-only list is fine).
   - **The six tests** — each with its label (from the `tests` array), a pass / fail / pending
     control, and a note field → `POST /character-test`. This is the spine of the screen; a failed
     test should read as "back a stage, name the test", not a hard stop.
   - **Audition** — the `spec` text (read-only is fine for now), and run / passed / note controls →
     `POST /character-audition`.
   - **Pressure test** — the `shots` list, each with a done toggle + a result field + a shared
     `run_by` → `POST /character-pressure` per shot.
   - **Reference frame** — the `cast`-item picker described above → `POST /character-reference`.
   - **Approve** — a button that calls `POST /character-approve` with a name; on 400, show the
     `missing` checklist inline (do **not** just toast the error — the whole point is the user sees
     what's left). On success the state flips to `approved` and the card moves to the top.
   - **Retire** / **Remove** — secondary actions.

**4. `cast_lock_block`** — on an approved character, show the `cast_lock_block` text from
`GET /character/{id}` in a read-only "What the producers receive" box, so it's visible that the
identity is locked and only scene/wardrobe/expression move per piece.

## Explicitly out of scope this round

- **Generating candidate images or the audition-turn video.** The controls record *whether* the turn
  ran and *whether* it passed; actually calling an image/video model to produce candidates and the
  turn is a later round (it'll reuse the studio-shot / cast-reference primitives). For now `run` /
  `passed` are recorded by a person who ran it elsewhere.
- **Wiring the character into the producers' cast-locks.** That's `prompts.py` (backend) reading
  `character.cast_lock_block()` — not `app.dc.html`, and not this round.
- **`landing.html`** — untouched here.

## Verification

`tools/checkfe.py` clean before and after (it will report the new `sc-if`/`sc-for`/`<div>` counts —
that's expected, note the deltas in your reply). Then load `http://localhost:8000/app`, open Memory →
Ground truth, and confirm: the panel renders with no characters, "Draft a character" produces a
document, the detail view saves, and `/character-approve` shows the `missing` checklist rather than
silently doing nothing.

Base your **next** round on whatever `app.dc.html` this session sends back after adopting this one.
