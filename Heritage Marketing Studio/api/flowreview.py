"""flowreview.py -- the editor's pass over the WHOLE film before anything is rendered (VIDEO_CRAFT_FRAMEWORK.md slice 2: D3, D4, E1-E3, E6, E7).

Pure text logic, no I/O: the facts it measures (shots, seconds, cut rate, runs), the prompt a model is given, how its reply is read, and the backstops
between a model's verdict and the script. The route in main.py (`POST /film-review`) only calls the model. Nothing here changes the script: the person sees
keep / cut / merge verdicts with reasons and presses "Apply" to SKIP the shots that were marked (a skip keeps the shot in the script, it is just not rendered).

Why it exists (the 28 Oct film): every scene was reviewed alone, so a moment already shown at two scales (scenes 2-3) was covered again, a shoulder shot added
nothing, and 14 shots in 30 s ran through an unhurried film. Nobody had ever looked at the film as a viewer watches it.
Brand- and category-agnostic: every input is the film's own data (logline, scenes, spoken lines, message, tone, pace); no word of any brand is in a rule.
"""
from __future__ import annotations

import json
import re

import sceneshots

MAX_PROMPT_SHOTS = 60
VERDICTS = ("keep", "cut", "merge")


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


def film_shots(rows, seconds, roles=None) -> list[dict]:
    """Every shot the film will actually render, in order: the scene's own row is shot 1 (the master), then its extra shots that are not skipped.
    Each is {scene_i, scene, role, shot, place, secs, size, job, why, visual, signoff_hold}. `place` is the extra's position in the row's own list (None for
    the master); `shot` is the number the person sees on the board (the master is 1, extras count from 2 by place, so a skipped shot never renumbers another).
    `seconds` is the scene's seconds; the master holds what the extras leave (never under 2 s)."""
    out: list[dict] = []
    for i, row in enumerate(rows or []):
        if not isinstance(row, dict):
            continue
        secs = max(0, _int((seconds or [])[i] if i < len(seconds or []) else 0, 4))
        raw = row.get("shots") if isinstance(row.get("shots"), list) else []
        extras = [(p, s) for p, s in enumerate(raw) if isinstance(s, dict) and str(s.get("visual") or "").strip() and not s.get("skip")]
        extra_secs = [max(2, _int(s.get("secs"), 2)) for _, s in extras]
        role = str((roles or {}).get(scene_no(row, i)) or row.get("beat_role") or "")
        no = scene_no(row, i)
        base = {"scene_i": i, "scene": no, "role": role}
        out.append({**base, "shot": 1, "place": None, "secs": max(2, secs - sum(extra_secs)) if extras else secs,
                    "size": str(row.get("shot_size") or "").lower(), "job": "", "why": "", "visual": _clip(row.get("visual") or row.get("title") or row.get("desc"), 220),
                    "signoff_hold": role == "brand" and not extras})
        for (p, s), es in zip(extras, extra_secs):
            out.append({**base, "shot": p + 2, "place": p, "secs": es, "size": str(s.get("shot_size") or "").lower(),
                        "job": sceneshots.job_of(s.get("job")), "why": _clip(s.get("why"), 160), "visual": _clip(s.get("visual"), 220), "signoff_hold": False})
    return out


def budgets(rows, seconds, pace="", roles=None) -> dict:
    """{scene number: how many EXTRA shots that scene may have} under the film's pace (sceneshots.budget: what fits its seconds, held to the pace, with the
    opening and an opted-in sign-off treated as in the proposer)."""
    out: dict[int, int] = {}
    for i, row in enumerate(rows or []):
        if not isinstance(row, dict):
            continue
        secs = _int((seconds or [])[i] if i < len(seconds or []) else 0, 4)
        role = str((roles or {}).get(scene_no(row, i)) or row.get("beat_role") or "")
        out[scene_no(row, i)] = sceneshots.budget(secs, pace, role, bool(row.get("signoff_shots")))
    return out


