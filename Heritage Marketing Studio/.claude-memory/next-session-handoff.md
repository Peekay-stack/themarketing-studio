---
name: next-session-handoff
description: "START HERE tomorrow (written end of 26 Oct 2026). Where the video work stopped, the one urgent deadline (17 Nov), the engine decision the owner has made, the exact next step awaiting their go-ahead, what is live vs queued, and the gotchas."
metadata:
  node_type: memory
  type: project
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-26T16:15:46.983Z
---

**Written at the end of 26 Oct 2026. Read this before anything else, then [[video-edit-consolidated-build-list]] (the master list, with every finding appended by date) and [[change-discipline-working-agreement]].**

## Where we stopped
The owner reviewed the engine trial and concluded: **pick ONE video engine and optimise the prompt for it** (the engines converge on a good starting frame; the differences are in how the prompt is read). I recommended **Gemini Omni 1.1 Flash**; the owner asked "is Omni good to go" and I answered **yes, to build for, with 3 conditions** (below). **Nothing was built for the engine switch.** The owner said "we stop now" — no open question in flight except the go-ahead for step 1.

## The deadline that matters
- **Google's Veo preview models are gone from the Gemini API** (HTTP 404 since 23 Oct 04:48 UTC, verified in Render logs; the 20s cutdown on 26 Oct 04:34 UTC was rendered on the fal fallback). So ALL renders since 23 Oct ran on **fal-hosted Veo 3.1**, whose endpoints carry **"will be deprecated on November 17, 2026"** (no replacement named). Both of our video routes can be gone in ~3 weeks. The studio UI still labels tiers "Veo 3.1 Lite/Standard" with stale Google cost estimates.

## NEXT STEP (waiting for the owner's go-ahead)
**Step 1, ~ $2-3 of credit:** (a) run trial scenes A and B through IMPROVED hand-written prompts on **Omni 360p drafts** (≈ $0.17 each) to see whether the prompt is the lever: scene B should show him actually DRINKING (not a toast; my old prompt said "lifts it"), no speech (add "no speech, no music, kitchen ambience only"), pouch proportions stated, expression specified, scene held; (b) a **concurrency test**: 6 parallel Omni drafts (≈ $1) because Omni's rate limits are NOT published. THEN build: (1) **Omni path** in `api/gemini.py` — POST `https://generativelanguage.googleapis.com/v1beta/interactions?key=`, model `gemini-omni-1.1-flash`, `input` = [{type:image, data:<b64>, mime_type}, {type:text, text}], `response_format` = {type:video, aspect_ratio:"16:9"|"9:16", resolution:"360p"|"720p"|"1080p"|"4k"}; response `steps[].content[]` item type `video` with inline base64 (<4 MB) or a file URI (poll Files API) for larger; no duration parameter (put "About N seconds." in the prompt; measured 5.01 s); output carries an audio track (strip it); map the studio's Draft tier → 360p (≈ $0.034/s) and Final → 720p (≈ $0.10/s); replace the dead `VIDEO_MODELS` Veo IDs; fix the stale tier labels/cost estimates in `app.dc.html` (~17396, `qualityNote`). (2) a **video-prompt compiler** with per-engine adapters (see the 26 Oct owner-reading block in the master list). (3) a **frame QA gate** for the pouch shape. Keep a **second engine behind the same adapter** (Kling 3.0 on fal, or MiniMax H3 Max).
**Omni conditions:** concurrency/rate-limit test; prompt-tuning proof on scenes A/B; second engine behind the adapter. **Omni limits:** 16:9/9:16 only; duration steered by prompt; audio comes with it; image editing of minors unsupported in EEA/CH/UK (a boy is in the Heritage scenes — owner to decide if that matters for the audience); no documented audio-off switch.

