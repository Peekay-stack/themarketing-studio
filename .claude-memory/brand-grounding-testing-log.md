---
name: brand-grounding-testing-log
description: "A standing log the user wants kept — every round of their testing feedback on the Grounded/Independent toggle, paired with what was found and fixed, appended after every round"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-16T06:19:45.622Z
---

**File**: `Heritage Marketing Studio/BRAND_GROUNDING_TESTING_LOG.md` (repo root of the studio project).

**The instruction (12 Sep 2026):** the user asked for a prompt-by-prompt log of their user-testing
feedback on the brand-grounding-modes toggle (see [[brand-grounding-modes-project]]) starting from
their first bug report, paired with the solution applied after each round — and to **keep updating it
after every subsequent round of feedback**, not just write it once.

**How to apply:** whenever the user reports a bug/issue with this feature (or any follow-on testing
round on it), after fixing it:
1. Append a new `## Round N` section to `BRAND_GROUNDING_TESTING_LOG.md` — never rewrite or renumber
   past entries, only add.
2. Each entry: the feedback verbatim (quote it, including screenshot descriptions where relevant), the
   root cause(s) found, and what was actually fixed — same level of detail as the existing entries.
3. This is a testing-feedback log specifically — distinct from `BRAND_GROUNDING_MODES_PLAN.md` (the
   build plan) and [[brand-grounding-modes-project]] (the build-status memory). Don't fold one into
   the other.

Eight rounds logged so far as of 15 Sep: Round 1 (toggle not reaching the IMC skill's own drafting
path — `brief_ai.py`'s brand-invention fallback; General→Independent rename); Round 2 (collapsed four
separate per-tab toggles into one master toggle after live testing showed two disagreeing pills read
as broken; added an "Independent work" row to the header's brand dropdown); Round 3 (Grounded mode
never auto-filled the IMC screen's Brand/Category fields from the active profile — fixed on screen
entry, on switching back to Grounded, and on switching to a different active brand); Round 4 (two
bugs: `im.draft`/`status` never cleared on toggle change, so a drafted IMC screen kept showing
"Redraft" after switching to Independent; `pickBrief` was syncing the master toggle to a picked
brief's own `brand_mode`, silently flipping Independent back to Grounded whenever the user pulled in
almost any pre-existing brief — removed that sync while keeping `enterHouse`/`enterPlan`'s, since
those open an already-decided document and `pickBrief` doesn't. Both live-verified 15 Sep with a real
test brief, created then deleted); Round 5 (user asked for an audit of the other producers, then a
one-pass fix + "default on all tabs, sub tabs and layers" — Round 4's stale-draft bug turned out to be
the studio's default shape, present in Social, Carousel, Video, POSM, Onground, PR's release tool, the
Idea Platform and the guided Brief Builder; fixed in one pass, then live-tested surface by surface
across several follow-up requests, catching two self-inflicted regressions along the way where a
blind reset would have deleted real content instead of just AI output — one on Onground's typed
activation idea, one on an actual *adopted* Idea Platform record (a saved document, not a draft));
two rounds both labeled "Round 6" (session-only persistence fixed via server-side `/studio-settings`;
the made-ledger's empty-string-means-unfiltered footgun fixed; real "Independent" badges added to the
brief/house/plan pickers; character-reference exemption scoped to cast only — then, separately, the
CORE Phase-1 grounding leak found live in POSM and fixed at the two shared chokepoints,
`prompts.py`/`producers.py`, per [[brand-grounding-modes-project]]); Round 7 (the user's own live
testing of Phase 1 surfaced four issues from seven screenshots — `imcSnapshot()`'s brand leak, Plan's
Channels layer never getting a real served-media list, carousel pack shots rendering as garbled
back-of-pack text from a self-contradicting prompt clause, plus a live red-herring where a stale
Independent toggle looked like a regression — all four fixed and live-verified); Round 8 (simplified
the IMC Independent warning to an always-on generic reminder per the user's choice; built Social's
missing pack/cast asset mechanism, reusing POSM's pick-or-upload card pattern per the user's choice,
live-verified end-to-end with a real `/scene-still` call and a visual check of the rendered image);
Round 9 (the user caught, from that same Round 8 demo image, that the real pouch reference rendered as
a bottle instead — `pack_clause` preserved colour/label but never named the container's physical form;
fixed and re-verified with a correctly-shaped pouch render); Round 10 (the user's own real use of the
Social asset picker — upload, objective, generate, adjust — surfaced three more issues in one session:
a fal-fallback path ignoring the requested image ratio, Adjust drifting the product to the wrong real
SKU with no anchor telling the model which pack was pinned, and Adjust fully re-rendering the image on
every note because of a brittle text-equality check instead of an explicit model judgment; all three
root-caused and fixed together, live-verified end to end); Round 11 (testing Independent mode directly
surfaced a real leak in a second, previously-unaudited layer — `brandPreamble()`, the shared client-
side preamble behind 8 producers, only checked Independent inside its "no brand at all" fallback, so
it did nothing when a real brand was active; `inputsContext()` had the same bug; both fixed, plus the
pack-upload UX trap removed by pointing at the one real mechanism instead of leaving two); Round 12
(the real cause of "only 1/6 posts resembled the pack" — `/scene-still`/`/posm-scene` stripped even an
explicitly-picked pack reference in Independent mode, contradicting cast's own precedent; fixed both,
added a "Let the studio design one" option for when no real pack exists yet, and fixed a second
frontend bug where the grounding banner discarded the server's honest summary whenever `grounded` was
false, silently undoing Round 11's own `/grounding` fix before it reached the screen).
See [[brand-grounding-modes-project]] for the full account.
