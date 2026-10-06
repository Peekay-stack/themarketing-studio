"""soundplan.py -- how the music bed behaves around the voice, from a plan.

Until now the bed was one static level for the whole film (about 15 dB under the voice, a 1.2s fade-in, nothing else):
it never lifted in a pause, never swelled at the turn and never resolved at the end. Professionals decide those
moments first and ride the music around the voice, which stays the reference (dialogue first, music and effects
brought underneath it).

A PLAN says, per scene, what the music does when nobody is speaking:

    under   stay low, as it always did
    open    lift in the pauses (the default)
    swell   lift further (the turn, the sign-off)
    out     drop away (a button that is just ambience)

while a spoken line always wins: the music is at its "under" level for the whole line, lowering a fraction of a
second BEFORE it starts and rising again half a second after it ends. Lines are placed by the mixer, so the envelope
is computed from where they actually fall, which is also why it survives a cutdown.

    {"duck": "normal" | "subtle" | "strong" | <dB>,        # how far the music lifts above "under" when open
     "ending": "fade" | "release" | "stop",
     "carve": true,                                        # a small dip in the voice's mid frequencies
     "scenes": [{"no": 1, "music": "open"}, ...]}          # a scene not listed gets the derived state

No plan -> `resolve` returns None and the mixer does exactly what it did before. Pure arithmetic, no model, no network.
"""
from __future__ import annotations

import math

STATES = ("under", "open", "swell", "out")
DUCK_DB = {"subtle": 5.0, "normal": 8.0, "strong": 12.0}
DEFAULT_DUCK = "normal"
ENDINGS = ("fade", "release", "stop")
DEFAULT_ENDING = "fade"

SWELL_DB = 3.0          # a swell sits this much above "open"
ATTACK = 0.06           # the music is down to "under" this long before a line starts
SHIFT = 0.8             # seconds for the music to move between scene states (per "under"-to-"open" lift)
RELEASE = 0.5           # seconds for the music to rise after a line (per "under"-to-"open" lift)
STEP = 0.02             # envelope sampling step
KNOT_TOL = 0.004        # simplification tolerance, in linear gain
MIN_GAP = 0.9           # pauses shorter than this are not worth lifting for: the lines count as one
FADE_OUT = {"fade": 2.5, "release": 0.6}
CARVE_FILTER = "equalizer=f=2000:t=o:w=2:g=-3"
MAX_KNOTS = 60


def _gain(db: float) -> float:
    return 10 ** (db / 20.0)


def describe(scenes) -> list[dict]:
    """Every scene with its beat role and the music state the plan starts from -- what the Sound design card shows.

    Roles come from the same function the shots are briefed with, so the sound and the picture agree about what each
    scene is for. A Turn or the Sign-off swells, a Button drops to ambience, everything else opens.
    """
    import filmcut
    rows = [r for r in (scenes or []) if isinstance(r, dict)]
    segs = filmcut.assign_roles([{"index": i, "seconds": 6, "continues": False, "scenes": [r]}
                                 for i, r in enumerate(rows)])
    out = []
    for i, (row, seg) in enumerate(zip(rows, segs)):
        role = str(seg.get("role") or "")
        out.append({"no": _no(row, i), "role": role,
                    "music": "swell" if role in ("turn", "brand") else ("out" if role == "button" else "open")})
    return out


def derive(scenes) -> dict[int, str]:
    """The starting state for every scene, from the beat roles alone (no model)."""
    return {d["no"]: d["music"] for d in describe(scenes)}


def _no(row: dict, i: int) -> int:
    try:
        return int(row.get("no") or (i + 1))
    except (TypeError, ValueError):
        return i + 1


def normalise(plan) -> dict | None:
    """A plan from outside (the client, a saved film), made safe. Unknown values fall back to the default
    rather than failing a render. None when there is nothing to apply."""
    if not isinstance(plan, dict) or not plan:
        return None
    duck = plan.get("duck", DEFAULT_DUCK)
    if isinstance(duck, (int, float)) and not isinstance(duck, bool):
        duck_db = max(0.0, min(24.0, float(duck)))
    else:
        duck_db = DUCK_DB.get(str(duck or "").strip().lower(), DUCK_DB[DEFAULT_DUCK])
    ending = str(plan.get("ending") or DEFAULT_ENDING).strip().lower()
    scenes: dict[int, str] = {}
    for it in plan.get("scenes") or []:
        if not isinstance(it, dict):
            continue
        state = str(it.get("music") or "").strip().lower()
        try:
            no = int(it.get("no"))
        except (TypeError, ValueError):
            continue
        if state in STATES:
            scenes[no] = state
    return {"duck_db": duck_db, "ending": ending if ending in ENDINGS else DEFAULT_ENDING,
            "carve": plan.get("carve") is not False, "scenes": scenes}


def resolve(plan, scenes, total) -> dict | None:
    """The plan joined to this film: each scene's time span (from the rows' timecodes, the same windows the voice
    lines use) and its music state (the person's, else the derived one). None when there is no plan."""
    import filmvoice
    norm = normalise(plan)
    if not norm:
        return None
    rows = [r for r in (scenes or []) if isinstance(r, dict)]
    total = float(total or 0)
    base = derive(rows)
    n = max(1, len(rows))
    spans = []
    for i, row in enumerate(rows):
        fallback = (total * i / n, total * (i + 1) / n)
        start, end = filmvoice._window(row.get("tc"), fallback)
        start, end = max(0.0, min(start, total)), max(0.0, min(end, total))
        if end <= start:
            start, end = fallback
        no = _no(row, i)
        spans.append({"no": no, "start": start, "end": end, "state": norm["scenes"].get(no, base.get(no, "open"))})
    return {"duck_db": norm["duck_db"], "ending": norm["ending"], "carve": norm["carve"], "scenes": spans,
            "total": total}


