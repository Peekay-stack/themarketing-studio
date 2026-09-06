# Handover 11 — one fix, and four small edits to keep

Handover 10 is in and verified against a live server. The brand profile screen and all three live-action
extras work. Nothing needs rebuilding.

Work on the `app.dc.html` you already have.

---

## The one thing to fix

**A shot row with a selected take shows `PLANNED`.**

The row badge and the stage strip disagree, and side by side it reads as a contradiction:

```
strip:   2 planned · 0 briefed · 0 shot · 1 selected · 0 signed
row 1:   PLANNED          ...  TAKES: take 1 · take 2 keeper
```

Both are right by their own rule. The badge derives `state` — three values, needs a take URL. The strip
reads `by_stage` — five values, and it knows about a selection. A take logged on set without a file
attached is exactly the case where they part company.

**The fix: every row now carries `stage` from the server.** Read that for the badge instead of deriving it.

```
stage:  planned | briefed | shot | selected | signed
```

Keep deriving `state` for anywhere you want the simpler three. Both are computed, neither is stored, and
now there is one answer for the badge rather than two.

---

## Four edits I made to your file — please keep them

All small, all verified in the browser.

1. **`loadShots` stores the status.** `shotStatus` was read by the stage strip and never written, so
   `hasStages` was permanently false and the strip never rendered at all. `/shots` now returns `status`
   (the same payload `/shotlist` gives), and the loader keeps it:
   ```js
   if (d && d.status) this.setState({ shotStatus: d.status });
   ```
   Your strip code was correct — it just had nothing to draw from.

2. **`loadStudioServer` keeps `readiness`.** The drawer's brand-profile card read the form's own payload,
   which is only fetched when the form opens — so it said *"0 of 5"* on a profile with two answered until
   you had been inside and come back.
   ```js
   if (d && d.readiness) this.setState({ bfReady: d.readiness });
   ```

3. **A fallback so that card can use it**, in the same `renderVals` block as `bfCoreCount`:
   ```js
   const rd = (d && d.core_total) ? d : ((s.bfReady || d) || {});
   ```
   with `coreDone`, `coreTotal`, `ready` and `bfSummary` all reading `rd`.

4. Nothing else. `checkfe` still gives **495 members, 0 duplicates**, 319/319 `sc-if`, 1402/1402 `div`.

Two of those three were my fault, not yours: `/shots` should always have carried a status, and I told you
`readiness` rides along on `/studio-settings` without saying it was the thing to build the card from.

---

## Backend that changed, with no UI work in it

- **The plan now reads the whole messaging house**, not a four-line summary of it. The per-medium messages
  go in verbatim, and generating the channels layer now returns one channel per medium with a note where
  the house has no message for it. No API change.
- **Both `.docx` documents open with a summary.** The house leads with *"The argument on one page"*, the
  plan with *"What this plan serves"*, and the round-trip caveat moved to the back — it was the first five
  paragraphs of every download. No API change; the four buttons you already have produce these.
- **`GET /shots` returns `status` and every row carries `stage`.** That is the fix above.

---

## Still open, and yours when you want it

1. The live-action screen's remaining polish, if any.
2. Nothing else is blocked on me.

```bash
python tools/checkfe.py && python tools/contract.py && python tools/test_tools.py
```

18/18.
