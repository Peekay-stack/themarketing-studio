# Round 14 — everything I intend to change, in one document

Supersedes the earlier draft. Covers your nine, the two you added, and **seven more I found by reading
the three documents you attached** — which I had not read when I wrote the first version. Some of those
are worse than anything on your list.

**Confirmed by you:** #8 go ahead · #7.2 composited type · project names · on-ground venue thinking.

Nothing is started.

---

# Part 1 · What I found in your documents

You asked whether I had checked them. I had not. I have now, and these were not on your list.

### 1.1 · The plan generated its phases twice and kept both  ·  **worst of these**

`Heritage_comm_plan_worksheet (2).docx`, phasing table — five rows:

```
1 · Make the dawn story known          Weeks 1–8
2 · Turn recognition into the daily…   Weeks 6–16
3 · Hold the habit…                    Weeks 14 onward
1 — Recognition                        —
2 — Doorstep switch                    —
```

Two complete sets of phases, one appended to the other. Regenerating a layer is **adding** rows instead
of replacing them. The second set has no windows, so it is the older, thinner attempt sitting underneath
the better one — and both go into the document as though they were one plan.

This is mine and it is first in the queue. It also means any layer you regenerated is probably carrying
duplicates you have not spotted.

### 1.2 · Every objective row has no date, and the business row no measure

```
business        …volume by…            no measure set    no date set
marketing       Move 20% of the 25–44… repeat purchase…  no date set
communication   Make 'milked at dawn'… prompted assoc…   no date set
```

`by_when` is empty on all three. The layer asks for "a number and a date" and the generator supplies
neither reliably. It is told not to invent dates — correct — but then it should **say what it needs**
rather than leave a blank that reads as an oversight.

### 1.3 · The audience pillar column contains prose

```
Pillar:  functional — 'Heritage moves every single day, and now every pack…'
```

That column takes one word — `emotional` or `functional`. A sentence in it is what produced your blocking
finding *"assigned 6 pillars"*. The generator is not being constrained to the allowed values.

### 1.4 · Every channel is unowned

All seven rows: `owner unknown`, `share unknown`. Hence seven `[Open]` findings about owners. The
generator is right not to invent an owner — but seven identical findings is noise, and the plan reads as
unfinished when the truth is "nobody has been assigned yet, which is a task, not a defect".

### 1.5 · The IMC brief's comparison matrix is nonsense

`Heritage_IMC_Brief (3).docx`, table 2:

| Dimension | Heritage | Nandini |
|---|---|---|
| Tagline / line | "Farm-Fresh Family Vitality" | State cooperative pride; |
| Target buyer | **Focal audience** | **Nandini milk, curd, ghee** |
| Key differentiator | Purity-led strength | State cooperative pride; |
| Recent moves | **—** | Aggressive pricing… |

