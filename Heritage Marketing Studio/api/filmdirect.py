"""filmdirect.py -- the director's read of a film: the BEAT MAP (VIDEO_CRAFT_FRAMEWORK.md slice 4: D1-D6).

Before anyone decides how many camera angles a scene needs, someone has to say what each scene is FOR. The beat map gives every scene one purpose and an intensity (0 quiet ...
3 payoff), says whether it is `continuous`, a `flashback`, a `flash-forward` or part of a `montage` (time passing by repetition), groups scenes that are one beat shown at
two scales, and names the TURN (where the change lands), the MESSAGE CARRIER (where the core line or hero object lands) and the hero object that must keep its shape.

It is stored on the film and read by the shot proposer (/scene-shots) and the flow review (/film-review). Two of its findings are RULES, not opinions, so they are enforced
there with no model: a scene inside a montage gets no extra angles (time passing is shown by variation, never by more angles on one moment: D5), and when two scenes are one
beat the second is the first's closer view and gets none (D3).

Pure text logic, no I/O: the route in main.py (`POST /film-direct`) only calls the model. Brand-, category- and language-agnostic: every input is the film's own data and the
judgement is by meaning, not by words.
"""
from __future__ import annotations

import json
import re

TIME_MODES = ("continuous", "flashback", "flash-forward", "montage")
_MODE_WORDS = {"flash back": "flashback", "flash-back": "flashback", "memory": "flashback", "past": "flashback", "flash forward": "flash-forward", "flashforward": "flash-forward",
               "future": "flash-forward", "present": "continuous", "real-time": "continuous", "real time": "continuous", "linear": "continuous", "time-passing": "montage",
               "time passing": "montage", "time lapse": "montage", "timelapse": "montage"}
INTENSITY_LABELS = ("quiet", "building", "high", "payoff")


