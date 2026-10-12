# Step 5, Surface 3: Video (clip, still, animation and music prompts, and the page's Video defaults). Plan for approval (12 Oct)

Status: **built and verified locally on branch `step5-surface3` (12 Oct), approved by the owner ("go with your recommendation" on all four decisions), NOT yet on master or live.** Held on a branch because the plan's own gate is open: Heritage's `imagery_style` answer is still pending on the live profile, and only the owner can accept it there. Decisions taken: keep "Indian" as the country; music = Option A (the brand's sound-world answer is passed into the music prompt); voice field starts empty; imagery_style to be accepted before the merge. Built as planned, plus three things found while building: (1) an EMPTY voice field made the narrator pool answer male (`filmvoice._band('')` is `male_adult`), flipping every brand's default narrator, so `_voice_setup` now asks for "warm female voice" when the field is empty (same narrator as the old default string; test pins it); (2) the voice default was set in TWO places in the page (initial state and the reset when the film objective changes), both changed; (3) 'premium' also sat in the vector, 3D and watercolour style strings, removed with the rest. Side effect to know: an empty voice field sends no language code (the old default string sent 'en'), so the VO language is auto-detected. Golden compare: 0 of 75 changed (these strings are outside what it captures); new test `tools/test_video_agnostic_defaults.py` (checked to fire on the old code). Swept with the wide keyword list from the 12 Oct lessons (purity, premium, wholesome, mother, family, farmer, Hinglish, Indian, Telugu, kurta, saree ...), and read hardcoded strings in the page, not only prompts.

## The key fact: Heritage's saved answers already say what the hardcodes say
The Video script prompt already carries every answered question (`brandPreamble(..., film=true)` keeps the full nuance set). Heritage's saved answers (seed, accepted on live) say:
- `people_setting`: "An authentic family setting: a family in a warm home, a mother and children at the table, shopkeepers at a neighbourhood shop, real locations in natural light, premium and wholesome."
- `sound_world`: "Warm, wholesome and uplifting. Gentle instrumentation (warm strings, a solo bansuri flute over a soft tanpura drone, light tabla), no vocals and no lyrics. A warm female voice, Telugu-accented English by default."
- `language_mix`: "Each market in its own principal language (Telugu in Telangana and Andhra Pradesh, Kannada in Karnataka, Tamil in Tamil Nadu, Marathi in Maharashtra, Hindi in Delhi and Haryana), with English for product and pack terms."
- `imagery_style`: **still pending on live** (the owner has not accepted it): photorealistic food and lifestyle photography, DSLR look, warm natural light; illustration with a warm storybook or folk-art feel.
So for Heritage most of what is hardcoded below is a duplicate of its own answers, and in one place a **contradiction**: the script prompt says "Dialogue in English + Hinglish where natural" while Heritage's own language mix says each market in its own language.

## A. Model-visible, category- or language-specific
| # | Where | What it says | Reaches |
|---|---|---|---|
| 1 | `main.py` 1294, the Video clip prompt | "Authentic Indian family setting, warm natural light, premium and wholesome" | every clip of every film, every brand |
| 2 | `main.py` `_IMG_STYLES["real"]` 1539-1544 | "professional commercial **food** & lifestyle photography ... condensation on **fresh milk**. Authentic contemporary Indian home, kitchen, or **dawn dairy-farm** setting with real people" | `/scene-still` and `/image` (1641, 1759): **Video stills, Social and Carousel images** (POSM and Onground deliberately do not use it) |
| 3 | `_IMG_STYLES["product"]` 1546-1547, `_VID_STYLES["product"]` 1572 | "appetising and premium"; "macro pack and **pouring** shots" | same, product style |
| 4 | `filmaudio.music_prompt` 103-104 | every music prompt ends "Instrumental score for a **premium Indian dairy brand** film — warm, wholesome, uplifting, **gentle Indian instrumentation**" (also on top of a piano, orchestral or modern-pop pick) | every music bed, every brand |
| 5 | Page defaults: `production.voice` 11732 = "Warm female (**Telugu-accented** English)"; script prompt 15466 (and the provocation rewrite 15488-15489) "Dialogue in English + **Hinglish** where natural" | the default voice request and the spoken language for every film | every brand |
| 6 | Page placeholders: 2746 ("warm Indian mother, late 20s ... mustard kurta; daughter ... grandmother in a white saree"), 2671 ("add a farm beat", "make the VO Hinglish") | example text in empty boxes (not sent) | the Video screen |

## B. Looked at and kept on purpose
- **"Indian" as the country.** The owner's standing decision is India only, with a key for a second market, so `accent = INDIAN` as the default voice pool, `_VID_STYLES` / `_IMG_STYLES` "warm Indian storybook feel" and "folk-art sensibility" (illustration presets), and "Indian" meaning the place stay. What goes is the **category** (dairy, milk, farm, pouring, food), **family** and **premium and wholesome** as universal defaults, and the **language** defaults (Telugu-accented, Hinglish).
- `VISUAL_RULES` (page 15444): already neutral, and it already carries a rule the Carousel lacks: "whenever a character appears at a different age or in different clothes ... name that age and those clothes in the scene's visual". See the side note below.
- `packscene` video clauses (Surface 1), `continuity.py`, `cut.py`, comments and docstrings (`filmvoice.py` "Sankranti ...", `heygen.py` voice list, `creative.py` model labels): not prompts, or real assets.
- `filmvoice.py` kin-word lists (amma, ammamma, thatha, anna): recognition vocabulary, Telugu-leaning. A gap for other languages, not a leak; left for the language answers (Step 7).
- The failure-pattern note about generated lettering ("in Devanagari or Telugu it is not writing at all", `main.py` 822): advice about a model limit, kept.

## Proposed change, one commit
1. **Clip prompt (1294):** drop "Authentic Indian family setting ... premium and wholesome". Setting and tone come from the film's own script and the brand block (`people_setting`).
2. **`_IMG_STYLES["real"]`:** keep what is true of the look (photoreal, 50mm, shallow depth of field, soft natural light, true-to-life colour, realistic skin and hands, no illustration) and drop "food & lifestyle", "condensation on fresh milk" and "dairy-farm" and the home/kitchen setting. "Product": "appetising and premium" goes, "the hero pack" stays. `_VID_STYLES["product"]`: "macro pack and pouring shots" becomes "macro product shots".
3. **`music_prompt`:** the tail becomes "Instrumental score for a brand film. No vocals, no lyrics." and the picked style steers the rest. **Option A (recommended):** `/music-options` also passes the brand's `sound_world` answer, added as one labelled line ("THE BRAND'S SOUND WORLD: ..."), so Heritage's bansuri-and-tanpura direction still reaches the music and a cement brand's does not. **Option B:** just remove the tail; Heritage then gets only the style it picks.
4. **Page defaults:** `production.voice` starts empty (the backend already handles an empty voice: Sarah, no language). The script sentence becomes "Spoken lines are in the languages THE BRAND's language mix gives, where natural; English if it gives none." and the provocation rewrite's regex is updated to match, so the two stay in step. Placeholders become neutral examples (2746: "Lead: a woman in her 30s, shoulder-length hair, mustard shirt; ..."; 2671: "tighten scene 2", "add a closing beat", "make the VO shorter").

## What I will NOT touch
`voice_block`, the brand preamble, `VISUAL_RULES`, POSM and Onground image prompts (they do not use these styles; Surfaces 4 and 5), the voice pool and its Indian default, the pack-detection regexes (sub-step 1b), and any stored Heritage data.

## Blast radius (what else changes when `_IMG_STYLES["real"]` changes)
Social and Carousel images use the same string, so their look changes for every brand too: no more "dairy-farm"/"fresh milk" bias, which is the point, but it is a visible change to the pictures. Heritage's `imagery_style` answer (when accepted) supplies the DSLR look; without it Heritage keeps "photoreal, shallow depth of field, natural light" from the shortened string.

## Verification
- `tools/golden_prompts.py --compare`: the prompts it captures do not include these strings, so it must show 0 changed (a guard that nothing else moved).
- New `tools/test_video_agnostic_defaults.py` (stubbed, no model): every `_IMG_STYLES` and `_VID_STYLES` entry free of food, milk, dairy, farm, pouring and family; `music_prompt` for a cement, beauty, apparel and biscuit brand carries no dairy, premium or "Indian instrumentation" (and carries the sound-world line only when answered, Option A); the clip prompt builder output for those brands carries no "Indian family" / "premium and wholesome"; the page file has no "Telugu-accented" default, no "Hinglish" sentence, and the provocation rewrite still matches the script sentence (so provocation mode still replaces it).
- Existing: `test_video_agnostic`, `test_provocation*`, `test_sound_plan*`, `test_produce_sound`, `test_nuance_heritage_checklist` (22) must still pass; `selfcheck`, `smoke`, `checkfe`, `partials verify`; tenant compare.
- Real page: open the Video screen, confirm the voice field is empty by default and the script prompt text (read through the page's prompt builder with the network stubbed) carries the new language sentence for Grounded and for a provocation.
- Live: push, `/selfcheck` commit match, log scan. **Not coverable without a model:** how the pictures, music and spoken language actually change. One real Heritage film check by the owner after deploy.

## Rollback
Revert the commit. No data changes.

## Side note, not part of this commit
The Carousel prompt has no equivalent of the page's film rule about naming age and clothes whenever a character appears at a different age or in different clothes. The mother who changed from kurta to saree between two slides (12 Oct run 1) is the case it covers. The cast pin fixed that run, so this is optional; if wanted it is a separate Carousel commit with its own real-model check.

## Decisions I need from you
1. **Keep "Indian" as the country default**, removing only category, family, premium and language defaults? (Recommended: yes, matching your India-only decision.)
2. **Accept Heritage's `imagery_style` on the live profile screen before this ships?** (Recommended: yes. It is the one Heritage answer still pending, and it carries the DSLR look the shortened string no longer spells out.)
3. **Music: Option A** (pass the `sound_world` answer into the music prompt) **or B** (just remove the tail)? (Recommended: A.)
4. **Voice default:** empty field (recommended), or prefill it from `sound_world` for brands that answered it?

## Cross-surface audit (12 Oct, after the owner asked for blast radius and wiring across Surfaces 1, 2 and 3)
Method: a change inventory per commit since Surface 1, then each change traced forward (what consumes it) and backward (what feeds it) through backend and page, then driven end to end through the REAL routes with the model, image and music engines stubbed (`tools/test_surfaces_wiring.py`, new), plus the real page for the paths a person takes.

**Found and fixed (Surface 3 branch):** the page sent NO `brand_mode` on `/produce-video`, `/music-options`, `/rescore` or `/voice-preview` (only storyboard frames sent it). So the Independent-mode guard I added to `_sound_world` could never fire from the page (an Independent film would still get the active brand's sound world in its music), and, older than any of this, an Independent film's clip prompts kept naming the active brand because `_vid_brand_mode` always read "grounded". Now all four calls send it (the shared `voicePayload` covers `/voice-plan` and `/voice-preview`). Effect to know: in Independent mode, clip prompts now say "brand film for a brand", which is what Independent mode is for.

**Traced and intact:** Surface 1 (carousel concept route answers 200 with `routes/count/note`; the prompt points at the brand's answers; Heritage's handling, ring-at-the-base and pack-in-the-picture lines arrive; a cement brand sees no dairy), Surface 2 and 2b (`/idea-draft`, `/campaign-draft`, `/plan-generate` channels and `/brand-brief-draft` carry the other-category examples; the campaign Word export prints the new shape line; every leftover occurrence of a removed string is a comment or docstring, none in the page), the IMC fix on the server (a redraft with the screen's id corrects the same library row, a draft without one adds a row, the page's reset shows the project-naming gate again), Surface 3 (music prompt with and without the sound world, Independent mode, `/voice-plan` with an empty voice identical to the old default's answer, `/scene-still` look, clip prompt). Browser: nothing persists the old voice default (`localStorage` holds only client name, accent and theme).

**Stub-only and static checks (not a live run):** `/rescore` and `/produce-video` bodies are checked in the page source, not by clicking through a render; no real image, music or speech was generated.
