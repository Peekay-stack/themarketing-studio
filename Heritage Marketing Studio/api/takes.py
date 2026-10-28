"""takes.py -- the film builder's saved state: FRAME takes (variants of a storyboard frame), CLIP takes (attempts at a shot's video), what is chosen, trims and the budget
(FILM_BUILDER_PLAN.md section 4; FILM_PIPELINE_MAP.md Part 3). Pure functions, no I/O: filmscript.save() passes the page's `video_builder` through `normalise` so whatever is stored has a known
shape and sane limits, and the clip routes (slice S1b onwards) use the same helpers.

KEYS are the film's own frame keys: "<position>" for a scene's master shot and "<position>.<k>" for its k-th extra shot, where position is the scene's 0-based place in the script. They are the
same keys `sceneFrames` uses, so the one existing re-keying logic (removing a shot closes the gap) covers both and a chosen frame can always be mirrored into `sceneFrames[key]`.

A take is append-only history: choosing one never deletes the others. The only things dropped here are takes that cannot be real any more (a render that was in flight when the server or page
went away) and takes beyond the per-shot cap (oldest unchosen first). Nothing here deletes a media file.
"""
from __future__ import annotations

import re
import time
import uuid

VERSION = 1
MAX_TAKES = 12                       # per shot, per layer; unchosen oldest go first
MAX_KEYS = 200
_KEY = re.compile(r"^\d{1,3}(\.\d{1,2})?$")
FRAME_STATUS = ("done", "error")     # a frame take that was "rendering" is not a take
CLIP_STATUS = ("done", "error", "rendering", "interrupted")
TIERS = ("draft", "final")
ENGINES = ("omni", "kling")
MODES = ("frame", "chain", "extend", "elements")

# Measured on the Gemini Omni API (27-29 Oct 2026): dollars per OUTPUT second. Anything not measured is None: the UI says "estimate unavailable", it never guesses.
RATE_USD_PER_SEC = {("omni", "draft"): 0.034, ("omni", "final"): 0.101}
OMNI_FLOOR_SECONDS = 3               # Omni's shortest clip: a 2 s shot is generated at 3 s and trimmed


def valid_key(key) -> bool:
    return bool(_KEY.match(str(key)))


def new_id(prefix: str = "tk") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _s(v, n: int) -> str:
    return str(v or "")[:n]


def _num(v, default=0.0, lo=0.0, hi=1e6) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    if f != f:                       # NaN
        return default
    return max(lo, min(hi, f))


def _url(v) -> str:
    """A served media path or an http(s) URL. A data: URI (which can be megabytes) is never stored in a take."""
    u = str(v or "").strip()
    return u if (u.startswith("/") or u.startswith("http://") or u.startswith("https://")) and len(u) <= 600 else ""


def _checks(v) -> list[dict]:
    out = []
    for c in (v if isinstance(v, list) else [])[:8]:
        if isinstance(c, dict) and str(c.get("id") or "").strip():
            out.append({"id": _s(c.get("id"), 30), "label": _s(c.get("label"), 40), "verdict": "check" if c.get("verdict") == "check" else "ok", "note": _s(c.get("note"), 240)})
    return out


def frame_take(raw) -> dict | None:
    """One frame take from what the page keeps for a rendered frame (its `sceneFrames` entry plus an id). Needs a stored url; a frame that never rendered is not a take."""
    if not isinstance(raw, dict):
        return None
    url = _url(raw.get("url"))
    if not url or raw.get("status") not in FRAME_STATUS + (None, "", "done"):
        return None
    if raw.get("status") == "rendering":
        return None
    return {"id": _s(raw.get("id"), 24) or new_id("fr"), "url": url, "status": "done" if raw.get("status") != "error" else "error", "provider": _s(raw.get("provider"), 24),
            "sig": _s(raw.get("sig"), 600), "recipe": _s(raw.get("recipe"), 80), "look": _s(raw.get("look"), 400), "packMissing": bool(raw.get("packMissing")),
            "packShape": _s(raw.get("packShape"), 160), "angleSame": _s(raw.get("angleSame"), 160), "checks": _checks(raw.get("checks")), "checkedUrl": _url(raw.get("checkedUrl")),
            "checkAccepted": bool(raw.get("checkAccepted")), "checkSeen": _s(raw.get("checkSeen"), 240), "note": _s(raw.get("note"), 200), "created": _s(raw.get("created"), 24) or _now()}


