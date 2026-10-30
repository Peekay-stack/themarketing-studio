# The craft layer: making TMS films memorable, entertaining and clear (plan and blast radius)

Status: **PLAN ONLY. Nothing in this plan is built.** Written 30 Oct 2026 for the owner's review, after 15 reference ads were read and the owner answered the log's 17 questions. Branch `film-engagement-2` (worktree `hms-fixes`, not merged, not live). Source of every claim about the ads: `AD_LEARNING_LOG.md` (sections "The purpose of this log", "Where the magic is", "Why the owner chose each reference", "The owner's decisions", Patterns, Candidate changes C1-C43).

## 0. The owner's words that govern this plan
1. The point of the ads was to show **when an ad becomes magical and effective**: the thought in the scripting, dialogues, key moments, the voice-over artiste, celebrity casting, attention hooks and how the proposition is dramatised.
2. **The director's vision decides; there is no hard and fast rule.** Everything is in scope.
3. Decisions already given: a jingle option (lyrics from the message and script, plus music, any language); the builder starts doing claims and demonstrations; wardrobe, location and lighting change as the script demands; dialogue, "God's voice" and a jingle mix freely; score celebrity ads for structure and SUGGEST a celebrity-led option (never use a real likeness); suggest a SERIES of 2-6 linked ads where there is a need; if the video engine is the constraint, stay with multiple shots.

So every check this plan adds is **advice with a reason, never a gate** (the standing rule: offer, never silently apply), and every craft device is an option the director may take or refuse.

## 1. "The more we use it, the sharper it gets": what is true and what is not
- **No model is trained, and none will be by this plan.** `learning.py` says so in its own header: Claude, Veo, Imagen and Lyria are frozen. What can sharpen with use is three things the app already has: **T1 retrieval** (approved work is kept and the closest few examples go in front of the model on the next brief), **T2 a scored prompt library** (templates that keep earning approval are promoted), **T3 corrections** (each rejection carries a reason; reasons become house rules in the next brief). All three are scoped per brand.
- It sharpens ONLY if decisions are captured (approve / reject with a reason), and ONLY as far as the captured work is good: wrong approvals teach wrong things, and the prompt can only carry so many examples. It needs a person curating, and it can be rolled back (everything is versioned).
- Real training (fine-tuning a model, a custom voice, a style LoRA) is a **later, separate** decision (section 8). It would send data to the vendor and needs hundreds of clean examples, which we do not have.
- The ad log never trains anything. It is distilled into a short original-safe brief (W0) that rides as prompt text. That text goes to the model provider as ordinary input; Chirp, Omni (Kling on fal) and the image and video engines never see it, only their own per-shot or per-line prompts.

## 2. Where the craft layer sits in the pipeline (`FILM_PIPELINE_MAP.md`, stages 1-12)
| New role | Stage it touches | What it adds |
|---|---|---|
| **Creative director (new, upstream)** | 2 Concept, 3 Script | message in one sentence; attention hook; ONE key moment; the proposition DRAMATISED as an event (a "move"); a memorable device; a quotable line; a casting-and-voice idea |
| Director (exists) | 3b the director's read | owner's tests added; two findings softened |
| **Sound designer and composer (new)** | 8 craft layers, 10-11 sound plan and render | a sound-design plan per scene; music that stops and returns; jingle; acted delivery |
| Series planner (new, optional) | 1 Brief / Plan | 2-6 linked ads with a thread, a hook and a closing signature |
| Learning loop (exists) | all approvals | capture of craft scores and your ratings |

## 3. The workstreams (each is a separate, reversible slice)
**W0. Foundations (text only, near free).**
- A **craft brief**: a short, ORIGINAL-SAFE distillation of the log: about a dozen "proposition moves" (reframe then proof, a stain as joy, absence as a trophy, a persona reversed, energy made visible, a flirtation in one take, exclusivity as an audition, a build to a reveal, an observation of tenderness, a gag that carries the benefit, a problem solved inside a family moment, an emotion tied to the benefit), the owner's six reasons, the jingle craft, the sound layering. No ad is named in the brief and no scene is copied (an originality guard in the prompt).
- Delivered like the brand-character skill: a versioned skill file read by `prompts.system_for()` behind a **feature flag** (off by default, on per tenant for the first tests).
- A **scorecard** (the evaluation set): the owner's six reasons plus message clarity, scored 0-3 with a one-line reason by a model call on a concept or a script, run only on request. It is the way to know whether anything we add helps. The 15 ads (reconstructed as scripts, as in `tools/adlab/director_reads_30oct.json`) are its calibration set.

