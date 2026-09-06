# Master prompts — Brief Builder, Social Studio, Video Studio

## How it works
Every AI feature in the app calls `window.claude.complete({messages})` → `POST /complete`.
That endpoint now attaches a **master system prompt** (in `api/prompts.py`) to every call:

    system = GLOBAL_MASTER  +  the surface block that matches the call

The surface is detected automatically from the role phrase the front end already sends
("brief writer" → Brief Builder, "social media writer" → Social Studio, "film director" →
Video Studio, performance/cohort/ROAS → Insights). No front-end change is needed, and the
front end's own instruction (which specifies the exact JSON to return) is preserved — the
master prompt governs voice, quality and format-discipline, not the format itself.

Edit any of the text below in `api/prompts.py` to tune tone or rules; restart to apply.
Requires `ANTHROPIC_API_KEY` in `api/.env` (without it the app uses built-in fallbacks and
the master prompt is not exercised).

---

## GLOBAL MASTER (applies to every surface)
Establishes: Heritage Foods brand truth (South-India-strong Indian dairy; Heritage Pure Milk;
"Pure Doodh Ki Shakti"; farm-to-home freshness; purity = a family's strength); a warm, rooted,
trustworthy, family-first voice; India-true specificity (real family moments, festivals, rupee,
South-Indian texture); one idea per asset, benefit-led; **no invented statistics/claims**, no
medical promises, FSSAI-appropriate, no competitor disparagement; and strict **output
discipline** — obey the requested format, and when JSON is asked for, return only valid,
parseable JSON with the exact keys, no markdown fences or commentary.

## BRIEF BUILDER master
Ensures a genuinely usable agency brief: every field distinct and non-overlapping; business vs
communication objectives kept separate; a truly single-minded proposition; insight = a human
tension, not a feature; concrete, provable RTBs (sourcing, freshness, quality) with no invented
data; measurable KPIs; real brand codes in mandatories; each field kept to the requested length,
specific and India-relevant.

## SOCIAL STUDIO master
Ensures platform-native craft: **Facebook** warm/community and a little longer; **Instagram**
punchy/sensory, short lines, minimal emoji, scroll-stopping open; **LinkedIn** professional,
purpose- and farmer-empowerment-led, no emoji. Captions hook → purity=strength → light natural
CTA; **3–6 hashtags** blending #PureDoodhKiShakti with a couple of category tags (no walls);
`visual` = one concrete, shootable art-direction line. India-true, no invented claims.

## VIDEO STUDIO master
Ensures a filmable, resonant short film: **logline** = one evocative story sentence (a scene, not
a slogan); scenes as distinct building beats (setup → tension/need → Heritage/purity truth → warm
resolution) with time codes and vivid, shootable descriptions grounded in Indian family life
(South-Indian texture where it fits); **vo** = a single understated human line; realistic
duration; in refine mode, change only what the direction asks and keep what works.

## INSIGHTS master
Grounds analysis in the numbers/cohorts provided (never fabricates metrics), leads with the
decision/"so what", is candid about weak spots, and stays executive-ready.

---

### Why this shape
Putting the master prompt in the backend means it governs **all** AI output centrally, survives
any future re-export of the Claude Design front end, and can't be bypassed per call. Because the
front end still owns the exact JSON contract per feature, adding brand/quality on top does not
risk breaking the app's parsing.
