# ASK_DESIGN_25 — the continuity check (and what changed in your round-24 return)

**The only thing to BUILD here is §3, the continuity check.** Your round-24 return already covered the
beat plan and the cutdown — you built both from the addendum note before it was formally sent, and both
are verified working against live data. They are kept below as §1 and §2 for reference only, marked
DONE; read them for the two render notes, not as an ask.

## Build on the file in this zip — NOT on your round-24 return

```
app.dc.html      1,014,921 bytes
sha256           259271ed580619cfa063ade5407ebe5c78f61a4541ba3e3406c9810227a0e6ed
```

Your round-24 return landed and is integrated. Base was confirmed byte-identical to what you were
given, and nothing on this side had touched the frontend since, so nothing was reverted. checkfe
**7/7**, including the seventh check you can't run.

**Four defects were fixed in it after it landed** — all four in this side's remit (bindings, payload
shapes, escapes), none of them design decisions. All four passed checkfe, passed contract, and threw no
console error; three were only findable with the screen open and real data in it.

| what | why it needed fixing |
|---|---|
| `hasCut` in `craftVals` → **`hasCutManifest`** | The Film tab already owns `hasCut` (`prod.versions.length > 0`) **later in the same object literal**, so it won. With a cut on disk and no film produced that session, `noCut` was false *and* `hasCut` was false — both branches off, so the **entire cut editor rendered as nothing**. It reads as an empty card, not as a fault. Exactly the collision you caught with `setMusicLevel` → `setCutMusicLevel`, but on a bag KEY — which checkfe's unique-class-members check does not cover. |
| `cutExec()` | Returned `(this.state.execs||{}).social`, so the **film's** cut was keyed to the **Social execution** — reading and *writing* another producer's cut history when one was briefed, and "No cut yet" forever when none was. Re-keyed to the plan (`video-<planId>`, falling back to `video`). See the open question below. |
| `/cut-propose` unwrapping | The route answers an ENVELOPE — `{edit:{class,why,cost,diff}, cut:{}}` — and `craftVals` read `propose.class` / `propose.cost` straight off it, getting `undefined`. The cost panel rendered as an empty box, and `commitDisabled` was **false** on an unchanged cut, so Commit stayed live with nothing to commit. That is your verify item #1, inverted. |
| literal `\uXXXX` in markup | The reorder buttons rendered the text `↑` / `↓` instead of ↑ ↓. You checked for literal `—` and were right that there were none — these are different codepoints. Worth adding `\\u[0-9a-fA-F]{4}` between `>` and `<` to your JS checks rather than the em-dash specifically. (Also fixed one pre-existing instance, "Plate without the line `→`".) |

**You were right about the cutdown copy.** "Nothing — already at or under target" was a guess, and it
was wrong: the *backend* was silently clamping a 2s request up to 4s and returning empty `notes`, so the
screen was describing a film that was neither at nor under target. `cutdown_plan()` now reports the
clamp and returns `asked` alongside `target`; the empty state now reads "Nothing dropped — every beat
survives at this length" and the reason arrives in `notes`. Render `notes` and it will be true.

### One structural question back to you

**Should a film be a real `video` execution?** `X_TABS` has no video entry, and the Video studio tracks
`production.versions` / `producedUrl` rather than an execution — so there was nothing correct for
`cutExec()` to point at, which is why it had borrowed Social's. The backend already has a `video` kind
in `execution.MANIFEST` ("Film", makes script / shoot board / film). Keying the cut to the plan works
and collides with nothing, but it is a workaround for a missing identity, not the answer.

**Left alone on purpose:** `loadShots()` has the same borrowed-`execs.social` shape, but it is
pre-existing and real shot data is already filed under that key — re-keying it would orphan
`tenants/*/shots`. Worth doing properly together, not quietly.

---

## §1 and §2 — DONE in your round-24 return. Reference only.

## Why the first two exist

