"""filmvoice.py — turn an approved script into cast, timed voice segments.

The film's soundtrack is not one narration blob. A row can carry narration ("VO") and several
characters, each with its own voice and a performance note in parentheses:

    Boy (young, half-asleep): Ammamma... sky's still sleeping, no?
    Grandmother (elderly, hushed, a smile in her voice): Sankranti wakes up before the sun does.

So each row is broken into typed SEGMENTS. Narration keeps one fixed voice for the whole film;
every character is cast to its own voice; performance notes drive delivery settings and are never
spoken. Each segment is synthesised separately and placed at its scene's timecode by filmaudio.

Preferred input is the row's structured `audio` list (the studio writes it). Scripts written before
that existed — or reworked by a model that dropped the field — fall back to parsing the `dialogue`
prose, which is why the parser below is deliberately tolerant.
"""
from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field

TTS_MODEL = "fal-ai/elevenlabs/tts/multilingual-v2"

WORDS_PER_SEC = 2.2       # measured: ElevenLabs reads ~136 wpm on these scripts
SPEECH_PAD = 1.4          # a breath either side of a scene's dialogue
_ALLOWED_BEATS = (4, 6, 8)  # Veo renders only these clip lengths
MAX_TTS_SPEED = 1.2       # the model's own ceiling

# --- casting ------------------------------------------------------------------------------
# Voices span three providers on fal. The ElevenLabs preset voices are American/British, which
# reads wrong for an Indian brand film, so native-Indian voices are registered alongside them and
# are the default. A raw ElevenLabs voice ID also works (verified), so any voice added to the
# account's ElevenLabs library — including Telugu/Hindi-accented community voices — can be used
# by pasting its ID.
EL_MODEL = "fal-ai/elevenlabs/tts/multilingual-v2"
KO_MODEL = "fal-ai/kokoro/hindi"
MM_MODEL = "fal-ai/minimax/speech-02-hd"

INDIAN, INTL = "Indian", "International"


@dataclass
class Voice:
    id: str            # what the UI stores
    label: str         # what the user reads
    provider: str      # "elevenlabs" | "kokoro" | "minimax"
    ref: str           # the provider's own voice identifier
    accent: str
    gender: str        # "female" | "male"
    age: str           # "young" | "adult" | "mature"
    pitch: int = 0     # minimax only — raising pitch is the only way to get a child read


