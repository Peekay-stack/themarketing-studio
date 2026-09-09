---
name: brand-character-skill-thread
description: "The brand-character skill + Sujatha character work (7 Sep) — skill doc complete but unwired, Sujatha v2 is an unapproved candidate; where it stands and the next steps"
metadata: 
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-08T11:59:21.047Z
---

Done 7 Sep 2026 (Sunday), same session as the landing-page work, and **not otherwise recorded** — no
round entry in [[studio-work-inventory]]. All files untracked in git as of 8 Sep.

## What exists

- **`api/character_skill/SKILL.md`** (236 lines, 7 Sep 21:17) — a complete skill in the house
  `*_skill/` pattern, named `brand-character`. Persona-vs-character distinction, the signature visual
  hook, six approval tests, the full method (pen portrait → visual brief with a Type/Look split →
  region as load-bearing → cast lock as two lists → raw-then-styled casting → audition turn →
  pressure test → explicit approval), image/video prompt craft, per-producer expression, ensemble
  casting. Reads as finished, same depth/voice as `posm_skill/SKILL.md`.
- **`Heritage_Brand_Character_Sujatha_v1.md`** (OPUS root, 7 Sep 20:19) — first application to
  Heritage Foods. Hook: "the new poured into the old" (pack poured into a dented brass heirloom
  davara). **Failed test 3** — specific at the cost of presentable (burn scar, un-slim build,
  unsmiling mouth read as unglamorous, not distinctively specific).
- **`Heritage_Brand_Character_Sujatha_v2.md`** (OPUS root, 7 Sep 21:05) — supersedes v1. Hook swapped
  to **Route A: the unhidden silver streak** (recognition via styling/grooming, not a prop); davara
  demoted to non-load-bearing recurring prop, the pour recorded as Route B. Glam skewed up per direct
  correction (toned/fit, camera-ready, real makeup/hair craft, scar removed, ownable bone structure
  kept). Region made load-bearing (Telugu, Hyderabad/Telangana, South Indian features — explicitly
  not "generic pan-Indian"). Added full visual brief, a 6-row expression-range table, two base image
  prompts (morning kitchen + dinner saree — the saree frame exists to verify the fit claim the
  kitchen framing hides), per-frame negatives, audition-turn spec (§7), 4-shot pressure-test
  checklist (§8), ranked open `[assumed]` items (§11), approval table (§12).

## Status

- **Skill doc: complete.** `character_skill/SKILL.md`. Not packaged as a standalone Claude Skill —
  same status as the other five unpackaged `*_skill/` modules flagged in [[account-migration-plan]].
- **Backend: BUILT 8 Sep (this session), verified on a disposable tenant, no real tenant touched.**
  - `api/character.py` — store (round-92 `_dir()` pattern) + skill-reader + `draft()` (via
    `jsonout.ask_json`) + `derive_state()` state machine (draft→candidate→audition→pressure→
    approved→retired) + the six-test gate. `can_approve()` returns a full checklist of what's
    still missing; `approve()` refuses without a named person AND without all six tests passing.
    `cast_lock_block(doc)` is the identity-only paragraph a producer's cast-lock will thread in.
  - `tenancy.KINDS` gained `"character"`.
  - 12 thin routes in `main.py` after `/actuals-remove`: `/characters`, `/character/{cid}`,
    `/character-draft`, `-save`, `-route`, `-test`, `-audition`, `-pressure`, `-reference`,
    `-approve`, `-retire`, `-remove`. `main` imports clean, 293 routes.
  - 9-check functional test passed (round-trip, state transitions, approve refusals, full-pipeline
    approve, `for_brand`, ordering, `cast_lock_block`, retire). All uncommitted.
