"""continuity.py — does this film read as one film?

A film generated shot by shot fails in a specific way: every clip is individually plausible and the
cut is six unrelated films. There are two separable questions in that, and they need completely
different answers.

**1. Did the references travel?** (certain, free, and the one that matters)

Identity and place are held by *reference images*, not by descriptions — `library.shot_references()`
returns the signed cast frame and the signed plate for exactly this reason. So the honest continuity
question is not "do these shots look alike" but "was each shot given the same face and the same
place to work from". That is a matter of record: it either carried the reference or it didn't. This
half is deterministic, costs nothing, and it is the half worth acting on, because it names the
*cause* rather than a symptom.

**2. Does the look hold?** (measured, advisory, and weaker than it appears)

This half was built second and deliberately trusted less, because it was tested before it was
believed. Measuring mean brightness, warmth and saturation across a real 30-second Heritage film
found a legitimate 22.8-point warmth spread between two shots — a lamp-lit puja and a window-lit
sofa. **Both shots were correct.** For comparison, applying an entire named grade (`warm-dawn` over
`neutral`) moves warmth by 13.7. So a perfectly coherent film varies by more than a whole grade
change, and any fixed threshold on colour drift would have flagged good work as broken.

**NAMING ONE SHOT DOES NOT WORK. This was built, tested, and removed — do not rebuild it.**

The obvious design is to flag the shot that deviates from the others. It was built twice and it
failed both times, on real footage:

  * *Compared against the median of all shots* — one shot of a four-shot film was re-graded to
    `cool-clean` and the checker asked to find it. The deviant shot dragged the median ~5 points
    toward itself, fell under the bar, and went unreported. Worse, the same shift pushed a
    legitimately saturated endframe over the bar, so the checker named an innocent shot. One miss
    and one false accusation from a single run.
  * *Compared leave-one-out against the median of the others* — which fixes the self-hiding, and
    still failed. On the untouched, coherent film it flagged the endframe (a pack shot lit by
    sparklers, sweets and diyas, +14.8 saturation above the other three and correctly so). Re-grading
    a different shot then tripped all four at once, because the median absolute deviation of three
    values is too fragile to set a bar with.

The reason is not a tuning problem. **Legitimate shot-to-shot variance in this material is the same
size as the defect being looked for** — a lamp-lit puja against a window-lit sofa sat 22.8 apart on
warmth, and a whole grade change is 13.7. No threshold separates them, so any per-shot verdict is a
coin toss wearing a number.

So the measured half reports two things it can actually defend:

  * **the film's spread**, as a film-level finding. "These shots span 21 of warmth, wider than a
    grade step" is true, useful, and names no culprit — and it points at the right fix anyway, which
    is one grade pass over the master rather than a hunt for the bad shot.
  * **distance from the plate**, per shot, when a signed-off plate exists. This one is principled
    where the others are not: the plate is the *declared* location, so a shot far from it has drifted
    from an intent somebody recorded, not merely from its neighbours.

  * brightness is reported but never flagged. Natural luma spread in that same film was 43 points
    against a ~10-point grade delta, so luma is the one metric where the signal is smaller than the
    noise. Reporting it as a finding would be dressing up a coin toss.

**The known blind spot, stated rather than hidden.** Because luma never flags, a mismatch that is
mostly a *contrast* move is invisible here — verified: putting one shot into `rich-contrast` while the
rest sat in `neutral` moved warmth only 3.5 and went unreported, correctly by these rules and still a
real mismatch a colourist would see. Final calibration was six cases: two correct films stayed clean
(including one with the endframe deliberately regraded), four one-grade mismatches were all caught,
and this contrast-only case was missed. That is the shape of what this measures — it finds a shot in
the wrong *colour*, not a shot in the wrong *contrast*.

And colour continuity is mostly **enforced rather than detected** anyway: `composite.grade()` puts
one look across the whole master in a single pass, which fixes the drift instead of reporting it.
That is the recommendation this module makes when it sees spread it cannot explain.

**What this does not do.** It does not verify that the face is the same face. That needs a vision
model, it would be the least reliable thing here, and it would invite trusting a guess over a fact.
Identity is *held* by the cast reference and *checked* by a person looking at the cut. Saying so is
more useful than a confidence score nobody can audit.

Like `shot_viability`, this refuses nothing. A film can be flagged everywhere and still be right.
"""
from __future__ import annotations

import os
import subprocess
import uuid

