# ASK_DESIGN_22 — the claim gate, the return trip, and the campaign's own proof axis

This is P3's frontend. The backend for it is built and verified — three genuinely new pieces of state,
all additive, nothing retired, nothing removed from anything you have already shipped.

## Build on the file in this zip. Please read this box first.

```
app.dc.html      965,900 bytes
sha256           6f7fed38a32aa64f387d28460a06ab106130a316fb55dd81fff2de083df2a045
```

This is the installed file, unchanged since your round-20/21 return — this side made no frontend edits
this round, so your own file (with the fixes you already applied) should be byte-identical to it. If it
is not, diff before you start; two rounds have been lost to the wrong base before.

**These markers must all be present in the base** (grep before touching anything):

| marker | expected count |
|---|---|
| `loadJobs` / `loadShelf` | 3 / 3 |
| `H_LIVE` | 4 |
| `total_layers` | 3 |
| `Load jobs table` | 1 |
| the real em dash in `Jobs — one table, computed` (not `—`) | present |

`tools/checkfe.py` is in this zip. Run it on your return before sending it back — its seventh check is
the only one that has ever failed here, and the JS port cannot run it.

---

## Why this round exists

The messaging house is written before an idea exists, so its core, emotional and functional layers are
a first pass — the best guess available with nothing to aim at yet. Once a platform is adopted, that
guess should be returned to and re-argued now that there is a mechanic to write toward. Nothing in the
product today marks whether that return trip ever happened, or shows a person which specific fact their
platform is actually staked on when they're asked whether a competitor could sign it.

Separately: five of Heritage's six recorded ladder paths report *"the bridge does not divide, so there
is no proof axis."* That is not six failures of the same house — it is the axis being asked for at the
wrong altitude. A campaign can often see three genuine divisions (three kinds of check, three occasions,
three audiences) that the bridge's own wording was never going to state as one sentence with a colon in
it. The campaign should be able to say so directly.

## What NOT to build this round

**Do not touch the "Two tests" panel.** `ideas.JUDGED` still has both `ours` and `durable`, exactly as
shipped. The plan originally called for retiring `ours` and moving it up to a pre-platform gate — that
was **deliberately not done** this round, because the only way to do it without emptying your live panel
first would have been to build its replacement blind, without your input on where it actually belongs
on screen. The data this needs is delivered below (`claim_fact`); the repositioning is a decision to
make together, once you've seen the shape of it, not something to guess at from this document alone.

**Do not build a new field for a "return trip" timestamp.** There isn't one, on purpose — see below.

## 1 · `claim_fact` — the specific thing being judged

`GET /idea-platform` now returns a `claim_fact` object alongside the platform's other fields:

```json
"claim_fact": {
  "available": true,
  "text": "500 dairy professionals check the milk every single day — purity here is people doing a job, not a slogan.",
  "pillar": "functional",
  "sourced": true,
  "id": "9c5aaee5"
}
```

This is the platform's own `pillar` + `rtb_id`, resolved to the actual fact text and whether it's
sourced. It was already being captured on adoption — nothing new is asked of the person. What's new is
that the fact itself is now resolvable to real words.

**The ask:** show this next to the existing "Could a competitor sign it?" badge in the Two Tests panel,
so the question reads against a specific, named claim instead of the whole platform sentence. Something
like: *"Testing: 500 dairy professionals check the milk every single day — purity here is people doing
a job, not a slogan. [functional, sourced]"* directly above or beside the badge. No new persistence, no
new route — this is read-only context for a control that already exists.

`available: false` (with `text: ""`) means the platform's `rtb_id` doesn't resolve — either it points at
an option that's since been deleted, or an older platform never had one set. Show nothing extra in that
case; don't invent a placeholder.

## 2 · The return trip — `ladder_confirmed` and `claim_state`

`GET /idea-platform` now also returns:

```json
"ladder_confirmed": false
```

And `GET /house/{house_id}` returns a sibling field alongside `house` and `status`:

```json
"claim_state": "provisional"
```

