"""filmedit.py -- the editor's notes on SOUND and RHYTHM, worked out from the script, the sound plan and the director's read (VIDEO_CRAFT_FRAMEWORK.md slice 5: E1, E4, E5, E6).

No model and no cost: everything here is arithmetic on what the film already says. The picture decisions (which shots, how many) were made by the shot plan and the flow review; this is
the other half of the cut, where the sound lands.

    E5  the music lifts on the TURN the director found (and not on a scene the planner guessed), and a line that carries the message gets a beat of silence before it;
    E5  a spoken line must fit its scene (it should not run past the cut);
    E1  length follows intensity: the turn and the message carrier are not given less time than an ordinary scene;
    E6  the film ends on its message carrier;
    E4  a cut inside one beat is made on the action, a cut between two times needs a marker (the director's read already names the unmarked ones).

A note that can be fixed in one move carries a `fix` the page applies to the sound plan or to a line's timing ({type: 'music', scene, value} or {type: 'line_lead', scene, value}); the rest
is advice. Pure functions, brand-, category- and language-agnostic (words are counted, never read).
"""
from __future__ import annotations

import filmvoice
import soundplan

LEAD_SLACK = 1.5          # seconds a scene must have spare (after its line) before a full 1.0 s of silence is suggested
LEAD_FULL = 1.0
LEAD_SHORT = 0.5
SHORT_SCENE_RATIO = 0.8   # a scene this much shorter than the average is "short" for an important beat