def stats(rows, seconds, pace="", roles=None) -> dict:
    """Facts measured from the plan, no model: shot count, average length, cut rate against the pace's band, the longest run of one shot size, extras with no job,
    scenes over their pace budget, and a list of plain-language `findings` ({kind, scene, note})."""
    pk = sceneshots.normalise_pace(pace) or "standard"
    pt = sceneshots.PACE_TABLE[pk]
    shots = film_shots(rows, seconds, roles)
    total = sum(s["secs"] for s in shots)
    n = len(shots)
    per10 = round(n * 10.0 / total, 1) if total else 0.0
    lo, hi = pt["band"]
    findings: list[dict] = []
    if total and n:
        if per10 > hi * 1.15:
            findings.append({"kind": "cut-rate", "scene": None, "note": f"{n} shots in {total} s is {per10} shots per 10 s: faster than {pt['label']} pace ({lo}-{hi}). "
                                                                       "The cuts will read as restless."})
        elif per10 < lo * 0.8 and n > 1:
            findings.append({"kind": "cut-rate", "scene": None, "note": f"{n} shots in {total} s is {per10} shots per 10 s: slower than {pt['label']} pace ({lo}-{hi}). Fine for a held, quiet film; "
                                                                       "check it does not drag."})
    run, best, run_at = 0, 0, None
    prev = None
    for s in shots:
        if s["size"] and s["size"] == prev:
            run += 1
        else:
            run = 1
        prev = s["size"] or None
        if run > best:
            best, run_at = run, s
    if best >= 3 and run_at:
        findings.append({"kind": "same-size-run", "scene": run_at["scene"], "note": f"{best} shots in a row are the same size ({run_at['size']}), ending at scene {run_at['scene']}. "
                                                                                    "A run of one size reads as the same picture again."})
    same_len = 0
    for a, b in zip(shots, shots[1:]):
        same_len = same_len + 1 if a["secs"] == b["secs"] else 0
        if same_len >= 4:
            findings.append({"kind": "same-length", "scene": b["scene"], "note": f"Five shots in a row hold {b['secs']} s each (to scene {b['scene']}). "
                                                                                 "Length should follow intensity: hold longer on what matters."})
            break
    no_job = [s for s in shots if s["place"] is not None and not s["job"]]
    for s in no_job:
        findings.append({"kind": "no-job", "scene": s["scene"], "note": f"Scene {s['scene']} shot {s['shot']} has no job (what it is for), so nothing says why it should be rendered."})
    over = []
    allowed_by_scene = budgets(rows, seconds, pace, roles)
    for i, row in enumerate(rows or []):
        if not isinstance(row, dict):
            continue
        secs = _int((seconds or [])[i] if i < len(seconds or []) else 0, 4)
        extras = [s for s in shots if s["scene_i"] == i and s["place"] is not None]
        allowed = allowed_by_scene.get(scene_no(row, i), 0)
        if len(extras) > allowed:
            over.append((scene_no(row, i), len(extras), allowed))
        if len(extras) > sceneshots.max_extras(secs):
            findings.append({"kind": "does-not-fit", "scene": scene_no(row, i), "note": f"Scene {scene_no(row, i)} is {secs} s, which holds {sceneshots.max_extras(secs)} extra shot(s) at 2 s each "
                                                                                       f"but has {len(extras)}: the last will be left out of the render."})
    for no, have, allowed in over:
        findings.append({"kind": "over-budget", "scene": no, "note": f"Scene {no} has {have} extra shot{'s' if have != 1 else ''}; {pt['label']} pace allows {allowed} for a scene this long."})
    for row_i, row in enumerate(rows or []):
        if isinstance(row, dict) and str((roles or {}).get(scene_no(row, row_i)) or row.get("beat_role") or "") == "brand" and row.get("signoff_shots"):
            last = [s for s in shots if s["scene_i"] == row_i][-1]
            if last["size"] != "product":
                findings.append({"kind": "signoff-last", "scene": scene_no(row, row_i), "note": "The film ends on this scene's last shot, which should show the pack clean and front-on (Product hero)."})
    return {"pace": pk, "shots": n, "seconds": total, "avg_shot": round(total / n, 1) if n else 0.0, "per10": per10, "band": [lo, hi], "longest_same_size_run": best,
            "extras": sum(1 for s in shots if s["place"] is not None), "findings": findings}


