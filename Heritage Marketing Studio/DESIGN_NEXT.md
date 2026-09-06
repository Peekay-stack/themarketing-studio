# The Marketing Studio — what changed, and the next screen

**Standalone extract.** These are sections 11 and 12 of `DESIGN.md`, pulled out so you do not
have to re-read 38KB to find what is new. `DESIGN.md` remains the single living document and
everything else in it still stands — brand system, the bag, the tooling, the do-not-undo list.

Two things here: a contract I got wrong and have fixed (no work for you), and one new screen.

# 11. Contract fix — `options`, `chosen` and `rows` are arrays

**Live now. No frontend change needed — you built this correctly and I returned the wrong shape.**

`status.layers[]` returned counts where you read arrays:

```js
const rawOpts = L.options || …           // got the integer 4
const nOpt = (ls.options || []).length   // (4).length -> undefined -> falsy
```

So the option panel had nothing to map and the rail said *"nothing offered yet"* — while the findings,
which counted the node directly, said *"4 options generated"*. A layer with work in it claiming to be
empty, which reads as data loss.

Now:

| field | shape |
|---|---|
| `status.layers[].options` | the option objects — `{id, text, note, source, tag, added}` |
| `status.layers[].chosen` | the chosen ids |
| `status.layers[].rows` *(plan)* | the actual rows |
| `n_options` · `n_chosen` · `n_rows` | counts, if you want them cheaply |

**Also removed:** the finding *"N options generated, none chosen"*. The rail says it, the cards show it,
and the counts carry it — as a finding it was duplication arriving as a band above the layer somebody was
working in. Findings are for things a person must act on, not for narrating the screen back to them.

My documentation caused this. §6.1 described the node's list of options and the status layer's `options`
with the same word and two different shapes. Fixed above.

---

# 12. Studio Settings — brand and category

**This is the new work.** Everything the studio generates is now grounded in a brand profile
(`GET /brands`), and the profile is backend-only — there is no screen. Four profiles exist; switching
between them needs a `curl`. That is the gap.

## Why this matters more than a settings form usually does

The studio has to answer *"make something pure"* for a milk brand and *"make something that holds"* for a
cement brand without being told which is which. That only works if it knows what the **category competes
on**. Purity is not a Heritage fact — it is the axis of the entire dairy category, the thing every
reason-to-believe argues on and every demo dramatises. Cement's axis is consistent strength. Apparel's is
fit and fabric. Beauty's is efficacy without irritation.

Capture the axis and the studio adapts to the category. Miss it and every output is competent and
generic — which is the one failure that would make the product feel ordinary.

So this screen is not configuration. **It is the input that decides whether the product is any good.**

## The design principle: every field says what it buys

Do not build a long form. Build a form that explains itself — because a field somebody skips is worse
than a field that does not exist. It silently degrades every output downstream and nobody knows why.

Each field carries a one-line *what this buys you*, and the screen shows a **readiness state** rather
than a completeness percentage:

> **Ready to ground copy.** Not ready for the proof gate — add at least two substantiated claims.
> Not ready for a trade plan — name this category's channels.

Readiness beats a progress bar because it names the capability that is missing rather than the boxes.

## The fields, in the order they should be asked

`*` marks the minimum five. With those the model produces category-true, legally-safe, provable work.
Everything else improves it.

### A · Identity

| field | what it buys |
|---|---|
| `name` * | every prompt and every document header |
| `hero_product` | what a film or a pack shot is actually of |
| `category` * | the category frame — what is credible, what is regulated |
| `market` * | occasions, idiom, retail, currency. Prevents generic-global copy |
| `languages` | which languages a script may mix |

### B · The claim space — the *"make something pure"* group

