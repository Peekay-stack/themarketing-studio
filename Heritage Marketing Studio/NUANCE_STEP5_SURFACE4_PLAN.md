# Step 5, Surface 4: POSM. Plan for approval (12 Oct)

Status: **built and verified locally, SHIPPED to master (12 Oct), approved by the owner ("go with your recommendation").** Decision 1 taken: Option A, the dormant `/posm-spec` skill path left as-is (dairy-illustrated, not reached by the live page; revisit only if it is ever wired in). Decision 2: `statutory_marks` is a nuance answer the owner can accept on live at leisure; not a blocker, because no food marks are hardcoded on the live path. The only code change: `producers.key_visual`'s opener "Indian FMCG retail" -> "Indian retail" and "Indian FMCG point-of-sale" -> "Indian retail point-of-sale" (two model-visible lines; the two other "Indian FMCG" occurrences in main.py and posm.py are docstrings, left). Golden: only the `posm` surface changed, all 5 brands, only those two lines; `tools/golden_step5` re-saved. `tools/test_surfaces_wiring.py` extended with a POSM section (opener says 'Indian retail' not 'FMCG'; Heritage's marks+routes answers reach the prompt; a cement brand's POSM prompt has no dairy; `/posm-mandatories` returns the brand's own). No real POS render was generated.

## Headline: POSM is mostly already brand-agnostic
The POSM path the page actually drives is already answer-driven. This surface is small, and most of it is verify-not-change. The dairy-heavy material that remains sits in a **skill path the live page never calls**.

## How POSM reaches the model (traced)
Two drafting paths exist; only the first is live from the page:
- **`producers.key_visual`** (route `/posm-keyvisual`, the live key-visual drafter). Prompt = an inline opener + `_ctx()` (the brand block, `brandprofile.voice_block(profile)` at default/creative scope). **No skill files.**
- **`posm.draft`** (route `/posm-spec`). This one loads `_skill_instructions()` = `SKILL.md` + four reference files (`key-visual.md`, `failures.md`, `adaptation.md`, `exhibits.md`). **The page has no call to `/posm-spec`** — it calls `/posm-keyvisual`, `/posm-mandatories`, `/posm-adapt`, `/posm-image`, `/posm-backdrop`, `/posm-scene`, `/posm-assemble`, `/posm-scamps`, `/posm-typeset`, `/posm-artwork`, `/posm-print`, `/posm-palette`, `/posm-formats`. So the four dairy-heavy reference files are **dormant** from the live flow.
- `/posm-adapt`, `/posm-formats`, `/posm-mandatories` are pure computation or a straight profile read — no model text.

