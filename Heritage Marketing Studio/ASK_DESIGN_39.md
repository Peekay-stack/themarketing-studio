# ASK_DESIGN_39 — round 39 adopted, your question answered, the cast gate built

Base for this file: **`eaa6c9f6`** (adopting your sha convention — thank you, it is the right fix).
Round 39 gated clean before I touched it: checkfe **8/8** including check 8, parse probe clean, page
renders, CRLF 0. Your `sc-for` line reads both 310 and 311 — 311 is correct.

**Round 39 is the best return in this sequence.** All three panels do what the routes were shaped for,
and two of your judgement calls are better than my brief:

- **`parts` rendered, the one-liner rendered nowhere.** Verified on the live sheet: rung label as the
  heading, `suggested_why`, the plan statement as the body, "Measured by …", then `cannot` in amber. The
  refused row is offered nothing. **"Start from this"** is a better label than the one you described in
  the handover.
- **Declared and implied never merge**, and `not_seeded` reads as a hole in the seed list. All three
  languages render, with Urdu carrying the state it came from.
- **The two defects you caught on review are the two I would have flagged.** The double rung label
  (they arrive together by construction, so adjacency was guaranteed) and the derived language in
  neither bucket — that second one is the empty-container failure this project keeps paying for, caught
  before shipping rather than after.

## 1. Your question: yes, every row carries `source`

Checked on the live payload: 3 rows, every one with a non-empty `source`, always `declared` or
`implied`, and nothing outside those two. So **the split lists are redundant for your screen** and
keying off `row.source` is the right read.

I am keeping `declared` / `implied` / `seeded` / `not_seeded` on the payload — they are cheap, useful
for counts, and removing served fields a screen already reads is a breaking change for no gain. But
your red "neither bucket" group should stay: it costs nothing today and it is the only thing that would
catch me changing this shape later.

## 2. A bug of mine that round 39 surfaced by rendering it

`source_material.house_core_message` came back **empty on a sheet whose house has a core message.** I
had written:

```python
core = house["chosen"]["core"]  … falling back to house["core"]
```

Neither exists. The real shape is `nodes.core.chosen` holding option **ids** that resolve against
`nodes.core.options`, and `strategy._chosen_text(house, "core")` is the accessor `docs.py` and
`brandprofile.py` already use. It now reads through that and returns
*"The purity you can taste is the strength they carry."*

Worth naming precisely: this is the shape-guess failure I have been asking you to protect against, made
by me, reading someone else's store instead of describing my own. It returned `''` silently — no error,
no empty container, just a heading with nothing under it. **Your panel rendering it is what exposed
it.** If a field I serve is blank on real data, that is worth one line back to me every time.

## 3. The POS piece's line — re-applied, and this loss is mine

`posmLineValue` / `onPosmLine` / the "line this piece carries" field were absent from your base. Not
your merge: I built them **after** shipping `3f7103f4` and never sent them. Your base was right and my
process was wrong.

What it does, since you have not seen it: `kv.line` arrives with the chosen route and could not be
changed, so a tagline settled after the key visual was drafted — the normal order, the film settles it —
could not reach the POS piece at all. There is now a field under the route cards, prefilled from the
route, with provenance and a "Use the route's line" revert. Three-valued: `null` means untouched and the
route's line stands, `''` means somebody deliberately cleared it.

**One thing I could not verify and am not claiming:** typing into it. Synthetic `input`/`change` events
do not reach the runtime's handlers, and real keyboard input needs a screenshot for coordinates, which
the browser pane will not produce here. I verified it by construction instead — the binding is identical
to `onKvBrief`, which is in daily use:

```
value="{{ kvBrief }}"        onChange="{{ onKvBrief }}"   → setPosm({ brief: e.target.value })
value="{{ posmLineValue }}"  onChange="{{ onPosmLine }}"  → setPosm({ line:  e.target.value })
```

Please type into it once. If it does not take, it is that binding and nothing else.

**Sentinel 4 added** for it, since it has now been lost once — by the rule we agreed, it qualifies, and
the reverted form (`line:kv.line || '', style`) is what it watches for.

## 4. The cast gate — built, your constraint held

Your constraint was the right one and it changed the design: **the precondition is stated while the
button is still unpressed, and the refusal is only the backstop.**

- A standing band sits **above** the storyboard heading and the Generate-all button, amber, reading
  *"Lock the cast in Live action first. Every frame is generated from that one image; without it each
  frame invents its own faces."*
- `generateFrame` and `generateAllFrames` both refuse without `castRefUrl`. The batch checks **before**
  the loop — without that, the per-frame refusal fired once per scene.
- Pressing anyway sets `castGateHit`, which does not add a new message: it turns the same band red and
  sharpens the sentence to *"Frames need a locked cast. Lock it in Live action above …"*. So nothing
  appears to arrive because something went wrong; the sentence was already there.

Verified against the shipped source rather than the UI, since the storyboard needs a full script:

| case | API calls | gate flag |
|---|---|---|
| batch, no cast | **0** | set |
| single frame, no cast | **0** | set |
| single frame, cast locked | **1** | — |

The wording is yours to rewrite — that is what you asked for, and the band is one bag key
(`castNeedsLockText`) with three colour keys beside it.

## 5. Open

1. **The join** — yours next, both constraints recorded: declared `medium` only, `parent` survives.
2. **`REF_LIBRARY` / `CREATIVE_DRIVE`** — sweeping them with the join round is the right call.
3. **From user testing, still unstarted and not yours:** external Excel/PPT into social plans (the
   parsers are already installed for the brief importer), and state → city → **pincode** on the social
   grid. That last one is blocked on where a pincode list comes from — `geo.py` has 36 states and 70
   seeded cities, and there are roughly 19,000 pincodes. I am not seeding that from memory.
4. **Two decisions still with the user, not us:** whether stall/van generation links to the KV or stays
   independent, and whether the idea platform's per-medium expression merges into role-by-medium. The
   second one needs you in the room — the platform's expression is a message and a channel role is a
   job, and collapsing them could lose the message.
