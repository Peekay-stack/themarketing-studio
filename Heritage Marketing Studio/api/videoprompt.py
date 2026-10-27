"""videoprompt.py -- the prompt a frame-animation video engine is given for one shot.

Pure text-building, no I/O, so it can be tested without an engine. The shape was proven on Gemini Omni drafts on
27 Oct 2026 (tools/engine_trials/omni_step1.py): one short section per idea, in the order a director would say it --
what HAPPENS (explicit verbs, an end state), the EXPRESSION, the CAMERA, what must stay IDENTICAL to the image,
the AUDIO, and no on-screen text. With that shape the boy in the trial scene DRINKS the milk (2 takes of 2); with
the old prompt (a brand paragraph with hashtags, leftover timecodes, editing-language role text, a list of DON'Ts)
he only lifted the glass like a toast, smiled, and grew a crest on his shirt.

What it deliberately does NOT do:
  * It does not describe the cast, the set or the pack in words: the approved frame already fixes them, and words
    only give the engine something to re-draw. The KEEP section says "identical to the image", nothing more.
  * It does not state a pack shape. Prompting "almost square, never stretched" was measured to change nothing
    (printed-panel aspect stayed 1.72-1.77 against a real 1.30): the shape is decided by the starting frame.
  * It does not write the shot length. gemini.video() owns the closing "About N seconds." sentence.
"""
from __future__ import annotations

import re

# Role -> one plain sentence about what the shot is FOR, in a director's words (the older text spoke in editing
# terms such as "reads in under two seconds", which a video model cannot act on).
_ROLE_NOTE = {
    "hook": "This is the opening shot: one simple, striking image, with no set-up.",
    "world": "This shot establishes the place and the person, wide enough to read, unhurried.",
    "mechanism": "This shot shows the process actually happening; the thing being demonstrated must be visible.",
    "turn": "This is the turning point of the film: the moment something changes, played clearly.",
    "button": "This is a short, light closing beat after the sign-off; it is not a second product shot.",
    "brand": ("This is the closing product shot: the pack presented clean and front-facing, with calm uncluttered "
              "space around it; leave that space empty."),
}

# What the person in the shot must not be given by the engine. The trial's old prompt produced a crest on a plain
# school shirt and a smile nobody asked for; stating "as described, nothing added" is what the new prompt adds.
_EXPRESSION = ("natural and exactly as the action describes; no smile, toast, pose or glance at the camera that the "
               "action does not call for.")
_KEEP_PEOPLE = ("every face, hairstyle and body; the clothing exactly as it is, adding no badge, crest, logo or "
                "text to any garment; the set, the objects in it, the light and the colour grade")
_KEEP_PACK = ("the product pack exactly as in the image: its shape and proportions, label, logo, colours and every "
              "printed word, at the same size and position in frame throughout, never stretched, redrawn, "
              "relabelled or swapped for another pack")
_AUDIO = "Audio: quiet room sound only; no speech, no singing, no music."
_NO_TEXT = "No on-screen text, captions, subtitles, logos or watermarks."

_TIMECODE = re.compile(r"^\s*\(?\d+(?:[.:]\d+)?\s*(?:s|sec|secs)?\s*[-–—]+\s*\d+(?:[.:]\d+)?\s*(?:s|sec|secs)?\)?\s*[:.\-–—]?\s*", re.I)


def clean_visual(text: str) -> str:
    """One scene's picture text with the leftovers of how it was stored removed: a leading timecode ("0-6s"), the
    ":." / ".:" / ".." that appear when the title ends in a full stop and the description is empty, runs of
    spaces. The words themselves are never changed."""
    t = " ".join(str(text or "").split())
    t = _TIMECODE.sub("", t)
    t = re.sub(r"\s*:\s*\.", ".", t)           # "watches.:."  -> "watches."
    t = re.sub(r"\.\s*:", ".", t)              # "watches.:"   -> "watches."
    t = re.sub(r"(?<!\.)\.{2}(?!\.)", ".", t)   # a doubled full stop (not an ellipsis)
    t = re.sub(r"^[\s.:;,\-–—]+", "", t)   # an orphaned lead-in
    t = re.sub(r"\s*:\s*$", "", t).strip()
    if t and t[-1] not in ".!?…":
        t += "."
    return t


def visual_text(items) -> str:
    """What the CAMERA sees for these scene rows: title/visual plus description, spoken line only as a last resort
    for a malformed row with no picture at all. The spoken line is a separate layer, mixed on after, and must not
    reach the picture prompt (stray mouth movement and lettering)."""
    out = []
    for s in items or []:
        if not isinstance(s, dict):
            continue
        head = str(s.get("title", "") or s.get("visual", "") or "").strip()
        desc = str(s.get("desc", "") or "").strip()
        if not head and not desc:
            desc = str(s.get("dialogue", "") or "").strip()
        piece = clean_visual(" ".join(p for p in (head, desc) if p))
        if piece:
            out.append(piece)
    return " ".join(out)


def _camera_text(camera_direction: str) -> str:
    return re.sub(r"^\s*Camera:\s*", "", " ".join(str(camera_direction or "").split()), flags=re.I).strip()


def compile_frame_shot(*, action: str, role: str = "", beat_note: str = "", continues: bool = False,
                       camera_direction: str = "", pack_in_frame: bool = False, revise: str = "") -> str:
    """The prompt for animating one approved frame.

    `action` is `visual_text(...)` for the shot. `camera_direction` is the already-decided camera sentence(s)
    (explicit movement class, locked product hold, film-wide camera note, or the restrained default).
    """
    parts = ["Animate this frame as one continuous shot, no cuts."]
    act = " ".join(str(action or "").split()) or "Keep the scene alive with small natural movement."
    if continues:
        act += " This continues the previous shot's action from a fresh angle; do not repeat it."
    note = " ".join(str(beat_note or "").split())[:300].rstrip(" .")
    if note:
        act += f" Direction: {note}."
    role_line = _ROLE_NOTE.get(str(role or ""), "")
    parts.append(f"ACTION: {act}" + (f" {role_line}" if role_line else ""))
    parts.append(f"EXPRESSION: {_EXPRESSION}")
    cam = _camera_text(camera_direction)
    if cam:
        parts.append(f"CAMERA: {cam}")
    keep = _KEEP_PEOPLE + ("; " + _KEEP_PACK if pack_in_frame else "")
    parts.append(f"KEEP IDENTICAL TO THE IMAGE: {keep}.")
    parts.append(_AUDIO)
    parts.append(_NO_TEXT)
    out = " ".join(parts)
    rv = " ".join(str(revise or "").split())
    return out + (f" Revision note: {rv}." if rv else "")
