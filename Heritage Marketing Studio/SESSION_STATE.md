# Where the work stands — handover for a fresh chat

Written 2026-08-19. Supersedes the 2026-08-17 version. Everything below is verified against a running
server or a test run unless it says otherwise.

---

## The project

**The Marketing Studio** — FastAPI backend (`api/`, **171 endpoints**) plus a single-file React frontend
(`api/frontend/app.dc.html`, ~960KB). Productised for sale to **B2C companies** — explicitly not B2B.
Pitch: *now do marketing the FMCG way, rooted to your category.* Multi-tenant, India-first.

**The spine, as of this session:**

```
Brief
  -> Messaging house    WHAT IS TRUE + HOW TRUTHS CONNECT (the ladder)   <- 9 layers now
    -> Idea platform    WHAT WE MAKE, durably (the mechanic)
      -> Campaign       WHAT WE SAY NOW (a path + a shape + a proof axis) <- NEW, child of platform
        -> Executions   WHAT EACH MEDIUM DOES (roles, not translations)
          -> Sales enabler
```

**Two agents work on this.** Claude Design owns `app.dc.html`; this side owns the backend and verifies
Design's work. The user carries handover documents between the two.

### Standing constraints — do not relax

- **Don't spend fal credits on our own testing.** FAL is strictly for VO. Images to Imagen/Gemini,
  video to Veo, music to Lyria.
- **OPUS is the only install to edit** (`C:\Users\punie\Heritage-Marketing-Studio-OPUS\`).
- **Never print secret values** — key names, lengths, first ~5 chars only.
- **Merge Design's handovers, never drop them in.** See "The Design base problem" below.
- **Load the page before saying a screen works.** Browser pane works; endpoint tests alone have
  produced wrong verdicts three times.
- **Snapshot `api/tenants/` before the FIRST test of a session.** A synthetic dict passed to
  `ideas.save()` / `campaign.save()` writes a real file — it created `platforms/t.json` this session.

### Running the server

```
cd api && .venv/Scripts/python.exe -m uvicorn main:app --port 8000
```

Frontend is served at **`/`**, not `/app.dc.html`. The server loads `api/.env` itself
(`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `FAL_KEY`). The user usually has 8000 occupied — use 8001/8002.

---

## What this session built

### 1 · The POSM skill — and, as of 2026-08-19 (later session), the backend behind it

`api/posm_skill/` — SKILL.md + 5 reference files + 15 exhibit images. Junctioned to
`.claude/skills/posm` so `/posm` is invocable. **`api/posm.py` now loads it** (`_skill_instructions()`,
the way `brief_ai.py` loads the brief skill) — see "The POSM backend" below.

The governing insight, arrived at after two wrong turns:

> **POSM is a flat-colour graphic layout with cut-out photographic elements placed on it — a nine-layer
> stack. It is NOT a photograph with words on top.**

9 of the 13 reference exhibits are built this way. Files:

- `SKILL.md` — the layer stack, the pack refusal, words-never-generated
- `references/key-visual.md` — 6 hero types, field-division and type-device vocabulary, the
  isolated-cut-out prompt, the crop gate
- `references/formats.md` — 30 formats with real mm, ratios, reading distances, substrates
- `references/adaptation.md` — re-flow layers (not crop a bitmap), the drop-out ladder
- `references/failures.md` — the user's two failure renders plus the Canva near-miss, dissected
- `references/exhibits.md` — all 13 references read structurally

**Established the hard way — do not re-derive:**

- The old `/posm-image` prompt said *"ONE subject, filling most of the frame"*. That rule produced both
  failure renders — written for a shelf strip, applied to posters. **Gone with the route rewrite.**
- `keyline.draw_line` / `_KV_SPACE` / reserved bands existed **only because** the architecture assumed
  the poster is a photograph. The translucent type slab is their inevitable output. **Deleted.**
- Master ratio must be **3:4**. `gemini.image()` clamps aspect to `1:1|16:9|9:16|4:3|3:4` and silently
  falls back to 1:1, so a 4:5 request returns a square. Now `posm.MASTER_RATIO` + `render_ratio()`.
- `POSM_FORMATS` had real errors: `shelf-strip` was 16:9 (real is about 12:1), `poster-a3` was 3:4 (A3
  is 5:7). **Fixed** — replaced by `posm.FORMATS`, 30 entries with real mm.
- `gemini-3-pro-image` (`IMAGE_MODEL_PRO`) was defined and **no route called it**. **Fixed** —
  `_img_tier()` in main.py, four named tiers, threaded through every `gemini.image` call site.
- **`gemini.image_from_reference()` at pro tier is excellent** — proven. It took a film frame of a farmer
  and returned an isolated cut-out on white: same face, shirt, lungi, no text, first attempt. Kept at
  `api/media/frame-4c833af248.jpg`.
- `/scene-still` with `reference_urls` **hijacks the prompt** with film-continuity language about faces
  and clothing (main.py:864) — useless for a pack.
- Canva MCP `generate-design` gets structure right and specifics wrong (brass not steel, cream not white
  milk), invents logos, and **generates copy** — one output contained `rozienfii`. `upload-asset-from-url`
  cannot reach localhost. There is no brand kit.
- **Tested conclusion:** templates + approved assets + deterministic type produces in-category POSM. A
  deterministic PIL assembly is in the scratchpad (`assemble.py` -> `kv-assembled.png`). Remaining faults
  were arithmetic, not stochastic. The portal's ceiling is set by whoever authors the templates.

### 2 · The ladder (messaging house gains a 9th layer)

`strategy.py`:

- New **`bridge`** layer between `rtb_functional` and `proof`.
- `ladders: [{id, f, b1, b2, e}]` — **one array of paths on the house.** No graph object. Many-to-many,
  robustness counts and the proof axis are all emergent from a list of paths.
- `link()`, `unlink()`, `link_with_bridge()`, `paths()`, `routes_to()`, `enumerated()`, `find_option()`,
  `draft_ladders()`, `ladder_findings()`, `_backfill()` (older houses get the node in memory).
- `status()` carries `ladders` (hydrated), `ladder_ends`, `ladder_fragile`.
- `BRIDGE_MAX_WORDS = 12`, enforced in code, not by prompt.

**`enumerated()` — divisions are DECLARED, not inferred.** Write them after a colon:
`"Complete nutrition for development: cognitive, physical, social"`. Parsing prose failed in both
directions (lost `cognitive` into the lead-in, kept `social development` with the noun attached). Prose
returns `[]` and a finding says the bridge does not divide.

**Known limit — do not keep tuning.** The drafter satisfies the colon rule with synonyms
(*no surprises, no doubts*) or alliteration (*cold, checked, controlled*). Tightening the prompt traded
axis quality for word-count compliance. The real test — does each division need *different evidence* — is
a human judgement. It is surfaced in the note, not solved.

### 3 · The campaign layer

`api/campaign.py` (new). Stored as **`platform.campaigns[]`** — a child, not a separate store.

- `SHAPES` — **four**: `frame` (sentence with a slot), `device`, `rule`, `act`. Do not assume `frame`;
  forcing every brand into a fill-in-the-blank produces mad-libs.
- `MEDIA` = `strategy.MEDIA` + `influencer` (8). Kept out of `strategy.MEDIA` to avoid churning the
  house screen.
- `ROLE_BY_RUNG` — each medium's role derived from the **rung of the ladder it can carry**. TV resolves
  the tension; POSM can only *recall* emotion, never build it; trade is off the consumer ladder entirely.
- `suggest_shape(house)` — reads culture tags: `idiom` to frame, `iconography` to device, `ritual` to act.
- `axis()` reads the bridge's divisions. `grid()` computes media x axis. **Neither is stored.**
- `draft()` — generates insight/resolution/shape/frame/slots from platform + ladder path + optional brief
  shift. Verified good: produced *"trust she never chose isn't a standard she can pass on with her own
  hands"* and the frame `{X} ki jaanch, roz taaza, roz shakti` off the brand's own idiom.
- `validate()` — 6 findings, all computed, all verified firing.

### 4 · The five tests shrank to two

`ideas.JUDGED` = `ours`, `durable`. `RETIRED_TESTS` records where the other three went:

- `true` -> **computed** by `strategy.ladder_findings()` (a platform on a ladder path stands on something)
- `elastic` -> **the campaign's role table**
- `tension` -> **moved down** to `campaign.insight`, required there

A person's own `verdicts` are stored unfiltered, so retired answers survive in old files.

### 5 · Routes and expressions merged

`EXPRESSIONS` now has **six** keys: `video, social, posm, activation, incentive, media`. `media` gained a
slot; that missing slot was the seam that split the layer in two. `ROUTE_TO_KIND` is **deprecated**;
`_fold_routes()` migrates legacy route text into empty expression slots **on read**, non-destructively.
`expression_jobs` ships the labels.

Four of five "routes" were the same field as an "expression" under another name. The precedence code
reconciling them is where a real defect lived — an empty route blanked a written expression.

### 6 · New routes

```
POST /house-ladder     link/unlink; accepts bridge_text to create+link in one call
POST /ladder-draft     candidate {f, bridge, e} triples — nothing written
POST /campaign         save/drop a campaign
GET  /campaign         layer status, answers bare
GET  /campaign-grid    computed grid
POST /campaign-draft   draft a campaign from platform + ladder path
```

### 7 · The POSM backend (`api/posm.py`, 700 lines)

Built around the nine-layer stack. **`keyline.py` is deleted**; `_KV_SPACE` and the reserved-band
vocabulary are gone from main.py. `producers.KV_LAYOUTS` is now `posm.TYPE_POSITIONS` — same keys, and
they describe the position of a type block **on a flat field** rather than a band held open inside a
photograph.

Almost all of it is tables and arithmetic, not prompts:

- **`FORMATS`** — 30 formats in three families (flat print, environmental, OOH) with real mm, print
  ratio, reading distance, sides, substrate and the trap in each.
- **Computed per format:** cap height (8.3mm/m, USSC) in mm and as a % of the piece; word count by
  distance; aspect delta and the re-flow band; drop-out tier and which layers leave; bleed and safe
  area from the substrate; what physically occludes the artwork.
- **`adaptation()` / `kit()`** — the adaptation sheet, and the cross-piece findings (two-sided pieces,
  a line that will not fit its distance, unmeasured formats, the crop gate).
- **`gate()`** — the library refusal, split in two the way the skill actually splits it: a missing pack
  or logo blocks the **master**, not the hero cut-out (the hero is not the pack, so it proceeds while
  the pack is sourced). `endorser-with-pack` and `range-array` are the exceptions — their library
  reference *is* the subject, so they block the render too.
- **`cutout_prompt()`** — the only prompt in the module: an isolated subject on plain white.
- **`draft()`** — loads `posm_skill` and returns the layer spec. Words are supplied, never generated.
- **`spec_findings()`** — the eight "before you offer it" checks, computed.

New routes:

```
GET  /posm-formats     rewritten — the whole table plus layers, heroes, devices, tiers, kits, gate
POST /posm-image       rewritten — renders the HERO CUT-OUT (isolated on white), not a poster
POST /posm-spec        draft the key visual as a nine-layer spec, through the skill
POST /posm-adapt       adaptation sheets for a kit — all computed, no model call
```

**Verified with two real renders and a real draft**, not just endpoint shapes. The dealer-board sheet
reproduces the reference's own worked example exactly (delta 2.67 wider, 49.8mm caps, 8.2%, 50mm safe).

---

## Current state — verified

- **18/18 `tools/test_tools.py`, 7/7 `tools/checkfe.py`, `tools/contract.py` clean, 165 (method, path)
  pairs, no duplicates.**
- `app.dc.html` = **949,677 bytes** installed; backup `app.dc.html.bak-20260819-094205` (954,212).

