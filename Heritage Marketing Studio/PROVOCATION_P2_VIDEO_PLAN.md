# Provocation P2: Video writes from an approved provocation

Drafted 7 Oct 2026, after a read-only sweep of Video's writing path. A PLAN: nothing here is built until the owner answers the decisions at the end.

## What Video does today (swept)

Every Video text generation is a **client-built prompt** sent through `/complete`; the server wraps it in a **system prompt** (`complete.complete` -> `prompts.system_for`, the only caller):

| Step | Client function (`app.dc.html`) | What the prompt says |
|---|---|---|
| Concept routes | `generateVideo` | preamble (brand voice incl. TONE) + objective + brief + "The idea platform this film stands on" + **"Propose THREE genuinely different creative routes"** (examples: family story, provenance, lighter observational), ~2 words/second of VO |
| Script | `writeFullScript` | preamble + concept + learned **anchors** (approved past work) + rules + locked copy; a **pack-shot sign-off scene is mandatory**; **"CASTING THE SOUND": give people dialogue, prefer a mix of VO and dialogue**; `VISUAL_RULES`; VO budget |
| Rework | `reworkScript` | revise the script rows per a note |
| Departments | `draftDept` | preamble + approved script + `decidedFacts` |
| Stock text if the model fails | `fallbackFullScript`, `fallbackVideo` | a generic script / refusal |

Server system prompt for a film = `GLOBAL_MASTER` (craft) + `THE BRAND` (voice block with TONE) + character + spine (house, platform, plan) + the **VIDEO** block: "setup -> small tension -> brand truth -> resolution", "vo: a single, human, spoken line".

**Why a provocation cannot work through that as it is:** the VIDEO block's structure rule, "give people dialogue", the mandatory pack-shot super, the brand TONE and the learned anchors all push toward the conventional film a provocation exists to depart from. A wordless, absence-led film would be fought by five instructions. And today the provocation reaches Video only as one quoted sentence ("The idea platform this film stands on: ...").

## What P2 builds

**1. A provocation route (the 4th card, as agreed).** "Use my provocation" becomes a card in the creative-routes row, enabled when the film stands on an approved provocation. Clicking it makes ONE model call that writes the film as a concept (`name, rationale, logline, duration, vo, scenes`: the shape routes already have) from the provocation's spine and film DNA. The three normal routes are written exactly as today, **without** the provocation. Nothing changes unless the person clicks it.

**2. Provocation mode on `/complete`.** New payload fields `provocation_id` / `use_provocation`. When an APPROVED provocation of this house is named (and the piece is Grounded, not Independent), `system_for` builds a different system prompt:
- brand **guardrails kept in full** (claims, banned words, regulator, never-do, mandatories); the brand **TONE dropped** (the provocation's stance replaces it);
- `GLOBAL_MASTER` kept; the **VIDEO block swapped** for a provocation-aware one (same JSON contract, but structure, voice-over length and dialogue follow the film DNA, not setup-tension-truth-resolution);
- a **PROVOCATION block**: message, device and how it works, the category-says / we-say pair, the line a stranger could repeat, what it breaks (so the film does not use those codes), the act (as the idea's proof), the film DNA (structure, humour, visual language, sound language, cast approach, VO words, how the brand arrives), the hard limits;
- with no provocation named, the system prompt is **byte-identical to today's** (pinned by a test).

**3. Script, rework and departments follow it.** When the working concept came from the provocation, `writeFullScript`, `reworkScript` and `draftDept` send `provocation_id`, and in that mode: the "pack-shot sign-off" rule becomes "the brand arrives as the film DNA says" (a closing brand moment is still required, its form comes from the provocation); "CASTING THE SOUND" follows sound language, cast approach and VO words; the learned **anchors are off** (rules and locked copy stay); a failed model call gives an **honest failure, never a stock script**.

**4. Provenance.** The concept carries `provocation_id`; the film saves and restores it (filmscript already stores the pick). Picking another route clears it, so later steps are ordinary again.

**5. Undo one P1 side effect.** The quote box and `standsCtx` currently follow the provocation (P1). With a separate route they must not: the three normal routes stand on the platform as before. The provocation keeps its own card and banner.

## Blast radius (swept)

- Server: `prompts.py` (`system_for`, a new `provocation_block`, a new video-provocation block), `complete.py` (`complete()` new arguments), `main.py` (`/complete` reads two fields, resolves with `provocation.resolve_for`). `system_for` has one caller (`complete.complete`).
- Frontend: `complete()` extra, a new route-generation function and card (template `conceptRouteCards`), `writeFullScript`, `reworkScript`, `draftDept`, the fallbacks, `loadVideoStandsOn` (revert the P1 provocation parameter), `pickConceptRoute`, save/restore, the P1 banner wording.
- Tests: a new `test_provocation_complete.py` (system prompt with and without, the TONE and VIDEO-block swap, Independent mode ignores it, another house's provocation ignored, a draft ignored); the page driven with stubs (4th card, payloads on script/dept/rework, normal routes unchanged).
- **Not touched:** Social, POSM, On-ground, PR; frames, cast lock and stills (P3); sound, music, beat roles (P4); exports (P5); the provocation tab; stands_on for other producers.

## What P2 will NOT do yet (said on screen too)

The Film DNA reaches the **text** (concept, script, departments) in P2. It does not yet reach the **Production** steps: a "no music" sound language will not switch Production's music off, a cast approach of "none" will not remove the cast lock, and frames will still be written with the usual craft. Those are P3 (cast, frames, craft override) and P4 (music, voice-over budget, beat roles, the "Authentic Indian family setting" line in the still prompt, `main.py:1286`).

## Verification

Local: stubbed-model tests of every prompt change, the page driven end to end, the full suite, `selfcheck`, tenant snapshot. Live: `/selfcheck` and logs only (login-only). No real model call from here: **the first real run is the owner's**, on "The Plain Glass" and "Before The First Glass".

## Decisions for the owner (recommended first)

1. **A 4th card, with the three normal routes untouched** (recommended), or make all three routes variations of the provocation.
2. **Drop the brand TONE in provocation mode** (recommended; keep every guardrail).
3. **Learned anchors off in provocation mode** (recommended; rules and locked copy stay).
4. **Honest failure, no stock script, in provocation mode** (recommended).
5. **The closing brand moment stays required, shaped by "how the brand arrives"** (recommended), or drop the pack-shot rule entirely for provocation films.

Rollback: a revert of the commit; no stored data changes (the concept's `provocation_id` is one extra key).
