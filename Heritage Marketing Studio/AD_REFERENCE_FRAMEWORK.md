# Reference-ad framework: how we read an ad and what we take from it (30 Oct 2026)

Why this exists: our film builder has rules (the craft framework, the pace presets, the director's read, the checks added on 29 Oct) written from our own films. The owner will share real ads that work. For each one we ask the SAME questions, in the order the builder works (concept, script, shoot board, shots, sound design, music, voice-over, casting, location, brand), write down what we saw, compare it with what our rules would have said, and only then decide if a rule should change. Nothing is changed off one ad.

Companion: `AD_LEARNING_LOG.md` (one entry per ad, append-only). Tools: `tools/adlab/measure_ad.js` (free measurements while the ad plays in the built-in browser).

## 1. Ground rules
1. **Judge as an audience first, then as a director** (the 28 Oct lesson: a film can pass every check and still bore). Every entry starts with what a viewer feels and where they would swipe, before any number.
2. **Every claim carries its evidence level.** Levels, strongest first:
   - **MEASURED**: a number computed from the file as it plays (cuts, shot lengths, motion, brightness, loudness, silences).
   - **SEEN**: read off frames I looked at (who, where, what is on screen, burned-in text, framing).
   - **READ**: text the platform gives (title, description, channel, date, views, captions or a transcript when one exists).
   - **INFERRED**: a reasoned guess from the above, marked as one.
   - **NOT JUDGED**: what I cannot do and will say so rather than guess: **I cannot hear.** I do not judge a voice's quality, accent, music genre or instruments, humour in a performance, or lyrics, unless the words are on screen or in a transcript. The sound is measured (levels, silences, where the level lifts), never described by ear. If the owner tells me what the music or voice is, it is recorded as OWNER-REPORTED.
3. **Views and age are a popularity signal, never a quality score.** They tell us the ad travelled, not why.
4. **One ad is a hypothesis, three ads that agree are a pattern, a pattern is a proposal, the owner decides.** The log records support counts for every candidate change.
5. **Brand- and category-agnostic**: an ad is read for how it works, not for who sold what. A rule we take from a fashion ad must make sense for dairy.
6. **Nothing is copied.** We store our own notes, short quotes (a few words) and numbers; no downloads of the ad, no transcripts reproduced.

## 2. The fact sheet (the same fields for every ad, so ads can be compared)
Brand | category | the link and the date read | length | year and platform | language(s) | format (live action, animation, mixed) | picture size | views and age (signal only) | who made it, if shown | the commercial job as the viewer would see it (awareness, offer, launch, reassurance) | evidence available (captions? description? measured? owner notes?).

## 3. The nine questions, in builder order
For each: what we ask, how we get evidence, the number to record, and which part of OUR system it tests.

### 3.1 Concept
- **Ask:** the idea in one sentence a stranger could retell; what is at stake for the people in it; whether anything happens (a reversal) or only a feeling is shown; the one image a viewer would describe to a friend; whether the brand is the reason the story works or is bolted on (swap the brand: does it still work?); whether it is a premise that travels (a known format, a twist on one).
- **Evidence:** SEEN + READ (title, description) + INFERRED. **Record:** the four moments (hook, surprise, turn, memorable), the stake, premise type (conflict / reversal / observation / demonstration / testimonial / absence of conflict), brand-necessity (integral / helpful / bolted-on).
- **Tests:** concept routes (`hook`, `surprise`, `turn`, `memorable`, `stake`, the "visible reversal" rule), the director's `concept` promises, the boring-premise gate.

### 3.2 Script and structure
- **Ask:** the beats in time order with what each is for; when the first hook lands (seconds), where the turn falls (% of the film), where the message and the brand first appear and land; how much changes scene to scene; what is repeated; how it ends.
- **Evidence:** MEASURED (cut times) + SEEN. **Record:** beat map with time codes, intensity 0-3 and energy 0-3 per beat (our scales), turn at x %, brand first seen at x s, scene count, spoken or on-screen words per 10 s.
- **Tests:** the director's read (`purpose`, `intensity`, `energy`, `change`, `turn_scene`, `carrier_scene`, findings `slow-hook`, `same-place`, `flat-energy`, `no-change`, `late-peak`), the writer rules (`VISUAL_RULES`, `deliveryRulesText`).

### 3.3 Shoot board (planning and production design)
- **Ask:** how many places and how different they are; time of day and light changes; the props that carry the story (the hero object); wardrobe as character; continuity (same prop, same costume); what the departments (DoP, lighting, props, wardrobe) evidently decided.
- **Evidence:** SEEN. **Record:** number of distinct places, the hero object and how often it is on screen, wardrobe notes per character, light note per place.
- **Tests:** the department notes (DoP, lighting, props, wardrobe, location), the film-wide Location line vs a scene's own `place`, the wardrobe lock, the A-series staleness (are notes written before frames).

### 3.4 Shots
- **Ask:** how many shots, how long they hold, how the rhythm changes (does it accelerate to the turn), the size mix (wide / medium / close / detail), how much the camera moves, hard cuts vs other joins, inserts and cutaways, the first shot, the last shot and how long the brand holds.
- **Evidence:** MEASURED (cuts) + SEEN (sizes, moves). **Record:** shots, average shot, shots per 10 s (against our Calm 2-2.5, Standard 2.5-3.5, Fast 3.5-5), longest and shortest shot, the longest same-size run, share of shots with camera movement, motion inside shots.
- **Tests:** `PACE_TABLE`, the shot planner's jobs and "life in the shot" rule, the flow review (`cut-rate`, `same-size-run`, `same-length`), the sequence rule, the sign-off hold.

### 3.4b Picture quality the audience would notice
- **Ask:** is anything wrong-looking (stretched limbs, a smeared product, a face that changes); is the product shape and label stable.
- **Evidence:** SEEN. **Record:** none expected in a real ad; if one appears, note it (it calibrates the clip look).

### 3.5 Sound design
- **Ask:** is there room tone and ambience, effects that sell the action (a pour, a click), silence used as a beat, sound that leads or follows a cut, how loud it is across the film, where the level lifts (on the turn?), how it ends (a sting, a held breath, a button).
- **Evidence:** MEASURED only (level per second, silent stretches, the loudest second, level lift points) + the burned-in text. **Not judged:** what the effects are.
- **Tests:** the sound plan, the editor's notes (music lifts on the turn, a beat of silence before the message, a silent tail), the Render check's silent-tail finding.

### 3.6 Music
- **Ask:** is there a bed; when does it enter and leave; does it change at the turn; does it duck under speech; does it end on a button; is it a known track or a library feel.
- **Evidence:** MEASURED (level shape, entry and exit seconds, the lift) + READ (description, comments naming a track) + OWNER-REPORTED. **Not judged:** genre, instruments, mood by ear.
- **Tests:** the music style / tempo / dynamics / on-turn settings and the re-score.

### 3.7 Voice-over and dialogue
- **Ask:** who speaks (narrator or characters), in which language(s) and how they mix, how many words in total and per 10 s, when the first and last words fall, whether the line that carries the message is spoken or only written, whether the product name or tagline is said, how much of the film is silent.
- **Evidence:** READ (captions or a transcript) + SEEN (burned-in subtitles) + MEASURED (speech-band presence and silence per second). **Not judged:** voice quality and delivery.
- **Tests:** the voice budget (`voBudget`: 32 words for 30 s, deliberately sparse), the Delivery row (thin script, silent sign-off, dropped concept voiceover), the Chirp casting and pace, the English-line-in-a-Telugu-film question.

### 3.8 Casting and performance
- **Ask:** how many people carry the story, ages and types, whether they are believable for the setting, whether a casting idea is the concept (for example children playing adults), how long faces are on screen, whether anyone looks to camera, how wardrobe tells who they are.
- **Evidence:** SEEN. **Record:** speaking characters, main faces, a known face (yes / no), casting device, the share of shots with a face.
- **Tests:** the cast sheet, the cast-and-location lock image, single-person references, `video_characters`, the limb-safety rule for faces and hands.

### 3.9 Location
- **Ask:** the places and how real they feel (a lived-in detail vs a clean set), how the place helps the story, how many times the film leaves its first place, depth and palette.
- **Evidence:** SEEN. **Record:** places and their order, the lived-in details named, palette and light per place.
- **Tests:** the Location line and plate, a scene's own `place`, the `same-place` finding.

### 3.10 Brand and call to action
- **Ask:** the first second the brand is visible or named, how it enters (story or logo), how long the pack or logo holds at the end, what the end line says and whether it is spoken, any offer or legal text and its size, whether the brand could be removed and the film still work.
- **Evidence:** MEASURED + SEEN + READ. **Record:** brand first seen (s and %), end hold (s), spoken tagline (yes / no), on-screen text lines.
- **Tests:** the pack-shot sign-off rules (a spoken payoff, the locked hold), `carrier_scene`, the sign-off conflict found on 29 Oct.

## 4. The audience verdict and the comparison with our rules
- **Audience verdict** (SEEN, as a viewer): attention curve in three words (where I lean in, where I would swipe), the memorable image, what I would repeat, whether it makes me want to watch again. Plain words, no scores.
- **Our system on this ad**, one row per dimension: **Our rule | What the ad does | Verdict** where the verdict is one of **CONFIRMS** (the ad does what our rule asks), **CONTRADICTS** (the ad succeeds while breaking our rule: the rule may be wrong or too narrow), **EXTENDS** (the ad does something our framework has no word for), **OUTSIDE** (something we cannot build or judge today), and a **confidence** (low for one ad).
- **What our director's read and checks would have said**: run in the head from the measured fields (risk, findings). A finding that fires on a good ad is a false alarm to record.

## 5. The log
`AD_LEARNING_LOG.md` holds: the rules of the log, an index table, one entry per ad in the order read (never rewritten, corrected only by a dated note), a **patterns** section (what N ads agree on, updated as ads arrive) and a **candidate changes** list with support counts (ad ids for and against), status (hypothesis / pattern / proposed / decided) and the owner's decision.

## 6. How an ad is read (the protocol, so every entry is comparable)
1. Open the link in the built-in browser; record the READ fields; note whether YouTube shows its own advert first (the tool waits it out). **Show the browser pane** (the app's pane switcher) before measuring: in a hidden pane the page draws no frames and the meter reads silence (found on the first run, 30 Oct).
2. Run `tools/adlab/measure_ad.js` once, pasted inline (YouTube blocks fetching a local script): it plays the ad at normal speed and records frame changes and sound levels (the sound goes only to a meter, never to the speakers). Reading it back gives cuts in two grades (`cuts` = sure; `cutsProbable` = whips and soft cuts in busy footage, to verify by eye), shot lengths, shots per 10 s, motion and brightness per second, loudness per second and the silent seconds. It sets YouTube's autoplay off for the tab (otherwise the page moves on to another video mid-measurement). A measurement is not trusted until the frame count is about 24 x the length and the sound is not -180 dB throughout.
3. Seek to each shot and each second of the hook, the turn and the end and look at frames large enough to read (burned-in text, faces, hands, product). Verify the probable cuts by eye and give the shot count as a range if any stay unverified.
4. Look for captions or a transcript; else rely on burned-in subtitles; else say "words not recoverable". **YouTube's on-page captions are auto-generated and unreliable in Hindi and other Indian languages** (garbled words): treat them as READ at low confidence and never quote them as the script.
5. Write the fact sheet and the nine questions with evidence levels; then the verdict and the comparison table; then update the patterns and the candidate changes.
6. Anything I cannot judge is listed in the entry under "Not judged", never filled with a guess.

## 7. What this framework does NOT do
- It does not score ads out of ten, rank them, or say an ad is "good" on numbers.
- It does not decide what we build: changes go through the owner after the log shows a pattern.
- It does not replace the checks in the builder; it tests whether those checks are right.
