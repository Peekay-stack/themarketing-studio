# Brand-agnostic audit: every surface except Video (7 Oct 2026)

Companion to `VIDEO_BRAND_AGNOSTIC_AUDIT.md`. The decision being tested: the backend carries itself from the **brand profile** (category, market, tone,
mandatories, competitors...) and holds no brand, category or market of its own. **Nothing was changed by this audit.**

## How it was done (and what it cannot see)
1. **Static scan** (`tools/scan_brand_signatures.py`): every string literal (not docstrings) in every backend module, every skill file and reference
   file, and every prompt line of the page, tagged *brand* (Heritage, Doodh, Amul, Nandini, Parle...), *category* (milk, dairy, ghee, kirana, pouch, FSSAI...)
   or *market* (India, Hinglish, ₹, lakh/crore, Telugu...).
2. **Probe** (`tools/probe_brand_signatures.py`): builds each surface's REAL prompt for a **cement** brand (model stubbed, scratch data, nothing written),
   strips the brand's own profile text, and lists what dairy / Heritage / India text rides along anyway.
3. Triage by hand. A scan finds literal signatures, **not behavioural defaults** (e.g. a surface that always proposes family stories). Those need output
   tests with two non-food brands, which spend credit; they are not covered here.

Three kinds of finding, because they need different decisions:
- **A. Brand or category signature**: another brand's name, tagline, example or product rules inside a prompt that every brand receives. Defect.
- **B. Market-bound (India)**: rupees, pincodes, Indian press, Indian regulators. The product is India-first, so this is a scope decision, not a defect.
- **C. Category-scope by design**: logic that only fits FMCG trade (kirana, distributor ROI). It works for food, personal care and the like and is
  incomplete for cement, apparel or durables. A product-scope decision.

## Result at a glance (cement brand, real prompts)

| Surface | Prompt size | Brand / category text that rode along | Verdict |
|---|---|---|---|
| **Brief builder** | 42,314 chars | Heritage, Parle, dairy, milk, curd, "Doodh", ₹ | **A, high** |
| **Messaging house** (strategy) | 8,500 | only the word "heritage" used as a word | clean |
| **Idea platform** | 7,843 | "the name of the dairy that filled it" exemplar | **A, medium** |
| **Campaign** | not captured | static: Heritage tagline and "Meet Your Farmer" as examples | **A, medium** (static) |
| **IMC plan** | 12,401 | nothing | clean |
| **Social** (system prompt) | 4,636 | nothing | clean |
| **Carousel** | 9,891 | "a small pack of milk", "a glass of milk" rules | **A, high** |
| **POSM** | 4,996 | "pouch", "Indian FMCG retail" | **A/C, medium** |
| **Onground** | 6,815 | kirana venue list, "in India" | **B/C, medium** |
| **Sales enabler** | 18,016 | dairy, milk, kirana, Indian FMCG, rupee | **C, high** |
| **PR** | client-built | static: Heritage example in the release reference; India regulators | **A low, B** |
| **Brand profile seed** | n/a | a Heritage Foods profile is created in code when a tenant has none | **A, medium** |

## Findings by surface

### Brief (Brief builder, NeedScope, brief formats)
- **A, high.** Every brief prompt carries the skill's reference files, and they hold worked examples for named brands: `backgrounder-guidance.md` has a full
  "Worked example (Heritage Foods, dairy — illustrative)" table (Heritage, curd, milk, Doodh); `cb-ca-db-da-framework.md`, `smp-guidance.md` and
  `docx-assembly.md` use Parle (19 mentions). A model copies a worked example.