Until now a film was "N shots of M seconds" — a shot list with no notion of what any shot was *for*.
That is the reason a generated film can be technically clean and still not be a film: nothing in the
pipeline knew which shot was the hook and which was the turn, so every shot was briefed as "shot 3 of
4" and the model filled the gap with pleasant, interchangeable footage.

There is now a **role grammar**: five named jobs a beat can hold.

| role | its job | what it costs if missing |
|---|---|---|
| `hook` | the first two or three seconds — one image that earns the next five | nobody is still watching when the argument starts |
| `world` | where we are and whose story this is | — droppable |
| `mechanism` | the proof, the demonstration, the routine actually happening | the claim is asserted rather than shown |
| `turn` | the moment something changes — the shot the film exists to deliver | — never dropped |
| `brand` | the endframe: the pack, clean, with space for type | — never dropped |

The generator now briefs each shot against its role, so this is not a label on a screen — it is what
the film is actually made from. `hook`, `turn` and `brand` are never dropped; `world` and `mechanism`
are, in that order.

## 1 · `GET /beat-plan?seconds=30` — **DONE**

What a film of this length should be made of, before a single shot is written.

```json
{ "seconds": 30, "asked": 30,
  "beats": [
    { "n": 1, "seconds": 8, "role": "hook", "role_label": "hook",
      "what":  "The first two or three seconds. One image that earns the next five.",
      "fails": "Nobody is still watching when the argument starts." },
    { "n": 2, "seconds": 8, "role": "mechanism", "what": "…", "fails": "…" }
  ] }
```

**The ask:** on the Video tab, when a duration is chosen, show the beat plan for that duration —
`n`, `seconds`, `role_label`, and the `what` line. Render the roles from the response, never from a
hard-coded list; a 15s film and a 60s film get different role sets and different counts.

`fails` is the more useful of the two sentences and the easy one to drop. It is what the beat costs
when it is missing, and it is the reason a person accepts a structure instead of arguing with it.
Put it where it is read — under the beat, on hover, secondary type, your call — but put it somewhere.

`seconds` may not equal `asked`: the beats are clamped to what the video model will actually render
(4, 6 or 8 seconds a clip, 8 the ceiling). When they differ, say so plainly rather than showing the
asked number as if it were the plan.

## 2 · `POST /cut-down` — **DONE**

A 30 from a 60, a 15 from a 30 — by dropping whole beats in role order, not by trimming everything
evenly.

```
POST /cut-down  { beats: [{n, role, seconds}], seconds: 20 }
```

```json
{ "target": 20, "seconds": 20.0,
  "beats":   [{"n":1,"role":"hook","seconds":6.0,"from_seconds":6}, …],
  "dropped": [{"n":2,"role":"world","seconds":8}, {"n":3,"role":"mechanism","seconds":8}],
  "kept_roles": ["hook","turn","brand"],
  "notes": ["Dropped 2 beat(s): world, mechanism."],
  "drop_order": ["world","mechanism"], "never_dropped": ["hook","turn","brand"] }
```

**The ask:** a "make a cutdown" control on an approved cut — pick a length, see **what gets dropped
before committing**, then commit through the cut editor's normal `/cut-commit` path. A cutdown is a
`free` edit class: the clips already exist on disk, so it re-cuts and never re-renders. Say that,
because "make me a 20" reads like it should cost something.

**Show `dropped` as prominently as `beats`.** The list of what is *leaving* the film is the decision
being made; the list of what stays is just the result. And render `never_dropped` somewhere near the
control — it is the answer to "why can't I have a 10 second version", and the honest answer is that
below three beats there is no film left to cut down, only footage.

`seconds` is what the cutdown actually comes to and it will not always equal `target` — beats are
whole, so 20 asked of 6/8/8/8/6 comes back as exactly 20 here but will not always land clean. Show
the returned `seconds`, not the target.

## 3 · The continuity check — **THE ASK.** Two halves, and they are not equal

