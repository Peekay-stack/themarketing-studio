# Ask — handover 7. Six tasks, all frontend.

**Base this on the `app.dc.html` in this folder, not on the one you sent.** Yours did not carry a logo
fix that was made after your base was taken; I merged your Next-layer work onto it rather than the other
way round, so this file has both. `FOR_DESIGN_NOW.md` in this folder has the reasoning for everything
below — this file is just the work.

Your handover 6 is in and verified against a real server-backed house, not just `demoStrategy`: Core
message → **"Next: Emotional message →"** (the double-unblock, right), Emotional RTBs → Functional RTBs,
layer 8 → "Start a plan from this house →". Nothing to redo.

Every backend route named here exists and is tested. Nothing below is blocked on me.

---

## 1 · Idea platform: three cards, not one field

**Now:** the screen drafts one platform into one field. A single draft becomes the answer by being the
only thing on the page.

**Build:** three cards from `POST /idea-draft`, and two visibly different controls.

```
POST /idea-draft { house, core?, brief?, n=3, build_on? }
  -> { options:[ { id, name, line, mechanic, kind, caveat, source,
                   built_from, built_from_name, stood_on } ],
       count, build_on, building_on,
       …first option also flat and under `idea` — your current code keeps working unchanged }
```

- **Try again** — call it again with no `build_on`. Fresh routes; the three are forced to differ in kind.
- **Build on this** — one per card, passes `build_on: <that card's id>`, or the whole card object inline
  for a draft that has not been adopted yet. Results come back carrying `built_from_name`; **show it**
  (*"developed from The 4AM Milk"*), otherwise an iteration is indistinguishable from a re-roll.

Two motions, two controls. That distinction is the entire ask — "iterate the existing one as well as
develop fresh ones" was the words used.

Show `kind` on the card. It is what makes three routes legible as three routes rather than three
sentences. Keep echoing `source` on adopt (still open from §4.2, two handovers ago) — an unedited
drafted line should not adopt as the author's.

---

## 2 · Social: more than one post, and say what it stands on

**Now:** one post per selected platform. **Your prompt is otherwise fine and I have not touched it.**

**Build two things:**

1. **Ask for three per platform** in the JSON shape your prompt requests. The count comes from your
   requested shape, not from the instruction — so the shape is where it has to change. Three that do
   different jobs: the one that recruits, the one that proves, the one that belongs to an occasion.
2. **A line above the panel naming the grounding** — *"Written against 'The 4AM Milk', for the channels
   in the plan."*

On (2): the posts are already grounded. Every prompt you send through `/complete` now receives the
chosen house messages, the sourced RTBs, the must-avoid list, the adopted idea platform with its
mechanic and its existing expressions, and the plan's channels, audiences, phasing and measures — as
binding constraint that outranks your instruction. Verified by sending your social prompt **verbatim,
unchanged**: three posts came back, all expressions of the adopted platform.

So nothing about the prompt needs rewriting for grounding. But invisible grounding gets re-typed by the
person on top of it, which is why (2) matters as much as (1).

---

## 3 · POSM: wire the panel up

**Now:** `produceAdaptations` makes no outbound call at all — not `/scene-still`, not `/posm-keyvisual`,
not `claude.complete`. That is the whole of *"POSM is not able to generate image unlike social."*

**Build three things.**

**(a) Routes, with layout and line.**

```
POST /posm-keyvisual { house?, platform?, execution?, brief?, n=3 }
  -> { options:[ { id, name, desc, line, layout, layout_note } ],
       note, layouts:{…}, stands_on:{ text, source } }
```

**Send `{}` and it works.** The backend resolves what the piece stands on: the platform's POSM
expression → the platform's line → the house's POSM message → the house's core → what was typed, **last**.

> This is the fix for *"it requires you to enter the proposition again"* and for *"default prompt should
> be idea platform and in case someone is skipping that then it should be messaging house."* It behaves
> exactly that way; verified with an empty body → `stands_on.source: "the idea platform"`.

So the prompt box becomes an **override, pre-filled, with its source shown above it** — not an empty
required field. Asking twice is how two copies of one proposition end up disagreeing.

