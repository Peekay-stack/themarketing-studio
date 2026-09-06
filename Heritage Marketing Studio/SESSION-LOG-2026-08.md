# Session log — film pipeline, providers, and the Google migration

Covers the work up to the "3 issues" review (frame/VO sync, voice picking, shoot-board re-sync),
which is where the next log picks up. Companion to `CHANGES.md`, which lists file-by-file edits;
this one records **what was wrong, what was done about it, and what was actually verified** — so a
later reader can tell a proven fix from an assumption.

Install: `Heritage-Marketing-Studio-OPUS` only. The `FULL_6` copy is abandoned and must not be synced.

---

## 1. The film wouldn't render at all

`fal-ai/veo/3.1` is not a model slug; the correct one is `fal-ai/veo3.1`. Every render 404'd behind
a "render isn't wired for preview" message that pointed at the wrong layer.

## 2. Every film came back 8 seconds

Veo renders **4/6/8s beats only** — there is no single-call 30s film. The fix was to plan a film as
a sequence of beats, render them separately, and join them with ffmpeg (`imageio-ffmpeg`, so nothing
has to be installed system-wide).

`filmcut._beat_lengths()` picks beats that sum *exactly* to the target, because greedily taking 8s
would bill a 10s film as 12s.

## 3. Audio restarted at every cut

Video models score each clip independently, so per-shot audio restarts at every join. The pipeline
was inverted to fix it:

> **render the picture SILENT → join it → build one soundtrack over the finished cut.**

This is also cheaper (Veo charges roughly half without audio) and it is why the silent master is
kept on disk: music can be changed later for the price of the audio alone, with no new video spend.

## 4. The voiceover read the script out loud

The VO was reading speaker labels, stage directions and emotions — "Heritage Pure Milk. Narrator.
She smiles warmly." Two rounds of fixes:

- **Structured audio.** Each scene carries an `audio` array of typed lines (`vo` / `dialogue`, with
  speaker, emotion, language) instead of prose. An `audio: []` means *deliberately silent* and must
  never fall through to prose parsing.
- **Prose parsing** for scripts that don't have it: `Name (note): line`, multi-speaker cells and
  `[SFX: …]` are understood; the label and the direction are stripped from what is spoken.

Bugs found along the way, each worth remembering:

| Symptom | Cause |
|---|---|
| "Heritage Pure Milk. Narrator" spoken as one line | label matching swallowed the preceding sentence — needed a sentence-boundary lookbehind |
| A boy cast as a mature woman | the cast sheet hint applied to *every* speaker instead of being scoped |
| `"she" in "sheet"` matched | substring test, not word-boundary — fixed with `\b` |
| `audio: []` spoke the word "Ambient" | empty list fell through to prose |

## 5. Casting: 40 voices, and they are all real

A registry of 40 voices across three providers on fal — **20 Indian**, including 16 ElevenLabs Indian
artists and genuine child voices, because the earlier presets were American/British and read wrong
for an Indian dairy brand.

Verified live against the account: **40/40 usable** (elevenlabs 29/29, kokoro 4/4, minimax 7/7).
So an empty VO is *never* an unavailable voice — look elsewhere.

Notable: a pasted ElevenLabs ID that "didn't work" was a **capital I vs lowercase l** — hence
`/voice-check`, which spends one tiny call to verify an ID rather than discovering it mid-render.

## 6. Scene length follows the dialogue — inside a fixed total

The first attempt let the film grow to fit the writing (a 30s film became 34s). That was rejected,
correctly: **a 30s slot is 30 seconds.** The rewrite keeps the total fixed and redistributes:

1. Every scene starts at Veo's 4s floor.
2. Each spare 2s step goes to whichever scene is furthest short of what its dialogue needs.
3. Beats still sum to exactly the chosen duration.

```
30s, 6 even scenes      -> [6,6,6,4,4,4]   = 30s
30s, scene 3 carries it -> [4,4,10,4,4,4]  = 30s   (renders as 6+4)
20s, 4 scenes           -> [4,8,4,4]       = 20s
```

**Consequence to remember:** Veo's 4s floor caps the scene count — 30s holds 7 scenes, 20s holds 5,
10s holds 2. Script targets were set to 6/4/2 so there is always room to redistribute.

### The pressure valve

When the words genuinely don't fit, delivery speeds up — capped at **1.2×**, and **one speed for the
whole film**, because per-line speed-ups make the read lurch at that cut. Verified: three 6s lines in
4s/10s/4s windows all came out at 5.0s, i.e. exactly 1.20×, including the line that had room.

