# ASK_DESIGN_19 — drafting the ladder, drafting the campaign, and merging Steps 3+4

Round 18 is merged and installed. **18/18 `test_tools`, 7/7 `checkfe`, `contract` clean, 171 endpoints,
no duplicates.**

Two notes on round 18 before the new work.

**Please build from the `app.dc.html` in this handover.** Round 18 was built on your own round-17 return
rather than the file we shipped, so all six fixes made *in* that return were missing again and I merged
them back by hand. The base here has both rounds in it.

**Your JS port of `checkfe` is faithful — it just omits the seventh check.** Your numbers matched mine
exactly (`sc-if` 347/347, `sc-for` 177/177, `div` 1502/1502, 526 members, 0 duplicates). The one it
doesn't cover, *template handlers reach the bag*, is the one that failed: `onIdeaExpression` was defined
on the class and named in the markup but absent from the render bag, so the five expression textareas were
dead controls. Worth porting — it's the failure class a diff cannot show.

Also fixed on your round-18 file: `loadCampaign` read `(d.campaign || d)` and bailed on `!got.name`, but
`GET /campaign` returns the layer *status* — no `name`, no `campaign` key unless an id is asked for — so it
returned every time. An existing campaign never hydrated and the roles table came up empty instead of
prefilled. And `hint-placeholder-count="5"` on the tests loop is now 2.

---

## 1 · Merge Step 3 and Step 4 into one

Your observation, and it's right. **Four of the five "Expression routes" are the same field as
"Expression by medium" under a different name.**

| Step 3 route | is stored as | Step 4 expression |
|---|---|---|
| Social | `social` | Social |
| POS material | `posm` | POS material |
| Onground activation | `activation` | On-ground activation |
| Trade | `incentive` | Sales incentive |
| Media planning | `media` | *(had no slot)* |
| *(had no route)* | `video` | Video |

`ROUTE_TO_KIND` was doing the translating, and `adopt()` carried a block of precedence code to stop one
store blanking the other — which is exactly where a real defect lived: an empty route wiped an expression
somebody had written.

**Backend is done and both shapes work simultaneously, so you can merge whenever it suits.**

- `EXPRESSIONS` now has **six** keys: `video, social, posm, activation, incentive, media`.
- `GET /idea-platform` returns `expressions` with all six, and legacy `routes` text is **folded in** on
  read — into empty slots only, so nothing anyone wrote disappears. `routes` is left on the record
  untouched; no file is silently rewritten.
- `expression_jobs` comes back beside it — `{key: the one-line job}` — so the labels come from the backend
  instead of a local array.
- `ROUTE_TO_KIND` is marked deprecated. Nothing new should write `routes`.

**What the merged step should be:** one section, six rows. Each row carries the medium name, its job line
from `expression_jobs`, the textarea, **Rewrite this one**, and the **Take it to the producer →** hand-off
that Step 3 had. Keep *Write these for me* at the top — it now writes six.

Delete Step 3. The `routes` state and the `ROUTE_TO_KIND` mapping in the client can go with it.

---

## 2 · Ladder drafting — `POST /ladder-draft`

Your question was whether the bridge layer has to be filled by hand. No — but the generic layer generator
is the wrong instrument, and I measured it before building this. Asked for four bridges on the Heritage
house it returned four paragraphs of 25–35 words, each one containing *both* the fact and the feeling, and
**none** of them dividing. A bridge means nothing on its own; it is the step between two named things, so
the unit of generation has to be the whole triple.

```jsonc
POST /ladder-draft   { "id": "<house id>", "n": 4 }
→ { "paths": [ { "f": "<option id>", "f_text": "500 dairy professionals check the milk every day…",
                 "bridge": "Nothing degrades between the farm and her kitchen: temperature, timing, handling",
                 "divides": ["temperature","timing","handling"],
                 "words": 11, "long": false,
                 "e": "<option id>", "e_text": "Strong kids, strong mornings — and I made that start possible.",
                 "why": "one sentence on what this path lets the brand argue",
                 "already": false } ],
     "note": "4 path(s); 3 carry a proof axis. …" }
```

