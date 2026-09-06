# Handover 3 to Claude Code — briefs get a library, brands get a switcher

**File:** `app.dc.html` (drop over `api/frontend/app.dc.html`)
**This round:** your four asks, plus a Start-the-platform card on the Idea platform tab.
**Not touched:** the video pipeline, the compositor, social generation, campaigns, the shot list,
Sales enabler, the house and plan layer screens. Everything from handover 2 is where it was.

Supersedes these parts of the earlier `HANDOVER.md`: the idea platform section (it now has a start
step), and anything describing a seeded brief list — there is no seeded brief list any more.

---

## 1. `POST /brief-save` — saving is what makes a brief exist

Wired in three places, all of which send the same body:

| Where | When |
|---|---|
| Brief editor footer — **Save draft** (was a dead button) | on click |
| Brief editor — **Submit for approval** | after the status change, `fields.status: "Pending"` |
| Brief editor — **Approve brief** | after the status change, `fields.status: "Approved"` |
| IMC screen sticky footer — **Save to brief library** | on click, `format: "IMC"`, whole draft under `fields.draft` |

**The id is sent under both names.** `/brand-brief-draft` returns `brief_id`, `/brief-save` upserted on
`id` — so a body carrying only one of them turns a correction into a second near-copy. The UI now sends
`{id, brief_id}` with the same value and reads the response back from either key. You have since made
the route accept and echo both; the client no longer depends on which one you settled on.

Above the footer there is a line that names the state rather than staying silent:

- nothing saved yet → *"Not in the library yet — nothing else can pull this brief until it is saved."* (amber)
- has an id → *"This brief has an id already: saving corrects it rather than adding a second copy."*
- just saved → *"Saved 14:32 — redrafting corrects this entry rather than adding another."* (green)

A failure says `Could not save — nothing was written to the library.` and keeps the screen unchanged.

## 2. `GET /brief-list` — one library, five places pull from it

`BRIEF_LIBRARY` is **deleted**. There is no fallback list of plausible briefs: a brief in a picker that
is not on the server is how work gets written against a brief nobody wrote. The picker therefore has
three distinguishable empties —

- **loading** — *Reading the brief library…*
- **unreachable** — a red-edged band saying the library could not be reached and that the list stays
  empty on purpose, with *↻ Re-read*
- **none saved** — *No briefs saved yet. Write one under Briefs and save it…*

and a count line (*"4 saved in the library"*) above the rows. Each row shows format tag, title, a brand
pill, `status · brand · updated`, and the proposition in italics.

**Pickers, and what each does with the pick:**

| Screen | Target | Effect |
|---|---|---|
| Social studio | `social` | sets `linkedBrief` and fills the campaign objective |
| Video → Film | `video` | sets `linkedBrief` |
| Strategy → Messaging house → *Start a house* | `house` | fills brand, and writes the brief's own words into the brief textarea (visible and editable — it is what the core message inherits) |
| IMC plan → *Start a plan* | `plan` | fills brand, holds the text, chip names the source |
| Strategy → Idea platform → *Start the platform* | `idea` | holds it as the brief the platform answers |

`/plan-new` is called with `brief` added when one was pulled, and **retried without it on 400/422** —
losing the plan over an unknown field would be worse than starting without the brief. If you want the
field, keep it optional; if you do not, nothing needs to change here.

The library is re-read after every save, and cleared and re-read when the active brand changes.

## 3. Briefs panel in Memory — on Ground truth, from the learning log

`Memory → Ground truth`, above *Add to the library*, because briefs are the other half of ground truth:
not uploaded artwork, but the words every generator is written against. `/learning` is now fetched on
entering that screen as well as the learning log.

- **Brand chips** from `learning.brands` — name, brief count (amber when zero), and *working on this*
  on the row whose `active` is true. That flag arriving on the row is what makes the marker possible;
  a join the client has to do itself is a join it gets wrong, so thank you for moving it.
