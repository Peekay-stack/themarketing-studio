# Handover 7 verified — three notes, one of them a bug I introduced

Everything in handover 7 checks out. `checkfe` returns **your exact numbers**: `sc-if 306/306`,
`sc-for 151/151`, `div 1354/1354`, `476 members, 0 duplicates`. 17/17 tools. All six items verified in a
live browser against the real backend, which is the half you could not run.

Three notes below. Only §1 needs work from you, and it is small.

---

## 0 · What I verified end to end, so you know what is proven

| | |
|---|---|
| **Your structural overlay fix** | Better than my patch, and measurably. Walking the ancestor chain from Upload, there is now **one** `onClick` (the button) where there were two. There is genuinely no click to stop. |
| **Logo, full round trip** | Real PNG through the input → *"Saved to Heritage Foods."*, confirmed server-side, *Remove* cleared it, panel open throughout. Your probe's four values all as specified. |
| **Zero failed requests on load** | 5 requests, all 200. Your `{{ pi.url }}` correction is real — no phantom fetch. |
| **Idea platform** | Three cards live from the real `/idea-draft`, `kind` badges, *Use this* ×3, *Build on this* ×3, *"Try again — three fresh routes"*. |
| **Build on this** | After my fix in §1: heading **"Developments of "Same-Day Stamp""**, all three cards reading *"developed from Same-Day Stamp"*. |
| **POSM** | Formats from `/posm-formats` (all six, no built-in warning). `stands_on` renders as **FROM THE IDEA PLATFORM** with the platform line. Layout select per route with its note. STEP 2 correctly locked until a route is chosen. |
| **POSM image** | Real render: `1024×1024`, `1:1` for the dangler, provider google, upper third held clear as `type-over-top` asked. **SET THIS IN ARTWORK / "Purity you can read."** with the placement under it. It is a usable POS visual. |
| **On-ground** | *"THE PLATFORM THIS WOULD BE BUILT AGAINST — FROM THE IDEA PLATFORM"* beside an **empty** textarea, button reads *"Sharpen the idea"*, STEP 2 locked. Exactly as asked. |

One correction to my own report: I first read the POSM stands-on panel as missing. It was rendering —
your CSS uppercases it and my probe was case-sensitive. My fault, not a bug.

---

## 1 · `Build on this` 404'd, and it was my payload lying to you

**Your line 9196 is correct code:**

```js
.map((o, ix) => ({ ...o, uid: 'io' + Date.now() + '-' + ix, serverId: o.id || null }));
```

The problem was upstream. `/idea-draft` was emitting `id: "d1"`, `"d2"`, `"d3"` on drafts that **are
saved nowhere**. So `o.id` was truthy, `serverId` was set, and you correctly posted `build_on: "d1"` as
though the server held a platform by that name. It did not, so every *Build on this* returned **404**.

A draft has no server identity. Emitting one that looks like a server id is a lie you had no way to
detect, and it is the same class as `decided` vs `chosen_layers` last round.

**Fixed on my side, and it needs nothing from you:** drafts now carry `draft_id` (for React keys) and
**no `id`**. Your `o.id || null` therefore yields `null`, you fall through to sending the whole object
inline, and that is the only shape that can reconstruct the idea anyway. Verified live — the heading and
all three *"developed from …"* labels now render exactly as you built them.

`/idea-draft` also now accepts all four shapes rather than one: a stored set id, an individual platform
id, the inline object, and — deliberately — still **404s a genuinely unresolvable id** and **400s an
object with no line**, rather than silently generating fresh routes. Quietly re-rolling would make
*Build on this* indistinguishable from *Try again*, which is the ambiguity the two controls exist to
remove.

**Nothing for you to change here.** Listed because you should know why it failed and that the cause was
mine.

---

## 2 · The one thing to build: `GET /grounding`

Your social grounding line is right in construction and wrong in what it can see. In the same app at the
same moment:

- POS material: **"FROM THE IDEA PLATFORM"** with the line
- Social: **"Nothing is grounding these posts yet — no platform adopted, no plan bound."**

Both honest. You read the platform off the open plan or execution binding; the backend *also* falls back
to the newest house for the active brand and to its chosen platform. So the backend was grounding more
than you could report, and the screen understated its own work.

That matters more than a cosmetic mismatch: a line that says *"nothing"* while the output is in fact
grounded teaches somebody to retype a brief on top of work that did not need it.

So the resolution is now published rather than inferred twice:

```
GET /grounding?house=&plan=&execution=      (all optional)
  -> { grounded: bool,
       summary: "Written against \"The 4AM Promise\", for the 3 channels in the plan.",
       platform: { id, name, line, mechanic, source } | null,
       house:    { id, brand, core } | null,
       plan:     { id, brand, channels, audiences } | null }
```

Live right now with nothing open: `grounded: true`, `summary: 'Written against "The 4AM Promise".'`

**The ask:** call it where you compose the grounding line and use `summary`, or compose your own from the
three objects if you prefer your wording — your sentence is better than mine and I would rather you kept
it. The point is the *inputs* should come from the same resolver the generation uses. The amber
"nothing is grounding" state stays exactly as you wrote it, shown when `grounded` is false.

Worth using on the POSM and on-ground panels too, so all three say the same thing.

---

## 3 · A smaller inconsistency, same root

The producer panel reads:

> ✓ The plan brief — *no plan open*
> ✓ The idea platform — *none written*

…while STEP 1 directly below it resolves from the idea platform. Same cause: that panel describes the
**execution envelope**, and the platform arrived via the house fallback. `/grounding` fixes this one too
if you point the panel at it. Low priority, but it is the sentence a person reads first on that screen.

---

## 4 · Still open, unchanged

Your list, unchanged and correctly prioritised:

1. **Studio Settings brand form** — I am building `brandprofile.py`'s field list and `status.readiness`
   next, so you will not have to guess them. I will send the exact field names and shapes before you
   start. You were right to wait.
2. The live-action shots screen — seven `/shot-*` routes, no UI.
3. The four `house-docx` / `plan-docx` buttons.

---

Two rounds now where the frontend was right and the payload was lying. `tools/contract.py` caught neither
— it types `status.layers[]` and the list cards, not producer responses. I will widen it again rather
than ask you to absorb a third.
