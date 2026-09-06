# ASK_DESIGN_57 — POSM asset panel + photoshoot system built directly; two real asks on top

**Frontend file changed substantially since your ASK_DESIGN_56 adoption — verify before touching
anything.** `sha256: 2272f038399c…`, 20,445 lines. I built directly in `app.dc.html` this round rather
than round-tripping through you first, given the pace of live user testing — diff against your own
ASK_DESIGN_56 build before assuming anything, same discipline as always; I'm telling you what changed
so the diff reads as intentional rather than as something to investigate.

## What changed since your last sync (context, not a request — already live and checkfe-clean)

Everything below is built, `checkfe.py`-clean (860/860 `sc-if`, 340/340 `sc-for`, 2795/2795 `<div>`), and
structurally verified on `studio-verify`. None of it has been tested against a real live generation
(needs real API credits + a real approved route — standing limitation this whole thread).

1. **"Assets for this piece" panel** — appears the moment a route is picked, before format selection.
   Pack shot and logo each get a picker over signed-off library items + inline upload. Cast (only for
   `person-in-benefit`/`endorser-with-pack` routes) gets a picker + an AI-draft button + a required
   "Use this — sign it in" approval step (`POST /library-adopt`, new route — see below) before a draft
   becomes usable; the safety-filter risk this manages is named on screen, not hidden. Location gets a
   free-text brief + AI-draft, used directly with no approval step (no gate of its own).
2. **Model photoshoot** — three angle slots (full body / three-quarter / tight crop) on the Cast card,
   each shot FROM the locked cast reference via a new shared primitive (`/studio-shot`, below), each
   independently regenerable.
3. **Auto angle→format mapping** — `produceAdaptations` now reads each format's own `reflow.band`
   (`/posm-adapt` already returned this, nothing new server-side) and picks the matching photoshoot
   angle (`wider→tight`, `taller→fullbody`, `near→threeq`) as that format's `hero_url` instead of the
   one shared hero cut-out, when that angle has been shot. Falls back to the shared hero when it hasn't
   — additive, never required.
4. **"Studio shot" gallery** — the open-ended case: checkboxes to include the locked model and/or pack,
   a free-text action, results in a gallery. For styled pack shots and consumption/usage shots (a model
   with the pack, a pack with a splash) that a plain cutout can't represent.
5. **`POST /library-adopt`** — new route. Takes a generated media URL, saves it into the library under a
   given kind with `source:'generated'` (the honest-labelling half of `library.add()`'s own `source`
   param), signs it off in the same call. The "generate a draft, then approve it" loop's missing piece.
6. **`POST /studio-shot`** — new route, the shared photoshoot primitive behind items 2 and 4.
   `{cast_id?, pack_id?, plate_id?, action, angle?, mode?, ratio?, style?}` → `{image_url, provider,
   mode, refs_used, prompt}`. `mode:'cutout'` (default) isolates on white for compositing;
   `mode:'scene'` renders a complete styled moment. Refuses 400 with no references given at all —
   deliberately not this route's job to hallucinate a subject. Full docstring in `main.py` explains the
   reasoning; worth reading before extending it.
7. One real bug fixed in `/posm-image`'s cast/actor fallback (a stray `break` meant it never actually
   fell back to `actor` when `cast` came up empty) — found while adding the `cast_id` override this
   panel needed.

## 1. Reuse the same combination idea in frame regeneration — the actual new ask

The user's own framing: this shouldn't be POSM-only. `/scene-still` already auto-attaches cast/pack/
plate references (that shipped two rounds ago), so the *backend* half of this mostly already exists.
What's missing is the affordance: a way to explicitly say, on a scene card, "this shot should include
the locked pack" (or a specific consumption-style action) rather than relying purely on keyword
detection in the scene's own description text.

Two shapes worth considering, your call which fits the Scripting/Shoot Board screen better:
- **Lightweight**: an "include pack" toggle per scene card (mirrors the sibling-frame picker you already
  built for continuity) that sets `include_pack:true` on the `/scene-still` call explicitly, bypassing
  the keyword heuristic rather than depending on it.
- **Fuller**: let a scene optionally route through `/studio-shot` instead of `/scene-still` when the
  beat is really a product-interaction shot (the pack held, poured, drunk from) rather than a story beat
  needing continuity with surrounding frames — `mode:'scene'`, `cast_id` from the locked cast, `pack_id`
  from a picker, `action` from what the scene calls for. This gets you real consumption shots inside the
  film, not just in POSM.

## 2. Optional polish, not required

Items 1–4 above were built fast, under live-testing pace, not with a design pass. `checkfe` clean and
functionally wired, but if you see spacing/layout/interaction worth tightening to match the rest of the
app's visual system, go ahead — nothing about the current shape is load-bearing.

## 3. A stretch idea, not a firm ask yet

Letting a "Studio shot" gallery result (a `mode:'scene'` combined shot) be picked directly as a format's
finished master — bypassing the pack/logo/headline compositing entirely for that one piece, since a
scene shot already IS the finished visual, same as `/posm-scene`'s output. Flagging it because it's a
natural next step, not scoping it yet — the picking UX (does it replace the format grid entry, sit
beside it) needs a real decision before it's buildable, not a guess.

## Still open, unrelated to this thread

`require_auth` rollout, SSO/desk confirmations — mine. The measurement ledger (`api/actuals.py`) is
built with no ingest/read screen yet — also mine to scope, not frontend work yet.
