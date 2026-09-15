---
name: brand-grounding-modes-project
description: "All 5 stages built and live-tested (11-15 Sep 2026) — Brief/Strategy/Plan/Producers share one Grounded/Independent toggle so \"no brand attached\" is a real, honored choice instead of an accident. Architecture collapsed from 4 per-tab toggles to 1 after user testing; 5 rounds of testing feedback fixed, incl. a studio-wide stale-draft-on-toggle bug across every producer — see the testing log."
metadata:
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-15T05:53:00.903Z
---

**Start here for this thread**: `BRAND_GROUNDING_MODES_PLAN.md` (repo root) has the full technical
plan. **`BRAND_GROUNDING_TESTING_LOG.md`** (repo root) has every round of user-testing feedback and
its fix, prompt by prompt — see [[brand-grounding-testing-log]], a standing instruction to keep
appending to it. This memory is the status/continuity layer on top of both.

## Current shape (as of 12 Sep, after 2 rounds of user testing)

**One toggle, not four.** Started as four separate per-tab toggles (Brief/House/Plan/Producers each
independently switchable) per the original design call — collapsed to a single `producerBrandMode`,
shown once in the header next to the brand chip, after live testing showed two pills on the same
screen (the header's and a tab's own) disagreeing reads as broken, not as flexible. Full story in the
testing log's Round 2. The header's brand-switcher dropdown now also carries a real "Independent
work" row alongside the actual brands — picking it sets the mode without touching which brand is
server-side active; picking any real brand (even one already active) always snaps back to Grounded.

## Why this exists

Traced from the user's original bug report ("generating Parle G still writes Heritage") through three
rounds of fixes that session (`brandprofile.resolve()`'s active-brand fallback in three places,
client-name-override-class staleness in the header/settings flow) to a much bigger finding: the whole
app had **no way to say "this piece is deliberately not tied to any brand."** Every text generation
(`/complete`, the shared chokepoint nearly all producers use) and every image generation fell back to
whichever brand was globally active, full stop. Separately, traced that **Ground Truth (the reference
library) and Learning (corrections/retrieval) were architecturally brand-blind** — no `brand` field on
library items at all, tenant-wide only for learning — so even *correctly* grounded work could silently
pull another brand's pack shot or house rules in this account's 5-brand tenant (Heritage Foods, Kumkum
Beauty, Loomwell, Parle G, Sthir Cement).

## Build status — all 5 stages done

- **Stage 1 — Ground Truth brand-scoping.** DONE, live-verified. `library.py`/`learning.py` gained a
  `brand` field + filter on every read/write function (additive — empty `brand` keeps old tenant-wide
  behavior). `made.py`'s `list_entries()` gained the same filter. ~15 real generation/status routes
  wired across `main.py`/`posm.py`/`shelf.py`/`continuity.py`.
- **Stage 2 — Brief.** DONE, live-verified both directions of the save round-trip.
  `briefstore.put()`/`/brief-save` carry `brand_mode`; `needBrand()`/`brandPreamble()` gained an
  `allowGeneral` bypass reaching `voice_block(None)`'s honest "don't invent a brand" instruction.
- **Stage 3 — Strategy/Messaging House.** DONE, live-verified with a real before/after `/house-prompt`
  comparison (Independent → honest no-brand instruction, zero leakage; Grounded Parle G → real brand
  facts, same test). `strategy.prompt_for()` checks `house.get("brand_mode")` before ever calling
  `resolve()`. `/house-generate`'s T1/T3 retrieval and locked-copy skip outright for Independent
  houses.
- **Stage 4 — Producers (`/complete` + image generation).** DONE, **live-tested 12 Sep morning**: real
  `/complete` calls in both modes came back correctly contrasted (Independent → "I don't know, no
  brand profile has been provided"; Grounded → "Heritage Foods, a dairy brand..."); a real
  `/scene-still` call in Independent mode came back `from_reference:false` with no reference pulled.
  `prompts.system_for()` skips `resolve()` entirely for `brand_mode="general"`. `_brand_line()`
  redesigned to accept `brand`/`brand_mode` instead of always resolving itself.
  `producers._ctx()` defaults from the bound house, skips character lookup when Independent.
  `/posm-image`/`/posm-scene`/`/scene-still` skip reference-image lookups entirely in Independent mode.
- **Stage 5 — Plan.** DONE, live-verified with the same before/after `/plan-prompt` method as Stage 3.
  `plan.py`'s `prompt_for()` and `set_brand_mode()`, new `/plan-brand-mode` route, `/plan-generate`
  skips T1/T3/locked-copy for Independent plans.

**Two real incidents caught mid-build, both by compile-checking immediately rather than batching:**
(1) `library.items()`'s `brand=""` silently means "don't filter," not "brand-agnostic only" — fixed
via a sentinel value. (2) One edit corrupted `main.py` with two literal NULL bytes (an odd string-
literal encoding fluke) — caught by `py_compile` right after the edit, fixed, then swept every touched
file for null bytes.

**Then, after shipping Stage 4/5, five rounds of real user testing found and closed further gaps** — a
completely separate code path (`/brand-brief-draft` → `brief_ai.py`) that had never been wired to the
toggle at all; the 4-toggles-not-1 architecture problem above; the IMC screen never auto-filling
Brand/Category from the active profile (Round 3); Round 4 (15 Sep), two bugs — `im.draft`/`status` not
clearing on toggle change (stale "Redraft" label after switching to Independent), and `pickBrief`
silently syncing the master toggle to a picked brief's own stored `brand_mode` (nearly every brief
predates this feature and reads `grounded`, so pulling one while Independent snapped the toggle back).
Fixed by clearing draft state on every toggle flip, and by removing `pickBrief`'s sync while
deliberately keeping `enterHouse`/`enterPlan`'s (those open an already-decided document; a picked
brief is just reference text for something not yet created).

