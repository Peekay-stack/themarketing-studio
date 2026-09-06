# Handover 16 — the idea platform screen. One crash fixed, four things built.

Built on the `app.dc.html` you sent, including your §0 fix — kept as-is, verified it was still needed
(the root project copy hadn't picked it up yet, so it's applied there now too).

---

## 0 · The crash — kept, and confirmed necessary

Your fix (hoist `tagList` above its first use, with the comment explaining why) was already correct.
The project's own `app.dc.html` still had the old ordering — same bug, not yet patched — so the same
hoist was applied there and the now-duplicate declaration 49 lines down was removed.

## 1 · Steer box — built

A textarea now sits above *Try again — three fresh routes*, placeholder matching your copy. `onIdeaSteer`
writes it to `idea.steer`, which is never cleared on a round, so it stays filled for the next adjustment.
`ideaDraft` sends it as `steer` on the request body — the same body for both **Try again**
(`draftIdeaFromSources`) and **Build on this** (`ideaBuildOn`), so one box drives both, as asked.

## 2 · Pillar / RTB on the route cards — built

Each option card now shows a `pillar` badge (emotional/functional/both, colour-coded) in place of the old
`kind` chip — `kind` still renders as a fallback only when an option has no `pillar` (old data won't go
blank). A "rests on: `{rtb}`" line sits under the idea line. `caveat` already rendered amber before this
round and needed no change.

## 3 · Expression by medium — built new

Nothing existed for this before — no fields, no route wired. Added a **Step 4: Expression by medium**
block: five slots (video, social, posm, activation, incentive) as labelled textareas, each editable by
hand. *Write these for me* calls `/platform-express-draft` with no `media` key; a per-slot *Rewrite this
one* sends `media:[key]`. Both include the steer box's text if filled. Response's `expressions` object
merges into local state; nothing calls the setter (`/platform-express`) yet — hand-typed edits are
held in state only. Flag if you want keystrokes persisted there too; wasn't clear from the ask whether
that was in scope for this round.

## 4 · Two-column testing — built

Added an *Ask the model to test this* button above the five tests (`/platform-judge`). Where the model
has answered, a two-column strip appears under that test's note: **You** (the existing clickable badge,
now read-only in this second view) beside **The model** (verdict badge, `note`, and `fix` when the verdict
is `weak`/`fails`). A row in `disagreements` gets a dashed amber background and a "Disagrees with you"
flag. `detail` renders as a banner above the list when present. Nothing here overwrites your existing
`tests[key].verdict` — that stays the person's decision, exactly as before.

## 5 · Docx — no change needed

`ipHasDl` already gates on `ip.id`, and `downloadDoc` already requests `/{kind}-docx/{id}`. Since the
route now accepts set/house/platform ids interchangeably, this needed nothing on the UI side.

---

## Not done / flagged

- Manual edits to the five expression slots are not sent to `/platform-express` (the setter) — see §3.
- No optimistic/error state shown yet for `/platform-judge` or `/platform-express-draft` beyond a toast
  and a busy label — same level of polish as the rest of this screen, but call it out if you want
  per-field save indicators like `/plan-row` got in round 15.

```bash
python tools/checkfe.py && python tools/contract.py && python tools/test_tools.py
```
not run on this end — no local copy of `tools/`.