VOICES: list[Voice] = [
    # --- Indian ElevenLabs voices (public library, all verified reachable through fal) ---------
    # These are real Indian-English/Hindi voice artists at ElevenLabs quality, so they lead every
    # band and are what the studio casts by default. NB: voice IDs mix capital I and lowercase l —
    # copy them, never retype them.
    Voice("in-f-riya", "Riya Rao · clear, conversational", "elevenlabs",
          "mActWQg9kibLro6Z2ouY", INDIAN, "female", "adult"),
    Voice("in-f-kanika", "Kanika · warm, expressive", "elevenlabs",
          "C2S5J6WvmHnrQWjUu6Rg", INDIAN, "female", "adult"),
    Voice("in-f-anika", "Anika · animated, friendly", "elevenlabs",
          "Sm1seazb4gs7RSlUVw7c", INDIAN, "female", "adult"),
    Voice("in-f-priyanka", "Priyanka · warm, bright storyteller", "elevenlabs",
          "T536A2SFCG4AEDVTRucQ", INDIAN, "female", "adult"),
    Voice("in-f-halle", "Halle · engaging, friendly", "elevenlabs",
          "WLYkHN9uYXdErr012rBi", INDIAN, "female", "adult"),
    Voice("in-f-kahani", "Kahani · motherly, calm", "elevenlabs",
          "ZthnDvLLxYzM9qeFVSJe", INDIAN, "female", "mature"),
    Voice("in-f-saanu", "Saanu · elderly, soft", "elevenlabs",
          "50YSQEDPA2vlOxhCseP4", INDIAN, "female", "mature"),
    Voice("in-f-shakuntala", "Shakuntala · clear, expressive", "elevenlabs",
          "EGQM7bHbTHTb7VUEcOHG", INDIAN, "female", "mature"),
    Voice("in-m-sujit", "Sujit · warm, steady", "elevenlabs",
          "uvq2obtsgd81iEJ31urT", INDIAN, "male", "adult"),
    Voice("in-m-amit", "Amit · Indian English, professional", "elevenlabs",
          "y3bFrCRcSPphE8Ksv5BW", INDIAN, "male", "adult"),
    Voice("in-m-omar", "Omar J · energetic storyteller", "elevenlabs",
          "srEfhy4AF67Mw9SpTVFd", INDIAN, "male", "adult"),
    Voice("in-m-kunal", "Kunal · mature, confident", "elevenlabs",
          "Qxb5zQvEo3DYQK2HNnXm", INDIAN, "male", "mature"),
    # Real Indian child voices — no pitch-shifting needed.
    Voice("in-g-gudiya", "Gudiya · very young girl", "elevenlabs",
          "csPuxct3x4tABDZeKliZ", INDIAN, "female", "young"),
    Voice("in-g-suhana", "Suhana · young, innocent", "elevenlabs",
          "A2VREc2wjqtSZloENLHe", INDIAN, "female", "young"),
    Voice("in-g-riya", "Riya · children's storyteller", "elevenlabs",
          "4RloeZf2FRvGiu4uoKOf", INDIAN, "female", "young"),
    Voice("in-b-bhola", "Bhola · cute young boy", "elevenlabs",
          "d7G4zsIoYxHBAwkKbqs5", INDIAN, "male", "young"),
    # --- Kokoro Hindi (backup: works with no ElevenLabs dependency) ---
    Voice("hi-female-1", "Hindi female · warm", "kokoro", "hf_alpha", INDIAN, "female", "adult"),
    Voice("hi-female-2", "Hindi female · mature", "kokoro", "hf_beta", INDIAN, "female", "mature"),
    Voice("hi-male-1", "Hindi male · warm", "kokoro", "hm_omega", INDIAN, "male", "adult"),
    Voice("hi-male-2", "Hindi male · mature", "kokoro", "hm_psi", INDIAN, "male", "mature"),
    # --- MiniMax: the only usable child reads (pitch-shifted) + neutral adults ---
    Voice("mm-boy-child", "Boy · child (pitched)", "minimax", "Decent_Boy", INTL, "male", "young", 4),
    Voice("mm-boy", "Boy · teen", "minimax", "Decent_Boy", INTL, "male", "young"),
    Voice("mm-girl-child", "Girl · child (pitched)", "minimax", "Lively_Girl", INTL, "female", "young", 3),
    Voice("mm-girl", "Girl · young", "minimax", "Lively_Girl", INTL, "female", "young"),
    Voice("mm-woman-wise", "Woman · wise", "minimax", "Wise_Woman", INTL, "female", "mature"),
    Voice("mm-woman-calm", "Woman · calm", "minimax", "Calm_Woman", INTL, "female", "adult"),
    Voice("mm-man-patient", "Man · patient", "minimax", "Patient_Man", INTL, "male", "adult"),
    # --- ElevenLabs presets (US/UK) ---
    Voice("el-sarah", "Sarah", "elevenlabs", "Sarah", INTL, "female", "adult"),
    Voice("el-charlotte", "Charlotte", "elevenlabs", "Charlotte", INTL, "female", "adult"),
    Voice("el-laura", "Laura", "elevenlabs", "Laura", INTL, "female", "adult"),
    Voice("el-matilda", "Matilda", "elevenlabs", "Matilda", INTL, "female", "mature"),
    Voice("el-rachel", "Rachel", "elevenlabs", "Rachel", INTL, "female", "mature"),
    Voice("el-lily", "Lily", "elevenlabs", "Lily", INTL, "female", "young"),
    Voice("el-alice", "Alice", "elevenlabs", "Alice", INTL, "female", "young"),
    Voice("el-liam", "Liam", "elevenlabs", "Liam", INTL, "male", "young"),
    Voice("el-will", "Will", "elevenlabs", "Will", INTL, "male", "young"),
    Voice("el-george", "George", "elevenlabs", "George", INTL, "male", "adult"),
    Voice("el-brian", "Brian", "elevenlabs", "Brian", INTL, "male", "adult"),
    Voice("el-bill", "Bill", "elevenlabs", "Bill", INTL, "male", "mature"),
    Voice("el-daniel", "Daniel", "elevenlabs", "Daniel", INTL, "male", "mature"),
]
_BY_ID = {v.id: v for v in VOICES}
_BY_LABEL = {v.label.lower(): v for v in VOICES}
_BY_REF = {v.ref.lower(): v for v in VOICES}


