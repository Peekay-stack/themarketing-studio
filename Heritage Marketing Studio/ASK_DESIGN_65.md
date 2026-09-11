# ASK_DESIGN_65 — a real "add a new brand" flow (header chip + Studio Settings)

## The bug this fixes

Today there is no way to create a second brand profile. Typing a different name into Studio
Settings' "Brand name" field does nothing to create one — that field is a separate, session-only
display override (its own helper text says "Leave blank to follow the brand on the open IMC
brief"), not a save. The only thing either the header chip or Studio Settings can do is *switch
between brand profiles that already exist* — and when only one profile is active and nothing
matches the name you typed, every screen silently falls back to showing that one active profile.
That's why a user working a brand-new brief for "Parle G" kept seeing Heritage Foods' data
everywhere: nothing named "Parle G" existed yet for anything to resolve to.

Base file: `api/frontend/app.dc.html`. Diff your working copy against the current committed one
before starting — same merge-never-replace discipline as every round before this.

## Backend — already built and verified this session, use as-is

**`GET /brand-fields`** gained a `new` query param (default `false`, fully backward compatible).
`GET /brand-fields?new=true` returns the same shape as always (`fields`, `spec`, `core`, `voice`,
`brand`, …) but **guaranteed blank** — `brand: null`, every field `"state":"missing"`,
`"value":""` — it never falls back to the active profile. Verified live: returns a clean blank
form regardless of what's currently active.

**`POST /brand-fields`** — unchanged contract, but now: if the payload has **no** `brand`/`id` and
the `name` given doesn't match any existing profile, the newly created profile is **automatically
made active** (was: created correctly, but left the old brand active everywhere, which looked like
the save had failed). Verified live: created a test brand with no id/brand in the payload, it came
back `"active": true` and every other profile flipped to `"active": false` in the same response.

Existing, unchanged, already used elsewhere in the file — reuse these, don't reinvent:
- `GET /brands` → `{brands: [...]}`, each with `id`, `name`, `category`, `active`.
- `POST /brand-active` `{id}` → switches active, returns the updated `brands` list — this is what
  `switchBrand(id)` (line 11368) already calls.

## Frontend — three surfaces

### 1. Header chip dropdown (`bagBrands()`, line 12545; rendered ~155-236)

Add a **"+ Create new brand"** row at the bottom of the `brandRows` list, visually distinct from
the switchable brand rows (they're clickable cards with a name/category/Active-badge; this one
reads as an action, not a brand). Wire it to a new `openNewBrandForm` handler (below). Keep
"Studio settings →" and "Close" as they are.

### 2. Studio Settings → Brand profile section (lines 266-293)

Add the same **"+ Create new brand"** button, but at the **top** of the brand-profile block — above
the `sc-for` list of `brandRows` at line 269, not below it. Below it, the existing brand-row list
and "What the studio is told →" card stay as they are.

Also: reword the "Brand name" field's helper text (line 293, currently "Leave blank to follow the
brand on the open IMC brief.") so it can't be mistaken for brand creation — something like *"Only
relabels the studio for this session — it does not create or edit a brand profile. Use '+ Create
new brand' above to add one."* Exact wording is yours; the point is a reader must not walk away
thinking this field is how you add Parle G.

### 3. The "add a brand" flow itself

**New handler**, alongside `openBrandForm` (line 19869):

```js
openNewBrandForm = () => {
  this.setState({
    screen: 'brandform', settingsOpen: false, brandMenuOpen: false,
    bf: null, bfVals: { name: (this.state.studio || {}).clientName || '' },
    bfVoice: '', bfCoreFramework: '', bfCoreEssence: '', bfCoreLayers: {},
    bfCoreBoundaries: '', bfCoreOpen: false,
  });
  window.scrollTo(0, 0);
  this.loadBrandFields(true);
};
```

**`loadBrandFields`** (line 19873) needs an `isNew` param. When true, call
`/brand-fields?new=true` instead of the brand/house/brief query string, and — this is the important
part — do **not** apply the existing "seed once" merge (`bfVals: { ...vals, ...(s.bf ?
(s.bfVals||{}) : {}) }`). That merge exists to protect a half-typed draft from being clobbered by a
redundant fetch of the *same* brand; for a genuinely new form it would instead leak whatever was
last in `bfVals`. For the `isNew` path, seed `bfVals` from the (blank) response only, keeping just
the `name` you pre-filled in `openNewBrandForm` if the response doesn't override it.

**On save of a form opened this way** (`saveBrandFields`, line 19939): no change needed to the
call itself — the backend now handles activation automatically when the payload has no bound
`brand`/`id`. After a successful save where the form was in "new" mode, close back to the same
place `closeBrandForm` goes (`screen:'home'`) and show the same toast pattern `switchBrand` already
uses: `'Now working on ' + name + ' — every generator is grounded in its profile.'`

### 4. Fix while you're in here: switching between two *existing* brands leaks stale fields

`switchBrand` (line 11368) updates the `brands` list, reloads briefs and the logo, but never
touches `bf` / `bfVals` / `bfCore*`. If the brand-profile form has been opened once already,
`loadBrandFields`'s seed-once merge means switching to a different existing brand and reopening the
form will show the *previous* brand's field values, not the new one's — the user's own bar:
"When you switch it back to existing brand, the fields should relate to that particular brand."
Add to `switchBrand`, right after the active-list update (~line 11378): reset
`bf: null, bfVals: {}, bfCoreFramework: '', bfCoreEssence: '', bfCoreLayers: {},
bfCoreBoundaries: '', bfCoreOpen: false`. That forces a genuine reload next time the form opens,
same as the new-brand path above.

## Do NOT touch

- Anything in `landing.html` — unrelated file, unrelated round.
- The brand-profile form's own field rendering (`bagBrandForm`, line 19976) — the fields it draws
  from `spec` don't change; only how the form is *entered* changes.
- `brand-brief-builder` / brief creation flow — out of scope here.

## Acceptance test before hand-back

1. Open the header chip → click "+ Create new brand" → form opens with every field blank, Brand
   Name pre-filled only if Studio Settings' name field already had something typed.
2. Type "Parle G" + a couple of fields, save → toast confirms it's now active; header chip and
   Studio Settings both show Parle G, not Heritage.
3. Reopen the form for Parle G → still shows Parle G's own (mostly blank) data, not Heritage's.
4. Switch back to Heritage from either surface → header chip, Studio Settings, and (if reopened)
   the brand-profile form all show Heritage's real saved data — not Parle G's, not blank.
5. Confirm Heritage's own profile is completely untouched throughout (check a couple of its field
   values before and after).
6. Desktop layout only for now — this doesn't need a mobile pass.

## Hand-back

Return the full `app.dc.html`. Run `tools/checkfe.py` first. State which base commit/version you
diffed against.
