"""takeqa.py -- cheap checks on ONE generated clip (film builder slice S5, FILM_BUILDER_PLAN.md): the "ok" a render reports is not proof (28 Oct: a 'successful' 30 s film held one frame for ten
seconds), so every take is looked at before the person spends more. Deterministic, no model, a second or two of ffmpeg: advisory chips on the take, never a block.

Thresholds are MEASURED, not guessed (28 Oct 2026, 37 real clips from Omni, Kling, Veo, Wan, Seedance, MiniMax plus synthetic known-bad ones, see FILM_BUILDER_PLAN.md S5):
  * real clips never move less than a span of about 4 (mean abs difference of the 64x36 gray first vs last sampled frame, 0-255); a frozen picture is 0.0 -> "still" below 2.0;
  * real clips never average below a brightness of about 74 (0-255); a black clip is 2 -> "black" below 15, a "dark frame" below 12 at any sampled point;
  * clips animated from the SAME frame start within 1-8 of each other at their first frame, clips of genuinely different shots start 56 or more apart -> "repeat" below 15.
A check that cannot read the file says so ("readable"); it never guesses.
"""
from __future__ import annotations

import subprocess

import filmcut

SAMPLES = 7                    # frames looked at, evenly across the clip (6 % to 94 %)
STILL_SPAN = 2.0               # first-vs-last difference below this AND every neighbouring difference below STILL_STEP = barely moves
STILL_STEP = 1.0
BLACK_MEAN = 15.0              # average brightness below this = almost black
DARK_FRAME = 12.0              # any sampled frame below this (when the clip is not black overall) = a nearly black frame
SHORT_BY = 0.3                 # seconds a clip may fall short of what was ordered before it is called short
REPEAT_BELOW = 15.0            # first-frame difference to the previous shot's clip below this = the same starting picture

LABELS = {"readable": "Won't play", "still": "Barely moves", "black": "Black", "short": "Shorter than ordered", "repeat": "Repeats the previous shot"}


def _mad(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / max(1, len(a))


def _check(cid: str, bad: bool, note: str = "") -> dict:
    return {"id": cid, "label": LABELS[cid], "verdict": "check" if bad else "ok", "note": note if bad else ""}


def measure(exe: str, path: str, n: int = SAMPLES) -> dict | None:
    """What the clip looks like, in numbers, or None when it cannot be read: {duration, adjacent: [neighbour differences], span, mean_luma, min_luma, min_luma_at, first}."""
    d = filmcut.probe_seconds(exe, path)
    if d <= 0:
        return None
    ts = [d * (0.06 + 0.88 * i / max(1, n - 1)) for i in range(n)]
    sigs = [(t, filmcut._frame_signature(exe, path, t)) for t in ts]
    sigs = [(t, s) for t, s in sigs if s]
    if len(sigs) < 3:
        return None
    lum = [(t, sum(s) / len(s)) for t, s in sigs]
    low = min(lum, key=lambda x: x[1])
    return {"duration": round(d, 2), "adjacent": [round(_mad(a[1], b[1]), 2) for a, b in zip(sigs, sigs[1:])], "span": round(_mad(sigs[0][1], sigs[-1][1]), 2),
            "mean_luma": round(sum(v for _, v in lum) / len(lum), 1), "min_luma": round(low[1], 1), "min_luma_at": round(low[0], 1),
            "first": filmcut._frame_signature(exe, path, d * 0.03)}


def check_clip(exe: str, path: str, ordered_seconds: float = 0.0, prev_path: str | None = None) -> dict:
    """The checks for one clip: {checks: [{id, label, verdict: ok|check, note}], measured: {...}}. `ordered_seconds` (0 = unknown) enables the length check; `prev_path` (the previous shot's
    chosen clip) enables the repeat check."""
    m = measure(exe, path)
    if m is None:
        return {"checks": [_check("readable", True, "The clip file could not be read, or it has no length.")], "measured": {}}
    adj, span = m["adjacent"], m["span"]
    checks = [_check("readable", False)]
    if max(adj) == 0 and span == 0:
        checks.append(_check("still", True, "The picture does not move at all: every frame looked at is identical."))
    else:
        checks.append(_check("still", max(adj) < STILL_STEP and span < STILL_SPAN, "The picture barely moves: the frames looked at are almost identical."))
    if m["mean_luma"] < BLACK_MEAN:
        checks.append(_check("black", True, f"The clip is almost black (average brightness {m['mean_luma']:.0f} of 255)."))
    else:
        checks.append(_check("black", m["min_luma"] < DARK_FRAME, f"A nearly black frame appears about {m['min_luma_at']:.1f} s in: check that it is meant."))
    if ordered_seconds and ordered_seconds > 0:
        checks.append(_check("short", m["duration"] < ordered_seconds - SHORT_BY, f"The clip is {m['duration']:.1f} s but {ordered_seconds:g} s were ordered."))
    if prev_path:
        pd = filmcut.probe_seconds(exe, prev_path)
        pf = filmcut._frame_signature(exe, prev_path, pd * 0.03) if pd > 0 else None
        if pf and m["first"]:
            diff = _mad(pf, m["first"])
            checks.append(_check("repeat", diff < REPEAT_BELOW, "It starts from almost the same picture as the previous shot's clip: check that this is not a repeat."))
    measured = {k: v for k, v in m.items() if k != "first"}
    return {"checks": checks, "measured": measured}


def middle_frame_jpeg(exe: str, path: str) -> bytes | None:
    """The middle frame of a clip as JPEG bytes (for the optional model look), or None. Nothing is written to disk."""
    d = filmcut.probe_seconds(exe, path)
    if d <= 0:
        return None
    r = subprocess.run([exe, "-y", "-ss", f"{d / 2:.3f}", "-i", path, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "3", "-"], capture_output=True)
    return r.stdout if (r.returncode == 0 and r.stdout[:2] == b"\xff\xd8") else None