**(b) The image.**

```
GET  /posm-formats -> { formats:{key:{label,ratio,note}}, layouts:{key:note}, styles:[…] }
POST /posm-image   { route|prompt, layout, line, format, ratio, style, house?, platform?, execution? }
  -> { image_url, provider, prompt, line, layout, layout_note, placement,
       format, ratio, subject, stands_on:{text,source}, note }
  501 no provider · 400 nothing to render · 502 both providers refused
```

Render the format and layout choices **from `/posm-formats`**, not hardcoded, so adding a size is a
backend change. Six formats: shelf strip · dangler · A3 poster · wobbler · gondola header · standee,
each with the ratio it needs.

**(c) Show the line beside the image, not in it.**

`/posm-image` deliberately does **not** render the headline into the picture. Image models garble type,
and they garble Devanagari and Telugu far worse than Latin — a POS piece going to print with a mangled
headline is the most expensive failure this product can cause. The image is composed with *reserved
space* where the chosen layout puts the line; `line` and `placement` come back beside it.

So present them as a pair: the image, and under it the line with where it goes. That is how a real studio
works, so it should not read as a limitation — please word it that way rather than as a caveat.

Five layouts, each carrying what it survives:
`type-locked-base` · `type-over-top` · `type-beside` · `type-only` · `product-only`.
The model picks one; **let someone override it.**

---

## 4 · On-ground: show what it would stand on

The gate is correct and stays: `POST /activation-idea` with an empty box returns **400** — *"Write the
idea first — this sharpens one, it does not supply one."* On-ground is the one execution where the idea
is a person standing in a street doing a thing, and a model that supplies it supplies something nobody
in the room believes in.

**One small build:** that 400 now also carries `stands_on: { text, source }` — the platform line the
activation *would* be built against. Show it beside the empty box **as context, not as a default value**.
It gives somebody something to write from without writing it for them.

`/activation-idea` and `/activation-element` now both receive the platform and the full IMC plan —
channels, audiences, phasing, measures, brand/activation split — so a sharpened idea is an expression of
the platform rather than a good idea sitting next to it.

---

## 5 · The overlay pattern, if you have appetite

I fixed the reported instance; the pattern is yours and the structural fix is better than mine.

Every drawer and modal here is *backdrop carries the close handler, panel is its child*, so a click
inside the panel bubbles out and closes it. I put `stopBubble` on four panels (settings, prompt drawer,
brief picker, launcher) and deliberately left the lightbox and brand menu alone.

The cleaner version is to make the backdrop a **sibling** of the panel rather than its parent. I did not
do that because it is your layout and a four-panel one-line fix was the change I could verify. If you
restructure it, drop `stopBubble` — it exists only to patch the nesting.

Worth knowing why it mattered: most controls survived it by accident (an accent swatch still saved on its
way out). The logo upload could not — it needs its `<input type="file">` still in the document when the
picker resolves, and the panel unmounting took the input with it.

---

## 6 · Still open from before, unchanged

1. **The Studio Settings brand form** (`DESIGN_NEXT §12`). Seven fields: what the category competes on ·
   what you can prove and what proves it · your regulator and banned words · purchase cycle and
   decider/payer/user · your real channels · the cheap alternative you lose to · price tier. Eight more
   are derivable from the brief and the house, so pre-fill and let someone correct rather than ask twice.
2. **The live-action shots screen** — seven `/shot-*` routes still have no UI.
3. **The four `house-docx` / `plan-docx` download buttons.**

---

## Before you send

```bash
python tools/checkfe.py       # syntax, pairing, duplicate members, bag spread
python tools/contract.py      # backend shapes vs what you iterate
python tools/test_tools.py    # 17 tests, includes both of the above
```

`contract.py` now also types the house and plan **list cards**, because two payloads were quietly
reporting finished work as empty — a house with all eight layers decided rendered as *"0 of 8 layers
decided — Not started."* Your code was right; I was sending `decided` where you read `chosen_layers`.
Fixed, and now checked.
