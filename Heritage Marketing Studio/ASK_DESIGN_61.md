# ASK_DESIGN_61 — Brand core (brand key / essence) on the brand-profile screen

**Base file**: `api/frontend/app.dc.html`, sha256 `3b96de56e3013304e6b9f8b4921f806809323c41fc3e56421e50cc7d4dbb7826`,
**24,455 lines**. This is the ASK_DESIGN_60 merge already folded in — NOT the root-level `app.dc.html`,
NOT your round-60 handback. **Open with the usual step: verify bytes + sha256 match before editing.**
Round 60 skipped that and was built ~2,900 lines behind; see `ASK_DESIGN_60_REPLY.md`.

Frontend only. The backend is built, live and tested (`brandprofile.py`, `main.py`) — no new routes.

## What this is

An **optional** input on the brand profile: the enduring **brand key / brand essence** — the fixed
root every campaign ladders to, and the boundary for what the brand can and can't do. It sits *above*
the messaging house (which flexes per campaign); the house must not contradict it.

One stored shape for every model — `essence` line + framework-specific `layers` + a `boundaries`
list (the "will not do", always present regardless of framework). The frontend renders the picker
from data the backend returns, same principle as the rest of this form.

## Data — already returned by the existing routes

`GET /brand-fields?brand=<id>` response gained a **`brand_core`** key:

```jsonc
"brand_core": {
  "framework": "brand_key",              // "" | brand_key | pyramid | prism | wheel | aaker
  "framework_name": "Brand Key (Unilever)",
  "essence": "Trusted like home milk",
  "essence_label": "Brand essence",       // label + help are framework-specific
  "essence_help": "Two or three words that hold components 5–8 together.",
  "boundaries": ["no celebrity endorsements", "never lead on price"],
  "layers": [                             // in framework order; render these fields
    { "key": "root_strength", "label": "Root strength",
      "help": "What first made the brand famous — the deep equity it can always draw on.",
      "value": "the co-operative dairy since 1992" },
    { "key": "discriminator", "label": "Discriminator", "help": "…", "value": "" }
    // …one per layer in the chosen framework
  ],
  "set": true,
  "frameworks": [                         // for the picker — all five, always
    { "key": "brand_key", "name": "Brand Key (Unilever)",
      "blurb": "The FMCG standard. Nine boxes in a keyhole…", "layer_count": 8 },
    { "key": "pyramid",   "name": "Brand Pyramid",  "blurb": "The lite option…", "layer_count": 4 },
    { "key": "prism",     "name": "Kapferer Identity Prism", "blurb": "A balanced hexagon…", "layer_count": 6 },
    { "key": "wheel",     "name": "Brand Essence Wheel", "blurb": "Concentric rings…", "layer_count": 3 },
    { "key": "aaker",     "name": "Aaker Identity System", "blurb": "Separates a fixed core…", "layer_count": 4 }
  ]
}
```

`POST /brand-fields` (and `POST /brand-save`) accept it back and return the same shape:

```jsonc
{ "brand": "<id>", "brand_core": {
    "framework": "pyramid",
    "essence": "…",
    "layers": { "attributes": "…", "functional_benefits": "…" },   // send as a {key: value} MAP, not the array
    "boundaries": ["…", "…"]
} }
```

Send `brand_core` **whole** (framework + essence + all layers + boundaries), not field-by-field —
the backend replaces it, keeps only the chosen framework's own layer keys, drops the rest. Switching
framework and saving re-labels; values under keys the new framework doesn't have are dropped.

## The screen

A new **"Brand core"** section on the brand-profile / setup screen (`isSetup` / the brand-fields
form). Optional and clearly so — collapsed by default with a one-line "Not set — the enduring essence
every campaign roots in. Optional, but a strong guardrail where the org has one." expander.

When expanded:

1. **Framework picker** — the five `frameworks[]` as selectable cards (name + blurb + layer_count).
   Picking one (or changing) sets `framework` and reshapes the fields below. No framework = the
   section is effectively off.
