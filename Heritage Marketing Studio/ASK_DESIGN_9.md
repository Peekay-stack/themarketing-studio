# Handover 8 reviewed — context, one fix, and five questions

You lost the chat history, so this is written to stand on its own. No prior reading needed.

**The file in this folder is your new base.** It is your handover 8 with one bug fixed (§2). Please build
handover 9 on it, not on the copy you sent.

---

## 1 · Where the project is, in one screen

**The Marketing Studio** — FastAPI backend + this single-file React app (`app.dc.html`), being productised
for sale to **B2C companies**, pitched as *"now do marketing the FMCG way, rooted to your category."*
Multi-tenant: any company, several brands inside it, each with a category. India-first.

The spine is a **fork, not a chain**:

```
Brief ─► Messaging house ─┬─► Communication plan ─┐
                          └─► Idea platform ──────┴─► Executions ─► Sales enabler
```

Executions are five producers: **social · POS material · on-ground · media · film** (film carrying live
action and the compositor).

Two rules that explain most decisions in the codebase:

- **Nothing downstream invents what upstream decided.** A producer never asks for a proposition the house
  or the platform already holds. That is what `GET /grounding` and the three-input panel are for.
- **Provenance is visible.** Every line is marked as the model's or the author's, and editing a model line
  re-sources it to the author. A drafted line nobody rewrote stays visibly the model's.

I run the backend and can drive a real browser, so I verify your work against a live server. You cannot,
which is why the "not verified" list in your handovers is the right thing to keep writing.

---

## 2 · One bug in handover 8, already fixed. Please keep the fix.

**`recompose` was declared twice.**

```js
7243:  recompose = (i) => async () => {   // your new live-action one, per shot row
9623:  recompose = async () => {          // the older execution one, /execution-recompose
```

The later declaration silently wins. So `recompose: this.recompose(i)` in the shot-row bag was not
building a handler — it was **invoking** the execution recompose during render. With an execution open,
rendering the shots table would have fired `POST /execution-recompose` once per row, per render.

Renamed the live-action one to **`recomposeShot`**, and its single use at line 8178. `checkfe` now passes:
`sc-if 304/304`, `sc-for 152/152`, `div 1360/1360`, **480 members, 0 duplicates**.

Your own duplicate-member check would have caught this — worth running it before every send, since it is
the one failure class that is invisible in review and fatal at runtime.

---

## 3 · What I verified, so you know what is proven

Everything below ran against a live server and a real browser.

| | |
|---|---|
| `GET /grounding` consumed correctly | `loadGrounding()` keys on house+plan+execution, caches on the key, and the resolver's summary wins with your local composition as the fallback. Exactly the ask. |
| The three-input standard | Now on the four producers, on Film, and on live action — same shape, same order. This is what was asked for and it was right to generalise it. |
| All 51 routes you call exist | No missing endpoints. |
| Brand profile form correctly **not** built | You were asked to wait for real field names. You waited. Right call — §5.1. |

**Not built, still open:** the four `house-docx` / `plan-docx` download buttons. Zero references in the
file. Lowest priority of the three, but it is the last one that is purely yours.

---

## 4 · The live-action screen: your model is better than my backend, so I am rebuilding to match

This is the main finding and it is **my work, not yours**. Every route you call exists, but six of them
expect a different shape, because you built a better model than `shots.py` implements.

- **You built:** plan the shots → attach real uploaded footage → pull a still from that footage → sign it
  off with a name → the compositor consumes signed takes only.
- **Mine assumed:** plan the shots → point a shot at a scene *number* → generate a still from a text
  description of the look → sign off.

Yours is right. It is what a shoot actually is, and the approval gate is the point. I am rebuilding
`shots.py` around it.

### The contract I will build, derived from your code

Confirm or correct this — I would rather match you than have you match me.

**The shot row**, every field your table reads:

```
id · no · slug · action · talent · location · length
take      the attached footage (url or filename)
filename  what the human called it
still     a frame pulled from the take
signed    null, or { who, at }
```

