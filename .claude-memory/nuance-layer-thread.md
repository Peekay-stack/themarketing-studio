---
name: nuance-layer-thread
description: "7 Oct: brand-agnostic done properly = a model-drafted, person-approved \"Nuance Read\" (not category families); plan written in NUANCE_LAYER_PLAN.md, nothing built, awaiting 4 decisions + go-ahead for the Phase 1 real-model test"
metadata:
  node_type: memory
  type: project
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-10-07T13:33:27.296Z
---

**Status (7 Oct 2026, parked by the owner, "pick it up again tomorrow"): PLAN WRITTEN, NOTHING BUILT.**
Full plan: `Heritage Marketing Studio/NUANCE_LAYER_PLAN.md` (repo). Evidence behind it: `BRAND_AGNOSTIC_AUDIT_OTHER_SURFACES.md`, `VIDEO_BRAND_AGNOSTIC_AUDIT.md`, tools `tools/scan_brand_signatures.py` + `tools/probe_brand_signatures.py`.

**Why it started:** the owner, after the audits, did not want "agnostic" to lose nuance (geographic: Bengali, Delhi, Assamese; audience; insight). I traced where nuance lives and how it enters prompts.

**Findings worth keeping:**
- Root cause: the profile's `category` and `market` are FREE TEXT, so no code can select on them; the `brandprofile.py` docstring promised "a lookup later" and it never came. So Heritage knowledge was written straight into code (milk-pack rules, kirana, "Indian FMCG", Video render/music defaults).
- Six ways nuance enters a prompt: profile -> `voice_block` constraints (clean); keyed tables (`geo` by state, `pr.TRADE_CATEGORIES` by category = exactly dairy/beauty/apparel/cement, `activation.FOOTFALL` by venue) but the profile never selects them; hardcoded system-prompt prose; worked examples in skills; render/music defaults in `main.py`/`filmaudio.py`; the model's own knowledge triggered by ONE sentence ("write for these places' own idiom", `prompts.py:218`).
- Code holds NO cultural idiom or festival data for any region; `geo.py` holds facts only (language ladders, gaps, census). `geo` already separates Assamese from Bengali (`principal_only`). Dev tenant: only Heritage has `states`/`languages` set, so the geo layer is inert for Kumkum/Loomwell/Sthir.
- All 11 `producers.VENUES` go to every brand ("VENUES YOU MAY USE"); `sales.CHANNELS` first six keys are tied to fixed screens (`SE_TABS`), so cement dealer credit / apparel MBO-EBO need a screen change + Design handover.
- `brief_ai.py` never calls `voice_block`, so Brief would not see any of this unless wired explicitly.

**Owner's decisions (7 Oct):** (1) nuance is per brand x line x audience, NOT per category family: dairy is family but ice cream/dairy beverage can be family or individual, high-protein is an individual (man or woman), cement can be family with a man leading or an individual man; the model must pick this up. (2) hand-written experimental content welcome, but the model must learn nuance itself from brand/category/geography/audience. (3) keep dated Indian benchmarks as sourced estimates. (4) India only for now, key designed for a second market.

**The design (replaces my earlier family-enum + playbook idea):** a "Nuance Read" with 7 fixed dimensions (consumption and roles, buying mode, route to market, proof and claims, product in use, occasions, place), free-text values, each statement tagged basis (profile/evidence/model knowledge) + unknowns + status; three scopes (brand, house/audience overlay, per-piece overlay), narrower wins; model drafts, person approves, only approved reads reach generation; hand-written reads for dairy/personal care/apparel/cement are calibration examples (always from a DIFFERENT category than the brand's, only inside the generator) and the acceptance test; place cards = `geo` facts + model-drafted, approved cultural layer. Heritage protected by seeding ITS read from today's hardcoded dairy text, then diffing real prompts before removing shared text (byte-identical no longer applies).

**Phases:** 0 store/schema; 1 PROVE THE RISKY STEP (generate reads for Heritage, Sthir, Kumkum, Loomwell + the owner's family/individual cases; needs real model calls = needs the owner's explicit go-ahead; nothing wired until the owner judges it); 2 wire into `voice_block`/`system_for`/`producers._ctx` + Brief; 3 retire hardcoded content one surface per commit; 4 place cards + occasions (Bengali/Delhi/Assamese acceptance tests); 5 Sales/Onground route archetypes + screens; 6 guard + learning loop.

**PICK UP HERE (8 Oct): four open decisions, my recommendations in brackets:** (a) unapproved read never injected [yes] vs tentative; (b) audience overlay at messaging-house level [assumed yes]; (c) evidence = profile + uploaded research only, or web research too; (d) where the read is edited [new "Nuance" section on the brand profile screen]. Then the owner's go-ahead for Phase 1. Per [[change-discipline-working-agreement]] this is a LARGE change: written plan approved first. Related: [[round31-queue]] (open owner-decision items from the audits), [[brand-grounding-modes-project]], [[prompt-priority-framework-gate-territory-task-evidence]] (the read needs Gate/Territory/Register roles).