def clip_take(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    status = raw.get("status") if raw.get("status") in CLIP_STATUS else "error"
    if status == "rendering":
        status = "interrupted"       # nothing is rendering when a saved film is read back: the job died with its server or page
    url = _url(raw.get("url"))
    if status == "done" and not url:
        status = "error"
    return {"id": _s(raw.get("id"), 24) or new_id("tk"), "url": url, "tier": raw.get("tier") if raw.get("tier") in TIERS else "draft", "engine": raw.get("engine") if raw.get("engine") in ENGINES else "omni",
            "seconds": _num(raw.get("seconds"), 0.0, 0.0, 60.0), "mode": raw.get("mode") if raw.get("mode") in MODES else "frame", "frame": _url(raw.get("frame")), "sig": _s(raw.get("sig"), 600),
            "interaction_id": _s(raw.get("interaction_id"), 200), "status": status, "error": _s(raw.get("error"), 300), "note": _s(raw.get("note"), 200), "checks": _checks(raw.get("checks")),
            "est_usd": (None if raw.get("est_usd") is None else _num(raw.get("est_usd"), 0.0, 0.0, 1000.0)), "created": _s(raw.get("created"), 24) or _now()}


def _cap(takes: list[dict], chosen_id: str, limit: int = MAX_TAKES) -> list[dict]:
    """Keep at most `limit` takes: the chosen one is never dropped, the oldest others go first."""
    if len(takes) <= limit:
        return takes
    drop = len(takes) - limit
    out = []
    for t in takes:
        if drop > 0 and t["id"] != chosen_id:
            drop -= 1
            continue
        out.append(t)
    return out


def _layer(raw, make, chosen_raw, with_status=False):
    takes_out: dict[str, list[dict]] = {}
    chosen_out: dict[str, str] = {}
    if not isinstance(raw, dict):
        return takes_out, chosen_out
    for key, lst in list(raw.items())[:MAX_KEYS]:
        if not valid_key(key) or not isinstance(lst, list):
            continue
        seen, takes = set(), []
        for item in lst[:MAX_TAKES * 3]:
            t = make(item)
            if t and t["id"] not in seen:
                seen.add(t["id"]); takes.append(t)
        cid = str((chosen_raw or {}).get(key) or "") if isinstance(chosen_raw, dict) else ""
        if cid not in seen or next(t for t in takes if t["id"] == cid)["status"] == "error":
            cid = ""
        takes = _cap(takes, cid)
        if takes:
            takes_out[str(key)] = takes
        if cid and any(t["id"] == cid for t in takes):
            chosen_out[str(key)] = cid
    return takes_out, chosen_out


def empty() -> dict:
    return {"version": VERSION, "frames": {}, "frame_chosen": {}, "takes": {}, "chosen": {}, "trim": {}, "budget": {"cap_usd": 0.0, "spent_usd": 0.0}}


def normalise(doc) -> dict | None:
    """The builder state made safe for storage. None when there is nothing in it (so a film that never used the builder stores nothing). Unknown keys and fields are dropped; a
    chosen take that no longer exists, or errored, is un-chosen; frame takes that were mid-render are dropped, clip takes that were mid-render become 'interrupted'."""
    if not isinstance(doc, dict):
        return None
    out = empty()
    out["frames"], out["frame_chosen"] = _layer(doc.get("frames"), frame_take, doc.get("frame_chosen"))
    out["takes"], out["chosen"] = _layer(doc.get("takes"), clip_take, doc.get("chosen"))
    trim = {}
    for key, v in (doc.get("trim") if isinstance(doc.get("trim"), dict) else {}).items():
        if valid_key(key) and isinstance(v, dict) and key in out["chosen"]:
            a, b = _num(v.get("in"), 0.0, 0.0, 600.0), _num(v.get("out"), 0.0, 0.0, 600.0)
            if b > a:
                trim[str(key)] = {"in": round(a, 3), "out": round(b, 3)}
    out["trim"] = trim
    b = doc.get("budget") if isinstance(doc.get("budget"), dict) else {}
    out["budget"] = {"cap_usd": round(_num(b.get("cap_usd"), 0.0, 0.0, 100000.0), 2), "spent_usd": round(_num(b.get("spent_usd"), 0.0, 0.0, 100000.0), 2)}
    if not (out["frames"] or out["takes"] or out["budget"]["cap_usd"] or out["budget"]["spent_usd"]):
        return None
    return out


def estimate_clip(seconds, tier: str = "draft", engine: str = "omni") -> float | None:
    """Estimated dollars for one clip of `seconds`: the measured output rate x the seconds actually generated (Omni never makes less than 3 s). None when the rate has not been measured
    (Kling via fal is reported, not measured): the page then says so instead of showing a number."""
    rate = RATE_USD_PER_SEC.get((engine, tier))
    if rate is None:
        return None
    secs = max(float(seconds or 0), 0.0)
    if secs <= 0:
        return 0.0
    if engine == "omni":
        secs = max(secs, OMNI_FLOOR_SECONDS)
    return round(rate * secs, 3)


def chosen_frame(doc, key) -> dict | None:
    """The chosen frame take for a shot, or None."""
    if not isinstance(doc, dict):
        return None
    cid = (doc.get("frame_chosen") or {}).get(str(key))
    return next((t for t in (doc.get("frames") or {}).get(str(key)) or [] if t.get("id") == cid), None)


def chosen_clip(doc, key) -> dict | None:
    if not isinstance(doc, dict):
        return None
    cid = (doc.get("chosen") or {}).get(str(key))
    return next((t for t in (doc.get("takes") or {}).get(str(key)) or [] if t.get("id") == cid), None)


def use_clips_for(doc, trims: bool = True) -> dict:
    """The `use_clips` payload for `_produce_video_sync` built from the chosen clip takes: {key: [{url, seconds, in?, out?}]}. Only done takes with a stored file are included."""
    out = {}
    for key in (doc.get("chosen") or {}) if isinstance(doc, dict) else {}:
        t = chosen_clip(doc, key)
        if t and t["status"] == "done" and t["url"]:
            item = {"url": t["url"], "seconds": t["seconds"], "mode": t["mode"]}
            tr = (doc.get("trim") or {}).get(key)
            if trims and tr:
                item["in"], item["out"] = tr["in"], tr["out"]
            out[key] = [item]
    return out
