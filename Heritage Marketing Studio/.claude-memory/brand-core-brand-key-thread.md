---
name: brand-core-brand-key-thread
description: "Brand core (brand key / essence) as an optional brand-profile input — backend built 8 Sep, ASK_DESIGN_61 out for the frontend, downstream wiring still to do"
metadata: 
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-08T11:59:29.482Z
---

Started 8 Sep 2026. The user wants the **brand key / brand essence** as an optional input in the
brand profile — "where it's available and followed it becomes a critical guide / guardrail / boundary
for what the brand can and can't do." Sits *above* the messaging house (which flexes per campaign);
the house must not contradict it.

Preceded by a thorough web search of five distinctly different models (Unilever Brand Key · Brand
Pyramid · Kapferer Identity Prism · Brand Essence Wheel · Aaker Identity System; Keller CBBE noted as
a diagnostic, not an input). All five collapse to one storage shape: `essence` line +
framework-specific `layers` + a `boundaries` list (the "will not do" — always present, no classic
model names it).

## Backend — BUILT & tested 8 Sep, uncommitted

`api/brandprofile.py`:
- `BRAND_CORE_FRAMEWORKS` — the 5 templates (name/blurb/essence_label/essence_help/layers[{key,label,help}]).
- `_normalise_brand_core()` — validates framework, keeps only that framework's layer keys, listifies
  boundaries. Unknown framework clears the core.
- `brand_core_view(b)` — joins the stored core to its template (labels + values + `set` flag +
  `frameworks[]` for the picker). For the frontend.
- `brand_core_block(b)` — the grounding fragment: `BRAND CORE — <framework>: "<essence>"` + labelled
  layers + `THIS BRAND WILL NOT (hard boundary …): …`. Empty when no core.
- Folded into `voice_block()` right after POSITIONING, before TONE.
- `put()` handles `brand_core` as a whole nested object (replace, not field-merge), like `colours`.

`api/main.py`: `GET /brand-fields` and `POST /brand-fields` / `POST /brand-save` responses gained a
`brand_core` key. **No new routes.**

Storage: `brands/<id>.json` → `brand_core: {framework, essence, layers:{key:value}, boundaries:[]}`.

## Frontend — MERGED & browser-verified 8 Sep

Design built ASK_DESIGN_61 on the **correct base this time** (`app.dc-3b96de56.html`, sha verified,
brand-character merge present — unlike round 60). +129/-2, 5 clean hunks, applied at exact match, LF
preserved. A collapsed-by-default "Brand core" section on the brand-profile screen (below the fields,
above Save): framework picker (5 cards) → essence input → per-framework layer textareas → boundaries
block with a red left border. All rendered from `brand_core` in `GET /brand-fields`, nothing
hardcoded; Save sends `brand_core` whole via `POST /brand-fields`.

**One gap found in the browser and fixed:** picking a framework rendered no fields —
`bfCoreLayerRows` was derived from `bc.layers` (the *saved* framework's fields), which is empty until
Save. Fixed by (1) backend: each `frameworks[]` entry in `brand_core_view` now carries its own
`layers` spec + `essence_label`/`essence_help`; (2) frontend `bagBrandCore`: field template follows
the *picked* framework (`frameworks.find(...).layers`), values from local edits or the saved
framework when it matches. Verified live end to end (pick → fields appear → switch → swap → Save →
`voice_block` carries `BRAND CORE` + layers + `THIS BRAND WILL NOT`). `ASK_DESIGN_61_REPLY.md` written.

checkfe after merge: sc-if 1029, sc-for 400, 924 members, 24 bags. `app.dc.html` now 24,588 lines.
All uncommitted (`brandprofile.py`, `main.py`, `api/frontend/app.dc.html`).

## Downstream connection map — mostly NOT built

- **Social / Video / house / platform / plan / sales**: live — all call `voice_block`, so essence +
  boundaries reach them. (More than first thought — it's every `voice_block` caller, not just
  Social/Video.)
- **PR**: WIRED 8 Sep — `pr.release_suggestions()` `source_material` now carries `brand_essence` +
  `brand_boundaries`. PR generates NO prose by design ("a press release cannot be plausible"), so
  this is handed over as reference for the writer, not injected into a prompt (there is none).
- **POSM / Onground**: still NOT wired for brand *core* — `producers.py` doesn't call `voice_block()`
  at all. (It now DOES call `character.for_prompt()` via `_ctx`, but not `voice_block`.) The brand
  core still only reaches POSM/Onground indirectly, through the house.
- **Brief**: pre-fill insight/target from the core (`derives_from` pattern); flag a proposition that
  contradicts the essence — not built.
- **Messaging house**: show essence/boundaries as a fixed banner; editing the core marks the house
  stale (same cascade as editing the house core) — not built.
- **Idea platform**: `spine_block()` should carry essence + boundaries; a soft check flags a
  `territory` that trips a boundary — not built.
- **IMC plan**: light — objectives ladder to essence, inherited transitively; no hard gate.
- **Brand character** ([[brand-character-skill-thread]]): a character's hook/type express the core
  personality; the identity ladders to the essence — a consistency cross-check, not built.

Full table is in `ASK_DESIGN_61.md`. See also [[studio-work-inventory]].