```
GET  /continuity-metrics  → what this measures, and what it refuses to claim
POST /continuity-check    → { shots: [{n, role, clip_url, seconds, refs?, provider?}] }
```

`shots` is the shape a cut's `beats` already has, so this sits on the cut editor from §1 of
ASK_DESIGN_24. The response has two halves and **the order they are shown in matters**:

```json
{ "headline": "References did not reach every shot — fix that before reading the look measurements…",
  "provenance": { "ok": false, "without_cast": [4], "without_plate": [1,2,3,4], "notes": ["…"],
                  "rows": [{"n":1,"role":"hook","has_cast":true,"has_plate":true,"exempt":false}] },
  "drift": { "ok": true, "spread": {"warmth": {"span": 2.1, "bar": 10.0, "flags": true,
                                               "compared": [1,2,3], "endframe": [{"n":4,…}]}},
             "findings": [], "plate_used": true, "note": "Drift is advisory…" } }
```

**Lead with `provenance`, and render `headline` above both.** Provenance is a matter of record — did
each shot carry the signed cast frame and the signed plate — and it is the *cause*. Drift is measured
and is a *symptom*. Shown the other way round, somebody spends a render re-grading a film whose actual
problem is that four shots never saw the plate.

Three things not to build:

- **No per-shot verdict on the drift half, and no score.** The module deliberately does not name a
  culprit shot; that was built, tested against real footage, and removed because it produced both a
  miss and a false accusation in the same run. `findings` on the drift half carry `scope: "film"` —
  render them as a statement about the cut, not a badge on a row.
- **Do not flag Brightness.** It arrives with `flags: false` and must render as information only.
  Render the flag state from the payload rather than deciding per metric on your side.
- **Do not show a face-match indicator.** There isn't one, on purpose. `note` says why; show it.

Two details worth honouring. `exempt: true` marks a live-action shot, which needs no cast reference —
render it as exempt, not as a pass, or the exemption reads as a green tick nobody earned. And
`spread.*.endframe` is the `brand` beat measured but deliberately held out of the comparison, because
a pack on a set is not the film's location — `compared` lists the shots that actually were compared,
so show that list rather than implying all of them were.

---

## Verify on your end

- `/continuity-check` with `shots` omitted → `400` naming the field, not a stack trace.
- A film where every shot carried its references → the headline reads as a pass on both halves.
- `/cut-down` now returns `asked` alongside `target` and explains a clamp in `notes` — render `notes`.
- `checkfe.py`, all seven.

## Verified on this end

All four routes exercised over real HTTP against a running server.

The continuity checker was calibrated against real Heritage footage rather than chosen thresholds, and
two designs were built and thrown away before this one: measuring the whole film's spread beats naming
a shot, because legitimate shot-to-shot variance in this material (a lamp-lit puja against a
window-lit sofa, 22.8 apart on warmth) is larger than the defect being looked for (a whole grade
change, 13.7). Final calibration was six cases — two correct films stayed clean including one with the
endframe deliberately regraded, four one-grade mismatches were all caught, and one contrast-only
mismatch was missed and is documented as a known blind spot. The plate comparison was proven both ways:
a film measured against its own location came back clean, and the same film against a plate one grade
off flagged all three scene shots. Roles confirmed to attach to the
**moment** rather than the raw beat — when one action runs past the model's 8-second ceiling it splits
into two clips, and both carry the same role; assigning roles beat-by-beat would have made the first
half of an action the `mechanism` and the second half the `turn`, which is a mis-labelled shot list,
not a film. The generator's prompts were captured without spending a render, and confirmed to carry
the role direction on every shot — including that the `brand` beat asks for the pack with **empty**
space around it and does not ask for lettering, since type is set in post and a generated Devanagari
or Telugu headline is not writing at all. 18/18 `test_tools.py`, `contract.py` clean, checkfe 7/7,
**185 routes**, page loads with only the four pre-existing SVG placeholder warnings, tenant tree,
library, renders and edits all byte-identical afterwards.