- **Skill file updated 8 Sep** with the logic + learning (user's explicit call — "build the logic
  and learning in the skill file", chosen instead of seeding Sujatha as data): a new subsection
  "The failure that actually happens: specific *instead of* presentable" (the v1→v2 lesson as a
  rule — keep ownable structure, re-cast glam up, make region load-bearing, don't soften the hook);
  a "Know which stage the character is at" block documenting the draft→candidate→audition→pressure→
  approved state machine and the approval gate the code now enforces; and an "identity-only block"
  paragraph in "Expressing it" describing what a producer's cast-lock receives.
- **`ASK_DESIGN_60.md` written 8 Sep** — the Ground Truth frontend panel handover. Full contracts
  for all 12 routes + the document shape + panel spec.
- **Frontend panel MERGED & browser-verified 8 Sep.** Design's handback (`app.dc.html` at OPUS root,
  Sep 8) was built on a **stale base** (21,006 lines vs the live 23,910 I specified) — it was missing
  Carousel/Priority-geography/Video-plan-binding, so it was NOT adopted whole. Instead: extracted
  Design's 6 additive hunks (panel markup + `bagCharacters` + `loadCharacters` wiring + state keys +
  the CDU hook + bag spread, ~545 lines) and `patch`-applied them onto the live
  `api/frontend/app.dc.html`. **One `patch --fuzz` mis-placement caught in the browser**: the
  `if (screen === 'library') this.loadCharacters();` line landed inside the state-object initializer
  → `SyntaxError: Unexpected token '==='`, whole DC logic class dead. Fixed by hand (moved it into
  `componentDidUpdate` beside `loadMade()`). checkfe clean (sc-if 1024, sc-for 398, div 3204, 917
  members, 23 bags), pure LF preserved, DC script `new Function()` parses, panel renders (empty
  state + count + draft form), `loadCharacters` fires brand-scoped, a real `/character-draft`
  round-tripped a full `candidate`-state doc (11 approval blockers, cast_lock_block present) — test
  characters deleted after, `default/character/` left empty. **Uncommitted.**
  Merged file was verified on a throwaway server on **:8010** (the standing 8000 server is pre-session
  and has NOT been restarted — it lacks the `character.py` routes; user must restart it).
- **WIRED INTO GENERATION 8 Sep** (uncommitted). New `character.for_prompt(brand)` — returns the
  approved character's `cast_lock_block()` with a "any person shown IS this character" header, or
  `""`. Threaded in at two funnels:
  - `prompts.system_for()` — after `voice_block`, gated `"" if surface is BRIEF` (same guard as
    `spine`). Covers **Social posts, Social carousel, Video script** (all reach `/complete`).
  - `producers._ctx()` — resolved from the original house/brief before the use_* switches null them.
    Covers **POSM, POSM carousel, Onground**.
  Verified: an approved character's block appears in `system_for` and `_ctx` output; suppressed on
  the real brief-builder surface; `import main` clean (no circular imports — `producers` now imports
  `brandprofile`+`character`, `prompts` imports `character`).
- **Still NOT wired**: the character's `reference.library_id` as the actual cast *reference image*
  in the image/video routes (`/scene-still`, `/posm-image`, `/cast-reference`) — those resolve
  `kind:"cast"` library items directly; making an approved character auto-supply its reference frame
  is the next piece. Also: candidate/audition image-video generation.
- **`ASK_DESIGN_60_REPLY.md`** written 8 Sep — tells Design the base was stale, the panel is merged
  onto live, the mis-placed hook, and to base ASK_DESIGN_61 on the merged `api/frontend/app.dc.html`.
- **Sujatha v2: CANDIDATE, Route A, NOT APPROVED.** "Audition turn not run, pressure test not run,
  NOT APPROVED." Route A "pending confirmation." No images generated. Not yet imported into the new
  `character` store as a structured document — the two `.md` files at the OPUS root are still the
  only copy.

## Next steps (decision points for the user)

1. Confirm Sujatha's hook route — A (silver streak, recommended) / B (davara pour) / C (carriage).
   Everything downstream forks here.
2. Validate the four `[assumed]` items in v2 §11 against segmentation data or a small qual check —
   most weight on whether the segment reads unhidden grey as confidence or as neglect.
3. Run the casting pipeline in order — 2–3 raw Polaroid candidates → pick on bone structure → style
   the chosen one → audition turn (video) → pressure test (§8's four shots) → named-person approval.
   Needs real image/video generation; nothing started.
4. Decide whether to wire the skill into the studio: a "Brand character" Library concept that
   Social / Carousel / POS / Video cast-locks point at (skill §9 already specifies each producer's
   use). Real build — module + route + frontend + Library slot beside pack/logo/cast, ~POSM
   asset-panel size. Also fills the "Video has no character-sheet document layer" gap in
   [[studio-save-audit-doc]]. Relates to [[pr-sales-enabler-producer-roadmap]] (structural parity).
5. Housekeeping — the two Sujatha briefs sit at the OPUS root, not under a tenant; if the studio is
   to own brand characters they belong under `api/tenants/default/`.

**Why:** the skill doc is real, polished work that looks done but is inert — easy for a fresh session
to either miss entirely or assume is live. The v1→v2 reasoning (why the hook changed, the glam
correction) is not in any file's history and would be re-litigated otherwise.

**How to apply:** before touching brand-character anything, check whether the user has confirmed
Sujatha's route and whether the skill has been wired — do not assume either. Treat v2 as the current
brief, v1 as superseded. If asked to bring it into the product, it is a real build, not a wiring fix.