> **Two figures in the earlier version of this document were wrong** and are corrected above: it claimed
> 960,973 bytes and 171 endpoints. The real installed file is 949,677 bytes and the app registers 165
> routes (161 `@app.*` decorators + FastAPI's own 4). The installed file being *smaller* than its own
> backup looks like the Design base problem and is not — it carries all six round-17 fixes and strictly
> more ladder/bridge/campaign content than the 954,212 backup; round 19's `IDEA_ROUTES` cleanup removed
> bytes. **Checked by grepping for the fixes, not by trusting the size.** Do that before raising an
> alarm on a byte count.
- Page loads clean. The only console noise is 4 pre-existing SVG placeholder warnings from the NeedScope
  wheel (`{{ w.d }}`, `{{ p.x/y/r }}`) — present before this session.
- **Tenant data clean:** 0 campaigns, 0 ladders, 8 platform files, no stray files.
- `ASK_DESIGN_18.md`, `ASK_DESIGN_19.md`, `Design_Handover_18.zip`, `Design_Handover_19.zip` in root.

### Verified live in the page

9 layers with `bridge` present; the count is dynamic (*"8 of 9 layers decided — Next: Bridges"*); the
ladder panel renders all three columns with *Record this path* and the colon hint.

### NOT verified live (could not reach)

The **two-test strip**, the **campaign panel** (especially prefilled roles), and **typing into an
expression textarea**. Step 4 needs Execution -> *Open the platform*, inside a collapsed panel the
dc-runtime will not open via synthetic events; coordinate clicks need a screenshot and the browser pane is
not displayed. **This is item 1 for Design's QA.**

---

## The Design base problem — read before merging anything

Design has now shipped **twice in a row** built on their own previous return rather than the file we sent:

```
handover 17 shipped        919,425
Design returned            922,468
installed after fixes      926,050   <- + six defects fixed IN their return
round 18 built on          922,468   <- wrong base; all six fixes missing AGAIN
round 19 built on          954,212   <- CORRECT base at last
```

**Always diff for what was REMOVED**, not just what was added. The six round-17 fixes to watch:
`onIdeaExpression` in the render bag · `exprSaved` on `state.idea` plus a rendered marker · *"held here —
adopt the platform to save it"* · `judgeStale` cleared after a re-run · steer precedence
(`(cur.steer||'').trim() ? cur.steer : got.steer`) · `expressions:` sent with adopt plus `gotId` read back.

**`tools/checkfe.py` takes a path argument** — run it on Design's file before anything else. Its 7th check
(*template handlers reach the bag*) caught the dead `onIdeaExpression` control twice. Design's JS port of
checkfe is faithful on the other six but **omits the 7th** — the only one that ever fails.

### Found by click-through QA of the campaign panel (2026-08-20)

The campaign panel was one of the three screens the previous session could not reach. First real click
found one defect immediately:

- **`draftCampaign` said "Pick a ladder path above first"** and the select is ~80 lines *below* the
  button, near Save — the button's own helper text says *"the ladder path chosen below"*, so the toast
  contradicted the label next to it. Anyone reading the toast looks up and finds nothing. Fixed, and
  split into two messages: when the house has paths, say the box is below the slots; when it has none
  the select is **disabled**, so "choose one" is not a followable instruction and it now says to record
  a path in the messaging house instead. Backup `app.dc.html.bak-20260820-175241`; 7/7 checkfe.

### Defects found in Design's files this session

- **Round 18:** all six round-17 fixes missing. `loadCampaign` read `(d.campaign || d)` and bailed on
  `!got.name`, so it returned every time — an existing campaign never hydrated and the roles table came
  up empty. Stale `hint-placeholder-count="5"`.
- **Round 19:** correct base, all 7 checks pass, good `IDEA_ROUTES` cleanup. One real defect — the
  `shift` payload read `sh.ca` / `sh.da` / `sh.line`, **none of which exist**. The real shape is
  `cb[] db[] ca_quote ca_declarative[] da_quote da_declarative[] shift_from shift_to caption`. Fixed, and
  extended to send the CA/DA **attitude** declaratives, because the tension is the attitude gap, not the
  behaviour gap.

---

## What is next

### Design — their queue is nearly empty; the bottleneck is this side

1. **Click-through QA** of the three unverified screens above. Highest value.
2. Learn the real `cb_ca_db_da` field names so the guess does not recur.
3. Three small optional items: surface `retired_tests`; the project-name field at brief creation
   (0 refs, long deferred); `pRowSaved` UI (2 frontend refs, **0** backend refs).

### This side — POSM backend is DONE; what remains

Items 1–4 of the old list are built and verified (see "The POSM backend" above). What is left:

1. **Hand Design the POSM screen.** This is now the bottleneck and it is on their side. The panel that
   exists still renders — it hydrated all 30 formats without a crash — but three strings in it are now
   wrong: *"each format rendered at the ratio it prints at"* (the master renders at 3:4 and formats
   re-flow), *"five ratios"* (there are 30), and the toolkit card still says the house has *eight*
   layers (it has nine). The screen wants rebuilding around the layer spec anyway.

   **The loop in `produceAdaptations` is now wrong and costs money.** It calls `/posm-image` once per
   selected format. Under the layer model the hero cut-out is **one asset for the whole kit** — every
   piece re-flows the same layers — so N formats currently means N near-identical renders of the same
   subject at the same 3:4 master ratio. The new shape is: render the cut-out **once**, then call
   `/posm-adapt` (free, no model) for the per-format sheets.
2. **The library is still empty** — no signed-off pack, no logo, for any brand. `gate()` refuses the
   master until they exist and names the upload. Nothing else can fix that; somebody has to upload the
   real pack shot.
3. **Assembly is not built and may not belong here.** The module produces the spec, the assets and the
   adaptation sheets; laying the nine layers up is a design-tool job. Decide whether the product
   composites (PIL, deterministic — the scratchpad proof-of-concept worked) or hands the spec out.

### Open decisions only the user can make

- **Green or blue for Heritage.** The house prescribes Deep Forest green plus ghee gold; every generated
  asset has converged on blue/red. Needs the real pack and logo to settle.
- **SMP or house core.** The brief's SMP is *pure milk, chosen fresh from good farmers every single day*;
  the house core is *Pure milk is where strength begins*. The worksheet itself flags the core as least
  differentiating, and the film and the SMP both point the other way.
- **Campaign grid cell editing** — needs a storage decision before it can be built.

### The proposed restructuring — "The Compact Spine" (2026-08-20)

A full redesign of the flow from messaging house to campaign, written after reading the generated
worksheet and platform record end to end. **Not built — this is a proposal awaiting the user's call.**

<https://claude.ai/code/artifact/2edb59ac-e860-4f4c-ac7e-2bda71ba10d8>

The diagnosis: the house has crept into the two layers below it. It answers *what is true* (its job),
*how we would show it* (layer 7's caps-titled demo concepts are platform candidates), and *what each
medium makes* (layer 9, written before an idea exists and overridden the moment one is adopted). The
downstream layers then redo both properly. It reads as repetition because it is repetition.

Second diagnosis: facts are being treated as decisions. "500 dairy professionals check the milk every
day" is an input that arrives as one option among five rephrasings of itself, carrying a source flag in
five places.

The shape: **six inputs on a shelf** (brief, evidence, codes & culture, assets, landscape, footprint)
plus **four decisions** — claim, platform, campaign, jobs. Key moves:

- the "ours" test moves UP to the claim (testing ownability after building on a parity claim is the
  expensive order); the bridge stops being a ninth layer and becomes the middle rung
- the house's proof & demo layer merges DOWN into the platform, where those concepts belong
- the proof-axis divisions move DOWN to the campaign — which is why 5 of 6 paths report "the bridge
  does not divide" while a campaign's proof divides naturally. It was asked one altitude too early
- medium becomes **one table**, role and expression in the same row. Digital, OOH and influencer
  currently carry a computed role and no expression; in one table that is a visible empty cell
- `media` leaves the medium list **and the Execution producers** — the user's call, 2026-08-20. It is
  the schedule, not a medium. **Where it goes is PARKED, not decided** — the user will say. Do not
  quietly route it into the plan; the IMC plan is the obvious candidate and that is a separate call.

### P0 IS BUILT AND VERIFIED (2026-08-20)

**The canonical medium taxonomy was settled by the user.** Seven top level, ten leaves:

```
tv · digital(social, influencer, owned, performance) · ooh · posm · activation · trade · pr
```

- `digital` is a **parent, not a medium** — its four leaves carry genuinely different rungs. The old
  single `digital` role ("the bridge, demonstrated, at high intent") was two jobs in one sentence and
  split into `owned` (dwell time, substantiate at length) and `performance` (intercept at intent).
- `video` is an **asset, not a medium** — `VIDEO_DELIVERS_TO = (tv, social, owned, performance)`.
- `activation` is one key; `on-ground` is its alias. Venues are attributes, not sibling media.
- `incentive` folds into `trade` as levers per channel — `sales.LEVERS` already models this.
- `pr` is new and closes a real gap: PR was already one of the seven brief formats
  (`brief_schema.py` has `stakeholders`, `narrative`) and had no rung in the spine.
- `media` is **PARKED** — see below.

**`api/media.py`** (new) is now the only file that says what a medium is. It holds the target taxonomy,
`ROLE_BY_RUNG`, `ALIASES`, `RETIRED`, `NEEDS_REVIEW`, and the three legacy vocabularies **verbatim**.
`strategy.MEDIA`, `ideas.EXPRESSIONS`, `campaign.MEDIA` and `campaign.ROLE_BY_RUNG` now import from it.
All four proved **byte-identical to a baseline captured before the change**.

**`api/shelf.py`** (new) — read-only wrapper over the seven inputs. Stores nothing. Reports 2 of 7
filled on Heritage and says why for each empty one. `evidence()` is the single home of the source flag.

**Two defects caught during P0, both worth remembering:**

- My transcription of `ROLE_BY_RUNG["trade"]` invented its last clause ("a trade kit is wasted" instead
  of "a good campaign dies at the counter"). Caught only because the values were diffed against a
  captured baseline rather than eyeballed. **Always diff a moved constant, never re-read it.**
- `normalise()` was doing two jobs — alias resolution *and* the content-migration guess — so
  `role_for("digital")` returned `owned`'s role, i.e. a parent with no rung answered as though it had
  one. Split into `normalise()` (renames only, always safe) and `migrate()` → `(target, needs_review)`.
  This is the same one-function-two-jobs shape as every other defect in this repo.

Verified: 18/18 test_tools · 7/7 checkfe · contract.py clean · **165 routes, unchanged** · tenant tree
identical **by content hash** · page loaded, Strategy renders "9 of 9 layers decided" with 9 layers and
7 chosen medium options exactly as before · only the 4 pre-existing NeedScope SVG warnings in console.

### P1 IS BUILT AND VERIFIED (2026-08-20)

`GET /jobs` and `GET /shelf` served. **Additive — nothing removed**, so the jobs table and the old
expression/roles blocks show the same data two ways and can be checked against each other.

**`campaign.jobs(house, p, c)`** — one row per leaf, ten keys always present. Resolution per row follows
`stands_on`'s order of authority: the platform's expression for that medium, then the house's line for
it, then empty — with `source` naming which. Takes the SET as `p` and resolves the adopted platform via
`_item()`, matching `get()` and `save()`.

**`_house_lines_by_leaf()` is the P2 fold-on-read, running early on purpose.** It files the house's seven
chosen medium paragraphs against the leaf each now belongs to, *while the layer they came from is still
on screen to check against*. OOH and Owned are drawing on it live, which proves the fold works before P2
removes anything.

Live on Heritage: **10 rows, 7 filled, 3 empty** — influencer, performance, pr. Plus one
`needs_review`: Owned inherited the old `digital` line, and only a reader can tell whether that was a
site, a search line or a social post.

**Two defects caught during P1:**

- I wrote the route against `ideas.chosen()` and `campaign.latest()`, **neither of which exists**. The
  `hasattr` guards I had put around them meant it would have silently passed `None` and rendered an
  empty table rather than failing. `ideas.resolve()` returns `(set, item_id, detail)` — an id string,
  not a dict — and `campaign.get(p, "")` already returns the most recent campaign. Do not guard a
  function you have not confirmed exists; the guard hides the bug.
- Adding `import media` to `campaign.py` made the parameter in `def defaults(media: tuple = ())` shadow
  the module inside that function. Latent rather than live (nothing there used the module yet), and
  renamed to `keys` before it became live. Same hazard as `import plan as plan_mod`.

**`tools/contract.py` gained `check_jobs()`** — 204 row-shape assertions, written *before* the panel
exists rather than after an outage. Proven to bite: removing one field from the row produced 20
mismatches.

Verified: 18/18 · 7/7 checkfe · contract clean · **167 routes** (165 + 2) · tenant tree identical by
content hash · both routes called from the page's own origin with every row complete, old panels
answering 200 · only the 4 pre-existing SVG warnings.

**`ASK_DESIGN_20.md` written** — the jobs table and shelf contract, the settled vocabulary, what not to
build (no `media` row, do not remove the old blocks), plus the four POS panel fixes owed from the POSM
work including the one that costs money (`produceAdaptations` renders once per format).

**Handed to Design.** `Design_Handover_20.zip` = `app.dc.html` + `ASK_DESIGN_20.md` + `tools/checkfe.py`.

**The base sent, for diffing the return:**

```
app.dc.html   951,050 bytes   sha256 15a24e75450f0c8f…
```

Verified byte-identical between the zip and the installed file before sending. `checkfe.py` is in the
zip this time with the instruction to run it — its 7th check is the only one that has ever failed and
Design's JS port omits it.

**On the return, grep for these before anything else.** Two are new this session and are the tell for a
wrong base; six are the round-17 fixes that went missing twice before:

| marker | count in the base |
|---|---|
| `Choose a ladder path below` | 1 |
| `judgeAsk` / `judgeWhy` / `srvAsk` | 3 / 3 / 2 |
| `onIdeaExpression` | 3 |
| `exprSaved` | 11 |
| `adopt the platform to save it` | 1 |
| `judgeStale` | 5 |
| `cur.steer` | 2 |
| `gotId` | 2 |

### P2 IS BUILT AND VERIFIED (2026-08-24)

**The house's medium layer is retired.** 9 layers → 8. `strategy.RETIRED_LAYERS` records where the
question went, `strategy.layer_label()` can still name a retired layer, and `status()` returns the stored
content under a new **`retired_layers`** key — kept OUT of `layers` so no screen offers it as something
to decide, and IN the payload so nothing is unreachable.

**Nothing was lost, and that took four separate protections:**

- `status().retired_layers` carries the 7 chosen options with their options list intact.
- `campaign._house_lines_by_leaf()` folds each chosen line onto the leaf it now belongs to — OOH and
  Owned are drawing on it live in the jobs table.
- The jobs row gained **`rationale`**, carrying the option's `note` (the channel reasoning — *"arterial
  roads near residential clusters, morning drive-time"*). Deliberately **not** routed onward to the
  plan: scheduling is parked, and filing it there would be making the parked decision.
- `docs.py` prints the retired layer under a heading saying where the question went. Without this,
  retiring a layer would have silently deleted 7 paragraphs from every download — the loop walks
  `strategy.LAYERS`. **Verified by building the docx: "8 of 8 layers decided" and all 7 medium lines
  still present.**

Also removed: the two `validate()` findings against the medium layer (a finding with no field to type
into teaches people to ignore the findings list — `campaign.jobs_findings()` asks the coverage question
properly, across 10 leaves instead of 7), and the unreachable `layer_id == "medium"` prompt branch.

**Three defects found by loading the page — none visible in a diff:**

1. **`strategy.houses()` counted `nodes.values()`**, i.e. every node carrying a choice including retired
   ones. A finished house reported 9 decided against a total of 8, so the card said "9 of 9" while the
   house said "8 of 8". Now counts only ids in `order`.
2. **The frontend rendered its own total** — `H_LAYERS.length` — with the server's numerator, in four
   places. Every card read "8 of 9 layers decided" over a finished house. All four now read
   `total_layers` from the server, falling back to the local list.
3. **The open-house rail was built from local `H_LAYERS`, not from `status.layers`** — so the retired
   layer kept its row, and clicking it would hit a route that rejects any layer not in `LAYER_BY_ID`. A
   visible control that errors is worse than an absent one. The rail now filters against the server's
   live layer ids, falling back to the full list before status loads.

Verified: 18/18 · 7/7 checkfe · contract clean (204 jobs-row checks) · **167 routes**, unchanged ·
tenant tree identical by content hash — **the medium node is untouched on disk** · page loaded: list
cards read 8 of 8 / 7 of 8 / 0 of 8, the opened house's rail reads "8 of 8 decided — all decided" with
no medium row, and all counts agree between card and detail · only the 4 pre-existing SVG warnings.

Frontend backup `app.dc.html.bak-20260824-120211`. **The three frontend fixes above are in the installed
file and NOT in `Design_Handover_20.zip`**, which was built before them — so Design's return will need
them merged back, or send them a refreshed base.

### Design's round-20/21 return — reviewed, five real defects found and fixed (2026-08-24)

Design returned `app.dc.html` (963,422 bytes, dropped at OPUS root) + `handover.md` covering BOTH
rounds: the jobs/shelf panel + POSM copy fixes + `produceAdaptations` rewire (round 20), and the
5-edit P2 patch applied cleanly on top (round 21). **checkfe 7/7 including the real 7th check**, all
round-17/19/P2 markers present, nothing reverted. Base-problem discipline held on their side.

**Five real defects found, all fixed and verified live in the browser — none were in Design's remit,
all backend-contract or payload-mismatch class, so fixed directly per the existing convention rather
than sent back as another round:**

1. **`/posm-adapt` — BLOCKING, reproduced with a live 400.** Design's rewired `produceAdaptations`
   sent `format` (singular) once per selected size; the route only accepts `formats` (a list) and
   returns adaptation SHEETS (text specs — cap height, bleed, tier, trap), never an `image_url`. Their
   success check (`d.image_url`) could never be true even with the field name fixed — every piece
   would report as failed forever. **Fixed**: one `/posm-adapt` call for ALL selected sizes at once
   (matches the route's actual free, no-model-call nature even better than the per-format loop did),
   each tile now uses the hero's own `image_url` (the master IS the picture for every format — that is
   the whole point of the layer model) with the sheet supplying the per-format text.
2. **`GET /shelf` — BLOCKING, reproduced live.** `loadShelf`'s guard was `!Array.isArray(d.inputs)`;
   `inputs` is an object keyed by id, never an array, so the panel could never load — not once. A
   second bug sat behind it (`shelfRows` called `.map()` on that same object, which would have thrown
   once the guard was loosened). **Fixed both**; verified live — the shelf now renders "2 of 7" with
   all seven input rows and their `why` text.
3. **Jobs summary — cosmetic, reproduced live.** `jobsTable.empty`/`.needs_review` are ARRAYS of
   medium keys, string-concatenated as if they were counts — rendered
   `"7 filled · influencer,performance,pr empty"`, and the truthy check on `needs_review` fired even
   when empty (`[]` is truthy in JS). **Fixed**; verified live — now reads
   `"7 filled · 3 empty · 1 need review"`.
4. **`campaign.jobs()` — a bug in MY OWN P1 code, not Design's.** A role hand-typed under the legacy
   key `on-ground` was silently dropped and replaced by the computed default for `activation`, because
   the expression/house-line lookups in `jobs()` were aliased through `media.normalise()`/`migrate()`
   and the roles lookup was not. Reproduced by saving a real campaign with a custom `on-ground` role
   and watching `/jobs` report `activation` as untouched. **Fixed**: added `media.legacy_keys_for()`
   (the reverse of `ALIASES`) and check it in `jobs()`'s roles lookup. Verified with a fresh server
   (the first "fix" attempt silently tested against a STALE server process that never died — caught by
   checking `netstat`/the startup log, which showed `Errno 10048: address already in use`. Always
   confirm a restarted server actually bound the port before trusting a re-test).
5. **Literal `—` visible on screen — cosmetic, reproduced live.** Design wrote the JS escape
   `—` directly into four places in raw static HTML text (three user-visible, one a comment) —
   valid inside a JS string literal (164 other correct instances in the file), meaningless in raw HTML
   text, so it rendered as the six literal characters. Two of the four are in the new jobs/shelf copy;
   one is in the POSM step-3 blurb Design edited for the round-20 copy fix. **Fixed** by replacing with
   the real em-dash character, matching the file's own established convention for static text.
   Confirmed the fix touched exactly 4 occurrences, not any of the 164 legitimate ones.

**Everything else in the return was clean and matched spec** — jobs-row field mapping, id-scoping
(verified against two real saved-then-dropped test campaigns, cleaned up after, tenant tree confirmed
byte-identical to the P0 snapshot both before and after), `H_LIVE` rail filtering, the `total_layers`
denominator fixes, no `media` row anywhere, `/jobs` correctly read-only.

Gate after all five fixes: 18/18 · 7/7 checkfe · contract clean (204 jobs-row checks) · tenant tree
identical to the P0 snapshot · loaded live in the browser: jobs table, shelf, needs-review tag, empty
holes, and the em-dash fix all confirmed rendering correctly with real Heritage data · console clean
except the 4 pre-existing SVG warnings. Backup taken before installing:
`app.dc.html.bak-20260824-124549`.

**Did not spend real image-generation credit.** The `/posm-adapt` fix was verified at the contract
level (direct route calls, and a page-origin fetch) rather than by clicking through to a real
`/posm-image` render, since that costs real money and wasn't necessary to prove the fix — ask before a
full paid click-through if that level of proof is wanted.

### P3 IS BUILT AND VERIFIED (2026-08-24) — backend only, deliberately scoped down

The original plan text for P3 was "House provisional/settled · the `ours` test becomes the claim gate,
retired from the platform · `campaign.divisions[]` with bridge fallback." Two rounds of reconnaissance
against the real data model **before writing anything** changed the scope of the middle item — recorded
here so the reasoning survives, not just the result.

**What was found before building:**

- `pillar`/`rtb_id` already exist on every adopted platform — "the ownable fact" the compact-spine
  design wanted at step 01 was **already being captured**, just not resolved to real text or shown
  next to the ownability question.
- `it["rtb"]` (a *different* field from `rtb_id`) is genuinely ambiguous across this codebase: one
  drafting prompt fills it with an id, a different one fills it with prose, and `test_platform()`'s own
  existing proof-gate reads it as though it were always an id. **Pre-existing, not introduced here** —
  flagged for a separate look, not fixed as part of P3.
- There is no "platform adopted at" timestamp anywhere (`adopted` is a bare `True`) — so
  provisional/settled could not be computed from edit-time comparisons without inventing a timestamp
  scheme the rest of the codebase doesn't have.
- The "Two tests" screen is live and working, keyed directly off `ideas.JUDGED`'s two keys. Retiring
  `ours` from that dict **today** would empty half of a shipped, working screen with no replacement UI
  built yet — a regression on the exact "never let a live screen break" discipline this whole retrofit
  runs on.

**Decision made on this basis: retire nothing this round.** `ideas.JUDGED` is untouched, the "Two
tests" screen is untouched. Instead, the DATA needed to ask the same question in the right place was
added, so Design can reposition it in a future round without any further backend change:

- **`ideas.claim_fact(it, house)`** — resolves `rtb_id` (never the ambiguous `rtb`) via the existing,
  already-correct `house_basis()` to the fact's real text, pillar and sourced-ness. Exposed on
  `/idea-platform` as `claim_fact`. Verified live: Heritage resolves to *"500 dairy professionals check
  the milk every single day…"*, functional, sourced.
- **`ideas.set_ladder_confirmed()` + `ladder_confirmed` field** — an explicit, person-set boolean (not a
  timestamp inference), mirroring `set_skipped()`'s existing pattern exactly. Defaults False on every
  platform, including every one adopted before this existed — the honest default, since none of them
  were ever asked. Does NOT auto-reset on later edits (documented trade-off: a materially new fact needs
  a person to notice and re-confirm; auto-resetting risked nagging on an unrelated typo fix).
- **`claim_state`** composed at the ROUTE level in `GET /house/{house_id}` (`"provisional"` |
  `"settled"` | `None`) — NOT inside `strategy.status()`, because `ideas.py` already imports `strategy`
  and the reverse would be circular. `main.py` is the one place both are safely in scope.
- **`POST /idea-platform {house, confirm_ladder:true}`** — a short-circuit mirroring the existing
  `skipped` pattern exactly, so confirming does not require re-sending the whole platform form.
  Verified live: `provisional` → confirm → `settled` → un-confirm → `provisional`, round-tripped
  cleanly.

**`campaign.divisions[]` — built exactly as planned, no scope change.**

- `campaign.save()` accepts `divisions: [str]`, stored verbatim.
- `campaign.axis()` tries the campaign's own `divisions` FIRST — authoritative once written, not
  re-derived from the bridge even if the bridge starts dividing later — and falls back to the existing
  bridge-colon-parse **only** when empty, which is exactly "unaffected for older campaigns."
  `axis_source()` added alongside so a screen can say which one supplied it, matching the
  `stands_on`-style discipline of never presenting a resolved value as neutral.
- `campaign.validate()` gains two findings: divisions outside 2–4 ("one division is not a division"),
  and — genuinely new, not existing anywhere before — a campaign-level "no proof axis" finding that
  fires once `divisions` has had its chance and the bridge fallback is still empty. The house-level
  `ladder_findings()` finding (bridge itself won't divide) is untouched; this is the narrower, campaign-
  specific version that a campaign can now clear on its own without anyone touching the house.
- Verified live with three real save/drop cycles: 3 divisions → axis returns them directly, grid shows
  3 columns, no ladder needed at all; 1 division → the range finding fires; 0 divisions + no ladder →
  the new no-proof-axis finding fires. All three test campaigns dropped, tenant tree restored to
  byte-identical against the P0 snapshot.

**Not done, and explicitly parked rather than silently skipped:** retiring `ours` from `JUDGED`, and
the pre-existing `rtb`/`rtb_id` ambiguity in `test_platform()`. Both need a decision, not a guess.

**Gate:** 18/18 · contract clean (still 204 jobs-row checks, unaffected) · tenant tree byte-identical to
the P0 snapshot after every test round-tripped · page loaded clean, only the 4 pre-existing SVG
warnings — the new fields are additive and the current frontend does not read any of them yet, so
nothing visible changed, as expected for a backend-only phase.

**No frontend touched this round.** `app.dc.html` is unchanged from the post-P2 state Design already
has. The design brief for what to build against this is `ASK_DESIGN_22.md` / `Design_Handover_22.zip`.

**Next: P3 frontend (Design's round)**, then P4 — activation, trade economics, film craft.

### P4 IS PARTIALLY BUILT — activation + trade economics done; film craft deliberately deferred (2026-08-24)

P4 was always three independent workstreams. Built two of them fully this pass; the third (film craft —
grade, sound, plates, viability gate, and the editable cut manifest) is its own dedicated effort, given
it needs new storage and a new library kind, and was not started.

**`api/activation.py` (new)** — the numbers layer for on-ground, on the `posm.py` pattern. Deliberately
does NOT duplicate `producers.VENUES`/`OG_ELEMENTS` (11 venues, 9 elements, already well-written prose)
— it imports and computes on top of them, with a startup check that raises if a `producers.VENUES` key
is ever added without a matching row here, so a new venue can't silently go uncomputable.

- `FOOTFALL` — footfall/intercept-rate/dwell-time ranges per venue, every one marked `[assumed]`
  exactly like `posm.FORMATS` marks its millimetres. Reach and intercept trade against each other by
  design: doorstep/RWA reach few and keep most; transit/mall atrium reach many and keep almost none.
- `cost_per_contact()` — refuses without a real summed cost ("a guess wearing a decimal point"),
  otherwise divides against the intercepted range.
- `PERMISSION_LEAD` — lead days and cost tier per venue, structured data added alongside the existing
  `access` prose rather than a second copy of who to ask.
- The drop-out ladder for `OG_ELEMENTS` at three scales (single-site / multi-site / tour) —
  `capture` and `education` never drop at any scale; `truck` goes first, then `van`+`leave_behind`.
  Verified live: a haat-route idea kept all 7 elements at single-site, dropped only `truck` at
  multi-site, dropped `van`+`truck`+`leave_behind` at tour.
- `kit_sheet()` composes all of the above for one idea; refuses cleanly if the idea's venue isn't on
  file.
- Routes: `POST /activation-kit`, `GET /activation-status`.

**`sales.py` gains `margin_story()` + `talk_track()`** — deterministic, not a model call. Two required
numbers (MRP, trade price); refuses if either is missing or if trade price isn't below MRP (catches a
swapped-argument mistake, verified). Computes margin per unit/case/facing-per-week; an optional
unbranded comparison only fires when BOTH its price and margin % are given, never invented to flatter
the branded number, and carries an explicit note that it assumes equal rate of sale for both since that
is not actually known. `talk_track()` never states a number `margin_story` didn't compute — with no
weekly figure it stops at margin per case rather than filling the gap with something that sounds
finished. Route: `POST /trade-margin-story`.

**Deliberately not wired to `shelf.trade_econ()`.** `margin_story()` is stateless — every call needs
fresh inputs — and there is nowhere in this codebase MRP/case/margin numbers persist. Wiring the 7th
shelf input to "available" would need inventing new storage nobody has asked for yet; left as an
honest, clearly-labelled placeholder until that storage decision is made deliberately, not as a side
effect of this pass.

Verified: 18/18 · contract clean · **170 routes** (167 + 3, exactly the three new ones) · tenant tree
untouched (nothing here writes) · all three new routes exercised over real HTTP including both success
and refusal paths on each · pre-existing `/activation-idea` and `/activation-elements` regression-
checked, unaffected · page loads clean, only the 4 pre-existing SVG warnings.

**No frontend touched.** Design's queue is P3's frontend; P4's ask is a separate round, not sent yet —
queued behind P3 rather than piled on top of it, since Design was about to start on P3 when this landed.

**`ASK_DESIGN_23.md` / `Design_Handover_23.zip` written and ready to send** — same base as round 22
(unchanged, hash-verified identical), explicitly framed as queued behind round 22 rather than stacked
on it, since the two touch different screens and can run in parallel if Design has bandwidth to split.

**Design's round-22 check-in handled without a new handover.** They swapped to the correct base
(confirmed byte-identical, same hash as rounds 22/23) and mapped all three ASK_22 placements
correctly — `claim_fact` beside the ownability badge, `claim_state` badges + return-trip banner,
divisions field near the ladder select. Replied with `ASK_DESIGN_22_REPLY.md` (not a re-issued zip,
since the base and spec hadn't changed) flagging three edge cases: show nothing when `claim_fact` is
unavailable, fire the return-trip banner once per fresh adoption rather than on every visit, and the
divisions field's interaction (rows vs. one delimited input) is their call, not a constraint.

### FILM CRAFT — the editable cut manifest is BUILT AND VERIFIED (2026-08-24)

The plan called this "workstream C's foundation — it should land before the rest of C, since
everything else in that workstream is an edit to an approved film." Built it as its own module rather
than folding it into `filmcut.py`, on the same reasoning `campaign.py` and `posm.py` were kept separate
from what they compute over: bookkeeping and rendering are different jobs.

**`api/cut.py` (new)** — the manifest `/rescore` already implies but never writes down. A cut is
`{id, execution, versions: [{version, parent_version, beats, tracks, grade, master_url, scored_url,
approved, diff, class}]}`. Versions are append-only; approving one does not block the next edit, it
just means the edit becomes version *n+1* rather than a mutation. `tenancy.KINDS` gained `"cuts"`
(scoped from day one, unlike `shots` which leaked between tenants before it was fixed).

**`classify()` is the actual deliverable** — what an edit costs, computed BEFORE anything renders:
`free` (reorder/retime/resuper/re-grade/cutdown — same clips, different cut), `audio` (tracks changed,
picture didn't), `one-clip` (N specific beats need a new render, named by number), `full` (every beat
does, or an explicit `trigger` in `cast`/`location`/`plate` says so — those two don't show up in a beat
diff at all, since the same structure can carry an entirely different film once the person in it
changes).

**Two real bugs found by testing with actual rendered files, not sample data:**

1. **The flagship "free" case — reorder — classified as needing two new renders.** Swapping beats 1 and
   3 compared position-for-position (beat 1's clip changed FROM A TO C), so it looked like both needed
   re-rendering. Fixed to check whether a beat's clip exists ANYWHERE in the parent version, not
   whether it matches at the same position — the whole point of a reorder is that nothing needs
   re-rendering, and the first version of this function got exactly that case wrong.
2. **`None` for `tracks` meant "wipe to empty" instead of "unchanged."** Any edit that didn't explicitly
   resend the full tracks object looked like it had erased the music bed — confirmed at the actual HTTP
   layer (a JSON body with no `tracks` key at all) where this matters most, since a real client won't
   resend unchanged fields on every call. Fixed to match `commit()`'s existing "None means carry
   forward" convention, which `classify()` had not been given.

**Verified with zero cost, not mocked.** Three synthetic clips generated locally via
`ffmpeg -f lavfi -i color=...` (solid-colour, Veo-legal 4/6/8s lengths) — no image or video model
called. `filmcut.stitch()` built a REAL master from them; `cut.start()` wrapped it as v1; all seven
edit classes tested and confirmed correct after the fixes; `commit()` re-stitched a real reorder as v2
(v1's `master_url` stayed untouched, proving immutability); `approve()` signed v2, refused an
unattributed sign-off, and `last_approved()` correctly kept returning v2 after an unapproved v3 was
committed on top. Double-start correctly refused. All five routes
(`POST /cut`, `GET /cut/{execution}`, `POST /cut-propose`, `POST /cut-commit`, `POST /cut-approve`)
hit over real HTTP with the same results. Every test artifact — synthetic clips, rendered test masters,
the cuts manifest itself — deleted afterward; tenant tree confirmed byte-identical to the P0 snapshot.

Gate: 18/18 · contract clean · **175 routes** (170 + exactly 5 new) · page loads clean, only the 4
pre-existing SVG warnings.

**Not built yet, and still genuinely separate pieces:** grade pass, sound bed (needs a new `sfx`/
`ambience` library kind), plates (the library kind exists, unread by any code path), the shot-viability
gate, and beat roles/cutdown ladder in `filmcut.py`. All of them are now edits *against* a cut rather
than operations on a bare file, which is what landing the manifest first was for.

**No frontend touched.** No ASK written for this yet — recommend pairing it with whichever of the
remaining film-craft pieces ships next, since a "propose an edit, see its cost, commit it" screen is
more useful to hand Design once there's at least one real edit type (the grade pass, most likely) to
demonstrate it against.

### Design's cumulative round-20/21/22 return — integrated, three real defects found and fixed (2026-08-24)

Design returned one file (971,856 bytes) covering all of rounds 20, 21 and 22 in sequence, plus
`handover.md` narrating each. checkfe 7/7 (372/372 sc-if, 179/179 sc-for, 1541/1541 div, 233 handlers —
matches their own JS-port counts exactly). All historical markers present, nothing reverted. The
`/posm-adapt` fix from the earlier review survived byte-for-byte — their round-20 narrative describes
the OLD broken shape (`format` singular) because that text was written before they swapped to my
corrected base; the actual shipped code is the fixed version throughout.

**One backend gap, exactly where Design flagged real uncertainty.** Their round-22 note said "I assumed
[`claim_state`] arrives on house LIST items too... flag if that's wrong." It was wrong — `claim_state`
was only ever composed in `GET /house/{id}`, never in `GET /houses` (the list) or `POST /house-new`.
**Fixed**: `claim_state` now composed per-card in `/houses` (one `ideas.for_house()` lookup per house,
cheap at this scale) and sent explicitly as `None` from `/house-new`. Verified against real data: three
Heritage houses (each genuinely has its own adopted platform — not previously checked) all correctly
`provisional`, Parle G correctly `null`.

**Two real frontend defects, both found by testing the actual navigation path a user takes, not by
reading the code:**

1. **The house-card claim badge was computed and never rendered.** `houseCards` correctly built
   `hasClaim`/`claimLabel`/`claimBg`/`claimFg`/`claimLine` for every card, but no `<sc-if>` in the
   `<sc-for>` template ever referenced them — the opened-house header badge was wired correctly, the
   list-card one never was. Live test showed zero "provisional"/"settled" text anywhere on the house
   list before the fix, three badges after.
2. **Reaching the Idea Platform tab via the Strategy sub-nav never loaded the campaign.**
   `sGoTab('idea')` called `loadIdea()` but not `loadCampaign()` — only the OTHER entry point
   (`goIdeaPlatform`, from Home's "Open the platform" link) called both. After a real page reload, the
   more direct nav path left STEP 4 (name, insight, slots, divisions) permanently unhydrated. This is a
   pre-existing gap between two navigation routes to the same screen, not something round 22
   introduced — found because a fresh `navigate()` clears all React state and the earlier click-path
   testing this session had (by chance) always gone through the entry point that worked.
3. **`divisionsText` never actually hydrated, on EITHER nav path, once found.** `campaign()`'s default
   shape carries `divisionsText:''` so the input has something to bind before any load; `loadCampaign()`
   spreads `{...this.campaign(), ...got}`, and `got` (the server response) never carries a
   `divisionsText` key — only `divisions` — so the stale default `''` survived every merge. At render
   time `c.divisionsText != null ? c.divisionsText : (c.divisions||[]).join(', ')` then picked the
   empty string every time, because `'' != null` is true and looks identical to "nothing typed yet."
   Fixed by setting `divisionsText` explicitly from `got.divisions` inside `loadCampaign()` itself.

**All three verified live, end to end, with real saves and a real reload — not just read from the
code:** house-card badges now show correctly (3 provisional, 1 null, matching real per-house platform
state); the full adopt → fresh banner → confirm → real page reload → badge-only sequence confirmed with
no re-nag; a campaign saved with `divisions: ["smell test", "temperature check", "packaging seal"]`
confirmed stored correctly server-side, then confirmed round-tripping back into the comma-separated
input after a real reload via the fixed nav path. Test campaign dropped, `ladder_confirmed` reverted,
tenant tree restored to byte-identical against the P0 snapshot.

Gate: 18/18 · contract clean · page loads clean, only the 4 pre-existing SVG warnings. Frontend backup
taken before installing. **Nothing needs to go back to Design for this round** — all three defects were
squarely in this side's remit (payload/binding mismatches in `app.dc.html`) and are already fixed and
installed.

### THE GRADE PASS IS BUILT AND VERIFIED (2026-08-24)

Extends `composite.py`'s existing `edit()` filter-chain pattern — no new storage, no new library kind,
building on the SAME `-vf` construction `edit()` already uses for aspect crops.

**`composite.GRADES`** — four named looks, not raw sliders (same "declared, not a slider" discipline as
POSM styles and activation scales): `neutral` (an explicit pass-through, so "no grade" is a real
choice), `warm-dawn`, `cool-clean`, `rich-contrast`. Each is one `eq=`/`colorbalance=` ffmpeg filter
recipe. `grade()` applies one to a WHOLE assembled master in a single pass — not per-clip before
stitching — because "one look across every clip" means exactly one correction over the finished film;
grading clips individually first would let them drift again the moment two takes are colour-matched
slightly differently.

**Verified the filter chains are real corrections, not just valid syntax** — a meaningful distinction,
since an ffmpeg filter string can parse and run cleanly while doing something imperceptible or in the
wrong direction. Ran `signalstats` over real output: `neutral` ≈ source (124.6 vs 124.56 YAVG, confirming
genuine pass-through); `warm-dawn` shows U down / V up (a warmer shift, matching its description);
`cool-clean` shows U up / V down (cooler, matching); `rich-contrast` shows the contrast/saturation move
with no colour-balance shift, matching its recipe having none.

**`POST /cut-grade`** — one call: apply a named grade to a cut's current master, write the graded file
to `composite.EDITS_DIR` (already mounted at `/edits`, reused rather than adding a second static mount),
commit it as the next version. `GET /grade-status` serves the named list for a screen to render from.

**A real bug, and it repeated a lesson from earlier this same session, inside the module that states
the lesson.** `cut.commit()` called `cut.classify()` directly; only `cut.propose_edit()` re-classified a
grade-only change from `none` up to `free` afterward. So `/cut-grade` — which calls `commit()` — reported
every grade change as `"nothing that this manifest tracks has changed"` one line after actually
rendering and committing a new graded master. Caught immediately by testing the real route rather than
trusting the unit-level classify() tests already written for it. **Fixed** by moving the grade
comparison inside `classify()` itself so both callers share one path — through a single exit point
(`done()`) so `grade_changed` is reported correctly even when it fires ALONGSIDE a beats or audio
change, which the first fix alone would still have dropped. Seven cases re-verified after the fix,
including the two that would have caught the original bug's blind spot (grade changed simultaneously
with audio, and with a one-clip replacement) and one negative case (resending the same grade name is
correctly NOT flagged as a change).

Verified live over real HTTP with a real ffmpeg-graded output file: `class: free`, `grade_changed: true`,
a genuine graded master written to `/edits/`; both refusal paths (unknown grade name, nonexistent
execution) confirmed. Gate: 18/18 · contract clean · **177 routes** (175 + exactly 2 new) · page loads
clean, only the 4 pre-existing SVG warnings · every test artifact removed, tenant tree byte-identical to
the P0 snapshot.

**No frontend touched, no ASK written yet.** This is the first real edit type to demonstrate the
propose → cost → commit flow against — worth pairing a Design ask for the cut/grade UI with whichever
of sound or plates lands next, rather than sending a screen ask for grade alone.

### THE SOUND LAYER IS BUILT AND VERIFIED (2026-08-24)

The department the plan called "the most under-rated, and entirely absent" — `filmaudio.py` had VO and
music and nothing else.

**Two new library kinds**, split because they behave differently in a mix rather than to be tidy:
`ambience` (a BED under the whole film — room tone, a yard at dawn) and `sfx` (a SPOT at one moment —
the clank, the pour). Merging them into one "sound" kind would leave the mixer unable to tell which of
the two it had been handed. Both added to `MEDIA_KINDS`. Both are uploads by construction: no model
here knows what a dented steel can sounds like on concrete at 5am.

**`filmaudio.mix_timeline()` extended, additively** — a film with neither mixes exactly as before.
Gains `ambience` (a second bed), `ambience_level_name`, and `spots` (`[{url, at, gain?}]`, each delayed
to its own moment like a voice line rather than bedded). Level hierarchy is deliberate and now real:
**ambience under music under voice**, since room tone is meant to be believed rather than noticed.
`AMBIENCE_LEVELS` named (`barely`/`present`/`location`) for the same reason the music ones are.

**`POST /cut-sound`** lays sound over a cut's master and commits the next version;
**`GET /sound-status`** serves the levels plus what the library actually holds, so a screen can say
"no ambience on file" instead of offering an empty picker.

**Three real bugs, all caught by testing rather than reading:**

1. **`music_level(has_voice=bool(labels))` counted foley spots as voice.** A film with foley and no
   narration would have ducked its score to the quiet under-VO level (0.18 instead of 0.55) to make
   room for speech that does not exist. Fixed to count voice labels only — **proven behaviourally**,
   not just by inspection: music-only measured −29.9 dB mean and music-plus-spots −28.7 dB (slightly
   louder from the added spot energy). Had the bug survived, the second would have sat ~10 dB quieter.
2. **Library refs could not be fetched at all.** `/library-file/…` URLs are unknown to
   `filmaudio._download` (it falls through to `gemini.local_path`, which knows `/media/…` and real
   paths only), so the first live run failed all three assets with "could not be fetched". Fixed —
   and fixed by **separating two resolutions that were being conflated**: `as_path()` gives the mixer
   a disk path, `as_url()` gives the manifest the portable `/library-file/…` reference. Resolving once
   and storing whatever came out would have written `C:\Users\…` into a document whose entire purpose
   is to describe the film reproducibly.
3. **`spots` were not in the cut manifest at all**, so a version whose clank at 4.2s existed only as
   an argument somebody passed once could never be reproduced. Added to `cut._clean_tracks()`,
   normalised and **sorted** so re-sending the same three spots in a different order is not mistaken
   for an audio change — verified, along with "adding a spot IS a change" and "re-sending identical
   tracks is NOT".

Verified end to end over real HTTP with real uploaded audio: 4 tracks mixed (music + ambience + 2
spots) at the correct duration; ambience-alone measured ~15 dB below the full mix, confirming the level
hierarchy is real and not merely nominal; a foley spot placed past the end of the cut **warns** rather
than silently vanishing; the signed-off gate confirmed (unsigned uploads correctly invisible to
`/sound-status` until signed); both refusal paths. Gate: 18/18 · contract clean · **179 routes** (177 +
exactly 2) · page loads clean, only the 4 pre-existing SVG warnings.

**Cleanup note:** this was the first piece to write to `library/`, which is real ground-truth storage
rather than scratch. Snapshotted before testing and restored after — library back to its original 2
items / 3 files, `renders/` and `edits/` clear, tenant tree byte-identical to the P0 snapshot.

### PLATES AND THE VIABILITY GATE ARE BUILT — FILM CRAFT BACKEND IS COMPLETE (2026-08-24)

**Plates, finally read.** `plate` had been a library kind since the library existed with **no code path
reading it** — so cast identity travelled as a reference image and place did not travel at all.
`library.shot_references()` now assembles the signed-off reference set in priority order (cast, then
plate) and caps it at the API's three, so when something must drop it is the least load-bearing thing
rather than whatever was last in a list. `/scene-still` attaches them automatically; client-supplied
refs still win and come first. `GET /continuity-status` reports what is held and what is missing.

**A conflict caught before it shipped:** `/scene-still`'s reference prompt said *"Change only the
action, SETTING and camera"* — an explicit instruction to invent a new location. Attaching a plate
under that wording would have had the two fighting and the words would have won: the same failure as
the POSM style strings overriding the isolation clauses. The sentence is now rewritten when a plate is
present ("reuse the SAME location and the same light") and left alone when it is not.

**A second gap found by testing:** the first version auto-added the **plate only**, so a person with a
signed cast frame and no explicit refs got a frame where the location held and the face did not — half
the feature, and it left `shot_references()`'s ordering logic computed-but-unused, which was the smell
that surfaced it. Now both channels attach. Verified at **zero cost** by monkeypatching
`gemini.image_from_reference` and calling the real route function: cast lands before plate, a
client-supplied ref is never displaced, and `use_plate:false` keeps the cast while reverting the prompt.

**`POST /shot-viability`** — five known failure modes (`lip sync`, `fine hand work`, `crowd of faces`,
`on-screen text`, `complex camera move`), each with advice on what to shoot instead. A gate in the
`posm.py` sense: refuses nothing, blocks nothing, and says so in its own `note` — a gate that reads as
a block gets worked around instead of read. Run against seven realistic Heritage shots: flagged all
five modes correctly and passed exactly the two that play to the model's strengths (milk pouring into a
pan, condensation on steel). Notably it flags the 500-people crowd shot, which is the risk identified
in the original craft analysis.

Gate: 18/18 · contract clean · **181 routes** · page loads clean · library restored to its original 2
items / 3 files, tenant tree byte-identical to the P0 snapshot.

### THE FILM-CRAFT DESIGN ASK IS OUT — `ASK_DESIGN_24.md` / `Design_Handover_24.zip`

Covers the whole surface at once, held back until there were three real edit types to demonstrate the
propose → cost → commit flow against: the cut editor (with the five-class cost table and the insistence
that `full` must not look like an ordinary confirm button), the grade picker, the sound panel, and the
two small high-value panels (continuity, viability gate).

**Base sent: 973,564 bytes, `sha256 1810904…` — NOT the base Design last returned.** The ASK opens by
naming the three defects fixed in their return after it landed (the unrendered card badge, the
`sGoTab` missing `loadCampaign()`, the `divisionsText` hydration), so they can diff for them rather
than wonder. Verified byte-identical between zip and installed before sending.

### BEAT ROLES AND THE CUTDOWN LADDER ARE BUILT — THE ORIGINAL FILM-CRAFT PLAN IS NOW COMPLETE (2026-08-24)

The last named item. `filmcut._beat_lengths()` already solved how long a beat may be (Veo takes 4, 6 or
8 and nothing else); what was missing was what each beat is FOR.

**`filmcut.BEAT_ROLES`** — five jobs in narrative order: `hook`, `world`, `mechanism`, `turn`, `brand`,
each carrying `what` it does and what **fails** without it. Not a style opinion: a film with no hook
loses the viewer before the argument starts, one with no turn has nothing for the rest of the campaign
to remind anyone of (which is why `campaign.ROLE_BY_RUNG` gives TV "the turn" and says no other medium
can carry it), one with no brand block was watched by somebody who cannot say whose it was.

**`roles_for(n)` / `plan_beats(seconds)`** — assigns roles to the beat lengths arithmetic already
produces. Extra beats beyond five extend `mechanism`, because a 60-second film is not a 30 with a
longer endframe. Reports honestly where the length does not divide (15s cannot be built from 4/6/8, so
the plan says it runs 18s) and where the length is too short to be a film at all (a 6s single-clip
piece is a bumper; it has no turn, and that is a limit of the length rather than something a better
plan fixes — `missing_roles` says so).

**`cutdown_plan(beats, target)`** — the POSM drop-out ladder applied to TIME. `DROP_ORDER = (world,
mechanism)`; `NEVER_DROPPED = (hook, turn, brand)`, because a cutdown without the turn is a different
film rather than a shorter one. Within a role the LAST occurrence drops first — a film with four
demonstration beats loses the fourth before the first, since the first is where the demonstration
starts. Survivors are trimmed to fit and **never stretched**: padding beats to hit a round number would
be holding frames nobody asked to hold.

**One real bug, caught by reading the output rather than trusting the loop.** The first version dropped
*every* beat of a droppable role before re-checking the total, so a 30s cutdown of a 60s master threw
away all four `mechanism` beats and came back **20s** — "drop the droppable roles" is not the same
instruction as "drop until it fits". Its outer guard also compared a beat *count* against a *duration*,
which is nonsense left from a bad draft. Fixed to drop one beat at a time and stop the moment what
remains fits. Re-verified across 45/30/20/15/6s targets from a 60s master: 44 / 28 / 20 / 15 / 6, with
hook+turn+brand surviving every one — including a deliberately absurd 1s target.

Routes: `GET /beat-plan?seconds=` and `POST /cut-down` (reads beats from a stored cut, or takes them
inline; carries `clip_url` through so the caller can re-stitch, verified picking the right clips).

Gate: 18/18 · contract clean · **183 routes** · page loads clean · tenant tree and library both
confirmed unchanged.

**Film craft is now complete against the original plan:** the editable cut manifest, the grade pass, the
sound layer, plates, the shot-viability gate, and beat roles + the cutdown ladder. Three of the four
"missing entirely" departments from the departmental scorecard (grade, sound, plates) are built; the
fourth was `performance`, which was recorded from the start as a hard limit to route around rather than
a gap to fill.

**Not in `ASK_DESIGN_24.md`** — that ask predates these routes. Written up separately as
**`ASK_DESIGN_25.md`** (now four routes: `/beat-plan`, `/cut-down`, `/continuity-metrics`,
`/continuity-check`), to send alongside their round-24 return rather than revising an ask they are
already building against. No new base file; it builds on the 24 zip.

### The generator now reads the role grammar (2026-08-24)

The role grammar existed and nothing consumed it — structurally identical to `plate` sitting unread in
`library.KINDS` for months, so it was closed before it became the same kind of discovery.

**`filmcut.assign_roles(segments)`** stamps `role` and `role_what` onto planned segments, and both
planners (`plan_by_scene`, `plan_segments`) return through it. The one correctness point: roles attach
to the **moment**, not the raw beat. A moment starts where `continues` is False, because `plan_by_scene`
splits one action across beats when it runs past Veo's 8s ceiling — assigning role-per-beat would make
the first half of an action the `mechanism` and the second half the `turn`, which is a mis-labelled shot
list, not a film. Verified against a scene needing 14s: it splits 8+6 and both halves stay `turn`.

**`main.py: _ROLE_DIRECTION` + `segment_prompt()`** — each shot is now briefed against its job instead
of "this is shot 3 of 4". `brand` is the one that needed care: every prompt in this file correctly ends
with *"no on-screen text or logos"* because type is set in post (a generated Devanagari or Telugu
headline is not writing at all), so the endframe direction asks for the pack **with empty space** for
the line and logo and explicitly says to leave it empty. Asking a role to produce what the rest of the
prompt forbids is how the `plate` work nearly ended up fighting the "change only the setting"
instruction — same trap, caught earlier this time.

Verified without spending a render: forced the fal path with `gemini.available -> False` and captured
the prompts from monkeypatched generators. Four beats of a real 30s Heritage script came back
hook / mechanism / turn / brand on the right scenes, and the endframe prompt was checked to ask for no
lettering while still forbidding text.

Gate: 18/18 · contract clean · checkfe 7/7 · **183 routes** · page loads with only the four
pre-existing SVG placeholder warnings · tenants, library, renders and edits all byte-identical.

### MEDIA · MP·1 built — media unparked, the Execution producer retired (2026-08-25)

**222 routes.** Plan: <https://claude.ai/code/artifact/27f9a664-5c67-446c-9c2e-ec582f55bf25>

**The decision, and it was already half-recorded.** `media.RETIRED["media"]` has said since 20 August:
*"A schedule is not a medium, and it has also left the Execution producers. Where it lands is a
separate call and has not been made — do not quietly route it into the plan."* This phase makes that
call: **its own top-level Media tab**, not a producer, and not folded into the plan.

`execution.RETIRED_KINDS["media"]` records it in the shape `strategy.RETIRED_LAYERS` already uses —
destination plus reason. The empirical argument is in there: the Execution screen **special-cases media
in six places** (skips the message load, exempts it from the proof requirement, four more branches),
and `message_required: False` was the first sign. A producer that cannot carry a message is not one.
Cardinality settles it — four social executions across four phases, one media plan.

Nothing deleted. `MANIFEST["media"]` stays with `retired: True` so stored executions still load and
report their own staleness — verified: `82a9a272f5` still loads, still resolves its label, still lists.
`execution.live_kinds()` is what a client should build a tab strip from, and `/producers` now returns
`live`, `producers` (all) and `retired`.

**I got a fact wrong in the plan artifact and corrected it.** I wrote that Heritage's brand share was
undeclared. It is not — the plan declares **60 with a long recorded reason** that already names the
43/57 gap and says closing it is a spend-weighting decision. My error: the split lives at
`plan["balance"]["brand_share"]`, and I had checked `nodes["balance"]["rows"]`, which is empty by design
because `balance` is a `kind: number` layer. The artifact now carries the correction.

**What that revealed instead — the real defect.** `balance` carried no flag saying whether the split was
*chosen* or merely inherited, so **a deliberate 60 and an untouched one were the same record**. Fixed:
`set_balance` writes `declared: True`, and new `plan.balance_of()` folds the flag for older plans (a
stored reason, or a non-default value, means it was declared) — fold-on-read, like `_fold_routes`. A
new finding now fires on an unconfirmed default, which could never fire before. Verified: Heritage folds
to `declared: True`; a fresh plan reports `False` and raises the finding.

**And the citation reached the wire.** `plan.BRAND_SHARE_BASIS` carries the 60's source (Binet & Field,
~1,000 IPA cases, ~0.5% share growth per 10 points of ESOV) **and** who disputes it (Ehrenberg-Bass —
data unsound, rule too elastic). It was previously a code comment only. A screen showing a bare "60"
shows arithmetic; one showing both shows a position somebody can argue with.

**`api/mediaplan.py` — the derived strategy, read-only, stores nothing.** `strategy_view(p, house)`
returns the plan's channels as a media strategy with `judged_on` read from `plan.ROLES` rather than
copied, the split via `balance_of` + `actual_split`, the phases as a flighting skeleton, and `DERIVES`
— what media takes from each plan layer and what it adds. `derived: True` is on the payload so a screen
cannot offer an edit.

Against the real Heritage plan: 7 channels, 7 with a role, 7 with a side, **0 with a weight**, 3 brand /
4 activation, declared 60 against an actual 43 on a channel-count basis — a −17 gap the plan was already
flagging and nobody had read. The phase containment test resolved real associations for all seven
channels. One finding: *"No channel carries a weight yet"* — non-blocking, because that is the gap the
desk exists to close.

`findings()` deliberately does **not** repeat what `plan.status` already reports (the declared-vs-actual
gap, the unconfirmed default). Two vocabularies for one fact is how they start to disagree.

Routes: `GET /media-status` (roles, sides, `DERIVES`, the brand-share basis, the retirement note),
`GET /media-strategy?plan=`, and `/producers` extended. All exercised over HTTP; 404 on an unknown plan;
no plan returns an honest "No plan open" finding rather than an empty grid.

Gate: 18/18 · contract clean · checkfe 7/7 · **222 routes** · Plan screen still renders "60% brand
declared" · Execution screen still renders · tenants (97), library, renders, edits byte-identical.

**Outstanding for Design (small, and it should not wait):** the frontend's `X_TABS` still hard-codes
`['media','Media planning','media']`, so the retired sub-tab is still on screen. It should build from
`/producers`.`live` — the same pattern the house rail already uses with `H_LIVE`. Until then there are
two homes, which is the failure this retirement exists to prevent.

**Still blocked:** MP·3 needs the money-or-weights answer; MP·2 needs the competitive-spend source.

### Design's round-26 return integrated — the PR screen. Nine defects, one root cause (2026-08-25)

Base confirmed byte-identical to the round-26 zip; no frontend work on this side since, so nothing
reverted. Return 1,185,765 bytes; **after fixes the base is 1,190,404 / `447cc1475270f657…`**, shipped as
`ASK_DESIGN_27.zip`. checkfe 7/7, no new bag collisions, zero literal escapes.

**THE ROOT CAUSE: every vocabulary this backend sends is a DICT keyed by id, not a list.** Modes,
phases, standalone kinds, languages, tiers, trade categories, release parts, kit elements, prominence,
sentiment, roles, notice elements, descent. Design handled it correctly in three places (`rungs`,
`five_w`, `translations`) and not in the rest, which split two ways:

  * `(dict || []).map` → **not a function**. The PR screen **whitescreened on open**:
    `((st && st.phases) || []).map is not a function`.
  * `(dict).length` → undefined → fell through to a hard-coded default and **silently ignored the
    server**. `parts` did this: the release rendered Design's fallback pyramid instead of the payload's
    own parts, including which are required. No crash, no console error — the dangerous variant.

Fixed with one normaliser, **`prSeq(d)`**, routed through **twelve** sites.

**The other eight:**

1. `cr.signatures || cr.signed` — the field is **`signoff`**. Always `{}`, so **every role read "not
   signed" immediately after someone signed**.
2. `cs.roles` — a dict; `.forEach` threw. Crisis panel could not render.
3. `cs.notice_elements` — same, `.map`.
4. `st.descent` — a dict of `{stance, why}` fed to `prLines`, filtered to nothing; chips never appeared.
5. `/pr-kit` sent **bare strings** for b-roll/stills/profile/release and for soundbite without a
   speaker. The route refuses a bare string, so **the kit form 400'd every time**.
6. `/pr-map-drop` sent the **name**; the route keys on the **id** — matched nothing, returned 200, map
   unchanged. Design flagged this themselves and were right. Silent no-op.
7. The jurisdiction control was a `<select>` whose options came from entered frameworks — and a
   framework row has no `id`/`name` for `prOpt`, so the only option was the placeholder and **an
   incident could never be opened from the screen**. Jurisdiction is free text on the backend
   deliberately (an incident can be opened before legal confirms anything). Now an input with the
   confirmed jurisdictions as a hint.
8. `by_outlet` printed `r.outlet || r.name` — a hex id for every outlet that was in the map.
9. The "signatures cleared" band was gated on `body.statement`, but the server clears on **product,
   risk or action** too — so editing one wiped three signatures with **no toast and no band**, the one
   thing the ask called unmissable. Now read off the response: signatures before, none after → announce.

**A verification trap worth remembering:** #9 appeared not to work through three test cycles because I
had edited the file and **not reloaded the page** — the browser was still running the pre-fix bundle.
Same shape as the stale-server trap. A temporary in-code debug hook forced the reload that proved the fix
had been right all along. Reload after every frontend edit before concluding anything.

**`tools/contract.py` widened.** Its find-by-name heuristic had started reading the PR screen's
translation and signature lookups as *layer* lookups and reporting four confident mismatches about fields
no layer carries — exactly the phantom-problem failure its own header warns about. Now scoped to lookups
where `layers` appears within three lines, and it reports how many it skipped. **Verified the real check
still bites** by breaking the layer lookup on purpose and watching it fail.

Driven in a real browser end to end: the funnel against the Heritage plan's three-level ladder; the media
map with tier cards and thirteen languages; and the crisis panel with a real FSSAI framework, a Class I
determination, the 24-hour duty overdue beside an 18.3h-left public notice, three signatures, and a
notice edit clearing all of them and saying so.

Gate: 18/18 · contract clean · checkfe 7/7 · 220 routes · page loads with only the four pre-existing SVG
warnings · tenants (97), library, renders, edits byte-identical, all three PR stores empty.

### Design's round-25 return integrated — three binding defects (2026-08-25)

Base confirmed byte-identical to what was shipped (`259271ed580619cf…`); no frontend work had been done
on this side since, so the swap reverted nothing. Return was 1,022,562 bytes; **after fixes the new base
is 1,023,570 / `89755e5211d069e7…`** and that is what `ASK_DESIGN_26.zip` now carries.

checkfe 7/7. Cross-fragment bag-key sweep: **no new collisions** (only the pre-existing nested `bg`).
Literal `\uXXXX` in markup: **zero** — they adopted the widened lint from round 25's reply and caught
two of their own before shipping. The `/continuity-check` payload and the flat response were both read
correctly, so no repeat of the envelope mistake.

**1 · Every drift finding rendered as an empty string.** `ccDriftFindings` mapped
`f.text || f.finding`; a drift finding carries **neither** — the field is `advice`. The whole actionable
half of the drift report was blank, and the panel showed metric spans followed by nothing, which reads
as "no advice" rather than as a fault. **Invisible until a finding actually fires**, which a clean test
film never does — found only by deliberately re-grading one beat of the test cut to `cool-clean` so the
spread crossed the bar.

**2 · Brightness displayed a bar it can never be measured against.** It arrives `flags: false`, so
`span 47.9 (bar 10)` read as a 3.6× failure on a metric that cannot fail — precisely the misreading the
`flags` field exists to prevent. Now renders `span 47.9 — reported, not flagged`.

**3 · The metric name rendered the payload KEY, not its `label`** — "Luma" where the payload says
"Brightness".

All three proven fixed on screen against a cut with one deliberately mis-graded beat: two full advice
sentences now render, Brightness names itself and carries no bar, and the flagged metrics still show
theirs.

**Design's open question, answered in the reply:** `/continuity-metrics` is fetched on every Craft-tab
open and rendered nowhere. Their own suggestion — an info affordance on the card header — is right, and
`does_not` is the part worth surfacing. Told them to give it that home **or drop the fetch**, because a
route called and never rendered is the same shape as the bag key computed and never bound.

Gate: 18/18 · contract clean (now 60 iterated fields) · checkfe 7/7 · 220 routes · page loads with only
the four pre-existing SVG warnings · tenants (97), library, renders, edits byte-identical.

### PR·7 written — `ASK_DESIGN_26.md`. The PR backend is complete (2026-08-25)

**All six backend phases done. 220 routes, 41 of them PR.** The screen is now the only outstanding
piece, and it is one Design round.

**`ASK_DESIGN_26.zip` deliberately carries NO `app.dc.html`.** The frontend is unchanged since the
ASK_DESIGN_25 zip (still `259271ed580619cf…`, 1,014,921 bytes), so 25's base is the newest file that
exists on this side — which means shipping it again would have Design build 26 on the same base as 25
and collide the two rounds in one file. The ask says plainly: **build on your own round-25 return**, and
if 25 has not started, do it first.

**Written as a large round with an explicit fallback order** — shell and modes → funnel and message set
→ media map → release → coverage → crisis — and says "partial is fine; a half-built panel that reads as
finished is not."

**Opens with a "what NOT to build" table before any section**, because for PR the refusals are the
product: no rupee value on coverage, no send button, no single blended reach number, no journalist ever
shown as suggested, no hard-coded language/tier/class lists, no zero where the answer is "no data", no
"approve all" on the crisis panel.

Every panel's payload was captured from the live modules rather than written from memory, and each
section names the sentence the backend supplies that the screen must not paraphrase — `role_why`,
`why_no_blend`, `why_missing`, `independent.what`, `ready_means`, and the crisis `limits` line.

The three places the ask insists on visible behaviour rather than a field: the **refused** funnel row
stays on screen with its `why`; `proof_missing` must look different from merely unsourced; and editing a
statement or class **clearing every signature** must be visible at the moment it happens.

**One structural judgement flagged for Design to overrule:** PR is proposed as a **top-level nav item
beside Sales enabler** rather than a sub-tab, because standalone PR answers to no plan and no execution
and Sales enabler is the existing precedent for exactly that optional linkage. The user asked for "one
sub tab and two buttons" — the two buttons are as specified; only the nesting is my call.

### PR·6 built — crisis and recall. What it REFUSES is the feature (2026-08-25)

**220 routes.** `pr.py` ~2,130 lines. New tenancy kind `pr_framework`.

Three rules, and every function exists to hold one:

**1. The framework is entered, never remembered.** `set_framework` **refuses an obligation with no
source** ("an obligation nobody can look up is not one this studio may assert") and **refuses a
framework with no named confirmer** ("obligations entered by nobody in particular are a recollection,
and this is the document a recall is run against"). `TRADE_CATEGORIES[…]["regulator"]` names *which*
regulator applies and explicitly does not state what it requires.

An unentered framework returns `entered: False` with a `why_empty` sentence and **never falls back on
another category's**. Proven: a beauty incident in India refuses the class scale outright rather than
grading cosmetics on food's I/II/III.

**2. The class is a determination, not an inference — and the module does not even know the class
NAMES.** They come from the entered framework, because hard-coding I/II/III would impose FSSAI's
taxonomy on cosmetics and cement. `set_class` demands a named person in quality, refuses a class outside
the framework's set, and refuses entirely when no framework exists.

**3. Nothing publishes itself.** Three separate signing functions, not one flag: QA sets the class,
Legal clears the statement, CEO signs when the class carries `escalate_ceo`. **Legal and CEO are refused
before QA has set the class** — nothing can be cleared against obligations nobody has identified. The
required set shrinks automatically when the class does: re-classing I → II dropped the CEO requirement.

**Editing clears every signature** — changing the statement *or* the class wipes the sign-off block.
Same discipline as the translations, same reason: what was signed is no longer what is on the page.

**The design error I caught in testing, and it mattered.** An overdue statutory duty was **blocking**
`ready`. That would mean the module actively delays a recall notice because the company was late on a
*different* obligation — making the situation worse to register disapproval of it. Now overdue duties
are loud (`level: risk`, prefixed `OVERDUE by 4.6h`) but **non-blocking**, surfaced in their own
`overdue` array, and `ready_means` states plainly that ready = "the statement is fit to issue", not
"this recall is on schedule". Getting the notice out must never wait on the authority filing.

**Other pieces:** `NOTICE_ELEMENTS` gates the three things a consumer notice must say — product, risk,
action — because those are the same three in every regime that has a public-notice duty at all.
`standby` holds holding statements written in calm (refused on a non-crisis sheet); a prepared sheet
with no standby statements blocks, and with them reports "Prepared, no incident open" as a *note* —
which is the state a crisis sheet should sit in most of the time. Duties carry `hours_left` computed
from `discovered_at`, with `clock_note` admitting the timestamps are the server's local clock and an aid
rather than the record.

`crisis_status()` also carries a `limits` sentence meant for the screen: *"This studio drafts and
checks. It does not determine the risk class, does not state what a regulation requires, and does not
send."* `findings()` now delegates crisis sheets to it, replacing PR·2's "crisis response is not built
yet" placeholder.

Routes: `GET /pr-crisis-status`, `GET|POST /pr-framework`, `POST /pr-standby`, `POST /pr-incident`,
`POST /pr-risk-class`, `POST /pr-notice`, `POST /pr-sign`, `GET /pr-crisis/{id}`. All exercised over
HTTP, including a full FSSAI framework entered with sources and a Class I recall run end to end.

Gate: 18/18 · contract clean · checkfe 7/7 · **220 routes** · page loads with only the four pre-existing
SVG warnings · tenants (97), library, renders, edits byte-identical; all three PR stores left empty.

**Next:** PR·7 — the screen, as one Design round. All six backend phases are done.

### PR·5 built — the coverage log and the measures, from one table (2026-08-25)

**211 routes.** `pr.py` ~1,700 lines.

**One table, every metric.** `coverage_report()` computes all of it from `sheet["coverage"]`, so two
panels cannot disagree about how much coverage there was — the failure this codebase keeps catching
elsewhere (`grid()` vs `jobs()`, the house count in four templates, `hasCut` in two bags).

**A row is one published item.** The same masthead running the story twice is two rows, and that is
correct. The outlet resolves against the brand's media map so language, tier and the audience figure
come from one place. **A title not in the map is allowed** and marked `off_map` — an unpitched pickup is
real coverage and often the most interesting kind, so refusing it would only teach people to log it
wrongly. The report surfaces those as "worth adding to the map; they are already interested".

**Pull-through is the headline number** — share of items carrying at least one *declared* message, plus
the stronger `front_share` (carried in the headline or lead, where it survives an edit) and a
per-message breakdown. On the test set: 6/8 = 0.75 overall, 0.5 front, and one declared message that
**appeared nowhere** — which is exactly the thing this measure exists to surface and nothing else would.
Logging an item against a message outside the declared set is refused at write time.

**Wire syndication is modelled rather than fudged.** A pickup carries `from_wire` pointing at the wire
item, which must already be logged. The report then splits `independent` from `syndicated`: forty
pickups of one PTI story are forty readerships and **one** editorial decision, and a report hiding
either is misleading. Dropping the wire item takes its pickups with it (verified: 2 removed).

**Sentiment is here because it is the specific thing AVE cannot see** — a demolition and a rave price
identically under it. Three values only; finer grading is a judgement two people score differently and
nobody can audit. `AVE_REFUSAL` is stated once and carried on every report.

**Two deliberate departures from the plan, both to avoid inventing a number:**

1. **No tier multipliers.** The artifact promised "tier-weighted reach". Weighting by an invented
   per-tier multiplier is a number with no method behind it — the same sin as a blended reach figure.
   Each item is instead weighted by its own outlet's **audited circulation**, with the unpriced share
   named. It still achieves what the tier weighting was for: forty small pickups cannot outscore a
   dominant masthead.
2. **Opportunities ≠ reach.** First pass summed circulation per item and called it weighted circulation
   — but two articles in Sakshi are two opportunities to see and roughly *one* readership. Now split:
   `opportunities.circulation` (per item, 3,150,000 on the test set) and
   `distinct_outlet_circulation` (once per outlet, 2,250,000 over 2 outlets), each with a sentence
   saying what it is and is not. Neither is called reach, because there is no exact reach figure
   available while IRS stays suspended.

Routes: `GET /pr-coverage-status`, `POST /pr-coverage`, `POST /pr-coverage-drop`,
`GET /pr-report/{id}`. All exercised over HTTP with every refusal.

Gate: 18/18 · contract clean · checkfe 7/7 · **211 routes** · page loads with only the four pre-existing
SVG warnings · tenants (97), library, renders, edits byte-identical.

**Known gap, deliberately not built:** there is no `drop_map` — emptying a brand's media map of outlets
leaves the (now empty) map file behind. Removing a brand's whole map is destructive and brand-level, and
it does not obviously want a route. Noted rather than built.

**Next:** PR·6 — crisis, with the QA → Legal → CEO ladder and the per-category framework table entered
rather than remembered. Then PR·7, the screen, as one Design round.

### PR·4 built — the release, its gate, the media kit, and `pr_skill` (2026-08-24)

**207 routes.** `pr.py` now 1,441 lines; `api/pr_skill/` is the seventh skill.

**The lead's five questions are STORED FIELDS, not parsed out of prose.** The one design decision worth
recording: gating a paragraph by looking for who/what/when/where/why inside it would be a guess dressed
as a check. `FIVE_W` is five named fields the drafter fills, so the gate names exactly which one is
missing ("The lead does not answer: why") and `pr_skill` gets an exact contract instead of "remember the
5Ws". Verified: blanking `why` produces that finding and nothing else.

**`RELEASE_PARTS`** — headline, dateline, lead, support, quote, background, boilerplate, contact, with
`required` per part. Required-ness is not style: a release with no attributed quote is the company
talking about itself in inverted commas, and one with no contact is a story a journalist cannot check.
A brand-new release blocks on **8** things and names each.

**Word count is a band with advice, not a refusal** (300–400 researched). A gate that refuses a
280-word release teaches people to pad.

**Other gates, all checkable rather than semantic:** an unattributed quote blocks; a mandatory not
placed **verbatim** blocks (locked copy is legal text — the existing studio rule, now enforced for PR);
a release carrying a message outside the sheet's declared set is refused at write time, because
pull-through can only be scored against the set; a carried message whose proof was **deleted** blocks
while merely unsourced does not. Unknown field names are refused rather than stored, so a typo cannot
create a field the gate never checks (`headlien` → refused).

**Translations: written and checked are separate acts, and editing clears the check.** `add_translation`
cannot set `checked_by` at all — only `check_translation` can, and it demands a name. Every edit resets
it to unchecked. A machine rendering of a legal claim shipping because a flag stayed true is the exact
accident that split exists to prevent, and in a script the desk cannot read back nobody downstream
catches it. Also refuses translating a release into its own source language.

**The media kit is elements, not a film.** `KIT_ELEMENTS` = soundbite / b-roll / stills / profile /
release, each with a `fails` sentence. A soundbite with no name against it blocks — unnamed footage of
somebody talking is not a soundbite.

**One imprecision found and fixed during testing.** The b-roll rule originally refused any `/edits/`
path as "a scored master". Wrong: that directory holds a *mixture* — silent `fit_to_beat` trims of
live-action takes, keyed composites, cutdowns *and* scored mixes, since a scored name derives from
wherever its master lived. So `looks_scored()` now keys only on **`-scored`**, which
`main._next_scored_name` produces and which is unambiguous, and `maybe_scored()` flags an `/edits/` path
as a **note asking for confirmation** rather than blocking it. Refusing on a signal that is only
sometimes right teaches people to work around the gate.

**`pr_skill`** — SKILL.md plus three references (`release.md`, `media-map.md`, `failures.md`), 22,819
chars loaded through `skill_instructions()`, the same loader shape `posm._skill_instructions` uses, and
loaded *by the product* rather than only reachable by someone typing `/pr` — the mistake posm made for
months. SKILL.md opens with a "what the code already decides, and you must not re-litigate" section
listing the six refusals, so the skill cannot argue with the gates. `failures.md` is nine named failure
modes each with its tell, why it fails and the fix — including the ad-shaped release, the objective
borrowed from the sales target, the 200-name list, the English-only launch, the VNR that is the ad, the
machine-translated claim, the paid voice presented as earned, AVE, and the recall statement written
from memory.

Routes: `GET /pr-release-status` (parts, five questions, word band, kit elements, whether the skill is on
disk), `POST /pr-release`, `POST /pr-release-write`, `GET /pr-release/{id}`, `POST /pr-translate`,
`POST /pr-translation-check`, `POST /pr-kit`. All exercised over HTTP including every refusal.

Gate: 18/18 · contract clean · checkfe 7/7 · **207 routes** · page loads with only the four pre-existing
SVG warnings · tenants (97), library, renders, edits byte-identical; `pr/` and `pr_map/` left empty.

**Next:** PR·5 — the coverage log and the six measures, computed from one table so no two panels can
disagree. Scraped monitoring belongs there. Then PR·6 (crisis, with the QA → Legal → CEO ladder) and
PR·7 (the screen, one Design round).

### PR·3 built — the media map, and the finding that there are TWO regulators (2026-08-24)

**200 routes.** Plan revision 3: <https://claude.ai/code/artifact/4b6f5b5c-8250-4c77-b1d1-b9fb79d1e7a2>

**All four open questions answered by the user.** Categories = the four existing brand cases (Heritage
Foods/dairy, Kumkum Beauty/beauty, Loomwell/apparel, Sthir Cement/cement). No SimilarWeb or Ahrefs
subscription. Crisis sign-off ladder = **QA → Legal → CEO when mission-critical**. Recommendations
otherwise taken.

**The research finding that changed the design: four categories gave four PRODUCT regulators plus one
that covers all of them, and the second matters more to a marketing studio.**

| category | product regulator |
|---|---|
| dairy/food | FSSAI — Food Recall Procedure Regulations 2017. The strongest case: 24h clock, Schedule I, risk class, Class I public notice with three mandatory elements. Gateable. |
| beauty | CDSCO — Drugs and Cosmetics Act 1940 + Cosmetics Rules 2020. **Asymmetry:** enforcement via registration suspension and prohibited-substance action; **no codified recall procedure with a public-notice template** like food's. The module must not imply one. |
| apparel | BIS — IS 15798 labelling/marking, traceability tightening. A labelling and claims regime, not a recall regime. |
| cement | BIS — mandatory ISI mark under IS 269 + Cement (Quality Control) Order 2003. A spec failure is a certification matter first. |

And the cross-category one: **CCPA Guidelines for Prevention of Misleading Advertisements and
Endorsements, 2022** — ASCI's code is the substance, CCPA gives it teeth. ₹10 lakh, ₹50 lakh for
repeats, plus a 1–3 year endorsement ban. **This upgrades deliverable 7 from good practice to a legal
requirement and widens it:** a disclosable material connection includes monetary payment, *free
product*, a *family relationship* and an *equity stake*. It also reaches beyond PR — the studio
generates claims for POSM, social and film too. Stored as `pr.CLAIMS_AUTHORITY`, deliberately separate
from `TRADE_CATEGORIES` because it is not a per-category fact.

**The map itself.** `tenancy.KINDS` gains `pr_map` — brand-level, not sheet-level, because a campaign
sheet and a recall sheet reach for the same list and a per-sheet copy is how two lists start disagreeing
about who covers dairy in Telugu. 13 languages; 5 tiers with **`wire` first** because one PTI pickup
syndicates and counting it as a single item understates it badly; 4 trade categories.

**Outlets may be suggested; people never are.** `add_journalist` refuses any record whose `origin` is
not `entered` or `imported` — a generated name, beat and contact is an invention about a real individual
that no reader could distinguish from a fact. `SEED_OUTLETS` is deliberately incomplete: only the titles
the concentration research established, with `SEED_SOURCE` recorded, and **8 of 13 markets return an
honest "no seed for this market"** rather than plausible mastheads assembled from memory.

**Freshness has four bands and `unverified` is separate from `stale`** — a row nobody ever checked is
not an old fact, it is not a fact, and collapsing the two would let an unchecked import pass as merely
ageing. Dropping an outlet takes its journalists with it: a contact with no masthead still looks
pitchable, which is worse than absent.

**Two fixes the tests forced, both about not lying with a number:**

1. A language with no circulation figures reported `circulation: 0`. Zero is a circulation; "no title
   here has a figure" is an absence. Now `None`, rendered as "no data".
2. PTI appeared on the missing-circulation list. A wire has no circulation of its own — so it was a
   permanent, unfixable row on a gap list, and a gap list that can never be cleared is one people stop
   reading. Wires now counted in their own bucket with `why_wire`.

`reach_by_language()` returns circulation and digital audience as **two figures with `blended: None`**
and a `why_no_blend` sentence, plus `why_missing` naming the IRS suspension since 2019 as the reason a
gap cannot be filled.

Routes: `GET /pr-map-status`, `GET /pr-map?brand=`, `GET /pr-map-suggest?languages=`, `POST /pr-outlet`,
`POST /pr-journalist`, `POST /pr-map-drop`, `GET /pr-reach?brand=`. All exercised over HTTP with every
refusal.

Gate: 18/18 · contract clean · checkfe 7/7 · **200 routes** · page loads with only the four pre-existing
SVG warnings · tenants (97), library, renders, edits byte-identical; `pr/` and `pr_map/` left empty.

**Note for PR·6:** the sign-off ladder maps onto the statutory split cleanly — QA determines the risk
class (the module must never infer it), Legal clears the statement, CEO is required when the class
triggers a public notice. Escalation becomes a property of the class rather than a judgement made under
pressure.

**Blocked/unactionable:** the digital-audience column is built and optional, but SimilarWeb and Ahrefs
need an interactive OAuth this session cannot run, and there is no subscription behind them anyway. A
title with no figure reports "no data" — never a zero, never an estimate.

**Next:** PR·4 — the text release with its structural gate, then the media kit. Needs `pr_skill`.

### PR·2 built — `pr.py`: the sheet, the objectives funnel, the message set (2026-08-24)

`api/pr.py` + eight routes. **193 routes.** Backend only; no screen, per the plan.

**The store.** `tenancy.KINDS` gains `pr` — scoped from day one, and the comment says why: it will hold
named journalists and later recall correspondence, which is the last material that should leak between
companies on a shared deployment (the lesson `shots` taught by having to be retrofitted). One store,
two modes, copied from `sales.py`'s optional-plan/house shape.

**A campaign sheet with no plan is refused** — "Campaign PR with nothing above it is standalone PR that
has not said so." Unknown mode, kind and phase all refuse with the valid list.

**The funnel descends the plan's own ladder instead of guessing.** The best find of this phase: the
plan's objectives layer already carries `level` — business / marketing / communication, "each answerable
to the one above". So "can PR carry this objective" is answered from **stored data**, not from
keyword-matching a sentence:

    business       -> refused     (PR cannot carry a revenue number; judged on one it looks like a
                                   failure whatever it achieves)
    marketing      -> contributes (moves consideration, does not own the outcome)
    communication  -> owns        (the row a PR objective is written against)

Verified against the real Heritage plan: business refused, marketing contributes, communication owns.
`set_objectives` refuses an objective tied to the business row, over HTTP as well as in-process.

What is *suggested* rather than derived is which of five PR jobs it is — `verify`, `explain`, `prepare`,
`news`, `institution` — by loose cue matching, in `shot_viability`'s spirit: advice, never a filter, and
never the basis of a refusal. It suggested `verify` for the 500-checks objective, matching "purity,
believe, proof". `cues` are stripped from the `/pr-status` payload so no screen can key off them.
Each rung carries a **`cannot`** field, which is what earns the table.

**The message set** is a stored object, not a field, because message pull-through is measured against it
and a set that changed after the outreach would make the metric meaningless. Capped at **3** — a
refusal, not a guideline. Proof resolves against the house's RTBs, i.e. the same evidence list the
platform's claim comes from, so PR and the idea platform provably stand on one set of facts.

**Three proof states, not two.** First pass reported "unsourced" for both a message that was never
sourced and one whose RTB had since been *deleted*. Those need different actions — the second is the
ground moving under a message already declared and possibly already pitched — so `proof_missing` now
distinguishes them and it is **blocking** where plain unsourced is not. `claim_fact` draws exactly this
distinction for the platform's claim; there was no reason PR should draw it less carefully.

**Two places my own comments overpromised, both corrected rather than left.** The `crisis` kind's
comment claimed the store shape "has to know about" risk class, clock and sign-off — it does not carry
them, so the comment was rewritten to say the fields arrive with the logic that validates them, because
a stored field nothing checks looks answered. And `findings()` was asking a recall sheet for a "PR
objective", which is the wrong question at the worst moment; a crisis sheet now reports **"Crisis
response is not built yet — do not run a recall from this screen"** as a blocking finding, and frames
its message set as the three statutory elements (product, risk, consumer action).

Routes: `GET /pr-status` (vocabulary for the screen, incl. the descent and every rung's `cannot`),
`GET /pr-sheets` (filterable by plan and mode), `POST /pr-sheet`, `GET /pr-sheet/{id}` (carries the
funnel and the proof options with it), `GET /pr-funnel?plan=`, `POST /pr-objectives`,
`POST /pr-messages`, `POST /pr-sheet-drop`. Every one exercised over real HTTP, refusals included.

Gate: 18/18 · contract clean · checkfe 7/7 · **193 routes** · page loads with only the four pre-existing
SVG placeholder warnings · tenants (97), library, renders, edits all byte-identical, and
`tenants/default/pr/` left empty.

**Next:** PR·3, the media map across thirteen languages — **blocked** on the two open questions in the
artifact: which categories first (multi-category means multi-regulator, and the trade press differs),
and whether a SimilarWeb or Ahrefs subscription can be authorised for the digital-audience column.

### PR·1 built — PR can be written into, and every producer now inherits the campaign (2026-08-24)

Plan: <https://claude.ai/code/artifact/4b6f5b5c-8250-4c77-b1d1-b9fb79d1e7a2> (revision 2, decisions folded in).

**The expression slot.** `media.LEGACY_EXPRESSIONS` → **`media.EXPRESSIONS`**, with `pr` added. The
rename is the point: its neighbours are lists of *media* awaiting retirement, but this dict is keyed by
**producer kind** and `execution.brief_from` reads `platform["expressions"][kind]` — so it is live, not
legacy, and leaving the name would have made the next reader retire it. Three readers updated
(`campaign` ×2, `ideas` ×1); no `LEGACY_EXPRESSIONS` references remain. `_expression_slots_by_leaf()`
now yields `pr: ["pr"]` automatically, because it maps each key through `normalise` and `pr` is a leaf.

That closes a defect that has been live since PR entered the taxonomy: the jobs table always showed a
`pr` row whose expression cell was **structurally incapable of holding anything**. It now resolves and
reports honestly empty until someone writes one.

**The producer.** `execution.MANIFEST["pr"]` — `medium: "pr"`, `message_required` True,
`proof_obligation.required` **True** (PR's whole role is "the functional truth, earned", so it is
exactly the kind that must be catchable by the proof gate), `makes: [media map, press release, media
kit]`. Served on `/producers`, verified over HTTP. The frontend's `X_TABS` is hard-coded and does not
expose it yet — correct, since PR gets its own screen at PR·7, not an Execution tab.

**The inheritance the user asked for, done once for everyone.** An execution could see the brief and the
idea platform, but **not the campaign** and not the house's own claim — so a producer worked from the
idea without the proof or the proof axis. `brief_from` now also attaches:

  * `campaign` — id, name, shape, ladder, plus `axis` and **`axis_source`**, so a borrowed axis is never
    shown as though it were written here (same rule as `producers.stands_on`).
  * `house` — the core lines, and the claim resolved through `ideas.claim_fact`, which reports
    `available: False` rather than guessing when the RTB it pointed at is gone.

Attached for **every kind, not just PR** — two code paths computing inheritance differently is the
failure this module's own header warns about. Verified: social, posm and video all carry
`['campaign','house','platform']`. Additive and absence-tolerant; older executions simply lack the keys.

**`kind_label()`** — every call site did `label.lower()`, which is right for "Film" → "a film" and wrong
the moment a label is an initialism: the refusal read *"a pr needs its own line"*. A label with no
lowercase letters is left alone. Four call sites switched.

**Module docstring de-numbered.** It said "Six kinds of work come out the far end" while MANIFEST held
seven. Rewritten to name them without a count, with a note saying why — this is the third time a count
written into prose has gone stale here (the docx "five tests", the toolkit card's "eight layers").

Verified end to end against real stored data (house `f7801a3886`, plan `abfaac5fe0`): a `pr` expression
written and resolved as the execution's message with the note reading "the platform's expression for
PR"; the house claim arriving `available: true` with its real RTB text and pillar; a saved campaign
appearing on the brief with `axis_source: "written on this campaign"`. `campaign.save` correctly refused
the first fixture for having no insight.

Gate: 18/18 · contract clean · checkfe 7/7 · **185 routes** · page loads with only the four pre-existing
SVG placeholder warnings · tenants (97), library, renders, edits all byte-identical.

**Two traps worth remembering.** The test wrote to a real platform file, and the hash-only snapshot
could not restore it — recovered byte-exact from `scratchpad/tenants-p0`. Snapshots should copy content,
not just hashes. And a test script run *from the scratchpad* imported hours-old backups of `ideas.py`
and `campaign.py` sitting in that directory, because Python puts the script's own directory on
`sys.path[0]`; it presented as a module missing a function that was demonstrably in the file. Backups
moved to `scratchpad/backups/`.

**Pre-existing, not touched:** `kind_label("activation")` yields "a on-ground activation" — the article
does not agree. Cosmetic, user-visible, and out of PR·1's scope.

**Next:** PR·2 — `pr.py`, the sheet on `sales.py`'s optional-linkage pattern, the objectives funnel and
the message set. Blocked on nothing. PR·3 needs the two answers in the artifact's open questions
(categories first, and whether a SimilarWeb/Ahrefs subscription can be authorised).

### Design's round-24 return integrated — four defects, three of them invisible to every tool (2026-08-24)

Base verified byte-identical to what was shipped (973,564 / `18109046c3…`), and **no frontend work had
been done on this side since**, so a straight swap reverted nothing. Return is 1,012,401 bytes.
checkfe **7/7** including the seventh check Design cannot run; contract clean and now seeing 58
iterated fields, up from 48.

Every one of the four defects below passed checkfe, passed contract, and threw no console error. Three
of them were only findable by getting the screen open with real data in it.

**1 · The cut editor rendered as literally nothing** — the worst kind, because it looks like an empty
card rather than a fault. `craftVals` returns `hasCut: !!cut`, but the Film tab already owns `hasCut`
(`prod.versions.length > 0`) **later in the same object literal**, so it won. With a cut on disk and no
film produced this session, `noCut` was false *and* `hasCut` was false — both branches off. Renamed to
`hasCutManifest`. Same collision class as Design's own `setMusicLevel` → `setCutMusicLevel` catch this
round, but on a bag KEY, which checkfe's unique-class-members check does not cover. Swept the whole bag
for cross-fragment duplicates afterwards: none left (the remaining hits are nested row-mapper literals).

**2 · The film's cut was keyed to the SOCIAL execution.** `cutExec()` returned
`(this.state.execs||{}).social`. With a social execution briefed, the Video tab's cut editor read and
**wrote** the social execution's cut history; with none briefed it said "No cut yet" no matter how many
films existed. Not a typo for `execs.video` — `X_TABS` has no video entry at all, and the Video studio
tracks `production.versions` / `producedUrl` rather than an execution. Re-keyed to the plan
(`video-<planId>`, falling back to `video`); `/cut` treats `execution` as an opaque string, verified.
**The open structural question for Design: should a film be a real `video` execution?** The backend
already has the kind in `execution.MANIFEST`; the frontend has no tab for it.

**3 · `/cut-propose`'s envelope read as its payload.** The route answers
`{edit:{class,why,cost,diff}, cut:{}}` and `craftVals` read `propose.class` / `propose.cost` off the
envelope — `undefined` every time. Two consequences: the cost panel rendered as an empty box, and
`commitDisabled` (`propose.class === 'none'`) was **false** on an unchanged cut, so Commit stayed live
with nothing to commit — the exact inverse of the rule, and Design's own verify item #1. Unwrapped in
`craftVals` so all sixteen fields read the right object from one place. Now proven in the browser both
ways: unchanged → "NONE / nothing to do / Beats 1 unchanged" with Commit grey and inert; edit a super →
"FREE / no render — a re-cut from clips already on disk" with Commit live.

**4 · Literal `\uXXXX` escapes rendering as text.** The reorder buttons showed `↑` / `↓`
instead of ↑ ↓. Design checked for literal `—` and found none — these are different codepoints.
Also fixed a **pre-existing** one ("Plate without the line `→`"). Zero left in markup; the ~170
remaining are inside JS strings, where they are correct.

**Not changed, deliberately:** `loadShots()` has the same borrowed-`execs.social` shape, but it is
**pre-existing** and real shot data is already filed under that key — re-keying it would orphan
`tenants/*/shots`. Flagged, not touched. `loadContinuity()`'s `execution=` param was dropped instead:
`/continuity-status` reads no query parameters, so it was harmless today and a silent wrong-scope read
the day it isn't.

**One backend gap of mine, found by the UI.** Asking for a 2-second cutdown returned a 4-second plan
with `notes: []` — `parse_seconds` clamps to 4..120 silently, so the screen said "already at or under
target" about a film that was neither. `cutdown_plan()` now reports the clamp and returns `asked`
alongside `target`. Design flagged that copy as a guess and was right; it now reads "Nothing dropped —
every beat survives at this length" with the true reason coming from `notes`.

**Verified in the browser with real data:** house cards read **8 of 8** (the P2 retired-layer count,
Design's round-21 verify item, previously unconfirmable without live `/houses`); all four grades render
from `/grade-status` with their `what` sentences; the sound panel shows the "ambience and foley are
uploads, not generations" sentence in place of empty pickers; continuity shows CAST: NONE / PLATE: NONE
with the backend's own `why`; the viability gate on an empty shot list is a graceful no-op, not an error.

Gate: 18/18 · contract clean · checkfe 7/7 · page loads with only the four pre-existing SVG placeholder
warnings · tenants (97), library (3), renders (52), edits all byte-identical after creating and deleting
two real cuts.

**Still outstanding for Design:** the continuity CHECK panel (`/continuity-check`,
`/continuity-metrics`) — §3 of `ASK_DESIGN_25.md` was written after they started this round, so
they built the round-24 `/continuity-status` badges only. That addendum is the next thing to send.

### The continuity checker — and two designs thrown away first (2026-08-24)

`api/continuity.py`, plus `GET /continuity-metrics` and `POST /continuity-check`. **185 routes.**

Two halves, deliberately unequal, and the payload is ordered so the certain one is read first:

**Provenance (certain, free, load-bearing).** Did each shot carry the signed cast frame and the signed
plate? A matter of record, and it names the *cause* rather than a symptom. Live-action shots are exempt
— flagging real footage for a missing cast reference trains people to ignore flags. One bug found and
fixed here: it originally matched a shot's refs against `library.reference_url()`'s *current* value, so
(a) a film with references read as having none whenever the library had nothing signed, and (b) the day
a cast frame is refreshed, every previously rendered shot would retroactively read as unreferenced. Now
judged by the library **kind in the path**, which no refresh changes.

**Look drift (measured, advisory, weaker than it looks).** This is where the work was.

*Calibrated, not chosen.* A named grade moves warmth 13.7–15.4 and luma ~9–10 (measured by grading a
real render and re-measuring the frame). `neutral` confirmed a true pass-through at ±0.1.

*Two designs built and thrown away.* Flagging the deviant shot failed twice on real footage. Comparing
against the median of all shots, a re-graded shot dragged the median toward itself, fell under the bar
and went unreported — while the same shift pushed a legitimately saturated endframe over the bar, so
the checker named an innocent shot. A miss and a false accusation in one run. Leave-one-out fixed the
self-hiding and still flagged the endframe on untouched, correct footage. **The reason is not tuning:
legitimate variance here is bigger than the defect.** A lamp-lit puja and a window-lit sofa in the same
correct film sat 22.8 apart on warmth; a whole grade change is 13.7. Both frames were pulled and looked
at to confirm. This is written into the module docstring as *"NAMING ONE SHOT DOES NOT WORK — do not
rebuild it"*, because the obvious design is the wrong one and nothing in a diff would say so.

*What it reports instead:* the **film's spread** as a film-level finding naming no culprit (and the fix
it points at — one grade pass over the master — is film-level anyway), and **distance from the plate**
per shot, which is principled because the plate is a *declared* intent rather than a neighbour.

*Two refinements that came out of testing, not from the plan.* The `brand` endframe is held out of the
location comparison — a pack lit by sparklers is a different KIND of shot, and left in it drove the
whole film's spread over the bar by itself. Excluding it collapsed natural variance from 15.1 to **3.4**,
which then allowed `SPREAD_BAR` to drop from 14 to **10**: fixing the cause of the noise, rather than
raising the threshold until the noise stopped mattering. And luma never flags — natural spread 36–43
against a ~10 grade delta is the one metric where the signal is smaller than the noise.

Final calibration, six cases: two correct films clean (including one with the endframe deliberately
regraded), four one-grade mismatches all caught, one contrast-only mismatch missed and **documented as
a known blind spot** rather than quietly tolerated. Plate comparison proven both ways over HTTP — a film
against its own location came back clean, the same film against a plate one grade off flagged all three
scene shots. It does not claim to verify identity; that needs a vision model and would be the least
reliable number on the screen.

**Two bugs fixed in passing, both "reported success while doing nothing":**

1. `composite.grade()` handed a still returned `(True, "")` and wrote a **video stream into a .png** —
   a 21KB file Pillow could not open at all. Found because the checker's plate comparison silently had
   nothing to measure. Now branches on `_is_image()`; video grading re-verified unchanged.
2. The checker itself skipped the plate comparison silently when a plate existed but could not be read,
   making the payload identical to "no plate signed off" — a different situation with a different fix.
   Now says so.

### A live blocker found and fixed: every execution on a fresh house (2026-08-24)

Found while answering whether the campaign idea reaches the executions. `execution.message_options()`
still read `house["nodes"]["medium"]` **directly** — the layer that P2 retired (`strategy.RETIRED_LAYERS`
now records it, destination "the jobs table"). So on any house created after that retirement it returned
`[]` for every kind, and `brief_from()` refused with *"write one in the message-by-medium layer"* —
pointing a person at a screen that no longer exists. **Reproduced: social, video, posm, activation and
incentive all returned zero options on a house with no `medium` node.** Nothing could be briefed.

Second defect in the same function: it compared the house's tag against `MANIFEST[kind]["medium"]` raw,
and MANIFEST still spells activation's medium the old way (`on-ground`) — so a line tagged with the
current key `activation` matched nothing. Exactly the rename that bit `campaign.jobs()` once already.

Fixed to resolve in `campaign.jobs()`'s **order of authority** — the platform's expression for this kind
first (it is the most specific decision, and it was made *after* the idea existed), then the house's
folded line — with both sides of the tag comparison passed through `media.migrate()`. `platform_for()`
takes only the house, so no new plumbing was needed. The refusal message now names the jobs table.
Verified across four cases: fresh house + platform yields an option for all five kinds; `on-ground` and
`activation` tags both match; platform ranks above house; and the platform expression is accepted as a
real `message` id.

**Remaining on the film side:** nothing outstanding. The plan's film-craft workstream is complete.

**Fixed in passing:** `.claude/launch.json` — the one the preview tool reads is at the OPUS **root**,
not in `Heritage Marketing Studio/`, and a `runtimeExecutable` path containing a space fails to
resolve. Now `cmd /c .venv\Scripts\python.exe …` with a cwd-relative path.

### The retrofit plan — how to adopt it without breaking things (2026-08-20)

<https://claude.ai/code/artifact/01f35943-ef3e-4211-9324-3dafd36ec3ca>

Companion to the Compact Spine: backend and frontend current-versus-revised, five shippable phases, a
risk register, and a build/extend/skip call on every new skill, tool and connector. **Nothing built.**

The governing constraint is this repo's own history — every shipped defect was a field two sides agreed
on the name of and not the shape. So the plan is additive-only, using the four migration precedents that
already work here: `_fold_routes()` (fold on read), `normalise_judged()` (alias for one release),
`RETIRED_TESTS` (record the destination), `_backfill()` (new structure for old data, in memory).

Plus a **connection register** — the seven user-visible joins that broke in testing (standing-on
resolution, the grounding line, campaign role hydration, expression save marker, adopt/gotId, checkfe's
7th check, placeholder counts), each with the test that proves it, run before any phase ships.

Phases: **P0** `media.py` + `shelf.py`, invisible · **P1** `/jobs` alongside the old panels · **P2**
retire the house medium layer behind a fold-on-read · **P3** split the claim, move the divisions
(highest risk, do alone) · **P4** three independent workstreams — activation, trade economics, and
film craft — then the two write-backs.

**P4 · film craft.** The quality bar is an AI-generated Tanishq ad the user sent, so the target is
"generated with no tells". A generated film fails **department by department**, and scored against the
code: four departments strong (casting via `image_from_reference`, music, voice, type-never-generated),
four half-built (wardrobe, cinematography, edit, and performance which is a hard limit), three **missing
entirely** — the grade pass, any sound design or foley, and location plates (`plate` is in
`library.KINDS` and no code path reads it). Order by return-per-effort: **grade, then sound.** Neither
needs a model and both apply to every film rather than one script. Plus a shot-viability gate on the
posm refusal pattern: refuse lip sync, fine hand work, crowds of faces, on-screen text.

Craft note worth keeping: the constraint set *is* the craft. Milk, steam, steel, condensation and dawn
light are the generator's strong suit, so Heritage is near-ideal — but crowds of individual faces are
not. **Do not show 500 faces, show 500 actions**, one check per cut. The mechanic already says "one of
the 500 checks as a person and a routine"; make the routine the hero.

**The editable cut.** An approved film must be editable without being remade, and today it cannot be —
the film is a rendered file, not an addressable stack. `/rescore` is the existence proof and the
precedent to generalise: it keeps a **silent master** and re-mixes audio over it, new file per take, and
its docstring already states the rule ("picture and soundtrack are separate layers, so swapping the bed
only costs the audio"). `shots.py` already gives every shot an id and a real sign-off chain. What is
missing is a stored, versioned **cut manifest** (beats → shot ids, in/out, supers, tracks, grade,
parent version) so an edit is a diff rather than a regeneration. Free: retime, reorder, supers,
re-grade, cutdowns. One clip: replacing a shot. **Full remake: changing the cast or the location** —
naming those two honestly is half the value. And codes are extracted from the *approved* version, or an
experimental grade quietly becomes the brand palette.

Build/skip calls worth keeping: **build** `activation_skill` + `activation.py` (the one real gap —
`producers.py` has the venue instinct with no table under it), `margin_story()` as arithmetic not a skill
(`sales_skill` already exists), `film_skill` for beat grammar (`filmcut._beat_lengths()` already solves
the Veo clip maths), a local continuity check, and a codes extractor for the Video write-back.
**Trial** Figma MCP as the POSM layup surface — it sets real Indic type and does not invent copy.
**Skip** Canva (generates its own headlines — tested, produced `rozienfii`) and a places MCP (the venue
table is 90% of the value).

### Framework work discussed and agreed but not built

- **Job/role by medium** exists in `campaign.ROLE_BY_RUNG`, but the house's own `medium` node still
  frames itself as *the same message re-expressed*, which is subtly the wrong frame.
- **The two-question authority split** — proposition authority (campaign -> platform -> house) versus
  **codes** authority (the TVC: cast, palette, mnemonic, tagline). `stands_on` does the left column only;
  a second function for the right was agreed and is unbuilt.
- A **conflict finding** should fire when the film's codes contradict the house's codes — live on
  Heritage right now (green versus blue).
- The brief builder produces `cb_ca_db_da` and, apart from the new campaign draft, **nothing downstream
  reads it**.

### The pattern worth remembering

Every defect found this session needed either the page open or a real generation run: a dead handler, a
dead hydration path, a shift payload reading three fields that do not exist, an axis parser confidently
wrong in two directions, and a fixture that wrote a real tenant file. None of them was visible in a diff.

**The POSM session repeated it exactly.** Three defects in `/posm-image` survived every check the repo
has, and all three were found by looking at one generated picture:

- **The subject fallback was the proposition.** With nothing else given, the route fed `stands_on` text
  — *"before a mother makes the first cup, 500 people have already checked the milk that morning"* — in
  as a cut-out brief. The model illustrated the sentence literally: tiny figurines with magnifying
  glasses standing on a carton. Now a 400 that says a hero brief describes something physical.
- **It invented a pack**, which is the single most expensive output this tool can produce. Now a 409
  (`posm.looks_like_pack`) naming the library upload.
- **`_IMG_STYLES` was fighting the prompt and winning.** The style strings describe whole scenes ("on a
  clean minimal surface, soft reflections"), so the render came back on a graduated backdrop with a
  cast shadow and a floor line — all three explicitly forbidden three sentences earlier. Cut-outs no
  longer take a scene style.
- Plus one that was there all along: **the panel sends `route: kv.id`**, and the old ordering took
  `route` before `prompt`, so every render this route ever made was briefed on the string `"kv1"`.

The second render, with a real hero brief, came back exactly right: pure white, no floor line, no
shadow, no lettering, cleanly maskable. Kept at `api/media/still-f0b41cdcd5.jpg`.