import composite
import filmcut
import library
import tenancy

# How far a full named grade moves each metric — measured, not chosen. `composite.grade()` was run
# over a real render and the frame re-measured: warm-dawn +13.7 warmth, cool-clean -15.4, and
# rich-contrast -9.0 luma. So one "grade step" is about 14 on the warmth and saturation axes.
#
# This is the absolute floor for calling something an outlier. Below it, two shots are closer
# together than two takes of the same shot under two of this studio's own looks — which is not a
# continuity problem in any sense a person could act on.
GRADE_STEP = 14.0

# The bar a film's spread has to clear to be worth mentioning. Sits BELOW one grade step, and that is
# deliberate and measured.
#
# Two facts set it. Once the endframe is held out of the comparison (see `drift`), natural spread
# across the scene shots of a coherent film was **2.1 warmth and 3.4 saturation** — tiny. And a single
# shot pushed one grade out of line produced a span of **13.0**, because the other shots do not sit at
# the extreme of the move. So a bar set exactly at one grade step (14) is guaranteed to just miss the
# very error it was sized for — verified: `cool-clean` on one shot of four scored 13.0 and went
# unreported.
#
# 10 sits ~3x above measured natural variance and comfortably below a one-grade error. It was only
# possible to lower it this far by fixing the cause of the noise (the endframe) rather than raising the
# threshold until the noise stopped mattering.
SPREAD_BAR = 10.0

# Frames sampled per clip. Three, at 20/50/80%, because the first and last frames of a generated clip
# are where fades and compression artefacts live, and one mid-frame alone misses a clip that drifts
# inside itself.
SAMPLE_POINTS = (0.2, 0.5, 0.8)

# The metrics, and whether each one is allowed to raise a finding.
#
# `flags: False` on luma is the whole lesson of this module. See the docstring — natural brightness
# spread in a correct film exceeded the grade delta, so it is information for a person reading the
# table, not evidence.
METRICS: dict[str, dict] = {
    "warmth": {
        "label": "Warmth",
        "flags": True,
        "what": "Red minus blue, averaged. The axis a grade moves most, and the one that makes two "
                "shots feel like two different times of day.",
    },
    "saturation": {
        "label": "Saturation",
        "flags": True,
        "what": "How far from grey the frame sits. Drifts when shots are generated from different "
                "prompts rather than graded from one master.",
    },
    "luma": {
        "label": "Brightness",
        "flags": False,
        "what": "Average brightness. Reported, never flagged — a film legitimately moves from a dark "
                "interior to a bright yard, and measured spread here exceeded a full grade change.",
    },
}


