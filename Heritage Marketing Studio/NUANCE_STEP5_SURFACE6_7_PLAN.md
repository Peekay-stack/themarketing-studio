# Step 5, Surfaces 6 (page strings) & 7 (seeded profile). Built 12 Oct

Status: **built and verified locally, shipping to master.** These are the page/data surfaces, not prompts, so the golden baseline is unchanged (0 of 75). app.dc.html stayed LF-only.

## Surface 6: page strings (app.dc.html)
The real bug here: **download filenames hardcoded "Heritage"**, so any other brand's film/brief/bible downloaded as `Heritage_...`. Fixed by a new `brandFile()` helper (the active brand name, file-safe, falling back to "Brand") used at every download site, and brand-driven title fallbacks.

| Change | Before | After |
|---|---|---|
| new helper | — | `brandFile(){ return (brandName()||'').replace(/[^a-z0-9]+/gi,'_')… \|\| 'Brand'; }` |
| production-bible download | `'Heritage'+(pbProj…)+'_Production_Bible_'` | `this.brandFile()+…` |
| production-bible title | `: 'Heritage Film')` | `: (brandName()? brandName()+' Film':'Film'))` |
| film-script download | `'Heritage'+(scProj…)+'_Film_Script_'` | `this.brandFile()+…` |
| film-script titles | `'Heritage Film'`, `'Heritage Film Script'` | brand-driven, `'Film'`/`'Film Script'` fallback |
| brief download | `'Heritage_Brief_'+…`, `'Heritage_Brief'`, `'Heritage Brief'` | `this.brandFile()+'_Brief…'`, brand-driven fallbacks |
| produced mp4 download | `'Heritage_Film_'+today` | `this.brandFile()+'_Film_'+today` |
| socialGrounding empty state | "could be any **dairy** brand in the category" | "could be any brand in the category" |
| two product placeholders | "e.g. Heritage Nourish+ Milk 500 ml" | "e.g. a 500 ml pack of your product" |
| sample cohort labels (COHORTS demo panel) | "Dairy & Groceries", "Repeat dairy buyers", "dairy basket", "dairy + baby SKUs", "Premium dairy + health SKU" | "Groceries", "Repeat grocery buyers", "grocery basket", "grocery + baby SKUs", "Premium grocery + health SKU" |

Left (deliberate): the draft-button caveat note (`bfSuggestLine`, "Until the studio's built-in dairy rules are removed…") stays until sub-step 1b (the pack-detection regexes) is done, which is when Step 5 is actually complete. Comments mentioning Heritage/dairy are developer-facing and left.

## Surface 7: the seeded profile (brandprofile.py)
A NEW tenant's first profile was a full **Heritage Foods** profile (category, hero product, master idea, codes, competitors, colours). Replaced `SEED` with a neutral placeholder `{"name": "Your brand"}`, still seeded active so `resolve()` and the switcher invariant hold, but a fresh tenant now starts with an empty brand to fill in, not someone else's. **No effect on any existing tenant:** `seed()` only runs when a tenant has zero profiles, and live `default` already has its brands saved (`seed()` returns None there). `SEED` is referenced only by `seed()`.

## Verification
- `golden_prompts --compare golden_step5`: 0 of 75 changed (page/data, not prompts).
- Fresh-tenant test: `seed()` on an empty tenant yields an active "Your brand" with empty category and no Heritage/dairy; a second call is a no-op.
- `tools/test_surfaces_wiring.py` extended: the page has no hardcoded-'Heritage' download names or dairy sample labels, uses `brandFile()`, socialGrounding is de-dairied; `brandprofile.SEED` names no category/codes/competitors.
- Real page: `brandFile()` → "Sthir_Cement_Co" for a cement brand, "Brand" with none; socialGrounding empty state says "any brand in the category". No console errors.
- `checkfe`, `partials verify` (LF-only, byte-identical round trip), all 25 tools tests, pytest (53), `selfcheck`, `smoke` all pass.
- Not coverable without a login: a real download on live (the filename is built client-side; verified by driving the real page).

## Rollback
Revert the commit. No data changes (SEED only affects a tenant that has no profiles yet).