Three things wrong at once: *Target buyer* is filled with the competitor's **hero brands**, *Tagline* and
*Key differentiator* get the **same** value, and Heritage's own column carries placeholders — `Focal
audience`, `—`. The matrix is built by mapping the wrong fields across.

### 1.6 · "Sources:" is an empty heading

Printed on page 1 with nothing under it.

### 1.7 · Section 7 is boilerplate that looks like content

> Pricing landscape per uploaded market data; validate against the latest reads.
> Distribution strengths and gaps per the supplied data and category context.
> Whitespace the focal brand can claim around the strategic bridge.

These say nothing. If no market data was uploaded, the section should say **"No market data was
uploaded, so this section is empty"** — a sentence shaped like content, containing none, is worse than a
blank.

### 1.8 · The plan document calls itself a house

The caveat block in the **plan** reads *"This house lives here, not in the Word file."* Wrong noun, my
copy, one-line fix.

---

# Part 2 · Your eleven

## #4 + #3 · The plan accuses you of things you have fixed  ·  *mine + Design*

Established by test: typing a measure **does** save, the backend **does** drop from 2 blocking to 1, and
the screen never hears about it. `editPlanCell` fires `/plan-row` and discards the response.

1. **`editPlanCell` awaits and applies the response.** The finding clears as you type. *(Design)*
2. **Debounced 400ms.** It currently POSTs once per keystroke. *(Design)*
3. **A `saved` marker on the row.** *(Design)*
4. **The banner stops double-counting** — `1 blocking · 1 overridden`, with who accepted it. *(mine)*
5. **A moot override is retired** — fix a finding you had overridden and the override is dropped with one
   line saying so. *(mine)*
6. **↯ No Save button.** A save button on an auto-saving form is a lie. Instead: the marker above, plus
   **the same "Next: <layer> →" control the house has**, appearing once a layer has a row. Try it; if you
   still want an explicit Confirm I will add one. *(Design)*

## #6 · Social ignores the brief  ·  *mine + Design*

You set the audience to rival-brand user and got loose-milk copy.

1. **Trace where the audience is lost** and fix it. I will not promise a mechanism before I have found it.
2. **The prompt box becomes a steer, not a gate.** *(Design)*
3. **A line above the posts naming what it wrote against** — audience, platform, channels. You would have
   caught this in one glance. *(Design)*

## #7 · POS material  ·  *mine*

1. **Three routes, not one.**
2. **The tagline goes on the piece, composited server-side.** The model renders the picture with space
   held open; I draw the line with a real font at the layout's position. Correct letterforms in any
   script, and the line stays editable because it is data.
3. **Craft rules grounded in practice, not my taste.** I will research POSM and dealer-board standards —
   contrast ratios, minimum type height against viewing distance, how much of the frame the pack occupies,
   what survives a 40kmph glance versus a 40cm shelf read — and encode them per format. A dangler and a
   gondola header are not the same picture and should not get the same brief.
4. **Preview at the true ratio, with the line on it.**

## #8 + #11 · On-ground ideas  ·  *mine*  ·  **confirmed, reversing the earlier gate**

You told me before not to generate ideas without a written prompt. You have now reversed that; I will
follow the new instruction.

1. **Two or three ideas, generated from the platform**, each structured:
   ```
   WHAT   ·  WHO  ·  WHERE  ·  WHEN  ·  HOW
   ```
   Five fields, because "engages with the brand" cannot be written into them.
2. **↯ Venue-led thinking, which is your addition and changes the shape.** An idea is not portable across
   venues — a boil-and-check demo that works in a society courtyard is illegal in a mall atrium and
   pointless in an office lobby. So each idea is generated **for a named venue type**, and the set spans
   more than one:
   ```
   kirana / general trade · modern trade aisle · mall atrium · office complex
   apartment society (RWA) · transit hub · college · residential doorstep
   ```
   Each carries what that venue permits, who controls access, and what it costs you to be there — because
   a mall atrium needs a licence and a kirana needs a shopkeeper's goodwill, and an idea that ignores
   that is not implementable.
3. **The typed box becomes a steer.**
4. **You pick one**, and it briefs the elements below.

## #9 · On-ground elements  ·  *mine + Design*

1. **Elements follow the chosen idea and its venue.** A mall atrium needs no van; a rural route needs no
   gondola. The backend returns the relevant set with a reason each:
   ```
   stall · van · truck · promoter uniform · promoter script · demo prop · leave-behind · permissions
   ```
   **Truck is new** (you asked) and **permissions is new** (the venue thinking demands it).
2. **Develop takes the chosen idea.** No more "brief it first".
3. **Each element gets a picture, not only a brief.**

## #1 · Lifestyle & culture  ·  *mine + Design*

**Cause found:** the dropdown you were using belongs to *Write your own* — it tags the line **you** write
and was never wired to generation. And generation is told to give a spread but never told **which kinds
are already covered**, so it repeats. `medium` does not have this problem because its gaps are computed
and fed back.

1. **Generation becomes gap-aware** — press *Offer options* twice and you fill the gaps. *(mine)*
2. **Options group by kind**, as `medium` groups by medium. *(Design)*
3. **The dropdown gets a label — "tag your line"** — so it stops reading as a filter. *(Design)*

## #2 · Idea platform exits and download  ·  *mine + Design*

1. **A next-step block after the tests.** Some of this exists in STEP 3; I will check whether those links
   work before asking for it twice. *(Design)*
2. **A platform .docx**, both modes — the idea, its mechanic, the five tests with verdicts and reasons,
   and the expression per producer. *(mine + one Design button)*

## #5 · Switching tabs loses everything  ·  *needs tracing*

Not planned yet. Almost certainly the same family as #4 — a response not applied, or the document not
reloaded on return — but the fix depends on which. **I want to reproduce it before proposing anything.**

## #10 · Project names  ·  *mine + Design*  ·  **new**

Two houses both called "Heritage" and no way to tell them apart.

1. **Every document gets a `project` name** — brief, house, plan, platform, shoot. Asked for once, when
   the first one is created, and inherited by everything downstream from it.
2. **The card shows it**: `Heritage · Diwali same-day push` rather than `Heritage`.
3. **Existing documents get one derived** from their brief title or creation date, marked as derived so
   you can correct it rather than being silently named.
4. **The .docx filename uses it** — `Heritage_Diwali-same-day-push_messaging-house.docx`, so a folder of
   downloads is legible.

---

# Part 3 · Order of work

| | | why |
|---|---|---|
| 1 | **1.1** duplicate rows on regenerate | it is corrupting documents now |
| 2 | **#4 + #3** the plan lying to you | it accuses you of things you fixed |
| 3 | **#6** social's lost audience | confidently wrong copy |
| 4 | **1.2–1.4** objectives, pillars, owners | quality of every plan |
| 5 | **#7** POS material, with the research | biggest single lift |
| 6 | **#8 + #11 + #9** on-ground, venue-led | the largest rework |
| 7 | **#10** project names | touches everything, so after the churn |
| 8 | **1.5–1.8** the IMC brief matrix + boilerplate | contained |
| 9 | **#1, #2, #5** | smallest |

---

# Part 4 · What I need from you

1. **Part 1 is new** — tell me if any of those seven is not worth fixing, or if I have misread one.
2. **#11 venue list** — is that the right set? Anything missing for Indian FMCG: *haat*, *mandi*, temple
   festival, wet market?
3. **#10** — should the project name be asked at the **brief** (earliest point) or at the **house**? I
   would say the brief, since everything descends from it.
4. **Order** — anything you want moved up.

Say go and I will start at the top. I will tell you before each backend change so you can restart when it
suits you.