def _clip(text, n) -> str:
    t = " ".join(str(text or "").split())
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def _int(v, default=0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _says(row: dict) -> str:
    if isinstance(row.get("audio"), list) and row["audio"]:
        return " ".join(str((a or {}).get("text") or "") for a in row["audio"] if isinstance(a, dict)).strip()
    return str(row.get("dialogue") or "").strip()


def scene_no(row: dict, i: int) -> int:
    return _int(row.get("no"), i + 1) if isinstance(row, dict) else i + 1


def mode_of(value) -> str:
    v = str(value or "").strip().lower().replace("_", "-")
    v = _MODE_WORDS.get(v, v)
    return v if v in TIME_MODES else ""


def build_prompt(*, rows, seconds, logline="", message="", tone="", pace="", characters="", hero="", roles=None) -> str:
    """The director's brief: the whole script in order, the film's own words, and what to decide per scene."""
    film = []
    if logline:
        film.append(f"THE FILM: {_clip(logline, 320)}")
    if message:
        film.append(f"ITS CORE MESSAGE: {_clip(message, 300)}")
    if tone:
        film.append(f"ITS TONE: {_clip(tone, 220)}")
    if characters:
        film.append(f"WHO IS IN IT: {_clip(characters, 360)}")
    if hero:
        film.append(f"THE HERO OBJECT (the product or key prop that must keep its shape): {_clip(hero, 160)}")
    lines = []
    for i, row in enumerate(rows or []):
        if not isinstance(row, dict):
            continue
        secs = _int((seconds or [])[i] if i < len(seconds or []) else 0, 4)
        role = str((roles or {}).get(scene_no(row, i)) or row.get("beat_role") or "")
        says = _clip(_says(row), 140)
        lines.append(f"SCENE {scene_no(row, i)} ({secs} s" + (f", planned job: {role}" if role else "") + f"): {_clip(row.get('visual') or row.get('title') or row.get('desc'), 260)}"
                     + (f' | says: "{says}"' if says else ""))
    return (
        "You are the director of a brand film, reading its finished script BEFORE any frame is drawn. Decide what each scene is FOR, as a viewer experiences the film in order. "
        "Judge by MEANING, in whatever language the film is written; never by particular words.\n\n"
        + "\n".join(film) + "\n\nTHE SCRIPT:\n" + "\n".join(lines) + "\n\n"
        "DECIDE, for every scene (use its number exactly as written):\n"
        "1. `purpose` — one plain line: what this scene does for the story (\"surprise at the short hem\", \"the memory that explains it\"). Not a description of the picture.\n"
        "2. `intensity` — 0 quiet, 1 building, 2 high, 3 payoff. Exactly one or two scenes may be 3. A film where every scene has the same intensity has no shape.\n"
        "3. `time_mode` — `continuous` (the present, in order), `flashback`, `flash-forward`, or `montage` (the story says the same thing happened again and again over days, months or years, "
        "and the scene is one of those repetitions). If the logline or the spoken lines say time passes by repetition, the repeating scenes are `montage`; they must show VISIBLY DIFFERENT "
        "days (light, clothes, what has changed), never the same action twice.\n"
        "4. `marker` — for any scene whose time_mode differs from the scene before it, name how the viewer is told the time has changed (a change of light, a younger face, a caption, a sound). "
        "If the script gives none, leave it empty: that is a finding, not something to invent.\n"
        "5. `beat` — a short id. Scenes whose main action is the SAME (same subject, same verb, same object, even at a different scale) are ONE beat shown twice: give them the SAME id. "
        "Different moments get different ids. Only neighbouring scenes may share an id.\n"
        "6. `hero` — true when the hero object (the pack, product or key prop) is visible in the scene.\n"
        "7. `place` — a short tag for WHERE the scene is (\"kitchen\", \"school gate\", \"street\"); the same place gets the same tag. Judge by the picture the script describes, not the story's setting alone.\n"
        "8. `energy` — 0 a held still, 1 small gestures, 2 clear action or a camera that moves with it, 3 big action or a reveal. How much HAPPENS on screen, not how important the beat is.\n"
        "9. `change` — one line: what is different at the END of the scene from its START (something learned, an object changed, a decision made, a mood turned). Empty when nothing changes.\n"
        "ENGAGEMENT. A film must be ENTERTAINING, not only clear and not repeated. Read it as a viewer who would swipe away: does the first scene earn the next five seconds with something unexpected or a question; does every scene change something; "
        "does the place, scale or energy change from one scene to the next; does it escalate towards the turn; is there at least one scene a viewer would remember? Judge this honestly in the fields above; do not describe a dull scene as lively.\n"
        "Then name the TURN (`turn_scene`: the one scene where the change or realisation lands) and the MESSAGE CARRIER (`carrier_scene`: where the core line or the hero object lands, usually the last), "
        "say whether the film as a whole is about `time_passing`, and give a one-sentence `summary` of the film's shape as a viewer would feel it.\n\n"
        "Return ONLY JSON, no prose and no markdown: "
        "{\"summary\":\"...\",\"time_passing\":false,\"hero_object\":\"\",\"turn_scene\":4,\"carrier_scene\":6,"
        "\"scenes\":[{\"no\":1,\"purpose\":\"...\",\"intensity\":1,\"time_mode\":\"continuous\",\"marker\":\"\",\"beat\":\"a\",\"hero\":false,\"place\":\"kitchen\",\"energy\":1,\"change\":\"...\"}]}")


def parse(raw: str):
    """The JSON object a model reply holds, or None when it cannot be read. Tolerates markdown fences and prose around the JSON."""
    t = str(raw or "").strip()
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.I)
    t = re.sub(r"\s*```\s*$", "", t)
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        data = json.loads(t[i:j + 1])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def validate(raw: dict, rows, roles=None) -> dict:
    """The beat map after the backstops: {summary, time_passing, hero_object, turn_scene, carrier_scene, scenes:[{no, purpose, intensity, time_mode, marker, beat, hero}],
    transitions, findings, notes}. Every scene of the script gets exactly one entry (a scene the model skipped gets a plain default and a note); intensity is 0-3; time_mode is one of
    TIME_MODES; beats are re-numbered b1, b2... and only NEIGHBOURING scenes may share one; the turn and the carrier must be real scenes (the carrier defaults to the sign-off scene, or
    the last); findings are the checks a program can make (unmarked time jumps, a flat film, a turn that is not the strongest scene, a carrier without the hero object)."""
    raw = raw if isinstance(raw, dict) else {}
    nos = [scene_no(r, i) for i, r in enumerate(rows or []) if isinstance(r, dict)]
    by_no = {}
    for s in raw.get("scenes") if isinstance(raw.get("scenes"), list) else []:
        if isinstance(s, dict) and _int(s.get("no"), -1) in nos and _int(s.get("no"), -1) not in by_no:
            by_no[_int(s.get("no"), -1)] = s
    notes: list[str] = []
    out: list[dict] = []
    prev_mode = "continuous"
    for n in nos:
        s = by_no.get(n)
        if s is None:
            notes.append(f"Scene {n} was not read by the review, so it has a plain default.")
            s = {}
        mode = (mode_of(s.get("time_mode")) or prev_mode) if s else "continuous"
        out.append({"no": n, "purpose": _clip(s.get("purpose"), 160), "intensity": max(0, min(3, _int(s.get("intensity"), 1))), "time_mode": mode,
                    "marker": _clip(s.get("marker"), 140), "beat": str(s.get("beat") if s.get("beat") is not None else "").strip()[:12] or f"n{n}", "hero": bool(s.get("hero")),
                    "place": _clip(s.get("place"), 40).lower(), "energy": max(0, min(3, _int(s.get("energy"), 1))), "change": _clip(s.get("change"), 160)})
        prev_mode = mode
    # beats: re-number; only neighbouring scenes share one
    k, last_raw = 0, None
    for sc in out:
        if last_raw is None or sc["beat"] != last_raw:
            k += 1
        last_raw = sc["beat"]
        sc["beat"] = f"b{k}"
    turn, carrier = _int(raw.get("turn_scene"), -1), _int(raw.get("carrier_scene"), -1)
    if turn not in nos:
        before_last = out[:-1]
        top = max((sc["intensity"] for sc in before_last), default=0)
        turn = next((sc["no"] for sc in before_last if sc["intensity"] == top), -1)
        if turn != -1:
            notes.append(f"No usable turn was named, so the strongest scene before the last (scene {turn}) is shown as the turn.")
    if carrier not in nos:
        brand = [n for n in nos if str((roles or {}).get(n) or "") == "brand"]
        carrier = brand[-1] if brand else (nos[-1] if nos else -1)
        notes.append(f"No usable message carrier was named, so scene {carrier} (the sign-off or the last scene) is shown.")
    findings: list[dict] = []
    transitions = []
    for a, b in zip(out, out[1:]):
        if a["time_mode"] != b["time_mode"]:
            marked = bool(b["marker"])
            transitions.append({"from": a["no"], "to": b["no"], "from_mode": a["time_mode"], "to_mode": b["time_mode"], "marked": marked})
            if not marked:
                findings.append({"kind": "unmarked-transition", "scene": b["no"], "note": f"The film moves from {a['time_mode']} to {b['time_mode']} between scene {a['no']} and scene {b['no']} "
                                                                                          "with nothing in the script to tell the viewer (a change of light, a younger face, a caption, a sound)."})
    if len(out) >= 4 and len({sc["intensity"] for sc in out}) == 1:
        findings.append({"kind": "flat", "scene": None, "note": f"Every scene has the same intensity ({out[0]['intensity']}): the film has no shape, nothing for the viewer to build to."})
    if turn in nos and out and max(sc["intensity"] for sc in out) > next(sc["intensity"] for sc in out if sc["no"] == turn):
        findings.append({"kind": "weak-turn", "scene": turn, "note": f"Scene {turn} is the turn but another scene is stronger; the change should land on the strongest scene."})
    hero = _clip(raw.get("hero_object"), 120)
    if hero and carrier in nos and not next(sc["hero"] for sc in out if sc["no"] == carrier):
        findings.append({"kind": "carrier-without-hero", "scene": carrier, "note": f"Scene {carrier} carries the message but does not show {hero}."})
    eng = engagement(out)
    findings += eng["findings"]
    groups: dict[str, list[int]] = {}
    for sc in out:
        groups.setdefault(sc["beat"], []).append(sc["no"])
    for b, members in groups.items():
        if len(members) > 1:
            findings.append({"kind": "one-beat", "scene": members[1], "note": f"Scenes {', '.join(str(m) for m in members)} are ONE beat shown at more than one scale; the first holds the beat and the "
                                                                              f"{'others are its closer ' + ('views' if len(members) > 2 else 'view')} (no extra angles on them)."})
    return {"summary": _clip(raw.get("summary"), 400), "time_passing": bool(raw.get("time_passing")), "hero_object": hero, "turn_scene": turn if turn in nos else None,
            "carrier_scene": carrier if carrier in nos else None, "scenes": out, "transitions": transitions, "findings": findings, "notes": notes, "engagement": {"risk": eng["risk"]}}