def resolve(name: str) -> Voice | None:
    """A registry id, a label, a provider voice name, or a raw ElevenLabs voice ID."""
    key = (name or "").strip()
    if not key:
        return None
    v = _BY_ID.get(key) or _BY_LABEL.get(key.lower()) or _BY_REF.get(key.lower())
    if v:
        return v
    # Raw ElevenLabs voice IDs are 20 URL-safe chars — let one through as a custom voice.
    if len(key) >= 18 and " " not in key:
        return Voice(key, f"Custom · {key[:8]}…", "elevenlabs", key, INDIAN, "female", "adult")
    return None


def pool(accent: str, gender: str, age: str) -> list[Voice]:
    """Voices for a band, preferring the requested accent but never returning nothing."""
    exact = [v for v in VOICES if v.accent == accent and v.gender == gender and v.age == age]
    # Age before accent when there is no exact match: a child role read by an adult voice is a
    # worse mistake than a child voice with the wrong accent (there is no Indian child voice).
    right_age = [v for v in VOICES if v.gender == gender and v.age == age]
    same_accent = [v for v in VOICES if v.accent == accent and v.gender == gender]
    return exact or right_age or same_accent or list(VOICES)


_FEMALE_WORDS = ("mother", "amma", "amamma", "ammamma", "mom", "mum", "woman", "girl", "daughter",
                 "grandmother", "granny", "aunt", "wife", "sister", "female", "she", "lady",
                 "nani", "paati", "akka", "bride")
_MALE_WORDS = ("father", "appa", "dad", "man", "boy", "son", "grandfather", "thatha", "uncle",
               "husband", "brother", "male", "he", "farmer", "shopkeeper", "grandson", "anna")
_YOUNG_WORDS = ("child", "kid", "boy", "girl", "young", "school", "toddler", "baby", "son",
                "daughter", "teen", "little", "grandson", "granddaughter", "kanna")
_MATURE_WORDS = ("elderly", "old", "grandmother", "grandfather", "granny", "ammamma", "thatha",
                 "nani", "paati", "senior", "veteran", "aged", "60s", "70s", "80s")

# Performance notes -> delivery. Nothing here is ever spoken aloud.
_DELIVERY = [
    (("whisper", "hushed", "quiet", "soft", "murmur"), {"stability": 0.40, "style": 0.20}),
    (("excited", "giggl", "laugh", "delight", "playful", "cheer", "joy"),
     {"stability": 0.30, "style": 0.50}),
    (("sleep", "drowsy", "yawn", "tired", "weary"), {"stability": 0.50, "style": 0.25,
                                                     "speed": 0.95}),
    (("urgent", "hurry", "shout", "call", "loud", "insist"), {"stability": 0.35, "style": 0.45,
                                                              "speed": 1.05}),
    (("sad", "wistful", "tender", "emotional", "moved"), {"stability": 0.45, "style": 0.35}),
    (("proud", "confident", "firm"), {"stability": 0.50, "style": 0.30}),
    (("warm", "gentle", "calm", "patient", "kind", "smile", "reassur"),
     {"stability": 0.55, "style": 0.15}),
]


def delivery_for(emotion: str) -> dict:
    """Map a performance note ('elderly, hushed, a smile in her voice') to TTS settings."""
    low = (emotion or "").lower()
    out = {"stability": 0.50, "style": 0.15}
    for words, settings in _DELIVERY:
        if any(w in low for w in words):
            out.update(settings)
            break
    return out


def _has(low: str, words) -> bool:
    """Whole-word match — substring tests would make 'she' hit 'sheet' and 'he' hit 'the'."""
    return any(re.search(rf"\b{re.escape(w)}\b", low) for w in words)


