"""cut.py — the approved film as a stack of addressable layers, not a rendered file.

`/rescore` already proves the shape this module generalises. It keeps a **silent master** and re-mixes
audio over it, writing a new file per take rather than overwriting the last one, because its own
docstring states the rule outright: *picture and soundtrack are separate layers, so swapping the bed
only costs the audio.* That is the whole design. What it does not have is a place to write down that a
version exists at all — today the "master" is a filename in a payload, `/rescore` fails outright with
"render the film again" the moment that file leaves disk, and there is no way to say a cut was ever
approved, let alone what changed between two versions of it.

**A cut is a manifest, not a video file.** `{execution, version, beats, tracks, grade, master_url,
scored_url, approved}`. The video files it points at — clips, masters, scored mixes — stay exactly
where they already live, in `filmcut.RENDERS_DIR`; this module never moves or deletes one. They are the
asset pool a manifest points into, not intermediate files a manifest replaces.

**Editing creates a new version; it never mutates an approved one.** Version *n+1* carries a
`parent_version` pointer and its own diff against the parent — which beats changed, which stayed
byte-for-byte the same, whether the audio or the grade moved. That diff is what lets a change be signed
off without re-approving the whole film, the same discipline this project already learned the hard way
on the frontend ("always diff for what was removed").

**The cost of an edit is computed before anything is re-rendered.** `classify()` answers one question —
retime, reorder, a new super, a re-grade or a cutdown cost nothing to re-render; swapping audio costs an
audio pass; replacing one shot costs one clip; changing the cast or the location costs the whole film —
and the two full-remake cases are named honestly rather than quietly attempted, because a client asking
to "try a different mother" is asking for a new film, and knowing that before the work starts is worth
more than any amount of pipeline speed.

This module owns the bookkeeping only. It does not call ffmpeg, does not talk to a video model, and does
not decide HOW a picture change gets re-rendered — that stays `filmcut.py`'s and `filmaudio.py`'s job,
exactly as it is today. A route reads `classify()`'s answer, does whatever rendering that answer calls
for using the modules that already do it, and hands the resulting URLs to `commit()`.
"""
from __future__ import annotations

import json
import os
import time
import uuid

import tenancy

CUT_DIR = tenancy.dir("cuts")
MANIFEST = os.path.join(CUT_DIR, "manifest.json")

# What a beat is made of. `shot_id` is optional and points at `shots.py`'s sign-off chain for a
# live-action beat; a generated beat has none and stands on `clip_url` alone. Both are legitimate —
# this manifest does not care how a clip was made, only which one is currently in this beat.
BEAT_FIELDS = ("n", "role", "shot_id", "clip_url", "seconds", "super")

# The beat roles this module expects `filmcut`'s cutdown ladder to eventually assign — named here so
# the drop-out rule below has real words to refer to rather than a bare "n". Not enforced: an older
# cut with no roles at all still classifies and diffs correctly, it just cannot be asked to cut down
# by role until they exist.
BEAT_ROLES = ("hook", "world", "mechanism", "turn", "brand")

# The two edits nothing here can do cheaply, named so a screen can say so rather than attempting them.
FULL_REMAKE_TRIGGERS = ("cast", "location", "plate")


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _load() -> list[dict]:
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            rows = json.load(fh)
        return rows if isinstance(rows, list) else []
    except (OSError, ValueError):
        return []


def _save(rows: list[dict]) -> None:
    os.makedirs(CUT_DIR, exist_ok=True)
    tmp = MANIFEST + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, MANIFEST)          # never leave a half-written manifest behind


def _clean_beat(b: dict, i: int) -> dict:
    b = b or {}
    return {
        "n": int(b.get("n") or i + 1),
        "role": str(b.get("role") or "").strip(),
        "shot_id": str(b.get("shot_id") or "").strip(),
        "clip_url": str(b.get("clip_url") or "").strip(),
        "seconds": float(b.get("seconds") or 0),
        "super": str(b.get("super") or "").strip(),
    }


