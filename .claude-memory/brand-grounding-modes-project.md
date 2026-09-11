---
name: brand-grounding-modes-project
description: "Multi-stage build (11 Sep 2026) giving every tab a Grounded/General toggle so \"no brand attached\" is a real, honored choice instead of an accident — Stages 1-4 built and compile-verified, Stage 5 (Plan) + full live testing still open"
metadata: 
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-11T15:57:19.860Z
---

**Start here for this thread**: `BRAND_GROUNDING_MODES_PLAN.md` (repo root) has the full technical
plan — schema, exact functions, file:line wiring per stage. This memory is the status/continuity
layer on top of it.

## Why this exists

Traced from the user's original bug report ("generating Parle G still writes Heritage") through three
rounds of fixes that session (`brandprofile.resolve()`'s active-brand fallback in three places,
[[client-name-override]]-class staleness in the header/settings flow) to a much bigger finding: the
whole app has **no way to say "this piece is deliberately not tied to any brand."** Every text
generation (`/complete`, the shared chokepoint nearly all producers use) and every image generation
fell back to whichever brand was globally active, full stop — a General/"no brand" intent had nowhere
to go. Separately, traced that **Ground Truth (the reference library) and Learning (corrections/
retrieval) were architecturally brand-blind** — no `brand` field on library items at all, tenant-wide
only for learning — so even *correctly* grounded work could silently pull another brand's pack shot or
house rules if two brands shared a tenant (this account now has 5: Heritage Foods, Kumkum Beauty,
Loomwell, Parle G, Sthir Cement).

User's own design call, after I asked and got specific direction: **default is always Grounded (brand
profile + its own Ground Truth)**; **General is an explicit opt-in per tab** (Brief/Strategy/Plan/
Producers each get their own toggle, independently changeable, but a downstream tab defaults from
whichever upstream document started it — door not gate, divergence shown never blocked).

## Build order and status (11 Sep 2026, one session)

- **Stage 1 — Ground Truth brand-scoping.** DONE, compile-verified, live-verified through the real
  authenticated session. `library.py`/`learning.py` gained a `brand` field + filter on every
  read/write function (additive — empty `brand` keeps old tenant-wide behavior, so nothing breaks
  until a caller passes one); `made.py`'s `list_entries()` gained the same filter (it already recorded
  `brand` per row, just never read it back). Wired ~15 real generation/status routes across
  `main.py`/`posm.py`/`shelf.py`/`continuity.py` (POSM image gen, `/scene-still`, house/plan/platform/
  trade text generation, continuity checks, `posm.gate()`).
- **Stage 2 — Brief.** DONE, live-verified (real save round-trips both ways: General → `brand:"",
  brand_mode:"general"`; old-style save with no `brand_mode` → correctly defaults `"grounded"`).
  `briefstore.put()` gained `brand_mode`; `/brief-save` enforces the pairing server-side too. Frontend:
  Grounded/General pill on both the guided Brief Builder and the IMC screen; `needBrand()` and
  `brandPreamble()` both gained an `allowGeneral` bypass (previously hard refusals with no escape
  hatch) — General now reaches `voice_block(None)`'s already-correct honest "don't invent a brand"
  instruction on purpose instead of never at all.
- **Stage 3 — Strategy/Messaging House.** DONE, live-verified with a real before/after prompt
  comparison (`/house-prompt`): a General house's actual generation prompt reads the honest no-brand
  instruction with zero leakage; a parallel Grounded Parle G house in the same test correctly carries
  real brand facts — proving the contrast, not just that one path always renders the same text.
  `strategy.prompt_for()` checks `house.get("brand_mode")` *before* ever calling `resolve()` — the
  actual bug-class fix. Houses default their mode from the brief that started them; new
  `/house-brand-mode` route changes it after the fact. `/house-generate`'s T1/T3 learning retrieval and
  locked-copy now skip outright for General houses (not scope-to-empty — approved scripts/corrections
  are inherently brand flavor, never genuinely brand-agnostic the way a research file can be).
