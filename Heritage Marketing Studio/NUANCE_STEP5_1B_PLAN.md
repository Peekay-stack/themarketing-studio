# Step 5, sub-step 1b: the pack-detection decision reads the brand's pack answer. Plan (12 Oct, branch `step5-1b`)

Status: built on a branch, **tested on localhost, NOT pushed to live** — the owner asked to test locally first, and this is the one change that alters *which* scenes get a real pack photo attached.

## The sweep: where "attach a real pack photo" is decided
| Site | What it decides | Dairy-specific tokens | Brand answer available? |
|---|---|---|---|
| `main.py` `scene_still` `want_pack` auto-block (~1820) | **THE decision**: auto-attach the signed-off pack photo to this image (Social, Carousel slides, Video frames — all go through `/scene-still`) | `glass of milk`, `milk bags`, `bags of milk` | yes — `brandprofile.resolve()` is read 20 lines below |
| `packscene._POUR_OR_OPEN` / `video_pack_in_use` | pack-in-ACTION wording, only *after* a pack is already attached (`if pack_used and …`) | `streams of milk`, `milk bags` | downstream of the decision |
| `packscene._PACK_NOUN` (colour-scrub) | strips colour words next to a pack noun | `milk bags`, `bags of milk` | n/a (text cleanup) |
| `posm.looks_like_pack` / `_PACK_WORDS` | POSM hero-vs-pack detection | **none — already generic** | n/a |
| page regexes (app.dc.html 15620 `PACK`, 15911 `PACK_RE`, 23207) | fallback `shows_pack` for a carousel slide when the model didn't set it | `milk bags`, `bags of milk` | the model sets `shows_pack` in the concept, which already carries `pack_in_scene` |

## The key realisation (why the simple "broaden the nouns" fix was deferred)
The dairy tokens are **not a cross-brand leak** — `milk bags`/`glass of milk` simply never match a cement or apparel scene, so they do no harm to other brands; removing them would *regress Heritage* (a "bag of milk" scene would stop attaching the pack). The deferral note's real worry was the opposite: *broadening* the nouns (add `tub`, `jar`, `bag`) would make Heritage's one signed-off pack — the **milk pouch** — attach to a **curd-tub** or **ghee-jar** scene (Heritage has many products, one pack photo). So broadening is wrong, and removing is wrong.

Meanwhile the brand already answers `pack_in_scene` ("always" / "only when it is in use" / "rarely" / "not a packed product"), and `voice_block` already renders it to the model as `PACK IN THE PICTURE: …`. The **attachment decision ignores it.** That is the real brand-agnostic gap.

## The change (one backend edit) + one page cleanup
1. **`scene_still` auto-attach respects `pack_in_scene`.** In the auto case (`include_pack` unset, no explicit `pack_id`), read the active brand's `pack_in_scene`:
   - **"not a packed product"** → `want_pack = False`. A brand with no pack never gets one auto-attached, even when a scene happens to say "label"/"bottle"/"pour". This is the one clearly-wrong behaviour today, and the fix is pure protection.
   - any other value (**"always"**, **"only when it is in use"**, **"rarely"**, unset) → the existing noun heuristic, unchanged. (An explicit `pack_id` or `include_pack:true` still forces attach, as today; `pack_mode:"auto"` still widens the vocabulary.)
   - This reads the brand's own answer at the decision point, adds **no new nouns** (so the curd-tub mis-attach stays avoided), and does **not** change Heritage (which is "only when it is in use").
   - Deliberately NOT forcing `want_pack=True` for "always": across a 15-frame Video that would crowd the 3-reference budget (cast+plate+pack); the model already gets "the pack is part of the picture; show it" from `voice_block`. Left as a possible follow-up.
2. **Remove the draft-button caveat note** (`bfSuggestLine`, app.dc.html ~23816). It said "Until the studio's built-in dairy rules are removed from its prompts…". After Surfaces 1–7 the prompt-level dairy rules ARE removed, so a non-dairy brand's accepted answers now work cleanly and the caveat is stale.

## What I will NOT touch
The dairy tokens in `scene_still` / `packscene` / the page regexes (harmless to other brands, load-bearing for Heritage), `packscene.video_pack_in_use` and the colour-scrub (downstream / text cleanup), `posm._PACK_WORDS` (already generic), and the noun heuristic itself. No new nouns anywhere.

## Forward & backward wiring
- **Backward (into `scene_still`):** `brandprofile.resolve()` already supplies the active brand (read 20 lines below the want_pack block); I read `pack_in_scene` from it. In General mode the pack is stripped regardless, so no leak. No new inputs.
- **Forward (out of `scene_still`):** the return shape is unchanged (`want_pack` only flips to False for a no-pack brand). The `pack_used`/`pack_source`/`pack_failed` fields the page reads are unchanged in shape. Carousel/Social/Video all call `/scene-still`; none of their payload contracts change.
- **The page caveat** is a display string with no consumer.

## Local verification (this is the gate before any live push)
- `golden_prompts --compare`: 0 changed (scene_still is a route, not a prompt-builder; the caveat is a page string).
- New targeted test: `/scene-still` for a **"not a packed product"** brand with a signed-off pack present and a scene that says "pack"/"bottle" → `pack_used:false` (no attach); the same brand with an explicit `pack_id` → still attaches; a normal brand ("only when in use") → unchanged (attaches on a pack scene); Heritage → unchanged.
- Existing: `test_pack_choice`, `test_pack_wording`, `test_carousel_concept`, `test_nuance_heritage_checklist`, the whole suite; `selfcheck`, `smoke`, `checkfe`, `partials verify`; tenant compare.
- Real page: the suggestion panel no longer shows the dairy caveat; a POSM/Carousel draft still works.
- **Not coverable without a model: a real render.** This changes attachment, so one real check (a Heritage carousel still attaches its pack; a hypothetical no-pack brand gets none) is worth doing on live after the owner approves.

## Rollback
Revert the commit. No data changes.
