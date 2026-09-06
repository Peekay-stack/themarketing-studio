# ASK_DESIGN_24 — the film craft surface: the cut editor, the grade, the sound, the gate

The whole film-craft backend is built. This is the screen work for it — held back deliberately until
there were **three real edit types** to demonstrate the flow against rather than one abstract manifest.

## Build on the file in this zip

```
app.dc.html      973,564 bytes
sha256           18109046c314343ec65a61cea06173ab74fe7b85748478a56720d9b2aae41bbe
```

**This is NOT the base you last returned.** Three defects were fixed in your round-20/21/22 return after
it landed, all in this side's remit (bindings and payload mismatches, not design decisions):

| what | why it needed fixing |
|---|---|
| the house-card claim badge | `hasClaim`/`claimLabel`/`claimBg` etc. were computed in `houseCards` but **no `<sc-if>` in the card template ever referenced them** — zero badges rendered on the house list. The opened-house header badge was wired correctly; the list card was not. |
| `sGoTab('idea')` | called `loadIdea()` but not `loadCampaign()` — so reaching the Idea Platform tab via the Strategy sub-nav (the direct route) left STEP 4 unhydrated after a page reload. `goIdeaPlatform` called both; this one didn't. Pre-existing, not something round 22 introduced. |
| `divisionsText` hydration | `loadCampaign()` spread `{...campaign(), ...got}`, and `got` only ever carries `divisions` (never `divisionsText`) — so the default `''` survived every merge and `'' != null` picked it every time. The field read blank on **every** load path, not just the one above. |

Also new on the backend since your last base: `claim_state` now arrives on `/houses` list items and
`/house-new` too, which was the open question you flagged — you were right that it wasn't there.

`tools/checkfe.py` is in the zip. Run all seven before sending back.

---

## What NOT to build

**Do not build a "generate the film" button anywhere in this.** Every route below operates on a cut that
already exists. Generation is the existing film pipeline and is untouched.

**Do not add a slider for grade or sound levels.** Both are named sets (`GET /grade-status`,
`GET /sound-status`) for the same reason POSM formats and activation scales are: a named look is a
decision somebody can hold an opinion about; a number from 0–1 is not.

**Do not upload ambience or foley from these screens.** They go through the existing library upload,
like every other piece of ground truth. These screens *choose* from what is signed off, and say so
plainly when nothing is.

---

## 1 · The cut editor — the core of it

A cut is the approved film as an **addressable manifest**, not a rendered file. The whole point is that
**the cost of an edit is visible before anything re-renders.**

```
GET  /cut/{execution}      → { cut: {id, execution, versions:[…]}, summary: {…} }
POST /cut                  → start a cut's history  { execution, beats:[…], tracks?, grade?, master_url? }
POST /cut-propose          → what an edit WOULD cost. Writes nothing.
POST /cut-commit           → create version n+1
POST /cut-approve          → { execution, who, version? }
```

A version looks like:

```json
{ "version": 2, "parent_version": 1,
  "beats": [{"n":1,"role":"hook","shot_id":"","clip_url":"…","seconds":4.0,"super":""}],
  "tracks": {"voice_url":"","music_url":"…","ambience_url":"…","spots":[{"url":"…","at":1.5}]},
  "grade": "warm-dawn", "master_url": "/renders/…", "scored_url": "/edits/…",
  "approved": {"who":"Ananya","at":"…"} ,
  "diff": {"changed":[1,3],"unchanged":[2],"added":[],"removed":[]},
  "class": "free" }
```

### The one screen that matters: propose before commit

`POST /cut-propose` with the edited beats returns an `edit` object and **writes nothing**:

```json
{ "class": "free", "why": "beats reordered, retimed or re-captioned — same clips, re-cut",
  "cost": "no render — a re-cut from clips already on disk",
  "diff": {"changed":[1,3],"unchanged":[2],"added":[],"removed":[]},
  "audio_changed": false, "grade_changed": false }
```

`class` is one of five, and **this is the thing to put in front of a person before they commit**:

| class | means | show it as |
|---|---|---|
| `none` | nothing this manifest tracks changed | nothing to do — disable commit |
| `free` | reorder, retime, new super, re-grade, cutdown | free — no render |
| `audio` | tracks changed, picture untouched | an audio pass |
| `one-clip` | named beats need a new render (`why` lists which) | N clips re-render, the rest stay byte-identical |
| `full` | cast, location or plate changing | **a new film, not an edit** |

**The ask:** a beats list on the Video screen (reorder, retime, edit the super per beat), and a
**"what will this cost" line that updates from `/cut-propose`** as the person edits — then a commit
that fires `/cut-commit`. The `full` class deserves to look different from the others: a client asking
to "try a different mother" is asking for a new film, and that should read as a warning, not a button
that quietly costs the whole budget. Pass `trigger: "cast" | "location" | "plate"` on propose/commit
when that is what the person is actually asking for — the beat diff cannot see it.