def _clean_tracks(t: dict | None) -> dict:
    t = t or {}
    # `spots` (foley) belongs in the manifest, not just in the render call that placed them. The
    # manifest has to describe the film completely enough to re-render it — a version whose clank at
    # 4.2s existed only as an argument somebody passed once is a version nobody can reproduce.
    # Normalised and SORTED so two orderings of the same three spots compare equal, and a re-send in a
    # different order is not mistaken for an audio change by `classify()`.
    spots = []
    for s in (t.get("spots") or []):
        if not isinstance(s, dict) or not str(s.get("url") or "").strip():
            continue
        try:
            at = round(max(0.0, float(s.get("at") or 0)), 3)
        except (TypeError, ValueError):
            at = 0.0
        row = {"url": str(s["url"]).strip(), "at": at}
        if s.get("gain") not in (None, ""):
            try:
                row["gain"] = round(float(s["gain"]), 3)
            except (TypeError, ValueError):
                pass
        spots.append(row)
    spots.sort(key=lambda r: (r["at"], r["url"]))
    return {"voice_url": str(t.get("voice_url") or "").strip(),
            "music_url": str(t.get("music_url") or "").strip(),
            "ambience_url": str(t.get("ambience_url") or "").strip(),
            "spots": spots}


def for_execution(execution: str) -> dict | None:
    """The cut for one execution — its whole version history. None if it has never been started."""
    execution = str(execution or "").strip()
    return next((r for r in _load() if r.get("execution") == execution), None) if execution else None


def latest(cut: dict | None) -> dict | None:
    """The most recent version. This is the ONLY version an edit may be proposed against — proposing
    against an older one would silently discard whatever the most recent version already changed."""
    vs = (cut or {}).get("versions") or []
    return vs[-1] if vs else None


def get_version(cut: dict | None, version: int) -> dict | None:
    return next((v for v in (cut or {}).get("versions") or [] if v.get("version") == version), None)


def last_approved(cut: dict | None) -> dict | None:
    """The most recent APPROVED version, or None. This is what a codes extractor or a downstream write-
    back should read — never the latest render, which may be an unapproved experiment. An experimental
    grade read as though it were approved is how it quietly becomes the brand's palette."""
    vs = [v for v in (cut or {}).get("versions") or [] if v.get("approved")]
    return vs[-1] if vs else None


def start(execution: str, beats: list[dict], *, tracks: dict | None = None, grade: str = "",
         master_url: str = "") -> tuple[dict | None, str]:
    """Create a cut's first version. Refuses if this execution already has one — editing an existing
    cut is `propose_edit` + `commit`, not a second `start` quietly replacing the version history."""
    execution = str(execution or "").strip()
    if not execution:
        return None, "A cut belongs to an execution — say which one."
    if for_execution(execution):
        return None, ("This execution already has a cut. Propose an edit against its latest version "
                      "instead of starting a new one — starting again would abandon its history.")
    if not beats:
        return None, "A cut needs at least one beat — an empty manifest has nothing to version."

    rows = _load()
    row = {
        "id": uuid.uuid4().hex[:10], "execution": execution, "created": _now(),
        "versions": [{
            "version": 1, "parent_version": None,
            "beats": [_clean_beat(b, i) for i, b in enumerate(beats)],
            "tracks": _clean_tracks(tracks), "grade": str(grade or "").strip(),
            "master_url": str(master_url or "").strip(), "scored_url": "",
            "approved": None, "created": _now(), "edited": _now(),
            "diff": None, "class": "new",
        }],
    }
    rows.append(row)
    _save(rows)
    return row, ""


def diff_beats(old_beats: list[dict], new_beats: list[dict]) -> dict:
    """Which beat NUMBERS carry different content, which carry the same, by position.

    Compared by beat number and content, not by clip identity — a reorder changes what sits at
    position 3 even though the clip that used to be there still exists elsewhere in the cut, and that
    is exactly the kind of change a diff exists to surface rather than hide because "nothing was
    deleted".
    """
    old_by_n = {b["n"]: b for b in old_beats}
    new_by_n = {b["n"]: b for b in new_beats}
    changed, unchanged, added, removed = [], [], [], []
    for n in sorted(set(old_by_n) | set(new_by_n)):
        if n not in old_by_n:
            added.append(n)
        elif n not in new_by_n:
            removed.append(n)
        else:
            fields = ("shot_id", "clip_url", "seconds", "super", "role")
            if all(old_by_n[n].get(f) == new_by_n[n].get(f) for f in fields):
                unchanged.append(n)
            else:
                changed.append(n)
    return {"changed": changed, "unchanged": unchanged, "added": added, "removed": removed}