def _int(v, default=0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _no(row: dict, i: int) -> int:
    return _int(row.get("no"), i + 1) if isinstance(row, dict) else i + 1


def _first_line(row: dict):
    """(index in row['audio'], entry) of the first spoken line of a structured scene, else (None, None). A scene written as prose has no per-line timing to set."""
    if isinstance(row.get("audio"), list):
        for j, a in enumerate(row["audio"]):
            if isinstance(a, dict) and str(a.get("text") or "").strip():
                return j, a
    return None, None


def effective_music(rows, sound_plan) -> dict[int, str]:
    """{scene number: the music state the film will really use}: the person's choice in the plan, else the one derived from the beat roles."""
    base = soundplan.derive(rows)
    norm = soundplan.normalise(sound_plan) or {"scenes": {}}
    return {n: norm["scenes"].get(n, st) for n, st in base.items()}


def notes(rows, seconds, beat_map=None, sound_plan=None, sound_off=False) -> dict:
    """{notes: [{id, kind, scene, note, fix?}], turn_scene, carrier_scene, music: {scene: state}, facts}. `kind` is sound / rhythm / ending / transition. Empty `notes` means nothing to say. `sound_off`: the person switched the Sound design card off, so the music is not theirs to tune and the music notes are left out."""
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    secs = [max(0, _int((seconds or [])[i] if i < len(seconds or []) else 0, 4)) for i in range(len(rows))]
    nos = [_no(r, i) for i, r in enumerate(rows)]
    out: list[dict] = []
    if not rows:
        return {"notes": [], "turn_scene": None, "carrier_scene": None, "music": {}, "facts": {}}
    bm = beat_map if isinstance(beat_map, dict) else {}
    roles = {d["no"]: d["role"] for d in soundplan.describe(rows)}
    turn = _int(bm.get("turn_scene"), -1)
    if turn not in nos:
        turn = next((n for n in nos if roles.get(n) == "turn"), -1)
    carrier = _int(bm.get("carrier_scene"), -1)
    if carrier not in nos:
        carrier = next((n for n in reversed(nos) if roles.get(n) == "brand"), nos[-1])
    music = effective_music(rows, sound_plan)
    idx = {n: i for i, n in enumerate(nos)}

    # E5 -- the music lifts on the turn the director found
    if not sound_off and turn in nos and music.get(turn) != "swell":
        out.append({"id": "music-turn", "kind": "sound", "scene": turn,
                    "note": f"The music is set to '{music.get(turn, 'open')}' on scene {turn}, the turn of the film: that is where it should lift, so the change lands with the music.",
                    "fix": {"type": "music", "scene": turn, "value": "swell", "label": f"Lift the music on scene {turn}"}})
    for n in ([] if sound_off else nos):
        if n not in (turn, carrier) and music.get(n) == "swell" and roles.get(n) == "turn" and turn in nos:
            out.append({"id": "music-misplaced", "kind": "sound", "scene": n,
                        "note": f"The music lifts on scene {n}, where the planner guessed the turn, but the director's read puts the turn at scene {turn}: the lift lands on the wrong moment.",
                        "fix": {"type": "music", "scene": n, "value": "open", "label": f"Keep the music level on scene {n}"}})

    # E5 -- a beat of silence before the message line
    if carrier in nos:
        row = rows[idx[carrier]]
        j, line = _first_line(row)
        words = filmvoice._scene_words(row)
        if line is not None and words:
            at = line.get("timing_at")
            has_lead = (at not in (None, "")) and _int(at, 0) > 0 or str(line.get("timing") or "").lower() in ("middle", "end")
            slack = secs[idx[carrier]] - words / filmvoice.WORDS_PER_SEC
            if not has_lead:
                lead = LEAD_FULL if slack >= LEAD_SLACK else (LEAD_SHORT if slack >= LEAD_SHORT + 0.3 else 0.0)
                if lead:
                    out.append({"id": "silence-before-message", "kind": "sound", "scene": carrier,
                                "note": f"The message line of scene {carrier} starts the moment the scene does. A beat of silence before it ({lead:g} s) lets the picture land first and gives the line weight.",
                                "fix": {"type": "line_lead", "scene": carrier, "value": lead, "label": f"Start the line {lead:g} s in"}})
                else:
                    out.append({"id": "silence-before-message", "kind": "sound", "scene": carrier,
                                "note": f"The message line of scene {carrier} fills the scene, so there is no room for a beat of silence before it: lengthen the scene or shorten the line."})

    # E5 -- a spoken line must fit its scene
    for i, row in enumerate(rows):
        words = filmvoice._scene_words(row)
        if words and secs[i]:
            need = words / filmvoice.WORDS_PER_SEC
            if need > secs[i]:
                out.append({"id": "line-overruns", "kind": "rhythm", "scene": nos[i],
                            "note": f"The line in scene {nos[i]} needs about {need:.1f} s but the scene holds {secs[i]} s: it would run past the cut. Shorten the line or lengthen the scene."})

    # E1 -- length follows intensity
    sc_by_no = {s.get("no"): s for s in (bm.get("scenes") or []) if isinstance(s, dict)}
    live = [s for s in secs if s]
    if live:
        avg = sum(live) / len(live)
        for n, label in ((turn, "turn"), (carrier, "message")):
            if n in nos and n != -1 and secs[idx[n]] and secs[idx[n]] < avg * SHORT_SCENE_RATIO and (sc_by_no.get(n) or {}).get("intensity", 3) >= 2:
                if not any(x["id"] == f"short-{label}" for x in out):
                    out.append({"id": f"short-{label}", "kind": "rhythm", "scene": n,
                                "note": f"Scene {n} is the {label} of the film but holds {secs[idx[n]]} s, less than the average scene ({avg:.1f} s). Hold longest on what matters."})

    # E6 -- end on the message carrier
    if carrier in nos and carrier != nos[-1] and roles.get(nos[-1]) != "button":
        out.append({"id": "end-on-message", "kind": "ending", "scene": carrier,
                    "note": f"The message lands in scene {carrier} but the film goes on for {len(nos) - 1 - idx[carrier]} more scene{'s' if len(nos) - 1 - idx[carrier] != 1 else ''}. End on the message carrier."})

    # E4 -- a cut inside one beat is made on the action
    seen: dict = {}
    for s in (bm.get("scenes") or []):
        if isinstance(s, dict) and s.get("beat"):
            seen.setdefault(s["beat"], []).append(s.get("no"))
    for beat, members in seen.items():
        if len(members) > 1:
            out.append({"id": "cut-on-action", "kind": "transition", "scene": members[1],
                        "note": f"Scenes {', '.join(str(m) for m in members)} are one beat: make the cut between them on the action (end the first mid-gesture and open the next on its completion), not on a pause."})
    return {"notes": out, "turn_scene": turn if turn in nos else None, "carrier_scene": carrier if carrier in nos else None, "music": music,
            "facts": {"scenes": len(rows), "seconds": sum(secs), "average_scene": round(sum(live) / len(live), 1) if live else 0}}
