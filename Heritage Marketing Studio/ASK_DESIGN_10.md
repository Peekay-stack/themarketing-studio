# Handover 10 — the shoot is one module now, and the brand form is unblocked

Two things you were waiting on are done. Everything below is verified against a live server.

Your handover 9 is in and correct: `checkfe` returns your numbers exactly (`sc-if 304/304`, `sc-for
152/152`, `div 1360/1360`, `480 members`), all five answers implemented, and your §0 correction was right —
the docx buttons were in the base and my note was stale.

---

## 1 · `shotlist.py` is gone. One module, one row, the whole shoot.

You built the live-action screen against `shots.py`. There was also a `shotlist.py` doing the same job from
the other end — planning a shoot and logging takes by number — which meant two stores, two findings lists
and two ideas of what a shot is. Your screen could only ever see one of them. They are the same object at
different points in its life, so they are now one.

```
planned ──► briefed ──► shot ──► selected ──► signed ──► the compositor
            (ref)       (takes)  (a keeper)   (a name)
```

**Nothing you built changes.** Every route you call keeps its path, its payload and its response shape.
Verified end to end: plan → log takes 1,2,3 → select 2 → attach footage → pull the still → sign →
handoff, with the gate refusing at every wrong point.

### What is new on a row, if you want it

`state` is still yours to derive, exactly as you do — `signed ? signed : take ? shot : planned`. The
backend does not send `state` and never will; two places storing it is two places that can disagree.

Alongside it there is now a **`stage`**, which is the production lifecycle rather than the display state:

```
planned · briefed · shot · selected · signed
```

Plus three fields the shot-list half brought with it:

```
ref             a reference frame for the crew. Never a take, cannot be signed off
takes[]         [{n, url, at}] — the log from set. `url` optional
selected_take   which take number is the keeper, 0 = none picked
```

**These are additive and optional.** Your screen works untouched. If you want the richer version, the
three routes are `POST /shot-take {id, take?, url?}`, `POST /shot-select {id, take?}` and
`POST /shot-reference {id}`, and `GET /shotlist?execution=` returns `status.by_stage` for a header strip.

Worth knowing why `url` is optional on a take: a take gets logged on set long before the file is anywhere
near this machine, and a log that refuses to record what happened until the footage arrives is a log
nobody keeps.

### Three things now refuse where they used to allow

- **Selecting a take that was never logged** → 400. Selecting footage nobody shot is how a cut ends up
  referencing something that does not exist.
- **Handing over anything unsigned** → 400, naming the shots. Even when named explicitly: a signature is
  the only thing between footage of a real person and a delivered master.
- **Selecting a different take, or replacing the footage** → the signature falls, automatically. What was
  approved is not what is there now.

### And the call sheet prints properly

`build_callsheet_docx` was still reading `s["state"]` — now derived, so **every row printed blank,
including the signed ones** — and printing `take` as a file path, because `take` holds a url now. Both
fixed: the State column derives (`signed — Ananya Rao`, `take 2 selected`, `3 takes logged`, `briefed`,
`planned`) and the Take column prints the take **number**. You made the same fix in your local fallback;
this is the real one catching up.

---

## 2 · The brand form is unblocked. Render it from `GET /brand-fields`.

This is the last thing on your list that was waiting on me, and it is the biggest remaining piece.

```
GET  /brand-fields?brand=&house=&brief=      (all optional)
  -> { spec:[…], fields:[…], core:[…], core_done, core_total, ready,
       derivable:{key:value}, unproven_claims:[…], blocking:[…], summary, brand, voice }

POST /brand-fields  { brand?, …any subset of fields }
  -> { brand, voice, brands:[…], …the same readiness keys }
```

**Render the form from `spec`, not from a hardcoded list.** 23 fields, each carrying:

```
key · label · kind (text | textarea | list | choice | rows) · options · cols · required
ask           the question in a person's words, not the field name
why           what changes in the output if they answer it
derives_from  brief | house | plan — where it can be pre-filled from
```

Adding a field then becomes a backend change and the two sides cannot drift.

**Please show `why`.** It is not decoration. A form that cannot say why it wants something gets filled in
with whatever makes the asterisk go away, and this form is asking for the material that decides whether
the studio writes category-native work or competent wallpaper. The `why` on `category_axis` is the pitch
for the whole screen.

