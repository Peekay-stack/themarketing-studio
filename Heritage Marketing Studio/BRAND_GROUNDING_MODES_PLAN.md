# Brand grounding modes — detailed build plan

Companion to the scenario table below is the exact wiring: what's new, what file, what gets added,
and what silent fallback gets removed at each point. Build order matches dependency, not tab order —
Ground Truth has to be brand-aware before "Grounded" means anything, and the Producers chokepoint has
to accept a mode before any tab's toggle can actually reach generation.

---

## Stage 1 — Ground Truth becomes brand-scoped (prerequisite, no toggle yet)

This stage has no user-facing toggle. It just stops three stores from being brand-blind. Everything
still behaves like today for a single-brand tenant; it only changes behavior once two brands share a
tenant, which is exactly the case that's broken now.

### `library.py`
**New:** `brand: str = ""` param on `add()`, stored as a new `"brand"` field on every row (mirrors
what `made.py` already does).
**Changed signatures:** `items(kind="", signed_only=False, brand="")`, `reference_url(kind, brand="")`,
`shot_references(..., brand="")` — each filters to `r.get("brand") == brand` before picking, when
`brand` is given; empty `brand` keeps today's tenant-wide behavior (needed for Stage-1-only rollout —
see migration note below).
**Unwired:** nothing removed yet — the empty-`brand` case is the old behavior, kept as the literal
default until every caller below is updated to pass one.
**Callers to update** (pass the resolved brand — ~30 sites, all mechanical, same shape):
`main.py` lines 720, 822-823, 1646, 1853, 2044, 5882, 5895, 6428, 6438, 6554, 6582-6583, 6902-6903,
6958 · `posm.py` 753-755, 789-790 · `continuity.py` 258, 417, 480 · `shelf.py` 170-171. Each of these
already sits inside a route that has `house`/`brief`/`payload` in scope — the brand comes from the
same `brandprofile.resolve(house, brief)` (or payload `brand`) call already being made nearby, not a
new lookup.
**Migration:** existing library rows have no `brand` field — `r.get("brand")` reads `""` for all of
them. A one-time script (or a manual pass in the Ground Truth tab) to tag existing items by brand is
worth doing before Stage 1 ships, otherwise every pre-existing asset silently stops being pulled once
callers start passing a real `brand` (safer than the reverse — an untagged asset that goes missing is
loud; one that keeps bleeding across brands is not).

### `learning.py`
**Changed:** `_dir()` → `_dir(brand_key: str = "")`, appends a brand subdirectory
(`tenancy.dir("learning") / _brand_slug(brand_key)`) when given one; empty stays at today's tenant
root (same migration posture as `library.py` — old data isn't silently orphaned).
**Changed signatures:** `anchors(kind, brief="", n=3, brand="")`, `anchor_block(kind, brief="", n=3,
brand="")`, `house_rules(limit=12, brand="")`, `rules_block(brand="")`, `record(..., brand="")`,
`keep_example(..., brand="")` — each opens the brand-specific directory when `brand` is given.
**Unwired:** the `GUARDRAILS` text already claims brand-scoping (`learning.py:99`) — no change needed
there, it becomes true instead of aspirational.
**Callers to update** (all in `main.py`, all already resolve a brand nearby): 2017, 2024, 2040-2042,
2973, 2976, 3322, 3324, 3544, 3549, 4215, 4218.

### `made.py`
**No signature change needed** — `brand` is already recorded per row. Only `list_entries()` gains a
`brand: str = ""` filter param.
**Unwired:** `_made_brand_project()` (`main.py:5528`) currently falls to `brandprofile.resolve()`
(active brand) as a last resort when neither payload nor house names one — that fallback stays for
Stage 1 (it's the correct "best-effort attribution" behavior for grounded work) but gets a guard added
in Stage 4 so General-mode work doesn't get silently attributed to whatever's active.
**Frontend:** History tab (`app.dc.html`, the `history`/`made` screen) needs a `brand=` query param
added to whatever loads it, and a "brand" column/filter shown — currently mixes every brand's output.

---

## Stage 2 — Brief

### Backend (`briefstore.py`)
**New field on every brief:** `brand_mode: "grounded" | "general"`, alongside the existing `brand`
field. `save()` (`briefstore.py:99`) starts writing it; defaults to `"grounded"` for backward
compatibility when absent (so old briefs — which all have SOME brand stamped, per today's
auto-stamp — keep working exactly as before).
**`briefs(brand="")`** unchanged in shape; `brands()` (`briefstore.py:282`) keeps its existing
`no_brand`/unbranded count, which now means something real instead of "brand field happened to be
blank."

### Frontend (`app.dc.html`)
**New UI:** a small mode control next to the existing brand context on the brief screen — default
"Grounded in [Brand]" pill (reading `this.brandName()`, same accessor as today), switchable to
"General work." New state: `briefBrandMode: 'grounded' | 'general'` (default `'grounded'`).
**Changed:** `saveBrief`/`saveImcBrief` (`app.dc.html:12697`, `12712`) — currently
`brand: this.brandName()` unconditionally. Becomes: `brand: s.briefBrandMode === 'general' ? '' :
this.brandName(), brand_mode: s.briefBrandMode`.
**Unwired:** nothing removed — this is additive; a brief saved without ever touching the new control
still gets today's exact behavior (grounded, active brand).

---

## Stage 3 — Strategy (Messaging House)

### Backend (`strategy.py`)
**New:** houses gain the same `brand_mode` field, defaulted from the linked brief's `brand_mode` at
creation.
**Changed:** the grounding line at `strategy.py:939-940` —
```python
brandprofile.resolve(house.get("brief"), house)
```
becomes conditional on `house.get("brand_mode") != "general"`: when general, skip `resolve()` entirely
and pass `voice_block(None)` directly rather than letting `resolve()`'s active-brand fallback fire.
**Unwired:** the implicit "no brand matched → use whichever is active" path, specifically for houses
tagged general. Grounded houses are untouched — `resolve()` still runs exactly as it does today for
them.
**`learning.anchor_block`/`rules_block` calls in this route** (`main.py:2973-2976`) — General-mode
houses skip these entirely (T1/T3 are brand-specific per the scenario table; nothing to retrieve for a
brand-agnostic house).

### Frontend
Same mode-pill pattern as Brief, defaulting to match the linked brief's `brand_mode` (not forced —
changeable independently, per the "door not gate" rule). New state: `houseBrandMode`.

---

## Stage 4 — Producers (the big one — `/complete` and image generation)

### The text path
**`complete.py`** — `complete()` gains `brand_mode: str = "grounded"` and (when grounded) an optional
`brand: str = ""` passed through to `system_for()`.
**`prompts.py`** — `system_for()`'s line 442, today:
```python
b = brand or brandprofile.resolve()
```
becomes:
```python
b = None if brand_mode == "general" else (brand and brandprofile.by_name(brand)) or brandprofile.resolve()
```
i.e.: General mode never resolves anything, full stop — this is the actual unwiring, the one line
that currently makes every `/complete` call fall back to the active brand with no way to opt out.
**`main.py`'s `/complete` route** (`main.py:300-326`) — reads `brand_mode`/`brand` off the payload the
same way it already reads `execution`/`force_typed`/etc., passes them through.
**`app.dc.html`'s `complete()` wrapper** (`app.dc.html:11337`) — the single chokepoint every producer
screen already calls through. Gains: reads the calling screen's own `brandMode` state (see below) and
folds `brand_mode`/`brand` into the `extra` object before the existing `window.claude.complete(call)`.
**`needBrand()`** (`app.dc.html:11312`) — today a hard refusal with no exception. Gains a bypass: when
the screen's own `brandMode === 'general'`, skip the refusal (there's deliberately no brand, that's
not an error state anymore).