Nothing is written. **Accept one path at a time:**

```jsonc
POST /house-ladder  { "id": "<house id>", "f": "…", "e": "…", "bridge_text": "the bridge verbatim" }
```

That creates the bridge as an option in the house (source `model`), marks it chosen, and records the edge —
all in one call, because the rung does not exist yet and making the person do the second half by hand
defeats the point.

**Where it goes:** a *Draft some paths* button on the Bridges layer, above the three columns, rendering the
candidates as a confirm/reject list. The three-column manual builder stays exactly as you built it — this
sits above it, because nobody should have to draw a graph from an empty panel. That was my omission in
ASK_DESIGN_18, not yours.

**Two things to surface, and they matter:**

- **`long: true`** — the bridge runs over 12 words. Flag it and let them trim before recording; don't hide
  the path, the pairing may still be the right one.
- **`divides`** — show the divisions as chips, and put the note's warning next to them. Measured on this
  house, the generator will satisfy the colon rule with synonyms (*"no surprises, no doubts"*) or
  alliteration (*"cold, checked, controlled"*) that read like an axis and prove nothing new. **The only
  real test is whether each division needs different evidence, and that is a judgement a person has to
  make.** Please don't present the axis as settled.

---

## 3 · Campaign drafting — `POST /campaign-draft`

Your question was what the campaign's input is, and whether generation is possible at all. The input is
**the platform plus one ladder path**, and yes — everything a first draft needs was already decided one or
two layers up.

```jsonc
POST /campaign-draft  { "house": "…", "ladder": "<ladder id>",
                        "shift": { "shift_from": "…", "shift_to": "…", "shift_line": "…" } }   // optional
→ { "draft": { "insight": "…", "resolution": "…", "shape": "frame",
               "frame": "{X} ki jaanch, roz taaza, roz shakti",
               "slots": [ {"text":"Aankhon","lang":"hi"}, … ],
               "ladder": "…", "roles": { …8 prefilled… },
               "why": "…", "shape_why": "…", "source": "model" },
     "note": "Drafted off … Proof axis: … Nothing is saved yet." }
```

Nothing is saved — it fills the form and the person edits, then `POST /campaign` as before.

Where each field comes from, so the screen can say so:

| field | derived from |
|---|---|
| insight | the brief's Current→Desired shift, if passed — the **CA→DA gap is the tension** |
| resolution | the emotional truth at the top of the ladder path |
| shape | the house's culture codes: an `idiom` → `frame`, `iconography` → `device`, `ritual` → `act`. `shape_why` carries the sentence. |
| frame | the brand's own idiom with a slot cut into it |
| slots | one per division of the bridge's proof axis, with `lang` set |
| roles | the role-by-rung defaults |

**On the optional `shift`:** the house's `brief` only holds `background`, so the Current→Desired lives in
the brief builder's `cb_ca_db_da` and **nothing downstream currently reads it.** If you can reach it from
the linked brief, pass it — the insight is markedly better with it. Without it the draft still works and
the note says the insight is inferred and needs confirming. Worth a `[unverified]` marker on the field in
that case.

**Where it goes:** a *Draft this from the platform* button at the top of Step 5, disabled until a ladder
path is selected — the draft needs one and returns 400 with the sentence to show otherwise.

Also from your screenshot: the ladder dropdown shows *"No path named — a finding will say so"* as the only
option when no paths exist. Correct, but it reads like a choice — better disabled with *"Record a path in
the messaging house first."*

---

## What is NOT built

- **No cell editing on the campaign grid.** Still computed-only; it needs a storage decision first.
- **No `retired_tests` copy** anywhere. Still optional.
- **No auto-accept of drafted paths.** Every path is confirmed one at a time, deliberately.
- The frontend half of the merge — that's this ask.

## Questions back to me

1. For the merged step, do you want the six rows in a fixed order, or grouped (consumer media first,
   `incentive` and `media` last)? `expression_jobs` preserves insertion order if that helps.
2. Should *Draft some paths* replace the empty three-column state entirely when no paths exist yet, or
   always sit above the columns?