- **Brief rows** from `learning.briefs` — tag, title, brand pill, `status · brand · updated`, the
  proposition (amber when missing: *"No proposition recorded — the producers will have nothing to
  carry"*), and a *Use in Social →* action that carries it straight into the producer.
- **`no_profile: true`** renders as an amber line on the row: *"No brand profile behind this brand —
  work generated from it is ungrounded."* This is the Parle G case, visible.
- Empty state explains the consequence: an unsaved brief exists only on the screen it was written on.

## 4. `GET /brands` + `POST /brand-active` — the brand switcher

Two places, one control.

**In the header**, left of the approvals count: a chip with the brand's initial, name and category. It
is the most consequential setting in the studio, so it is readable at a glance rather than buried.
Clicking it opens a panel of every profile with category (amber when missing — *"outputs will be
category-generic"*), market, and the master idea or positioning in quotes. The active one carries an
`active` pill; the others say *Switch*.

**`voice` is exposed.** Each row has a quiet *what the model is told about this brand* toggle that
prints the voice block verbatim in a mono panel. A tool that grounds itself invisibly is asking to be
trusted rather than checked, and this is the screen where seeing it matters.

Switching POSTs `{id}`, takes `brands[]` back from the response when you return one (otherwise it flips
the flag locally), then clears and re-reads the brief library. A failure says so and names the brand
still active.

**In Studio settings**, the same list appears as the *first* section — above brand name, logo and
accent. Those change how the work looks; this changes what it says.

With no profiles: one line, *"No brand profiles on the server yet"*, and one consequence, *"Every
output is written from the prompt alone until a profile is active — which reads competent and could be
any brand in the category."*

## 5. New: *Start the platform* on the Idea platform tab

A card above STEP 1 with the platform's only two legitimate sources side by side:

- **The messaging house** — a select of `/houses`; picking one fetches `/house/{id}`, holds it as the
  open house, and prints its chosen core message underneath. Three honest states: no house chosen /
  no core message chosen in that house yet / opening.
- **The brief** — the same `/brief-list` picker, showing title and proposition, clearable.

Then **Draft the platform** → `POST /idea-draft` (see CONTRACTS.md), and *Write it myself*, which
scrolls to STEP 1 and focuses the name field.

**Nothing is composed on the client.** With no `/idea-draft` the toast says *"No drafting route on the
server — the sources are held and the two fields are yours to write."* A platform assembled from two
strings would read like an idea and be nobody's.

STEP 1's *standing on* line now names the brief too, and warns when a platform answers a brief with no
core message behind it.

---

## What I need from you

1. **`POST /idea-draft`** — the only new ask. Contract in CONTRACTS.md. Optional: the card works
   without it, honestly.
2. **The six items from DESIGN_NEXT §12** — `brandprofile.py` fields, `voice_block()` ordering,
   `status.readiness`, the proof gate reading `claims[]`, `sales.CHANNELS` falling back to
   `profile.channels[]`, and the filled seeds. Then I build the Studio Settings profile form: grouped
   panels A–F, `claims[]` and `channels[]` as repeatable rows, and the readiness strip. The brand
   switcher is built so that screen hangs off it.
3. **`POST /idea-platform`** — still outstanding from handover 1. The five tests are re-answered every
   session without it, and `skipped` is a decision, not a UI preference.
4. Everything else on the earlier list (`/execution-options`, the seven shot endpoints, the Sales
   enabler contract) is unchanged.

## Decisions that are yours to overrule

- **No seeded brief list, anywhere.** An unreachable library shows nothing and says why. If you would
  rather ship demo briefs, seed them server-side and they will appear like any other row.
- **The brief's text goes into the house's brief field**, not behind an id. The core message is drafted
  from what is on screen, so it has to stay readable and editable.
- **`/plan-new` gets `brief` optimistically and retries without it.** Say the word and I will send it
  unconditionally, or drop it.
- **A platform is never auto-composed.** Sources are held; the sentence is a person's.
- **The briefs panel lives on Ground truth, not the learning log.** It is what you gave the studio, not
  what the studio worked out.

## Notes on the build

- Header layout is now shrink-safe: the nav absorbs shrink and scrolls (scrollbar chrome hidden), the
  brand chip is capped at 180px and sheds its category line under 1320px, the approvals count hides
  under 1120px, and the gear and avatar are `flex:none` so a control is never the thing that gets
  squeezed off the edge.
- Brief rows are normalised in one place (`normalizeBriefRow`) and tolerate `id`/`brief_id`,
  `fields`/`brief`, `updated`/`created`/`at`, and `proposition`/`smp`/`bigIdea`. Add keys freely.
- Both new bags are separate methods spread into `renderVals` — `bagBriefs(s, imcBrief)` and
  `bagBrands(s)`. Keep that split if you add to them.
- `/brands` is read once on mount; `/brief-list` on mount, on entering Briefs, Strategy and Plans, on
  opening any picker, after every save, and after a brand switch.
- The idea platform is **still a top-level `sc-if isIdeaScreen` block**. Do not nest it — that is what
  blanked it once already.
