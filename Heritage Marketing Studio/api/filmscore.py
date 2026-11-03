"""filmscore.py -- the CRAFT SCORECARD for a film concept or script (FILM_CRAFT_LAYER_PLAN.md, workstream W0).

Is this film memorable, entertaining and clear? One model call reads the concept (or the script) and scores the owner's own tests 0-3, each with a one-line reason, plus the strongest and the weakest
test and one concrete way to strengthen the weakest. **Advice only**: it runs when someone asks, it blocks nothing, it saves nothing, and it never claims to have searched for copies (the
originality line is the model's own judgement). Nothing is trained: this is a prompt and a parser.

The tests come from the reference-ads learning log (AD_LEARNING_LOG.md, "Why the owner chose each reference" and "Where the magic is").
"""
from __future__ import annotations

import json
import re

TESTS = (
    ("message", "One clear message", "Can the film's single message be said in one plain sentence, and does the film deliver it?"),
    ("hook", "Attention hook", "Do the first seconds open a question or break an expectation, so a viewer wants to know what happens next?"),
    ("moment", "One memorable moment", "Is there ONE moment people would remember and retell (a reaction, a reversal, a line, a gag, an image), and does the film build to it?"),
    ("dramatised", "The proposition as an event", "Is the brand's promise MADE TO HAPPEN on screen (a proof, a gag, a reversal, a demonstration, an emotion tied to the benefit) rather than stated?"),
    ("device", "A memorable device", "Is there a short, repeatable device that carries the message (a line, a tune, a question with a reveal, a recurring character, a gag)?"),
    ("performance", "Performance and casting are the idea", "Is the casting and the way people speak and act part of what makes it work (a persona, an age, a pairing, lines acted to the moment)?"),
    ("original", "Original", "Does it avoid copying or closely echoing a known film? This is your own judgement from memory, not a search; say so when unsure."),
)
IDS = tuple(t[0] for t in TESTS)


def _clip(text, n) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def film_text(concept=None, rows=None, seconds=None) -> str:
    """The film as plain text for the prompt: the concept's own lines when it has them, and the script's scenes when a script is given."""
    out = []
    c = concept if isinstance(concept, dict) else {}
    for key, label in (("logline", "LOGLINE"), ("hook", "HOOK"), ("surprise", "SURPRISE"), ("turn", "TURN"), ("memorable", "MEMORABLE MOMENT"), ("stake", "STAKE"),
                       ("message", "MESSAGE"), ("move", "PROPOSITION MOVE"), ("device", "DEVICE"), ("line", "QUOTABLE LINE"), ("cast_idea", "CASTING IDEA")):
        if c.get(key):
            out.append(f"{label}: {_clip(c.get(key), 320)}")
    beats = c.get("scenes") if isinstance(c.get("scenes"), list) else []
    for b in beats[:10]:
        if isinstance(b, dict):
            out.append(f"BEAT {_clip(b.get('t'), 12)} {_clip(b.get('title'), 60)}: {_clip(b.get('desc'), 240)}")
    for i, r in enumerate(rows or []):
        if not isinstance(r, dict):
            continue
        sec = (seconds or [])[i] if i < len(seconds or []) else ""
        says = r.get("dialogue") or " ".join(str((a or {}).get("text") or "") for a in (r.get("audio") or []) if isinstance(a, dict))
        out.append(f"SCENE {r.get('no', i + 1)}" + (f" ({sec} s)" if sec else "") + f": {_clip(r.get('visual') or r.get('title') or r.get('desc'), 260)}" + (f' | says: "{_clip(says, 140)}"' if str(says or "").strip() else ""))
    return "\n".join(out)


def build_prompt(*, concept=None, rows=None, seconds=None, logline="", message="", tone="", characters="") -> str:
    film = []
    if logline:
        film.append(f"LOGLINE: {_clip(logline, 320)}")
    if message:
        film.append(f"ITS CORE MESSAGE: {_clip(message, 300)}")
    if tone:
        film.append(f"ITS TONE: {_clip(tone, 220)}")
    if characters:
        film.append(f"WHO IS IN IT: {_clip(characters, 300)}")
    body = film_text(concept, rows, seconds)
    tests = "\n".join(f"  {i + 1}. `{tid}` ({label}): {q}" for i, (tid, label, q) in enumerate(TESTS))
    return (
        "You are a veteran creative director scoring a brand film IDEA (a concept or a script, before anything is drawn or recorded) on what makes advertising memorable, entertaining and clear. "
        "Judge as a viewer would feel it, by MEANING and in whatever language it is written. Be honest: do not flatter, do not call a flat idea strong, and score only what the text shows.\n\n"
        + ("\n".join(film) + "\n\n" if film else "") + "THE FILM:\n" + (body or "(nothing was sent)") + "\n\n"
        "SCORE each test 0-3: 0 absent, 1 weak or only stated, 2 present and working, 3 outstanding. Give ONE plain line of reason per test that quotes or points at something in the text.\n" + tests + "\n\n"
        "Then name the `strongest` and the `weakest` test (by id), give a one-sentence `summary` of how the film would feel to a viewer, and ONE concrete `suggestion`: a way to strengthen the weakest test that keeps the film's own idea (an option for the director, not an order).\n\n"
        "Return ONLY JSON, no prose and no markdown: "
        "{\"tests\":[{\"id\":\"message\",\"score\":2,\"reason\":\"...\"}],\"strongest\":\"hook\",\"weakest\":\"device\",\"summary\":\"...\",\"suggestion\":\"...\"}"
    )


def parse(raw: str):
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


def validate(raw: dict) -> dict:
    """{tests:[{id,label,score,reason}], total, max, strongest, weakest, summary, suggestion, notes}. Every test of TESTS appears once in order; a test the model skipped has score None and is
    left out of the total (unknown is not zero); scores are clamped to 0-3; ids the server did not send are ignored; labels come from the server, never from the model."""
    raw = raw if isinstance(raw, dict) else {}
    got = {}
    for t in raw.get("tests") if isinstance(raw.get("tests"), list) else []:
        if isinstance(t, dict) and str(t.get("id") or "") in IDS and str(t.get("id")) not in got:
            got[str(t["id"])] = t
    tests, notes, total, n = [], [], 0, 0
    for tid, label, _q in TESTS:
        t = got.get(tid)
        try:
            score = None if t is None else max(0, min(3, int(round(float(t.get("score"))))))
        except (TypeError, ValueError):
            score = None
        if score is None:
            notes.append(f"The review did not score '{label}', so it is not counted.")
        else:
            total += score
            n += 1
        tests.append({"id": tid, "label": label, "score": score, "reason": _clip((t or {}).get("reason"), 200)})
    scored = [t for t in tests if t["score"] is not None]
    strongest, weakest = str(raw.get("strongest") or ""), str(raw.get("weakest") or "")
    if scored:
        if strongest not in {t["id"] for t in scored}:
            strongest = max(scored, key=lambda t: t["score"])["id"]
        if weakest not in {t["id"] for t in scored}:
            weakest = min(scored, key=lambda t: t["score"])["id"]
    else:
        strongest = weakest = ""
    return {"tests": tests, "total": total, "max": 3 * n, "scored": n, "strongest": strongest, "weakest": weakest,
            "summary": _clip(raw.get("summary"), 400), "suggestion": _clip(raw.get("suggestion"), 400), "notes": notes}
