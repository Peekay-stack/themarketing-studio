# Handover — ASK_DESIGN_61: Brand core (brand key / essence)

**File**: `app.dc-3b96de56.html`, base verified: 24,456 lines (spec named 24,455 — 1-line rounding,
consistent with the file this ask pointed at), sha-named `3b96de56…`. Frontend only, per the ask — no
new backend routes used.

## What was built

New **"Brand core"** section on the brand-profile screen (`isBrandForm`), placed below the existing
field cards and above Save/Back. Collapsed by default, showing the exact "Not set — the enduring
essence…" copy from the ask when empty, or `framework_name — essence` once set. Nothing about a
framework's fields is hardcoded — it all renders from whatever `brand_core` the server returns.

Expanded, it shows:
- **Framework picker** — the five `frameworks[]` as cards (name + blurb), click to select; a "Clear —
  no framework" link when one is chosen.
- **Essence** — single input, label/help pulled from `essence_label` / `essence_help`.
- **Layers** — one textarea per `layers[]` entry, label + help text, prefilled from `.value`.
- **Boundaries** — line-per-item textarea ("What this brand will never do"), given the heavier
  treatment asked for: `#C0392B` left border, tinted background.

### Save behaviour
`saveBrandFields` now also sends `brand_core: { framework, essence, layers: {key:value map},
boundaries: [] }` whole to the existing `POST /brand-fields`, and redraws the section from whatever
`brand_core` comes back in the response — same round-trip pattern the rest of the form already uses.
Switching framework and saving is what reshapes the layer fields; nothing is reshaped client-side
before that, matching the ask's own note that the backend drops non-matching keys.

### State seeding
`bfCoreFramework` / `bfCoreEssence` / `bfCoreLayers` / `bfCoreBoundaries` / `bfCoreOpen` seed once on
first load (same rule as `bfVals` — a background reload never clobbers a half-typed draft), and are
re-seeded from the server's response after every save.

## Out of scope this round (per the ask)
- Framework diagrams (keyhole / pyramid / hexagon / wheel).
- Downstream wiring into brief/house/idea/plan/producers/character — backend, later rounds. Item 6
  (voice block already carrying `BRAND CORE` / `THIS BRAND WILL NOT`) needed no frontend change and
  will simply appear in the existing "What the model is told" panel once the backend sends it.

## On ASK_DESIGN_60_REPLY.md
Not edited — it's Claude Code's note back to you about the round-60 base-sha slip, not a file this
side ships changes into. Forward it to Claude Code as-is next round if that was the intent; flag if
you actually wanted something built from it.

## Verification
Loaded clean in preview, no console errors. Run `tools/checkfe.py` against your local checkout before
merging.

## Next round
Base ASK_DESIGN_62 on the file this round returns. Confirm bytes + sha before editing — that's the
step round 60 skipped.
