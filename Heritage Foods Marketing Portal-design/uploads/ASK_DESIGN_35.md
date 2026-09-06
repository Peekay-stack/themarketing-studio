# ASK_DESIGN_35 — channel weights: the half that was missing

Small round, mostly server. **Three hunks in your file**, all commented at the site so they read as
deliberate rather than spare. Nothing else in `app.dc.html` was touched — the diff against your
round-34 base is those three hunks and nothing more.

## 0. Before building: two things in the audit's order of work were already done

The recommended order in *The Studio, Tab by Tab* puts two Small items ahead of every Medium. Both
turned out to be closed already, so this round skipped to #7.

- **#1, the fabricated Home metrics (F1)** — done. Home now reads *"No delivery data is connected …
  this stays empty rather than showing a figure the studio cannot source."* Confirmed on the loaded
  page, not from the diff.
- **#2, the shared unauthenticated asset directories (F10)** — done, and done properly. `renders`,
  `media` and `edits` are routes now rather than `StaticFiles` mounts, `tenancy.asset_path` resolves
  tenant-first then legacy and refuses anything escaping its directory, there is one function for auth
  to land in, and `/asset-state` reports honestly how many files are still sitting in the legacy
  folders instead of claiming isolation it does not have. No action needed from either of us.

Also worth recording, because I got it wrong out loud first: **`api/.venv` exists and always did.**
`launch.json`'s python path is relative to its own `cwd` of `api`, so looking for `.venv` from the
project root finds nothing and looks like a broken config. It is not broken.

## 1. What F3 actually was

Not "no weight column" — the column has existed all along. `channels.cols` carries `share`, the cell
is editable, `actual_split` reconciles it against the declared split, a finding fires at ten points of
divergence, and your `balActualText` and `balBasis` already render the result. That is most of the
feature, and I had it recorded as not started.

What was missing was the enforcement, and it was missing in a way none of the gates could see.

**Weights that did not add up were silently renormalised.** `actual_split` divided by the column's own
total, so a column reading 40/20/10/5/10/5/5 came back as **74% brand**. The same seven channels
weighted to sum 100 read **70%**. Four points of difference, arithmetically correct in both cases,
with nothing on screen to say which one you were looking at.

**A half-filled column was indistinguishable from an empty one.** Four of seven weighted fell all the
way back to channel count and reported the identical sentence an untouched plan reports.

## 2. Your file — three hunks

**a. `COL_HINT`, new, above `COL_FLAG`.** The header-tooltip rule was one inline ternary that only
`role` got. It is a table now, and `share` carries the sentence that was missing everywhere:
*"Percentage of total spend. Every channel together must add up to 100 — a column that sums to
anything else is not used, and a half-filled column is not used either."* `side` and `pillar` picked
one up for free. Real middots and em dashes, not escapes, per the convention in the rest of the markup.

**b. `pCols` reads the table** instead of the ternary. One line.

**c. `balBasisFg` reads a served flag.** This is the one worth your attention, because it is a defect
in the pattern rather than in the value. It used to be:

    balBasisFg: (act.basis && /unknown|count/i.test(act.basis)) ? '#B07A12' : '#6B7280',

The warning colour was decided by pattern-matching the server's prose. The new basis sentence —
*"weighted by planned spend — but the weights add up to 95%, not 100…"* — contains neither "unknown"
nor "count", so **the most serious of the three states would have rendered in neutral grey.** I
checked that in the page rather than assuming it: that regex returns `false` against that string.
`actual.trusted` is now served as a boolean and read first, with the regex kept only as a fallback for
a payload that predates the flag.

No new bag key, no new markup, no new `sc-if`. If you would rather the warning had its own band
instead of only a colour, that is your call and I have not pre-empted it.

## 3. Server

`plan.actual_split` now returns, additively — existing keys unchanged, so nothing downstream moved:

| key | type | meaning |
|---|---|---|
| `weighted` | int | how many channels carry a parseable share |
| `n_channels` | int | how many channels there are |
| `sum` | float or null | what the entered weights actually add up to |
| `sums_to_100` | bool or null | null when nothing is entered |
| `trusted` | bool | whether the figure is a share of the plan, or a ratio of what was typed |

`basis` gained two sentences it did not have: the sum shortfall, and *"spend unknown on 3 of 7
channels"* for the partial case. `mediaplan.split` passes `actual` through whole, so the Media tab
gets all of it with no change, and its no-channels fallback dict now carries the same keys — without
`trusted` it would have fallen through to the prose test and rendered as quietly trustworthy.

`plan.validate` gained **one** finding: the weights do not sum to 100, fired only when the column is
complete. Deliberately **not** added: "no channel carries a weight" and "n of m unweighted".
`mediaplan.findings` already owns both, and its own docstring is right that saying a thing twice in
two vocabularies is how the two start to disagree — I wrote both, then took them out. Both states
still reach the Plan screen through the balance finding, whose basis clause now names them. There is a
comment at the site saying not to re-add them.

The drafting instructions changed too, so generated rows stop reproducing the gap: `share` is now
described as a percentage of total spend that must sum to 100, with *"leave the whole column empty
rather than filling some rows: partly weighted is worth nothing."*

## 4. Verified in the page, not in the diff

Plan `abfaac5fe0`, seven channels, on a loaded screen:

- untouched column → `weighted 0/7`, basis *"spend unknown — computed on channel count"*, actual 43/57
  against a declared 60 — F3's evidence reproduced exactly
- four of seven weighted → basis *"spend unknown on 3 of 7 channels"*, sum finding correctly silent
- all seven summing to 95 → actual **74%**, basis names the shortfall, the finding renders on the
  Channels layer with its own Resolve door, and the basis line computes to **`rgb(176, 122, 18)`** —
  the amber
- all seven summing to 100 → `trusted: true`, clean basis, finding gone

The plan file was snapshotted first and restored byte-for-byte after; all four plans md5-match their
pre-test state. Worth knowing for your own testing: **editing channel rows makes Phases and Measures
stale**, because their signature is built on channels. Two findings appear that have nothing to do
with weights.

Gates: checkfe 7/7 (685 class members), test_tools 18/18, 246 routes, `app.dc.html` CRLF 0.

## 5. Open, and yours

1. **Where the weight column wants to live.** The hint is a tooltip, which is the cheapest honest
   thing and probably not the right one — a running total beside the column ("95 of 100") would tell
   a person mid-typing what a tooltip tells them only if they hover. I have not built it, because it
   is a layout decision on the rows editor and that is yours.
2. **`sum` and `weighted` are served and unrendered.** Same question as `/continuity-metrics` in round
   26: give them a home, or say so and I will stop serving them.
3. Still standing from round 34, unchanged: the nine hardcoded-brand prompts, and the `MEDIA_DEFS`
   six-vs-eleven taxonomy split. Neither is touched here.