2. **Essence** — a single-line input, labelled from `essence_label`, helper from `essence_help`.
3. **Layers** — one field per `layers[]` entry, labelled from `.label`, helper text from `.help`,
   prefilled from `.value`. Textarea is fine; these are a sentence or two each.
4. **Boundaries** — a list input (same control as `avoid` / `mandatories` elsewhere on this form):
   "What this brand will never do." Always shown regardless of framework.
5. **Save** through the existing `POST /brand-fields` with `{ brand, brand_core: {...} }`. On the
   response, redraw from the returned `brand_core` (same as `setup`).
6. Show the **effect**: this form already renders `voice` (the grounding block) so a person can see
   what the model is told. `voice_block` now includes a `BRAND CORE — …` section and a
   `THIS BRAND WILL NOT …` line when a core is set — no change needed, it'll just appear.

Visual language: match the rest of the brand-profile form (the `ask`/`why` card pattern, `#DDD9D1`
borders, Epilogue headings). Boundaries deserve a slightly heavier treatment (they're a hard
constraint) — a left border in `#C0392B` or similar, consistent with how the app marks refusals.

## Out of scope this round

- The framework-specific *diagram* (keyhole / pyramid / hexagon / wheel). Nice later; the fields are
  what matters now.
- The downstream wiring below — that's backend, separate rounds.

---

## How brand core connects downstream (context — mostly backend, later rounds)

`voice_block()` already carries the essence + boundaries into **Social and Video** generation today
(they resolve the profile and read `voice_block`). The rest is follow-on:

| Stage | Field(s) it touches | Connection | Status |
|---|---|---|---|
| **Brief** | `insight` ↔ core `insight`; `target` ↔ core `target`; proposition/SMP must ladder to `essence`; brief RTB ↔ core `reasons_to_believe` | **Pre-fill + consistency.** Brief screen pre-fills insight/target from the core (marked "from brand core, editable", same `derives_from` pattern the profile form already uses); a proposition that contradicts the essence raises a finding. | not built |
| **Messaging house** | house *core message* ↔ `essence`; functional pillars ↔ `benefits`; emotional pillars ↔ `values_personality` / `culture`; house RTBs ↔ core `reasons_to_believe`; tone ↔ `personality` | **Parent constraint + stale cascade.** House screen shows the essence + boundaries as a fixed banner it must ladder to; editing the brand core marks the house "stale", exactly like editing the house core cascades to dependent layers today. | not built |
| **Idea platform** | `territory` must sit inside `boundaries`; platform `why` ↔ core `insight`; platform `rtb` ↔ core `reasons_to_believe`; `idea`/`mechanic` express the `essence` | **Boundary gate + grounding.** `ideas.prompt_for()` / `spine_block()` already surface why/territory/proof/rtb — add the essence + boundaries so a drafted platform is generated inside the guardrails; a soft check flags a territory that trips a boundary. | not built |
| **IMC plan** | plan *objectives* ladder to `essence`; channel/format choices shouldn't include anything a boundary rules out | **Light.** Mostly inherited transitively through the house/platform. Surface the essence as context on the plan screen; no hard gate. | not built |
| **Producers** | every prompt | **Hard constraint.** `voice_block` carries `BRAND CORE` + `THIS BRAND WILL NOT` at the weight of `avoid`/`banned_words`. **Gap:** `producers.py` (POSM, Onground) doesn't call `voice_block()`/`resolve()` at all — 2 of 6 producers don't see the guardrail yet. PR especially needs `boundaries` (a spokesperson line that crosses one is a real risk). | Social/Video: live. POSM/Onground/PR: not wired. |
| **Brand character** | a character's `hook` / `type_line` express core `personality` / `self_image`; the whole identity ladders to the `essence` | **Consistency.** A cross-check in the character skill / the six-test spine. | not built |

## Next round

Base ASK_DESIGN_62 on the file this round returns. Confirm its sha before editing.
