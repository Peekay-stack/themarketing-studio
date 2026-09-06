# ASK_DESIGN_56 — three frontend gaps behind already-shipped, already-verified backend work

**Frontend file: unchanged since round 58 — `sha256: 2b5d71db9bcc…`, still your own last file.** Rounds
59–60 were entirely backend (`api/main.py`, `api/posm.py`, `api/library.py`, `api/tenancy.py`, two new
files `api/actuals.py` + `api/keyvisual.py`). Nothing to merge this time — build directly on top of
what you last shipped.

All three items below are real user-testing findings, not speculative asks. Every backend route named
is already live on the server and tested directly against it (unit tests plus real HTTP calls) — nothing
here is waiting on me. **Ship item 1 first** — it's blocking the user from testing POSM at all right now.

## 1. Inline cast/pack/logo upload in POSM — build this first

**What happened**: user tried to generate a `person-in-benefit` POSM hero and got a refusal telling them
to "Upload the approved frame under Library → Cast (or Actor) and sign it off" — with no way to actually
do that from the POSM screen. They have to leave entirely, go to Memory → Ground truth, find the right
chip among 14, upload, sign off, and come back. Their own words: *"there is no field to input this??"*

This is also inconsistent with how Video Studio already solves the same class of problem: its cast lock
generates a reference inline, in that screen, no trip to Library required. POSM has no equivalent.

**The refusal already tells you exactly what's missing** — nothing new to compute, just read the shape:
```
409 { "detail": "...",
  "gate": { "can_render_assets": bool, "can_assemble_master": bool,
    "blocks":       [ { "kind": "pack"|"logo", "what": str, "do": str } ],
    "asset_blocks": [ { "kind": "cast",        "what": str, "do": str } ],
    "pack":  { "count": int, "url": str },
    "logo":  { "count": int, "url": str },
    "cast":  { "count": int },
    "note": str } }
```
`blocks`/`asset_blocks` is the actual list of what's missing, in the order to show it.

**Ask**: when a POSM generation call (`/posm-image`, and the new `/posm-scene` below) comes back 409 with
one or more `gate.blocks`/`gate.asset_blocks` entries, render an inline uploader right there — one per
missing `kind` — instead of just the text. Three existing, unchanged, already-live routes do the whole
job:
- `POST /library-add` — **multipart form**, not JSON: fields `kind` (the missing kind string, e.g.
  `"cast"`), `files` (the chosen file(s)), optional `name`/`note`/`tags`/`who`. Returns
  `{added:[{id, url, kind, signed_off:false, ...}], detail, summary}`.
- `POST /library-sign` — JSON `{id, on:true}`. Returns `{item, summary}`. Call this immediately after a
  successful add — signing off in the same flow is the whole point, not a separate later step the person
  has to remember.
- Then retry the original POSM call that got refused.

**One thing worth knowing, not a frontend bug**: this account already has two `kind:"actor"` items sitting
unsigned since 13 Aug (`take-1`, `take-2`). I checked the actual files — 70 bytes each, literal 1×1 pixel
PNGs, dead test stubs from early development, not real photos. If you're testing against this tenant's
real library and wondering why "Actor" already shows 2 unsigned items, that's why. Not something to
silently clean up from this ask — the user has the existing "Remove" control for that whenever they want.

## 2. Sibling-frame reference for storyboard continuity

**What happened**: Scene 4 (a continuation of Scene 1's exam-hall setting) came back with people facing a
different direction than Scene 1 — nothing in the pipeline enforces blocking/orientation continuity
between two shots that are supposed to be the same physical scene.

`/scene-still` already accepts a **`reference_urls`** array (plural) — this is not new, it's the same
channel the backend's own cast/pack/plate auto-references already travel through. **But the frontend has
only ever sent the singular `reference_url`** (`generateFrame`, one string, the cast reference) — never
the array form, so there's currently no way to send more than one reference image at once.

**Ask**: on a scene card, add a lightweight "match this to another shot" control — a dropdown or small
thumbnail row of this script's already-approved frames — that lets a person pick an earlier scene to
match blocking/orientation against. When set, switch `generateFrame`'s payload from
`body.reference_url = castRefUrl` to `body.reference_urls = [castRefUrl, chosenSiblingUrl].filter(Boolean)`
(array form) for that call. No backend change needed — the endpoint already reads either shape, and
already manages the 3-image cap by dropping least-load-bearing first, so this is additive on top of the
cast/pack/plate it already attaches automatically.

## 3. Wire the real assembled POSM output — two new routes, plus the two-lane switch

**What happened**: `/posm-image`'s own response text has said all along — *"mask it out of the white and
place it on the flat brand-colour field with the pack, the type and the brand block"* — but nothing ever
did that. `produceAdaptations()` just shows the raw, isolated hero cut-out as if it were the finished
piece, for every format. Round 60 built the actual missing step.

Three pieces, all live and tested, none wired into any screen yet:

- **`POST /posm-backdrop`** — `{brief, format?, style?}` → `{image_url, provider, prompt}`. Generates a
  plain, subject-free environment (a green pitch, a home kitchen — whatever the route needs) for the hero
  to be composited onto. Refuses `409` on a paintable format (see the mode switch below), naming the
  reason, same shape as every other refusal in this app.
- **`POST /posm-assemble`** — `{hero_url, format, headline?, type_position?, backdrop_url?, field_hex?,
  pack_url?, logo_url?}` → `{image_url, format, type_position, pack_used, logo_used}`. Takes the hero
  cut-out `/posm-image` already returns and actually composites it — background, a pack card, real
  rendered headline type, the logo — into one PNG. `pack_url`/`logo_url` default to the brand's
  signed-off/on-file assets when omitted, so this works even if you pass neither.
- **`POST /posm-scene`** — `{brief, format, headline?, cast_ids?:[id,...], pack_id?, style?}` →
  `{image_url, provider, refs_used, has_cast, note}`. The other lane, for creative a cutout can't
  represent: one generated image with people, environment, product, headline and logo all baked in
  together (a family/group scene, an occasion piece). `cast_ids` lets several library entries stand for
  several different real people (capped at 3 total references, shared with the pack). **`has_cast:false`
  in the response means no real photo was available to pin identity to — show that note to the person,
  don't hide it or imply the scene used a real reference when it didn't.**
- **`/posm-image` now also returns `mode` (`"paintable"|"rich"`) and `mode_why`.** The format itself
  decides by default (a wall painting is hand-painted, so it comes back `"paintable"` and the backend
  already forces flat/spot-colour art regardless of what style was requested) — this is what should back
  the two-button switch: default the buttons to whichever `mode` came back, let a person override by
  resending the same call with an explicit `mode` field (`"paintable"` or `"rich"`).

**Ask**: replace `produceAdaptations()`'s "show the raw cut-out as the finished tile" with a real call to
`/posm-assemble` (cutout lane) or `/posm-scene` (integrated-scene lane — whichever the chosen route/hero
type calls for), and surface the paintable/rich mode switch above the format grid, defaulted from
`/posm-image`'s own `mode` field.

## Still open, none of it frontend

`require_auth` on the ~150 live routes, SSO/desk confirmations, and the measurement-ledger ingest UI
(the store itself, `api/actuals.py`, is built — no screen reads or writes it yet, and that's mine to
scope next, not yours).
