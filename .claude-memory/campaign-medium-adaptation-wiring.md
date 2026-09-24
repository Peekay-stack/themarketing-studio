---
name: campaign-medium-adaptation-wiring
description: "The campaign-level 'adapt the platform's expression for this medium' wiring fix — backend + frontend, feature-complete and locally verified, not deployed"
metadata: 
  node_type: memory
  type: project
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-09-24T18:08:01.940Z
---

24 Sep: built the fix scoped after critically evaluating the user's own marketing-strategy framework
(SMP → CACB/DADB → house → Idea Platform → **Campaign** → medium adaptation) against the real code. The
gap found: Campaign and Expressions were parallel children of an adopted Idea Platform, not sequential —
`producers.stands_on()` read `platform["expressions"][kind]` directly, and a campaign's own fields were
never read by any producer. Locked design (user confirmed): a campaign picker at execution creation
(option B, for flexibility), wiring-only — explicitly NOT touching the RTB emotional/functional split,
bridge depth, core-as-synthesis, or campaign-level CACB→DADB scoring.

**Built and live-verified, end to end, with real data (not just endpoint tests):**
- `execution.brief_from()` now accepts an explicit `campaign_id` in `sel`, resolved like `plan` already
  is (empty still falls back to the platform's latest campaign — unchanged default, confirmed by testing
  both with and without an explicit pick).
- `campaign.write_expressions()` — new, real ADAPTATION prompt (not `ideas.write_expressions()`'s fresh
  generation): reads the platform's own per-medium line and narrows it to the campaign's insight/
  resolution. Verified live: real Anthropic output, genuinely campaign-specific per medium, not a
  restatement of the platform's line.
- `campaign.express()`/`express_many()` setters, mirroring `ideas.py`'s pattern exactly.
- New routes `/campaign-express` (store) and `/campaign-express-draft` (generate), mirroring
  `/platform-express`/`/platform-express-draft`.
- `producers.stands_on()` gets a new TOP-PRIORITY check: a bound campaign's expression wins over the
  platform's own, source label `"the campaign, adapted for X"`. Threaded through all 8 call sites in
  `main.py` plus POSM/Onground's internal generation (`key_visual`, `activation_ideas`) via their
  existing `exec_brief` param — no new params needed there.
- Social/Video's `prompts.py` path: `_execution_block()` (not `stands_on()`) surfaces the campaign's
  adaptation, inheriting that block's existing "where the two differ, this wins" precedence over the
  platform block above it — verified via direct `prompts._execution_block()` call with a real execution id.
- `execution.stale_because()` now catches a bound campaign being dropped or its expression rewritten —
  same staleness-bug class fixed twice earlier in [[brand-grounding-modes-project]], closed before it
  could reopen here.
- Frontend: a "Which campaign" picker on both Execution and Video brief forms (optional, defaults to
  none), added to the existing generic `xFields`/`vxFields` array — no new markup template needed.
- Frontend: a full "Campaign expression by medium" panel on the Idea Platform screen (Strategy → Idea
  platform, below the campaign's own grid) — 8 rows (platform's 7 + PR, since PR executions read a
  campaign expression too), each with a textarea + debounced auto-save + "Rewrite this one", plus one
  "Adapt these for me" bulk button. Mirrors the platform's own "Expression by medium" panel one layer
  down, same interaction pattern.

**Two real bugs found and fixed during this build, both live-verified:**
1. Onground's quote-box label hardcoded "the platform this would be built against" even when the actual
   source became a campaign — read as "the platform... — from the campaign, adapted for X". Fixed to
   "what this would be built against".
2. The campaign panel's "Adapt these for me" (bulk) button silently also generated and PERSISTED a
   ninth expression (`media`) that the panel never shows or lets anyone edit, because
   `campaign.write_expressions()` defaults to every key in `media.EXPRESSIONS` when none are named, and
   the bulk call wasn't naming the real eight explicitly (only the single-row rewrite was). Fixed by
   always sending the explicit eight; re-verified live that `media` stays empty after the fix.

**Status: feature-complete, fully local, nothing deployed.** User will test on local tomorrow (25 Sep).
[[round31-queue]]'s artifact still lists this as open — needs a republish once the user has tested it.
