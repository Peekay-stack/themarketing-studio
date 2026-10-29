"""Free checks on a finished film (FILM_CONSOLIDATED_PLAN.md C2): no model, no cost, ffmpeg only.

The 28/29 Oct grandmother film rendered "successfully" (30.0 s, picture and sound) yet ended on 6 s of a pack that barely moved and about 1.7 s of near silence. Nothing in the render
result said so. This reads the finished mp4 and reports, per scene, how much the picture moves, and lists what a viewer would feel: a shot that barely moves, a frozen stretch (the
stitch bug the 28 Oct render once had), a silent tail. It is advice, never a block, and it does not read the language or the story. Scene windows come from the script's own timecodes
("0-4s"), so a film whose scenes were re-timed by the voice plan is measured against the re-timed windows (the script rows carry them since the voice plan copies them back).

Numbers (8 frames a second, 160x90 grey, mean absolute change between frames on a 0-255 scale), measured on the round 2 film: a held close-up opening 0.5-1.0, a moving scene 6-14, the
near-still pack scene 0.08. Pure functions where possible; `report` is the only one that runs ffmpeg.
"""
from __future__ import annotations

import os
import re
import subprocess

import filmcut

FPS = 8
STILL_BELOW = 0.25        # mean change per frame under this = the picture barely moves
STILL_MIN_SECS = 3.0      # a scene shorter than this is a beat, not a held shot
FREEZE_MIN_SECS = 1.5     # an exact freeze this long is a defect, not a held shot
SILENT_TAIL_SECS = 1.2

_TC = re.compile(r"(\d+(?:\.\d+)?)\s*[-–—]+\s*(\d+(?:\.\d+)?)")


def windows(scenes) -> list[dict]:
    """[{no, start, end}] from script rows that carry a timecode like '4-10s'; rows without one are skipped."""
    out = []
    for i, r in enumerate(scenes or []):
        if not isinstance(r, dict):
            continue
        m = _TC.search(str(r.get("tc") or ""))
        if not m:
            continue
        a, b = float(m.group(1)), float(m.group(2))
        if b > a:
            out.append({"no": r.get("no") if r.get("no") is not None else i + 1, "start": a, "end": b})
    return out


def parse_motion(text: str) -> list[float]:
    """The per-frame mean change from ffmpeg's `metadata=print` output. The first frame is compared with black, so it is dropped."""
    vals = [float(m.group(1)) for m in re.finditer(r"lavfi\.signalstats\.YAVG=([0-9.]+)", text or "")]
    return vals[1:]


def parse_ranges(text: str, start_key: str, end_key: str) -> list[tuple[float, float]]:
    """(start, end) pairs from ffmpeg's `freezedetect` / `silencedetect` log lines. A range still open at the end of the film has end None -> use the caller's duration."""
    starts = [float(x) for x in re.findall(start_key + r": *(-?[0-9.]+)", text or "")]
    ends = [float(x) for x in re.findall(end_key + r": *(-?[0-9.]+)", text or "")]
    out = []
    for i, s in enumerate(starts):
        out.append((s, ends[i] if i < len(ends) else None))
    return out


def scene_motion(steps: list[float], wins: list[dict], fps: int = FPS) -> list[dict]:
    """Mean change per scene window. `steps[i]` is the change between frame i and i+1, so it sits at i/fps. The last step of a window is the cut into the next scene, so it is left out."""
    out = []
    for w in wins:
        a, b = int(w["start"] * fps), int(w["end"] * fps)
        seg = steps[a:max(a + 1, b - 1)]
        out.append({**w, "motion": round(sum(seg) / len(seg), 3) if seg else None})
    return out


def findings(scenes_motion: list[dict], freezes: list[tuple[float, float]], silences: list[tuple[float, float | None]], duration: float, signoff=None) -> list[dict]:
    """Plain advice from the measurements. Kinds: barely-moves, frozen, silent-tail. `signoff` is the sign-off scene's number: the render holds that pack shot locked and still ON PURPOSE (so the pack never
    grows or drifts), so a still sign-off is reported in its own words, not as a fault."""
    out = []
    for s in scenes_motion:
        m, length = s.get("motion"), s["end"] - s["start"]
        if m is not None and m < STILL_BELOW and length >= STILL_MIN_SECS and signoff is not None and s["no"] == signoff:
            out.append({"kind": "barely-moves", "scene": s["no"], "signoff": True, "note": f"Scene {s['no']} (the sign-off) holds still for {length:g} s: the pack shot is locked on purpose so the pack never grows or drifts. "
                        "If the ending feels flat, put a person's action beside the pack, say the payoff line over it, or shorten the hold."})
        elif m is not None and m < STILL_BELOW and length >= STILL_MIN_SECS:
            out.append({"kind": "barely-moves", "scene": s["no"], "note": f"Scene {s['no']} barely moves for {length:g} s (picture change {m:.2f}; a held but alive shot is 0.5 or more). "
                        "A still shot reads as a pause: add a movement, a reveal or a cut, or shorten it."})
    for a, b in freezes:
        b = duration if b is None else b
        if b - a >= FREEZE_MIN_SECS:
            out.append({"kind": "frozen", "scene": None, "note": f"The picture is frozen from {a:.1f} s to {b:.1f} s ({b - a:.1f} s). That is a join or render fault, not a held shot."})
    for a, b in silences:
        b = duration if b is None else b
        if duration - b <= 0.3 and b - a >= SILENT_TAIL_SECS:
            out.append({"kind": "silent-tail", "scene": None, "note": f"The film ends on {b - a:.1f} s of near silence (from {a:.1f} s). Fine if it is a held breath; otherwise land the last line or the music there."})
            break
    return out


def _run(args: list[str], timeout: int = 180) -> str:
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (p.stdout or "") + "\n" + (p.stderr or "")


def duration_of(text: str) -> float:
    m = re.search(r"Duration: *(\d+):(\d+):(\d+(?:\.\d+)?)", text or "")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0


def report(path: str, scenes=None, signoff=None) -> dict:
    """Measure the film at `path`. {ok, duration, scenes:[{no,start,end,motion}], findings:[...]} or {ok: False, detail}."""
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return {"ok": False, "detail": "ffmpeg is not available on this server."}
    if not path or not os.path.exists(path):
        return {"ok": False, "detail": "That film is not on the server."}
    try:
        info = _run([exe, "-hide_banner", "-i", path])
        duration = duration_of(info)
        steps = parse_motion(_run([exe, "-v", "error", "-i", path, "-an", "-vf",
                                   f"fps={FPS},scale=160:90,format=gray,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"]))
        freeze_log = _run([exe, "-hide_banner", "-i", path, "-an", "-vf", "freezedetect=n=-60dB:d=1", "-f", "null", "-"])
        freezes = [(a, b) for a, b in parse_ranges(freeze_log, "freeze_start", "freeze_end")]
        silence_log = _run([exe, "-hide_banner", "-i", path, "-vn", "-af", "silencedetect=n=-38dB:d=0.4", "-f", "null", "-"]) if "Audio:" in info else ""
        silences = parse_ranges(silence_log, "silence_start", "silence_end")
    except Exception as exc:                                  # a probe that fails is "no report", never a broken render
        return {"ok": False, "detail": f"Could not read the film: {type(exc).__name__}."}
    sm = scene_motion(steps, windows(scenes))
    return {"ok": True, "duration": round(duration, 2), "scenes": sm, "findings": findings(sm, freezes, silences, duration, signoff), "has_audio": "Audio:" in info}