- **Stage 4 — Producers (`/complete` + image generation).** DONE, compile-verified only — **live
  testing deferred to tomorrow morning (12 Sep) at the user's own instruction**, this is the one stage
  that has NOT been clicked through in a browser yet. Built:
  - `prompts.system_for()` gained `brand_mode`; when `"general"`, skips `resolve()` entirely rather
    than falling to whichever brand is active — this is the actual fix for the chokepoint every
    producer's text generation shares.
  - `complete.py`/`main.py`'s `/complete` route thread `brand_mode` through.
  - Frontend: **one shared `producerBrandMode` state for the whole Producers tab** (not one per
    screen — matches how the user themselves listed the tabs: "brief, strategy, Plan, Producers", one
    Producers tab, not four). Pill lives in the **app header**, next to the brand chip, so it's visible
    regardless of which producer screen is open. `complete()`'s wrapper auto-injects `brand_mode` into
    every one of its 14 call sites with zero per-call-site changes needed. `needBrand()`/
    `brandPreamble()`'s 8 remaining producer call sites (Video, PR, Social, department heads, campaign
    lead, analytics lead) all pass the bypass explicitly.
  - `_brand_line()` (image/video prompt phrase) redesigned to accept `brand`/`brand_mode` instead of
    always calling `resolve()` itself; its 6 callers updated, `/posm-scene`'s logo instruction skipped
    outright in General mode rather than asking for "a brand"'s logo (nonsensical).
  - `producers._ctx()` (POSM/Onground's shared context builder) defaults `brand_mode` from the bound
    house, skips the recurring-character lookup when General.
  - `/posm-image`/`/posm-scene`/`/scene-still` all skip their reference-image lookups **entirely** in
    General mode, matching the plan's own stated design — pulling any brand's pack/cast for unbranded
    work would be worse than pulling nothing.
  - **A real bug found and fixed mid-build**: `library.items()`'s `brand=""` means *"caller doesn't
    filter"* (backward-compat default), not *"brand-agnostic only"* — passing empty string for General
    mode would have silently returned every brand's assets unfiltered, reproducing the exact bug this
    whole project exists to close. Fixed via a sentinel value (`"general-mode"`, a string no real brand
    will ever match) wherever General-mode callers need `posm.gate()`'s honest-zero-count behavior
    without bypassing its person-hallucination safety check (a different, non-brand concern that must
    still apply).
  - **A real data-corruption incident, caught by compile-checking before moving on**: one edit
    introduced two literal NULL bytes into `main.py` (a `" general "` string literal somehow saved with
    its spaces as `\x00` — cause unclear, isolated to that one edit, not reproduced elsewhere). Caught
    immediately by `py_compile` failing with `SyntaxError: source code string cannot contain null
    bytes`, fixed with a byte-level patch, then swept **every** touched backend file for null bytes
    before continuing. Lesson: always `py_compile` (or byte-scan) immediately after an edit with an
    unusual literal, don't wait for a batch check at the end.

## Not yet built

- **Stage 5 — Plan.** Not started. Same shape as Strategy: `brand_mode` field on plans, skip the
  claims-proof-gate check when General (report "no brand attached, nothing to check claims against"
  rather than silently passing or failing), pill on the plan screen.
- **POSM's `/posm-assemble`/`/posm-artwork`/`/posm-print`** (the downstream compositing/export steps,
  as opposed to `/posm-image`'s fresh generation) still call `library.reference_url(..., brand=_gen_brand)`
  unconditionally — no General-mode branch built for these three yet. Lower priority: they operate on
  an already-generated hero image, not fresh brand-fact generation, but still worth closing.
  `/posm-artwork`'s own `brandprofile.resolve()` call is also still the blind, no-docs form.
  Note the `brand=""` empty-string gotcha (see above) applies here too if this gets built without care.
- **Explicit `cast_id`/`pack_id` overrides in `/posm-image`/`/scene-still`** are not brand-ownership
  checked even in Grounded mode (a caller naming a specific id bypasses the filter entirely) — a
  pre-existing gap, not introduced by this project, lower priority than the automatic-fallback bug this
  project targets.
- **Existing library items have no `brand` tag** (the field didn't exist before Stage 1) — until
  someone tags them, they remain visible to every brand's Grounded generation (the safe default for
  the transition), which also means Stage 4's General-mode "skip lookups entirely" can't yet be
  compared against a real tagged multi-brand library in live testing tomorrow. Worth a manual tagging
  pass, or accept that early live tests will show "no reference available" for General mode regardless
  (which is at least honest, just not a full proof the filter itself works end-to-end with real data).

## Testing checklist for tomorrow (12 Sep)

1. Restart the server fresh (`--reload` doesn't reliably pick up backend edits in this environment —
   confirmed repeatedly this session; always kill and restart manually, verify via `/health` + a clean
   startup log before trusting any result).
2. Click through the header's new Grounded/General pill from at least one of each: Social, Video, POSM,
   On-ground, PR. Confirm the toggle visually updates and persists across screen navigation within one
   session (it's a single shared `producerBrandMode`, not per-screen, so it SHOULD carry over — verify
   that's the experience the user actually wants, since it wasn't explicitly re-confirmed after the
   "one tab" reframing).
3. Generate one real piece of text in General mode (small, cheap — a single social caption) and read
   the actual output for brand leakage, the same way Stage 3's `/house-prompt` comparison did.
4. Generate one real image in General mode (POSM hero or a scene-still) and confirm no reference image
   was pulled (check the response's `refs_used`/`has_cast` fields, not just that it didn't error).
5. Switch back to Grounded on the same screen mid-session and confirm the NEXT generation correctly
   regrounds (no stale General-mode leftover state) — mirrors the switchBrand staleness testing pattern
   already proven this session.

## Related

[[brandprofile-active-fallback-bug-class]] (if written) — the original `resolve()` fallback pattern
this project's Stage 1-4 work is the completion of. The hot-reload gotcha hit repeatedly today
(4+ times) is already covered in `CLAUDE.md` itself ("backend edits need a server restart... despite
`--reload` being set") — no separate memory needed, just keep obeying it.