### The image/video path
**`main.py`'s `_brand_line()`** (`main.py:2532`) — gains a `brand_mode`/`brand` parameter (or, cleaner,
becomes `_brand_line(brand: dict | None)` and every one of its 6 callers passes the already-resolved
brand or `None` instead of the function calling `resolve()` itself). Callers: 1160, 1167, 1718, 1835,
6462, 7003 — each already sits in a route with a house/brief/payload brand in scope.
**Reference images**: every one of the ~30 `library.*` calls updated in Stage 1 already accepts a
`brand` param — the image/video routes pass `""`/`None` when the piece is General mode, and Stage 1's
filtering means an empty brand now correctly returns **nothing** rather than the tenant's most-recent
item of that kind. This is the change that stops a General-mode piece from silently inheriting
whichever brand's pack shot happens to be newest.

### Frontend, per producer screen (Social, Video, POSM, On-ground, PR, Sales enablers)
**New state per screen:** `socialBrandMode`, `videoBrandMode`, `posmBrandMode`, `onGroundBrandMode`
(names indicative — match existing per-screen state naming already in the file), each defaulting to
match `linkedBrief`'s `brand_mode` when one is linked, else `'grounded'`.
**New UI:** the same mode pill, placed consistently across all four/six producer screens — this is
the one that most needs the "visible as the header brand chip" treatment from the plan doc, since it's
the last checkpoint before generation actually runs.
**17 call sites** (`this.complete(`/`this.needBrand()`, counted directly in the file) — each producer
action already calls through the one wrapper; the wrapper change above means these sites themselves
need no individual rewiring beyond making sure the screen's own `brandMode` state is set before the
call, which the new UI element handles.

---

## Stage 5 — Plan

Same shape as Strategy: new `brand_mode` field defaulted from the linked house, same conditional skip
on the claims-proof-gate check (`plan.py`'s resolve call at `plan.py:1037`) when general — proof gate
explicitly reports "no brand attached, nothing to check claims against" rather than silently passing
or silently failing.

---

## Sequencing and checkpoints

1. **Stage 1** ships alone, verified with two real brands' worth of library/learning/made data on
   localhost — confirms cross-brand bleed is actually closed before any toggle UI exists.
2. **Stage 2 (Brief)** — smallest surface, proves the `brand_mode` field/pill pattern end to end.
3. **Stage 3 (Strategy)** — same pattern, one more layer, plus the first real "General" generation
   through `voice_block(None)`.
4. **Stage 4 (Producers)** — the load-bearing one; touches the shared chokepoint every other producer
   relies on. Gets its own checkpoint before shipping given the blast radius.
5. **Stage 5 (Plan)** — smallest remaining surface, last.

Each stage: `checkfe.py` + LF check after every `app.dc.html` edit, local verification on
`localhost:8000` (both modes, both brands), before moving to the next stage. Nothing pushed to
`origin/master` until you've reviewed on localhost and said so — same as every round this session.
