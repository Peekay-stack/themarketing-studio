# Step 4: what the model drafts (real run, 2026-10-09 11:35)

Model: `claude-opus-4-8` (the studio's own). One call per group, exactly as the profile screen's button does it. Nothing was saved anywhere. Each draft carries its basis: **profile** (stated or directly implied), **context**, or **knowledge** (the model's general knowledge, which you must confirm). A blank means the model said it could not know.

| Brand | drafted | left blank | basis | errors |
|---|---|---|---|---|
| Heritage Foods | 15 | 0 | context 2, knowledge 9, profile 4 | none |
| Kumkum Beauty | 15 | 0 | context 3, knowledge 8, profile 4 | none |
| Loomwell | 15 | 0 | context 2, knowledge 7, profile 6 | none |
| Sthir Cement | 15 | 0 | context 3, knowledge 8, profile 4 | none |
| Heritage Ice Cream (probe) | 15 | 0 | knowledge 14, profile 1 | none |
| Vigor Protein for men (probe) | 15 | 0 | knowledge 11, profile 4 | none |
| Vigor Protein for women (probe) | 15 | 0 | knowledge 11, profile 4 | none |
| Sthir Cement, family home build (probe) | 15 | 0 | knowledge 11, profile 4 | none |
| Sthir Cement, trade buyer (probe) | 15 | 0 | knowledge 12, profile 3 | none |

## Heritage Foods

*dev profile as frozen; asked even where a reviewed answers file exists, to compare with it*

What it was given: Brand: Heritage Foods | Category: Dairy — milk, curd, and value-added dairy | Market: India, strongest across South India (Telangana, Andhra Pradesh, Karnataka, Tamil Nadu), expanding nationally | Hero product: Heritage Pure Milk | Positioning: The purest everyday milk for families who will not compromise | States it sells in: Andhra Pradesh, Telangana | Languages it can be written in (language codes): te, en | Competitors: Amul, Nandini, Dodla, Arokya, loose/unbranded milk | Anything else: A daily cold-chain category: general trade and home delivery dominate, and quick commerce is less disruptive here than in snacks or beverages.

### How the product is shown (9.2s)

- **How it is used or handled** (`product_in_use`, basis: knowledge): The milk is boiled first, then poured into tea or coffee, over cereal, or set into curd; it is almost never drunk straight from the packet cold. The pouch is snipped at a corner and emptied into a vessel, not sipped from directly.
- **What must be visible** (`must_show`, basis: knowledge): - the blue-and-white sachet/pouch or the fresh milk poured into a steel vessel<br>- milk being boiled on a stove or frothing in a vessel<br>- a South Indian kitchen or doorstep setting<br>- steam/warmth signalling the morning boil<br>- a corner-snipped pouch, not a rigid bottle<br>- curd set in a steel or ceramic container  
  *could not know:* Exact current Heritage pack design, colours and SKU formats (pouch sizes, tetra, curd cups)
- **Is the pack in the picture** (`pack_in_scene`, basis: knowledge): always
- **Kind of imagery** (`imagery_style`, basis: profile): Warm, domestic morning-ritual imagery centred on family and the kitchen — the boil, the first cup of chai/coffee, children before school. Purity is shown through freshness cues (steam, white milk, clean steel) rather than clinical studio shots.

### Who buys it and where it is met (13.4s)

- **Household or one person** (`buying_unit`, basis: profile): a household
- **Product lines** (`lines`, basis: knowledge): line: Heritage Pure Milk (toned/full cream pouches) · who_uses: whole family daily · who_decides_pays: homemaker or household head · how_bought: daily pouch pickup or home delivery subscription · where_sold: kirana, dairy booths, doorstep · how_used: tea, coffee, boiling, drinking<br>line: Curd · who_uses: family at meals · who_decides_pays: homemaker · how_bought: cup or pouch, often daily · where_sold: kirana, dairy outlets · how_used: with rice, buttermilk, cooking<br>line: Value-added dairy (paneer, ghee, butter, UHT, flavoured milk) · who_uses: family; kids for flavoured milk · who_decides_pays: homemaker; sometimes individual buyer · how_bought: weekly/stock-up or impulse · where_sold: supermarkets, kirana, modern trade · how_used: cooking, festivals, snacking, on-the-go drinking<br>line: Curd/buttermilk & lassi tetra/pouch · who_uses: individuals, commuters · who_decides_pays: the drinker · how_bought: single-serve impulse · where_sold: convenience, kirana, chillers · how_used: refreshment, with meals  
  *could not know:* Exact SKU lineup and which value-added lines are active in AP/Telangana
- **Routes to market** (`routes`, basis: context): route: General trade (kirana & dairy booths) · who_buys_there: families buying daily milk and curd<br>route: Home delivery / subscription · who_buys_there: regular households wanting doorstep daily milk<br>route: Heritage Parlours / exclusive outlets · who_buys_there: families buying full dairy range<br>route: Modern trade / supermarkets · who_buys_there: stock-up buyers of value-added dairy<br>route: Quick commerce · who_buys_there: urban buyers for top-up and value-added items  
  *could not know:* Actual share split across routes (profile gives none)
- **Where people meet the brand** (`meeting_points`, basis: context): - Neighbourhood kirana stores<br>- Heritage dairy booths/parlours<br>- Doorstep via milkman/delivery<br>- Supermarkets and modern trade chillers

### Proof and marks (6.4s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - FSSAI licence number<br>- Veg symbol (green dot)<br>- Net quantity / volume declaration<br>- MRP (inclusive of all taxes)<br>- Best before / Use by and packed date<br>- Nutritional information per 100ml  
  *could not know:* Exact FSSAI licence number for Heritage; whether packs also carry 'Toned/Full Cream/Standardised' milk-type declaration and the specific fat/SNF percentages required for each variant
- **The worst public event** (`worst_case`, basis: knowledge): A failed safety test or recall for adulteration or contamination — e.g. detergent, urea, added water, or antibiotic/aflatoxin residues found in a milk or curd batch, or a reported illness from spoiled product. FSSAI (and the state food safety authority) acts first, issuing test results, recall orders or licence action.

### Place, language and occasions (12.9s)

- **Place by place** (`place_notes`, basis: knowledge): state: Andhra Pradesh · how_people_buy_use: Daily morning milk via home delivery and kirana; boiled for coffee, curd set at home · register: Telugu-first, warm and family-centric; 'స్వచ్ఛమైన పాలు' (pure milk) · festivals_seasons: Sankranti (big for curd, ghee, sweets); Ugadi; summer buttermilk/curd demand · references: Filter coffee, perugu (curd) with rice, Sankranti sweets<br>state: Telangana · how_people_buy_use: Morning and evening milk via home delivery and general trade; curd and buttermilk daily · register: Telangana Telugu, everyday and trustworthy; 'స్వచ్ఛమైన పాలు' · festivals_seasons: Bathukamma, Bonalu, Sankranti; summer majjiga (buttermilk) season · references: Perugu, majjiga, Irani/filter chai, Bathukamma gatherings
- **Language mix of the work** (`language_mix`, basis: profile): Lead with Telugu for mass warmth and trust, with English for product and modern value-added lines. Voice-over primarily Telugu (including Telangana register for that state), with light English for brand and pack terms.
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: Sankranti · when: Mid-January · where_it_matters: Andhra Pradesh and Telangana — curd, ghee, milk sweets<br>moment: Ugadi · when: March–April · where_it_matters: Andhra Pradesh and Telangana — festive milk/sweets<br>moment: Summer peak · when: April–June · where_it_matters: Both states — buttermilk, curd, cold milk demand rises<br>moment: Bathukamma / Bonalu · when: September–October (Bathukamma); July–August (Bonalu) · where_it_matters: Telangana — festive curd and milk sweets  
  *could not know:* Brand's own launch windows and promo/sale periods not provided

### Look and sound (6.1s)

- **People and settings** (`people_setting`, basis: profile): Show middle-class South Indian families in Telugu-speaking homes — a mother receiving the morning milk packet at the doorstep, boiling it for coffee/chai, setting curd overnight. Meet buyers at the neighbourhood kirana store and the Heritage parlour, and at the doorstep via the home-delivery boy on his early-morning round.
- **What it sounds like** (`sound_world`, basis: knowledge): Warm, unhurried early-morning calm — a clean Telugu voice with a natural Andhra/Telangana accent, or crisp Indian English, speaking plainly about purity and trust. Gentle, homely music over the sounds of a waking household: milk boiling, steel tumblers, the first coffee.  
  *could not know:* Whether the brand uses a jingle or signature sound, and its preferred tone (traditional vs. modern).

## Kumkum Beauty

*states added for this run: Delhi, West Bengal, Assam*

What it was given: Brand: Kumkum Beauty | Category: Beauty — skincare and colour cosmetics | Market: India, metros and tier-1, e-commerce first, then modern trade and beauty specialty | Hero product: The barrier-repair moisturiser | Positioning: Efficacy without irritation, for Indian skin and Indian weather | States it sells in: Delhi, West Bengal, Assam | Competitors: HUL brands, L'Oreal, Mamaearth, Minimalist, The Ordinary, Sugar | Anything else: Regulated by the Drugs & Cosmetics Act and CDSCO, not FSSAI — cosmetic claims only, and claim substantiation is the whole competitive game. Replenishment cycle of roughly three to four months, but the category is trial-driven, so first purchase is the hard part.

### How the product is shown (10.0s)

- **How it is used or handled** (`product_in_use`, basis: knowledge): Scoop or dispense a small amount and smooth it evenly over cleansed face and neck with fingertips, patting it into the skin until absorbed. It is spread on, not rinsed off, rubbed in harshly, or applied in thick visible layers.
- **What must be visible** (`must_show`, basis: knowledge): - a modest pea-sized to fingertip dollop of cream, not a heavy blob<br>- fingers mid-application against bare, un-made-up skin<br>- a smooth matte-to-dewy finish with no greasy sheen<br>- realistic Indian skin tones and textures<br>- the jar or tube open with visible cream<br>- soft, natural daylight rather than harsh studio glare  
  *could not know:* The actual pack format (jar vs pump vs tube) and its exact dieline
- **Is the pack in the picture** (`pack_in_scene`, basis: context): always
- **Kind of imagery** (`imagery_style`, basis: context): Clean, clinical-but-warm derma-adjacent imagery: close skin texture shots, ingredient and claim callouts, and before/after or barrier-diagram cues that signal efficacy and substantiation. Faces are real and relatable rather than glossy glamour, leaning science-credible to separate from pure colour-cosmetics styling.

### Who buys it and where it is met (12.0s)

- **Household or one person** (`buying_unit`, basis: knowledge): either  
  *could not know:* Whether barrier-repair moisturiser is shared in a household or kept personal; skincare often personal but moisturisers can be family-used
- **Product lines** (`lines`, basis: profile): line: Barrier-repair moisturiser (hero) · who_uses: Adults with sensitive/compromised skin · who_decides_pays: The user, self-purchase · how_bought: Trial-driven first buy, then 3-4 month replenishment · where_sold: E-commerce first, then modern trade, beauty specialty · how_used: Daily, AM/PM as leave-on barrier care<br>line: Skincare actives/serums · who_uses: Routine-led skincare buyers · who_decides_pays: The user, self-purchase · how_bought: Claim-led, research before trial · where_sold: E-commerce, beauty specialty · how_used: Targeted step in daily routine<br>line: Colour cosmetics · who_uses: Makeup wearers, younger skew · who_decides_pays: The user, self-purchase · how_bought: Shade/occasion-driven, often impulse · where_sold: Beauty specialty, e-commerce · how_used: Occasion or daily wear, applied to face/lips/eyes  
  *could not know:* Exact SKUs within skincare and colour ranges; the profile only names the hero moisturiser
- **Routes to market** (`routes`, basis: profile): route: E-commerce (brand site + marketplaces) · who_buys_there: Research-led, metro/tier-1 skincare buyers comparing claims<br>route: Beauty specialty (Nykaa/Tira-type) · who_buys_there: Category-engaged buyers browsing and trialling<br>route: Modern trade · who_buys_there: Walk-in shoppers in metros/tier-1 wanting to see/touch before buying  
  *could not know:* Actual share split across routes; profile states sequence (e-comm first) but no numbers
- **Where people meet the brand** (`meeting_points`, basis: profile): - Beauty specialty stores in metros/tier-1<br>- Modern trade shelves (supermarkets/retail chains)<br>- Delhi, Kolkata, Guwahati retail footprints  
  *could not know:* Whether brand runs own counters, kiosks, or sampling events

### Proof and marks (7.2s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - Manufacturing licence no. (Mfg. Lic. No.) under Drugs & Cosmetics Rules<br>- Name and address of manufacturer/importer<br>- Net quantity in metric units<br>- Batch no., Mfg date and Best before/Use by/Expiry<br>- MRP (inclusive of all taxes)<br>- Full list of ingredients in descending order (for pack > threshold)  
  *could not know:* Exact wording/threshold under current Legal Metrology (Packaged Commodities) Rules and whether product is domestic (Mfg Lic No.) or imported (Import Registration No.); owner should confirm against actual pack.
- **The worst public event** (`worst_case`, basis: context): A batch fails CDSCO/state drug control testing or triggers reports of adverse skin reactions (burning, contact dermatitis), leading to a 'not of standard quality' flag and recall. The state Drugs Control / licensing authority acts first, since cosmetics are policed at state level under the Drugs & Cosmetics Act, with CDSCO above it.

### Place, language and occasions (14.0s)

- **Place by place** (`place_notes`, basis: knowledge): state: Delhi · how_people_buy_use: E-commerce first; buys on efficacy claims and ingredient lists, layers moisturiser against pollution and dry winters · register: Hindi-English mix, ingredient-literate, compares actives and INCI · festivals_seasons: Harsh dry winter and dusty, polluted air; Diwali gifting; summer heat · references: Pollution and AQI, dry winter skin, barrier repair for city skin<br>state: West Bengal · how_people_buy_use: E-commerce and beauty specialty in Kolkata; weighs value and gentleness, concerned with humidity and sweat · register: Bengali-English mix, warm and considered · festivals_seasons: Durga Puja as the peak gifting and self-care moment; humid monsoon; cool dry winter · references: Durga Puja prep and new-look, humid Kolkata weather<br>state: Assam · how_people_buy_use: E-commerce led as access is thinner; values non-irritating formula for humid, variable climate · register: Assamese-English mix, plain and practical · festivals_seasons: Bihu as the key cultural moment; long humid monsoon; tea-belt humidity · references: Bihu, high humidity and rain  
  *could not know:* Actual buyer behaviour, retail depth and local speech for each state; whether gifting drives trial here
- **Language mix of the work** (`language_mix`, basis: knowledge): Lead with Hindi-English for Delhi and English across e-commerce, with Bengali-English touches for West Bengal and Assamese-English for Assam where the voice-over is localised. Keep ingredient and claim terms in English for consistency and substantiation.  
  *could not know:* Brand's own tone preference and how localised the VO budget allows
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: Durga Puja · when: Sept–Oct · where_it_matters: West Bengal, Assam<br>moment: Diwali gifting · when: Oct–Nov · where_it_matters: Delhi<br>moment: Dry winter skin season · when: Nov–Feb · where_it_matters: Delhi<br>moment: Bihu · when: Apr (Bohag) and Jan (Magh) · where_it_matters: Assam<br>moment: Big-billion / festive e-commerce sale · when: Oct · where_it_matters: All three states, e-commerce first<br>moment: Humid monsoon · when: Jun–Sept · where_it_matters: West Bengal, Assam  
  *could not know:* Exact e-commerce sale windows the brand plans around and launch timing

### Look and sound (7.4s)

- **People and settings** (`people_setting`, basis: profile): Urban women in their 20s–30s in Delhi, Kolkata and Guwahati flats, shown at the bathroom basin or dressing area dealing with real skin concerns — dullness, sensitivity, humidity in Bengal and Assam, dry pollution-heavy Delhi winters. Also the phone screen itself: the e-commerce product page, swatch close-ups and ingredient-led reels where first trial actually happens.
- **What it sounds like** (`sound_world`, basis: knowledge): Calm, clinical-but-warm Indian-English voice with light regional familiarity, unhurried pace that lets claims and ingredients land rather than hype. Soft, uncluttered music — nothing festive or Bollywood-loud — matching a barrier-repair, efficacy-without-irritation tone.  
  *could not know:* Whether the brand uses Hindi/Bengali/Assamese voiceovers or English-only, and its actual tonal preference (dermatologist-serious vs. friendly).

**Dairy or Heritage words in this brand's drafts:** none

## Loomwell

*states added for this run: Delhi, West Bengal*

What it was given: Brand: Loomwell | Category: Apparel — everyday and casual wear, men's and women's | Market: India, metros and tier-1/2, online-first with a growing own-store footprint | Hero product: The everyday cotton shirt | Positioning: Fewer, better everyday clothes for people who dress for their own day | States it sells in: Delhi, West Bengal | Competitors: Zara, H&M, Max, Uniqlo, D2C natives, unorganised local tailoring | Anything else: Seasonal category with festive and wedding peaks. Online returns run 25-40% and are the single biggest economic issue — fit and colour accuracy matter more than reach. Discounting is structural in the channel, so full-price sell-through is the real measure.

### How the product is shown (11.3s)

- **How it is used or handled** (`product_in_use`, basis: profile): They wear it — pull it on and button it up for an ordinary working or going-out day, worn open over a tee or tucked into trousers, sleeves often rolled. It is not a statement or occasion piece worn once; it is repeat everyday wear, never styled only for a runway or festive-only moment.
- **What must be visible** (`must_show`, basis: context): - true cotton texture with natural creasing, not a flat synthetic sheen<br>- accurate fabric colour as it reads in daylight<br>- collar, placket and real buttons sitting correctly<br>- fit on a real body — shoulder seam, drape, sleeve length<br>- visible weave and stitch detail at cuffs and hem<br>- how it moves/falls rather than a stiff mannequin pose
- **Is the pack in the picture** (`pack_in_scene`, basis: knowledge): rarely  
  *could not know:* Whether Loomwell's own-store and D2C imagery deliberately features hangtags or branded packaging
- **Kind of imagery** (`imagery_style`, basis: profile): Natural-light lifestyle and clean studio shots on real-looking people in everyday Indian urban settings, shot to show true colour and fit rather than high-fashion drama. Calm, understated and daylight-led, leaning on fabric and body over styling theatre — in line with 'dress for your own day'.

### Who buys it and where it is met (11.1s)

- **Household or one person** (`buying_unit`, basis: knowledge): either  
  *could not know:* Whether some lines (e.g. gifting during festive/wedding peaks) skew to household vs self-purchase for this specific brand
- **Product lines** (`lines`, basis: profile): line: Everyday cotton shirt (hero) · who_uses: working men and women dressing for their own day · who_decides_pays: the wearer, self-purchase · how_bought: online-first, fit and colour the deciding factors · where_sold: D2C site, own stores in Delhi & West Bengal · how_used: daily wear to work, casual outings<br>line: Women's everyday casual wear · who_uses: women in metros and tier-1/2 · who_decides_pays: the wearer herself · how_bought: online, high return sensitivity on fit · where_sold: D2C site, own stores · how_used: day-to-day casual and workwear<br>line: Festive / wedding-season pieces · who_uses: men and women attending occasions · who_decides_pays: wearer, sometimes bought as gift · how_bought: seasonal peak buying, occasion-driven · where_sold: online and own stores · how_used: festive and wedding gatherings  
  *could not know:* Whether Loomwell formally separates these as distinct lines or treats them as one everyday range
- **Routes to market** (`routes`, basis: profile): route: Own D2C website / app · who_buys_there: online-first metro and tier-1/2 shoppers who care about fit and colour<br>route: Own retail stores · who_buys_there: shoppers in Delhi & West Bengal who want to try on and avoid return risk  
  *could not know:* Whether Loomwell also sells via marketplaces (Myntra, Ajio) or only own channels; actual share split across routes
- **Where people meet the brand** (`meeting_points`, basis: profile): - Loomwell own stores in Delhi<br>- Loomwell own stores in West Bengal (Kolkata)<br>- Festive and wedding-season shopping occasions  
  *could not know:* Exact store locations, presence in malls vs high streets, any pop-ups or exhibitions

### Proof and marks (6.4s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - Name and address of manufacturer/importer/packer<br>- Common/generic name of commodity (garment)<br>- Net quantity (number of pieces)<br>- Month and year of manufacture/pre-packing/import<br>- MRP inclusive of all taxes<br>- Consumer care contact details  
  *could not know:* Exact Legal Metrology (Packaged Commodities) Rules declarations required for apparel e-commerce listings vs physical pack; confirm whether care/wash labelling and fibre composition are treated as mandatory for your SKUs.
- **The worst public event** (`worst_case`, basis: context): A viral consumer complaint or regulator action over misleading labelling — wrong MRP, fibre composition, or country of origin — or a systemic fit/colour-accuracy failure driving mass returns and refund disputes. The consumer (via social media and the marketplace) and then the Legal Metrology department or a consumer forum/CCPA typically act first.

### Place, language and occasions (12.1s)

- **Place by place** (`place_notes`, basis: knowledge): state: Delhi · how_people_buy_use: Online-first with store visits to check fit; everyday wear plus festive/wedding buying · register: Hindi-English mix, brand-aware, value-conscious · festivals_seasons: Diwali, wedding season (winter), harsh summer drives light cotton demand · references: North Indian winter layering, metro commute wardrobes<br>state: West Bengal · how_people_buy_use: Online-first in Kolkata and tier-2; cotton valued for humid climate · register: Bengali-English mix, aesthetic and quality-conscious · festivals_seasons: Durga Puja is the dominant buying peak, Poila Boishakh, winter weddings · references: Durga Puja new-clothes tradition, Kolkata's humid summers  
  *could not know:* Loomwell's actual buyer behaviour differences between these two states; whether its store footprint is concentrated in Delhi or Kolkata
- **Language mix of the work** (`language_mix`, basis: knowledge): Use primarily English with natural Hindi-English code-mixing for Delhi; for West Bengal, English leading with light Bengali touches at festive moments. Keep voice-over clean English with regional warmth rather than heavy dialect.  
  *could not know:* Loomwell's current copy language and whether it localises per state
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: Durga Puja · when: Sep-Oct · where_it_matters: West Bengal<br>moment: Diwali / festive peak · when: Oct-Nov · where_it_matters: Delhi and both states<br>moment: Winter wedding season · when: Nov-Feb · where_it_matters: Delhi primarily, both states<br>moment: Poila Boishakh (Bengali New Year) · when: Mid-April · where_it_matters: West Bengal<br>moment: Summer cotton demand · when: Apr-Jun · where_it_matters: Both states, humid Kolkata and hot Delhi<br>moment: End-of-season sale windows · when: Jun-Jul and Dec-Jan · where_it_matters: Both states, online channel  
  *could not know:* Loomwell's own launch windows and sale calendar; whether it participates in marketplace sale events

### Look and sound (7.0s)

- **People and settings** (`people_setting`, basis: profile): Urban working Indians in their late 20s to 40s — salaried professionals, freelancers, small-business owners in Delhi and Kolkata — shown in lived-in flats, on the way to work, in cafes and on the commute, not at parties. Wardrobes and mirror moments at home, plus clean, well-lit own-stores where fit and fabric are inspected up close.
- **What it sounds like** (`sound_world`, basis: knowledge): Calm, unhurried and neutral Indian-English voice — the way an educated metro professional actually speaks, with natural Hindi or Bengali inflection, never a hard-sell retail tone. Music is understated and modern: soft acoustic or low-key contemporary beds, measured pace, room to show cloth and detail rather than hype.  
  *could not know:* Whether the brand wants English-led or Hindi/Bengali-led voice, and any existing sonic or tone-of-voice guidelines

**Dairy or Heritage words in this brand's drafts:** none

## Sthir Cement

*states added for this run: Bihar, West Bengal, Assam*

What it was given: Brand: Sthir Cement | Category: Cement — building materials (OPC and PPC, bagged trade cement) | Market: India, state-level markets weighted to semi-urban and rural; freight cost makes every market regional rather than national | Hero product: Sthir PPC 50kg | Positioning: Consistent strength, bag after bag, on the sites that cannot afford a bad batch | States it sells in: Bihar, West Bengal, Assam | Competitors: UltraTech, Ambuja, ACC, Shree, Dalmia, regional single-plant brands | Anything else: The defining category truth: THE DECIDER IS NOT THE BUYER. A mason, contractor or engineer recommends and the individual home builder pays — so influencer programmes (mason meets, loyalty, technical training) do the work that advertising does elsewhere. For the home builder it is a once-in-a-lifetime purchase; for the contractor it is continuous. Dealer and sub-dealer credit, not shelf space, is the channel constraint. Institutional and project sales are a separate business from trade cement.

### How the product is shown (12.1s)

- **How it is used or handled** (`product_in_use`, basis: knowledge): The bag is cut open and the grey powder is emptied into a pan or mixing spot, then mixed by hand or machine with sand, blue metal (aggregate) and water into a paste that is poured into shuttering, laid as mortar between bricks, or plastered onto walls with a trowel (karni). It is never used dry and never applied neat without sand and water.
- **What must be visible** (`must_show`, basis: knowledge): - the printed 50kg woven/laminated bag, grey with brand print<br>- wet grey concrete or mortar, not dry powder, on an active site<br>- masons in lungi/trousers with trowel, float or ghamela (pan)<br>- a half-built brick or RCC structure with exposed shuttering or rebar<br>- sack cut open and powder being tipped into the mix<br>- dust, cement stains on hands and clothes, rough unfinished surroundings
- **Is the pack in the picture** (`pack_in_scene`, basis: context): always
- **Kind of imagery** (`imagery_style`, basis: context): Site-realism: the finished pukka house as the end-dream, and the mason/contractor as hero of the trade-facing work, shot on real under-construction sites rather than studios. Strength and trust are signalled through structure (pillars, slabs, bonded brickwork) and the bag held or stacked, not through abstract lifestyle imagery.

### Who buys it and where it is met (10.6s)

- **Household or one person** (`buying_unit`, basis: profile): either
- **Product lines** (`lines`, basis: profile): line: Sthir PPC 50kg · who_uses: masons, contractors on home sites · who_decides_pays: mason/contractor recommends, home builder pays · how_bought: by the bag on credit from dealer/sub-dealer · where_sold: semi-urban and rural trade counters · how_used: plastering, slabs, general residential casting<br>line: Sthir OPC 50kg · who_uses: masons, contractors wanting early strength · who_decides_pays: engineer/contractor recommends, builder pays · how_bought: by the bag on credit from dealer/sub-dealer · where_sold: same trade counters, regional markets · how_used: structural concrete, columns, high-early-strength work<br>line: Institutional / project cement · who_uses: project contractors, engineers · who_decides_pays: procurement/engineer decides and pays · how_bought: bulk tender, direct supply, separate from trade · where_sold: project sites, direct from plant/depot · how_used: infrastructure and large builds  
  *could not know:* Whether Sthir actually sells OPC in bags in these states and what grades/SKUs beyond 50kg PPC exist
- **Routes to market** (`routes`, basis: profile): route: Dealer then sub-dealer on credit · who_buys_there: home builders and contractors buying by the bag<br>route: Direct project/institutional supply · who_buys_there: project contractors and procurement teams  
  *could not know:* Actual share split between trade and project sales
- **Where people meet the brand** (`meeting_points`, basis: context): - Dealer and sub-dealer cement counters<br>- Mason meets and loyalty events<br>- Technical training sessions for masons/engineers<br>- The home-construction site itself<br>- Project sites for institutional sales

### Proof and marks (6.6s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - ISI mark with IS 1489 (Part 1) for PPC<br>- ISI mark with IS 269 for OPC<br>- BIS CM/L licence number<br>- Grade (e.g. 43/53 for OPC)<br>- Week and year of packing<br>- Net weight 50kg / MRP  
  *could not know:* Exact licence numbers for Sthir's specific plant(s) and current IS code revisions; confirm which grades/types are actually sold per state.
- **The worst public event** (`worst_case`, basis: knowledge): A failed BIS conformity test or market sample showing the cement does not meet IS 1489/IS 269 strength or setting requirements, triggering stop-marking or licence suspension; BIS acts first, and state authorities or the dealer network react downstream.  
  *could not know:* Whether Sthir has any history of BIS non-conformance or structural-failure complaints on its sites.

### Place, language and occasions (19.4s)

- **Place by place** (`place_notes`, basis: knowledge): state: Bihar · how_people_buy_use: Individual home builder buys on mason/contractor advice; bought from local dealer/sub-dealer on credit, bag by bag as construction progresses · register: Hindi/Bhojpuri; strength talked about as 'majbooti' and bharosa · festivals_seasons: Construction peaks after monsoon into winter; slabs cast on auspicious days; Chhath and Diwali as milestones · references: Pucca ghar aspiration; the once-in-a-lifetime family home<br>state: West Bengal · how_people_buy_use: Mason (rajmistri) and contractor drive brand choice; home builder pays, dealer credit the key constraint; staged purchase through the build · register: Bengali; quality spoken of as consistency 'boshtobhabe' good, bag after bag · festivals_seasons: Durga Puja as the big calendar anchor; building slows in heavy monsoon, picks up in dry season · references: The family house, nijer bari, as life's big build<br>state: Assam · how_people_buy_use: Mason/contractor recommends, individual owner pays; dealer and sub-dealer network with credit; purchase spread across the build · register: Assamese; plain emphasis on reliable set and strength · festivals_seasons: Heavy, long monsoon shapes the pour calendar; Bihu as the main cultural marker · references: Building the family home as a once-in-a-lifetime event  
  *could not know:* Verified local mason/trade slang for cement quality in each state, region-specific auspicious-day casting customs, and safe local references the brand already uses
- **Language mix of the work** (`language_mix`, basis: knowledge): Lead in each state's main language — Hindi/Bhojpuri in Bihar, Bengali in West Bengal, Assamese in Assam — with simple technical terms (PPC, strength, grade) kept in familiar form. Voice-over should sound local and trade-fluent, not national-Hindi generic.  
  *could not know:* Whether the brand prefers standard Hindi over Bhojpuri in Bihar, and how much English technical vocabulary its mason audience actually uses
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: Post-monsoon building season · when: Roughly October onwards into winter · where_it_matters: Bihar, West Bengal, Assam — the main dry-season construction window<br>moment: Monsoon slowdown · when: June–September (longer in Assam) · where_it_matters: All three states; pours and slab work slow, affects offtake<br>moment: Durga Puja · when: Autumn · where_it_matters: West Bengal — major cultural anchor and spending period<br>moment: Chhath / Diwali · when: Autumn · where_it_matters: Bihar — milestone season tied to home and auspicious work<br>moment: Bihu · when: Spring (and other dates) · where_it_matters: Assam — main cultural marker  
  *could not know:* Exact auspicious casting dates the trade follows, any dealer/mason loyalty-scheme windows the brand runs, and launch windows specific to Sthir

### Look and sound (6.8s)

- **People and settings** (`people_setting`, basis: profile): Show the mason and contractor on a half-built single-family home — exposed brick, bamboo scaffolding, a slab being poured by hand — in semi-urban and rural Bihar, Bengal and Assam. Show the dealer counter with stacked bags, and mason meets where the trade gathers, not polished show-flats.
- **What it sounds like** (`sound_world`, basis: knowledge): Confident, grounded male voice in Bhojpuri, Bengali or Assamese depending on state, at an unhurried working pace — the tone of a trusted mistri, not a city announcer. Simple rhythmic music or on-site sound (trowel, mixing), nothing aspirational-glossy.  
  *could not know:* Whether the brand uses a single pan-region Hindi voice or localises per state, and any existing jingle or sonic signature.

**Dairy or Heritage words in this brand's drafts:** none

## Heritage Ice Cream (probe)

*owner's case: dairy, but ice cream can be family or individual. The profile does NOT say which.*

What it was given: Brand: Heritage Ice Cream (probe) | Category: Dairy — ice cream and frozen desserts | Market: India, South India | Hero product: Heritage Ice Cream | States it sells in: Telangana, Andhra Pradesh | Languages it can be written in (language codes): te, en | Regulator: FSSAI

### How the product is shown (9.9s)

- **How it is used or handled** (`product_in_use`, basis: knowledge): People eat it — scooped from a cup or tub with a spoon, licked off a cone or a kulfi/candy stick, or spooned over as part of a bowl or family dessert. It is never chewed hard or drunk, and it is eaten quickly before it melts in the South Indian heat.
- **What must be visible** (`must_show`, basis: knowledge): - soft scoop texture with slight melt or glossy surface, not frozen-solid blocks<br>- the format clearly: cup with flat wooden spoon, cone, matka/kulfi, or family tub<br>- real flavour cues — e.g. chunks, nuts, choco chips, fruit pieces<br>- condensation or a hint of melt signalling cold served in heat<br>- hands or a spoon mid-scoop for a 'being eaten now' feel  
  *could not know:* Which exact formats (cup, cone, kulfi, tub, bar) and signature flavours Heritage leads with
- **Is the pack in the picture** (`pack_in_scene`, basis: knowledge): only when it is in use
- **Kind of imagery** (`imagery_style`, basis: knowledge): Warm, appetite-led close-ups of the scoop or cone with rich flavour and texture, often with family or sharing moments. Bright, festive and value-friendly rather than premium-minimalist, with local warmth suited to Telangana/Andhra audiences.  
  *could not know:* Whether Heritage positions as everyday/family value or premium indulgence

### Who buys it and where it is met (12.0s)

- **Household or one person** (`buying_unit`, basis: knowledge): either
- **Product lines** (`lines`, basis: knowledge): line: Family packs / tubs · who_uses: whole household, guests · who_decides_pays: parents / head of household · how_bought: planned grocery or online grocery buy · where_sold: supermarkets, dairy parlours, quick-commerce · how_used: served as dessert at home after meals<br>line: Single-serve cups & kulfi · who_uses: one person, kids · who_decides_pays: the eater or parent · how_bought: impulse at counter · where_sold: parlours, kirana freezers, canteens · how_used: eaten on the spot<br>line: Cones & bars (sticks/candy) · who_uses: kids, youth · who_decides_pays: self or parent · how_bought: impulse from freezer · where_sold: kirana shops, roadside carts, parlours · how_used: eaten on the go<br>line: Party / bulk bricks & assorted packs · who_uses: families at functions · who_decides_pays: host / household · how_bought: planned bulk buy for occasions · where_sold: dairy parlours, distributors · how_used: served at celebrations and gatherings  
  *could not know:* exact Heritage SKU/line list
- **Routes to market** (`routes`, basis: knowledge): route: Heritage dairy parlours / brand outlets · who_buys_there: families, walk-in customers<br>route: Kirana shops & general stores with freezers · who_buys_there: impulse buyers, kids<br>route: Supermarkets / modern trade · who_buys_there: households stocking up<br>route: Quick-commerce & online grocery · who_buys_there: urban households, young buyers<br>route: Roadside carts / push-cart vendors · who_buys_there: on-the-go passersby, children  
  *could not know:* actual channel mix and shares for Heritage
- **Where people meet the brand** (`meeting_points`, basis: knowledge): - Heritage dairy parlours<br>- kirana shops with ice-cream freezers<br>- supermarkets and modern-trade freezers<br>- roadside ice-cream carts<br>- canteens and food courts

### Proof and marks (6.2s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - FSSAI logo with 14-digit licence number<br>- Green veg mark (brown non-veg mark if egg-containing)<br>- Net quantity in ml/g<br>- Best before / use by date<br>- List of ingredients and allowed additives (INS numbers)<br>- 'Frozen Dessert' declaration if made with vegetable fat, not 'Ice Cream'  
  *could not know:* Whether this hero line is true dairy ice cream or a frozen dessert (vegetable fat), which changes the mandatory product-name declaration.
- **The worst public event** (`worst_case`, basis: knowledge): A failed FSSAI test or consumer complaint — for example excess coliform/bacterial contamination, a non-permitted additive, or a foreign object — triggering a recall or product seizure. The state Food Safety department (Telangana/Andhra Pradesh Commissioner of Food Safety under FSSAI) acts first, lifting samples and issuing notices.

### Place, language and occasions (11.8s)

- **Place by place** (`place_notes`, basis: knowledge): state: Telangana · how_people_buy_use: Bought at local dairy parlours, kirana stores and Heritage outlets; family packs for home, cups/cones/bars on the go · register: Telugu with casual English; warm, everyday tone · festivals_seasons: Peak in summer (Mar–Jun); dessert for Ugadi, Bonalu, Bathukamma family gatherings · references: Hyderabad summers, family celebrations, after-dinner treat<br>state: Andhra Pradesh · how_people_buy_use: Bought at dairy parlours, kirana and supermarkets; family packs, tubs for home, single-serve for kids and travellers · register: Telugu-first, simple and familial · festivals_seasons: Peak in hot summer (Mar–Jun); Ugadi, Sankranti feasts and weddings · references: Coastal heat, Sankranti gatherings, shared family dessert  
  *could not know:* Actual channel split and how buyers describe specific flavours/formats locally
- **Language mix of the work** (`language_mix`, basis: profile): Lead in Telugu for warmth and reach, with light English for product names and modern formats. Voice-over primarily Telugu, English kept minimal.
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: Summer ice cream season · when: March–June · where_it_matters: Telangana and Andhra Pradesh<br>moment: Ugadi · when: March/April · where_it_matters: Telangana and Andhra Pradesh<br>moment: Sankranti · when: January · where_it_matters: Andhra Pradesh (and Telangana)<br>moment: Bathukamma / Bonalu · when: around Sep–Oct / Jul–Aug · where_it_matters: Telangana  
  *could not know:* Whether the brand runs specific launch windows, trade sales, or festival promotions on set dates

### Look and sound (6.4s)

- **People and settings** (`people_setting`, basis: knowledge): Middle-class Telugu families in Hyderabad, Vijayawada and smaller towns of Telangana and Andhra — kids and parents at home, at local parlours, and buying from neighbourhood kirana shops and bakeries with Heritage deep-freezers. Also roadside ice cream carts and family celebrations like birthdays and summer evenings.  
  *could not know:* Whether the brand skews to family tubs (home) versus impulse single sticks/cups (parlour/cart), which would change the setting emphasis.
- **What it sounds like** (`sound_world`, basis: knowledge): Warm, familiar Telugu voice with a local South Indian accent, friendly and unhurried; light, cheerful music suited to family and summer moods. Pace is relaxed and homely rather than fast or trendy.  
  *could not know:* Brand's actual tone preference (nostalgic/family vs youthful/fun) and whether ads run in te, en or both.

## Vigor Protein for men (probe)

*owner's case: a functional product bought by an individual man*

What it was given: Brand: Vigor Protein for men (probe) | Category: Functional nutrition — high-protein bars and shakes | Market: India, metros | Hero product: Vigor high-protein bar | Positioning: A high-protein bar for men who train | States it sells in: Delhi, West Bengal | Languages it can be written in (language codes): hi, en | Who decides: the man himself | Who pays: the man himself | Who uses it: the man himself

### How the product is shown (8.5s)

- **How it is used or handled** (`product_in_use`, basis: knowledge): The bar is unwrapped and eaten by hand, bitten into straight from the foil sleeve — typically around a workout. The shake is a powder scooped into a shaker or glass, mixed with water or milk, shaken and drunk; the bar is never cooked, sliced or spread.
- **What must be visible** (`must_show`, basis: knowledge): - dense bar with visible protein/nougat layer and a bite mark<br>- torn or peeled foil wrapper with the bar half out<br>- chocolate or coating cracked, not glossy-perfect<br>- shaker bottle or gym water bottle nearby<br>- a grip of a man's hand holding it mid-grab<br>- gym/training sweat, kit bag or weights in background
- **Is the pack in the picture** (`pack_in_scene`, basis: knowledge): always
- **Kind of imagery** (`imagery_style`, basis: knowledge): Gym-floor and post-workout realism — male athlete mid-training or catching breath, strong directional light, sweat and effort foregrounded with a hard masculine palette of blacks, greys and accent colour. Shots are energetic and body-focused (forearm, grip, torso), not soft lifestyle or kitchen settings.

### Who buys it and where it is met (9.3s)

- **Household or one person** (`buying_unit`, basis: profile): one person
- **Product lines** (`lines`, basis: profile): line: Vigor high-protein bar · who_uses: men who train · who_decides_pays: the man himself · how_bought: online subscription or single packs; gym counter · where_sold: e-commerce, quick-commerce, gym stores · how_used: pre/post-workout or as a snack on the go<br>line: Vigor high-protein shake · who_uses: men who train · who_decides_pays: the man himself · how_bought: tubs or RTD bottles online or at supplement stores · where_sold: e-commerce, supplement stores, gyms · how_used: mixed post-workout or as a meal replacement  
  *could not know:* Whether shake line actually exists or only bars; exact pack formats
- **Routes to market** (`routes`, basis: knowledge): route: D2C brand website · who_buys_there: loyal men ordering in bulk/subscription<br>route: E-commerce marketplaces (Amazon, Flipkart) · who_buys_there: men comparing protein brands<br>route: Quick-commerce (Blinkit, Zepto, Instamart) · who_buys_there: men wanting same-day single packs<br>route: Gym and supplement stores · who_buys_there: men buying at point of training  
  *could not know:* Actual channel mix and shares for this brand in Delhi and West Bengal
- **Where people meet the brand** (`meeting_points`, basis: knowledge): - gyms and fitness studios<br>- supplement/nutrition stores<br>- quick-commerce delivery<br>- modern-trade grocery shelves in metros  
  *could not know:* Which specific retail or gym partnerships exist in Delhi and West Bengal

### Proof and marks (5.5s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - FSSAI logo + 14-digit licence number<br>- Veg/Non-veg green/brown dot<br>- Nutritional Information panel (per 100g/serving, incl. protein)<br>- Ingredients list with allergen declaration<br>- Net quantity, MRP, mfg/expiry (Legal Metrology)<br>- Name & address of manufacturer/marketer (FBO)
- **The worst public event** (`worst_case`, basis: knowledge): A failed FSSAI test showing the bar's actual protein content is lower than the label claim (a misbranding/substandard finding), or a batch flagged for banned additives or contamination. FSSAI (or the state food safety department in Delhi/West Bengal) acts first, issuing notices, sampling and potential recall.

### Place, language and occasions (9.8s)

- **Place by place** (`place_notes`, basis: knowledge): state: Delhi · how_people_buy_use: Bought online (Amazon, HealthKart) and at gym counters; eaten post-workout or as a snack between meals · register: Hinglish gym talk — 'gains', 'protein intake', 'bulking' · festivals_seasons: New-year resolution season (Jan); pre-summer 'shredding' phase (Mar–May) · references: Gym culture, Delhi fitness influencers, cricket/gym routines<br>state: West Bengal  
  *could not know:* Solid West Bengal specifics for how protein bars are bought/used and spoken about in Kolkata gym culture; confirmation of Delhi buying habits and seasonal training cycles
- **Language mix of the work** (`language_mix`, basis: profile): Lead in Hinglish — English for product and training terms ('high-protein', 'post-workout'), Hindi for the emotional push. Keep pack and claims in clean English.  
  *could not know:* Whether West Bengal copy should lean more toward English or add Bengali-flavoured phrasing
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: New-year resolution season · when: January · where_it_matters: Delhi<br>moment: Pre-summer shredding phase · when: March–May · where_it_matters: Delhi  
  *could not know:* E-commerce sale windows (e.g. Great Indian/Big Billion days) relevance to this brand, and any West Bengal-specific moments for this category

### Look and sound (5.6s)

- **People and settings** (`people_setting`, basis: profile): Men in their 20s–30s training in neighbourhood gyms and home setups across Delhi and Kolkata, shown mid-workout or packing a bar into a gym bag. Settings are everyday urban metro flats, gym floors with weights, and local supplement counters rather than aspirational imported-studio looks.
- **What it sounds like** (`sound_world`, basis: knowledge): Driving, gym-floor beats with a confident, motivating male voice in Hindi or English, Delhi/Kolkata urban accent. Pace is brisk and punchy, matching a workout rhythm.  
  *could not know:* Whether the brand prefers a hard fitness-bro tone or a calmer, informed one; any music or voice references already in use.

**Dairy or Heritage words in this brand's drafts:** ['fssai', 'hinglish', 'milk']

## Vigor Protein for women (probe)

*owner's case: the same product bought by an individual woman. Compare with the men's probe.*

What it was given: Brand: Vigor Protein for women (probe) | Category: Functional nutrition — high-protein bars and shakes | Market: India, metros | Hero product: Vigor high-protein bar | Positioning: A high-protein bar for women who train | States it sells in: Delhi, West Bengal | Languages it can be written in (language codes): hi, en | Who decides: the woman herself | Who pays: the woman herself | Who uses it: the woman herself

### How the product is shown (7.9s)

- **How it is used or handled** (`product_in_use`, basis: knowledge): The bar is unwrapped and eaten by hand, bitten into like a snack bar — often around a workout. It is not cooked, melted, or mixed into anything.
- **What must be visible** (`must_show`, basis: knowledge): - dense chocolate/protein bar with visible chew and nut or crisp texture at the bite<br>- the wrapper peeled back, not a bare naked bar<br>- woman-sized hand holding it, mid-bite or just unwrapped<br>- gym or post-workout context cues (mat, towel, water bottle, activewear)<br>- protein/gram claim legible on the wrapper<br>- realistic bar scale — fits in the hand, not oversized  
  *could not know:* Actual wrapper design, colour and the exact protein claim on pack
- **Is the pack in the picture** (`pack_in_scene`, basis: knowledge): always
- **Kind of imagery** (`imagery_style`, basis: knowledge): Bright, high-energy fitness imagery: women in activewear training or cooling down, clean well-lit gym or home-workout settings with sweat-and-strength realism. Macro shots of the bar's texture at the bite sit alongside the active lifestyle frame.

### Who buys it and where it is met (9.8s)

- **Household or one person** (`buying_unit`, basis: profile): one person
- **Product lines** (`lines`, basis: profile): line: High-protein bar · who_uses: woman who trains · who_decides_pays: the woman herself · how_bought: online or at gym/retail, often by the box · where_sold: e-commerce, D2C site, gym counters, pharmacies · how_used: post-workout or on-the-go snack<br>line: Protein shake · who_uses: woman who trains · who_decides_pays: the woman herself · how_bought: online in tubs or sachets · where_sold: e-commerce, D2C site, gyms · how_used: mixed with water/milk post-workout  
  *could not know:* Whether the shake line actually exists; profile names bars and shakes in category but hero is the bar
- **Routes to market** (`routes`, basis: knowledge): route: D2C brand website · who_buys_there: women training, repeat subscribers<br>route: E-commerce marketplaces (Amazon, Flipkart, HealthKart) · who_buys_there: first-time and comparison buyers<br>route: Quick commerce (Blinkit, Zepto, Instamart) · who_buys_there: metro women wanting instant delivery<br>route: Gyms and fitness studios · who_buys_there: members buying at the counter<br>route: Pharmacies / health stores · who_buys_there: walk-in shoppers  
  *could not know:* Actual channel mix and which routes the brand uses; no shares stated in profile
- **Where people meet the brand** (`meeting_points`, basis: knowledge): - Gyms and fitness/CrossFit studios<br>- Yoga and Pilates studios<br>- Pharmacies and health-food stores<br>- Quick-commerce delivery (in-hand at home)<br>- Running/fitness community events in Delhi & Kolkata  
  *could not know:* Which physical points the brand is actually present in across Delhi and West Bengal

### Proof and marks (5.1s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - FSSAI logo and licence number<br>- Veg/Non-veg green/brown dot<br>- Nutritional information panel (per serve/100g, including protein)<br>- Net quantity declaration<br>- Name and address of manufacturer/marketer<br>- Best before / use by date and batch number
- **The worst public event** (`worst_case`, basis: knowledge): A failed lab test or complaint showing the bar contains less protein than claimed, banned substances, or contamination — triggering an FSSAI notice, recall, or misleading-claim action. FSSAI (and the state food safety commissioner in Delhi/West Bengal) acts first, often after a consumer complaint or routine sampling.

### Place, language and occasions (11.6s)

- **Place by place** (`place_notes`, basis: knowledge): state: Delhi · how_people_buy_use: Bought online (Amazon, brand site, quick-commerce) and at gym counters; eaten post-workout or as a mid-day snack · register: Hindi-English mix, gym and fitness slang; aspirational, direct · festivals_seasons: New-year resolution season (Jan), wedding-prep months, summer gym push · references: Gym culture, morning runs, metro commute snacking<br>state: West Bengal · how_people_buy_use: Bought online and in Kolkata gyms/health stores; used post-workout or as protein top-up · register: Bengali-English mix with Hindi/English acceptable; warmer, conversational · festivals_seasons: New-year resolution season (Jan); pre-Durga Puja fitness push · references: Kolkata fitness scene; health-conscious urban routine  
  *could not know:* Exact retail vs online split, local gym chains, and how Vigor is actually spoken about in each city
- **Language mix of the work** (`language_mix`, basis: profile): Primarily Hindi-English (Hinglish) for Delhi, confident and gym-literate; for West Bengal keep English-led with light Hindi, as Bengali copy isn't in the brand's listed languages.  
  *could not know:* Whether audience prefers more pure-Hindi or more English in each metro
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: New-year resolution / fitness push · when: January · where_it_matters: Delhi and West Bengal metros<br>moment: Summer gym/shred season · when: Apr–Jun · where_it_matters: Delhi<br>moment: Pre-Durga Puja fitness prep · when: Aug–Sep · where_it_matters: West Bengal<br>moment: Wedding-season prep · when: Oct–Dec · where_it_matters: Delhi  
  *could not know:* Whether the brand runs its own sale windows or launch dates to align with

### Look and sound (6.6s)

- **People and settings** (`people_setting`, basis: profile): Show urban Indian women in their 20s-30s mid- or post-workout — gym floors, strength-training corners, yoga/Pilates studios, and home after a session — in Delhi and Kolkata settings, bar grabbed from a gym bag or kitchen counter. Think everyday fit women who lift and train, not fitness models or clinical weight-loss before/afters.
- **What it sounds like** (`sound_world`, basis: knowledge): Upbeat, driving workout energy with a confident, warm female voice; natural urban Hinglish for Delhi and some English/Bangla warmth for Kolkata, spoken at a brisk, motivating pace. Encouraging and peer-like, not shouty or hyper-masculine supplement-ad tone.  
  *could not know:* Whether the brand wants a motivational/gym energy or a calmer wellness tone, and whether Bangla voice is in scope given the hi/en language set.

**Dairy or Heritage words in this brand's drafts:** ['fssai', 'hinglish', 'milk']

## Sthir Cement, family home build (probe)

*owner's case: cement as a family decision with a man leading*

What it was given: Brand: Sthir Cement, family home build (probe) | Category: Cement — building materials (OPC and PPC, bagged trade cement) | Market: India, semi-urban and rural | Hero product: Sthir PPC 50kg | States it sells in: Bihar, Assam | Languages it can be written in (language codes): hi, as, en | Regulator: BIS | Who decides: the man of the family, on the contractor's advice | Who pays: the family | Who uses it: the mason building the family's own house

### How the product is shown (8.4s)

- **How it is used or handled** (`product_in_use`, basis: knowledge): The mason mixes the bagged cement with sand, aggregate and water on-site, usually hand-mixed on the ground or in a pan, then it is used to lay bricks, plaster walls, or cast slabs and columns. It is never used dry straight from the bag, and never poured as a finished liquid product — it is always a wet mortar or concrete worked by hand or trowel.
- **What must be visible** (`must_show`, basis: knowledge): - the 50kg woven PPC bag with visible Sthir branding and BIS mark<br>- grey wet cement mortar on a trowel or being mixed<br>- a mason in ordinary work clothes, often barefoot or in sandals<br>- brick courses, plastering, or a slab/column being cast<br>- sand and aggregate heaps on a semi-urban/rural house site<br>- an unfinished family house (exposed brick, under-construction roof)
- **Is the pack in the picture** (`pack_in_scene`, basis: knowledge): always
- **Kind of imagery** (`imagery_style`, basis: knowledge): Warm, aspirational realism of a family building its own pucca house — strength, trust and the proud moment of a completed home, shot on real semi-urban/rural sites. Imagery leans on the bag itself, the mason at work, and the father/family looking on, often with claims of strength and durability.

### Who buys it and where it is met (8.8s)

- **Household or one person** (`buying_unit`, basis: profile): a household
- **Product lines** (`lines`, basis: profile): line: Sthir PPC 50kg · who_uses: mason building the family's own house · who_decides_pays: man of the family decides on contractor's advice; family pays · how_bought: by the bag at local dealer, often a few bags at a time as work progresses · where_sold: neighbourhood cement/building material dealer · how_used: mixed on site for plaster, slab, brickwork in slow self-build<br>line: Sthir OPC 50kg · who_uses: mason or contractor on faster/structural work · who_decides_pays: man of the family on contractor's advice; family pays · how_bought: by the bag at local dealer · where_sold: neighbourhood cement/building material dealer · how_used: structural concrete, columns, RCC where early strength wanted
- **Routes to market** (`routes`, basis: knowledge): route: local building-material / cement dealer (retail counter) · who_buys_there: families and their masons buying a few bags at a time<br>route: contractor-arranged supply from dealer · who_buys_there: family's contractor ordering on their behalf  
  *could not know:* actual share split between walk-in family purchase and contractor-routed orders in Bihar/Assam
- **Where people meet the brand** (`meeting_points`, basis: knowledge): - local cement/building-material dealer shop<br>- the house construction site<br>- dealer signage and wall paint in the bazaar<br>- hardware shops in semi-urban/rural market towns

### Proof and marks (5.6s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - ISI mark with IS 1489 (Part 1) for PPC<br>- BIS licence number (CM/L-...)<br>- Grade (e.g. PPC)<br>- Net weight 50 kg<br>- Week and year of packing<br>- MRP and manufacturer name/address  
  *could not know:* Exact BIS licence number for Sthir and whether MRP is printed on bag in these states
- **The worst public event** (`worst_case`, basis: knowledge): A BIS sample drawn from the market fails to meet IS 1489 (e.g. low compressive strength or short weight), leading to a stop on sale and possible licence suspension. BIS acts first, often after a dealer or consumer complaint, and can cancel the ISI licence.

### Place, language and occasions (12.3s)

- **Place by place** (`place_notes`, basis: knowledge): state: Bihar · how_people_buy_use: Bought bag-by-bag from local trade dealer, often on contractor's recommendation; self-build homes · register: Hindi with Bhojpuri/Maithili flavour; plain, trust-first talk about strength (mazbooti) · festivals_seasons: Construction peaks post-monsoon to winter (Oct-Mar); slab-pour avoided in heavy rains · references: Building own pucca ghar, griha pravesh, family saving for the house<br>state: Assam · how_people_buy_use: Bought in bags from local dealers; self-build family homes in semi-urban/rural areas · register: Assamese and Hindi; practical, respectful tone on durability against damp · festivals_seasons: Heavy monsoon shapes build timing; dry season preferred for casting; Bihu as a cultural anchor · references: Own house, humid/high-rainfall climate concerns  
  *could not know:* Confirm local dealer buying habits, brand-specific slogans, and which regional dialects to lead with per state
- **Language mix of the work** (`language_mix`, basis: profile): Lead in Hindi for Bihar and Assamese for Assam, with English only for technical terms like PPC, 50kg and BIS. Keep voice-over conversational and local, matching how masons and contractors actually speak on site.
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: Post-monsoon build season · when: Oct-Mar · where_it_matters: Bihar and Assam<br>moment: Monsoon (slow construction) · when: Jun-Sep · where_it_matters: Bihar and Assam, stronger in Assam<br>moment: Griha pravesh / auspicious house-start muhurat · when: Festive/auspicious dates · where_it_matters: Bihar  
  *could not know:* Exact local auspicious windows for starting construction, any dealer-scheme/discount periods, and Assam-specific house-build customs

### Look and sound (7.2s)

- **People and settings** (`people_setting`, basis: profile): Show a family's own under-construction house in semi-urban or rural Bihar/Assam — a half-built single or two-storey pucca home with exposed brick, bamboo scaffolding and a visible RCC slab being cast. Feature the mason (mistri) at work, the male head of the family inspecting with the contractor (thekedar), and the local cement/hardware dealer's shop where the bags are stacked.
- **What it sounds like** (`sound_world`, basis: knowledge): Grounded, trustworthy and reassuring — a male voice in Bhojpuri-inflected Hindi for Bihar or Assamese for Assam, speaking plainly at an unhurried pace, emphasising strength and the family home lasting generations. Music is simple and warm, not flashy, leaning on local/folk-tinged instrumentation rather than urban pop.  
  *could not know:* Whether the brand has an existing jingle, sonic signature or preferred tone (e.g. aspirational vs. purely functional).

**Dairy or Heritage words in this brand's drafts:** none

## Sthir Cement, trade buyer (probe)

*owner's case: cement bought by an individual, a contractor. Compare with the family case.*

What it was given: Brand: Sthir Cement, trade buyer (probe) | Category: Cement — building materials (OPC and PPC, bagged trade cement) | Market: India, semi-urban and rural | Hero product: Sthir PPC 50kg | States it sells in: Bihar, Assam | Languages it can be written in (language codes): hi, as, en | Regulator: BIS | Who decides: the contractor | Who pays: the contractor | Who uses it: the contractor's own crew

### How the product is shown (9.7s)

- **How it is used or handled** (`product_in_use`, basis: knowledge): The crew mixes the grey powder with sand, aggregate and water on-site — either in a drum mixer or hand-mixed on the ground with a spade (phawda) — then pours or lays the wet mortar/concrete for slabs, plaster, brickwork and foundations. The dry powder is never used as-is; it is always mixed with water and cured, never eaten or applied neat.
- **What must be visible** (`must_show`, basis: knowledge): - grey cement powder, not white<br>- the printed 50kg bag with BIS/ISI mark visible<br>- a mason/crew mixing on-site with phawda or mixer<br>- sand and aggregate heaps nearby<br>- wet grey slurry or plaster being laid<br>- a semi-urban/rural under-construction brick structure
- **Is the pack in the picture** (`pack_in_scene`, basis: knowledge): always
- **Kind of imagery** (`imagery_style`, basis: knowledge): Grounded on-site documentary imagery: masons and crews at work on a half-built house or slab, bags stacked at the dealer or site, with strength and trust (ghar, bharosa, mazbooti) as the emotional note. Clean hero shots of the bag with the BIS mark often anchor the frame.

### Who buys it and where it is met (11.1s)

- **Household or one person** (`buying_unit`, basis: knowledge): either  
  *could not know:* Whether bagged cement here is more often bought for a single home build or project; it varies by buyer (self-builder household vs contractor)
- **Product lines** (`lines`, basis: profile): line: Sthir PPC 50kg · who_uses: contractor's masons and crew · who_decides_pays: the contractor · how_bought: by the bag, often tens of bags per site · where_sold: local cement/building-material dealer · how_used: plaster, brickwork, slab casting in semi-urban/rural homes<br>line: Sthir OPC 50kg · who_uses: contractor's crew, also for RCC work · who_decides_pays: the contractor · how_bought: by the bag from dealer or stockist · where_sold: local cement dealer · how_used: higher-strength RCC, columns, early-strength work  
  *could not know:* OPC grade split (43 vs 53) and whether both grades are actively pushed in Bihar/Assam
- **Routes to market** (`routes`, basis: knowledge): route: local building-material dealer / counter · who_buys_there: contractors buying by the bag for sites<br>route: stockist / distributor to dealer · who_buys_there: dealers restocking; large contractors buying bulk<br>route: direct from company to large sites/projects · who_buys_there: bigger contractors for volume orders  
  *could not know:* Actual route mix for Sthir in Bihar and Assam, and whether direct-to-site exists at this scale
- **Where people meet the brand** (`meeting_points`, basis: knowledge): - local cement/building-material dealer shop<br>- dealer godown / stockyard<br>- construction site where crew lays cement<br>- hardware and sariya (steel) bazaar clusters  
  *could not know:* Brand-specific presence like painted dealer boards or site boards in Bihar/Assam

### Proof and marks (4.8s)

- **Marks and declarations** (`statutory_marks`, basis: knowledge): - ISI mark with IS 1489 (Part 1) for PPC<br>- BIS licence number (CM/L)<br>- Grade/type (PPC)<br>- Net weight 50 kg<br>- Month and year of packing<br>- MRP and manufacturer details
- **The worst public event** (`worst_case`, basis: knowledge): A failed BIS conformity test or market sample showing the cement does not meet IS 1489 strength/fineness, or site complaints of weak set and cracking on a build, leading to a stop-sale or licence suspension. BIS acts first, usually followed by the dealer/distributor pulling stock.

### Place, language and occasions (14.2s)

- **Place by place** (`place_notes`, basis: knowledge): state: Bihar · how_people_buy_use: Bought bag-by-bag at local dealer/kirana-style counters; contractor picks brand, mason mixes on site for RCC and plaster · register: Hindi with Bhojpuri/Maithili flavour; talk of strength, setting, bori rate · festivals_seasons: Construction peaks post-monsoon and winter; slows in heavy rains; Chhath and Diwali as cash/spending windows · references: Ghar banana, pucca makaan, mazboot nींv; local dealer trust<br>state: Assam · how_people_buy_use: Bought in bags from town dealers; used for homes and plinth work; damp climate makes storage and setting a concern · register: Assamese and Hindi; emphasis on resistance to moisture/humidity · festivals_seasons: Long monsoon slows work; dry months are build season; Bihu as key cultural/spending moment · references: Ghor sopa, strong foundation against rain-heavy climate  
  *could not know:* On-the-ground buying patterns, dealer behaviour, and how contractors in each state specifically talk about PPC vs OPC
- **Language mix of the work** (`language_mix`, basis: profile): Lead in Hindi for Bihar and in Assamese for Assam, kept simple and site-practical; use English only for technical terms like PPC, 50kg, BIS/grade. Voice-over should sound like a trusted local dealer or experienced mason, not corporate.
- **Calendar moments** (`calendar_moments`, basis: knowledge): moment: Post-monsoon build season · when: October–March · where_it_matters: Bihar and Assam (main construction window)<br>moment: Monsoon slowdown · when: June–September · where_it_matters: Bihar and Assam (work and sales dip, heavier in Assam)<br>moment: Chhath/Diwali spending window · when: October–November · where_it_matters: Bihar (cash availability, home work)<br>moment: Bihu · when: April (Bohag Bihu) · where_it_matters: Assam (cultural and spending moment)  
  *could not know:* Whether the brand or dealers run specific trade sales/launch windows or scheme periods

### Look and sound (7.1s)

- **People and settings** (`people_setting`, basis: profile): Show the mason-contractor (thekedar/mistri) and his small crew on a semi-urban or rural site — a half-built single-storey brick house, a boundary wall or a local shop under construction in Bihar or Assam. Also the trade counter: the cement dealer's godown with stacked 50kg bags, where the contractor loads sacks onto a cycle, cart or small tempo.
- **What it sounds like** (`sound_world`, basis: knowledge): Grounded, no-nonsense male voice in Bhojpuri/Hindi or Assamese, speaking plainly about strength (mazbooti), setting and value-for-money rather than aspiration. Steady, confident pace with simple local rhythm, not slick urban ad music.  
  *could not know:* Whether the brand prefers a particular regional dialect emphasis (Bhojpuri vs standard Hindi in Bihar) or a specific tagline/jingle style.

**Dairy or Heritage words in this brand's drafts:** ['kirana']


---

## Addendum: what the run exposed, and what was changed (9 Oct)

Reading the 135 drafts above against the profiles found four faults in the prompt and the cleaning code. Each was fixed and
four brands (Heritage Foods, Kumkum Beauty, Vigor for men, Sthir trade buyer) were re-run for real, 20 more calls.

| Fault in the first run | Fix | Re-run result |
|---|---|---|
| Drafts labelled `context` when nothing had been pasted (10 of them) | `context` with no pasted context is read as `knowledge` (unconfirmed) | 0 labelled `context` |
| A specific stated in the value while also listed under "could not know" (Heritage: a blue-and-white pouch) | Prompt rule: leave an unsure specific out of the value | The pouch colour is gone. One case remains: Heritage parlours are still in the meeting points while the note says it does not know |
| Coined or garbled local words (a Devanagari glyph inside a Latin word; romanised Bengali and Assamese phrases that may not exist) | Prompt rule: no local words unless certain | None in the Sthir trade re-run (one brand re-run, so a small sample) |
| Rows that name a state and say nothing | Dropped in code | Not seen |
| (found in the re-run) Two rows for one state, one of them describing another state (Sthir trade: two "Assam" rows, Bihar missing) | Both rows are withheld and the conflict is stated | Covered by a test; not reproduced in a real call |

Not fixed, and for you to judge:
- **The model never leaves a value empty.** 135 of 135 questions drafted in the first run, and again in the re-run. It says what it could not know in a note, but still writes an answer. Every draft therefore has to be read, not trusted.
- **`profile` as a basis is generous.** Several "profile" drafts are inferences (Kumkum's "urban women in their 20s-30s" is not in the profile).
- **`buying_unit` has no option for a trade or business buyer.** For the cement contractor probe it answered "either" with a note, which is defensible but is not the "individual man" case. A fourth option ("a business or trade buyer") is a question-design change for you.
- **Craft rules learnt from past failures are not in the model's drafts**: the visible-milk-in-the-glass rule, the oversized-pack rule and "pack only when in use" came from real failures in this studio. Heritage's reviewed answers carry them; a new brand starts without them.
