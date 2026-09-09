# Handover — ASK_DESIGN_60: Brand characters panel

**File**: `app.dc.html` (frontend only, per the ask — no backend changes).

## What was built

New panel **"Brand characters"** in the Ground Truth room (Memory → `isLibrary` screen), inserted
between the "Briefs in memory" card and the "Add to the library" card, matching that card's visual
language (white card, `#DDD9D1` border, 16px radius, Epilogue 20px title, count chip).

### List view
Each character row shows: name (or an initial avatar if no reference frame yet), a **state pill**
(grey draft/candidate, amber audition/pressure, green approved, muted retired), segment + its source
tag, the hook line, a tests counter (`n/6`), a route badge with confirmed/unconfirmed marker, and the
reference-frame thumbnail when `reference_id` resolves against `s.library.items`. Empty state renders
a short line above the draft form.

### Draft a character
Name (optional) + pen-portrait/segment textarea → `POST /character-draft` → opens the new document in
the detail view immediately.

### Detail / edit view
All sections from the doc shape, editable in place, saved via `POST /character-save`:
- Name, segment, segment source (select)
- Pen portrait: identity key/value rows (dynamic from whatever keys the doc has) + background, day in
  life, head goals, heart goal, challenge, context
- Hook & route: line, detail, prop (+ load-bearing toggle), routes considered (read-only "roads not
  taken"), route-select buttons + confirm toggle → `POST /character-route`
- Visual brief: type line, look, region (+ load-bearing toggle), setting, light, texture, expression
  range (read-only list)
- Cast lock: never-changes / changes-freely as line-per-item textareas
- **The six tests** — pass/fail/pending per test + note → `POST /character-test`
- Audition — passed/failed + note → `POST /character-audition`
- Pressure test — per-shot done toggle + result, shared run-by → `POST /character-pressure`
- Reference frame — picker over `s.library.items` filtered to `kind==='cast' && signed_off` →
  `POST /character-reference`
- Approve — name field + button → `POST /character-approve`; on refusal, re-fetches
  `GET /character/{id}` and renders the `missing` checklist inline (not a toast)
- `cast_lock_block` shown read-only once approved
- Retire / Remove

### Wiring
- `loadCharacters()` (`GET /characters?brand=<active>`) fires alongside `loadLibrary()` /
  `loadLearning()` whenever the Library screen is entered.
- `openCharacter(id)` (`GET /character/{id}`) drives the detail view, including `can_approve`,
  `missing`, `cast_lock_block`.
- All 12 routes from the ask are called; state pills, route/test/pressure semantics follow the doc
  exactly. `state` is never set from the frontend — only rendered from what the backend returns.

## Known simplifications (flagged, not hidden)
- `expression_range` and `routes_considered` are read-only lists (per the ask's own allowance for
  routes considered; extended the same treatment to expression range for time).
- `identity` supports editing existing keys; there's no "add a new key" control yet.
- No image/video generation controls — out of scope per the ask.

## Verification
Loaded clean in preview, no console errors. `tools/checkfe.py` was not run in this environment — run
it against your local checkout before merging; expect new `sc-if`/`sc-for`/`<div>` counts from this
panel.

## Next round
Base ASK_DESIGN_61 on this file. Likely candidates: identity key add/remove, wiring the character
picker into producer cast-locks (flagged explicitly out of scope this round), or the audition/pressure
generation controls once the image/video backend lands.
