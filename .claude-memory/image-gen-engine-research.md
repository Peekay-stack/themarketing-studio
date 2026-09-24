---
name: image-gen-engine-research
description: "Image/video engine choice, compositing vs generation, which providers are reachable, plus the living playbook artifact that now supersedes this as the up-to-date version — check the artifact first"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-09-24T07:49:28.858Z
---

**LIVE DOCUMENT, check this first**: [Image and Video Engine Playbook](https://claude.ai/artifact/TQ4v3So79uCASppWBmkiNF)
— the maintained, up-to-date version of everything below, split into Part A (image: stills engine
comparison, pack/identity fidelity work, Gemini's own image blueprint checked against our code) and
Part B (video: engine comparison table across Veo/Kling/Seedance/Runway/Luma/Hailuo/Pika/PixVerse, a
dedicated storyboards subsection, Gemini's own Veo blueprint checked against our code). Update the
artifact directly (same URL, republish with `url` set) rather than writing new research only here —
this memory file is the anchor/pointer plus the parts of the 22 Sep research not worth re-deriving from
the artifact every time.

Researched 22 Sep during [[brand-grounding-modes-project]]'s Round 20 (the prompting-technique review
that preceded shipping the camera-technical/reference-labelling wording), then extended 24-25 Sep with a
second-opinion review of two Gemini implementation blueprints (Flash image, Veo video) checked line-by-line
against the real code, plus a fresh video-engine market scan. Captured here so it doesn't need
re-researching from scratch — but the artifact above is the current version; this file may lag it.

**What this app actually uses** (confirmed by reading `api/gemini.py`, not assumed): stills go through
`IMAGE_MODEL = "gemini-3.1-flash-image"` (Gemini 3.1 Flash Image, aka "Nano Banana 2") via `gemini.image()`/
`gemini.image_from_reference()`; video (the Video producer / film pipeline only) goes through
`VIDEO_MODELS` — Veo 3.1 lite/standard. Veo has **no still-image mode at all** — it never touches Social/
Carousel/POSM stills. `creative.py`'s fal.ai integration (Flux, via `image_from_reference`) is the
automatic fallback when the Google call fails or is out of quota.

**The choice was validated, not found wanting.** As of 22 Sep, Gemini 3.1 Flash Image leads Arena's
text-to-image leaderboard (1280 Elo) ahead of GPT Image 1.5 (1248). The pack-fidelity struggles this whole
project has fought are not a sign of picking a weak engine — they're a known, cross-provider limitation
(every engine researched shares the same "advertising hero shot" prior for product photography).

**Two techniques tried and folded into the shipped wording (22 Sep, packscene.py/main.py):**
1. Camera-technical framing (a lens/distance constraint) instead of only descriptive/prohibitive prose —
   from Google's own Nano Banana prompting guide, which says the model understands real photographic
   parameters directly.
2. Reference-image role labelling + reordering (spatial constraints before character-identity tokens) —
   from Veo's own prompting guide's formula, applied to the image side even though Veo itself isn't used
   for stills.
Both proven on a live trial before shipping (BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 20").

**Compositing is the real fidelity fix, explicitly not started.** The industry-standard way dedicated
product-photography tools (Photoroom, Flair.ai, Pebblely, Claid) guarantee product accuracy is
fundamentally different from what this project does: they never ask a generative model to redraw the
product at all. They cut the real product photo out once (background removed) and paste it onto a
separately-generated background afterward — fidelity is guaranteed by construction, not requested by
prompt. This project's approach (reference-conditioned generation + wording) is the correct
implementation of the *other* half of the industry, and has a real ceiling: no wording, however good, has
fully closed the "pack presented toward camera" failure mode across five rounds of trying (Rounds 16-20).
A full compositing pipeline is a genuinely bigger, separate build (a product-cutout step, a placement
step, a blend step) — discussed at length with the owner, explicitly not begun. If this comes up again:
the cheapest middle ground discussed was compositing ONLY the CTA slide (the one slide every carousel
always shows the pack on) with a fixed placement, not a full pipeline.

**Other engines, if ever worth trying:** Ideogram, Recraft, Flux and GPT Image are all reachable through
the *same* fal.ai integration already wired in `creative.py` — trying a different model there is a
model-ID swap, not a new integration. GPT Image specifically tested as the strongest of that group on
literal multi-constraint instruction-following (the exact property this project has been fighting for),
stronger than Recraft (which is tuned for consistent *style* across a design system, not literal photo
fidelity). **Midjourney has no official API at all and never will by design** — every "Midjourney API" on
the market is an unofficial Discord-automation wrapper that violates their ToS and risks account bans; it
was ruled out entirely, not deprioritised. DALL-E 2/3 are fully deprecated and removed from OpenAI's own
API; GPT Image is their replacement.