def _band(hints: str) -> str:
    low = (hints or "").lower()
    fem = _has(low, _FEMALE_WORDS)
    masc = _has(low, _MALE_WORDS)
    gender = "female" if fem and not masc else ("male" if masc and not fem else
                                                ("female" if fem else "male"))
    if _has(low, _MATURE_WORDS):
        age = "mature"
    elif _has(low, _YOUNG_WORDS):
        age = "young"
    else:
        age = "adult"
    return f"{gender}_{age}"


def _sheet_hint(characters: str, who: str) -> str:
    """Only the part of the cast sheet that names THIS speaker.

    Feeding the whole sheet into every speaker's hints lets other characters' ages and genders
    outvote the one being cast — which is how a "Boy" ended up with a mature female voice.
    """
    who = (who or "").strip().lower()
    if not who or not characters:
        return ""
    for part in re.split(r"[;.\n|]", characters):
        if re.search(rf"\b{re.escape(who)}\b", part.lower()):
            return part
    return ""


# --- segments -----------------------------------------------------------------------------
@dataclass
class Segment:
    kind: str                      # "vo" | "dialogue"
    text: str
    scene: int = 0                  # the script row this line belongs to
    speaker: str = ""
    emotion: str = ""
    language: str | None = None
    start: float = 0.0             # scene window, seconds
    end: float = 0.0
    voice: str = ""
    url: str | None = None
    settings: dict = field(default_factory=dict)

    @property
    def words(self) -> int:
        return len(self.text.split())


_CUE_LABELS = {"sfx", "music", "super", "supr", "title", "text", "card", "logo", "graphic",
               "vfx", "sound", "ambience", "ambient", "note", "camera", "on screen", "on-screen"}
_VO_LABELS = {"vo", "v.o", "v.o.", "voiceover", "voice over", "voice-over", "narrator",
              "narration", "anncr", "announcer"}
# Placeholders and stage notes a script uses to mean "nobody speaks here". Read aloud they are
# worse than silence, so they never reach the voice.
_EMPTY = {"", "-", "–", "—", "n/a", "na", "none", "silence", "no dialogue", "nil", "(silence)",
          "ambient", "ambience", "atmos", "ambient sound", "natural sound", "ambient / natural sound",
          "ambient/natural sound", "no vo", "no voiceover", "music only", "sfx only", "no speech",
          "wild track", "room tone", "beat", "pause"}

# NAME, optional (performance note), then a colon. Handles "Boy (young, half-asleep):" and "VO:".
# A label may only begin the string or follow a sentence end — otherwise the name greedily swallows
# the tail of the previous sentence ("...the pack shot. NARRATOR:" becoming one speaker) and
# the swallowed words are lost from the voiceover.
_NAME = (r"(?:V\.O\.|V\.O|VO"
         r"|[A-Za-z][\w'’\-]*(?:\s+[A-Za-z][\w'’\-]*){0,2})")
_LABEL_RE = re.compile(
    r"(?:^|(?<=[.!?…])\s+|(?<=\])\s*|(?<=\))\s*)"
    rf"({_NAME})\s*(?:\(([^)]*)\))?\s*:\s*")
_BRACKET_CUE = re.compile(r"\[[^\]]*\]")                     # [SFX: birds] — drop outright
_INLINE_PAREN = re.compile(r"\(([^)]*)\)")                   # (pouring milk) inside spoken text


def _clean_spoken(text: str) -> tuple[str, str]:
    """Strip inline stage directions from spoken text; return (spoken, extra_direction)."""
    notes = " ".join(m.group(1) for m in _INLINE_PAREN.finditer(text))
    text = _INLINE_PAREN.sub(" ", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" ;,-–—")
    return text, notes


