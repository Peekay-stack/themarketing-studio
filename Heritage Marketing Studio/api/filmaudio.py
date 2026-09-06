"""filmaudio.py — build the soundtrack and lay it over the joined film.

Video models score each clip independently, so per-shot audio restarts at every cut. Instead we
render the picture SILENT, join it, and build the soundtrack here: narration and character dialogue
as separately-cast, separately-timed voice segments (see filmvoice), plus one instrumental bed for
the whole film, mixed over the finished cut.

Each voice segment is placed at its scene's timecode rather than concatenated into one blob, so the
read stays in sync with the picture. Where the dialogue is too long for the film, ONE speed-up is
applied to every line (see mix_timeline) rather than tightening the offending line alone — a single
brisk read beats a read that lurches at one cut. Narration keeps one voice throughout; characters
get their own.

Rendering silent is also cheaper: Veo charges roughly half without audio.

Providers (all on fal, verified against the account):
  Voice fal-ai/elevenlabs/tts/multilingual-v2   (Indian-English / Hindi capable, per-line settings)
  Music fal-ai/elevenlabs/music                 (force_instrumental + exact music_length_ms)
        cassetteai/music-generator              (fallback; prompt + duration in seconds)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

TTS_MODEL = "fal-ai/elevenlabs/tts/multilingual-v2"
MUSIC_MODEL = "fal-ai/elevenlabs/music"
MUSIC_FALLBACK = "cassetteai/music-generator"

MUSIC_UNDER_VO = 0.18     # default bed level when there's a voiceover over it
MUSIC_ALONE = 0.55        # bed level when the film has no VO
MAX_VO_STRETCH = 1.2      # ElevenLabs' own speed ceiling; also our atempo limit
# TTS comes back mono, and amix inherited that, so films were delivered as single-channel audio —
# fine to review, not something you hand a broadcaster. Force two channels on every mix: the bed
# keeps its own stereo image and the voice sits centred.
CHANNELS = "2"

# How loud the bed sits under the voice. "Bed too loud / too quiet" is a judgement call, so it is
# a choice in the UI rather than a constant only I can change.
MUSIC_LEVELS = {"subtle": 0.10, "balanced": 0.18, "forward": 0.30}

# Ambience sits UNDER the music, which sits under the voice. That order is the whole point of having
# three separate beds rather than one: room tone is meant to be believed rather than noticed, so it
# runs lower than the score and never competes with a line. Named levels for the same reason the music
# ones are named — "too loud" is a judgement, not a constant.
AMBIENCE_LEVELS = {"barely": 0.06, "present": 0.12, "location": 0.22}
AMBIENCE_DEFAULT = "present"

# A foley spot is placed, not bedded, so it needs to be heard — it is the clank or the pour that makes
# a shot feel recorded rather than rendered. Higher than either bed by design, and still under a line.
SFX_GAIN = 0.7


def ambience_level(name) -> float:
    """The named ambience level, defaulting rather than raising — an unknown name from a client is a
    reason to mix at a sensible level, not a reason to fail a whole render."""
    return AMBIENCE_LEVELS.get(str(name or "").strip().lower(), AMBIENCE_LEVELS[AMBIENCE_DEFAULT])


def music_level(name, has_voice: bool = True) -> float:
    if not has_voice:
        return MUSIC_ALONE
    if isinstance(name, (int, float)):
        return max(0.02, min(1.0, float(name)))
    return MUSIC_LEVELS.get(str(name or "").strip().lower(), MUSIC_UNDER_VO)


# Named music styles, each with the wording that actually steers the model. Free text stays
# supported — a style just gives a reliable starting point and something to audition against.
MUSIC_STYLES: list[dict] = [
    {"id": "warm-strings", "label": "Warm strings",
     "prompt": "Warm, tender string ensemble with soft sustained pads; gentle and reassuring."},
    {"id": "indian-flute", "label": "Gentle Indian flute",
     "prompt": "Solo bansuri flute over soft tanpura drone and light strings; serene, pastoral, "
               "unmistakably Indian."},
    {"id": "tabla-light", "label": "Tabla & light percussion",
     "prompt": "Light tabla groove with plucked sitar accents and soft strings; warm, rhythmic, "
               "everyday-morning energy."},
    {"id": "festive-dhol", "label": "Festive dhol",
     "prompt": "Celebratory dhol and shehnai with rising brass; festive, communal, joyous."},
    {"id": "devotional", "label": "Devotional / temple",
     "prompt": "Reverent harmonium and temple bells with a low drone; calm, devotional, timeless."},
    {"id": "piano-ambient", "label": "Ambient piano",
     "prompt": "Sparse felt-piano motif with airy ambient pads; intimate, modern, unhurried."},
    {"id": "cinematic", "label": "Cinematic orchestral",
     "prompt": "Cinematic orchestral build — strings, soft horns and light timpani; premium and "
               "emotive with a clear lift."},
    {"id": "upbeat-modern", "label": "Modern upbeat",
     "prompt": "Bright modern acoustic pop bed — claps, plucked guitar, warm bass; optimistic and "
               "contemporary."},
]
_MUSIC_BY_ID = {m["id"]: m for m in MUSIC_STYLES}


def music_prompt(style_or_mood: str) -> str:
    """A named style id, or free text, into the full generation prompt."""
    key = str(style_or_mood or "").strip()
    base = _MUSIC_BY_ID.get(key, {}).get("prompt") or key or "Warm, tender string ensemble."
    return (f"{base} Instrumental score for a premium Indian dairy brand film — warm, wholesome, "
            "uplifting, gentle Indian instrumentation. No vocals, no lyrics.")

# ElevenLabs voice names, picked for warm brand-film reads.
_FEMALE, _MALE = "Sarah", "George"
_KNOWN_VOICES = {v.lower(): v for v in (
    "Rachel", "Sarah", "Laura", "Charlotte", "Alice", "Matilda", "Lily", "Jessica", "Aria",
    "George", "Brian", "Daniel", "Callum", "Liam", "Will", "Eric", "Chris", "Roger", "Bill")}


def pick_voice(hint: str) -> tuple[str, str | None]:
    """Map the studio's free-text voiceover field onto (ElevenLabs voice, language_code).

    'Warm female (Telugu-accented English)' -> ('Sarah', 'en');  'Hindi male' -> ('George', 'hi').
    An exact voice name typed by the user wins.
    """
    text = (hint or "").strip()
    low = text.lower()
    for name in re.findall(r"[A-Za-z]+", text):
        if name.lower() in _KNOWN_VOICES:
            voice = _KNOWN_VOICES[name.lower()]
            break
    else:
        voice = _MALE if re.search(r"\bmale\b", low) and "female" not in low else _FEMALE
    lang = None
    for word, code in (("hindi", "hi"), ("telugu", "te"), ("tamil", "ta"),
                       ("kannada", "kn"), ("marathi", "mr"), ("bengali", "bn")):
        if word in low:
            # Indic language named with "-accented English" still means an English read.
            lang = "en" if "english" in low else code
            break
    return voice, lang or ("en" if low else None)


def _dig_audio_url(result) -> str | None:
    if not isinstance(result, dict):
        return None
    for key in ("audio", "audio_file", "audio_url", "output"):
        v = result.get(key)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
        if isinstance(v, str) and v.startswith("http"):
            return v
    if isinstance(result.get("url"), str):
        return result["url"]
    return None


def run_fal(model: str, args: dict) -> str | None:
    """Call a fal audio model and dig the URL out. Shared with filmvoice."""
    import fal_client  # type: ignore
    try:
        return _dig_audio_url(fal_client.subscribe(model, arguments=args, with_logs=False))
    except Exception as e:
        print(f"[filmaudio] {model} failed: {e}", file=sys.stderr, flush=True)
        return None


_run_fal = run_fal          # kept for existing callers


def synth_vo(text: str, voice_hint: str = "") -> str | None:
    """One narration blob in a single call. Superseded by the segment pipeline (filmvoice);
    retained for callers that just want a single continuous read."""
    text = (text or "").strip()
    if not text:
        return None
    voice, lang = pick_voice(voice_hint)
    args = {"text": text, "voice": voice, "stability": 0.45, "similarity_boost": 0.8}
    if lang:
        args["language_code"] = lang
    print(f"[filmaudio] VO: voice={voice} lang={lang} chars={len(text)}", file=sys.stderr, flush=True)
    return run_fal(TTS_MODEL, args)


def synth_music(mood: str, seconds: int) -> str | None:
    """One instrumental bed covering the full film length. `mood` may be a style id or free text."""
    prompt = music_prompt(mood)
    ms = max(10_000, min(300_000, int(seconds) * 1000))
    url = _run_fal(MUSIC_MODEL, {"prompt": prompt, "music_length_ms": ms,
                                 "force_instrumental": True})
    if not url:
        print("[filmaudio] falling back to cassetteai for music", file=sys.stderr, flush=True)
        url = _run_fal(MUSIC_FALLBACK, {"prompt": prompt, "duration": max(1, min(180, int(seconds)))})
    return url


def probe_duration(exe: str, path: str) -> float | None:
    """Length of a media file in seconds, via ffmpeg's own stderr banner (no ffprobe needed)."""
    out = subprocess.run([exe, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration:\s*(\d+):(\d\d):(\d\d(?:\.\d+)?)", out)
    if not m:
        return None
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def _download(url: str, dest: str) -> bool:
    import httpx
    try:
        # A locally-stored asset (Google returns bytes, so they live on disk) needs no HTTP.
        import shutil

        import gemini
        src = gemini.local_path(url)
        if src:
            shutil.copyfile(src, dest)
            return True
        with httpx.stream("GET", url, timeout=180.0, follow_redirects=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as fh:
                fh.writelines(r.iter_bytes(1 << 16))
        return True
    except Exception as e:
        print(f"[filmaudio] download failed: {e}", file=sys.stderr, flush=True)
        return False


def _measure(exe: str, placed, tmp: str, span: float, notes: list) -> tuple[list, float]:
    """Fetch and measure every line, then settle on ONE delivery speed for the whole film.

    The tightest scene sets the pace, and so does the film as a whole; the result is capped at
    MAX_VO_STRETCH. Applying a single factor everywhere is the point — tightening only the offending
    line is gentler on paper and makes the read lurch at that one cut, which is far more audible
    than a film that is uniformly a shade brisk. Returns [(segment, file, natural duration)] and the
    speed to play them at, so the audition and the final mix can share both.
    """
    takes: list[tuple] = []
    for n, seg in enumerate(placed):
        path = os.path.join(tmp, f"seg{n:02d}.mp3")
        if not _download(seg.url, path):
            notes.append(f"{seg.speaker or 'narration'} line dropped (download failed)")
            continue
        dur = probe_duration(exe, path) or 0.0
        if dur > 0:
            takes.append((seg, path, dur))
    tempo = 1.0
    for seg, _path, dur in takes:
        room = max(1.0, min(seg.end, span or seg.end) - seg.start)
        tempo = max(tempo, dur / room)        # the tightest scene...
    spoken = sum(d for _s, _p, d in takes) + 0.18 * max(0, len(takes) - 1)
    if span:
        tempo = max(tempo, spoken / span)     # ...and the film as a whole
    tempo = min(MAX_VO_STRETCH, round(tempo, 3))
    if tempo > 1.005:
        notes.append(f"whole film read {tempo:.2f}x faster so the dialogue fits without cutting "
                     f"words (one speed throughout, so it doesn't lurch at the cuts)")
    return takes, tempo


def preview_audio(exe: str, seconds: float, out_path: str, segments,
                  music: str | None = None, tmp_dir: str | None = None,
                  level=None) -> tuple[bool, list[str]]:
    """The soundtrack alone, as an mp3 — so the mix can be judged without rendering any video.

    Same placement rules as the real mix, over silence instead of picture — including the single
    film-wide speed, so what you approve here is what the render sounds like.
    """
    import tempfile
    notes: list[str] = []
    placed = [s for s in (segments or []) if getattr(s, "url", None)]
    if not placed and not music:
        return False, ["no audio to preview"]
    tmp = tmp_dir or tempfile.mkdtemp(prefix="vo-preview-")
    takes, tempo = _measure(exe, placed, tmp, max(1.0, seconds), notes)
    inputs = ["-f", "lavfi", "-t", f"{max(1.0, seconds):.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
    filters, labels = [], ["[0:a]"]
    idx = 1
    cursor = 0.0
    for n, (seg, path, dur) in enumerate(takes):
        start = max(seg.start, cursor)
        eff = dur / tempo
        inputs += ["-i", path]
        chain = f"[{idx}:a]"
        if tempo > 1.001:
            chain += f"atempo={tempo:.3f},"
        filters.append(f"{chain}adelay={int(start * 1000)}:all=1[p{n}]")
        labels.append(f"[p{n}]")
        cursor = start + eff + 0.18
        idx += 1
    if music:
        mpath = os.path.join(tmp, "bed.mp3")
        if _download(music, mpath):
            inputs += ["-i", mpath]
            filters.append(f"[{idx}:a]volume="
                           f"{music_level(level, has_voice=len(labels) > 1)},"
                           "afade=t=in:st=0:d=1.2[bed]")
            labels.append("[bed]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:"
                   "dropout_transition=0:normalize=0,alimiter=limit=0.95[aout]")
    cmd = [exe, "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[aout]",
           "-t", f"{max(1.0, seconds):.3f}", "-c:a", "libmp3lame", "-b:a", "192k",
           "-ac", CHANNELS, out_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return False, notes + ["preview timed out"]
    if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return True, notes
    print(f"[filmaudio] preview failed ({res.returncode}): {res.stderr[-400:]}",
          file=sys.stderr, flush=True)
    return False, notes + ["preview mix failed"]


def mix_timeline(exe: str, video: str, out_path: str, segments, music: str | None = None,
                 tmp_dir: str | None = None, level=None, ambience: str | None = None,
                 ambience_level_name=None, spots=None) -> tuple[bool, list[str]]:
    """Place each voice segment at its scene's timecode and mix with the music bed, an ambience bed
    and any foley spots.

    Segments are laid out in script order, each anchored to its scene start but never overlapping
    the previous line (a line that runs long pushes the next one later).

    Delivery speed is decided once for the whole film by `_measure`, then applied to every line.

    `ambience` is a second bed, mixed under the music — room tone for the whole film. `spots` is a
    list of `{url, at, gain?}` foley placements: one sound at one moment, delayed to `at` seconds.
    Both are additive; a film with neither mixes exactly as it did before they existed.
    """
    import tempfile
    notes: list[str] = []
    placed = [s for s in (segments or []) if getattr(s, "url", None)]
    spots = [s for s in (spots or []) if isinstance(s, dict) and str(s.get("url") or "").strip()]
    if not placed and not music and not ambience and not spots:
        return False, ["no audio to mix"]
    tmp = tmp_dir or tempfile.mkdtemp(prefix="vo-audio-")
    picture = probe_duration(exe, video) or 0.0

    takes, tempo = _measure(exe, placed, tmp, picture, notes)
    inputs, filters, labels = ["-i", video], [], []
    cursor, idx = 0.0, 1                      # input 0 is the picture
    for n, (seg, path, dur) in enumerate(takes):
        start = max(seg.start, cursor)        # never talk over the previous line
        eff = dur / tempo
        if picture and start + eff > picture + 0.25:
            notes.append(f"{seg.speaker or 'narration'} line still runs past the end of the cut at "
                         f"{tempo:.2f}x — shorten it or give that scene more seconds")
        inputs += ["-i", path]
        chain = f"[{idx}:a]"
        if tempo > 1.001:
            chain += f"atempo={tempo:.3f},"
        chain += f"adelay={int(start * 1000)}:all=1[v{n}]"
        filters.append(chain)
        labels.append(f"[v{n}]")
        print(f"[filmaudio] place {seg.kind:8s} {seg.speaker or 'NARRATOR':12s} "
              f"at {start:5.1f}s len {eff:4.1f}s ({seg.voice})", file=sys.stderr, flush=True)
        cursor = start + eff + 0.18            # small breath between lines
        idx += 1

    # Foley spots. Placed like a line rather than bedded like music: each one is delayed to its own
    # moment. `at` past the end of the picture is reported rather than silently dropped — a spot that
    # never plays is indistinguishable from one that was never added, which is the kind of silence
    # nobody notices until a review.
    voice_labels = len(labels)
    for n, sp in enumerate(spots):
        spath = os.path.join(tmp, f"sfx{n}.mp3")
        if not _download(str(sp.get("url") or ""), spath):
            notes.append(f"foley spot {n + 1} could not be fetched")
            continue
        try:
            at = max(0.0, float(sp.get("at") or 0))
        except (TypeError, ValueError):
            at = 0.0
        if picture and at > picture:
            notes.append(f"foley spot {n + 1} is placed at {at:.1f}s, past the end of a "
                         f"{picture:.1f}s cut — it will not be heard")
        try:
            gain = float(sp.get("gain") or SFX_GAIN)
        except (TypeError, ValueError):
            gain = SFX_GAIN
        inputs += ["-i", spath]
        filters.append(f"[{idx}:a]volume={gain},adelay={int(at * 1000)}:all=1[s{n}]")
        labels.append(f"[s{n}]")
        idx += 1

    if music:
        mpath = os.path.join(tmp, "bed.mp3")
        if _download(music, mpath):
            inputs += ["-i", mpath]
            # `has_voice` counts VOICE labels only. Passing `bool(labels)` here would have meant a
            # film with foley and no narration got the quiet under-VO bed level, ducking the score
            # under speech that does not exist.
            vol = music_level(level, has_voice=bool(voice_labels))
            filters.append(f"[{idx}:a]volume={vol},afade=t=in:st=0:d=1.2[bed]")
            labels.append("[bed]")
            idx += 1
        else:
            notes.append("music bed unavailable")

    if ambience:
        apath = os.path.join(tmp, "ambience.mp3")
        if _download(ambience, apath):
            inputs += ["-i", apath]
            avol = ambience_level(ambience_level_name)
            filters.append(f"[{idx}:a]volume={avol},afade=t=in:st=0:d=1.5[amb]")
            labels.append("[amb]")
            idx += 1
        else:
            notes.append("ambience bed unavailable")

    if not labels:
        return False, notes or ["no audio survived"]

    if len(labels) > 1:
        # normalize=0 is essential: amix otherwise divides by the number of inputs and the whole
        # mix goes quiet as more lines are added.
        filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:"
                       "dropout_transition=0:normalize=0,alimiter=limit=0.95[aout]")
    else:
        filters.append(f"{labels[0]}alimiter=limit=0.95[aout]")

    cmd = [exe, "-y", *inputs, "-filter_complex", ";".join(filters),
           "-map", "0:v:0", "-map", "[aout]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", CHANNELS,
           "-movflags", "+faststart"]
    cmd += ["-t", f"{picture:.3f}"] if picture else ["-shortest"]
    cmd += [out_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return False, notes + ["audio mix timed out"]
    if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"[filmaudio] mixed {len(labels)} track(s) -> {os.path.basename(out_path)}",
              file=sys.stderr, flush=True)
        return True, notes
    print(f"[filmaudio] mix failed ({res.returncode}): {res.stderr[-500:]}",
          file=sys.stderr, flush=True)
    return False, notes + ["audio mix failed"]


def mux(exe: str, video: str, out_path: str, vo: str | None = None,
        music: str | None = None) -> bool:
    """Lay VO and/or the music bed over the (silent) cut.

    The bed sits well under the voice when there is one. If the VO overruns the picture we nudge it
    up to 1.2x rather than letting it get clipped mid-sentence; music is simply trimmed to picture.
    """
    if not vo and not music:
        return False
    inputs = ["-i", video]
    filters, mix_labels = [], []
    if vo:
        inputs += ["-i", vo]
        vo_idx = len(mix_labels) + 1
        chain = f"[{vo_idx}:a]"
        v_len, a_len = probe_duration(exe, video), probe_duration(exe, vo)
        if v_len and a_len and a_len > v_len + 0.35:
            tempo = min(MAX_VO_STRETCH, a_len / v_len)
            chain += f"atempo={tempo:.3f},"
            print(f"[filmaudio] VO {a_len:.1f}s over {v_len:.1f}s picture -> atempo {tempo:.3f}",
                  file=sys.stderr, flush=True)
        filters.append(f"{chain}apad,volume=1.0[vo]")
        mix_labels.append("[vo]")
    if music:
        inputs += ["-i", music]
        m_idx = len(mix_labels) + 1
        level = MUSIC_UNDER_VO if vo else MUSIC_ALONE
        filters.append(f"[{m_idx}:a]volume={level},afade=t=in:st=0:d=1.2[bed]")
        mix_labels.append("[bed]")
    if len(mix_labels) == 2:
        filters.append("[vo][bed]amix=inputs=2:duration=longest:dropout_transition=0,"
                       "alimiter=limit=0.95[aout]")
    else:
        filters.append(f"{mix_labels[0]}alimiter=limit=0.95[aout]")
    cmd = [exe, "-y", *inputs, "-filter_complex", ";".join(filters),
           "-map", "0:v:0", "-map", "[aout]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", CHANNELS,
           "-movflags", "+faststart"]
    # `apad` is deliberately unbounded so the bed never cuts out early; bound the OUTPUT to the
    # picture instead. (`-shortest` is unreliable next to `-c:v copy` and can hang.)
    picture = probe_duration(exe, video)
    cmd += ["-t", f"{picture:.3f}"] if picture else ["-shortest"]
    cmd += [out_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print("[filmaudio] ffmpeg mux timed out", file=sys.stderr, flush=True)
        return False
    if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"[filmaudio] mixed {'VO+music' if vo and music else ('VO' if vo else 'music')} "
              f"-> {os.path.basename(out_path)}", file=sys.stderr, flush=True)
        return True
    print(f"[filmaudio] ffmpeg mux failed ({res.returncode}): {res.stderr[-400:]}",
          file=sys.stderr, flush=True)
    return False
