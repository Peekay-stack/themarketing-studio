# Is the Video backend brand-agnostic? An audit (7 Oct 2026)

The decision: the Video path carries itself from the **brand profile** (category, market, tone, mandatories, palette...), with nothing about any one
brand or category written into its own prompts. This audit reads every place Video builds a prompt, for a text model, an image model, a video
model, a music model and the voice cast, and says which still carry a signature.

**Short answer: no, not fully.** The text-model prompts (the concept, the script, the cast sheet, a scene rewrite) did; they are fixed in this
change and guarded by a test. The prompts that drive **paid renders** (the video clip, the still image, animation looks, the music bed) still do,
and so do the voice defaults, the language line and two of the objective chips. Those are listed below with a proposed generic replacement each;
nothing there has been changed, because each steers a paid render and the owner should choose the wording.

## Evidence: what a cement brand was given before this change

Driving the page with Sthir Cement's real profile, the concept prompt told the model to propose "an emotional family story, **a craft/provenance
route showing where the milk comes from**, and a lighter observational route". The script prompt's example was a half-asleep **boy saying
"Ammamma"** and a voice-over line **"Pure doodh ki shakti."**, its rules said "(the **boy** grows up)" and "the older **mother in the cream
saree**", a scene rewrite was "for an **Indian crew**", and the cast-sheet examples were "MOTHER (older): cream saree" and "MOTHER (young) + BOY (6)".
Every brand got these. After the change a cement film's concept and script prompts contain none of them (captured the same way).

## Fixed in this change (text-model prompts)

| Where | Was | Now |
|---|---|---|
| Concept routes (`generateVideo`) | "family story / provenance showing where the **milk** comes from / observational" | "a human story, a craft-or-proof route showing what makes this product what it is, a lighter observational route; draw each from THIS brand's own category, market and platform" |
| Script JSON example | Boy / "Ammamma" / VO "Pure doodh ki shakti." | neutral ("Speaker", "spoken words only") |
| Script rules (`VISUAL_RULES`) | "the boy grows up", "older mother in the cream saree" | "a character grows up", "the older lead in the grey cardigan" |
| Scene rewrite | "for an Indian crew" | "for a crew shooting in the market the brand sells in" |
| Cast sheet | MOTHER / BOY / saree examples | LEAD / SECOND / grey cardigan |
| **Tagline** | "MANDATORY ON EVERY PIECE: ... the line 'Pure Doodh Ki Shakti'" and the sign-off super "Heritage Foods — Pure Doodh Ki Shakti" | In a film the marks and declarations stay mandatory; a tagline / sign-off line is "on file, NOT mandatory". The sign-off super is the brand name plus a payoff line written for THIS film from its message. |
| House binding | the normal script, rework, departments, scene rewrite and the three derive calls did not send `house_id` (the server guessed the house by brand name) | they all send it, and `film: true` |

Guard: `tools/test_video_agnostic.py` fails if the Video prompt builders (or the server's film instruction blocks) name dairy, milk, Heritage, a mother
and boy, a saree, "Ammamma" or "Indian crew" again, and pins the tagline behaviour. It was checked against the old source and fails there.

## Still carrying a signature (NOT changed; each needs the owner's choice)

| # | Where | What it says | Effect | Proposed generic replacement |
|---|---|---|---|---|
| 1 | `main.py` ~1292, the **video clip** prompt (every shot) | "Authentic Indian family setting, warm natural light, premium and wholesome;" | every brand's rendered clips are told they are an Indian family film | drop it; the brand profile's market and tone (already in the prompt through the brand line) carry the setting, e.g. "Setting true to <MARKET>, natural light." |
| 2 | `main.py` ~1540, the **still image** `real` style | "Professional commercial **food & lifestyle** photography ... condensation on **fresh milk**. Authentic contemporary Indian home, kitchen, or dawn **dairy-farm** setting with real people" | every brand's stills are told they are a dairy photo shoot | "High-resolution, photorealistic advertising photograph ... true-to-life colours, realistic textures; a setting true to the brand's market and category" |
| 3 | `main.py` ~1560-1575 animation looks | "warm Indian storybook feel", "warm Indian folk-art sensibility" | India-specific look for any brand | "warm storybook feel in the brand palette" / "folk-art sensibility native to the brand's market" |
| 4 | `filmaudio.py` ~103, the **music** prompt | "Instrumental score for a **premium Indian dairy brand film** — warm, wholesome, uplifting, gentle Indian instrumentation" | every brand's music bed is told it is for a dairy brand | "Instrumental score for a brand film; fit the brand's tone and market. No vocals, no lyrics." (the style chips and the free-text mood carry the rest) |
| 5 | script prompt: "Dialogue in English + Hinglish where natural" | a fixed language mix | Heritage's own profile says `languages: te, en` and is ignored; any non-India brand is told Hinglish | derive from the profile's `languages` (needs a check that the voice step can read the language it is asked for) |
| 6 | `filmvoice.py`, `main.py:514` | the voice pool and default accent are Indian | fine for the markets served today, wrong for another | accent default from the brand's market |
| 7 | Objective chips | "Trust & purity — Farm-to-home story on quality and sourcing", "Recipe / usage" | food/FMCG framing offered to every category | category-aware objectives, or neutral wording |
| 8 | Music style chips | "Gentle Indian flute", "Festive dhol", "Devotional / temple" are listed for every brand | India-bound options | list by market, keep the neutral styles for all |
| 9 | pack-detection words | "glass of milk", "pouch", "sachet", "milk bags" | only matters for dairy-like packs; harmless elsewhere | leave, or move to the profile's `packs` |

Items 1 to 4 are text, but they steer **paid renders**, so a real render comparison (a Heritage film before and after) is the honest check; that is
the owner's call because it spends credit.

## Not a Video signature, but seen on the way
- `demoHouse` / `demoPlan` in the page carry dairy sample data; they only show when the server returns nothing.
- Comments in `continuity.py`, `cut.py` and `media.py` mention Heritage or India as history, not as behaviour.
