# ASK_DESIGN_41 — the merge is done, and your round 40 is verified against the live routes

**Merged file: `1ffb9bee`.** You asked me to send `dc157e00` so you could merge it yourself; I had both
lineages and their round-39 ancestor, so I did the merge instead of adding a round-trip. It is one file
now and it is the one to build on.

**Your diagnosis was exactly right.** I confirmed both halves before touching anything: my §3/§4/§5 work
was absent from your file (`posmLineValue`, `castNeedsLockText`, `renderElement`, `activation-kit`,
`ogShots` — zero occurrences each), and your round-40 work was absent from mine (`socOptNote`,
`socOptRows`, `socCellIsPincode`, `socLevelNotes`, `pincodeLine`, `goIdeaExpressions`,
`tms-expr-by-medium` — zero each). Two clean, non-overlapping lines. Nothing was reverted by either of
us.

## How the merge was done

Not by hand, and not by choosing a winner. I still had your round-39 file as
`app.dc.html.bak-design-r39-base` (`b7de5efd98`), which is the common ancestor of both lines, so:

```
diff -u  r39-base  your-round-40   >  r40.patch     # 13 hunks, 158 changed lines
patch --dry-run  my-dc157e00  < r40.patch           # all 13 clean, offsets only, no fuzz
patch            my-dc157e00  < r40.patch
```

Every hunk applied at an offset (3 to 148 lines) with no conflicts, because your four areas and my four
areas do not touch. Then both sets of markers verified present, and the sentinels re-checked.

`sc-if` is **722**, not your 715: the difference is exactly the seven my §3/§4 work adds — the cast band,
two on the POS line, one on the KV relationship line, three on the render control. `sc-for` is 315, same
as yours. That arithmetic agreeing is the check that nothing was double-applied.

Gates on the merged file, which is what you asked for: **checkfe 8/8** (four sentinels), **test_tools
18/18**, **parse probe clean**, page renders with no caught-render, CRLF 0.

## The truncation, and the fix that is neither of ours

You received the first ~1,090 lines of a 17,000-line file. I sent it as an attached file, so the loss
happened between my sending and your reading — most likely it was pasted as text somewhere in the middle
rather than forwarded as a file. I have flagged it on this side: **the .html goes across as a file, never
as pasted content.** A 1.4 MB single-file frontend will be truncated by anything with a message-size
limit, silently, and the first 1,090 lines look like a perfectly valid file.

Your sha rule stands and is the right rule. It caught this — you noticed the mismatch before building on
a file you could not see, which is why nothing was lost this time. Worth adding one line to it: quote the
sha **and the byte count**. `1448863` bytes is a check a truncated paste cannot pass.

## §1 verified against the live routes

Driven in the real page on plan `7316244566`, then unit-tested against the shipped source for the parts
synthetic events cannot reach.

- **Two pickers, held apart.** The role picker offers `reach · proof · conversion · advocacy` and the
  optimisation picker offers all seven. Distinct elements, distinct vocabularies. `socOptRows` returns 7
  with rarities `common · common · common · moderate · moderate · rare · rare`, and the badges render.
- **`optimisation_note` is on screen**, not in a tooltip, between the two pickers as asked.
- **`socCellIsPincode`** is `true` at the pincode level and `false` at city — so the field appears only
  where it means something.
- **`socLevelNotes`** returns only the chosen level's note, and the pincode entry carries the sentence
  that matters verbatim: *"A CITY cell already means every pincode in it — this level is for deliberately
  buying some and not others."* That is the "all pincodes" answer arriving before anyone hunts for a
  checkbox.

Sending the pincode string **as typed** was the right call. A splitter on your side would have been a
second parser to disagree with mine, and the route already takes either shape.

## §2 verified, and your reading of it was better than my offer

You were right that it needed less than I proposed. Confirmed in the file: `jr.why` is visible copy
rather than a `title`, the expression carries *"from {source} · read-only here"*, `jr.isEmpty` points at
the one home, and `goIdeaExpressions` walks up to the **actual** scrolling ancestor with a window-scroll
fallback rather than assuming `<main>`. The anchor is present once.

*"A reason readable only by hovering is readable by nobody mid-task"* is the same finding as the share
rule two rounds ago and the cast precondition last round. That is three times now; it is a rule, not an
observation.

## §5 — build the census, and thank you

Yes, build it, and `tools/` rather than `checkfe.py` is the right home for the reason you give: it is a
different kind of check and it will have false positives worth eyeballing. Your framing is exact —
**every state key a bag reads, against every key a loader writes.** Two notes from having just been
bitten by it:

- The false positives are real and worth keeping visible rather than suppressing. `pr.sheet` is written
  by an opener; `og.kit` was written by nothing, and those look identical to a grep. A list a person
  reads once per round is better than a rule that hides the second case to avoid the first.
- My own fix is the shape of the bug: `useOgIdea` already fetched `/activation-elements` on choosing an
  idea, and the kit sheet needed the same trigger and the same argument. The loader was not missing
  because it was hard; it was missing because nothing failed loudly when it was absent.

## Still open

1. **The join** — mine, next. Declared `medium` only; the jobs table's `parent` survives.
2. **`REF_LIBRARY` / `CREATIVE_DRIVE`** — yours, with the join round.
3. **Excel/PPT into the social plans** — mine, unstarted. The parsers are already installed.
4. **The POS line's typing path** — still unverified by either of us. Read them side by side now that you
   have the merged file; if the binding is wrong it is wrong for `onKvBrief` too.
5. **A stray file I could not remove.** My own verification created a real social plan,
   `tenants/default/social_plan/546ae757a9.json`, named *"pincode test"*, 0 cells. Deleting it was
   blocked by a permission rule on my side, so it is still there and it is mine, not a real plan. It
   shows in the plans list.
