# Nuance layer: plan (7 Oct 2026, DRAFT for the owner's approval; nothing built)

Follows `BRAND_AGNOSTIC_AUDIT_OTHER_SURFACES.md` and `VIDEO_BRAND_AGNOSTIC_AUDIT.md`. Owner's decisions so far:
1. Nuance is not a property of a category. Dairy is mostly family, but ice cream or a dairy beverage can be family OR individual, and a high-protein product is an individual (man or woman). Cement can be a family decision with a man leading, or an individual man. **The model must pick this up when a brand or category comes in.**
2. Hand-written content is welcome as experiment, but the model must **learn nuance on its own** from brand, category, geography, audience and the other variables.
3. Dated Indian benchmarks stay as sourced estimates. 4. India only for now, with room for another market to plug in.

## What this replaces
The earlier idea (a fixed category-family enum with one hand-written playbook per family) is dropped. A family label cannot say "this line is bought by an individual woman, this one by a family", and nothing hand-written can cover every brand. It keeps one thing: code needs something to **select on**, because that is why the Heritage text ended up written into prompts.

## The idea: a Nuance Read, per scope, drafted by the model, approved by a person
A structured document with FIXED DIMENSIONS (so code can select on them) and FREE-TEXT VALUES (so the model is not boxed in).

Each dimension carries: `value` (short), `nuance` (1 to 3 sentences), `basis` (`profile` | `evidence` | `model knowledge`), `unknowns` (what the model could not know and wants confirmed), `status` (proposed | approved | edited).

| Dimension | What it answers | Replaces today's... |
|---|---|---|
| Consumption and roles | who uses, who decides, who pays, who leads; family / household / individual. **One brand can hold several audiences, each with its own** | `decider/payer/user` (one set per brand), "families" defaults |
| Buying mode | habit, considered, project, gift, occasion; cycle | `purchase_cycle` (kept, now per audience) |
| Route to market | how it reaches the buyer, in terms of channel archetypes | `sales.CHANNELS`, `producers.VENUES`, kirana text |
| Proof and claims | what must be proven, which marks and regulator | FSSAI/veg-mark band in POSM, `pr.TRADE_CATEGORIES` use |
| Product in use | how it is handled and shown (poured, applied, worn, built with) and whether a pack appears | Carousel milk rules, `packscene` patterns, "pack" rules |
| Occasions | the moments that matter, by place | the three stray Diwali/Sankranti examples |
| Place | per state: language and register, idiom, culture, sub-regional variants, what NOT to generalise | one line, "write for these places' own idiom" |

Category conventions and insights already exist elsewhere (the provocation audit; the strategy layers). The read **links** to them and does not copy them.

## Three scopes, narrower wins (the rule the prompts already use)
- **Brand read**: the base.
- **House / audience overlay**: states only what differs (the ice-cream house for individuals versus the family-milk house).
- **Execution overlay**: the piece's priority geography and audience (this is where `_execution_block`'s geography line already sits).