The audition preview had **no** speed handling at all, so what you approved wasn't what rendered.
Both now share the same measurement.

## 7. The film was 32 seconds, and that was a sync bug

Veo returns each clip a few frames long (~0.34s). Six shots = +2s. But the soundtrack is placed at
*absolute* timecodes, so the picture cut at 6.33/12.67/19… while the audio expected 6/12/18 — by the
closing scene the sound ran **two seconds ahead of its own picture**.

Each clip is now cut back to the beat it was ordered at, frame-exactly (a stream copy can only cut on
frame boundaries and drifted 0.08s per clip, so the trim re-encodes).

```
clips as returned : [6.33,6.33,6.33,4.33,4.33,4.33] = 31.98s
after per-clip trim: [6,6,6,4,4,4]  -> boundaries [6,12,18,22,26,30]
joined: 32.00s -> 30.00s
```

Also: audio was mono (TTS is mono and `amix` inherited it). Now forced to stereo.

## 8. Providers: what runs where

**fal is strictly for voice.** Image, video and music go to Google.

| Capability | Model | Note |
|---|---|---|
| Image / character lock | `gemini-3.1-flash-image` | output must be `image/jpeg`; png is rejected |
| Video | `veo-3.1-lite-generate-preview` · `veo-3.1-generate-preview` | **only these two on the Gemini API** |
| Music | `lyria-3-clip-preview` / `-pro-` | billed **per clip** ($0.04), not per second |
| Voice | fal → ElevenLabs / Kokoro / MiniMax | |

Engines are selectable per capability (auto / google / fal) because a render once quoted Veo Lite's
price and quietly spent fal credits.

### Three bugs in the Google path, all silent

1. **`veo-3.1-fast-generate-preview` does not exist.** Veo 3.1 Fast is a Vertex model. Every
   middle-tier render 404'd and fell through to fal — the quoted-Google-billed-fal bug. Tiers are now
   engine-aware: Google = Lite/Standard, fal = Fast/Standard.
2. **`durationSeconds` was never sent.** Every Google shot would have come back at Veo's default
   length whatever beat was asked for, breaking both the film length and the sync.
3. **The reference frame used the wrong encoding.** Google's own docs show `image.inlineData`, but
   that is the *Standard* model; **Lite requires Vertex-style `bytesBase64Encoded`** and rejects
   inlineData outright. Without this, every draft silently dropped to text-to-video and **reinvented
   the cast on every shot** — the thing the character lock exists to prevent.

### Verified live on Google — 4/4

```
Imagen / Gemini image (16:9 frame)      OK  15s
Character lock (image from reference)   OK  17s   same face, sari, bangles, kitchen
Veo 3.1 Lite, 4s, image-to-video        OK  46s   duration exactly 00:00:04.00
Lyria music clip (10s bed)              OK  14s   first bed ever produced
```

Google returns clips at *exactly* the length ordered, unlike fal.

## 9. Costs, corrected against the published rates

| Engine · tier | Model | 30s film |
|---|---|---|
| Google · Draft | Veo 3.1 Lite | **$1.50** |
| Google · Final | Veo 3.1 Standard | $12.00 |
| fal · Draft | Veo 3.1 Fast | $3.00 |
| fal · Final | Veo 3.1 Standard | $6.00 |

Google's draft is half fal's; Google's final is double fal's. Billed seconds equal the film length
exactly, because the beat planner sums to the chosen duration.

## 10. Also fixed

- `brief_render.py` was **missing from this install** — the cause of the IMC brief shipping with no
  NeedScope graphic and no CB/CA. Restored, then the figures were made legible (fonts scale with the
  page, cards size to their content, the shift caption moved below, the NeedScope badge draws before
  the pins).
- Music: 8 named styles × 3 bed levels, auditioned as short clips, the chosen bed locked and reused,
  and every scored version kept.

---

## Open at the time of writing

- Three legacy pages (`/studio`, `/brand-brief-builder`, `/builder`) still carry the old identity.
- `GUIDELINES.fonts` lists the portal's old fonts as *Heritage's* brand fonts — almost certainly wrong.
- 60s/120s films need a job + polling endpoint; a single request will time out.
- The distributable zips are stale.

## Rules established, worth not relearning

1. **fal is for voice.** Image, video and music are Google.
2. **A 30s slot is 30 seconds.** Scene lengths flex; the total does not.
3. **Silence is never an acceptable failure.** A dropped line, a short film or a dead quota must say
   so — every one of those shipped quietly at least once.
4. **Identity travels as an image, not a description.** Seeds and prose do not hold a face.
5. **Verify a key or a voice with one cheap call**, not with a render.
