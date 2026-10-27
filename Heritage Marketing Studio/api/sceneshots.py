"""sceneshots.py -- "Break into shots": proposing the EXTRA camera angles for one scene (VIDEO_COVERAGE_PLAN.md, step 3).

Pure text logic, no I/O: the prompt a model is given, how its reply is read, and the deterministic backstops that stand between a
model's proposal and the script. The route in main.py (`POST /scene-shots`) only calls the model; nothing here is saved by itself --
the person sees an editable proposal and accepts it.

What the 27 Oct trials taught (plan section 11) and where it lands here:
  * Sizes alone ("medium", "over-the-shoulder") produced near-copies of the master frame, so every shot must state the camera POSITION.
  * A wide shot shows parts of the room the master frame never showed; without a signed location plate the room is invented, so a wide
    shot on an unlocked location carries a warning (and the prompt steers away from it).
  * Objects drift between angles (the glass was on the counter, then in the boy's hands, then back): the prompt says keep every object
    in the state it has in shot 1.
  * The scene's total seconds never change: the extras are given whole seconds and the master keeps the rest (filmvoice.split_shot_seconds).
"""
from __future__ import annotations

import json
import re
import uuid

import filmvoice
import videoprompt

SIZES = ("wide", "medium", "close", "detail", "over", "product")
MOVES = ("static", "push-in", "pull-out", "pan", "tracking", "handheld", "orbit")
_SIZE_WORDS = {"close-up": "close", "closeup": "close", "close up": "close", "cu": "close", "ecu": "detail", "macro": "detail",
               "insert": "detail", "detail insert": "detail", "extreme close-up": "detail", "ots": "over", "over-the-shoulder": "over",
               "over the shoulder": "over", "over-shoulder": "over", "two-shot": "medium", "two shot": "medium", "mid": "medium",
               "medium shot": "medium", "wide shot": "wide", "establishing": "wide", "long": "wide", "product hero": "product"}
_MOVE_WORDS = {"push in": "push-in", "pushin": "push-in", "dolly in": "push-in", "pull out": "pull-out", "pullout": "pull-out",
               "dolly out": "pull-out", "track": "tracking", "follow": "tracking", "hand-held": "handheld", "locked": "static",
               "locked-off": "static", "still": "static", "none": "", "": ""}
PREFER = ("close", "detail", "over", "medium")      # what to reach for when the location is not locked (no wide)