def classify(old_v: dict, new_beats: list[dict], new_tracks: dict | None,
            trigger: str = "", new_grade: str | None = None) -> dict:
    """What this edit costs to realise, computed BEFORE anything is re-rendered.

    `trigger` names the edit when the beats/tracks diff alone cannot tell — specifically the two full
    remakes, which are not visible as a beat diff at all: changing the cast or the location touches
    every clip's CONTENT without necessarily changing the manifest's structure, since the same beat
    numbers, the same roles and even the same durations can carry an entirely different film once the
    person in it is someone else. Pass `trigger` as one of `FULL_REMAKE_TRIGGERS` whenever the person
    is asking for that, rather than waiting for the diff to notice — it cannot.

    `new_grade` follows the same `None`-means-unchanged convention as `new_tracks`. This lives INSIDE
    `classify()` rather than being bolted on by whichever caller happens to check it — `commit()` used
    to call this function directly while only `propose_edit()` re-classified a grade-only change from
    `none` up to `free` afterward, so `/cut-grade` (which calls `commit()`) reported every grade change
    as costing nothing to do at all, one line after actually rendering a new master to do it. Two
    places computing the same answer is exactly how this project's other defects happened; this one
    was found the same session the rule was written down, inside the module that carries the rule.
    """
    grade_changed = new_grade is not None and new_grade != old_v.get("grade", "")
    old_beats = old_v.get("beats") or []
    d = diff_beats(old_beats, new_beats)
    old_tracks = _clean_tracks(old_v.get("tracks"))
    # `None` means "this edit does not touch the tracks", not "wipe them to empty" — the same
    # unchanged-unless-named convention `commit()` already uses. Comparing against an empty dict here
    # made EVERY edit that didn't explicitly resend the tracks look like it had erased the music bed,
    # which is the opposite of what "propose an edit" is supposed to be safe to call.
    effective_tracks = old_tracks if new_tracks is None else _clean_tracks(new_tracks)
    audio_changed = old_tracks != effective_tracks

    # Every branch below returns through here, so `grade_changed` is never dropped just because some
    # OTHER thing about the edit also happened to need a render — the exact gap that made `commit()`
    # and `propose_edit()` disagree in the first place.
    def done(**kw) -> dict:
        kw.setdefault("audio_changed", audio_changed)
        kw["grade_changed"] = grade_changed
        return {"diff": d, **kw}

    if trigger in FULL_REMAKE_TRIGGERS:
        return done(**{"class": "full",
                       "why": f"the {trigger} is changing — every clip carries it, so this is a new "
                              f"film, not an edit of this one",
                       "cost": "full remake — every beat is re-rendered"})

    if d["changed"] or d["added"] or d["removed"]:
        # A beat needs a genuinely new render only if its clip does not exist ANYWHERE in the parent
        # version — not merely if it sits at a different POSITION than before. Comparing position-for-
        # position first classified a reorder as needing two new renders, because beat 1 held a
        # different clip than beat 1 used to. A reorder is the flagship "free" case this manifest
        # exists to make possible, so getting it wrong here would have undercut the whole point.
        old_clips = {b.get("clip_url") for b in old_beats if b.get("clip_url")}
        new_by_n = {b["n"]: b for b in new_beats}
        needs_render = [n for n in d["changed"] + d["added"]
                       if new_by_n.get(n, {}).get("clip_url") not in old_clips]
        if needs_render:
            if len(needs_render) == len(new_beats):
                return done(**{"class": "full", "why": "every beat's clip is changing",
                               "cost": "full remake"})
            return done(**{"class": "one-clip",
                           "why": f"{len(needs_render)} beat(s) need a new render: "
                                 f"{', '.join(str(n) for n in needs_render)}",
                           "cost": f"{len(needs_render)} clip(s) re-rendered; every other beat "
                                   f"stays byte-identical"})
        # Every changed beat kept its own clip — a reorder, a retime, a new super. Free. A grade
        # change riding along costs nothing extra: the re-cut this already needs is the same ffmpeg
        # pass a grade-only edit would have needed on its own.
        return done(**{"class": "free" if not audio_changed else "audio",
                       "why": "beats reordered, retimed or re-captioned — same clips, re-cut" +
                             (" and the audio changed too" if audio_changed else ""),
                       "cost": "no render — a re-cut from clips already on disk" +
                               (" plus an audio pass" if audio_changed else "")})

    if audio_changed:
        return done(**{"class": "audio", "why": "only the audio changed",
                       "cost": "an audio pass over the existing master"})

    if grade_changed:
        return done(**{"class": "free", "why": "only the grade changed",
                       "cost": "no render — a filter pass over the master"})

    return done(**{"class": "none", "why": "nothing that this manifest tracks has changed",
                   "cost": "nothing to do"})


