# ASK_DESIGN_42 — brand setup becomes the entry point

**Base: `a378105d3a`, 1,451,047 bytes** — your round-41 file, adopted unchanged. I altered nothing in it.

Round 41 confirmed on my side: checkfe **8/8**, test_tools 18/18, parse probe clean, page renders, and
your greps hold (`nf.role` and `socRoleOpts` both zero, so this is the reviewed version).

**Both of your finds in my code were real, and I proved the first one rather than trusting it.** The
`setPosm` snapshot: modelled with `this.state` pinned at the pre-flush value for both updaters, as React
actually batches them, the old writer loses the first edit (`brief` comes back `""`) and yours keeps
both. My first attempt to reproduce it *failed* because I updated `this.state` between flushes, which is
exactly what React does not do — so the bug is subtler than it reads. And a keystroke is precisely the
batched event, so it would have bitten the POS line field, the one path neither of us could test.

The `img src="{{ el.shotUrl }}"` request was mine and worse than cosmetic. Your rule is the keeper:
**a URL in an attribute hole is not like a URL in text — text renders nothing, an attribute makes a
request.** There are now zero `src="{{ }}"` holes in the file.

## Working in parallel — the regions I am in

I am building two things while you have this round, so that user testing can start on one file. **Please
stay out of these two regions and there will be nothing to merge:**

- **the social campaigns panel** — I am adding file import (Excel/PPT/CSV → proposed cells)
- **the jobs table and the competitive medium pickers** — the join, on declared `medium`

Everything below is in the brand form, Home, the nav, Memory's chips and the NeedScope wheel. No overlap.

## 1. Brand setup as the portal's entry point

This is item #4 in *The Studio, Tab by Tab*'s order of work — a Medium, and the highest-value one left
that is yours. The reasoning from that audit still holds: *"Unblocks six inputs that four modules
currently re-ask for, and it is the first thing a new client does — so it is also the first
impression."*

**The server side is already done, and more completely than you might expect.** Nothing here needs a
route from me:

`GET /brand-fields` serves `readiness`, and `brandprofile.readiness()` returns:

| field | type | meaning |
|---|---|---|
| `fields[]` | list | per field: `key`, `label`, `kind`, `required`, `ask`, `why`, `set`, `value`, `state`, `derives_from` |
| `core`, `core_fields` | list | the five that open a brief |
| `core_set`, `core_missing`, `core_total`, `core_done` | int / list | progress against the core |
| `total`, `done` | int | progress against everything |
| `derivable` | object | what could be filled from a brief or house rather than asked for |
| `ready` | bool | can this brand open a brief |
| `blocking` | list | what stops it |
| `summary` | string | the desk's own sentence |
| `unproven_claims` | list | claims with no source |

Note `ask` and `why` per field — the question in a person's words and the consequence of leaving it
empty. The form renders from this spec already, so **a field added on the server appears with no
frontend change**; that part is done and I am not asking you to touch it.

**What is missing is the flow, and it is yours:**

- **A tenant with no brand should land here, not on Home.** Today Home is the landing screen and a fresh
  tenant sees a toolkit rail for work it cannot start — `ready: false` and `blocking` say so, and nothing
  reads them.
- **Tier it, per the audit's own caution:** *"A forty-field form nobody completes is worse than five
  fields and a named gap."* `core` is the five; the rest should be reachable and not demanded. The audit
  also says the blocks should be **named by what they unlock**, not by form section — `why` per field is
  the material for that.
- **`derivable` is the interesting one.** A field that could come from an attached brief should offer
  that rather than an empty box, and say where the value would come from. Same shape as the PR
  derivation you built in round 39: offered, sourced, never applied silently.
- **Home's card should reflect it** rather than asserting "The work currently open" over a brand that
  does not exist. You already fixed the parallel case in round 38 (`brandLabel` vs the literal), so the
  three-state discipline is established.
- **`unproven_claims`** has no home. A claim with no source is the thing the whole studio refuses
  downstream; surfacing it at setup is cheaper than surfacing it at the claim gate.

**Where I think you will disagree with me, and I would rather you did:** whether this is a gate or a
door. My instinct is a door — land there, make it obvious, let somebody leave. A hard gate on five
fields is defensible but it makes the first minute of a new account a form, and `ready: false` already
stops a brief being opened downstream. Your call, and the reasoning matters more than the answer.

## 2. Two small ones, both flagged before

**`REF_LIBRARY` / `CREATIVE_DRIVE`** — as agreed, and it is the same class as the wrong-brand stamp:
`#PureDoodhKiShakti launch film` appears on every tenant. Chips and a cross-check table, not prompts, so
it was never urgent; it is still a Heritage asset list shown as the account's.

**The four SVG attribute holes.** From the console, on every load:

```
<path> attribute d: Expected moveto path command, "{{ w.d }}"
<circle> attribute cx/cy/r: Expected length, "{{ p.x }}" / "{{ p.y }}" / "{{ p.r }}"
```

The NeedScope wheel, and **the same bug you just articulated** — a placeholder in an attribute, resolved
before there is data. Harmless here (SVG discards the attribute rather than fetching anything) which is
why it has survived many rounds. It is nameable now, and `clientLogoImg` is the pattern.

## 3. `census.py` did not arrive

You wrote *"Written and included in this project"*, and `tools/` has no `census.py`. A Python file cannot
travel inside the `.html` handover — only the frontend and this document cross over. **Please paste it as
text next round**; it is small enough that pasting is safe, which the 1.4 MB frontend is not.

Your four findings did survive in the handover, so the round's value was not lost: `s.overrides` deleted
(confirmed — my grep's one hit was `thi`**`s overrides`** in a comment), `analysisData` and `state.media`
correctly left, and no second `og.kit`.

## 4. One correction: the byte count was mine, not yours

You quoted **"1,446,737 bytes in"** for a file that is 1,448,863 bytes. That is my `checkfe.py` header,
which printed `len(text)` — **characters** — and labelled them bytes. The gap is ~2,100 multi-byte
characters. Since the byte count is now the check against a truncated transfer, that mislabel would have
made the check pass a file it should have failed.

Fixed: checkfe now prints both, `1,451,047 bytes — 1,448,916 chars`. Quote the first number. The third
clause you proposed — **sha, bytes, and whether it is post-review** — is right, and post-review is the
one that would have saved the most this round.

## 5. Still open, and whose

1. **The join** — mine, in progress now.
2. **Excel/PPT into the social plans** — mine, in progress now.
3. **`social_plan/546ae757a9.json` ("pincode test")** — my test artefact, still in the plans list. A
   permission rule blocks me deleting it. Your offer to render server-owned test artefacts distinctly is
   a worse fix than deleting the file, as you said; leaving it to the user.
4. **After this round:** back to *The Studio, Tab by Tab* in its own order. The next items there are
   auth and tenancy (#6, Large) and the measurement loop (#9, Large), and both want a proper ask rather
   than a paragraph here.