- **A, medium.** The brief's own JSON template gives Heritage values as the examples: `bridge_label e.g. "Pure Doodh Ki Shakti"`, `shift_from e.g.
  "dependable purity"`, `shift_to e.g. "chosen family strength"`. The page's bridge-label placeholder is also "Pure Doodh Ki Shakti".
- **A, medium.** The brief **formats'** default field values are food/FMCG: pack format "500ml & 1L pouch, 1L carton", "nutrition panel", product format
  "FSSAI/regulatory clearance", "shelf-life"; the section help reads "Brand block, legal, FSSAI, nutrition, MRP/batch".
- **B.** The client brief writer says "specific and India-relevant"; the skill says to use the rupee sign for Indian prices.
- Placeholders that name a brand or festival: library naming ("Heritage Nourish+ M..."), project naming ("Diwali same-day push"), Video cast ("warm Indian mother").
- Proposed fix: move worked examples out of the prompt into neutral placeholders (or keep one example per category family, chosen by the profile's category);
  neutral template values; the formats' defaults empty or category-keyed.

### Strategy
- **Messaging house**: clean.
- **Idea platform, A, medium.** `ideas_skill/SKILL.md` teaches "what a mechanic is" with ONE dairy exemplar ("Every pack carries the name of the dairy that filled
  it", then five expressions of it), in every platform draft. Also "Celebrate the mothers of India" (B), and `ideas._STOP` lists "milk" as a stop-word.
  Proposed fix: two or three exemplars from different categories, or neutral wording.
- **Campaign, A, medium.** The campaign shapes' own examples are Heritage's tagline structure ("{X} ki Shakti, Pure Doodh Se", repeated in the page's
  `CAMPAIGN_SHAPES`), "Meet Your Farmer" (a dairy act), "Amul's topical girl" (a named competitor), and "Mothers 25-40". **B:** the draft prompt says "this is India...".
  Proposed fix: neutral examples; the competitor example removed.

### Plan
- **IMC plan** (`plan.py`, `plan_skill`): clean, no brand, category or market in the real prompt. The model for the others.
- **Social plan** (`socialplan.py`): **B** by design: Indian geography, pincodes, "lakh" city bands.
- **Media plan** (`mediaplan.py`): **B**: Indian annual-report disclosure as the spend source.

### PR
- `pr.py` has no brand or category text in code. Its regulator and trade-press table is **keyed by category** (`dairy, beauty, apparel, cement`): data-driven,
  but only those four, and all Indian regulators (FSSAI, CDSCO, BIS) and penalties in rupees (**B/C**: any other category has no row).
- **A, low.** `pr_skill/references/release.md` has a Heritage / milk release as its worked example. `pr_skill` is otherwise India-specific (Devanagari/Telugu type,
  the suspended Indian Readership Survey) (**B**).
- PR prompts are built on the page; the static scan found no dairy text in them.

### Social
- The server's Social block is **clean** (probe). The page's Social prompt carries **pack rules** ("never describe opening, pouring from or holding a pouch unless
  the pack is in use", nutrition panel, ingredients) that assume a packaged product (**C**, low). The "nothing is grounding these posts" notice reads "could be
  **any dairy brand** in the category" and is shown to every brand (**A, low**).
- `packscene.py` (pack rules for Social, Carousel and Video stills) carries dairy words in its patterns ("streams of milk", "milk bags") (**A, medium**).

### Carousel
- **A, high.** `producers.carousel_concept` hardcodes dairy rendering rules for every brand: "describe it being handled the way someone actually handles a small
  **pack of milk** — carried at the side, handed over, tucked in a crate", and "Whenever a **glass of milk** appears anywhere in a route... describe enough visible milk
  in it". Proposed fix: say "the pack" and "the product" and let the profile's category carry the rest, or key the rule to liquids in the profile's `packs`.

### POSM
- **A/C, medium.** The key-visual prompt opens "art-directing point-of-sale material for **Indian FMCG retail**" and "HOW THIS CATEGORY IS BUILT" with FMCG's flat-colour
  construction as the rule for every brand; a "pouch" example; the mandatories band "Veg mark, FSSAI, licence number" (statutory marks for food) is the default.
- The skill's **exhibit library** is ten real FMCG pieces (Dabur, Nivea, Pantene, Mother Dairy, Nandini, Surf Excel); its failure references are Heritage's own renders
  (Heritage, milk, pouch). The retail-format taxonomy is "General trade / kirana", "Chiller-led (dairy, beverages, ice cream)".
- Proposed fix: state which category families POSM supports; take the mandatories band from the profile; add exhibits for the others or label the library FMCG.

### Onground (activation)
- **B/C, medium.** Four prompts open "planning consumer activations **in India**"; the venue list (kirana, modern trade, mall atrium, RWA...) with Indian footfall numbers
  and permission lead times rides in every prompt; the element image prompt says "real Indian location"; leave-behind sizes include a "sample sachet label".
  Proposed fix: take the market from the profile; make the venue list category-aware (a cement brand's venues are dealer points and site meets).

### Sales enabler
- **C, high.** The whole module is Indian FMCG trade logic: the kirana counter, "distributor ROI runs roughly 20-35%, and 25-40% in dairy", Indian quick-commerce
  listing costs, "daily cold-chain" weighting, dairy examples in the tab placeholders ("Sponsored on 'milk'"). For cement (dealer / sub-dealer credit) or apparel
  (MBO / EBO) the channels are not modelled. This is scope, not a leak: say which category families it serves, or make the channel set a profile-keyed table.

### Insights, measurement, demos
- The page's sample cohorts and analysis (dairy cohorts, ₹ CPC) are tagged "Sample"; `demoHouse` and `demoPlan` hold dairy sample data shown only when the server
  returns nothing. Low.

### Brand profile and seeds
- **A, medium.** `brandprofile.py` **creates a Heritage Foods profile in code when a tenant has none** (the scratch tenants in every test print "[brand] seeded the first
  profile: Heritage Foods"), so any fresh tenant's first brand is Heritage. `database.py` seeds a Heritage brief for its (unused) SQL routes.
- The profile's own field help uses several categories ("Dairy, cement and skincare do not share a playbook"): this is the right pattern.

### Mine
- `provocation_skill/SKILL.md` cites dairy precedents (a Kenyan dairy, an old milk campaign). They are precedents, not examples to copy, but they skew toward dairy ideas for a dairy brand.

## Proposed order
1. **Carousel milk rules** and **`packscene`** (high, small, text only).
2. **Brief builder** worked examples and the JSON template values (high, one skill folder).
3. **Idea platform / Campaign** exemplars (medium).
4. **Seed profile**: start a new tenant empty (or with a neutral placeholder) instead of Heritage.
5. **POSM / Onground / Sales enabler / PR**: first decide the scope (which category families and markets), then generalise. These are product choices, not wording fixes.
6. **Guard**: grow `tools/test_video_agnostic.py` into a surfaces guard from `tools/probe_brand_signatures.py` (a cement brand's real prompts must carry no dairy / Heritage /
   Parle text), so these cannot come back. It fails today on items 1 to 3 and 5, which is the point.
