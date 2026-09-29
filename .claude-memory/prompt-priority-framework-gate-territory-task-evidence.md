---
name: prompt-priority-framework-gate-territory-task-evidence
description: "Gate/Territory/Task/Evidence prompt-priority framework built for producers, then wired the same way into Brief/House/Idea Platform/Campaign/Plan — shipped 29 Sep"
metadata:
  node_type: memory
  type: project
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-09-29T10:04:26.415Z
---

**SHIPPED 29 Sep, pushed to `master` (commit `de5840e`), Render deploy triggered.** Full design doc, evidence
and per-layer tables: [Gate, Territory, Task, Evidence artifact](https://claude.ai/artifact/Ts878VDEvcGHmU8MWHKtuo)
— the durable record, kept current rather than duplicated here.

**What it is:** a shared six-role vocabulary (Gate / Territory / Task / Evidence / Register / Steer) for what
goes into a generation prompt and which input wins when two disagree. Built first for the producers
(`producers._ctx()`, `prompts.system_for()`), then the same lens turned upstream onto Brief, Messaging House,
Idea Platform, Campaign and Plan.

**Real bugs found and fixed along the way** (not just the framework):
- `prompts._resolve_house()`/`plan_channels_block()` read brand profiles by `.get("brand")`, which only ever
  exists on a HOUSE dict — profiles carry `.name`. Silently returned `""` for every real call since this code
  existed; `house_block()`/`platform_block()`/`plan_channels_block()` had never actually reached Social/Video.
- Same functions also picked a house/plan by guessing from a brand-name string with no house/campaign scoping
  — confirmed live as the cause of a "South India" line landing on a "Heritage Maharashtra Push" post. Fixed
  by threading an explicit `house_id` through `complete()`/`system_for()`.
- The bridge script every `/app` page injects (`main.py`'s `_HEAD_INJECT`) forwarded only `messages` to
  `/complete`, silently dropping `execution`, `house_id`, the three toggles, `brand_mode` — a long-standing,
  pre-existing transport bug, not introduced this round. Fixed to forward the whole payload.
- `house_block()`'s RTB read used non-existent layer ids (`ertb`/`frtb`).
- A source-tag whitelist (`"brief"|"library"|"user"`) was duplicated in five places
  (`strategy.generate()`, `ideas.py`, `plan.py`, `docs.py`, `app.dc.html`'s badge lookup) — extended
  consistently to a new `"research"` tag as part of Phase 2 below.
- Plan's `channels`/`phases` layers read the House's **retired** `medium` node for "what the brand says per
  medium" instead of the Idea Platform's live `expressions` — empty for any house worked on since the
  retirement.

**Four upstream phases, all built + verified + shipped:**
1. Plan gets `THE BRIEF` directly (`plan.py`, all 7 layers) + Channels reads the live platform expressions.
2. RTB layers actively validate candidates against research synthesis and tag `source:"research"`
   (`strategy.py`, `ideas.py`, `plan.py`, `docs.py`, `app.dc.html`).
3. Core/Emotional/Functional messages get a shared `_transition_block()` (CB→DB attitude shift + NeedScope
   territory, computed once) — `strategy.py` + a new `briefstore.py` canon field (`needscopeTerritory`).
4. `campaign.draft()` gains a real `voice_block()` call (was missing) + the house's core message as an
   ambient, platform-subordinate Territory input.

**Verification discipline used throughout:** `py_compile` + `selfcheck.py` after every edit; several phases
also verified with a real live generation through the running local server (temporarily patching a real test
house's brief for CB/DB/NeedScope, then restoring it byte-for-byte from a backup afterward — no residual test
data left in any tenant file); `tools/smoke.py` run against the committed tree before pushing.

**Deliberately NOT touched — still open:** Brief (`brief_ai.py`) never calls `brandprofile.voice_block()` at
all — no Gate, no brand profile, no Brand Essence reaches Brief generation. The screen's own Independent-mode
banner overclaims here (implies Grounded mode uses the brand profile; it doesn't, in either mode). A real gap,
scoped and evidenced in the artifact, not part of this round's build.

**Commits** (on `master`, in this order): `7934be9` (producers rebuild), `7d6dc28` (upstream phases 1-4),
`de5840e` (frontend: PR house-proof card + research-source badge). See [[change-discipline-working-agreement]]
for the process followed; see [[round31-queue]] item 20, now superseded by this broader rebuild.
