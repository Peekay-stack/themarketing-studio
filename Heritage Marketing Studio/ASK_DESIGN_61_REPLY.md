# ASK_DESIGN_61 — reply: adopted, one gap fixed

Built on the correct base this round — `app.dc-3b96de56.html`, sha verified, the brand-character
merge present. Thank you. `checkfe` clean (`sc-if` 1029/1029, `sc-for` 400/400, 924 members, 24
bags). Line endings pure LF. All five hunks applied at exact match, no fuzz.

## One real gap — fixed

**Picking a framework showed no fields.** `bagBrandCore` derived `bfCoreLayerRows` and
`bfCoreHasLayers` from `bc.layers` — but that's the **saved** framework's field list (with values),
returned by the backend from what's stored. Nothing is stored until Save, so a fresh pick left
`bc.layers` empty and no layer fields rendered. `essence_label` / `essence_help` had the same
problem (they followed the saved framework, not the picked one).

Fix, in two parts:

1. **Backend** (`brandprofile.brand_core_view`): each `frameworks[]` entry now carries its own
   `layers` spec (`[{key,label,help}]`, no values) plus `essence_label` / `essence_help`. So the
   picker has every framework's field template up front, no round trip.
   ```jsonc
   "frameworks": [
     { "key": "brand_key", "name": "Brand Key (Unilever)", "blurb": "…", "layer_count": 8,
       "essence_label": "Brand essence", "essence_help": "…",
       "layers": [ { "key": "root_strength", "label": "Root strength", "help": "…" }, … ] },
     …
   ]
   ```
   Top-level `layers` still reflects the **saved** framework (its fields *with* stored values) — it's
   now only a value source.

2. **Frontend** (`bagBrandCore`): the field template follows the framework picked in the UI —
   ```js
   const fwSel = frameworks.find(f => f.key === curFramework) || null;
   const layerTmpl = fwSel ? (fwSel.layers || []) : [];
   const savedVal = (key) => ((bc.layers || []).find(x => x.key === key) || {}).value || '';
   …
   bfCoreEssenceLabel: (fwSel && fwSel.essence_label) || bc.essence_label || 'Brand essence',
   bfCoreEssenceHelp:  (fwSel && fwSel.essence_help)  || bc.essence_help  || '…',
   bfCoreLayerRows: layerTmpl.map(l => ({ key:l.key, label:l.label, help:l.help,
     value: layerVals[l.key] !== undefined ? layerVals[l.key] : savedVal(l.key) })),
   bfCoreHasLayers: !!curFramework && layerTmpl.length > 0,
   ```
   Values come from local edits (`layerVals`), falling back to the saved framework's stored value
   only when the picked framework still matches what's saved.

## Verified live (real backend, disposable tenant)

Section renders collapsed → expands → 5 framework cards → picking **Brand Key** shows its 8 layer
fields, switching to **Prism** swaps to its 6 → filled essence + two layers + boundaries → **Save**
round-trips through `POST /brand-fields` → `voice_block` in the form's own preview now carries
`BRAND CORE — …`, the layer values, and `THIS BRAND WILL NOT …`.

## Next round

Base ASK_DESIGN_62 on the merged file this session returns. Confirm its sha.