def parse_dialogue(line: str) -> list[Segment]:
    """Fallback: split a prose `dialogue` cell into typed segments."""
    line = _BRACKET_CUE.sub(" ", str(line or "")).strip()
    if line.lower() in _EMPTY:
        return []
    runs, pos, label, note = [], 0, None, ""
    for m in _LABEL_RE.finditer(line):
        if m.start() > pos:
            runs.append((label, note, line[pos:m.start()]))
        label = m.group(1).strip().lower().rstrip(".")
        note = (m.group(2) or "").strip()
        pos = m.end()
    runs.append((label, note, line[pos:]))

    segs: list[Segment] = []
    for lab, nte, body in runs:
        if lab is not None and lab in _CUE_LABELS:
            continue                                   # a production cue: not spoken
        spoken, inline = _clean_spoken(body)
        if not spoken or spoken.lower() in _EMPTY:
            continue
        is_vo = lab is None or lab in _VO_LABELS
        segs.append(Segment(
            kind="vo" if is_vo else "dialogue",
            speaker="" if is_vo else lab.title(),
            emotion=" ".join(x for x in (nte, inline) if x),
            text=spoken))
    return segs


def _from_structured(items) -> list[Segment]:
    """Preferred path: the row's `audio` list, written by the studio."""
    segs = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        text, inline = _clean_spoken(str(it.get("text") or ""))
        if not text or text.lower() in _EMPTY:
            continue
        kind = str(it.get("type") or "vo").strip().lower()
        kind = "dialogue" if kind.startswith("dial") else "vo"
        speaker = str(it.get("speaker") or "").strip()
        if kind == "vo" or speaker.lower() in _VO_LABELS:
            kind, speaker = "vo", ""
        segs.append(Segment(
            kind=kind, speaker=speaker.title(),
            emotion=" ".join(x for x in (str(it.get("emotion") or "").strip(),
                                         str(it.get("age") or "").strip(), inline) if x),
            language=(str(it.get("language") or "").strip() or None),
            text=text))
    return segs


_TC_RE = re.compile(r"(\d+(?:[.:]\d+)?)\s*[-–—to]+\s*(\d+(?:[.:]\d+)?)")


def _window(tc, fallback: tuple[float, float]) -> tuple[float, float]:
    """'0–5s' / '5-11s' / '0:05-0:11' -> (start, end). Falls back to an even slice."""
    m = _TC_RE.search(str(tc or ""))
    if not m:
        return fallback

    def secs(v: str) -> float:
        if ":" in v:
            mm, ss = v.split(":")[:2]
            return int(mm) * 60 + float(ss)
        return float(v)
    try:
        a, b = secs(m.group(1)), secs(m.group(2))
    except ValueError:
        return fallback
    return (a, b) if b > a else fallback


def _scene_words(row: dict) -> int:
    """Spoken words in a row — from the structured `audio` list, else parsed from the prose."""
    if isinstance(row.get("audio"), list):
        segs = _from_structured(row["audio"])
    else:
        segs = parse_dialogue(row.get("dialogue"))
    return sum(s.words for s in segs)


