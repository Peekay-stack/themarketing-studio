# Step 5, Surface 5: Onground (consumer activation). Plan (12 Oct)

Status: sweep done. Small change, same shape as Video's clip prompt and POSM's opener; building it now (no live-profile gate).

## Finding: Onground is already brand-agnostic except five hardcoded "in India" strings
Every Onground prompt already carries the brand block (`_ctx` / `brand_ctx`), which renders the brand's own `market` (MARKET line) and `meeting_points` ("WHERE PEOPLE MEET THE BRAND IN PERSON"). So the hardcoded "in India" in each opener is **redundant with the brand block's MARKET line** — the same reason Video's "Authentic Indian family setting" was dropped (setting comes from the brand's own answer).

## A. Model-visible, hardcoded country assertion (all carry the brand block already)
| # | Where | String |
|---|---|---|
| 1 | `producers.activation_ideas` (producers.py ~923) | "planning consumer activations **in India** — real ones…" |
| 2 | `producers` activation-idea-adjust prompt (~1103) | "planning a consumer activation **in India** — a stall, a van, a promoter, a street." |
| 3 | `producers` activation-element prompt (~1135) | "writing a production brief for one element of a consumer activation **in India**." |
| 4 | `/activation-element-image` (main.py ~8509) | "for an **Indian** consumer activation at {venue}." |
| 5 | `/activation-element-image` (main.py ~8519) | "Photographic, **real Indian location**, natural light…" |

All five carry `_ctx`/`brand_ctx`, which already states the brand's market (Heritage: "India, strongest across South India…"). "India" here is the country, not dairy — but it is hardcoded, redundant with the brand block, and a forward-looking liability the day a second-market key is added (the owner's own India-only-with-a-key framing).

## B. Kept on purpose (Indian-consumer defaults / a picked catalogue / Step 8)
- **`VENUES`** (kirana, modern_trade, mall_atrium, office_complex, rwa, sabzi_mandi, haat, temple_festival, transit, college, doorstep): a generic Indian-consumer venue catalogue the model picks from. It maps almost exactly to Heritage's `meeting_points` answer, which already reaches the prompt. Replacing this fixed list with the brand's own `meeting_points` (so a cement brand gets dealer points and sites, not kirana) is **Step 8 (selectors)** in the master plan — new archetypes and a screen change — not Surface 5. Left as-is here.
- **Leave-behind / stall sizes** (`activation.py`): "sensible Indian retail defaults", a picked catalogue overridden by a real spec, same discipline as `posm.FORMATS`. Not category-specific. Left.
- "a stall, a van, a promoter, a street" (generic activation nouns), the capture/promoter rules: generic craft, kept.

## Change (one commit)
Drop the five country assertions so the brand's own `market` governs (via the brand block already in each prompt):
1. "consumer activations in India — real ones" → "consumer activations — real ones" (the MARKET line in THE STRATEGY block states where).
2. "a consumer activation in India — a stall, a van…" → "a consumer activation — a stall, a van…".
3. "one element of a consumer activation in India." → "one element of a consumer activation."
4. "for an Indian consumer activation at {venue}." → "for a consumer activation at {venue}." (`brand_ctx` carries the market; its no-profile branch already says "keep this generic").
5. "Photographic, real Indian location, natural light…" → "Photographic, a real location, natural light…" (keeps the realism instruction, drops the country assertion).

India-only still holds: every current brand's profile says India, so the brand block supplies it. A cement or apparel brand gets its own market and no forced "Indian activation".

## What I will NOT touch
`VENUES`, the leave-behind/stall size catalogue, `_ctx`/`voice_block`, the capture/promoter rules, the venue-selector logic (Step 8), the pack-detection vocabulary (1b), and any stored data.

## Verification
- `golden_prompts --compare golden_step5`: the `onground` surface changes only by the dropped country words, for all 5 brands; nothing else. (The element-image prompt is a route, not in golden — covered by the wiring test.)
- Extend `tools/test_surfaces_wiring.py`: `/activation-idea` for a cement, beauty, apparel and biscuit brand carries no "in India"/"Indian" country assertion and no dairy; Heritage's `meeting_points` ("WHERE PEOPLE MEET THE BRAND IN PERSON") still reaches the prompt; the route answers 200 with its shape.
- Existing: `test_nuance_heritage_checklist`, `selfcheck`, `smoke`, `checkfe`, `partials verify`, tenant compare.
- Live: push, `/selfcheck` match, log scan. Not coverable without a model: real activation renders.

## Rollback
Revert the commit. No data changes.