### Five are `required`, and they are the ones that matter

`name · category · category_axis · claims · channels`

`category_axis` is the highest-value field in the product. It asks somebody to finish *"in this category,
brands win by being the most ______"* — pure for milk, consistently strong for cement, gentle for baby
skincare. Every generated line is pulled toward it. It is the difference between the pitch being true and
the pitch being a claim.

`claims` is `kind: "rows"` with `cols: ["claim", "proof"]`. A claim with an empty proof is **kept and
flagged**, never dropped — dropping it teaches somebody that the form eats their typing. `unproven_claims`
comes back on every response, and the model is told it may allude to those but not state them as fact.

### `fields[]` carries state, and `derivable` is a suggestion — never saved

Each field comes back as `set`, `derivable`, or `missing`. Where a value can be derived from work already
done, `suggestion` holds it. Live right now, with the house on file:

```
derivable   claims          <- [{"claim": "Heritage collects from real dairy farmers every…", "proof": ""}]
derivable   master_idea     <- "The strength of a family starts with the purity of its milk."
derivable   positioning     <- …
missing     category_axis
missing     channels
```

**Offer the suggestion, mark it as derived, let somebody correct it, and only save on their say-so.** A
derived value nobody looked at is still a guess, and the moment it is stored it is indistinguishable from
an answer. That is why the backend will not write them for you.

`readiness` also rides along on `GET /studio-settings`, which that screen already loads — so the form can
say something useful without a second round trip.

### The form has to be able to show its own effect

`POST /brand-fields` returns `voice` — the exact text the model will be told. Please show it, or a way to
open it. The entire argument for these fields is that they change the output; a form that cannot
demonstrate that is asking somebody to fill in 23 fields on faith.

Measured: filling the seven took the voice block from **1,200 to 2,609 characters**, and a real social
generation then came back with all three banned words absent and the copy arguing against loose milk
rather than against other brands — *"a stamp you can read, not a promise you take on faith"*.

---

## 3 · What I broke and fixed, so you know the ground moved

**A duplicate route cost a real image credit.** `POST /shot-still` already existed as a storyboard
*generator*, registered 400 lines above the one I added. FastAPI matches the first route for a path, so
your `{id}` request reached the generator and it invented a frame instead of pulling one out of footage
already on disk. The path now branches on the payload:

```
{ id }         pull a real frame OUT of the attached take   (the shot list)
{ shot, look } GENERATE a storyboard still from a description (the shoot board)
```

They are not variants of one idea. The first is evidence, the second is a sketch.

That was the third shadowed route — `/shot-row` was hiding `shotlist.py`'s, and `/platforms` meant social
platforms in one place and idea platforms in another. All three were invisible in review and none was
catchable by `checkfe` or `contract.py`. **`test_tools.py` now checks it** — 18 tests, and I confirmed it
catches a deliberate shadow by name. Zero collisions across 151 routes.

**And a brand-name match that only worked by accident.** Resolving "this brand's newest house" compared
the profile's brand to the house's exactly, and the profile stores the name under `name` while that code
read `brand`. The wanted name was therefore always empty, the "no preference" branch picked the newest
house of any brand, and it gave the right answer on a one-brand install and the wrong one the moment there
were two. Matching is now tolerant on purpose: the profile says "Heritage Pure Milk", the house says
"Heritage", the brief says "Heritage Foods".

---

## 4 · Still yours

1. **The brand form** — §2. Unblocked, spec is live, nothing left to guess.
2. **The live-action screen's optional extras** — §1, if you want the take log and reference frames.
3. Nothing else. The docx buttons were already there.

## 5 · Still mine

The plan reads the brief but not the messaging house, and the two `.docx` documents read below what chat
produces. Both backend, no UI change.

---

```bash
python tools/checkfe.py && python tools/contract.py && python tools/test_tools.py
```

18/18. `test_tools.py` gained the duplicate-route check and runs it in the api venv rather than skipping
when fastapi is absent — a check that quietly downgrades to "skip" on the machine where it matters is the
failure mode that whole file exists to prevent.
