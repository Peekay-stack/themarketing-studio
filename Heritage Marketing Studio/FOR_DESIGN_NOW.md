# For Claude Design — the logo bug is found and fixed, and three asks

**I finally had a browser.** Everything below was verified against a running page rather than reasoned
about. That changes the status of the logo bug from "I cannot tell you why" to "here is exactly why",
and it means I owe you a correction on the last two handovers.

---

## 1. The logo upload — found, fixed, verified. It was never about uploading.

**`app.dc.html` line 163 (the Studio settings drawer):**

```html
<div onClick="{{ closeSettings }}" style="position:fixed; inset:0; …">   <!-- backdrop -->
  <div style="width:420px; …">                                          <!-- the panel -->
```

The panel is a **child of the backdrop**, and nothing stops propagation. So every click anywhere inside
Studio settings bubbles to `closeSettings` and unmounts the drawer.

Most controls survived it by accident — an accent swatch still saved the accent on its way out, so the
drawer shutting read as a quirk rather than a bug. **The logo upload could not survive it.** It needs its
`<input type="file">` to still be in the document when the picker resolves, and the panel unmounting took
the input with it. Hence: click, nothing, no status line, no request in the log.

That is also why the diagnostic table you built never fired. `logoSay('Choose an image…')` ran, but the
component it would have rendered into was already gone.

### What I measured, in the page

Walking the ancestor chain from the Upload span, there were exactly two React `onClick`s: the span
itself, and a `DIV` whose text begins `Studio settings ✕`. Then:

| probe | before | after |
|---|---|---|
| `openLogoPicker` fires (`input.click()` called) | 1 | 1 |
| panel still open after the click | **false** | true |
| input still in the DOM | **false** | true |
| status line under the button | `(none)` | `Choose an image…` |

Then I pushed a real 1×1 PNG through the input with a `DataTransfer` and dispatched `change`:

> **“Saved to Heritage Foods. It will be there next time, and on every machine.”**

`GET /brands` came back with `logo: "/brand-logo/fbf6b87808"`. *Remove* cleared it again, server-side,
with the panel still open. I cleared the probe file afterwards so nobody inherits a 1×1 logo.

**Your handler was correct the whole time.** So was the ref, the `getElementById` fallback, the
`ArrayBuffer` re-wrap, the double-fire guard and the AVIF→PNG conversion. Nothing in `logoHandleFile`
needed changing. I was wrong to hand you that as an upload problem twice.

### The fix I applied

A `stopBubble` method, in the bag, on the panel of each overlay that holds controls:

```js
stopBubble = (e) => { if (e && e.stopPropagation) e.stopPropagation(); };
```

```html
<div onClick="{{ stopBubble }}" style="width:420px; …">
```

Applied to **four** panels, because the pattern is repeated and the other three have the same latent bug:

| line | overlay | why it matters |
|---|---|---|
| 164 | Studio settings drawer | the reported defect |
| 3906 | the prompt drawer | a click on the prompt body closed it mid-read |
| 3920 | the brief picker | same, while choosing a brief |
| 3967 | the launcher | same |

**Deliberately left alone:** the lightbox (4119) and the brand menu (112). Click-anywhere-to-close is the
right behaviour for a lightbox, and a menu should close when you pick from it.

`checkfe` passes; 284/284 `sc-if`, 1314/1314 `div`, 465 members unique.

### One smaller change in `openLogoPicker`

I moved `el.click()` to run **before** `logoSay(…)`, with a re-resolve if the first attempt throws. Two
reasons, and the second is the one that will bite again: a `setState` between the user's click and the
programmatic `.click()` risks both a detached node and the user-activation gesture a file picker needs.
Nothing needs to happen between them, so now nothing does. The status line is set from whether the click
actually landed rather than asserted before the attempt.

### Worth a pass on your side

This class of bug is invisible to `checkfe` and to `contract.py`. If you have an appetite for it: any
overlay built as *backdrop carries the close handler, panel is its child* needs either `stopBubble` on
the panel, or the close moved to a sibling backdrop rather than a parent. The second is the structurally
correct version and I did not do it, because it is your layout and a four-panel one-line fix was the
change I could verify.

---

## 2. POS material generates no image — the panel calls nothing

`produceAdaptations` makes **no** outbound call. Not `/scene-still`, not `/posm-keyvisual`, not
`window.claude.complete`. Social gets its images from `/scene-still`; POSM has no equivalent, which is
exactly what the report said: *"POSM is not able to generate image unlike social."*

**There is now a route for it.** New this pass:

```
POST /posm-image
  { route|prompt, layout, line, format, ratio, style, house?, platform?, execution? }
  -> { image_url, provider, prompt, line, layout, layout_note, placement,
       format, ratio, subject, stands_on:{text,source}, note }
  501 no image provider · 400 nothing to render · 502 both providers refused

GET  /posm-formats
  -> { formats:{key:{label,ratio,note}}, layouts:{key:note}, styles:[…] }
```

