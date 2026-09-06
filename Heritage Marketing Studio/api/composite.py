"""composite.py — real footage on a generated background, and cutdowns of an approved master.

Two jobs that sit outside the model entirely. Both are ffmpeg, which matters: they are exact,
they cost nothing per run, and they are repeatable — a cutdown of an approved film must be the
approved film, not a fresh generation that happens to look similar.

**Green screen.** A real actor shot against green, keyed and placed on a plate. This is the honest
route to a high-quality film with real people in it: no model has to invent a face, hold it across
shots, or be talked out of six fingers. The talent is the talent; only the location is generated.

**Edits.** Cutdowns and reframes are derived from the approved master by trimming and cropping. A
20s cut made from an approved 30s master is the same footage — so it inherits the approval, and the
compliance question "is this the film legal signed off?" has a defensible answer.

The chroma key defaults suit a decently lit green screen. `similarity` is how far from the key
colour still counts as green (too low leaves a green rim; too high eats the subject), and `blend`
softens the matte edge. Both are exposed because no single pair of numbers fits every shoot.
"""
from __future__ import annotations

import os
import re
import subprocess
import uuid

import filmcut
import tenancy

# Standard "chroma key green" — Rosco 4415 / digi-green sits around here. A shoot lit on blue
# should pass its own key colour instead.
GREEN = "0x00B140"
BLUE = "0x0047BB"

# Tenant-scoped since the shared-directory leak was found: new files land under
# `api/tenants/<tenant>/edits/`. Files written before that still live in the bare `api/edits/`
# and are still SERVED from there, because their URLs are recorded inside stored documents —
# see `tenancy.asset_path`, which reads tenant-first then legacy. Bound at import, so this is
# one tenant per process; serving several from one process needs this to become a call.
EDITS_DIR = tenancy.asset_dir("edits")

# Aspect presets for social cutdowns. Height is fixed at a sensible master size and the width
# follows, so every derived edit is the same vertical resolution.
ASPECTS = {
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "1:1":  (900, 900),
    "4:5":  (864, 1080),
}


def _run(cmd: list[str], timeout: int = 900) -> tuple[bool, str]:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "ffmpeg timed out"
    return res.returncode == 0, (res.stderr or "")[-600:]


def _is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def probe_video(path: str) -> dict:
    """Width, height, fps and duration — enough to judge whether a clip will cut against the rest.

    Cheap: ffmpeg reads the header and stops. No decode, no re-encode.
    """
    exe = filmcut.ffmpeg_exe()
    if not exe or not os.path.exists(path):
        return {}
    res = subprocess.run([exe, "-i", path], capture_output=True, text=True)
    err = res.stderr or ""
    out: dict = {"seconds": round(filmcut.probe_seconds(exe, path), 2)}
    dim = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", err)
    if dim:
        out["width"], out["height"] = int(dim.group(1)), int(dim.group(2))
    fps = re.search(r"(\d+(?:\.\d+)?)\s*fps", err)
    if fps:
        out["fps"] = round(float(fps.group(1)), 2)
    return out


def match_warnings(clip: dict, target_w: int = 1280, target_h: int = 720,
                   target_fps: float = 24.0) -> list[str]:
    """Say at ingest what would otherwise be discovered in the master.

    A phone-shot green screen cut against a Veo scene lands badly — wrong shape, wrong cadence. Both
    are fixable while someone is still holding the file, and awful to find in a delivered film.
    """
    notes = []
    w, h = clip.get("width"), clip.get("height")
    if w and h:
        if h < target_h:
            notes.append(f"{w}x{h} is smaller than the {target_w}x{target_h} the film renders at — "
                         f"it will be scaled up and look softer than the shots around it")
        ratio, want = round(w / h, 3), round(target_w / target_h, 3)
        if abs(ratio - want) > 0.02:
            notes.append(f"shot at {ratio:.2f}:1 against the film's {want:.2f}:1 — the sides or the "
                         f"top and bottom will be cropped away")
    fps = clip.get("fps")
    if fps and abs(fps - target_fps) > 0.5:
        notes.append(f"{fps:g} fps against the film's {target_fps:g} — motion will judder slightly "
                     f"unless it is conformed first")
    return notes