Show `diff.unchanged` explicitly. "Beats 1, 2, 4, 5 unchanged" is what lets a change be signed off
without re-approving the whole film.

## 2 · The grade

```
GET  /grade-status   → { grades: { neutral|warm-dawn|cool-clean|rich-contrast: {label, what} } }
POST /cut-grade      → { execution, grade }  → applies it, commits the next version
```

Four named looks with a `what` sentence each. `neutral` is a real pass-through, not an absent value.
Returns `master_url` for the newly graded file plus the usual `edit`/`summary`. **The ask:** a picker
rendered from `/grade-status` (never a hard-coded list), showing each `what`, applied to the whole
master in one pass. `400` on an unknown name lists the valid ones.

## 3 · The sound

```
GET  /sound-status  → { music_levels, ambience_levels, ambience_default, sfx_gain, library:{ambience[],sfx[]}, why }
POST /cut-sound     → { execution, ambience?, ambience_level?, music?, music_level?, spots?:[{url|id, at, gain?}] }
```

Two new library kinds: **`ambience`** (a bed under the whole film — room tone, a yard at dawn) and
**`sfx`** (a spot at one moment — a clank, a pour). The level hierarchy is deliberate: **ambience under
music under voice**, because room tone is meant to be believed rather than noticed.

`library.ambience` / `library.sfx` list only **signed-off** items. When both are empty, `why` explains
it — *"Ambience and foley are uploads, not generations — no model here knows what a dented steel can
sounds like on concrete at 5am."* **Show that sentence rather than an empty picker.** This is the
department a generated film is worst at and it carries most of what "real" feels like, so the absence
is worth stating.

**The ask:** an ambience picker (from the signed list) with its level, and a foley list where each row
is *a sound + a time in seconds*. `spots` accepts a library `id` or a `url`, so send ids. A spot placed
past the end of the cut comes back as a note in `detail` — surface it, because a spot that never plays
is otherwise indistinguishable from one nobody added.

## 4 · Continuity and the viability gate — two small, high-value panels

```
GET  /continuity-status  → { has_cast, has_plate, refs[], kinds[], cast, plate, why }
POST /shot-viability     → { shots: [str] }
```

**Continuity.** Cast identity travels as a reference image and always has; **place did not travel at
all** until now — the `plate` library kind existed since the library existed and no code path read it.
`/scene-still` now auto-attaches the signed cast *and* plate (client-supplied refs still win, and come
first). Show `why` when either is missing: *"no signed-off plate — each shot will invent its own
location and light, which is what makes separate renders read as separate films."*

**The viability gate.** Post the shot list, get back per-shot risks with advice:

```json
{ "shots": [{"n":2, "shot":"Ramesh speaks to camera…", "ok":false,
             "risks":[{"risk":"lip sync","advice":"Spoken dialogue on camera. Lip sync is the single most reliable tell…"}]}],
  "flagged": 5, "count": 7, "summary": "5 of 7 shot(s) ask for something a model reliably gets wrong.",
  "note": "Advice, not a refusal — a flagged shot may still be the right shot." }
```

Five risks: `lip sync`, `fine hand work`, `crowd of faces`, `on-screen text`, `complex camera move`.
**Render `note` next to the flags.** This refuses nothing — a flagged shot may still be the right shot,
and a gate that reads as a block will be worked around instead of read.

## Verify on your end

- `/cut-propose` on an unchanged cut → `class: "none"`; commit should be disabled, not an error.
- The `full` class rendering — confirm it does not look like an ordinary confirm button.
- `/sound-status` with an empty library → the `why` sentence shows, not an empty dropdown.
- `checkfe.py`, all seven.

## Verified on this end before this was written

Every route exercised over real HTTP against a running server with real files, not sample payloads.
Highlights: all five edit classes confirmed, including the reorder case (which the first implementation
got wrong — it classified a reorder as needing two new renders, because it compared beats
position-for-position instead of asking whether a clip existed anywhere in the parent); a real
ffmpeg-graded master written and its signal stats checked to confirm each grade shifts hue and contrast
in the direction its own description claims; a real 4-track sound mix (music + ambience + 2 foley
spots) with the level hierarchy confirmed ~15 dB apart, and the `has_voice` fix proven behaviourally
rather than by inspection; the viability gate run against seven realistic Heritage shots, flagging all
five failure modes and passing the two that play to the model's strengths. 18/18 `test_tools.py`,
`contract.py` clean, **181 routes**, page loads with only the four pre-existing SVG placeholder
warnings, and every test artifact removed — library, renders, edits and the tenant tree all restored
byte-identical.