def beats_for(seconds: float) -> list[int]:
    """The Veo beats (4/6/8s) that cover `seconds`, using as few clips as possible."""
    need = max(4, int(math.ceil(seconds)))
    lo, hi = min(_ALLOWED_BEATS), max(_ALLOWED_BEATS)
    for k in range((need + hi - 1) // hi, need // lo + 2):
        surplus = need - lo * k
        if surplus < 0:
            continue
        if surplus % 2:                       # beats step in 2s, so odd needs one more second
            surplus += 1
        if surplus > (hi - lo) * k:
            continue
        beats, i = [lo] * k, 0
        while surplus > 0 and i < k:
            room = min(hi - beats[i], surplus)
            beats[i] += room
            surplus -= room
            i += 1
        return sorted(beats, reverse=True)
    return [hi] * max(1, (need + hi - 1) // hi)


def scene_needs(rows) -> list[float]:
    """Seconds each scene's dialogue wants at natural pace — unsnapped, and only a demand, not a
    promise. A silent scene asks for the 4s minimum."""
    out = []
    for row in (rows or []):
        if not isinstance(row, dict):
            continue
        words = _scene_words(row)
        out.append((words / WORDS_PER_SEC + SPEECH_PAD) if words else 4.0)
    return out


def allocate(rows, total: int) -> list[int]:
    """Divide a FIXED total across the scenes, weighted by how much dialogue each one carries.

    The film's length is a media constraint — a 30s slot is 30 seconds — so the total never moves.
    What moves is where the seconds sit: every scene starts at Veo's 4s floor, then each spare 2s
    step goes to whichever scene is furthest short of what its dialogue wants. A talky scene holds
    longer, a quiet one cuts away sooner, and the beats still sum to exactly `total`.

    If the scene count alone exceeds the total (7 scenes cannot fit in 20s at 4s each) every scene
    gets the floor and the caller reports the overrun — that one is arithmetic, not a choice.
    """
    need = scene_needs(rows)
    n = len(need)
    if not n:
        return []
    floor = min(_ALLOWED_BEATS)
    per = [floor] * n
    for _ in range(max(0, int(total) - floor * n) // 2):
        # Furthest-behind first. Once every scene has what it asked for this keeps handing the
        # surplus to the least-served scene, so slack spreads instead of piling onto one shot.
        i = max(range(n), key=lambda k: need[k] - per[k])
        per[i] += 2
    return per


def film_tempo(rows, per_scene) -> float:
    """One delivery speed for the WHOLE film, so nothing lurches between cuts.

    Taken from the tightest scene: if any scene's lines cannot be said inside the seconds it was
    given, everything speeds up by the same factor, capped at MAX_TTS_SPEED. A per-scene speed
    would be gentler on paper and audibly jerky in practice.
    """
    need = scene_needs(rows)
    worst = 1.0
    for words_secs, secs in zip(need, per_scene):
        # The pad is a courtesy, not a requirement — only count it as 0.5s so the speed-up fires
        # when the words genuinely don't fit, not merely because the breathing room is tight.
        speech = max(0.0, words_secs - SPEECH_PAD) + 0.5
        if secs > 0:
            worst = max(worst, speech / secs)
    return min(MAX_TTS_SPEED, round(worst, 3))


def scene_seconds(rows, target_total: int = 0) -> list[int]:
    """Per-scene lengths. With a target the seconds are shared out inside it (see `allocate`);
    without one each scene simply takes what its dialogue needs."""
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    if target_total:
        return allocate(rows, int(target_total))
    return [sum(beats_for(x)) for x in scene_needs(rows)]


def retime(rows, target_total: int = 0) -> tuple[int, list[str]]:
    """Rewrite each row's `tc` so scene lengths follow the dialogue. Returns (total, notes).

    Mutates the rows so the script table, the storyboard and the render all agree on the timing.
    The total stays at `target_total`; only the split between scenes changes.
    """
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    if not rows:
        return max(4, int(target_total or 0)), []
    per = scene_seconds(rows, target_total)
    notes: list[str] = []
    at = 0
    for row, secs in zip(rows, per):
        row["tc"] = f"{at}–{at + secs}s"
        at += secs
    if target_total and at != target_total:
        notes.append(f"{len(rows)} scenes can't fit {target_total}s — Veo's shortest shot is 4s, so "
                     f"this cut runs {at}s. Merge two scenes to hold the {target_total}s length")
    tempo = film_tempo(rows, per)
    if tempo > 1.005:
        notes.append(f"dialogue runs long for {at}s — delivered {tempo:.2f}x faster across the "
                     f"whole film (one speed everywhere, so it doesn't lurch at the cuts)")
    return at, notes


def build_segments(rows, total: float) -> tuple[list[Segment], list[str]]:
    """Rows -> cast, budgeted, time-windowed segments. Also returns human-readable warnings."""
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    notes: list[str] = []
    segments: list[Segment] = []
    n = max(1, len(rows))
    for i, row in enumerate(rows):
        fallback = (total * i / n, total * (i + 1) / n)
        start, end = _window(row.get("tc"), fallback)
        start, end = max(0.0, min(start, total)), max(0.0, min(end, total))
        if end <= start:
            start, end = fallback
        # An `audio` list that is present but EMPTY means "this scene is deliberately silent" —
        # it must not fall through to prose parsing, or the stage note gets read aloud.
        if isinstance(row.get("audio"), list):
            segs = _from_structured(row["audio"])
        else:
            segs = parse_dialogue(row.get("dialogue"))
        if not segs:
            # The "empty VO" failure: a scene the writer meant to be spoken that yields no line and
            # passes in silence with no explanation. Placeholders like "Ambient" are deliberate and
            # stay quiet; anything else is reported, because a silent scene nobody asked for is
            # indistinguishable from a broken voice until someone says which it was.
            written = str(row.get("dialogue") or "").strip()
            structured = row.get("audio")
            if isinstance(structured, list):
                meant = any(str((x or {}).get("text") or "").strip() for x in structured)
            else:
                meant = bool(written) and written.lower() not in _EMPTY
            if meant:
                notes.append(f"scene {row.get('no', i + 1)}: nothing could be spoken from "
                             f"“{(written or 'these lines')[:60]}” — it reads as a stage "
                             f"direction or a placeholder, so this scene stays silent")
            continue
        # Scene length is derived FROM the dialogue (see scene_seconds/retime), so a line should
        # never need shortening. This stays only as a guard for a window fixed externally and
        # genuinely too short — otherwise the writing wins over the clock, not the other way round.
        budget = max(4, int((end - start) * WORDS_PER_SEC * 1.6))
        while sum(s.words for s in segs) > budget and len(segs) > 0:
            longest = max(segs, key=lambda s: s.words)
            if longest.words <= 4:
                break
            keep = max(4, longest.words - (sum(s.words for s in segs) - budget))
            trimmed = " ".join(longest.text.split()[:keep]).rstrip(",;:")
            if trimmed == longest.text:
                break
            longest.text = trimmed
            notes.append(f"scene {row.get('no', i + 1)}: line shortened to fit "
                         f"{end - start:.0f}s")
        for s in segs:
            s.start, s.end = start, end
            s.scene = int(row.get("no") or (i + 1))
        segments.extend(segs)
    return segments, notes


def cast(segments: list[Segment], narrator_voice: str, narrator_lang: str | None,
         characters: str = "", accent: str = INDIAN) -> dict[str, str]:
    """Assign a voice to narration and to each character, preferring `accent`.

    Narration keeps one voice for the whole film and it is never reused for a character.
    """
    narr = resolve(narrator_voice)
    if not narr:
        narr = pool(accent, "female", "adult")[0]
    used = {narr.id}
    assigned: dict[str, str] = {}
    for seg in segments:
        if seg.kind == "vo":
            seg.voice = narr.id
            seg.language = seg.language or narrator_lang
            seg.settings = delivery_for(seg.emotion)
            continue
        who = seg.speaker or "Character"
        if who not in assigned:
            band = _band(f"{who} {seg.emotion} {_sheet_hint(characters, who)}")
            gender, age = band.split("_")
            options = pool(accent, gender, age)
            pick = next((v for v in options if v.id not in used), options[0])
            assigned[who] = pick.id
            used.add(pick.id)
        seg.voice = assigned[who]
        seg.language = seg.language or narrator_lang
        seg.settings = delivery_for(seg.emotion)
    return assigned


def voice_catalog() -> list[dict]:
    """Every voice the studio can cast, labelled and grouped for the picker."""
    age_word = {"young": "young", "adult": "adult", "mature": "mature"}
    return [{"id": v.id, "label": v.label, "accent": v.accent,
             "group": f"{v.accent} · {v.gender} · {age_word.get(v.age, v.age)}"}
            for v in VOICES]


def apply_overrides(segments: list[Segment], choices: dict, narrator: str) -> str:
    """Honour the user's own casting. `choices` maps speaker (or 'Narration') to a voice id."""
    choices = {str(k).strip().lower(): str(v).strip() for k, v in (choices or {}).items() if v}
    want_narr = resolve(choices.get("narration") or choices.get("narrator") or "")
    if want_narr:
        narrator = want_narr.id
    for seg in segments:
        if seg.kind == "vo":
            seg.voice = narrator
            continue
        v = resolve(choices.get((seg.speaker or "").lower(), ""))
        if v:
            seg.voice = v.id
    return narrator


def plan(segments: list[Segment], narrator: str) -> dict:
    """A readable account of exactly what will be said, by whom, in which voice and when."""
    speakers: dict[str, str] = {"Narration": narrator}
    for s in segments:
        if s.kind == "dialogue" and s.speaker:
            speakers[s.speaker] = s.voice
    return {
        "narrator": narrator,
        "cast": [{"speaker": k, "voice_id": v, "voice": voice_label(v)}
                 for k, v in speakers.items()],
        "lines": [{"scene": s.scene or (i + 1), "kind": s.kind, "speaker": s.speaker or "Narration",
                   "voice": voice_label(s.voice), "voice_id": s.voice,
                   "text": s.text, "emotion": s.emotion,
                   "start": round(s.start, 1), "end": round(s.end, 1), "words": s.words,
                   "est_seconds": round(s.words / WORDS_PER_SEC, 1)}
                  for i, s in enumerate(segments)],
        "words": sum(s.words for s in segments),
    }


def voice_label(vid: str) -> str:
    v = resolve(vid)
    return v.label if v else (vid or "")


def _tts_args(seg: Segment) -> tuple[str, dict]:
    """Build the provider-specific request for one line. Param names differ per provider."""
    v = resolve(seg.voice) or pool(INDIAN, "female", "adult")[0]
    if v.provider == "kokoro":
        # Kokoro takes `prompt` (not `text`) and exposes no delivery controls.
        return KO_MODEL, {"prompt": seg.text, "voice": v.ref}
    if v.provider == "minimax":
        setting = {"voice_id": v.ref, "speed": seg.settings.get("speed", 1) or 1,
                   "vol": 1, "pitch": v.pitch}
        return MM_MODEL, {"text": seg.text, "voice_setting": setting}
    args = {"text": seg.text, "voice": v.ref, "similarity_boost": 0.8}
    args.update({k: val for k, val in seg.settings.items()
                 if k in ("stability", "style", "speed")})
    if seg.language:
        args["language_code"] = seg.language
    return EL_MODEL, args


def synth(segments: list[Segment], max_workers: int = 4) -> int:
    """Synthesise every segment (in parallel). Returns how many produced audio."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    import filmaudio

    def one(seg: Segment):
        model, args = _tts_args(seg)
        url = filmaudio.run_fal(model, args)
        if url:
            return seg, url, ""
        # A voice the account can't reach (a pasted ElevenLabs ID that isn't in the library, say)
        # must not silently drop the line — fall back to a stock voice and report which.
        chosen = resolve(seg.voice)
        fallback = pool(INDIAN, "female" if (chosen is None or chosen.gender == "female") else "male",
                        chosen.age if chosen else "adult")[0]
        if not chosen or fallback.id != chosen.id:
            seg.voice = fallback.id
            model, args = _tts_args(seg)
            url = filmaudio.run_fal(model, args)
            if url:
                who = seg.speaker or "narration"
                return seg, url, (f"{who}: voice '{chosen.ref if chosen else '?'}' unavailable — "
                                  f"used {fallback.label} instead")
        return seg, None, f"{seg.speaker or 'narration'}: voice generation failed"

    ok, notes = 0, []
    # NB: not named `pool` — that would shadow this module's pool() helper, which one() calls to
    # find a fallback voice, and the fallback would die with "object is not callable".
    with ThreadPoolExecutor(max_workers=min(max_workers, max(1, len(segments)))) as ex:
        for fut in as_completed([ex.submit(one, s) for s in segments]):
            try:
                seg, url, note = fut.result()
                if note:
                    notes.append(note)
            except Exception as e:
                print(f"[filmvoice] segment failed: {e}", file=sys.stderr, flush=True)
                continue
            seg.url = url
            ok += 1 if url else 0
    for s in segments:
        print(f"[filmvoice] {s.kind:8s} {s.speaker or 'NARRATOR':14s} {voice_label(s.voice):18s} "
              f"{s.start:5.1f}-{s.end:4.1f}s {s.words:3d}w "
              f"{'ok' if s.url else 'FAILED'}  \"{s.text[:52]}\"",
              file=sys.stderr, flush=True)
    return ok, notes
