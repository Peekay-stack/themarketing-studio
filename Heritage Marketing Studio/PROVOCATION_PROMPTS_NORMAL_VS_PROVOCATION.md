# What the model is actually given: a normal film versus one written from a provocation

Captured 7 Oct 2026 by driving the real page with the model stubbed (so these are the exact `/complete` payloads), plus the real
server system prompt built for the same house. Brand and house: Heritage Foods, house `063785d77c` (dev tenant). The provocation is a
representative record ("The Plain Glass"). Every call has TWO parts: the **client prompt** (the user message, built in `app.dc.html`) and
the **system prompt** (built by `prompts.system_for` from the brand profile, the house, the platform and, in provocation mode, the provocation).

## 1. The concept

### Client prompt, normal route (three routes)
```
You are a film director at an ad agency for Heritage Foods.

[the brand voice block, 13 lines: BRAND, CATEGORY, MARKET, HERO PRODUCT, MASTER BRAND IDEA ("everything ladders to this"), POSITIONING,
 TONE: Warm, wholesome and reassuring, with a premium modern finish, BRAND CODES, MANDATORY ON EVERY PIECE: FSSAI mark; the line
 'Pure Doodh Ki Shakti', COMPETITORS, BRAND PALETTE, ALSO TRUE, AUTHORITY]

Communication objective: "Brand awareness". Propose THREE genuinely different creative routes for a 30s film — not three phrasings of one
idea. Each must take a distinct angle: for example an emotional family story, a craft/provenance route showing where the milk comes from,
and a lighter observational route. Give each a short route name and a one-line reason it could work. The voiceover is performed as ONE
continuous read across the whole film (it does not restart per shot), so write roughly 32 words per route — about 2 words per second of
30s — as flowing connected sentences, never per-scene fragments. Return ONLY JSON (no markdown): {"routes":[{"name":..., "rationale":...,
"logline": string, "duration": "30s", "vo": "the full ~32-word voiceover", "scenes": [{"t":"0–5s","title":string,"desc":string}, ... 4 concept
beats]}, ...exactly 3 routes]}.
```
Call extras: `brand_mode`, `house_id`, `force_typed`, `skip_mandatories`. No provocation fields.

### Client prompt, provocation route (one concept)
```
You are a film director at an ad agency for Heritage Foods.

[the same brand voice block WITHOUT the TONE line; everything else identical, including MANDATORY and MASTER BRAND IDEA]

Communication objective: "Brand awareness". Write ONE film concept of 30s that dramatises the approved provocation in your instructions:
"The Plain Glass" — "Milk disappears into everything a family drinks, except the one glass that matters most.". Follow its message, its
device, its film structure, humour, visual language, sound language and cast approach; do not fall back on the category’s usual film. The
voiceover is about 18 words, one continuous read across the whole film. Give a short route name and a one-line reason it works. Return ONLY
JSON (no markdown): {"name":..., "rationale":..., "logline": string, "duration": "30s", "vo": string, "scenes": [{"t":"0–5s","title":string,"desc":string}, ... 4 concept beats]}.
```
Call extras: `brand_mode`, `house_id`, `provocation_id`, `use_provocation: true`. (With a film that says no voice-over the voiceover sentence reads: "EMPTY: the provocation says there is none, so "vo" is an empty string".)

**What differs:** one concept instead of three; the "emotional family story / provenance / lighter observational" menu is gone; the tone line is gone; the provocation's name and line are named and the model is told to follow its film notes; the voice-over length comes from the provocation (0 allowed) instead of "2 words per second".

## 2. The script