def max_extras(secs) -> int:
    """How many EXTRA shots a scene of `secs` seconds can hold at >= 2 s each (the scene's own row is shot 1): 4 s -> 1, 6 s -> 2, 8 s -> 3."""
    try:
        return max(0, min(filmvoice.MAX_EXTRA_SHOTS, int(secs) // filmvoice.SHOT_FLOOR - 1))
    except (TypeError, ValueError):
        return 0


def _clip(text, n) -> str:
    t = " ".join(str(text or "").split())
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def _spoken(row: dict) -> str:
    """The scene's spoken words, for RHYTHM only (what the shots must serve, never repeat)."""
    parts = []
    if isinstance(row.get("audio"), list):
        parts = [str((a or {}).get("text") or "") for a in row["audio"] if isinstance(a, dict)]
    elif row.get("dialogue"):
        parts = [str(row.get("dialogue"))]
    return _clip(" ".join(p for p in parts if p.strip()), 260)


def build_prompt(*, row: dict, secs: int, n_extras: int, logline: str = "", characters: str = "", location_line: str = "",
                 wardrobe: str = "", camera_notes: str = "", look_note: str = "", plate_locked: bool = False,
                 pack_in_scene: bool = False, prev_visual: str = "", next_visual: str = "", signoff: bool = False) -> str:
    master = videoprompt.visual_text([row]) or _clip(row.get("visual"), 300)
    cam = _clip(row.get("camera"), 120)
    size = str(row.get("shot_size") or "").strip().lower()
    spoken = _spoken(row)
    ctx = []
    if characters:
        ctx.append("CAST: " + _clip(characters, 700))
    if location_line:
        ctx.append("LOCATION: " + _clip(location_line, 300))
    if wardrobe:
        ctx.append("WARDROBE: " + _clip(wardrobe, 300))
    if camera_notes or look_note:
        ctx.append("CAMERA AND LOOK OF THE FILM: " + _clip(" ".join(x for x in (camera_notes, look_note) if x), 500))
    near = []
    if prev_visual:
        near.append("the scene before shows: " + _clip(prev_visual, 200))
    if next_visual:
        near.append("the scene after shows: " + _clip(next_visual, 200))
    pack_in_scene = pack_in_scene or signoff
    sizes_ok = [s for s in SIZES if s != "product" or pack_in_scene]
    signoff_rule = (
        "\nTHIS IS THE CLOSING SIGN-OFF SCENE. The film ends on its LAST shot, and that must be the pack: clean, readable, front-facing, with "
        "calm uncluttered space around it for the line and the logo. The extra shots add life AROUND the pack (the hands, the glass, the table) "
        "and must never hide, redraw or crowd it. Make the LAST extra shot size `product`, locked-off, the pack square to the camera and "
        "nothing moving in front of it.\n" if signoff else "")
    wide_rule = ("A wide shot is allowed." if plate_locked else
                 "AVOID wide shots: the location is NOT locked, so a wide shot would show parts of the room the master frame never "
                 "showed and the room would be invented. Prefer close, over, detail and medium.")
    return (
        "You are the first assistant director on a brand film, planning the COVERAGE of ONE scene: the other camera angles that will be "
        "cut together with the scene's master shot, the way a crew shoots a scene from several positions.\n\n"
        + (f"THE FILM: {_clip(logline, 300)}\n" if logline else "")
        + f"THE SCENE ({secs} seconds in total). Shot 1, the master, is already fixed and is NOT yours to change:\n"
        f"  Master shot: {_clip(master, 400)}"
        + (f"\n  Master camera: {cam}" if cam else "") + (f"\n  Master size: {size}" if size else "") + "\n"
        + (f"  Spoken over this scene (for rhythm only; never put words in a shot): \"{spoken}\"\n" if spoken else "")
        + ("\n".join(ctx) + "\n" if ctx else "")
        + ("NEIGHBOURING SCENES (do not repeat their pictures): " + "; ".join(near) + "\n" if near else "")
        + signoff_rule
        + f"\nWrite {n_extras} EXTRA shot{'s' if n_extras != 1 else ''} for this scene (shot 2" + (f" to shot {n_extras + 1}" if n_extras > 1 else "") + ").\n\n"
        "RULES\n"
        "1. SAME MOMENT, SAME PLACE, SAME PEOPLE. Each extra shot is one camera view of one moment of this scene (no split screens, no "
        "montage). Use only the people, props and place already in the scene or the notes above. Do not invent characters, products, "
        "signage or locations.\n"
        "2. STATE THE CAMERA POSITION. For every shot give `camera_position`: one sentence saying where the camera stands, what is in "
        "the soft foreground and what it looks at, for example \"The camera is just behind the mother's right shoulder, her shoulder "
        "soft in the left foreground, looking across at the boy.\" A size name alone is NOT enough: the angle must clearly differ from "
        "the master and from every other shot, in distance AND in side or height.\n"
        "3. KEEP EVERY OBJECT IN THE STATE IT HAS IN SHOT 1 (a glass full or empty, a pouch open or closed, who holds what) unless this "
        "shot's action is the thing that changes it. The shots are cut together, so the action must continue, not restart.\n"
        "4. NO WORDS ON SCREEN OR IN THE MOUTH. No dialogue, no quoted speech, no captions, no on-screen text, no logos. Describe only "
        "what the camera sees.\n"
        f"5. SIZES: choose from {', '.join(sizes_ok)}. `detail` is an extreme close-up of one thing (the hands, the pour, the label); "
        "`over` is over-the-shoulder. " + wide_rule + " Do not give two neighbouring shots the same size.\n"
        f"6. SECONDS: `secs` is whole seconds for each extra shot, between 2 and 4. The master keeps the rest and stays the longest shot; all shots together fill "
        f"the scene's {secs} seconds.\n"
        "7. MOVEMENT: give `camera` (a short plain phrase, e.g. \"slow push-in\", \"handheld drift\", \"locked-off\") and `movement_class`, one of "
        + ", ".join(MOVES) + " (or \"\" if none). Keep movement gentle; the people's faces must stay recognisable.\n\n"
        "Return ONLY JSON, no prose and no markdown: "
        "{\"shots\":[{\"camera_position\":\"...\",\"action\":\"what the camera sees in this shot, one or two sentences\","
        "\"shot_size\":\"close\",\"camera\":\"slow push-in\",\"movement_class\":\"push-in\",\"secs\":2}]}")


def parse(raw: str):
    """The list of shot dicts a model reply holds, or None when it cannot be read. Tolerates markdown fences and prose around the JSON."""
    t = str(raw or "").strip()
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.I)
    t = re.sub(r"\s*```\s*$", "", t)
    for a, b in (("{", "}"), ("[", "]")):
        i, j = t.find(a), t.rfind(b)
        if i >= 0 and j > i:
            try:
                data = json.loads(t[i:j + 1])
            except ValueError:
                continue
            if isinstance(data, dict):
                data = data.get("shots") if "shots" in data else data.get("rows")
            if isinstance(data, list):
                return [s for s in data if isinstance(s, dict)]
    return None


_BAN_SENTENCE = re.compile(r"\b(captions?|subtitles?|on-?screen text|title card|super(?:imposed)?|watermark|logo text|speech bubble)\b", re.I)
_QUOTED = re.compile(r"[\"“”][^\"“”]{0,200}[\"“”]")


def _clean(text: str, notes: list, who: str) -> str:
    """One piece of shot text with quoted speech removed and any sentence that asks for text/captions dropped."""
    t = " ".join(str(text or "").split())
    if _QUOTED.search(t):
        t = _QUOTED.sub("", t)
        notes.append(f"{who}: quoted words were removed from the description (a shot shows a picture, it does not speak)")
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]
    kept = [s for s in sentences if not _BAN_SENTENCE.search(s)]
    if len(kept) != len(sentences):
        notes.append(f"{who}: a sentence about on-screen text was removed")
    return videoprompt.clean_visual(" ".join(kept))