def facts_text(st: dict) -> str:
    return (f"{st['shots']} shots in {st['seconds']} s (average {st['avg_shot']} s, {st['per10']} shots per 10 s; the {sceneshots.PACE_TABLE[st['pace']]['label']} band is "
            f"{st['band'][0]}-{st['band'][1]}); longest run of one shot size: {st['longest_same_size_run']}.")


def build_prompt(*, rows, seconds, shots, st, logline="", message="", tone="", pace="standard", characters="", roles=None) -> str:
    """The editor's brief: the whole cut in order (every shot a viewer will see), the facts measured from it, and what to decide."""
    pk = sceneshots.normalise_pace(pace) or "standard"
    pt = sceneshots.PACE_TABLE[pk]
    film = []
    if logline:
        film.append(f"THE FILM: {_clip(logline, 300)}")
    if message:
        film.append(f"ITS CORE MESSAGE (nothing may weaken or compete with it): {_clip(message, 300)}")
    if tone:
        film.append(f"ITS TONE: {_clip(tone, 220)}")
    if characters:
        film.append(f"WHO IS IN IT: {_clip(characters, 360)}")
    film.append(f"ITS PACE: {pt['label']} — {pt['feel']}. About {pt['per10']} shots per 10 seconds, average shot {pt['avg_shot']}.")
    lines = []
    by_scene: dict[int, list[dict]] = {}
    for s in shots[:MAX_PROMPT_SHOTS]:
        by_scene.setdefault(s["scene_i"], []).append(s)
    for i, row in enumerate(rows or []):
        if not isinstance(row, dict) or i not in by_scene:
            continue
        role = by_scene[i][0]["role"]
        says = _clip(_says(row), 120)
        lines.append(f"SCENE {scene_no(row, i)} ({_int((seconds or [])[i] if i < len(seconds or []) else 0, 4)} s"
                     + (f", job in the film: {role}" if role else "") + ")" + (f' — spoken: "{says}"' if says else ""))
        for s in by_scene[i]:
            tag = "master" if s["place"] is None else (s["job"] or "no job stated")
            why = f" — added because: {s['why']}" if s["why"] else ""
            lines.append(f"  shot {s['shot']} [{tag}, {s['secs']} s, {s['size'] or 'size not set'}]: {s['visual']}{why}")
    jobs = ", ".join(sceneshots.JOBS)
    return (
        "You are the director and the editor of a brand film, reviewing the finished script and shot plan BEFORE anything is rendered. Every shot costs real money and "
        "a viewer's attention. Extra shots exist for a cinematic feel and must NOT take away from the story, the film's entertainment value or its core message. "
        "Judge the film as a viewer watches it, in order, not scene by scene.\n\n"
        + "\n".join(film) + "\n\nTHE CUT, IN ORDER (shot 1 of a scene is its master; later shots are extra camera angles):\n" + "\n".join(lines)
        + "\n\nMEASURED FACTS: " + facts_text(st) + "\n\n"
        "DECIDE:\n"
        "1. BEATS. Group the scenes into beats. Scenes whose main action is the same (same subject, same verb, same object) are ONE beat shown at two scales, not two beats. "
        "Read the logline and the spoken lines for MEANING: does the story say the same action happened again and again over days, months or years (a routine, a habit, "
        "\"one at a time\", \"every morning\")? If so `time_passing` is true, even when the picture shows the action only once: that is shown by variations (light, "
        "clothes, what has changed), never by more angles on one moment. Name the TURN (the scene where the change or realisation lands) and the MESSAGE CARRIER (the scene where the core line or hero object lands, usually the last).\n"
        "2. VERDICT on EVERY extra shot (shot 2 and later). `keep`, `cut`, or `merge` (it repeats another shot, name which in `merge_with`, e.g. \"scene 3 shot 1\"). "
        "The test is: what would the viewer lose if it were cut? If nothing, cut it. Also cut a shot whose job is already done by a neighbouring scene, a shot that is the same "
        f"thing again from another angle, and a shot that would be hard for a generator to draw cleanly (two legs in motion, crowds, interlocking hands). Jobs a shot may have: {jobs}. "
        "Never cut the shot the film ends on if it carries the message. Give a one-line `reason` a viewer would agree with.\n"
        "3. NOTES. Only real problems across scenes: repetition, length not following intensity (hold longest on the turn and the message carrier), a flashback or "
        "time jump with no marker, a spoken line with no picture that carries it, a run of one size. Skip anything that is fine.\n"
        "4. SUMMARY. Two sentences, as a viewer: does it flow, and what is the one thing to fix first.\n\n"
        "Return ONLY JSON, no prose and no markdown: "
        "{\"summary\":\"...\",\"time_passing\":false,\"turn_scene\":4,\"carrier_scene\":6,"
        "\"beats\":[{\"scenes\":[2,3],\"purpose\":\"one line\",\"repetition\":true}],"
        "\"verdicts\":[{\"scene\":2,\"shot\":2,\"verdict\":\"cut\",\"merge_with\":\"\",\"reason\":\"one line\"}],"
        "\"notes\":[{\"scenes\":[2,3],\"kind\":\"repetition\",\"note\":\"one line\",\"suggestion\":\"one line\"}]}")


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