def propose_edit(cut: dict, new_beats: list[dict], new_tracks: dict | None = None,
                 grade: str | None = None, trigger: str = "") -> dict:
    """What WOULD happen if this edit were committed. Nothing is written. This is the whole point of
    the manifest existing: the cost is visible before anyone asks for the render."""
    cur = latest(cut)
    if not cur:
        return {"class": "none", "why": "no cut to edit yet"}
    return classify(cur, [_clean_beat(b, i) for i, b in enumerate(new_beats)], new_tracks,
                    trigger, new_grade=grade)


def commit(cut: dict, new_beats: list[dict], *, new_tracks: dict | None = None,
          grade: str | None = None, master_url: str = "", scored_url: str = "",
          trigger: str = "") -> tuple[dict | None, dict, str]:
    """Create version n+1. Returns `(cut, edit_info, error)`.

    `master_url` / `scored_url` are supplied by the CALLER, already produced by `filmcut.stitch()` or
    `filmaudio.mix_timeline()` according to what `classify()` said this edit costs — this function
    never renders anything itself. Left blank, they carry forward from the parent version unchanged,
    which is correct for an audio-only or metadata-only edit that never touched the picture.
    """
    cur = latest(cut)
    if not cur:
        return None, {}, "This cut has no version to edit yet — start it first."
    cleaned = [_clean_beat(b, i) for i, b in enumerate(new_beats)]
    info = classify(cur, cleaned, new_tracks, trigger, new_grade=grade)

    rows = _load()
    row = next((r for r in rows if r.get("id") == cut.get("id")), None)
    if not row:
        return None, {}, "This cut no longer exists."

    new_v = {
        "version": cur["version"] + 1, "parent_version": cur["version"],
        "beats": cleaned,
        "tracks": _clean_tracks(new_tracks) if new_tracks is not None else cur.get("tracks", {}),
        "grade": str(grade) if grade is not None else cur.get("grade", ""),
        "master_url": str(master_url).strip() or cur.get("master_url", ""),
        "scored_url": str(scored_url).strip() or (
            cur.get("scored_url", "") if not info["audio_changed"] else ""),
        "approved": None, "created": _now(), "edited": _now(),
        "diff": info["diff"], "class": info["class"],
    }
    row["versions"].append(new_v)
    _save(rows)
    return row, info, ""


def approve(cut: dict, who: str, version: int | None = None) -> tuple[dict | None, str]:
    """Sign off a version — by default the latest. A signed version is not mutated further; the next
    edit, whatever it is, becomes the version after it."""
    who = str(who or "").strip()
    if not who:
        return None, "Approval needs a name — an unattributed sign-off is not a signature."
    rows = _load()
    row = next((r for r in rows if r.get("id") == cut.get("id")), None)
    if not row:
        return None, "This cut no longer exists."
    v = get_version(row, version) if version is not None else latest(row)
    if not v:
        return None, "No such version."
    v["approved"] = {"who": who, "at": _now()}
    _save(rows)
    return row, ""


def summary(cut: dict | None) -> dict:
    """The cut's own account of itself — version count, what's approved, what the latest edit cost."""
    if not cut:
        return {"exists": False}
    vs = cut.get("versions") or []
    cur = vs[-1] if vs else None
    appr = last_approved(cut)
    return {
        "exists": True, "id": cut.get("id", ""), "execution": cut.get("execution", ""),
        "version_count": len(vs),
        "latest_version": cur.get("version") if cur else None,
        "latest_class": cur.get("class") if cur else None,
        "latest_approved": bool(cur and cur.get("approved")),
        "last_approved_version": appr.get("version") if appr else None,
        "beats": len(cur.get("beats") or []) if cur else 0,
    }