Three possible values: `"provisional"` (a platform is adopted, the ladder hasn't been confirmed since),
`"settled"` (confirmed), or `null` (no platform adopted from this house at all — the question doesn't
apply yet). This is deliberately **not** a timestamp comparison — there is no "adopted at" time anywhere
in this codebase, and inventing one to infer the state would be guessing at a signal that mostly isn't
there. It's a plain flag a person sets by actually doing the return trip and saying so.

**Set it** with the same route you already call to adopt a platform, sent alone:

```
POST /idea-platform  { "house": "<id>", "confirm_ladder": true }
```

This mirrors the existing `{ house, skipped: true }` pattern exactly — same shape, same short-circuit,
does not require re-sending the whole platform form. Send `confirm_ladder: false` to un-confirm.

**The ask:**
- On the house list cards and the opened house, show a small badge next to the brand/progress line —
  *"provisional"* in amber, *"settled"* in green, nothing when `claim_state` is `null`.
- When a platform is freshly adopted (the `/idea-platform` POST that carries a real `line`/`idea`
  succeeds), prompt the return trip — a toast or inline banner: *"An idea now exists. The house was
  written before it — worth going back and re-arguing the core, the pillars and the bridge against it."*
  with a link back to the messaging house screen, and a **"Mark the ladder as revisited"** action that
  fires `confirm_ladder: true`. This is the "prompted, not remembered" behaviour the plan calls for —
  it only needs to fire once per adoption, not nag on every visit.
- `ladder_confirmed` does **not** reset automatically when the platform's sentence or mechanic is
  edited later — a deliberate choice on this side, to avoid re-flagging provisional on an unrelated typo
  fix. If you want it to reset when the person picks a genuinely different pillar or RTB, that's a
  reasonable frontend-side call (re-send `confirm_ladder: false` yourself when you detect the change) —
  not something the backend currently does for you.

## 3 · The campaign's own proof axis — `divisions`

A campaign can now carry its own divisions directly, instead of only inheriting whatever the bridge's
colon-parsed text happens to yield.

```
POST /campaign  { …, "divisions": ["cognitive", "physical", "social"] }
```

Stored verbatim, returned on the campaign object as `divisions: [...]`. **Written once, it wins** — the
campaign's own axis is checked first everywhere the proof axis is used (`GET /campaign-grid`'s `axis`
and `grid.axis`/`grid.columns`), and only falls back to the bridge's colon-parse when `divisions` is
empty. An older campaign with nothing in `divisions` computes exactly as it always has — nothing changes
for it.

**The ask:** add a small "Proof axis" field to the campaign form — 2 to 4 short text inputs (add/remove
a row, same interaction as the existing slots list), sitting near where the ladder path is chosen. Two
findings will already come back and should render like the campaign's other findings:

- *"{name} writes N division(s) — two to four is the range this framework argues for…"* if 1 or 5+ are
  written.
- *"{name} has no proof axis — write two to four divisions directly… or divide the bridge on this
  path."* if nothing was written and the bridge doesn't divide either. This is new — it did not exist
  as a campaign-level finding before (only as a house-level one about the bridge itself, which is
  unrelated and still fires separately; both can be true at once and that's fine).

The grid (`GET /campaign-grid`) already re-columns itself against whichever axis won — no frontend
computation needed there, just read `grid.axis` / `grid.columns` as you already do.

## Verify on your end

- `claim_fact.available: false` on a platform whose `rtb_id` doesn't resolve — confirm nothing renders
  oddly (no empty bracket, no "undefined").
- The confirm/un-confirm round trip: adopt a platform, confirm the ladder, reload, see `"settled"`;
  un-confirm, reload, see `"provisional"` again.
- A campaign with 3 divisions and **no ladder path set at all** — confirm the grid still columns
  correctly (this works without a ladder now, which is new).
- `checkfe.py`, all seven, on your actual return.

## Verified on this end before this was written

Every new field and route tested against real Heritage data, not just read from the code: `claim_fact`
resolved the real sourced functional RTB text; the confirm/un-confirm/re-confirm cycle round-tripped
cleanly through `/house/{id}`'s `claim_state`; three real campaigns were saved with 3, 1, and 0
divisions respectively and each produced the exact finding described above, then all three were
dropped. 18/18 `test_tools.py`, `contract.py` clean, tenant tree restored to byte-identical against the
snapshot after every test round. Page loads with only the four pre-existing SVG placeholder warnings.