State is **derived, never stored**: `signed` → signed, else `take` → shot, else planned. I will not send a
`state` field; deriving it your way is correct and I will keep the backend from disagreeing with you.

**The calls:**

```
GET  /shots?execution=<id>          -> { shots: [row], summary }
POST /composite-upload  multipart   { file, shot }        -> { url }
POST /shot-attach                   { id, url, filename } -> { shot }
POST /shot-still                    { id }                -> { shot }   (still pulled FROM the take)
POST /shot-sign                     { id, who }           -> { shot }   (signed = { who, at })
POST /shot-sign                     { id, clear:true }     -> { shot }   (signed = null)
POST /shot-recompose                { id, note }          -> { shot }   (signature cleared — correct)
POST /shot-remove                   { id }                -> { ok, summary }
POST /shots-callsheet               { shots, idea }        -> .docx
```

Two of these are currently actively wrong on my side and would lose work, so they are first in the queue:

- `/shot-attach` reads `{id, scene}` and **drops your `url` and `filename` entirely** — the uploaded take
  is thrown away and the shot is attached to scene 0.
- `/shot-sign` reads `{id, who, on}` with `on` defaulting to **true**, so `{clear:true}` **re-signs**
  instead of withdrawing the signature.

Your handling of a recompose invalidating the signature is right and I will enforce it server-side too, so
it holds even if a signature is written by something other than this screen.

---

## 5 · The five things I need from you

Short answers are fine. Only Q1 blocks me.

**Q1 — `/shots-callsheet`: `idea` is a string or an object?**
You send `idea: this.idea().line || ''`, a **string**. My docx builder expects a dict and will either
crash or print wrongly. I would rather take `{ name, line }` so the call sheet can print the platform's
name above its line. Say which and I will build that.

**Q2 — Should `/shots` scope to the execution, or is the shot list global?**
You send `?execution=<id>`; my handler ignores it and returns every shot. Scoping is the obvious answer,
but it changes behaviour for anyone with shots already saved, so I want it confirmed rather than assumed.

**Q3 — What should `note` on `/shot-recompose` actually do?**
You send `{ id, note }`. I can (a) store it as a reason on the shot's history, (b) feed it to the
compositor as a direction for the rebuild, or (c) both. (b) is the useful one but it is also the one that
spends a render, so your intent matters.

**Q4 — Who is `who` on a signature?**
You send `this.props.managerName || 'unattributed'`. Is `managerName` coming from studio settings? If so I
will make `/shot-sign` fall back to the stored `manager_name` server-side, so a signature is never
`'unattributed'` just because the prop was not threaded.

**Q5 — Does the compositor need anything beyond signed takes?**
Your comment says */shots already answers the compositor with the signed takes only*. Confirm that is the
whole handoff, or tell me what else it needs and I will add it to the same response rather than a second
route.

---

## 6 · What I am building next, so you can plan around it

1. **`shots.py` rebuilt** to §4's contract, plus the two work-losing fixes.
2. **`brandprofile.py` fields + `status.readiness`** — then you can build the Studio Settings brand form
   without guessing. **I will send you the exact field names and shapes before you start it.** Do not
   begin it until then; that is why you were right to wait.
3. The plan reading the messaging house, not just the brief, and the quality of the two `.docx` documents.
   Both backend, no UI change.

The only thing on your side is the four docx buttons, and answers to §5.

---

## 7 · Checks, before every send

```bash
python tools/checkfe.py       # syntax, pairing, DUPLICATE MEMBERS, bag spread
python tools/contract.py      # backend shapes vs what you iterate
python tools/test_tools.py    # 17 tests, includes both
```

If you cannot run them, the properties they measure are: `sc-if`/`sc-for`/`div`/`span` balance, **class
members declared exactly once**, every `{{ hole }}` resolving against the class, and zero `<img>` tags in
the template. The duplicate-member check is the one that mattered this round.

Two rounds running, your frontend was right and my payload was lying to it. If a call fails, send me the
request and the response rather than working around it — the odds are it is mine.
