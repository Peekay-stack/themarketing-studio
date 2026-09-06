"""filmcut.py — turn a script into a full-length film.

Video models render short beats only (Veo caps at 8s per call), so a 20s or 30s film has to be
rendered as several clips and joined. This module owns that: splitting the approved script into
renderable segments, then concatenating the returned clips into one MP4 the UI can play and
download as a single `video_url`.

ffmpeg comes from the `imageio-ffmpeg` wheel (it bundles its own binary), so there is nothing to
install system-wide. If it is missing we degrade to "return the first clip" rather than failing.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

import httpx

import tenancy

MAX_CLIP_SECONDS = 8          # Veo's hard per-call ceiling
_ALLOWED_CLIP = (4, 6, 8)     # Veo only accepts these beat lengths

# Tenant-scoped since the shared-directory leak was found: new files land under
# `api/tenants/<tenant>/renders/`. Files written before that still live in the bare `api/renders/`
# and are still SERVED from there, because their URLs are recorded inside stored documents —
# see `tenancy.asset_path`, which reads tenant-first then legacy. Bound at import, so this is
# one tenant per process; serving several from one process needs this to become a call.
RENDERS_DIR = tenancy.asset_dir("renders")


def ffmpeg_exe() -> str | None:
    """The bundled ffmpeg, or any ffmpeg on PATH. None if neither is available."""
    try:
        import imageio_ffmpeg  # type: ignore
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return shutil.which("ffmpeg")


def parse_seconds(duration, default: int = 20) -> int:
    """'20s' / '20' / 20 -> 20. Clamped to a sane film length."""
    try:
        secs = int(float(str(duration).strip().lower().rstrip("s")))
    except (TypeError, ValueError):
        return default
    return max(4, min(120, secs))


def _beat_lengths(total: int) -> list[int]:
    """Beat lengths from _ALLOWED_CLIP that add up to `total` exactly where possible.

    Greedily taking 8s would bill a 10s film as 8+4=12s, so instead use the fewest clips that
    sum exactly (10 -> 6+4). Falls back to a greedy split for lengths that can't be hit exactly.
    """
    lo, hi = min(_ALLOWED_CLIP), max(_ALLOWED_CLIP)
    for k in range((total + hi - 1) // hi, total // lo + 1):
        surplus = total - lo * k                     # spread as +2 steps over the base clips
        if surplus < 0 or surplus % 2 or surplus > (hi - lo) * k:
            continue
        lengths = [lo] * k
        i = 0
        while surplus > 0:
            room = min(hi - lengths[i], surplus)
            lengths[i] += room
            surplus -= room
            i += 1
        return sorted(lengths, reverse=True)         # longest beats first
    lengths, remaining = [], total                   # can't be exact (odd length) — greedy
    while remaining > 0:
        n = next((x for x in sorted(_ALLOWED_CLIP, reverse=True) if x <= remaining), lo)
        lengths.append(n)
        remaining -= n
    return lengths or [lo]


# --- what each beat is FOR, and what survives a cutdown ----------------------------------------
#
# `_beat_lengths` above answers how long each beat may be. It does not answer what any of them is for,
# and that is the difference between eight clips and a film. These are the five jobs a 30-second brand
# film actually does, in narrative order.
#
# Not a style opinion: each role is the thing that fails if the beat is missing. A film with no hook
# loses the viewer before the argument starts; one with no turn has nothing for the rest of the campaign
# to remind anybody of (which is exactly why `campaign.ROLE_BY_RUNG` gives TV "the turn" and says no
# other medium can carry it); one with no brand block was watched by somebody who cannot name whose it
# was.
BEAT_ROLES: dict[str, dict] = {
    "hook":      {"what": "The first two or three seconds. One image that earns the next five.",
                  "fails": "Nobody is still watching when the argument starts."},
    "world":     {"what": "Where and who. Establishes the place and the person the film is about.",
                  "fails": "The argument lands on somebody the viewer has not met."},
    "mechanism": {"what": "The thing being shown — the proof, the demonstration, the routine. The "
                          "middle, and where extra length goes.",
                  "fails": "The claim is asserted rather than shown."},
    "turn":      {"what": "What changes. The reason the film is a film and not a montage.",
                  "fails": "Nothing downstream has a feeling to remind anyone of."},
    "brand":     {"what": "The endframe: pack, logo, mnemonic, the line as real type.",
                  "fails": "Somebody watched it and cannot say whose it was."},
}

NARRATIVE_ORDER = ("hook", "world", "mechanism", "turn", "brand")

# The drop-out ladder, applied to TIME rather than to a POSM kit — the same reasoning as
# `posm.DROP_ORDER`: deciding what leaves per cutdown by feel is how a 15-second edit stops being the
# same film as the 30. `world` goes first because context is the most compressible thing in a film;
# `mechanism` second because a shortened film can assert what a long one demonstrates. Nothing else may
# go: a cutdown without the turn is not a shorter version of the film, it is a different one.
DROP_ORDER = ("world", "mechanism")
NEVER_DROPPED = ("hook", "turn", "brand")

# Under three beats there is not room for hook + turn + brand, so there is no three-act film to plan.
# Said out loud rather than faked: a 6-second single-clip piece is a bumper, and pretending it has a
# turn produces a plan nobody can shoot.
MIN_FILM_BEATS = 3


def roles_for(n_beats: int) -> list[str]:
    """Which roles an `n_beats` film has, in narrative order.

    Extra beats beyond five extend `mechanism` — the middle is where a longer film puts more, because
    a 60-second film is not a 30 with a longer endframe.
    """
    if n_beats <= 0:
        return []
    if n_beats < MIN_FILM_BEATS:
        # A bumper. Give it the endframe first, then a hook if there is a second beat — the two things
        # a very short piece can actually do.
        return ["brand"] if n_beats == 1 else ["hook", "brand"]
    keep = list(NARRATIVE_ORDER)
    for role in DROP_ORDER:                      # shed the compressible middle until it fits
        if len(keep) <= n_beats:
            break
        keep.remove(role)
    out = keep[:]
    if n_beats > len(out):                       # longer film: extend the middle
        anchor = "mechanism" if "mechanism" in out else out[len(out) // 2]
        at = out.index(anchor)
        out[at:at + 1] = [anchor] * (1 + n_beats - len(out))
    return out[:n_beats]


def plan_beats(total_seconds: int) -> dict:
    """A shot plan for a film of `total_seconds`: how long each beat runs and what it is for.

    Pure arithmetic over `_beat_lengths` plus `roles_for` — no model, no judgement. The point is that
    the shape of the film is decided before anything is generated, and every beat can be briefed
    against a job rather than "shot 3 of 4".
    """
    total = parse_seconds(total_seconds)
    lengths = _beat_lengths(total)
    roles = roles_for(len(lengths))
    beats, seen = [], {}
    for i, (secs, role) in enumerate(zip(lengths, roles)):
        seen[role] = seen.get(role, 0) + 1
        spec = BEAT_ROLES.get(role, {})
        beats.append({"n": i + 1, "seconds": secs, "role": role,
                      # A film with three `mechanism` beats needs them told apart when briefing.
                      "role_label": (f"{role} {seen[role]}" if roles.count(role) > 1 else role),
                      "what": spec.get("what", ""), "fails": spec.get("fails", "")})
    planned = sum(lengths)
    notes = []
    if planned != total:
        notes.append(f"{total}s cannot be built exactly from {'/'.join(str(c) for c in _ALLOWED_CLIP)}"
                     f"-second clips, so this plan runs {planned}s. Ask for {planned}s, or accept the "
                     f"difference and trim in the edit.")
    if len(lengths) < MIN_FILM_BEATS:
        notes.append(f"{len(lengths)} beat(s) is a bumper, not a film — there is no room for a hook, a "
                     f"turn and a brand block, so this plan has no turn. That is a real limit of the "
                     f"length, not something a better plan would fix.")
    missing = [r for r in NEVER_DROPPED if r not in roles]
    return {"seconds": planned, "asked": total, "beats": beats, "count": len(beats),
            "roles": roles, "missing_roles": missing, "notes": notes,
            "role_spec": BEAT_ROLES}


def cutdown_plan(beats: list[dict], target_seconds: int) -> dict:
    """Which beats survive a cutdown to `target_seconds`, and how long each one gets.

    Beats are dropped in the ladder's fixed order, never by feel; whatever survives is then trimmed
    proportionally to hit the target, with `_ALLOWED_CLIP`'s floor respected only where the source beat
    is being re-generated — a cutdown TRIMS existing clips, so a 2-second slice of an approved 8-second
    beat is legitimate here in a way it never is when ordering a new one.

    Returns a plan, not a file. Executing it is `filmcut.stitch()` over the surviving clips, or
    `composite.edit()` per beat — which is why a cutdown classifies as `free` in `cut.classify()`:
    every frame it uses is already on disk.
    """
    target = parse_seconds(target_seconds)
    # `parse_seconds` clamps to 4..120, and a clamp that happens silently is a lie the caller repeats.
    # Asking for a 2-second cutdown returned a 4-second plan with an empty `notes`, so the screen said
    # "already at or under target" about a film that was neither — it had been quietly rounded up.
    # Say it here, once, where the clamp actually happens.
    asked = None
    try:
        asked = int(float(str(target_seconds).strip().lower().rstrip("s")))
    except (TypeError, ValueError):
        asked = None
    clamp_note = []
    if asked is not None and asked != target:
        clamp_note = [f"Asked for {asked}s; the shortest a cutdown can be is {target}s — a clip below "
                      f"that is a flash, not a shot." if asked < target else
                      f"Asked for {asked}s; capped at {target}s."]

    rows = [b for b in (beats or []) if isinstance(b, dict)]
    if not rows:
        return {"target": target, "asked": asked, "beats": [], "dropped": [], "seconds": 0,
                "notes": clamp_note + ["no beats to cut down"]}

    def secs_of(bs) -> float:
        return sum(float(b.get("seconds") or 0) for b in bs)

    keep = rows[:]
    dropped: list[dict] = []
    # Drop ONE beat at a time, cheapest-to-lose first, and stop the moment what is left fits. Dropping
    # every beat of a role before re-checking is the bug the first version of this had: a 30s cutdown
    # of a 60s master threw away all four `mechanism` beats and came back 20s long, because "drop the
    # droppable roles" is not the same instruction as "drop until it fits".
    #
    # Within a role, the LAST occurrence goes first. A film with four demonstration beats loses the
    # fourth before the first: the first is where the demonstration starts, and the later ones are
    # elaboration.
    for role in DROP_ORDER:
        if secs_of(keep) <= target:
            break
        for b in reversed([x for x in keep if str(x.get("role")) == role]):
            if secs_of(keep) <= target:
                break
            keep.remove(b)
            dropped.append(b)

    have = secs_of(keep)
    out, notes = [], list(clamp_note)
    if have <= 0:
        return {"target": target, "asked": asked, "beats": [], "dropped": dropped, "seconds": 0,
                "notes": notes + ["nothing survived the cutdown"]}
    # Trim the survivors only if they still overrun. Never stretch to fill: a cutdown that padded beats
    # to hit a round number would be holding frames nobody asked to hold.
    scale = min(1.0, target / have)
    for b in keep:
        secs = round(max(1.0, float(b.get("seconds") or 0) * scale), 2)
        out.append({**b, "seconds": secs, "from_seconds": b.get("seconds")})
    got = round(sum(b["seconds"] for b in out), 2)
    if got > target + 0.05:
        notes.append(f"The beats that may not be dropped ({', '.join(NEVER_DROPPED)}) already run "
                     f"{got}s against a {target}s target, so this cutdown is {got}s. A shorter one "
                     f"would have to lose the turn, which makes it a different film rather than a "
                     f"shorter one.")
    elif got < target - 2.0:
        notes.append(f"This cutdown runs {got}s against a {target}s target. The next beat that could "
                     f"fill it is one the ladder already dropped — put it back deliberately if the slot "
                     f"has to be filled exactly, rather than stretching what is here.")
    if dropped:
        notes.append(f"Dropped {len(dropped)} beat(s): "
                     f"{', '.join(str(b.get('role') or b.get('n')) for b in dropped)}.")
    return {"target": target, "asked": asked, "seconds": got, "beats": out, "dropped": dropped,
            "kept_roles": [b.get("role") for b in out], "notes": notes}


def assign_roles(segments: list[dict]) -> list[dict]:
    """Give every segment the narrative job of the MOMENT it belongs to. Mutates and returns.

    Roles attach to moments, not to raw beats, and that distinction is the whole correctness of this
    function. `plan_by_scene` splits one action across several beats when it runs past Veo's 8-second
    ceiling and marks the extras `continues` — those are the same story moment at a different camera
    angle. Assigning roles beat-by-beat would make the first half of one action the `mechanism` and the
    second half the `turn`, which is not a film, it is a mis-labelled shot list.

    So: a new moment begins wherever `continues` is False, roles are assigned across the moments, and
    every beat inherits its moment's role.
    """
    segs = [s for s in (segments or []) if isinstance(s, dict)]
    if not segs:
        return segs
    starts = [i for i, s in enumerate(segs) if not s.get("continues")] or [0]
    roles = roles_for(len(starts))
    for m, start in enumerate(starts):
        end = starts[m + 1] if m + 1 < len(starts) else len(segs)
        role = roles[m] if m < len(roles) else (roles[-1] if roles else "")
        spec = BEAT_ROLES.get(role, {})
        for i in range(start, end):
            segs[i]["role"] = role
            segs[i]["role_what"] = spec.get("what", "")
    return segs


def plan_by_scene(scenes: list, per_scene: list) -> list[dict]:
    """One shot per scene, each as long as that scene's dialogue needs.

    A scene needing more than Veo's 8s ceiling becomes several beats continuing the same action, so
    the writing sets the pace rather than being cut to fit a fixed grid.
    """
    import filmvoice
    out: list[dict] = []
    for row, secs in zip(scenes, per_scene):
        for n, b in enumerate(filmvoice.beats_for(secs)):
            out.append({"index": len(out), "seconds": b, "scenes": [row], "continues": n > 0})
    return assign_roles(out or [{"index": 0, "seconds": 4, "scenes": [], "continues": False}])


def plan_segments(scenes: list, total_seconds: int) -> list[dict]:
    """Split a FIXED total into <=8s segments — the legacy path, kept for callers that pin length.

    The main render now uses plan_by_scene(), so scene length follows the dialogue instead of the
    dialogue being trimmed to fit the clock.
    """
    scenes = [s for s in (scenes or []) if isinstance(s, dict)]
    segments = [{"index": i, "seconds": secs, "scenes": [], "continues": False}
                for i, secs in enumerate(_beat_lengths(total_seconds))]
    if scenes:
        # Spread scenes over segments, keeping order and never dropping one.
        n_seg = len(segments)
        for i, scene in enumerate(scenes):
            segments[min(i * n_seg // len(scenes), n_seg - 1)]["scenes"].append(scene)
        for seg in segments:            # a segment that got nothing continues the previous beat
            if not seg["scenes"]:
                prev = segments[max(0, seg["index"] - 1)]["scenes"]
                seg["scenes"] = prev[-1:] if prev else []
                seg["continues"] = bool(prev)
    return assign_roles(segments)


def _copy_local(url: str, dest: str) -> bool:
    """A locally-stored asset (Google returns bytes, so they live on disk) needs no HTTP."""
    import gemini
    src = gemini.local_path(url)
    if not src:
        return False
    import shutil
    shutil.copyfile(src, dest)
    return True


def _download(url: str, dest: str) -> None:
    if _copy_local(url, dest):
        return
    with httpx.stream("GET", url, timeout=180.0, follow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as fh:
            fh.writelines(r.iter_bytes(1 << 16))


def probe_seconds(exe: str, path: str) -> float:
    """Length of a media file in seconds, or 0.0 if ffmpeg can't tell us."""
    res = subprocess.run([exe, "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", res.stderr or "")
    if not m:
        return 0.0
    h, mm, ss = m.groups()
    return int(h) * 3600 + int(mm) * 60 + float(ss)


def _trim(exe: str, path: str, seconds: float) -> str:
    """Cut a clip back to the beat length it was ordered at. Returns the path to use.

    Veo hands back a little more than asked for — a few frames of tail on each clip — so six shots
    that should total 30s arrive as 32s. Left alone that is not merely a long film: the soundtrack is
    placed at absolute timecodes, so every scene after the first sits further behind its own picture
    and the closing line lands seconds late. Trimming each clip to its planned length keeps sound and
    picture locked, and costs only the frames the model added past the beat.
    """
    if seconds <= 0 or probe_seconds(exe, path) <= seconds + 0.02:
        return path
    out = f"{os.path.splitext(path)[0]}-cut.mp4"
    # Re-encoded rather than stream-copied: a copy can only cut on a frame boundary and lands a
    # frame or two long, which compounds across shots until the last cut is half a second adrift
    # from the timecode its dialogue was placed at. `-t` is exact when the frames are re-written.
    attempts = [[exe, "-y", "-i", path, "-t", f"{seconds:.3f}",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "copy", out],
                [exe, "-y", "-i", path, "-t", f"{seconds:.3f}", "-c", "copy",
                 "-avoid_negative_ts", "make_zero", out]]
    for cmd in attempts:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
            return out
        print(f"[filmcut] could not trim clip to {seconds}s: {res.stderr[-200:]}",
              file=sys.stderr, flush=True)
    return path


def _make_exact(exe: str, path: str, seconds: float) -> None:
    """Force the joined film to be exactly `seconds` long, in place.

    Per-clip trimming gets the sync right but leaves the total a few frames long, because a stream
    copy can only cut on frame boundaries. A 30s slot means 30.000s, so re-encode once at the end —
    `-t` is frame-accurate when the frames are being written rather than copied. Cheap: one pass over
    a half-minute of 720p, and only when the join actually came out long.
    """
    if seconds <= 0 or probe_seconds(exe, path) <= seconds + 0.02:
        return
    tmp_out = f"{os.path.splitext(path)[0]}-exact.mp4"
    res = subprocess.run([exe, "-y", "-i", path, "-t", f"{seconds:.3f}",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-c:a", "copy", "-movflags", "+faststart", tmp_out],
                         capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
        os.replace(tmp_out, path)
        print(f"[filmcut] trimmed the join to exactly {seconds:.0f}s", file=sys.stderr, flush=True)
    else:
        print(f"[filmcut] could not make the join exact: {res.stderr[-200:]}",
              file=sys.stderr, flush=True)


def stitch(urls: list[str], lengths: list[int] | None = None) -> str | None:
    """Download the clips and concatenate them into one MP4 under renders/.

    `lengths` is the beat each clip was ordered at. Given those, every clip is cut back to its beat
    so the finished film is exactly as long as it was planned, timed and priced — see _trim for why
    that matters to sync and not just to the running time.

    Returns the output filename (not a full path), or None if it couldn't be produced.
    """
    urls = [u for u in urls if u]
    if not urls:
        return None
    exe = ffmpeg_exe()
    if not exe:
        print("[filmcut] no ffmpeg available; cannot join clips", file=sys.stderr, flush=True)
        return None
    os.makedirs(RENDERS_DIR, exist_ok=True)
    name = f"film-{uuid.uuid4().hex[:10]}.mp4"
    out_path = os.path.join(RENDERS_DIR, name)
    tmp = tempfile.mkdtemp(prefix="film-")
    try:
        parts = []
        for i, url in enumerate(urls):
            p = os.path.join(tmp, f"part{i:02d}.mp4")
            try:
                _download(url, p)
            except Exception as e:
                print(f"[filmcut] clip {i} download failed: {e}", file=sys.stderr, flush=True)
                continue
            want = (lengths or [])[i] if i < len(lengths or []) else 0
            parts.append(_trim(exe, p, float(want)))
        if not parts:
            return None
        listing = os.path.join(tmp, "parts.txt")
        with open(listing, "w", encoding="utf-8") as fh:
            for p in parts:
                fh.write(f"file '{p.replace(chr(92), '/')}'\n")
        planned = float(sum(lengths)) if lengths else 0.0
        base = [exe, "-y", "-f", "concat", "-safe", "0", "-i", listing]
        if planned > 0:
            base += ["-t", f"{planned:.3f}"]   # backstop, in case a clip refused to trim
        # Same model and settings for every clip, so a stream copy normally works; re-encode
        # only if it doesn't (mismatched timebases etc.).
        attempts = [base + ["-c", "copy", out_path],
                    base + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                            "-c:a", "aac", "-movflags", "+faststart", out_path]]
        for cmd in attempts:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                print(f"[filmcut] joined {len(parts)} clip(s) -> {name}", file=sys.stderr, flush=True)
                _make_exact(exe, out_path, planned)
                return name
            print(f"[filmcut] ffmpeg failed ({res.returncode}): {res.stderr[-400:]}",
                  file=sys.stderr, flush=True)
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
