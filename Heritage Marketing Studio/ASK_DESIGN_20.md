# ASK_DESIGN_20 — the jobs table, and the shelf

## Build on the file in this zip. Please read this box first.

```
app.dc.html      951,050 bytes
sha256           15a24e75450f0c8f…
```

The `app.dc.html` in this zip **is the installed file** and is the only correct base. Two of the last
three rounds were built on a previous return instead, and both times every fix made since that return
was silently reverted — round 18 lost six of them and they had to be re-applied by hand.

Two things make this cheap to get right:

1. **Check the size and hash above against the file you start from.** If they do not match, you have the
   wrong base.
2. **This base already contains two fixes made since round 19.** If either is missing from your return,
   the base was wrong:
   - `draftCampaign` no longer says *"Pick a ladder path above first"* — the select sits ~80 lines
     *below* that button. It now says *"Choose a ladder path below"*, and says something different again
     when the house has no paths at all (the select is disabled in that case, so "choose one" is not a
     followable instruction).
   - The test cards take **both** halves of the question from the server (`judgeAsk` / `judgeWhy`). They
     used to take the server's whole question for the bold headline and keep a local copy of the
     elaboration for the grey line — and the server's question string *contains* its own elaboration, so
     every card printed the same sentence twice, one line apart.

`tools/checkfe.py` is included in this zip. **Please run it on your return before sending it** — it takes
a path argument:

```
python tools/checkfe.py app.dc.html
```

Its **seventh** check (*template handlers reach the bag*) is the only one that has ever failed here, and
it has caught a dead control twice. The JS port of checkfe is faithful on the other six and omits that
one, so it will pass a file the real check fails.

---


Backend for phase 1 is on the server and verified. Two new routes, **nothing removed**. Every panel you
already built still answers exactly as it did — this round is additive on purpose, so the same data is
visible two ways and the two can be checked against each other.

## Why this exists

Three screens have been asking the same question at three altitudes in three vocabularies:

| screen | asks | vocabulary |
|---|---|---|
| house · message by medium | 7 media | digital, social, tv, ooh, posm, on-ground, trade |
| platform · expression by medium | 6 media | video, social, posm, activation, incentive, media |
| campaign · roles by medium | 8 media | the house seven, plus influencer |

They share **two names out of eight**. That is how the house came to say POS material was *"roz taaza,
roz shakti"* while the platform said it was *"500 checked this before you"* — two POS lines in one
strategy, only one of which a producer ever read.

`GET /jobs` replaces all three with one table. The role is **computed** from the rung a medium can carry;
the expression sits **beside it in the same row**, where the role explains it.

## The canonical vocabulary (settled, do not re-derive)

Seven top level, ten leaves. `api/media.py` is now the only file that defines this.

```
tv
digital        ├ social  ├ influencer  ├ owned  └ performance
ooh
posm
activation     (on-ground is an alias)
trade          (incentive folded in as levers per channel)
pr             (new)
```

- **`digital` is a parent, not a medium.** It has no role of its own. Its four leaves carry different
  rungs, which is the argument for splitting it.
- **`video` is not a medium** — it is an asset delivered to tv, social, owned and performance at their
  own lengths and ratios.
- **`media` is parked.** A schedule is not a medium. It has left the medium list *and* the Execution
  producers, and where it lands has not been decided. Do not build it anywhere.

## `GET /jobs?house=<id>` — or `&set=` / `&id=` for a specific campaign

Returns `{rows, count, filled, empty, needs_review, parents, findings, campaign, house, taxonomy}`.

**Every row carries all ten of these keys, always.** `tools/contract.py` now asserts it — 204 row checks,
and I verified it fails loudly if any one is dropped. `expression` may be an empty string; the KEY is
always present, so `row.expression` never reads undefined.

```
medium        "influencer"                         the leaf key
label         "Influencer"                         what to print
parent        "digital"  |  ""                     "" means it is its own top level — group by this
role          "emotional endpoint, third-party"    computed, or the campaign's typed override
role_source   "computed" | "typed"                 say which; a computed role is a suggestion
why           "Someone like the buyer saying…"     the reasoning behind the role
expression    ""                                   what it makes. EMPTY IS A REAL STATE
source        ""                                   where the expression came from, or "" if empty
needs_review  false                                inherited a line from before digital split
empty         true                                 render this as a hole, not as blank
```

Live on Heritage right now — 10 rows, 7 filled, **3 empty**:

```
TV & film     ·         emotional endpoint + the turn        the platform, expressed as video
Social        digital   the bridge, demonstrated             the platform
Influencer    digital   emotional endpoint, third-party      — EMPTY
Owned         digital   the bridge, demonstrated at length   the house's digital message  ⚠ review
Performance   digital   one rung, at the moment of intent    — EMPTY
Out of home   ·         one rung, chosen                     the house's ooh message
POS material  ·         functional truth + emotional RECALL  the platform
Activation    ·         the bridge, experienced              the platform
Trade         ·         OFF the consumer ladder entirely     the platform, expressed as incentive
PR            ·         the functional truth, earned         — EMPTY
```

### The three things this table is for

1. **`empty: true` must read as a hole, not as an empty box.** Three media carry a job nobody has written
   the work for. That was invisible when roles lived on an 8-row screen and expressions on a 6-row one.
   An empty cell is a decision not yet taken and should look like one.
2. **`source` must be shown.** OOH and Owned are drawing on the *house's* medium lines, not the
   platform's. Presenting a borrowed line as though it were written here is the thing `stands_on` exists
   to prevent.
3. **`needs_review: true` needs a marker.** Owned inherited a line written when digital was one medium —
   it could have been a site, a search line or a social post, and only a reader can tell.

Group rows by `parent`. Four rows sit under Digital; the rest are their own top level.

## `GET /shelf?house=<id>&brief=<id>`

The seven inputs, read-only, storing nothing. `{inputs, filled, of, empty, summary}` — each input has
`label`, `what`, `feeds`, `available`, and a `why` sentence when it is empty.

Heritage reports **2 of 7**. Show the empty ones with their `why` rather than hiding them: `trade_econ`
does not exist anywhere yet, and that absence is why the trade expression currently asserts an argument
about the shopkeeper's arithmetic with nothing behind it.

## What NOT to do this round

- **Do not remove the existing expression block or the roles block.** They stay until phase 2, so the
  jobs table can be checked against them. Two views, same data, both correct.
- **Do not build a `media` / media-planning row.** Parked.
- **Do not write to `/jobs`.** It is computed. Editing an expression still goes through the route it
  goes through today.

## Please also fix, while you are in the file

Three strings in the POS panel are now wrong after the earlier POSM work:

1. *"each format rendered at the ratio it prints at"* — the master renders at 3:4 and formats **re-flow**.
2. *"five ratios"* — there are 30 formats.
3. The toolkit card still says the messaging house has **eight** layers. It has nine.

And one that costs money: `produceAdaptations` calls `/posm-image` **once per selected format**. Under
the layer model the hero cut-out is one asset for the whole kit, so six formats currently means six
near-identical renders of the same subject at the same 3:4 ratio. Render the cut-out **once**, then call
`/posm-adapt` for the per-format sheets — that route is free and makes no model call.

## Verified before this was written

18/18 `tools/test_tools.py` · 7/7 `tools/checkfe.py` · `tools/contract.py` clean including the new
jobs-row assertion · **167 routes** (165 + the two new) · tenant tree identical by content hash · page
loaded, both routes called from the page's own origin, every row complete, old panels answering 200 ·
console shows only the four pre-existing NeedScope SVG placeholder warnings.