## How the model learns, and how it stays honest
- **Inputs:** the profile (category, market, states, languages, competitors, channels, cycle, roles, cheap alternative, notes), the house/platform audience, ingested research, competitor evidence the person gave, and corrections on file.
- **Provenance:** every statement is tagged. The provocation audit already does this with `seen` versus `memory`; the read extends the pattern.
- **Human gate:** only an approved read reaches generation. An unapproved one is shown as "proposed", never asserted. A brand with no approved read gets a neutral lens (no assumptions).
- **Calibration, not rules:** the hand-written experimental reads (dairy, personal care, apparel, cement) are used (a) as shape examples INSIDE the read generator only, always from a different category than the brand's, so they cannot be copied into creative, and (b) as the **acceptance test**.
- **Place cards:** facts stay curated in `geo.py` (language, gap, census, cities, keyed by state). The cultural layer (idiom, sub-regional variants such as Assamese versus Bengali-speaking Assam, or Delhi's Punjabi and Purvanchali households) is model-drafted, person-approved, and stored per brand. No static 36-state table of stereotypes.
- **Learning loop (later):** a person's edit to a read is stored before and after, and offered as a correction on the next similar read.

## What happens to each hardcoded item
- **Becomes read-driven:** Carousel milk rules and `packscene` patterns (Product in use); POSM "Indian FMCG retail" opener and mandatory band (Proof, Route); "in India" in four Onground prompts (market from profile); Video clip/still/music/voice defaults and "English + Hinglish" (Place, Audience, Languages).
- **Stays as keyed data, offered only when the read says it applies:** `geo.py`; `pr.TRADE_CATEGORIES` (becomes a reference list the read cites; an unknown regulator is flagged "confirm", not invented); sales benchmarks and listing costs (kept as sourced, dated estimates); `activation.FOOTFALL` and `PERMISSION_LEAD` (venues filtered by Route; new archetypes added: dealer point, site, store, pharmacy, salon).
- **Deleted:** brand, competitor and tagline examples; dairy exemplars in Brief, Ideas and Campaign; the seeded Heritage profile for new tenants.

## Protecting Heritage
Because the new design is model-drafted, "byte-identical" no longer applies. The protection is: **Heritage's own read is seeded from the dairy text that sits in the code today**, then approved. So Heritage's prompts stay equivalent on day one, and only then does the shared hardcoded text come out. A before/after diff of Heritage's real prompts is the check, and the legacy text stays behind a switch until the owner has compared.

## Phases (each a separate commit; verify local then live)
0. **Store and schema** (`nuance.py`, scopes, provenance, approve/edit routes, one compact rendered block). No generation change.
1. **Prove the risky step first.** Generate reads for Heritage, Sthir, Kumkum, Loomwell AND the owner's cases (family milk; ice cream individual versus family; high-protein for a man and for a woman; cement family-led versus individual). The owner judges. **Needs real model calls and the owner's explicit go-ahead.** Nothing is wired until this passes.
2. **Wire** the approved read into the one chokepoint (`brandprofile.voice_block`, `prompts.system_for`, `producers._ctx`) with Gate / Territory / Register roles. Note `brief_ai.py` never calls `voice_block`, so Brief needs wiring explicitly or it will not see any of this.
3. **Retire the hardcoded content**, one surface per commit, probe-checked with all four brands.
4. **Place cards and occasions**, with Bengali, Delhi and Assamese as named acceptance tests.
5. **Route archetypes in Sales and Onground.** The biggest piece: `SE_TABS` and the first six channel keys are tied to fixed screens, so cement (dealer credit) and apparel (MBO/EBO) need a screen change and a Design handover. Possible interim: show only the channels the read marks relevant.
6. **Guard and learning loop:** grow the probe into a test that no surface carries another brand's markers.

## Risks
- A model read can be confidently wrong or stereotyped about a place or audience: provenance tags, "unknowns", and the approval gate are the answer. They are not a guarantee.
- Prompt weight: the rendered read is kept short; place cards are pulled in only for the piece's priority geography.
- Reads live in tenant files: test fixtures must not write real tenant data (snapshot `tenants/` first).
- Not verified yet: whether the model derives the individual-versus-family distinction reliably. Phase 1 exists to find out.

## Blast-radius sweep (8 Oct): what it found, and what it changes in this plan
Method: every caller and sibling found by grep across backend and page, plus the code read where it mattered. Nothing was run against a model and nothing was changed. Not checked: live data (the live tenant cannot be read without a login).

### 1. A correction to the plan above: the audience does not live on the house
- The messaging house has no audience layer (`strategy.LAYERS`: core, emotional, functional, two RTBs, bridge, proof, culture).
- The audience is a **Plan row** (`plan.LAYERS["audiences"]`: audience, rank, believes_now, pillar) and the occasion is a Plan **phase** row. An execution binds one audience, one occasion, one channel and one measure (`execution.REFS`).
- There is also no "product line" anywhere: the profile has one `category` and one `hero_product`. "Ice cream versus milk" has no home today (separate brand profile? a house?). **So the middle scope moves from house to the Plan's audience row, and the product-line question becomes an open decision.**

### 2. Forwards: everything that reads the profile
- `brandprofile.voice_block` is the chokepoint and has **about 15 prompt call sites in 11 modules**: `prompts.system_for` (Social, Video through `/complete`), `producers._ctx` (Carousel, POSM, Onground), `ideas` (4), `campaign` (2), `plan`, `sales`, `strategy`, `character`, `generation`, `provocation_gen`. Nine more routes in `main.py` return it to the page.
- **Brand-level content added inside `voice_block` reaches all of them with no per-module edit**, which is the cheap path. Overlays (audience row, per-piece) cannot go there, because `voice_block(b)` knows nothing about the plan or the piece. They go where `house_block`, `platform_block` and `_execution_block` already sit, and every other module that holds a house or plan would need its own line. That means touching about seven modules.
- **Paths that do not go through `voice_block`:** `pr.py` (reads `brand_core` directly, line 1415, so it needs its own wiring), `brief_ai.py` (imports `brandprofile` nowhere), `brandbrief.py` and `socialplan`/`mediaplan` (read states and languages only).
- **The page splices the same text into client-built prompts** (`brandPreamble`, about 10 call sites: Brief writer, Social, Video script and departments, IMC lead, analytics). So a brand-level read in `voice_block` reaches those too. Two consequences: (a) it would also reach prompts it does not suit (analytics, brief writer), and (b) `brandPreamble`/`filmVoice` do line-by-line string surgery on the voice text (drop lines starting `TONE:`, rewrite the `MANDATORY ON EVERY PIECE:` line). **New lines must never start with those prefixes, and each section must be a single line or a clearly separated block.**
- **Provocation conflict:** in provocation mode the page and the server drop TONE and the film flag demotes the tagline. A read that states category conventions as Territory would contradict a provocation that is meant to break them. The read needs the same demotion rule, and `provocation_gen.audit_codes` (which already asks the model for category codes) overlaps with the read's conventions. Link them, do not copy.
- **Grounding toggle:** Independent/General mode passes `brand=None` and gets no profile. The read must attach only through a resolved profile, so a General piece carries nothing. Needs a test.

### 3. Backwards: what feeds the read, and where it can go wrong
- **`brandprofile.resolve()` falls back** to the only profile, or the active one, when a document's brand name does not match exactly (`by_name` is exact). The code already records this as the source of cross-brand leaks ("Heritage" versus "Heritage Foods"). **A read keyed through `resolve()` inherits the fallback and could attach the wrong brand's read.** Fix to build in: attach a read only when the document carries a `brand_id` that matches, or add a resolver that reports whether it matched or fell back.
- `derivable()` pre-fills `category`, `market`, `hero_product` and `competitors` from the brief, and the profile's `put()` merges only whitelisted fields. So the profile can change under a read. **The read must store a hash of the profile values it was drafted from**, and show "profile changed since this read" (cheap, because the profile has no staleness today).
- **Geo inputs are mostly empty:** in the dev tenant only Heritage has `states` and `languages`; Kumkum, Loomwell and Sthir are unset and Parle G is empty. The seed has none. **The live Heritage profile is unverified**; the owner should check "Where it actually sells" on the live profile screen. If it is empty, the geography layer does nothing there today.

### 4. Storage
- Embed only the **approved current read** in the profile record, as `brand_core` does (`put()` already tolerates an extra nested key, and `profiles()` and `/brands` return the whole record to the page on every call). **Keep drafts and edit history out of it**: they would bloat every `/brands` response.
- Drafts and history need a separate store: a new kind in `tenancy.KINDS` (added deliberately; `tenancy.dir` creates the folder, including on the live disk) and a cleanup in `brandprofile.remove`, which today deletes only the profile file.
- The audience-row overlay would live on the Plan record; the per-piece overlay on the execution record. Both are existing stores.

### 5. Staleness
- No staleness signature includes the brand profile today (`strategy.signature`, `ideas.platform_signature`, `plan.house_fingerprint`, `execution.stale_because` read only house, plan and platform choices). A changed or newly approved read will therefore not flag anything stale. That matches how the profile behaves. Recommended: stamp the read version on newly generated content for display, and do not add stale-nagging in the first release.

### 6. Frontend (page) changes
- **Brand profile screen** (`app.dc.html` about lines 9500 to 9650 and 23540 to 23810): a Nuance section follows the `brand_core` pattern, which means parallel `bfNuance*` state in **five places**: the reset (`switchBrand` and the form-open reset, about 12539), the load (about 23543 and 23580), the save body (about 23649) and the post-save echo (about 23681). `bfVoice` was once missing from a reset, so that is where it will break first.
- **Plan screen:** audience rows gain a per-audience read (new column or panel).
- **Server-rendered form spec:** `/brand-fields` already renders from data, so a new group costs little.
- **Other page strings the audit did not list:** export filenames and titles hardcode "Heritage" (`downloadScriptWord`, `downloadProductionBible`, `downloadBriefWord`), the Video defaults hardcode a Telugu-accented voice and an Indian accent for every brand (`state.production.voice`, `voiceAccent`), `socialGrounding` says "could be any dairy brand", and the music chips include "Gentle Indian flute". These are page edits in Phase 3.
- `app.dc.html` is edited by Design in alternating rounds. Every page change here needs the merge-never-replace discipline, `checkfe.py`, `partials.py verify`, a reload and a real-page check; the file stays LF-only.

### 7. Other risks found
- **Live deploy ordering:** the hardcoded dairy text can only come out after Heritage's read is approved **on live**. The code deploy and the live data are separate steps. Do it as an owner-run step: a one-time seed route or script that writes Heritage's read from today's text on live, then the code removal. Do NOT seed it from code at startup, which would reintroduce a brand in code.
- **Model-call length:** a full multi-audience read in one call can approach the Cloudflare timeout that already produced a 524 on a 5-deck brief (`/research-ingest` was split out for it). Draft per dimension or per audience, or use the same split-route pattern, and detect `max_tokens` truncation (a past lesson).
- **Tests:** the existing tests that pin the text we would remove are `tools/test_pack_choice.py`, `test_video_agnostic.py`, `test_provocation_gen.py`, `test_provocation_complete.py` and `api/tests/test_made.py`. Each phase 3 commit updates its own.
- **New routes are protected by default** (`RequireLoginMiddleware` exempts only the listed public paths), so no change is needed there.
- **Exports** (`docs.py`) carry the brand name and logo, not the voice text, so Word exports are unaffected unless we choose to include the read.
- **Costs:** one extra model call per read; the read itself adds prompt length to every producer (keep it short).
- **Not verified:** the model's real output for any of this; live data; how Design's current copy of the brand screen differs.

## Decisions needed (revised after the sweep)
1. Unapproved read: never injected (my recommendation) or injected as "tentative"?
2. **Audience level (changed):** attach the audience overlay to the **Plan's audience rows** (my recommendation, since that is where the audience actually lives) instead of the house.
3. **Product line (new):** how is "ice cream versus milk" represented? Options: a separate brand profile per line, a field on the audience row, or a new "line" concept.
4. Evidence: only the profile and uploaded research, or may the read also draw on web research?
5. Screen: where the read is edited (brand profile screen, a new "Nuance" section) or elsewhere?
6. Live seed: the owner runs a one-time step on live to create Heritage's read before the dairy text is removed.
