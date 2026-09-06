# Ask Design — round 30

Rounds 28, 29, 29b and 29c are integrated and live against the real backend. `tools/checkfe.py` passes
all seven, including the seventh you can't run: **518/518 `sc-if`, 253/253 `sc-for`, 2059/2059 `<div>`,
644 class members with no duplicates, 16 bag methods spread, 275 template handlers all reaching the
bag.** Your counts matched mine exactly.

The Media tab works. Against the live Heritage plan it renders all seven channels with roles, sides and
"—" for the missing shares, the read-only band, the split, the citation card with the dispute in its own
block, and the door to the retired panel. Execution reads "three producers" with the retired line under
the strip. Nothing threw.

**Base:** take `app.dc.html` from the attached zip. It is your round-29c file plus the two fixes in §1.

---

## 1. Two things I changed in your file

### a. `prFirstPhase` / `prFirstKind` — reverted, re-applied

This is the second time. Round 29 was built on the round-27 base, which predates the fix I sent in
ASK_DESIGN_28A §A, so it came back as the old version.

```js
// before — st.phases is a DICT, so l.length is undefined and this returns ''
prFirstPhase(){ const st = this.pr().status; const l = (st && st.phases) || []; ... }
// after
prFirstPhase(){ const st = this.pr().status; const l = this.prSeq(st && st.phases); ... }
```

Verified against live `/pr-status` just now: before the fix both returned `''`; after, `tease` and
`corporate`. Untreated, a campaign PR sheet is created with **no phase** where the screen means `tease`.

It's the residual of the round-26 dict bug — these two used `.length` rather than `.map`, so they never
threw, which is exactly why they survive review. I've added a comment on them saying they have been
reverted once, so the next round knows it wasn't deliberate. **Nothing else of mine was outstanding** —
I diffed your base against my copy and this was the only hunk.

### b. The nav wrap threshold: 1180px → 1450px

Your comment on that block was right — *"keeps the last item on screen at any width instead of one
width"* — and the number was 265px too low. Measured in the browser, need vs available:

| Viewport | Nav needs | Nav has | Result |
|---|---|---|---|
| 1280 px | 626 | 527 | **Campaigns and Memory both clipped** |
| 1440 px | 684 | 681 | **Memory clipped** |
| 1600 px | 841 | 841 | fits — by 0 px |

Between 1180 and ~1445 the nav still overflowed with the scrollbar suppressed, so the tail was hidden
with nothing to say it was there. 1280, 1366 and 1440 are the three commonest laptop widths, so the
broken band was most of the real audience. Raising the breakpoint fixes it: at 1280 and 1440 the nav now
wraps to two rows with nothing clipped and the header stays at 84px. 1600 is untouched — still one row,
still `nowrap`.

**The part I did not fix, because it is yours to decide:** 1600px fits by *zero pixels*. A twelfth
destination, or a longer brand name in the chip beside the nav, starts clipping again — and a media
query cannot see a sibling's width, so no breakpoint here is safe against that. That is a structure
question: grouping (Execution / Sales enabler / PR / Media are arguably one family), an overflow menu,
or something better. Worth settling before the next two screens land, because they will want doors.

## 2. The shapes are settled — and three of them moved

You flagged these as guesses. Two of your three guesses were right; the mismatches were **my** naming,
not yours, so I fixed the backend rather than asking you to read a worse key.

| What you read | Was | Now | Why |
|---|---|---|---|
| `split.brand` \|\| `split.brand_share` | `declared_share` | **`brand_share`** | `plan.balance_of` already called it `brand_share` and `/plan-status` publishes it that way. A third name for one fact is the two-definitions failure — it made Media read "not set" while Plan read 60. |
| `basis.claim` \| `what` \| `text` | *absent* | **`claim`** | There was a citation on the wire with no statement of what it was a citation *for*. `value` (the number 60) is a different thing and is still there. |
| `basis.dispute` \| `against` | `disputed_by` | **`dispute`** | Renamed in `plan.BRAND_SHARE_BASIS` and `mediaplan.ESOV_BASIS` both, so one renderer handles either. |

`basis_of_default` is now `{value, claim, source, dispute, note}` in both places. Your read needs no
change — it already reaches all three of claim, source and dispute.

Confirmed correct as you built them, no change needed: `sg.channels`, `split.default`, `split.declared`
(the three-valued reading is right, and Heritage renders "declared"), and `basis_of_default` taking
precedence over `basis`. Your `basis` / `basis_of_default` comment about the same word meaning two things
is a good catch and both names are staying.

## 3. `can` / `cannot` is now served — and it caught your static list going stale

Your `st.can || st.does || st.owns` panel was rendering the amber "shape not read" line, correctly,
because `/media-status` had no such key. It does now: eight `can` rows and seven `cannot` rows, keyed
dicts with `label` and `what`, which your `prSeq` reads without changes. It renders in full.

Building it surfaced the real problem it solves. **"What this tab will own" is hard-coded, and two of its
five items are already built** — so the screen currently says *"Competitive intelligence — the part being
built first"* about eight lines below the served list saying the desk holds the competitive picture. Money
is the same. That is the exact staleness the served version exists to prevent.

Please drop the hard-coded list and let `cannot` carry it. The `cannot` rows already say weight,
flighting and the calendar are missing, and they say it with the reason — *"the phase windows exist and
are read; weight per week inside them does not"*. If you want the roadmap framing kept as a separate
block, take it off `cannot` rather than off a literal.

## 4. Two new backends with no screens yet

Both built and tested since your last round. Not asking you to build them here — flagging so the rail
decision in §1 is made knowing what is coming.

- **`/geo-status`, `/geo-cities`** — 36 states and UTs with zones and languages, cities above a
  population line. Names, codes and old names all resolve. Ten of thirty-six states have a principal
  language the studio cannot write in, and that list is on the wire.
- **`/social-plans`, `/social-plan`, `/social-plan-frame`, `/social-plan-benchmark`, `/social-cell`** —
  a geography-wise social campaign that holds a budget. Its one interesting output: it computes whether
  a geography split can run at all before any money moves. Seventy cities on ₹40 lakh at a ₹250 cost per
  action comes back *too fine — about 37 cells supportable*, and it blocks.

I'll send those as a proper screen ask with the shapes settled, once the rail question is answered.

## What to send back

`app.dc.html` and your note. Please build on the attached base so §1a does not have to happen a third
time — and if you would rather I stop patching your file directly and send diffs instead, say so and I
will.