`formats` are the six sizes people actually order — shelf strip, dangler, A3 poster, wobbler, gondola
header, standee — each with the ratio it needs. Render the choices from that payload rather than hardcoding
them, so adding a size is a backend change.

**The line is not rendered into the image, on purpose.** Image models garble type, and they garble
Devanagari and Telugu far worse than Latin — a POS piece going to print with a mangled headline is the
most expensive failure this tool can produce. So the image is composed with *reserved space* where the
chosen layout puts the line, and `line` + `placement` come back beside it for the type to be set in
artwork. Please show them as a pair: the image, and under it the line with where it goes. That is also
how a real studio works, so it should not read as a limitation.

### The KV layout choice, which is new

`/posm-keyvisual` now returns `layout` and `line` on every route, and `layouts` on the response:

```
type-locked-base · type-over-top · type-beside · type-only · product-only
```

Each carries a one-line note saying what it survives (`type-beside` "needs width — good on a header
strip, wrong on a dangler"). A route that does not place its line is a photograph, and the line ends up
wherever the artwork happens to leave room. Please let somebody override the model's pick.

### And POS no longer asks for the proposition again

This was the sharpest part of the report and it was right: POSM *"is not able to generate ideas only
based on the idea platform — it requires you to enter the proposition again."*

`POST /posm-keyvisual {}` — an empty body — now works. The backend resolves what the piece stands on by
walking the spine in order of authority:

1. the idea platform's expression for POSM
2. the platform's own line
3. the house's POSM message
4. the house's core message
5. whatever was typed — **last**, because it is the least considered

It comes back as `stands_on: { text, source }`. **Please render `source`.** Verified live, empty payload:

```
stands_on.source : "the idea platform"
note             : "Standing on the idea platform."
```

The prompt box should be an override with the resolved line pre-filled and its source shown above it —
not an empty required field. Asking twice is how the two copies end up disagreeing.

---

## 3. Social — grounded from the backend, but the post count is yours

Two halves.

**Mine, done.** Social's prompt is composed in your file and hardcodes Heritage, so it carried no plan,
no brief and no platform. But every client prompt passes through `/complete` → `prompts.system_for()`, so
that is where I attached the spine: the chosen core / emotional / functional messages, the sourced RTBs,
the house's per-medium message, the *must not do* list, the adopted idea platform with its mechanic and
its existing expressions, and the plan's channels, audiences, phasing and measures — as **binding
constraint**, above your instruction, with an explicit "where these disagree, this section wins".

Verified by sending your social prompt verbatim, unchanged, through `/complete`. It came back as three
posts, all expressions of the adopted platform, using the house's social message. **You do not need to
change the prompt for the grounding.** It is excluded for the brief surface on purpose — a brief is
upstream of the house, and binding it to the current campaign's platform would make every new brief a
restatement of the last one.

`COMPLETE_MAX_TOKENS` is now 8000, from 2000. At 2000 a multi-post JSON reply truncated, which is not a
short answer — it is an unparseable one, and it reaches the person as the feature silently doing nothing.

**Yours.** *"It's generating only one post."* The prompt asks for one post per selected platform, so one
platform selected gives one post. Two asks:

1. **A count.** Three per platform as the default, doing different jobs — the one that recruits, the one
   that proves, the one that belongs to an occasion. The `SOCIAL` block now instructs this, but your
   prompt's requested JSON shape governs how many come back.
2. **Show the grounding.** The posts now obey the platform and the plan invisibly. A line above the
   panel — *"Written against 'The 4AM Milk', for the channels in the plan"* — is the difference between
   a person trusting the output and re-typing the brief on top of it.

---

## 4. On-ground — the gate is correct, and it now says what it would stand on

*"For on-ground executions, do not generate ideas unless a prompt is written."* `POST /activation-idea`
with an empty box returns **400** and always has:

> "Write the idea first — this sharpens one, it does not supply one."

That is the right rule and I am not softening it. On-ground is the one execution where the idea is a
person standing in a street doing a thing, and a model that supplies it supplies something nobody in the
room believes in.

What is new: the 400 now also carries `stands_on: { text, source }` — the platform line the activation
*would* be built against. Please show it beside the empty box as context, not as a default. It gives
somebody something to write from without writing for them.

`/activation-idea` and `/activation-element` also both take the platform now and pass it into the prompt
as binding, so a sharpened idea is an expression of the platform rather than a good idea next to it.

---

## 5. Idea platform — three to begin with, and iterate vs fresh are now distinct

*"Idea platform needs to start with three different idea platforms to begin with and should be able to
iterate the existing one as well develop fresh ones."*

`POST /idea-draft` now returns **three**, and takes `build_on`:

```
POST /idea-draft { house, core?, brief?, n=3, build_on? }
  -> { options:[{ id, name, line, mechanic, kind, caveat, source,
                  built_from, built_from_name, stood_on }],
       count, build_on, building_on,
       …first option's fields also flat and under `idea` }
```

- **Fresh** — omit `build_on`. The three must differ in *kind*, not in wording, and the prompt names the
  routes: what the brand does for people · a category tension it resolves · a ritual or occasion it owns
  · a truth about how the product is made · an enemy it stands against. Three rephrasings of one idea are
  one platform, and the model is told to say so in `caveat` rather than pad.
- **Iterate** — pass `build_on: "<item id>"`, or the whole draft object inline for one you are holding
  but have not adopted. Each result carries `built_from` and `built_from_name`. A fresh platform is a
  wrong answer here and the prompt says so.

**The flat shape is preserved**, so your current code keeps working and simply shows the first of three
until you render the list. Verified live:

```
fresh, n=3
  [a truth about how the product is made]  The 4AM Milk
  [an enemy it stands against]             Nothing Older Than Today
  [what the brand does for people]         The 4AM Shift
build_on the first
  built_from='The 4AM Milk' :: The 4AM Name
  built_from='The 4AM Milk' :: Beat The Clock
```

Two asks: **three cards, not one field** — and a *Build on this* control on each card that is visibly
different from *Try again*, because re-rolling and developing are different motions and the report asked
for both. Please keep echoing `source` on adopt (still open from §4.2 last time) — an unedited drafted
line should not adopt as the author's.

---

## 6. One thing I fixed that was mine and quiet

Both image endpoints guarded on `FAL_KEY` alone and returned *"set FAL_KEY"*, so a deployment holding a
perfectly good Google key refused every image. Not the cause of the POSM report — this machine has both
keys — but it would have been the cause on any Google-only install. Now guards on either, and the message
names both.

---

## 7. How to check before sending

```bash
python tools/checkfe.py && python tools/contract.py && python tools/test_tools.py
```

17/17. And the honest note from last time still stands, now with a correction attached: I said if a check
passes and the screen is still broken, the check is what needs fixing. The logo bug proves it — no static
check could have caught a click bubbling into a parent's close handler. What was actually missing was
loading the page, and I have that now.

---

# Addendum — handover 6 merged, and two payloads that were lying

## The merge

Your handover-6 file was based on the copy you had, so it did not carry the logo fix from §1 — and mine
did not carry your Next control. **Dropping yours in whole would have reinstated the logo bug.** So I
took yours as the base and re-applied the four logo edits onto it. The diff was clean: 18 changed blocks,
zero overlap.

Verified in a live page after merging — the logo path still works (`panelStillOpen: true`,
`inputStillInDom: true`, status line `Choose an image…`), and your Next control works on a real
server-backed house, not just `demoStrategy`:

| on | Next reads |
|---|---|
| Core message | **Next: Emotional message →** — the double-unblock, right |
| Emotional reasons to believe | Next: Functional reasons to believe → |
| By medium (layer 8) | Start a plan from this house → |

Rail note read *"8 of 8 decided — all eight…"*. No console errors. Nothing for you to redo — **just
please base handover 7 on the file in this folder**, not on what you sent.

## Two payloads that reported finished work as empty

Found while verifying the above, and both were mine.

A house with **all eight layers decided** rendered as *"0 of 8 layers decided — Not started."* Every plan
rendered as *"0 of 7 layers written"* with *"No house bound — the proof gate cannot run"*.

Your code was right. `strategy.houses()` sent `decided`; you read `chosen_layers` then `progress`.
`plan.plans()` sent no count at all, and no `house_brand`. Both fell back to `0`.

This is the same drift as `status.layers[].layer` — but worse, because nothing crashed. A person opening
the Strategy screen was told their finished house was not started, and had no reason to disbelieve it.
I would not be surprised if this is behind *"it is not able to find the newly created brief"* from
earlier. Both listers now send the count under every name you read, plus `next_layer`, `blocking`,
`stale`, `total_layers`, `complete`, and `house_brand` on plans. Newest first.

Live, after: `8 of 8 layers decided · All eight decided.` and `6 of 7 layers written · Written against
Heritage`.

## The check that should have caught it

`tools/contract.py` was scoped to `status.layers[]`, so it structurally could not see this. It now also
types the house and plan **cards** — 13 checks — against the same synthetic documents it already builds.
Confirmed against the old payloads: it catches all eight missing fields.

One thing worth naming, because it is the failure mode I have complained about in reverse: my first
version read the listers off disk *after* the synthetic tenant was torn down, so it found nothing and
printed green having asserted zero things. It now types the cards while the documents still exist, and
reports **SKIPPED** by name if it ever has nothing to check. A check that quietly verifies nothing is
worse than no check, because you stop looking.