## What is already answer-driven (verify, do not touch)
- **The mandatory band.** `/posm-mandatories` reads `prof.get("mandatories")` (Heritage's live profile: `FSSAI mark`, `the line 'Pure Doodh Ki Shakti'`). Separately, the key-visual prompt carries the brand's `statutory_marks` answer through `voice_block` → `MARKS AND DECLARATIONS THAT MUST APPEAR ON PACK AND IN PRINT` (Heritage's answer: veg mark, FSSAI mark, FSSAI licence number). A cement brand with BIS/ISI marks answered would get those instead. **No hardcoded food marks reach the live prompt.**
- **The retail formats / routes.** The brand's `routes` answer renders as `ROUTES TO MARKET: ... Do not write for a route that is not on this list.` `posm.FORMATS` / `KIT_PRESETS` (kirana, chiller-led dairy, modern trade) are a format **catalogue** the person picks from, computed by `/posm-adapt`; they are options, not prompt text asserting a category. Heritage's `routes` and `meeting_points` answers are already saved on live.

## A. Model-visible on the LIVE path, category-shaped
| # | Where | What it says | Verdict |
|---|---|---|---|
| 1 | `producers.key_visual` opener (producers.py ~561): "art-directing point-of-sale material for **Indian FMCG** retail ... **Indian FMCG** point-of-sale is flat-colour graphic design with cut-out photographic elements ... The pack is always present and never the hero." | This is genuine **Indian-retail POS craft**, true for any product category sold through Indian retail, not dairy. "Indian" = the country (keep, India-only decision). "FMCG" slightly narrows it — a cement dealer board or an apparel store POS is retail POS but not "fast-moving consumer goods". | **Small**: generalise "FMCG" → "retail", keep everything else including "Indian". Not dairy leakage. |

That is the whole live-path category exposure. There is no dairy word in `producers.key_visual`.

## B. Dormant (the `/posm-spec` skill path — not called by the page)
The four reference files are dairy/Heritage-heavy but reach the model only through `posm.draft`, which nothing in the page calls:
- `failures.md` — entirely real Heritage Pure Milk failure renders (filenames, "PURE DOODH A YDG LTD", brass-vs-steel milk). The *lessons* (hallucinated brand mark, clipped pack, no mandatory zone) are generic; the *evidence* is real dairy screenshots that cannot be "swapped to another category".
- `exhibits.md` — 13 real FMCG pieces across honey, shampoo, detergent, skin cream and dairy. This is a **deliberate cross-category craft library** (the cross-category-format-study lesson says this is the *right* design); 4 of 13 are Mother Dairy, so it leans dairy but is not dairy-only.
- `adaptation.md` — a "Pure milk is where strength begins" worked example + a food mandatory line.
- `key-visual.md` — the white-key compositing rule illustrated with milk ("in dairy half the subjects are white: milk, a glass of it"); the rule is generic, the illustration is dairy.
- `SKILL.md` — layer 9 "Veg mark, FSSAI, licence number" named as the default mandatory example; "Indian FMCG ... flat-colour graphic design" opener (same as A1).

## Proposed change (one small commit) + one decision
1. **`producers.key_visual` opener:** "Indian FMCG retail" → "Indian retail"; "Indian FMCG point-of-sale" → "Indian retail point-of-sale". Keep the composition truth and "Indian" verbatim. This is the only dairy/category-narrowing text on the live path.
2. **Decision for you — the dormant skill path (`failures.md`, `exhibits.md`, `adaptation.md`, `key-visual.md`, `SKILL.md` mandatory example):**
   - **Option A (recommended): leave it as-is.** It is not reached by the live page, so it changes no live output. Removing the dairy worked examples would cost real craft evidence (the failures are genuine Heritage renders; the exhibits are a deliberate cross-category reference). Note it in the plan as "dormant, dairy-illustrated, intentionally kept" and revisit only if `/posm-spec` is ever wired into the page.
   - **Option B: neutralise the prose** (swap the `adaptation.md` worked example and the SKILL.md mandatory example to a non-food category; reword the `key-visual.md` white-key illustration to not say "dairy"; leave `exhibits.md` and the real `failures.md` screenshots as the cross-category reference they are). More consistent, future-proofs `/posm-spec`, but touches craft text for no live effect and risks the "gutting the SKILL.md" mistake the lesson warns about.

## What I will NOT touch
`voice_block`, `_ctx`, the mandatory/marks flow (already answer-driven), `posm.FORMATS`/`KIT_PRESETS` (a picked catalogue), the white-key compositing *logic*, the pack-detection vocabulary (`_PACK_WORDS`, sub-step 1b), `exhibits.md` and the real failure screenshots, and any stored Heritage data.

## Verification
- `tools/golden_prompts.py --compare golden_step5`: the `posm` surface it captures (via `producers.key_visual`) should change only by "Indian FMCG" → "Indian retail" for all five brands; everything else 0. I will read the diff.
- Extend `tools/test_surfaces_wiring.py` (or a small new test): `/posm-keyvisual` for a cement, beauty, apparel and biscuit brand carries no dairy word and no "FMCG"; Heritage's `statutory_marks` (marks line) and `routes` (routes line) appear in its POSM prompt; `/posm-mandatories` returns the brand's own mandatories. If Option B, add a dormant-path check that the skill prose carries no food mandatory for a non-food brand.
- Existing: `test_nuance_heritage_checklist` (the POSM checklist rows), `test_pack_choice`, `test_pack_wording`, `selfcheck`, `smoke`, `checkfe`, `partials verify`, tenant compare.
- Real page: open POSM, confirm a key-visual draft and the mandatories list for the active brand.
- Live: push, `/selfcheck` commit match, log scan. **Not coverable without a model:** real POS renders — one real Heritage POS check by the owner after deploy.

## Rollback
Revert the commit. No data changes.

## Decisions I need from you
1. **Dormant skill path: Option A (leave it, recommended) or Option B (neutralise the prose)?**
2. **Heritage's `statutory_marks` answer** — is it accepted on the live profile? (The live mandatory band already works off the older `mandatories` field; `statutory_marks` is the newer nuance answer that feeds the "MARKS AND DECLARATIONS" line. Not a blocker for this commit, since no dairy marks are hardcoded, but worth confirming it is saved so Heritage's POS carries veg mark + licence number, not only FSSAI.)