def _despill_type(key: str) -> str:
    """Despill the colour actually being keyed.

    This was hardcoded to green, which quietly stripped green from a subject shot on a BLUE screen —
    and, worse, made a wrongly-configured key look like it had worked, because the verification
    measures leftover green and the despill had already removed it.
    """
    try:
        v = int(str(key).lower().replace("0x", "").replace("#", "")[:6], 16)
    except ValueError:
        return "green"
    r, g, b = (v >> 16) & 255, (v >> 8) & 255, v & 255
    return "blue" if b > g and b > r else "green"


def key_over_plate(fg: str, bg: str, out_path: str, *, key: str = GREEN,
                   similarity: float = 0.18, blend: float = 0.08,
                   seconds: float = 0.0, spill: bool = True) -> tuple[bool, str]:
    """Key `fg` (green-screen footage) over `bg` (a still plate or a clip).

    The plate is scaled to *cover* the frame and centre-cropped rather than squashed — a location
    stretched to fit reads as a mistake immediately, where a crop reads as a choice.
    """
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return False, "ffmpeg unavailable"
    if not os.path.exists(fg):
        return False, "the green-screen clip is missing"
    if not os.path.exists(bg):
        return False, "the background plate is missing"

    dur = seconds or filmcut.probe_seconds(exe, fg) or 0.0
    w, h = 1280, 720
    inputs = []
    if _is_image(bg):
        # A still plate has to be looped, or it lasts one frame and the rest of the shot is black.
        inputs += ["-loop", "1", "-i", bg]
    else:
        inputs += ["-stream_loop", "-1", "-i", bg]     # a short plate repeats under a longer take
    inputs += ["-i", fg]

    chain = (
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},setsar=1[plate];"
        f"[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,"
        f"chromakey={key}:{similarity}:{blend}"
        # The screen bounces off skin and hair; without a despill the subject keeps a coloured
        # fringe that gives the composite away instantly. Despill the colour being keyed, not
        # always green — see _despill_type.
        + (f",despill=type={_despill_type(key)}:mix=0.5:expand=0" if spill else "")
        + "[talent];[plate][talent]overlay=shortest=1:format=auto[v]"
    )
    cmd = [exe, "-y", *inputs, "-filter_complex", chain, "-map", "[v]"]
    # Keep the performance's own audio — it is a real take, and re-recording it would be daft.
    cmd += ["-map", "1:a?", "-c:a", "aac", "-b:a", "192k", "-ac", "2"]
    cmd += ["-t", f"{max(0.1, dur):.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]
    ok, err = _run(cmd)
    if ok:
        return True, ""
    # despill is not in every ffmpeg build; the key itself still works without it.
    if spill and "despill" in err:
        return key_over_plate(fg, bg, out_path, key=key, similarity=similarity, blend=blend,
                              seconds=seconds, spill=False)
    return False, err


def green_ratio(path: str, at: float = 0.5) -> float:
    """Fraction of a frame that is still strongly green. The composite's own honesty check.

    A keyed shot should come out near zero. If it doesn't, the key colour or the tolerance is wrong
    and the operator should be told rather than left to notice on a big screen later.
    """
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return -1.0
    tmp = os.path.join(os.path.dirname(path), f"_probe-{uuid.uuid4().hex[:6]}.png")
    ok, _err = _run([exe, "-y", "-ss", f"{at:.2f}", "-i", path, "-frames:v", "1", tmp], timeout=120)
    if not ok or not os.path.exists(tmp):
        return -1.0
    try:
        from PIL import Image
        im = Image.open(tmp).convert("RGB")
        im.thumbnail((160, 160))
        px = list(im.getdata())
        green = sum(1 for r, g, b in px if g > 90 and g > r * 1.4 and g > b * 1.4)
        return round(green / max(1, len(px)), 4)
    except Exception:
        return -1.0
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def still_from(path: str, out_path: str, at: float = -1.0) -> tuple[bool, str]:
    """Pull one frame out of a take, as the still everything downstream keys against.

    `at` in seconds, or -1 to take the midpoint — the midpoint being the frame most likely to show the
    shot rather than someone walking into it. An image in gets copied rather than re-encoded, so this is
    safe to call on a still that is already a still.

    Why a real frame and not a generated one: the compositor keys against a frame, and a frame invented
    from a description is not the footage. A signed take whose still came from somewhere else is a shot
    that passed the gate on evidence it does not have.
    """
    if _is_image(path):
        try:
            import shutil as _sh
            _sh.copyfile(path, out_path)
            return True, ""
        except OSError as e:
            return False, str(e)
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return False, ("No ffmpeg available, so a frame cannot be pulled from footage. Install "
                       "imageio-ffmpeg, or attach a still image as the take.")
    if at < 0:
        dur = float((probe_video(path) or {}).get("duration") or 0)
        at = round(dur / 2.0, 2) if dur > 0.4 else 0.0
    ok, err = _run([exe, "-y", "-ss", f"{at:.2f}", "-i", path,
                    "-frames:v", "1", "-q:v", "2", out_path], timeout=180)
    if ok and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return True, ""
    # A seek past the end returns success with no file. Retry from the head before giving up, because
    # a duration probe on a variable-frame-rate phone clip is often slightly long.
    if at > 0:
        ok2, err2 = _run([exe, "-y", "-i", path, "-frames:v", "1", "-q:v", "2", out_path], timeout=180)
        if ok2 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return True, ""
        return False, err2 or err or "ffmpeg produced no frame"
    return False, err or "ffmpeg produced no frame"


# --- edits of an approved master ---------------------------------------------------------------

def edit(master: str, out_path: str, *, seconds: float = 0.0, aspect: str = "",
         start: float = 0.0, mute: bool = False) -> tuple[bool, str]:
    """Derive a cutdown / reframe from an approved master.

    Trimming and cropping only — nothing is re-generated, so the result is the approved film with
    less of it. That is the whole point: a 9:16 cutdown of a signed-off master carries the sign-off.
    """
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return False, "ffmpeg unavailable"
    if not os.path.exists(master):
        return False, "the master is missing"
    full = filmcut.probe_seconds(exe, master) or 0.0
    if seconds and start + seconds > full + 0.05:
        return False, (f"a {seconds:.0f}s cut starting at {start:.0f}s does not fit a "
                       f"{full:.0f}s master")
    cmd = [exe, "-y"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", master]
    vf = []
    if aspect in ASPECTS:
        w, h = ASPECTS[aspect]
        # Cover and centre-crop. Padding would letterbox a film that was shot to fill the frame.
        vf.append(f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1")
    if vf:
        cmd += ["-vf", ",".join(vf), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
    if mute:
        cmd += ["-an"]
    else:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ac", "2"]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    cmd += ["-movflags", "+faststart", out_path]
    ok, err = _run(cmd)
    return (True, "") if ok else (False, err)


def fit_to_beat(src: str, out_path: str, seconds: float) -> tuple[bool, str]:
    """Make a live-action take exactly `seconds` long so it can stand in for a generated scene.

    Longer than the beat: trimmed. Shorter: the last frame is held.

    Holding a frame is an editorial decision, not a neutral one, so it is reported rather than done
    quietly. The alternative was worse in every direction — dropping back to generation throws away
    the footage someone deliberately attached, and letting the scene run short breaks the guarantee
    that the beats sum to the slot the film was sold into.
    """
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return False, "ffmpeg unavailable"
    have = filmcut.probe_seconds(exe, src) or 0.0
    if have <= 0:
        return False, "could not read that shot"
    if have >= seconds - 0.05:
        return edit(src, out_path, seconds=seconds)
    hold = seconds - have
    cmd = [exe, "-y", "-i", src,
           "-vf", f"tpad=stop_mode=clone:stop_duration={hold:.3f}",
           "-af", "apad", "-t", f"{seconds:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-movflags", "+faststart", out_path]
    ok, err = _run(cmd)
    if not ok:
        return False, err
    return True, (f"the take is {have:.1f}s against a {seconds:.0f}s beat, so its last frame is held "
                  f"for {hold:.1f}s — shorten the scene or use a longer take if that reads as a freeze")


# Named looks, not a slider. A person picking "cool-clean" is making the same kind of decision as
# picking a POSM style or a hero type elsewhere in this app — a declared choice from a small, described
# set, not a set of raw numbers nobody can hold an opinion about. Each is one ffmpeg filter chain:
# `eq` for brightness/contrast/saturation, `colorbalance` for a shadow/midtone/highlight tint. Kept
# short on purpose — a long menu of grades is a menu nobody reads before picking the top one.
#
# This is the fix for the actual gap: nothing in the pipeline today unifies the look across clips that
# were each generated separately and drift in colour and contrast against each other. A grade is not
# artistic polish here, it is the thing that makes several separate renders read as one film.
GRADES: dict[str, dict] = {
    "neutral": {
        "label": "Neutral",
        "what": "No correction. The pass-through option, so “no grade” is a real choice and "
                "not just an absent field.",
        "eq": "", "balance": "",
    },
    "warm-dawn": {
        "label": "Warm dawn",
        "what": "Lifted shadows, a warm cast toward amber. For the 6am, first-light material this "
                "brand's own films actually use.",
        "eq": "eq=contrast=1.03:brightness=0.02:saturation=1.08",
        "balance": "colorbalance=rs=0.05:gs=0.02:bs=-0.06:rm=0.03:gm=0.01:bm=-0.03",
    },
    "cool-clean": {
        "label": "Cool clean",
        "what": "Slightly cooler, higher contrast, a touch less saturated. The ‘hygienic, "
                "checked, controlled’ register rather than the warm one.",
        "eq": "eq=contrast=1.08:brightness=-0.01:saturation=0.95",
        "balance": "colorbalance=rs=-0.04:bs=0.06:rh=-0.03:bh=0.05",
    },
    "rich-contrast": {
        "label": "Rich contrast",
        "what": "Deeper blacks, punchier saturation. The general premium-FMCG look, for a piece "
                "that has to hold up next to a shelf full of competitors rather than sit alone.",
        "eq": "eq=contrast=1.14:saturation=1.12:gamma=0.96",
        "balance": "",
    },
}


def grade_filter(name: str) -> str:
    """The ffmpeg `-vf` fragment for a named grade, or '' for `neutral` / unknown.

    Unknown names fall through to the empty string rather than raising, because this is called from
    inside a larger filter chain (`edit()`'s own `-vf`) where the caller has already validated the name
    against `GRADES` and reported a refusal if it did not match — see `grade()` below for that refusal.
    """
    g = GRADES.get(name) or {}
    return ",".join(p for p in (g.get("eq", ""), g.get("balance", "")) if p)


def grade(src: str, out_path: str, name: str) -> tuple[bool, str]:
    """Apply one named grade to a whole file — the finished master, not each clip before it is
    stitched. "One look applied across every clip" means exactly one correction over the assembled
    film; grading clips individually first would let them drift again the moment two different takes
    are colour-matched slightly differently by whichever model rendered them.

    Refuses on an unknown name rather than silently applying nothing, and picture-only: the grade never
    touches audio, so this can run whether or not the master has a score on it yet.
    """
    if name not in GRADES:
        return False, f"'{name}' is not a grade this module knows. Choices: {', '.join(GRADES)}."
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return False, "ffmpeg unavailable"
    if not os.path.exists(src):
        return False, "the master is missing"
    vf = grade_filter(name)
    cmd = [exe, "-y", "-i", src]
    if vf:
        cmd += ["-vf", vf]
    if _is_image(src):
        # A still gets encoded as a still. Without this branch the h264 settings below were applied to
        # a single-frame input and ffmpeg wrote a VIDEO stream into whatever extension was asked for —
        # `grade("x.png", "y.png", "cool-clean")` returned `(True, "")` and produced a 21KB file that
        # PIL could not open at all. Reporting success while writing something unreadable is worse
        # than refusing, and this is a real thing to want: grading a plate to match a film's look.
        cmd += ["-frames:v", "1", out_path]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-movflags", "+faststart", out_path]
    ok, err = _run(cmd)
    return (True, "") if ok else (False, err)


def new_grade_name(name: str = "grade") -> str:
    safe = "".join(c if c.isalnum() else "-" for c in (name or "grade").lower()).strip("-")[:20]
    return f"{safe or 'grade'}-{uuid.uuid4().hex[:8]}.mp4"


def new_edit_name(label: str = "edit") -> str:
    safe = "".join(c if c.isalnum() else "-" for c in (label or "edit").lower()).strip("-")[:28]
    return f"{safe or 'edit'}-{uuid.uuid4().hex[:8]}.mp4"
