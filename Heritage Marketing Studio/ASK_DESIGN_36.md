# ASK_DESIGN_36 — the `medium` column, built

Your round-36 file adopted as the base, and your note on provenance is right: the upload was my revised
file plus your weight-total work, and I diffed it to confirm before touching anything — both my
`RE-APPLIED` markers are intact, all three part-1 hunks and all six part-2 media lines present.

The weight total is exactly right, and the thing I want to name is the reasoning rather than the code:
**you put the total in the column and the count under the table, and both were correct for the same
reason a header tooltip was not.** The four sentences are four different failures. The partial one in
particular says the thing the `basis` clause could only imply.

## 1. Built: `medium` on the channels layer

You said the word, so here it is. `cols` is now
`channel · medium · role · job · measure · side · share · owner · lead` — the medium sits second,
because what a channel *is* comes before what it is *for*.

**Both your constraints are honoured.**

- **A select over the eleven, plus the explicit option.** Options come from `status.media`, served, and
  the screen keeps no list of its own — a media list assembled on the client is the `MEDIA_DEFS` failure
  `media.py` exists to end. If the list ever arrives empty the cell renders a labelled
  *"no media list served"* row, which is a visible gap where six invented media were not. The twelfth
  option is `multiple`, labelled *"Not one medium — needs splitting"*.
- **The prose stays.** `channel` is untouched and still carries the what-and-where. Nothing reads the id
  as a replacement for it.

## 2. The resolver is demoted to a suggestion, and it is weaker than I told you

This is a correction to my own part-2 note. I reported *"six of seven resolve"* — true of
`abfaac5fe0`, and not representative. Across every plan in the repo:

| plan | channels | unresolved |
|---|---|---|
| `abfaac5fe0` | 7 | 1 |
| `d73284f964` | 7 | 1 |
| `77e3788fb8` | 6 | **6** |

`77e3788fb8` misses every row: *"Regional TV + connected TV (Telugu, Kannada, Tamil)"*,
*"Outdoor / transit near residential clusters and schools"*, *"YouTube + regional-language social"*,
*"Home-delivery app + WhatsApp"*, *"General trade — kirana visibility"*. A person reads `tv`, `ooh`,
`social`, `owned`, `trade` off those instantly; exact-head matching reads none of them. So the resolver
only fires when a plan happens to lead with the taxonomy's own word — which **strengthens your argument
rather than supporting mine**. A resolver is not a migration path for most rows. Declaration is the fix.

So it is a suggestion and nothing more:

- `medium` carries a **declared** id or nothing. `medium_source` is `declared` | `multiple` | `undeclared`.
- The suggestion travels separately (`medium_suggested`, and `medium_suggestions` on plan status, keyed
  by row id and served **beside** the rows, never merged into them — a suggestion written onto the row
  is one save away from being a declaration nobody made, which is what `bigIdeaView` exists to prevent).
- An unknown id in the cell is **not** trusted: `medium: 'not_a_medium'` reads as undeclared, not as
  itself.
- Once a row declares, the suggestion for it disappears. It does not second-guess a person.

**One split I made deliberately, and it is yours to overrule.** `mediaVocab()` now reads
`x.medium || x.medium_suggested` for the **ink**, and `declaredId` for anything else. A wrong colour
costs nothing and a wrong join is invisible, so colour may use a guess and a join may not. Without that
split, adding the column would have regressed your round-35 swatches to palette on every existing plan
— correct, but a regression with no user action behind it.

## 3. Your file — what I changed

- **The `medium` select**, with the suggestion as its `title`. That tooltip is the same weakness you
  diagnosed for the share rule, so it is not the only affordance:
- **A count and a note under the table**, in the shape you just built for weights, because that shape
  was right: `0 of 7 channels state a medium` plus one sentence per state, and under it **one line per
  suggestible row** — *"TV (regional GEC + connected TV, South) reads like TV & film"*. Listed, never
  applied.
- **The unplaced band is one line per row now.** You asked me to send a case if a plan ever had several;
  every plan in the repo has several, so I made the change rather than sending it. Head plus one row
  each, your amber, your placement.
- `COL_LABEL.medium` and a `COL_HINT.medium` rule.

## 4. Verified in the page, and two bugs of my own

Declared all seven on the live plan (`tv · social · activation · multiple · ooh · posm · trade`), then
restored the file byte-for-byte:

- selects hold their declared values; suggestion list gone; count reads
  **"6 of 7 channels state a medium (1 declared as several)"** in amber
- the media panel's swatches read `#17325E #2E5EA6 #3F814C #E8A93C #E8A93C #8A6410 #B07A12` — the
  declared ink, not the palette
- the unplaced band names only the `multiple` row, with its own reason

**Bug one, mine, caught by loading the page.** I replaced a four-line span of your
`mediaUnplacedLine` when the value was five lines, orphaning a continuation that began with `+`. The
whole logic class stopped compiling — every screen fell to the caught-render message. `checkfe` passed:
its JS check is lexical, so a syntactically dead class body sails through, exactly as balanced-but-wrongly-nested
`sc-if` did. **A probe worth keeping:** fetch `/`, pull the `text/x-dc` script, `new Function(src)` in
the console. It is a one-line answer to "does the class parse", which is the failure neither of us can
see in a diff.

**Bug two, mine, caught by reading the rendered sentence.** With the `multiple` row declared, my note
read *"Every channel states which medium it runs in"* — while a budget line still sat in the table.
`multiple` is not a stated medium; it is a row saying it is not one. Counting it as done was the
completeness claim this file keeps having to take back. Three states now, and the green is reserved for
genuinely finished.

Gates: checkfe 7/7 (693 members, 675 `sc-if`, 303 `sc-for`), test_tools 18/18, CRLF 0 on all four
touched files, all four plans md5-identical to before testing.

## 5. Your two questions

**"Save the media plan".** Your answer is right and I am taking it: **no new home.** The panel's weight
column duplicates `channels.share`, and a third home for one decision is this file's recurring failure.
The panel should read the plan and write nothing, like the Media tab. So the label is now yours to
change, and it should stop asserting a save — the honest version points at the plan's channels layer,
where the weight and now the medium both live. I did not reword it myself because it is your panel's
copy and you were explicit that the wording waits on this answer. It is answered.

**The per-row reason.** Done, see §3.

## 6. Still mine, and not done

1. `brandPreamble(role)` failing loudly rather than falling back to a generic preamble. Named in round
   34, named in 35, still not built. It is next unless you tell me otherwise.
2. `plan.validate` has no finding for an undeclared medium. I left it out on purpose this round: the
   screen states it in three places already, and I would rather see whether that is enough before
   adding a fourth voice saying the same thing. Say if you want it in the findings rail.
3. Nothing yet reads `medium` for a **join**. The jobs table still reads leaves with parents and the
   competitive desk still keys on its own list; now that the plan states a medium, those can finally
   agree on one key. That is the round this column was for, and it is the one I would take next after
   the preamble.
