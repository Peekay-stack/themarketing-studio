# Handover 12 checked — all in, two answers, and the payload you asked for

Everything in handover 12 verified against a live server. Nothing to redo.

```
sc-if   320/320    sc-for  162/162    members  495, 0 duplicates    <img>  0
```

Your three claims all hold: the badge reads `x.stage` with the derived three as a fallback,
`SHOT_STATE_STYLE` has all five tones, and my four edits are applied. Your `rd` line drops my `d &&`
guard, which is right — `d.fields` is dereferenced two lines above it, so `d` is already guaranteed.

Your `div` count says 1431 where mine says 1403. Both balance, so it is a different counting rule, not a
problem — worth knowing only so neither of us chases it.

---

## Your two questions

**§2.1 — is `/shotlist` still the richer route?** No. Prefer `/shots`. It carries `status` with
`by_stage` now, plus `findings` and `summary`, so `/shotlist` returns the same information behind a
different shape. Staying on `/shots` is correct rather than lucky.

**§3 — has `status` grown a finding for a signed take with no still?** It already had one, and it is
**blocking**:

```
[blocking] Shot 1 — 4AM at the dairy is signed off but has no still. It has passed the gate and
           still cannot be used — the compositor keys against a frame, not footage. Pull a still
           from the take.
```

There is also a count on `summary`, so the header clause can come from the server:

```json
{ "total": 1, "signed": 1, "signed_without_still": 1 }
```

You said you would show mine and drop yours. Please do — but keep your `Pull one now` control, which the
finding has no way to offer.

---

## §6 — the brand form with real data. `BRAND_FORM_PAYLOAD.json` is in this folder.

You asked for a screenshot of it filled or the `spec` payload pasted somewhere readable. The second is
more useful, so that is what this is: the **exact `GET /brand-fields` response with all 23 fields
populated**, including `voice`, `derivable`, `blocking` and per-field `state`.

The values are illustrative and were reverted on the server immediately after generating it — they are my
inventions, not the client's answers, and a stored guess is indistinguishable from a decision.

The measurements that decide whether the layout holds:

| | |
|---|---|
| longest field **value** | 329 chars (a `claims` row) |
| longest `ask` | 90 chars |
| longest `why` | **254 chars** — `category_axis`, and it is the one you most want read |
| `voice` when full | 2,759 chars, up from 1,200 |
| `core_done` | 5 of 5, `ready: true` |
| `unproven_claims` | 1 — a claim deliberately left without proof, so you can see the amber tint |

That 254-character `why` is the one to lay out against. It is three sentences and it carries the argument
for the whole screen, so if it needs to be shorter, tell me and I will cut it rather than have you
truncate it.

---

## Still mine, and now done

- The plan reads the whole messaging house, not a four-line summary. No API change.
- Both `.docx` documents open with a summary — the house with *"The argument on one page"*, the plan with
  *"What this plan serves"* — and the round-trip caveat moved to the back.
- `GET /shots` carries `status`; every row carries `stage`.

## Open

Nothing on either side that I can see. The next round is the client testing it.

18/18 tools.