SAME_PLACE_RUN = 4        # this many neighbouring scenes in one place reads as one long scene
FLAT_RUN = 3              # this many neighbouring scenes at energy 0-1 is a stretch where nothing happens
LATE_PEAK = 0.4           # the first scene of real intensity should come by this share of the film


def engagement(scenes: list) -> dict:
    """Is this film ENTERTAINING, from the director's own per-scene fields (place, energy, change, intensity)? {risk: low|medium|high, findings: [{kind, scene, note}]}. These are checks a
    program can make; the model supplies the fields and is told to judge honestly. Kinds: slow-hook (the first scene is quiet), same-place (a long run in one place), flat-energy (a run of
    scenes where almost nothing happens), no-change (scenes that change nothing), late-peak (nothing builds until late). Added after the 28 Oct film: less repetitive, but one kitchen, six passive
    scenes, nothing changing until scene 4, and 'boring as hell'."""
    out: list[dict] = []
    n = len(scenes)
    if n < 3:
        return {"risk": "low", "findings": []}
    first = scenes[0]
    if first["energy"] <= 1 and first["intensity"] <= 1:
        out.append({"kind": "slow-hook", "scene": first["no"], "note": f"The film opens quietly (scene {first['no']}: energy {first['energy']}, intensity {first['intensity']}). The first seconds must earn the next five with something unexpected, a question or a visible action."})
    run, start = 1, 0
    for i in range(1, n + 1):
        if i < n and scenes[i]["place"] and scenes[i]["place"] == scenes[i - 1]["place"]:
            run += 1
            continue
        if run >= SAME_PLACE_RUN:
            out.append({"kind": "same-place", "scene": scenes[start]["no"], "note": f"{run} neighbouring scenes (scene {scenes[start]['no']} to {scenes[i - 1]['no']}) happen in the same place ('{scenes[start]['place']}'). A viewer sees one room for as long as it lasts: change the place, the time of day or the scale, or cut one."})
        run, start = 1, i
    run, start = 0, 0
    for i, sc in enumerate(scenes + [None]):
        if sc is not None and sc["energy"] <= 1:
            if run == 0:
                start = i
            run += 1
            continue
        if run >= FLAT_RUN:
            out.append({"kind": "flat-energy", "scene": scenes[start]["no"], "note": f"Scenes {scenes[start]['no']} to {scenes[i - 1]['no']} are all held stills or small gestures: nothing happens on screen for {run} scenes in a row. Give at least one of them an action, a reveal or a moving camera."})
        run = 0
    idle = [sc["no"] for sc in scenes if not sc["change"]]
    if len(idle) >= max(2, n // 3):
        out.append({"kind": "no-change", "scene": idle[0], "note": f"Scenes {', '.join(str(x) for x in idle)} change nothing: the story, an object or the mood is the same at their end as at their start. A scene that changes nothing is a cut candidate or needs something to happen."})
    peak = next((i for i, sc in enumerate(scenes) if sc["intensity"] >= 2), None)
    if peak is not None and peak > 0 and peak / n > LATE_PEAK:
        out.append({"kind": "late-peak", "scene": scenes[peak]["no"], "note": f"Nothing builds until scene {scenes[peak]['no']} ({peak} of {n} scenes in). Escalate earlier, or give the opening scenes a stake of their own."})
    risk = "high" if len(out) >= 3 else ("medium" if out else "low")
    return {"risk": risk, "findings": out}


def no_coverage(beat_map) -> dict:
    """{scene number: the reason it may carry NO extra angles}, from a stored beat map. Two rules, no model: a scene inside a MONTAGE (time passing is shown by variation, not by
    more angles on one moment: D5) and any scene after the first of a one-beat group (the first holds the beat, the others are its closer views: D3)."""
    out: dict[int, str] = {}
    if not isinstance(beat_map, dict):
        return out
    seen_beats: set[str] = set()
    for sc in beat_map.get("scenes") if isinstance(beat_map.get("scenes"), list) else []:
        if not isinstance(sc, dict):
            continue
        n = _int(sc.get("no"), -1)
        if n < 0:
            continue
        if sc.get("time_mode") == "montage":
            out[n] = "this scene is part of a montage (time passing by repetition): it is shown by a different day, never by more angles on one moment"
        elif sc.get("beat") in seen_beats:
            out[n] = "this scene is the closer view of the beat the scene before it already holds, so it is its own coverage"
        if sc.get("beat"):
            seen_beats.add(str(sc["beat"]))
    return out


def read_text(beat_map, scene: int | None = None) -> str:
    """The beat map as plain text for another prompt (shot proposer, flow review): one line per scene, this scene marked. '' when there is no map."""
    if not isinstance(beat_map, dict) or not isinstance(beat_map.get("scenes"), list) or not beat_map["scenes"]:
        return ""
    lines = []
    for sc in beat_map["scenes"]:
        if not isinstance(sc, dict):
            continue
        n = _int(sc.get("no"), -1)
        bits = [f"{INTENSITY_LABELS[max(0, min(3, _int(sc.get('intensity'), 1)))]}", str(sc.get("time_mode") or "continuous")]
        if sc.get("place"):
            bits.append(f"in {sc['place']}")
        if sc.get("energy") is not None:
            bits.append(f"energy {max(0, min(3, _int(sc.get('energy'), 1)))}/3")
        if n == beat_map.get("turn_scene"):
            bits.append("THE TURN")
        if n == beat_map.get("carrier_scene"):
            bits.append("THE MESSAGE CARRIER")
        lines.append(f"  Scene {n} ({', '.join(bits)}): {_clip(sc.get('purpose'), 110)}" + ("  <== THIS SCENE" if scene is not None and n == scene else ""))
    head = "THE DIRECTOR'S READ OF THE FILM (given; do not redo it)" + (f": {_clip(beat_map.get('summary'), 220)}" if beat_map.get("summary") else "")
    return head + "\n" + "\n".join(lines)