**Round 5 (15 Sep, same day):** the user asked for an audit of the other producers, then "fix all of
them the same way, one pass... default on all tabs, sub tabs and layers." Round 4's stale-draft bug
turned out to be the studio's *default* shape, not a one-off — audited and confirmed present in Social
(`posts`), Carousel (`routes`/`concept`/`slides`), Video (`videoConcept`/`fullScript`/every
department's `shoot` card/`sceneFrames`/cast reference), POSM (`pm.options`/`scamps`/`images`/every
rendered piece), Onground (`og.ideas`), PR's release sub-tool (`release`/`rel`/`relStatus`), plus two
upstream surfaces not in the original ask — the Idea Platform (`idea.line`/`options`) and the guided
Brief Builder used by Media/Digital/Packaging/PD/PR-format (`state.brief`). Fixed all of it in one
pass in `setProducerBrandMode`: AI output clears, whatever the person typed stays. A first pass reset
`posm`/`og`/`idea` to `null` outright — live-testing the fix itself (not the user) caught that this
also deletes real typed input living in the same namespace (`og.idea`, the person's own activation
sentence); rebuilt as field-by-field clears instead, re-tested, confirmed fixed. Live-verified end to
end with real generation calls on Social and Onground (including the regression), then Video and POSM
on a follow-up request (Video: real concept generated, toggle-cleared, typed brief survived; POSM:
real key-visual route generated, toggle-cleared, Step 2 correctly re-locked, typed brief survived),
then Carousel and PR-release on a further follow-up (Carousel: three real routes generated,
toggle-cleared, typed brief survived; PR-release: real press-register copy drafted for a live sheet,
toggle reset the whole sub-tool to its pre-start "No release on this sheet yet" state — not just
blanked fields — and a fresh Independent-mode start came back genuinely empty), then the guided Brief
Builder on a final follow-up (real AI-drafted Background/Business-objective copy for a Media-format
brief cleared on toggle, while Deliverables/Budget correctly reverted to their exact `formatDefaults`
template seed text rather than blanking, and the typed ask survived). Only the Idea Platform itself
remains code-reviewed only — same pattern, static checks passed, not separately live-tested. Deliberately left
untouched, not silently skipped: `state.campaign` (the Idea Platform's own ladder/roles/posts/video
hub — server-persisted like House/Plan, needs that same treatment, not a client reset) and House/
Plan's own per-layer generated-but-uncommitted suggestion rows. Full detail: see
[[brand-grounding-testing-log]] and `BRAND_GROUNDING_TESTING_LOG.md`.

## Not yet built / lower priority, still open

- **POSM's `/posm-assemble`/`/posm-artwork`/`/posm-print`** (downstream compositing/export, as opposed
  to `/posm-image`'s fresh generation) still call `library.reference_url(..., brand=_gen_brand)`
  unconditionally — no Independent-mode branch built for these three yet. Lower priority: they operate
  on an already-generated hero image, not fresh brand-fact generation. `/posm-artwork`'s own
  `brandprofile.resolve()` call is also still the blind, no-docs form. The `brand=""` empty-string
  gotcha (see above) applies here too if this gets built without care.
- **Explicit `cast_id`/`pack_id` overrides in `/posm-image`/`/scene-still`** are not brand-ownership
  checked even in Grounded mode (a caller naming a specific id bypasses the filter) — pre-existing,
  not introduced by this project, lower priority than the automatic-fallback bug this project targets.
- **Existing library items have no `brand` tag** (the field didn't exist before Stage 1) — until
  someone tags them, they stay visible to every brand's Grounded generation (the safe default for the
  transition). Worth a manual tagging pass at some point.
- **The IMC Brief prompt textarea is never cleared** when switching to Independent (only Brand/
  Category are) — a deliberate choice (it's the person's own analysis request, not a brand fact),
  flagged to the user, not yet confirmed as final either way.
- Nothing in this feature has been committed or pushed as of 12 Sep — still sitting local pending the
  user's own review.

## Related

`CLAUDE.md` already covers the hot-reload gotcha hit repeatedly this project ("backend edits need a
server restart... despite `--reload` being set") — no separate memory needed, just keep obeying it.
