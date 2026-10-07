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

## Decisions needed
1. Unapproved read: never injected (my recommendation) or injected as "tentative"?
2. Overlay level: at the house (messaging house) level, confirmed?
3. Evidence: only the profile and uploaded research, or may the read also draw on web research?
4. Screen: where the read is edited (brand profile screen, a new "Nuance" section) or elsewhere?
