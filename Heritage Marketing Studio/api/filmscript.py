"""filmscript.py — the Video producer's own document layer: script, department cards, character
sheet, and scene→frame mapping. One draft per house.

**Why per house, not its own project id.** Nothing upstream gives a video script a project id of its
own — `videoObjective` is a label a person picks from a short fixed list ("Brand awareness", "Campaign
film"...), never a key. One resumable draft per house matches every other single-active-item this
codebase already keeps that way (`ideas.py`'s chosen platform, the one adopted campaign) rather than
inventing a new multi-project list nobody asked for.

**Why this is not `cut.py`.** `cut.py`'s manifest looked, from an older audit, like it might already
cover this gap — it does not. That one is the *post-production* edit history (beats, tracks, grade),
scoped to an execution that exists only once a script is approved and a film is actually being cut.
This module is the working draft *before* that point: writing the script, drafting department cards,
generating storyboard frames — all of which, until now, lived in the screen's own React state with no
backend route at all. A reload mid-script lost it outright (confirmed 1 Oct against the live code —
the save/location audit's Finding #3 was still real, 26 days after it was first written down).

**A whole replace, not a merge.** The screen always sends its complete current draft, the same
convention `campaign.save()`/`ideas.adopt()` already use — there is nothing granular here worth a
partial-field update, and a merge would have to guess which half-sent field meant "unchanged" versus
"cleared", the exact ambiguity those two modules' own comments already warn about.
"""
from __future__ import annotations

import json
import os
import time

import tenancy

DIR = tenancy.dir("filmscripts")

# The fields this module owns. Deliberately narrower than everything a video project eventually touches
# (produced-film URL, cast/plate/pack library choices, aspect/music/voice production settings) — this
# is Phase 1 of the gap, the part that loses real authored work (a written script, a department note, a
# rendered frame) rather than a picked option that costs one click to redo.
FIELDS = ("video_objective", "video_concept", "script_status", "script_phase",
          "full_script", "scene_frames", "shoot", "video_characters")


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _path(house_id: str) -> str:
    return os.path.join(DIR, f"{house_id}.json")


def _blank(house_id: str) -> dict:
    return {"house": house_id, "video_objective": None, "video_concept": None,
            "script_status": "none", "script_phase": "concept", "full_script": None,
            "scene_frames": {}, "shoot": {}, "video_characters": "", "updated": ""}


def load(house_id: str) -> dict:
    """The saved draft for this house, or the blank shape if nothing has ever been saved — same keys
    either way, so the screen has one code path to hydrate from, the same discipline `ideas.as_read()`
    already uses for exactly this reason."""
    house_id = str(house_id or "").strip()
    blank = _blank(house_id)
    if not house_id:
        return blank
    try:
        with open(_path(house_id), encoding="utf-8") as fh:
            saved = json.load(fh)
    except (OSError, ValueError):
        return blank
    if not isinstance(saved, dict):
        return blank
    return {**blank, **{k: v for k, v in saved.items() if k in blank}}


def save(house_id: str, data: dict) -> dict:
    """Replace the saved draft whole. Returns the row actually written."""
    house_id = str(house_id or "").strip()
    if not house_id:
        return {}
    row = {
        "house": house_id,
        "video_objective": data.get("video_objective"),
        "video_concept": data.get("video_concept"),
        "script_status": str(data.get("script_status") or "none"),
        "script_phase": str(data.get("script_phase") or "concept"),
        # Rows/dicts straight through — `main.py` validates shape no more than `campaign.save()`
        # validates `roles`/`expressions`; this is a screen's own working state, not a document with
        # rules of its own to enforce.
        "full_script": data.get("full_script"),
        "scene_frames": data.get("scene_frames") if isinstance(data.get("scene_frames"), dict) else {},
        "shoot": data.get("shoot") if isinstance(data.get("shoot"), dict) else {},
        "video_characters": str(data.get("video_characters") or ""),
        "updated": _now(),
    }
    tmp = _path(house_id) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(row, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path(house_id))
    return row


def clear(house_id: str) -> bool:
    """Drop the saved draft — a fresh `/idea-draft`-style "start a new one" should not leave a stale
    file behind for the next house visit to accidentally resurrect."""
    house_id = str(house_id or "").strip()
    if not house_id:
        return False
    path = _path(house_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