def _thumb(path: str, size: int = 120):
    """A small RGB thumbnail, or None. Small on purpose: these are averages, and 120px is plenty."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        im = Image.open(path).convert("RGB")
        im.thumbnail((size, size))
        return im
    except Exception:
        return None


def _measure(im) -> dict | None:
    """Mean brightness, warmth and saturation of one frame."""
    if im is None:
        return None
    px = list(im.getdata())
    n = len(px)
    if not n:
        return None
    return {
        "luma":       round(sum(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px) / n, 1),
        "warmth":     round(sum(r - b for r, g, b in px) / n, 1),
        "saturation": round(sum(max(p) - min(p) for p in px) / n, 1),
    }


def image_metrics(path: str) -> dict | None:
    """Metrics for a still — a plate, a pack shot, an approved frame."""
    if not path or not os.path.exists(path):
        return None
    return _measure(_thumb(path))


def clip_metrics(path: str, seconds: float = 0.0) -> dict | None:
    """Metrics for a clip: the MEDIAN of three sampled frames.

    Median rather than mean, because one flash frame or one hard cut inside a clip would drag a mean
    somewhere no part of the clip actually sits.
    """
    if not path or not os.path.exists(path):
        return None
    if composite._is_image(path):
        return image_metrics(path)
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return None
    dur = float(seconds or 0) or float(composite.probe_video(path).get("seconds") or 0)
    if dur <= 0:
        dur = 4.0
    got: list[dict] = []
    for frac in SAMPLE_POINTS:
        tmp = os.path.join(composite.EDITS_DIR, f"_cont-{uuid.uuid4().hex[:8]}.png")
        os.makedirs(composite.EDITS_DIR, exist_ok=True)
        try:
            subprocess.run([exe, "-y", "-ss", f"{dur * frac:.2f}", "-i", path, "-frames:v", "1", tmp],
                           capture_output=True, timeout=120)
            m = image_metrics(tmp)
            if m:
                got.append(m)
        except (subprocess.SubprocessError, OSError):
            pass
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
    if not got:
        return None
    out = {"frames": len(got)}
    for key in METRICS:
        vals = sorted(m[key] for m in got)
        out[key] = vals[len(vals) // 2]
    return out


def _median(vals: list[float]) -> float:
    s = sorted(vals)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else round((s[n // 2 - 1] + s[n // 2]) / 2, 2)


def _mad(vals: list[float], mid: float) -> float:
    """Median absolute deviation — a spread measure one outlier cannot inflate.

    Standard deviation is the wrong tool here: with four shots, the single odd shot moves the
    threshold far enough to stop being odd, which is how a checker quietly passes everything.
    """
    return _median([abs(v - mid) for v in vals])


def _kind_of(url: str) -> str:
    """The library kind a reference URL points at, from its path.

    Path-based on purpose: it survives a pack refresh, a re-sign and a rename, none of which change
    which folder a file lives in.
    """
    marker = "/library-file/"
    if marker not in (url or ""):
        return ""
    return (url.split(marker, 1)[1].split("/", 1) + [""])[0]


def provenance(shots: list[dict]) -> dict:
    """Which shots carried the cast and the plate. The half of continuity that is a matter of record.

    A shot is exempt when it is live-action: real footage of a real person needs no cast reference,
    and flagging it would train people to ignore the flags.
    """
    refs = library.shot_references()
    rows = []
    for i, s in enumerate(shots or []):
        s = s if isinstance(s, dict) else {}
        live = str(s.get("provider") or "") == "live-action"
        carried = [str(x) for x in (s.get("refs") or []) if x]
        # A shot generated before this was recorded says nothing either way. Fall back to the
        # library's current state, which is what the generator would have used, and mark it inferred
        # rather than presenting a guess as a record.
        inferred = "refs" not in s and not live
        # Judged by the KIND of reference carried, not by whether the URL equals the one signed off
        # today. Matching against `refs["cast"]` was wrong twice over: it reported False for every
        # shot whenever the library had nothing signed (so a film with references looked like a film
        # without), and — worse — the day a pack or cast frame is refreshed, `reference_url` returns
        # the new one and every previously rendered shot would retroactively read as unreferenced.
        # The kind is in the path, which does not change under it.
        has_cast = bool(refs["cast"]) if inferred else any(_kind_of(r) in ("cast", "actor")
                                                           for r in carried)
        has_plate = bool(refs["plate"]) if inferred else any(_kind_of(r) == "plate" for r in carried)
        # Kept separately, because "carried a cast frame" and "carried the one signed off today" are
        # different questions and only the first is a continuity fact.
        current = bool(refs["cast"]) and any(r == refs["cast"] for r in carried)
        rows.append({
            "n": int(s.get("n") or i + 1),
            "role": str(s.get("role") or ""),
            "live_action": live,
            "exempt": live,
            "has_cast": True if live else has_cast,
            "has_plate": True if live else has_plate,
            "from_frame": bool(s.get("from_frame")),
            "current_cast": current,
            "inferred": inferred,
        })
    gen = [r for r in rows if not r["exempt"]]
    no_cast = [r["n"] for r in gen if not r["has_cast"]]
    no_plate = [r["n"] for r in gen if not r["has_plate"]]
    notes = []
    if no_cast:
        notes.append(f"Shot(s) {', '.join(map(str, no_cast))} carried no cast reference — each one "
                     f"invented its own face, and the cut will not match.")
    if no_plate:
        notes.append(f"Shot(s) {', '.join(map(str, no_plate))} carried no plate — each one invented "
                     f"its own location and light, which is what makes separate renders read as "
                     f"separate films.")
    if any(r["inferred"] for r in rows):
        notes.append("Reference use was inferred from the library's current signed-off state, not "
                     "read off the render — these shots predate the record.")
    return {
        "rows": rows, "shots": len(rows), "generated": len(gen),
        "live_action": len(rows) - len(gen),
        "without_cast": no_cast, "without_plate": no_plate,
        "library": {"has_cast": refs["has_cast"], "has_plate": refs["has_plate"], "why": refs["why"]},
        "notes": notes,
        "ok": not (no_cast or no_plate),
    }


def drift(clips: list[dict], plate_path: str = "") -> dict:
    """Measured look drift across the shots. Advisory, and deliberately hard to trip.

    `clips` is [{n, role, path, seconds}]. When a plate is given, each shot is also measured against
    it — the plate is the *declared* location, so distance from the plate means something that
    distance from the other shots does not.
    """
    rows = []
    for i, c in enumerate(clips or []):
        c = c if isinstance(c, dict) else {}
        m = clip_metrics(str(c.get("path") or ""), float(c.get("seconds") or 0))
        rows.append({"n": int(c.get("n") or i + 1), "role": str(c.get("role") or ""),
                     "measured": bool(m), **({k: m[k] for k in METRICS} if m else {})})
    measured = [r for r in rows if r["measured"]]
    if len(measured) < 2:
        return {"rows": rows, "measured": len(measured), "findings": [], "spread": {},
                "note": ("Nothing to compare — continuity is a relationship between shots, and this "
                         "is one shot." if len(measured) == 1 else
                         "No frames could be measured. ffmpeg or Pillow is unavailable, or the clip "
                         "files are not on this disk."),
                "ok": True}

    plate = image_metrics(plate_path) if plate_path else None
    # The endframe is not part of the location's look, and comparing it to one is a category error.
    # A `brand` beat is a pack on a set — the Heritage endframe measured here is a carton lit by
    # sparklers with sweets and diyas around it, legitimately +14.8 saturation above the three scene
    # shots and correctly so. Left in, it drove the whole film's spread over the bar on its own and
    # the checker suggested a grade pass on footage that did not need one.
    #
    # This exclusion is a craft judgement, not a statistical one: the endframe is a different KIND of
    # shot, so it gets measured and reported and kept out of the continuity comparison. With it out,
    # the same coherent film spans 3.4 instead of 15.1.
    scene = [r for r in measured if r["role"] != "brand"] or measured
    endframe = [r for r in measured if r["role"] == "brand"]
    spread, findings = {}, []
    for key, spec in METRICS.items():
        vals = [r[key] for r in scene]
        mid = _median(vals)
        lo, hi = min(vals), max(vals)
        span = round(hi - lo, 1)
        spread[key] = {"label": spec["label"], "median": mid, "mad": round(_mad(vals, mid), 2),
                       "flags": spec["flags"], "what": spec["what"], "range": [lo, hi],
                       "span": span, "bar": SPREAD_BAR,
                       "plate": plate[key] if plate else None,
                       "compared": [r["n"] for r in scene],
                       "endframe": [{"n": r["n"], key: r[key]} for r in endframe]}
        if not spec["flags"] or span < SPREAD_BAR:
            continue
        widest = [r["n"] for r in scene if r[key] in (lo, hi)]
        # A FILM-LEVEL statement, not an accusation against one shot. See NAMING ONE SHOT below.
        findings.append({
            "scope": "film", "metric": key, "label": spec["label"],
            "span": span, "range": [lo, hi], "bar": SPREAD_BAR, "widest": widest,
            "advice": (f"These shots span {span:.0f} of {spec['label'].lower()} — wide enough to read "
                       f"as more than one look. Widest apart: shots "
                       f"{' and '.join(map(str, widest))}. One grade pass over the whole master "
                       f"unifies them in a single render, at no cost per shot."),
        })
    # A plate that exists and cannot be read must say so. Silently omitting the comparison made the
    # payload identical to "no plate signed off", which is a different situation with a different fix —
    # found when a deliberately corrupted plate produced a clean report instead of a complaint.
    if plate_path and not plate:
        findings.append({
            "scope": "film", "metric": "plate", "label": "Plate unreadable",
            "advice": ("A plate is signed off but its file could not be measured — it may be corrupt "
                       "or in a format Pillow cannot open. The location comparison was skipped, so "
                       "this report is thinner than it looks."),
        })
    if plate:
        for r in scene:
            gap = abs(r["warmth"] - plate["warmth"])
            # SPREAD_BAR, not a laxer bar of its own. A plate one whole grade away from the footage
            # produced gaps of 12.4-14.5 in testing, so the 1.5x-grade-step bar this originally used
            # (21) could not catch the exact mismatch it existed for — the same off-by-a-hair error
            # that SPREAD_BAR was introduced to fix. There is no reason a declared reference should be
            # held to a looser standard than the shots are held to against each other.
            if gap >= SPREAD_BAR:
                findings.append({
                    "n": r["n"], "role": r["role"], "metric": "plate", "label": "Against the plate",
                    "value": r["warmth"], "median": plate["warmth"], "off": round(r["warmth"] - plate["warmth"], 1),
                    "bar": SPREAD_BAR,
                    "advice": ("This shot is far from the warmth of the signed-off plate — the "
                               "location it was supposed to be in. Either the plate did not reach "
                               "this shot, or the model overrode it."),
                })
    return {
        "rows": rows, "measured": len(measured), "spread": spread, "findings": findings,
        "plate": plate, "plate_used": bool(plate),
        "note": ("Drift is advisory. A lamp-lit beat is legitimately warmer than a window-lit one — "
                 "measured on a real film, two correct shots sat 22.8 apart on warmth, which is more "
                 "than a whole grade change. Read a finding as 'look at this', never as 'this is "
                 "wrong'."),
        "ok": not findings,
    }


def check(shots: list[dict], *, use_plate: bool = True) -> dict:
    """Both halves, with the certain one first.

    `shots` is [{n, role, path|clip_url, seconds, provider?, refs?, from_frame?}].
    """
    shots = [s for s in (shots or []) if isinstance(s, dict)]
    refs = library.shot_references()
    plate_path = ""
    if use_plate and refs["plate"]:
        plate_path = library.local_path(refs["plate"].replace("/library-file/", "")) or ""

    prov = provenance(shots)
    clips = []
    for i, s in enumerate(shots):
        raw = str(s.get("path") or s.get("clip_url") or s.get("url") or "")
        clips.append({"n": int(s.get("n") or i + 1), "role": str(s.get("role") or ""),
                      "seconds": s.get("seconds") or 0, "path": _resolve(raw)})
    look = drift(clips, plate_path)

    # Provenance first and on its own line. It is the cause; drift is a symptom, and a symptom read
    # before its cause is how somebody spends a render re-grading a film whose real problem is that
    # four shots never saw the plate.
    headline = "This film reads as one film on both checks."
    if not prov["ok"]:
        headline = ("References did not reach every shot — fix that before reading the look "
                    "measurements, because it is the cause of most of what they show.")
    elif not look["ok"]:
        headline = ("Every shot carried its references, and some still drift on look — one grade pass "
                    "over the master is the cheap fix.")
    return {
        "provenance": prov, "drift": look,
        "shots": len(shots),
        "headline": headline,
        "ok": prov["ok"] and look["ok"],
        "note": ("Identity is not verified here. A face is held by the cast reference and checked by "
                 "a person watching the cut — a confidence score from a vision model would be the "
                 "least reliable number on this screen."),
    }


def _resolve(url: str) -> str:
    """A served URL back to a path on this disk, for the three places films actually live.

    The three asset kinds go through `tenancy.asset_path`, which looks in the tenant's directory
    before the legacy shared one and refuses anything that escapes either. This function had the
    containment check right before tenancy existed — that check is now in one place and used by both
    this reader and the serving route, so they cannot drift into disagreeing about what is reachable.

    `library` is still resolved locally because it is not yet tenant-scoped. That is a known gap, not
    an oversight: see `tenancy.ASSET_KINDS`.
    """
    if not url:
        return ""
    if os.path.exists(url):
        return url
    for kind in tenancy.ASSET_KINDS:
        prefix = f"/{kind}/"
        if url.startswith(prefix):
            return tenancy.asset_path(kind, url[len(prefix):])
    if url.startswith("/library-file/"):
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.normpath(os.path.join(here, "library"))
        p = os.path.normpath(os.path.join(root, url[len("/library-file/"):].replace("/", os.sep)))
        return p if p.startswith(root + os.sep) and os.path.exists(p) else ""
    return ""


def status() -> dict:
    """What the checker measures and what it refuses to claim. Rendered as a panel, not hard-coded."""
    refs = library.shot_references()
    return {
        "metrics": {k: {"label": v["label"], "what": v["what"], "flags": v["flags"]}
                    for k, v in METRICS.items()},
        "grade_step": GRADE_STEP,
        "samples_per_clip": len(SAMPLE_POINTS),
        "library": {"has_cast": refs["has_cast"], "has_plate": refs["has_plate"],
                    "why": refs["why"]},
        "does_not": ["verify that the face is the same face — that needs a vision model, and it "
                     "would be the least reliable thing here",
                     "flag brightness, whose natural spread in a correct film exceeded a full grade "
                     "change",
                     "refuse anything — a flagged shot may still be the right shot"],
    }
