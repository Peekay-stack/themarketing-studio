# Ask Design — round 28, addendum

Sent shortly after ASK_DESIGN_28. **The base changed**, so take `app.dc.html` from the attached
`ASK_DESIGN_28A.zip` rather than the one in the round-28 zip. Round 28's five numbered asks stand
unchanged — this only adds to them.

I found all three items below by opening the Execution screen with real data, after the round-28 note
was already written. None was visible in the file.

---

## A. Two lines I fixed, so you don't merge over them

`app.dc.html:14260-14261`, `prFirstPhase()` and `prFirstKind()`.

These were the residual of the round-26 dict-vocabulary bug. I fixed twelve `.map` sites with `prSeq`
and missed these two, because they used `.length` instead — so they never threw. A dict has no
`.length`, so both quietly returned `''` and the server's list was ignored:

```js
// before — st.phases is a dict, so l.length is undefined
prFirstPhase(){ const st = this.pr().status; const l = (st && st.phases) || []; return l.length ? this.prOpt(l[0]).v : ''; }
// after
prFirstPhase(){ const st = this.pr().status; const l = this.prSeq(st && st.phases); return l.length ? this.prOpt(l[0]).v : ''; }
```

Verified against the live `/pr-status`: `prFirstPhase()` returned `''` and now returns `tease`;
`prFirstKind()` returned `''` and now returns `corporate`.

What it was costing, at `14247`/`14249`: a **campaign** sheet created without an explicit phase was
posted with `phase: ''` and stored with no phase at all, where the screen means `tease`. A
**standalone** sheet was posted with `kind: ''` and the backend's own `kind or "corporate"` default
caught it — so that half was correct by coincidence, and would have stopped being correct the moment
either list was reordered.

This is exactly the failure mode my own comment above `prSeq` predicted — "the few that used `.length`
instead fell through to a hard-coded default and silently ignored the server" — and it survived two
rounds of review because nothing threw and nothing looked wrong.

## B. "Four producers" is hard-coded in two more places

Round 28 §1 named `X_TABS`. Loading the screen showed the *count* is written out separately as well, so
removing the tab leaves the sentence claiming a producer that isn't there:

- `app.dc.html:13241` — `xHeadline: 'One idea, one brief, four producers'`, the Execution page heading.
- `app.dc.html:360` — the home-screen toolkit card: *"One idea platform, then four producers: social,
  POS material, onground and media."* This one names `media` explicitly, in prose, on the first screen
  anyone sees.

Both should come off the same live list as the strip. Something like `X_LIVE.length + ' producers'` for
the heading, and the card's sentence built from the live labels rather than typed out. If you'd rather
keep the prose handwritten, that's fine — but then it has to stop saying `media`, and it should say four
only while there are four.

`api/frontend/app.dc.html:1639`, `3061`, `4176`, `10674` and `11753` also say "four producers" in
**comments**. Those are yours to leave or update as you like; I mention them only so a grep for the
phrase doesn't look alarming.

## C. The top nav is already full — before the Media tab exists

Measured on the live page, with all ten nav items rendered:

| Viewport | Nav needs | Nav has | Result |
|---|---|---|---|
| 1280 px | 713 px | 527 px | overflows by 186 px — **PR is scrolled off-screen** |
| 1600 px | 841 px | 841 px | fits exactly, with nothing to spare |

`nav.hf-nav` carries `overflow-x:auto`, so nothing breaks — the items are all in the DOM and reachable
by scrolling. But at 1280 the PR item is simply not visible, and PR is a whole desk. I'd assumed it was
missing from the nav entirely until I queried the DOM and found it there, seventh of ten.

A "Media" label needs roughly another 77 px including the gap, which puts the nav over even at 1600.
So the Media tab cannot just be appended — the rail needs a decision first, and it is your call which:
grouping (Execution / Sales enabler / PR / Media are arguably one family), an overflow menu, tighter
spacing, or something better. Worth settling before you build the screen rather than after.

Please tell me which way you go, because it affects where I point the hand-off from
`EXPRESSION_GO.media` in round 28 §3.

---

## Base

`ASK_DESIGN_28A.zip` contains the current `app.dc.html` (with item A applied) and both notes. Please
build on that file. If your working copy already has edits against the round-28 base, merge item A in
rather than replacing your file — it is two lines and the diff is above.