**W1. Concept craft (stage 2).** Each of the three routes already carries hook, surprise, turn, memorable, stake (film engagement lever #2). Add: `message` (one sentence), `move` (which proposition move), `device` (jingle, tag line, reveal, character moment, gag), `line` (the quotable line), `cast_idea`. Routes must be genuinely different in MOVE, not only in wording. Displayed on the route card; a concept without them behaves exactly as before.

**W2. Script craft (stage 3).** The writer rules (`VISUAL_RULES` and the audio-line rules in the page) gain: mark the key moment and the hook scene; carry the quotable line into the dialogue; allow dialogue, narrator and jingle to mix per scene (the `audio` rows already carry kind, speaker, text, emotion, pace, timing).

**W3. The director's read (`filmdirect.py`, `/film-direct`).** C37: ask whether there is ONE message and ONE memorable device. C36: `slow-hook` and `same-place` become quiet notes (they fired on 10 and 11 of the 13 reference ads the owner prizes, none got a low risk). Still advice only.

**W4. Sound design layer (`soundplan.py`, `filmaudio.py`, `/sound-plan`, `/rescore`).** C42, C39. The builder already has three beds (voice, music, ambience), placed foley spots from a library and a bed envelope around the voice. To check first: is the plan written automatically per scene from the script; how rich is the sound library; can the music be cut out and brought back at chosen moments. Add: a per-scene sound-design note (ambient, foley, a hit sound), a music policy (jingle build, or voice-led with music entering at the reveal).

**W5. Jingle option (C28, C33, C43).** Lyrics written by the model from the message and script (short, hummable, a simple expression of the proposition, in any language); the music via the existing music model path (`MUSIC_MODEL` in `filmaudio.py`; whether it can sing the lyrics is to be verified in a trial); the cut follows it. A new paid generation path: needs a cost quote and a trial before building.

**W6. Acted delivery (C40).** Lines already carry an `emotion` note. Today it chooses the voice band and, on ElevenLabs, stability and style presets; on Chirp only the voice and a per-line pace are controlled (the tone picker was removed on 23 Oct). Hush, loud, questioning and irritated are not controlled. A trial first: what each voice engine can do per line (volume, style direction, pauses). No build before the trial.

**W7. Claims and demonstrations (C11, C12).** A shot type for split screens, proof graphics, a claim line with its footnote, a name super: composed on top of generated pictures in `composite` and the Edit room, not generated by the video engine (so it is exact and cheap). New fields on a scene (a `proof` block).

**W8. Wardrobe and place that change with the script (C13).** The wardrobe lock fixes one state today; per-scene wardrobe state (clean to muddy, dry to wet) touches the cast sheet, the frame prompts and the staleness fingerprints (see the blast radius).

**W9. Series of 2-6 and the closing signature (C32, C41, C35).** A series planner on `campaign.py` that proposes linked ads (a common thread and hook, one closing line that ends every film). A celebrity-led option may be SUGGESTED in the concept (structure only, no likeness).

**W10. Learning capture.** Record the owner's rating and the scorecard result with every approved script (`learning.record` / `keep_example`), so the retrieval anchors are good work, and so a dataset exists if training is ever considered.

## 4. Suggested order and the owner's gates
| Phase | Slices | Spends money? | The owner tests |
|---|---|---|---|
| A. Text craft | W0, W1, W3 (and W10 capture) | A few cents per concept or read | Three real briefs on localhost: do the routes feel sharper than before? score them with the scorecard |
| B. Voice and sound | W2, W4, W6 trial, W5 trial | Trials only (quoted first) | One film with a sound-design plan; one jingle trial; one acted-delivery trial |
| C. Picture side | W7, W8 | Frames (quoted first) | A claims film; a wardrobe-change film |
| D. Series | W9 | Text only | A 3-ad series for one brand |
Each phase ends with the page checks, the Python tests, a wiring audit (as done twice before) and your localhost test; nothing is merged without your sign-off.

## 5. Blast radius: everything these changes can touch
| Area | Files (this branch) | What changes | What could break | Guard |
|---|---|---|---|---|
| The page (monolith, 31,798 lines, LF only) | `api/frontend/app.dc.html` (writer rules ~15,966, director call ~16,174, concept lever #2 ~18,795, `soundPlan` 59 references, `rescore` 13, voices 6) | Route card fields, writer prompt, sound panel, director card, series screen | **Design handovers: their copy is always stale, merge never replace;** an accidental CRLF rewrite of 31k lines; a `{{ }}` image binding leak; frames going stale by a new field | LF-aware patching; page checks in `tools/page_checks`; reload and drive the real page; never drop in their file |
| System prompt | `api/prompts.py` (`system_for`) | The craft brief rides here (flag) | **Golden prompt tests change** (`tools/golden_prompts.py`, `tools/golden*`); every call that uses `system_for` (Social, Video, plan, platform, trade) gets longer | Flag off by default; apply to `film=True` calls only first; regenerate the goldens deliberately |
| The director's read | `api/filmdirect.py`, `/film-direct` in `api/main.py` | Two findings softened, two checks added | `test_film_direct.py`, `test_film_concept_delivery.py`; the director card and the approve-confirm wording (Phase 4 of the boring-film plan) | Update tests with the change; keep `risk` computation honest |
| Saved films | `api/filmscript.py` (`FIELDS`), `test_film_saved_roundtrip.py` | New concept and scene fields (message, move, device, line, proof, wardrobe state) | A field that is not in `FIELDS` is lost on save; an extra field could mark approved frames STALE (the A-series bug) | Treat new craft fields like `SCENE_EXTRAS`: excluded from the picture fingerprints unless they change the picture |
| Sound and voice | `api/soundplan.py`, `api/filmaudio.py`, `api/filmvoice.py`, `api/filmedit.py`, `/sound-plan`, `/voice-plan`, `/voice-preview`, `/produce-video`, `/rescore`, `/editor-notes` | Sound-design plan, jingle path, delivery direction, new editor notes | `test_sound_plan*.py`, `test_produce_sound.py`, `test_voice_*.py`, `test_loudness.py`, `test_film_edit.py`; mixes and loudness; a silent tail rule (C5) | New fields optional; defaults identical to today |
| The Edit room and cutdowns | `api/cut.py`, `/cut-down`, `/cut-sound` | Cutdowns must keep the sound design, the jingle and the closing signature | The cutdown path is frameless and had its own gaps before (26 Oct audit) | Audit sibling entry points, not only the diff |
| Composite and sign-off | composite step, `render-holds-signoff-locked-still` rule | Supers, split screens, proof graphics; a speaking presenter or a coda in the sign-off | The sign-off is deliberately locked still; checks that read it | Read the render path before adding any scene-level rule |
| Campaign and series | `api/campaign.py`, `/campaign*`, house and platform | A series planner and a signature line | Campaign-to-medium wiring, staleness tracking, "update campaign" behaviour | Reuse the existing campaign objects; no new storage |
| Learning | `api/learning.py` and its callers in `api/main.py` (the record, keep-example, anchors and rules routes near lines 3872-3900, and the strategy, plan, platform and trade writers) | Capture of ratings and craft scores | Tenant and brand scoping (`brand=` on every call); the guardrails | Never write across tenants; the craft brief itself is TMS product knowledge in code, NOT tenant data |
| Cost | model-call and generation spend; the made ledger (`api/made.py`) records what was produced | Extra model calls (a scorecard, a sound-design plan, lyrics) | Beta spend caps are still open (Phase 4 of the deploy plan) | Quote every paid trial; text-first |
| Tests | `tools/test_*.py` (about 60 files), `api/tests`, `tools/page_checks`, `tools/smoke.py` | New tests for each slice; some existing tests change | A test that pins a prompt string | Run the whole suite per slice |
| Deploy | Render service, branch policy | None until you sign off and merge | Live is master `b1519e6`; this branch is not live | No push to master without your go |
| Docs and memory | `FILM_PIPELINE_MAP.md`, `VIDEO_CRAFT_FRAMEWORK.md`, `AD_LEARNING_LOG.md`, memory | Updated per slice | Drift between the log and the plan | The plan lists its sources; the log stays append-only |

**What does not change:** the cast lock, the frame generation and the video engines, the render's locked sign-off, the approval gates, the brand grounding modes, tenancy, and every film already saved (all new fields are optional and absent on old films).

## 6. Cost
- Phase A adds one prompt block (about 1-2 thousand tokens) to the concept and script calls, one optional scorecard call and no new generation: a few cents per film.
- Phase B adds a sound-design plan call (cents), and paid trials for the jingle and for acted delivery; each is quoted first.
- Phase C adds frames only when you choose to generate them.
- The director's read run on 13 ads cost about 11 s and an estimated 90 cents in total; a normal film's read is about 7 cents.

## 7. Risks and how they are held
- **Copying other people's ads.** The brief names no ad and no scene; the originality guard is in the prompt; the scorecard asks "is this a copy of a known ad?".
- **False confidence.** Checks that fired on every prized ad were demoted (C36); a score is never a gate; every score shows its reason.
- **Over-fitting to Indian mass-market comedy.** The log's own caution: none of the references is Telugu or heritage. The craft brief states the MOVES, not the tone, so a quiet heritage film can use them too.
- **Prompt bloat and drift.** The brief is short, versioned and flag-guarded; the goldens are re-baselined deliberately.
- **Honesty.** The product says "no model is trained here" (learning.py); this plan keeps that true.

## 8. Training, later and only if the scorecard shows a gap
Fine-tuning a text model for one narrow job (for example short jingle lyrics in Telugu), a custom brand voice, or a style LoRA for pack and character looks: each sends data to the vendor, needs consented, clean data, and should wait for the dataset W10 builds. Not part of this plan's slices.

## 9. Decisions for the owner
1. Approve **Phase A** (W0, W1, W3, W10) as the first slice, behind a flag, on three real briefs?
2. May I check each vendor's data-use terms (Anthropic, Google, ElevenLabs, fal) before any training is considered?
3. Is the GitHub repo `Peekay-stack/themarketing-studio` private? (The log and the memory mirror are pushed there.)
4. For the trials in Phase B: which language should the jingle trial use (Telugu, Hindi, English)?
5. Which two real briefs, besides a dairy one, should we test on (a different category, so we see the moves travel)?

## 10. Verification per slice
The Python tests, the page checks, a localhost run you drive, a wiring review (as `FILM_WIRING_AUDIT.md`), the scorecard before and after on the same three briefs, and the log updated with the result. A slice that does not improve the scorecard or that you do not like is switched off by its flag.