def _master_longest(lens: list[int]) -> list[int]:
    """The master carries the scene's action, so it stays at least as long as any extra angle: seconds move from the longest extra to the
    master until it is (a 10s scene proposed as 2 + 3 + 3 + 2 becomes 3 + 2 + 3 + 2). The total never changes; extras stay >= 2s."""
    out = list(lens)
    while len(out) > 1 and out[0] < max(out[1:]) and max(out[1:]) > filmvoice.SHOT_FLOOR:
        i = max(range(1, len(out)), key=lambda j: out[j])
        out[i] -= 1
        out[0] += 1
    return out


def validate(raw_shots, *, secs: int, plate_locked: bool = False, pack_in_scene: bool = False, master_size: str = "",
             want: int | None = None, signoff: bool = False) -> dict:
    """The proposal after the deterministic backstops: {shots, master_secs, notes}. Never raises on a bad model reply: unusable shots are
    dropped and said so. Each kept shot is {id, visual, shot_size, camera, movement_class, secs, warnings}."""
    notes: list[str] = []
    limit = max_extras(secs)
    if want is not None:
        limit = min(limit, max(0, int(want)))
    shots: list[dict] = []
    for n, s in enumerate(raw_shots or [], start=2):
        who = f"shot {n}"
        action = _clean(s.get("action") or s.get("visual"), notes, who)
        pos = _clean(s.get("camera_position"), notes, who)
        if not action and not pos:
            notes.append(f"{who}: nothing usable to show, left out")
            continue
        if not pos:
            notes.append(f"{who}: the model gave no camera position, so this angle may come out like shot 1 — add one")
        visual = " ".join(p for p in (pos, action) if p)
        size = str(s.get("shot_size") or "").strip().lower()
        size = _SIZE_WORDS.get(size, size)
        if size not in SIZES:
            notes.append(f"{who}: unknown size \"{size or 'none'}\", set to medium")
            size = "medium"
        if size == "product" and not pack_in_scene:
            notes.append(f"{who}: a product hero is only for a scene about the pack, set to detail")
            size = "detail"
        mv = str(s.get("movement_class") or "").strip().lower()
        mv = _MOVE_WORDS.get(mv, mv)
        mv = mv if mv in MOVES else ""
        warnings = []
        if size == "wide" and not plate_locked:
            warnings.append("Location is not locked — the room may differ from shot 1.")
        shots.append({"id": "sh" + uuid.uuid4().hex[:8], "visual": visual, "shot_size": size, "camera": _clip(s.get("camera"), 120),
                      "movement_class": mv, "secs": s.get("secs"), "warnings": warnings})
    if len(shots) > limit:
        notes.append(f"{len(shots) - limit} shot(s) left out: a {secs}s scene holds {limit + 1} shots at 2s each" if limit
                     else f"a {secs}s scene is too short to cover")
        shots = shots[:limit]
    if signoff and shots and shots[-1]["shot_size"] != "product":
        shots[-1]["warnings"].append("Sign-off scene: the film ends on this shot, so it should show the pack clean and front-on "
                                     "(set the size to Product hero).")
    prev = str(master_size or "").strip().lower()
    for k, sh in enumerate(shots, start=2):
        if prev and sh["shot_size"] == prev:
            sh["warnings"].append(f"Same size as shot {k - 1} ({prev}) — check the angle really differs.")
        prev = sh["shot_size"]
    lens, dropped = filmvoice.split_shot_seconds(secs, [sh["secs"] for sh in shots])
    lens = _master_longest(lens)
    if dropped:
        notes.append(f"{dropped} shot(s) left out: the scene is too short for that many shots")
        shots = shots[:len(lens) - 1]
    for sh, s_secs in zip(shots, lens[1:]):
        sh["secs"] = s_secs
    return {"shots": shots, "master_secs": lens[0], "notes": notes}