def _scenes_list(v) -> list[int]:
    out = []
    for x in (v if isinstance(v, list) else [v]):
        n = _int(x, -1)
        if n >= 0 and n not in out:
            out.append(n)
    return out[:8]


_JOB_RANK = ("payoff-hold", "reaction", "insert", "reveal", "pov", "establish", "match", "")


def validate(raw: dict, shots: list[dict], budget_by_scene: dict | None = None, pace: str = "") -> dict:
    """The review after the backstops: {summary, time_passing, turn_scene, carrier_scene, beats, verdicts, notes, skips, notes_out}.
    Every EXTRA shot (place not None) ends with exactly one verdict (a shot the model did not mention is kept, and says so); verdicts for shots that do
    not exist are dropped; a verdict with no reason is kept as `keep`; a cut on the film's closing shot when it is the product hero is refused; `skips` is the list
    of {scene, shot, place} the Apply button will switch off (cut and merge verdicts only)."""
    raw = raw if isinstance(raw, dict) else {}
    notes_out: list[str] = []
    extras = {(s["scene"], s["shot"]): s for s in shots if s["place"] is not None}
    last = shots[-1] if shots else None
    seen: dict = {}
    for v in raw.get("verdicts") if isinstance(raw.get("verdicts"), list) else []:
        if not isinstance(v, dict):
            continue
        key = (_int(v.get("scene"), -1), _int(v.get("shot"), -1))
        if key not in extras:
            notes_out.append(f"A verdict for scene {key[0]} shot {key[1]} was ignored: that shot is not in the plan.")
            continue
        verdict = str(v.get("verdict") or "").strip().lower()
        verdict = verdict if verdict in VERDICTS else ""
        reason = _clip(v.get("reason"), 240)
        merge_with = _clip(v.get("merge_with"), 60)
        if not verdict:
            notes_out.append(f"Scene {key[0]} shot {key[1]}: the verdict was not keep, cut or merge, so the shot was kept.")
            verdict = "keep"
            reason = reason or "No clear verdict from the review."
        elif verdict != "keep" and len(reason) < 6:
            notes_out.append(f"Scene {key[0]} shot {key[1]}: a {verdict} with no reason was not applied, the shot was kept.")
            verdict, reason = "keep", "No reason was given for cutting it."
        s = extras[key]
        if verdict != "keep" and last is not None and s is last and s["size"] == "product":
            notes_out.append(f"Scene {key[0]} shot {key[1]} is the film's closing pack shot: it was kept.")
            verdict, reason = "keep", "The film ends on this shot and it carries the message."
        seen[key] = {"scene": key[0], "shot": key[1], "place": s["place"], "verdict": verdict, "reason": reason,
                     "merge_with": merge_with if verdict == "merge" else "", "job": s["job"]}
    verdicts = []
    for key, s in extras.items():
        if key in seen:
            verdicts.append(seen[key])
        else:
            verdicts.append({"scene": key[0], "shot": key[1], "place": s["place"], "verdict": "keep", "reason": "Not singled out by the review.", "merge_with": "", "job": s["job"]})
    # The pace budget is a RULE, not a judgement: however many shots the model kept, a scene may not carry more extras than the film's pace allows. The surplus
    # (lowest-priority job first, later shots first) is marked cut with that reason, so the cut is explained and the person can switch any of them back on.
    scenes_present = {s["scene"] for s in shots}
    turn, carrier = _int(raw.get("turn_scene"), -1), _int(raw.get("carrier_scene"), -1)
    if budget_by_scene is not None:
        label = sceneshots.PACE_TABLE[sceneshots.normalise_pace(pace) or "standard"]["label"]
        for no in sorted({v["scene"] for v in verdicts}):
            allowed = _int(budget_by_scene.get(no), 0)
            if no == turn:      # the turn the review found may be covered even in a short scene (framework section 6), as the proposer allows for the opening
                allowed = max(allowed, sceneshots.budget(sum(s["secs"] for s in shots if s["scene"] == no), pace, "turn"))
            live = [v for v in verdicts if v["scene"] == no and v["verdict"] == "keep"]
            protected = [v for v in live if last is not None and extras[(v["scene"], v["shot"])] is last and last["size"] == "product"]
            order = sorted([v for v in live if v not in protected], key=lambda v: (_JOB_RANK.index(v["job"]) if v["job"] in _JOB_RANK else len(_JOB_RANK), v["shot"]))
            room = max(0, allowed - len(protected))
            for v in order[room:]:
                v["verdict"], v["by"] = "cut", "pace"
                v["reason"] = f"Over the {label} pace budget: a scene this long holds {allowed} extra shot{'s' if allowed != 1 else ''}." + (f" (Review said: {v['reason']})" if v["reason"] else "")
    beats = []
    for b in raw.get("beats") if isinstance(raw.get("beats"), list) else []:
        if isinstance(b, dict) and _scenes_list(b.get("scenes")):
            beats.append({"scenes": _scenes_list(b.get("scenes")), "purpose": _clip(b.get("purpose"), 160), "repetition": bool(b.get("repetition"))})
    notes = []
    for n in raw.get("notes") if isinstance(raw.get("notes"), list) else []:
        if isinstance(n, dict) and len(_clip(n.get("note"), 300)) >= 6:
            notes.append({"scenes": _scenes_list(n.get("scenes")), "kind": _clip(n.get("kind"), 30), "note": _clip(n.get("note"), 300), "suggestion": _clip(n.get("suggestion"), 240)})
    return {"summary": _clip(raw.get("summary"), 500), "time_passing": bool(raw.get("time_passing")),
            "turn_scene": turn if turn in scenes_present else None, "carrier_scene": carrier if carrier in scenes_present else None,
            "beats": beats[:12], "verdicts": verdicts, "notes": notes[:12],
            "skips": [{"scene": v["scene"], "shot": v["shot"], "place": v["place"]} for v in verdicts if v["verdict"] != "keep"],
            "notes_out": notes_out}