| field | what it buys |
|---|---|
| `category_axis` * | **the most valuable field on the screen.** What this category competes on, in a phrase. Drives every RTB, every demo proposition, every platform mechanic |
| `claims[]` * | `{claim, evidence, verified_by}` — **the proof gate reads this.** Without two substantiated claims every RTB returns flagged unsourced and no execution can be given proof work |
| `substantiation_standard` | what proof this category demands — lab report, BIS certificate, clinical study, none |
| `regulator` | FSSAI · Drugs and Cosmetics Act with CDSCO · BIS · ASCI · Legal Metrology. Decides what may be said |
| `forbidden_words[]` * | *cures · permanent · fairness · guaranteed.* Hard vocabulary bans, checked rather than hoped for |
| `words_we_own[]` | the phrases that make copy sound like this brand rather than the category |
| `mandatories[]` | what must appear on every piece |

### C · The buying situation

| field | what it buys |
|---|---|
| `purchase_cycle` | daily · impulse · replenishment · seasonal · considered · once-in-a-lifetime. Drives phasing **and** the brand/activation split |
| `decider` / `payer` / `user` | three fields, deliberately. In cement the mason decides and the homeowner pays — miss that and the plan is aimed at the wrong person |
| `switch_trigger` | what actually makes somebody change brand |
| `occasions[]` | the real purchase occasions, not the calendar's |
| `price_tier` | mass · mid · premium. Changes both tone and channel |

### D · Route to market — this is what fixes the trade sheet

| field | what it buys |
|---|---|
| `channels[]` | `{name, role, share_now, intermediary, what_they_earn}`. **Five of the eight FMCG channels are wrong outside FMCG** — a cement brand has dealers and sub-dealers, not kirana and dark stores. This field replaces the hardcoded list |
| `influencers_at_purchase[]` | mason · pharmacist · salon · dealer · the platform's algorithm |

### E · Competitive frame

| field | what it buys |
|---|---|
| `competitors[]` | becomes `{name, owns}` — knowing what each has already claimed is what stops us claiming it back |
| `default_belief` | the category belief we are arguing with. Feeds the plan's `believes_now` and the whole current-to-desired shift |
| `unbranded_alternative` | loose milk, the local tailor, the mason's usual bag. Often the real competitor in India |

### F · Craft and codes

| field | what it buys |
|---|---|
| `tone` | voice on every asset |
| `visual_codes[]` | pack cues, colour, iconography — what makes a frame recognisable |
| `never_show[]` | *milk being wasted · unsafe site practice · before-and-after implying a medical outcome.* Enforced at ideation, where it is cheap |
| `colours{}` | the client's palette, kept separate from the studio's |

## What the screen needs

- **A brand switcher**, in the header or in Settings. `GET /brands` lists them, `POST /brand-active {id}`
  switches. Exactly one active — the studio has to know which brand it is working on.
- **Grouped panels A to F**, collapsed by default except A and B. B is where the value is.
- **The readiness strip** above, rendered from `status.readiness`.
- **`claims[]` as repeatable rows**, not a textarea — three columns, `{claim, evidence, verified_by}`.
  An empty evidence cell is a finding, because a claim with no evidence is exactly what the proof gate
  exists to catch.
- **`channels[]` as repeatable rows** too. Seed from a category default where one exists and let the
  author edit — never lock them.
- **`GET /brands` returns `voice` per brand** — the exact text a generator is told. Put it behind a quiet
  *what the model is told about this brand* link. A tool that grounds itself invisibly is asking to be
  trusted rather than checked, and this is the screen where seeing it matters most.
- **Empty is not zero, again.** An unfilled field says what it costs — *"no category axis: RTBs will
  argue on nothing in particular"* — never a blank.

## What I will build before you start

1. The fields above on `brandprofile.py`, with `claims[]` and `channels[]` as structured rows.
2. `voice_block()` extended to render them in order of authority, so the axis and the claim space reach
   every generator.
3. `status.readiness` — the capability list, so the strip has something real to render.
4. The proof gate reading `claims[]`, so a substantiated claim genuinely clears an unsourced RTB.
5. `sales.CHANNELS` falling back to `profile.channels[]` when the profile has them — the taxonomy fix.
6. Filled seeds for all four brands — dairy, apparel, beauty, cement — so you design against real
   content rather than lorem.

Contracts land in this document before you build. Nothing here changes an endpoint you already call.