def _merged_lines(lines) -> list[tuple[float, float]]:
    """The lines as sorted windows, with the ones closer than MIN_GAP joined (no lift for a breath)."""
    wins = sorted((float(a), float(b)) for a, b in (lines or []) if b > a)
    out: list[list[float]] = []
    for a, b in wins:
        if out and a - out[-1][1] < MIN_GAP:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def envelope(resolved: dict, lines, under: float, total: float) -> list[tuple[float, float]]:
    """The music gain over time as piecewise-linear knots [(seconds, linear gain)], starting at 0 and ending at
    `total`. `under` is the bed's level beneath a line (the person's Subtle/Balanced/Forward choice)."""
    total = max(0.5, float(total))
    opened = under * _gain(resolved["duck_db"])
    level = {"under": under, "open": opened, "swell": opened * _gain(SWELL_DB), "out": 0.0}
    # The speeds are measured against the lift between "under" and "open": the attack, release and shift times
    # are how long THAT move takes, and a bigger move (a swell) takes proportionally longer.
    unit = max(opened - under, 0.02 * under, 1e-3)
    spans = resolved["scenes"]
    wins = _merged_lines(lines)

    def scene_target(t: float) -> float:
        for s in spans:
            if s["start"] <= t < s["end"]:
                return level[s["state"]]
        if not spans:
            return opened
        return level[spans[-1]["state"]] if t >= spans[-1]["end"] else level[spans[0]["state"]]

    def in_line(t: float) -> bool:
        return any(a <= t < b for a, b in wins)

    def line_cap(t: float) -> float:
        # the lookahead: the music must be down by the time a line starts
        return under if (in_line(t) or in_line(t + ATTACK)) else math.inf

    knots: list[tuple[float, float]] = []
    cur = min(scene_target(0.0), line_cap(0.0))
    post_line = False             # True from a line until the music has finished rising again
    for k in range(int(total / STEP) + 2):
        t = min(total, k * STEP)
        scene_t, cap = scene_target(t), line_cap(t)
        want = min(scene_t, cap)
        if want < cur:
            # a line coming: fast (the attack); a scene state coming down: slow
            cur = max(want, cur - unit / (ATTACK if cap < scene_t else SHIFT) * STEP)
        elif want > cur:
            cur = min(want, cur + unit / (RELEASE if post_line else SHIFT) * STEP)
            if cur >= want:
                post_line = False
        if cap != math.inf:
            post_line = True
        knots.append((t, cur))
        if t >= total:
            break
    return _simplify(knots)


def _simplify(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Fewest knots that stay within KNOT_TOL of the sampled curve (Ramer-Douglas-Peucker)."""
    if len(points) < 3:
        return points

    def rdp(lo: int, hi: int, keep: set) -> None:
        (t0, g0), (t1, g1) = points[lo], points[hi]
        worst, at = 0.0, -1
        for i in range(lo + 1, hi):
            t, g = points[i]
            lin = g0 + (g1 - g0) * ((t - t0) / (t1 - t0) if t1 > t0 else 0.0)
            if abs(g - lin) > worst:
                worst, at = abs(g - lin), i
        if worst > KNOT_TOL and at > 0:
            keep.add(at)
            rdp(lo, at, keep)
            rdp(at, hi, keep)

    keep = {0, len(points) - 1}
    rdp(0, len(points) - 1, keep)
    out = [points[i] for i in sorted(keep)]
    if len(out) > MAX_KNOTS:                      # never let a pathological plan build a huge filter
        step = len(out) / MAX_KNOTS
        out = [out[int(i * step)] for i in range(MAX_KNOTS)] + [out[-1]]
    return out


def gain_expression(knots: list[tuple[float, float]]) -> str:
    """The knots as an ffmpeg expression of `t`: the first level plus one non-overlapping ramp per segment."""
    if not knots:
        return "1"
    expr = f"{knots[0][1]:.4f}"
    for (t0, g0), (t1, g1) in zip(knots, knots[1:]):
        d = g1 - g0
        if abs(d) < 1e-6 or t1 <= t0:
            continue
        expr += f"+({d:.4f})*clip((t-{t0:.3f})/{t1 - t0:.3f},0,1)"
    return expr


def bed_filter(resolved: dict | None, lines, under: float, total: float) -> str | None:
    """The music bed's filter chain (before its fade-in) for a plan, or None to keep the old static level."""
    if not resolved or not lines or not resolved.get("scenes"):
        return None
    knots = envelope(resolved, lines, under, total)
    chain = f"volume='{gain_expression(knots)}':eval=frame"
    if resolved.get("carve"):
        chain += "," + CARVE_FILTER
    return chain


def ending_filter(resolved: dict | None, total: float) -> str:
    """The fade-out for the plan's ending ('' for a hard stop or no plan)."""
    if not resolved:
        return ""
    d = FADE_OUT.get(resolved.get("ending") or "")
    if not d or total <= d:
        return ""
    return f",afade=t=out:st={total - d:.3f}:d={d}"