### Client prompt, the passages that change (everything else is identical)
| Passage | Normal | Provocation mode |
|---|---|---|
| Sign-off | "The film MUST include a pack-shot sign-off — a scene that shows the pack and carries the pack-shot super "Heritage Foods" — and that is normally the final scene. Only when the concept calls for a comeback AFTER the pack shot may a short closing button… Dialogue in English + Hinglish where natural." | "The film MUST include a brand sign-off scene: the brand arrives exactly as the provocation says ("<how the brand arrives>"), and that scene carries the super "Heritage Foods" and is normally the final scene. Only when the concept calls for a comeback AFTER the sign-off may a short closing button… Any spoken words follow the provocation’s sound language, in English + Hinglish where natural." |
| Sound | "CASTING THE SOUND: when a person is on camera and would naturally speak, give them DIALOGUE in their own words… A film where every line is "vo" is wrong unless the concept is genuinely wordless observation; prefer a mix…" | "SOUND (provocation mode): follow the provocation’s sound language, cast approach and voice-over length exactly. Speech only where the provocation has it; a wordless film has "audio": [] on every scene." (the rules about what an "audio" entry may contain are kept) |
| Speech budget | "STRICT SPEECH BUDGET — … NO MORE than 32 words, about 5 words per scene… At least one scene MUST have "audio": []…" | "SPEECH BUDGET: the provocation sets the voice-over at about N words across the ENTIRE film…", or "NO SPEECH: the provocation says there is no voice-over and no dialogue, so every scene has "audio": []." |
| Example in the rules | "(the boy grows up)" | "(a character is older)" |
| JSON example at the end | a half-asleep Boy saying "Ammamma... sky is still sleeping, no?" and a VO line "Pure doodh ki shakti." | a neutral template: `"audio": []`, plus the shape of one entry; no boy, no tagline |
| Learned examples (anchors) | given | NOT given (the house rules and any locked copy still are) |
| If the model fails | a stock script (`fallbackFullScript`) | an honest failure, nothing invented |
| Call extras | `brand_mode` only | `brand_mode`, `house_id`, `provocation_id`, `use_provocation: true` |

## 3. The system prompt (what the server adds, same house, same brand)

| Part | Normal | Provocation mode |
|---|---|---|
| Craft (`GLOBAL_MASTER`) | yes | yes |
| Brand block | all lines incl. TONE | the same lines **without TONE** (guardrails, mandatories, banned words, claims, regulator all kept) |
| Recurring character | when the brand has an approved one | dropped when the cast approach is objects, animated or none |
| "THE STRATEGY ALREADY DECIDED — BINDING" (house core message, RTBs, avoid list, the platform with its insight and mechanic) | yes | yes |
| …"How it is already expressed elsewhere — be consistent with these" (the platform's earlier video, social, POSM… expressions) | yes | **left out** (a provocation may depart from how the platform is expressed) |
| …"Where your instruction and this section disagree, this section wins" | yes | adds: "The one exception is the PROVOCATION section further down: it may depart from how the platform is expressed… never from what the platform says and never from the guardrails above." |
| PROVOCATION block | none | name, one line, message, device and how it works, category says / we say, the repeatable line, what it breaks ("do NOT use any of these as this piece's own habits"), the act (as the idea's stated proof), stance (replaces the usual tone), FILM NOTES, hard limits |
| Film instructions | "everyday setup → small tension → brand truth → resolution", "logline… a human at its centre", "vo: a single, human, spoken line" | "PROVOCATION MODE": follow the provocation's structure, device, humour, visual and sound language, cast approach and voice-over length; no usual arc, no warm family tableau, no tagline dump; "vo: exactly as long as the provocation says. Zero words is allowed" |

## 4. What a provocation film is still asked to carry (owner decisions, not bugs)

- `MANDATORY ON EVERY PIECE: FSSAI mark; the line 'Pure Doodh Ki Shakti'` and `MASTER BRAND IDEA … everything ladders to this` stay in the brand
  block. A provocation that wants no tagline in the film (e.g. "Your First Pour, Your Time") is therefore asked to carry the line anyway.
  Say if provocation mode should relax these for a piece, knowing they are the brand's own mandatories.
- The normal script call does not send `house_id` (the concept call does), so the server guesses the house for a normal script, rework and
  department draft; the provocation script sends it. Pre-existing, not changed.
- The cast sheet, the location line and the look reference are derived by separate calls that are not yet in provocation mode (P3).