## Live vs queued
- **LIVE (verified deploys):** `8f750c8` B1 (optional film-wide "Camera & lens" note, off by default, reaches frames + production AND cutdown renders, saved with the film) + B2 (spoken line removed from the video prompt) + shot-variety rule; `53b45f4` B7 (opt-in "land the music's lift on the turn", never heard on a real track). Everything after is memory/tools only.
- **QUEUED for "after the weekly quota resets" (owner said):** [[cutdown-fidelity-build-plan]] (Edit-room cutdowns lose the pack: no frames → text-to-video; fix list A1-A7; open decision D1: reuse rendered clips + frames for new scenes) and [[video-generation-upgrade-queue]] (B3 reference tagging now UNBLOCKED by the Kling O1 result, B4 location sheet, B5 takes/re-roll, B6 negative-prompt-vs-label test). The owner said "start with the video build, we will pick the editor later" — so the ENGINE/PROMPT work comes before the Edit-room cutdown work.
- **Parked, do NOT act:** Remotion skills are downloaded (`Downloads\remotion-skills`) but NOT installed — owner is experimenting first; VN-inspired editor extras (auto-captions for imports, fades, music-to-beat) are candidates only.

## Findings to remember (details in the master list)
- **The trial bypassed the studio** (direct API calls with my own prompt), so B1/B2 did not apply to those clips. **The studio's own frame-animation prompt has problems** found by capturing it: whole brand paragraph with hashtags pasted in, leftover timecode/punctuation clutter, editing-language role text, a list of DON'Ts written for Veo, no audio line, no precise verb/end state.
- **The rectangular pouch is a FRAME-stage problem:** printed panel long:short ratio real pack 1.30 vs scene-B frame 1.74 (A unreliable, tilted). `packscene.pack_clause` says "proportions" with no numbers; the library stores no pack dimensions.
- All 7 engines kept the real pouch in both scenes; Omni drifted in scene B (plain wall, crest on the shirt); Wan zoomed to a blur in A; Seedance too slow (348-512 s) and refuses photoreal faces in REFERENCE mode only; Kling O1 reference-to-video PASSED (each element needs ≥1 `reference_image_urls`).
- Prices verified: Omni 720p ≈ $0.101/s and 360p ≈ $0.034/s (MEASURED tokens: 28,960 vs 9,655 per 5 s); fal Kling v3 Pro $0.112/s silent; Seedance 2.0 Fast $0.2419/s; Runway $0.01/credit (Gen-4.5 12 cr/s, Turbo 5). UNVERIFIED: MiniMax (reported $0.18/s official at 768p), Kling 4.0, Wan, Luma. **fal returns no cost per call** — the owner should read the fal dashboard for the ~22 paid trial clips.

## Owner's open items
Watch the clips and give picks (https://claude.ai/artifact/TwYR3GaERo9fmbkPhC4sK5); check the fal dashboard spend; decide whether the Omni minors restriction matters; give the go-ahead for step 1; D1-D3 in the master list.

## Where things are
Artifacts: comparison https://claude.ai/artifact/TwYR3GaERo9fmbkPhC4sK5 · engine playbook (now with Part C) https://claude.ai/artifact/TQ4v3So79uCASppWBmkiNF · build-list page https://claude.ai/artifact/3oiRZQU67HTaeEg8hfwg9A. Trial media: `C:\Users\punie\Downloads\engine-trial\` (clips, refs, frames, comparison sheets). Trial scripts: **`tools/engine_trials/`** in the repo (the session scratchpad is temporary — do not rely on it).

## Gotchas
- `main.py`, `filmaudio.py`, `filmvoice.py` are **CRLF in the working tree** (index LF, `autocrlf=true`); `app.dc.html` and `filmscript.py` are LF. The Edit tool preserves CRLF; for scripted patches normalise to LF, assert exact counts, write back uniform CRLF. Write scripts to a FILE with the Write tool, not a long inline heredoc (the shell mangled quoting once).
- Render logs: the project `render` MCP is DNS-dead; use the claude.ai Render connector (`ToolSearch select:mcp__2edd1d5f-d2e4-4489-a310-3e413b7a9532__list_logs`), service `srv-dagfb76k1f9s73cmr8og`, workspace `tea-dageqc8u01pc73fi55c0`.
- Audit rule ([[audit-sibling-entry-points-not-just-my-diff]]): diff every sibling entry point (`produceVideo` vs `renderCut` vs `/rescore`, Google vs fal) before saying "wiring intact".
- Never guess a price: label every figure official / measured / reported, as in the master list.
