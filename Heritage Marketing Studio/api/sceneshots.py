"""sceneshots.py -- "Break into shots": proposing the EXTRA camera angles for one scene, with the judgement of a cinematographer and an editor
(VIDEO_COVERAGE_PLAN.md step 3; VIDEO_CRAFT_FRAMEWORK.md slice 1).

Pure text logic, no I/O: the prompt a model is given, how its reply is read, and the deterministic backstops that stand between a model's proposal and
the script. The route in main.py (`POST /scene-shots`) only calls the model; nothing here is saved by itself -- the person sees an editable proposal.

THE RULE (the owner's, 28 Oct 2026): extra shots exist for a cinematic feel and must NOT take away from the story, the film's entertainment value or
its core messaging. So a shot is proposed only if it
  * has a JOB (establish / reveal / reaction / insert / pov / payoff-hold / match) and a one-line reason,
  * shows something NEW that the master and the neighbouring scenes do not,
  * fits the film's PACE (Calm / Standard / Fast set how many extras a scene may have),
and ZERO extra shots is a valid, often the best, answer.

What the 27 Oct trials taught (plan section 11) and where it lands here:
  * Sizes alone ("medium", "over-the-shoulder") produced near-copies of the master frame, so every shot must state the camera POSITION.
  * A wide shot shows parts of the room the master frame never showed; without a signed location plate the room is invented (a warning, and the prompt steers away).
  * Objects drift between angles: the prompt says keep every object in the state it has in shot 1.
  * The scene's total seconds never change: the extras get whole seconds and the master keeps the rest (filmvoice.split_shot_seconds).
What the 28 Oct film taught: the first version asked for the MAXIMUM extras every scene (six drinking shots for 12 s, a shoulder shot that added nothing).
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

# The cinematic JOB of a shot: why it exists. A shot with no job is not proposed.
JOBS = ("establish", "reveal", "reaction", "insert", "pov", "payoff-hold", "match")
JOB_LABELS = {"establish": "Establish", "reveal": "Reveal", "reaction": "Reaction", "insert": "Insert", "pov": "POV",
              "payoff-hold": "Payoff hold", "match": "Match"}
JOB_MEANING = {
    "establish": "place and scale: where we are and how big or small the subject is in it",
    "reveal": "detail to context, or context to detail: something the master hides until now",
    "reaction": "a face (or a body) takes the moment in; the feeling, not the action",
    "insert": "an object or gesture that carries the story (the thing the viewer must notice)",
    "pov": "what a character sees, so the viewer is inside the moment",
    "payoff-hold": "the held shot the whole beat builds to (the realisation, the message)",
    "match": "a shot that sets up a cut to the NEXT scene (a matching shape, movement or object)",
}
_JOB_WORDS = {"cutaway": "insert", "detail": "insert", "reveal-detail": "reveal", "hold": "payoff-hold", "payoff": "payoff-hold",
              "emotional close-up": "reaction", "reaction shot": "reaction", "scale": "establish", "establishing": "establish",
              "point of view": "pov", "point-of-view": "pov", "match cut": "match", "match-cut": "match", "payoff hold": "payoff-hold"}

# PACE: how many extra shots a film's tone can carry. (VIDEO_CRAFT_FRAMEWORK.md section 6; starting numbers, tuned on real films.)
PACES = ("calm", "standard", "fast")
PACE_TABLE = {
    "calm": {"label": "Calm", "max_extras": 1, "min_scene": 6, "avg_shot": "4-5 s", "per10": "2-2.5", "band": (2.0, 2.5),
             "feel": "tender, emotional, unhurried: fewer, longer shots; hold on what matters"},
    "standard": {"label": "Standard", "max_extras": 2, "min_scene": 6, "avg_shot": "3-4 s", "per10": "2.5-3.5", "band": (2.5, 3.5),
                 "feel": "a balanced brand story: steady, clear rhythm"},
    "fast": {"label": "Fast", "max_extras": 3, "min_scene": 4, "avg_shot": "2-3 s", "per10": "3.5-5", "band": (3.5, 5.0),
             "feel": "energetic and quick: more cuts, shorter holds"},
}
# The opening (hook) and the turn may be covered even in a short scene: a reveal there is worth the cut.
EXEMPT_ROLES = ("hook", "turn")
_CALM_WORDS = ("tender", "calm", "unhurried", "gentle", "intimate", "quiet", "slow", "emotional", "heartfelt", "nostalgic", "reflective",
               "poignant", "serene", "contemplative", "measured", "patient")
_FAST_WORDS = ("energetic", "energy", "fast", "punchy", "playful", "quick", "dynamic", "bold", "vibrant", "upbeat", "youthful", "high-energy",
               "lively", "rapid", "snappy", "fun", "frantic", "pacy")


def normalise_pace(value) -> str:
    v = str(value or "").strip().lower()
    return v if v in PACES else ""


def suggest_pace(text) -> tuple[str, str]:
    """A DEFAULT pace from the film's tone words (brief tone, sound mood, logline...). Only a suggestion: the person overrides in one click.
    Returns (pace, why). No tone words either way -> 'standard'."""
    t = " " + re.sub(r"[^a-z\-]+", " ", str(text or "").lower()) + " "
    calm = [w for w in _CALM_WORDS if f" {w} " in t]
    fast = [w for w in _FAST_WORDS if f" {w} " in t]
    if len(calm) > len(fast):
        return "calm", "the tone reads " + ", ".join(calm[:3])
    if len(fast) > len(calm):
        return "fast", "the tone reads " + ", ".join(fast[:3])
    return "standard", "no clear tone words, so a balanced default"


def max_extras(secs) -> int:
    """How many EXTRA shots a scene of `secs` seconds can physically hold at >= 2 s each (the scene's own row is shot 1): 4 s -> 1, 6 s -> 2, 8 s -> 3."""
    try:
        return max(0, min(filmvoice.MAX_EXTRA_SHOTS, int(secs) // filmvoice.SHOT_FLOOR - 1))
    except (TypeError, ValueError):
        return 0


def budget(secs, pace="", role="", signoff=False) -> int:
    """How many extra shots THIS scene may have: what fits its seconds, held to the film's pace. A scene shorter than the pace's minimum gets none
    unless it is the opening or the turn (or a sign-off the person opted in). A pace that is not set counts as Standard."""
    p = PACE_TABLE[normalise_pace(pace) or "standard"]
    base = max_extras(secs)
    try:
        s = int(secs)
    except (TypeError, ValueError):
        s = 0
    if not signoff and str(role or "") not in EXEMPT_ROLES and s < p["min_scene"]:
        return 0
    return max(0, min(base, p["max_extras"]))


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


def outline_text(outline, this_index=None) -> str:
    """The whole script in a few lines, so a shot is judged against the FILM and not one scene: every scene's seconds, picture, spoken line and the
    jobs of the extra shots it already has. `outline` is a list of {no, secs, visual, says, shots:[{job, visual}]}."""
    lines = []
    for i, o in enumerate(outline or []):
        if not isinstance(o, dict):
            continue
        mark = "  <== THIS SCENE" if this_index is not None and i == this_index else ""
        shots = "; ".join(f"{s.get('job') or 'shot'}: {_clip(s.get('visual'), 70)}" for s in (o.get("shots") or []) if isinstance(s, dict))
        says = _clip(o.get("says"), 70)
        lines.append(f"  Scene {o.get('no', i + 1)} ({o.get('secs', '?')} s): {_clip(o.get('visual'), 150)}"
                     + (f" | says: \"{says}\"" if says else "") + (f" | extra shots: {shots}" if shots else "") + mark)
    return "\n".join(lines)


def build_prompt(*, row: dict, secs: int, n_extras: int, pace: str = "standard", role: str = "", logline: str = "", message: str = "",
                 tone: str = "", outline=None, scene_index=None, characters: str = "", location_line: str = "", wardrobe: str = "",
                 camera_notes: str = "", look_note: str = "", plate_locked: bool = False, pack_in_scene: bool = False,
                 prev_visual: str = "", next_visual: str = "", signoff: bool = False) -> str:
    master = videoprompt.visual_text([row]) or _clip(row.get("visual"), 300)
    cam = _clip(row.get("camera"), 120)
    size = str(row.get("shot_size") or "").strip().lower()
    spoken = _spoken(row)
    pk = normalise_pace(pace) or "standard"
    p = PACE_TABLE[pk]
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
    wide_rule = ("A wide shot is allowed." if plate_locked else
                 "AVOID wide shots: the location is NOT locked, so a wide shot would show parts of the room the master frame never "
                 "showed and the room would be invented. Prefer close, over, detail and medium.")
    signoff_rule = (
        "\nTHIS IS THE CLOSING SIGN-OFF SCENE. The film ends on its LAST shot, and that must be the pack: clean, readable, front-facing, with "
        "calm uncluttered space around it for the line and the logo. The extra shots add life AROUND the pack (the hands, the glass, the table) "
        "and must never hide, redraw or crowd it. Make the LAST extra shot size `product`, locked-off, the pack square to the camera and "
        "nothing moving in front of it.\n" if signoff else "")
    jobs = "; ".join(f"`{j}` = {JOB_MEANING[j]}" for j in JOBS)
    film = []
    if logline:
        film.append(f"THE FILM: {_clip(logline, 300)}")
    if message:
        film.append(f"ITS CORE MESSAGE (nothing may weaken or compete with it): {_clip(message, 300)}")
    if tone:
        film.append(f"ITS TONE: {_clip(tone, 200)}")
    film.append(f"ITS PACE: {p['label']} — {p['feel']}. Average shot about {p['avg_shot']}, about {p['per10']} shots per 10 seconds. "
                f"Fewer, better shots always beat more shots.")
    return (
        "You are the cinematographer and the editor of a brand film, deciding whether ONE scene needs extra camera angles and, only if it does, which. "
        "Extra shots exist to give the film a cinematic feel WITHOUT taking anything away from the story, the entertainment value or the core message.\n\n"
        + "\n".join(film) + "\n"
        + ("\nTHE WHOLE SCRIPT (so you judge this scene against the film, not on its own):\n" + outline_text(outline, scene_index) + "\n" if outline else "")
        + f"\nTHE SCENE ({secs} seconds in total). Shot 1, the master, is already fixed and is NOT yours to change:\n"
        f"  Master shot: {_clip(master, 400)}"
        + (f"\n  Master camera: {cam}" if cam else "") + (f"\n  Master size: {size}" if size else "")
        + (f"\n  This scene's job in the film: {role}" if role else "") + "\n"
        + (f"  Spoken over this scene (for rhythm only; never put words in a shot): \"{spoken}\"\n" if spoken else "")
        + ("\n".join(ctx) + "\n" if ctx else "")
        + ("NEIGHBOURING SCENES (do not repeat their pictures): " + "; ".join(near) + "\n" if near else "")
        + signoff_rule
        + "\nFIRST DECIDE WHETHER THIS SCENE NEEDS ANY EXTRA SHOT. Add a shot ONLY if all three are true:\n"
        f"  A. JOB: it does one of these jobs the master cannot: {jobs}.\n"
        "  B. NEW INFORMATION: it shows something neither the master nor the scenes around it show (a face, a hand, an object, a place, a change). "
        "If the honest answer is \"the same thing, closer\", it is not a shot.\n"
        "  C. IT SERVES THE FILM: it deepens the story, keeps the film entertaining (no run of similar shots) and supports the core message.\n"
        "ZERO extra shots is a valid and often the best answer: return an empty list and say why. "
        f"You may propose at most {n_extras} extra shot{'s' if n_extras != 1 else ''}; fewer is better.\n"
        "  * If the scene before or after already shows this scene's action at another scale (a wide then a closer view of the same moment), this scene "
        "IS already coverage of it: return none.\n"
        "  * If the film shows TIME PASSING by repeating an action (days, months, a routine), do not add angles on one moment: return none and say so.\n"
        "  * Avoid pictures image and video generators draw badly: two legs or feet in motion, crowds, interlocking hands, readable text. Prefer one "
        "subject, one limb, a still or slow frame.\n\n"
        "RULES FOR ANY SHOT YOU DO PROPOSE\n"
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
        "{\"needs_coverage\":true,\"why\":\"one sentence: why this scene does or does not need extra angles\","
        "\"shots\":[{\"job\":\"reveal\",\"why\":\"what this shot adds that shot 1 does not\",\"camera_position\":\"...\","
        "\"action\":\"what the camera sees in this shot, one or two sentences\",\"shot_size\":\"close\",\"camera\":\"slow push-in\","
        "\"movement_class\":\"push-in\",\"secs\":2}]}")


def parse(raw: str):
    """What a model reply holds: {needs_coverage, why, shots:[...]}, or None when it cannot be read. Tolerates markdown fences and prose around the
    JSON, and an older bare list of shots."""
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
            meta = {"needs_coverage": None, "why": ""}
            if isinstance(data, dict):
                meta = {"needs_coverage": data.get("needs_coverage") if isinstance(data.get("needs_coverage"), bool) else None,
                        "why": _clip(data.get("why"), 400)}
                data = data.get("shots") if "shots" in data else data.get("rows")
            if isinstance(data, list):
                return {**meta, "shots": [s for s in data if isinstance(s, dict)]}
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


def job_of(value) -> str:
    """The cinematic job named in a model's reply, as one of JOBS, or '' when there is none we recognise."""
    v = str(value or "").strip().lower().replace("_", "-")
    v = _JOB_WORDS.get(v, v)
    return v if v in JOBS else ""


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
             want: int | None = None, signoff: bool = False, pace: str = "", role: str = "") -> dict:
    """The proposal after the deterministic backstops: {shots, master_secs, notes, budget}. Never raises on a bad model reply: unusable shots are
    dropped and said so. A shot must have a recognised JOB and a one-line reason (WHY); the number is held to the scene's budget under the film's pace.
    Each kept shot is {id, job, why, visual, shot_size, camera, movement_class, secs, warnings}."""
    notes: list[str] = []
    cap = budget(secs, pace, role, signoff)
    limit = cap if want is None else min(cap, max(0, int(want)))
    shots: list[dict] = []
    for n, s in enumerate(raw_shots or [], start=2):
        who = f"shot {n}"
        job = job_of(s.get("job"))
        why = _clip(s.get("why"), 240)
        if not job:
            notes.append(f"{who}: no clear job (establish / reveal / reaction / insert / pov / payoff-hold / match), so it was left out")
            continue
        if len(why) < 6:
            notes.append(f"{who}: no reason given for what it adds, so it was left out")
            continue
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
        shots.append({"id": "sh" + uuid.uuid4().hex[:8], "job": job, "why": why, "visual": visual, "shot_size": size,
                      "camera": _clip(s.get("camera"), 120), "movement_class": mv, "secs": s.get("secs"), "warnings": warnings})
    if len(shots) > limit:
        pk = PACE_TABLE[normalise_pace(pace) or "standard"]
        if limit:
            notes.append(f"{len(shots) - limit} shot(s) left out: a {secs}s scene on {pk['label']} pace holds {limit} extra shot{'s' if limit != 1 else ''}")
        else:
            notes.append(f"all extra shots left out: a {secs}s scene gets none on {pk['label']} pace")
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
    return {"shots": shots, "master_secs": lens[0], "notes": notes, "budget": cap}
