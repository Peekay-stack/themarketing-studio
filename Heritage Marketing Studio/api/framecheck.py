"""framecheck.py -- the gate a storyboard frame passes BEFORE it is animated and paid for (VIDEO_CRAFT_FRAMEWORK.md slice 3: Q1-Q3).

A model looks at the frame beside what the shot was meant to show and reports only real defects: the frame is two pictures pasted together (a reference sheet's panels),
people who should not be there or are missing, a body that is wrong (legs of different length, extra or merged limbs, hands, feet), words or logos nobody asked for, or
a different picture from the description. Built here as a prompt, a reader for the reply and the backstops; `look()` makes the one model call, the route calls `look()`.

Why a model and not a pixel rule (measured 28 Oct 2026, 15 frames of the rejected film): a "hard vertical seam" detector was tried first. The real collage (scene 5's master,
the mother and the boy pasted in at the left 27 %) joins cream wall to cream wall, so its seam is no harder than the ordinary vertical edges that every kitchen frame has
(windows, table legs, a person's edge: 60-90 % of rows step in almost every frame). Neither a gradient rule nor a column-correlation rule separated it from the 14 good frames,
so no pixel rule is shipped: a rule that misses the very defect it exists for is worse than none.

Advisory by design: a failed check is a chip on the frame and a line in the pre-flight, never a block; the person can accept it. Brand- and category-agnostic: the only inputs are
the frame, the shot's own words and the film's own cast note.
"""
from __future__ import annotations

import base64
import json
import os
import re

ISSUE_IDS = ("collage", "extra-people", "missing-people", "anatomy", "text", "mismatch", "other")
MOTION_ISSUE_IDS = ISSUE_IDS + ("drift",)      # a look at SEVERAL frames of one clip may also name a change between them
ISSUE_LABELS = {"collage": "Pasted panels", "extra-people": "Extra person", "missing-people": "Person missing", "anatomy": "Anatomy",
                "text": "Unwanted text", "mismatch": "Not the shot", "other": "Other", "drift": "Changes between frames"}
MEDIA_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}


def model_name() -> str:
    return os.environ.get("FRAMECHECK_MODEL") or os.environ.get("GEN_MODEL", "claude-opus-4-8")


def vision_prompt(*, description: str, cast: str = "", wardrobe: str = "", pack_expected: bool = False, frames: int = 1) -> str:
    """The brief for the vision model: look at the frame and report only real defects against what the shot was meant to show. With `frames` > 1 the attached pictures are frames of ONE clip in
    time order and the brief is about what CHANGES between them (a limb that stretches, a pack that smears): the single-frame brief is returned byte for byte as before when `frames` is 1."""
    desc = " ".join(str(description or "").split())[:600]
    ctx = []
    if cast:
        ctx.append("WHO SHOULD BE IN THE FILM: " + " ".join(str(cast).split())[:700])
    if wardrobe:
        ctx.append("WARDROBE: " + " ".join(str(wardrobe).split())[:300])
    ctx.append("A product pack " + ("SHOULD" if pack_expected else "is not required to") + " appear in this frame.")
    if frames and int(frames) > 1:
        n = int(frames)
        return (
            f"You are the quality-control reviewer of a film. Look at the {n} attached frames. They are taken from ONE short video clip, in time order (early, middle and late), and the clip is about to be paid for in a cut. "
            "Report only REAL defects that would make a viewer notice something wrong, judged against what the shot was meant to show and ABOVE ALL against what CHANGES between the frames. Do not critique style, taste or composition.\n\n"
            f"WHAT THIS SHOT SHOULD SHOW: {desc}\n" + "\n".join(ctx) + "\n\n"
            "CHECK, in order:\n"
            "1. `drift` — something changes between the frames that should not: an arm, hand or leg that stretches, splits, merges, grows or vanishes; an arm or hand that crosses the face; a face that turns into someone else; "
            "the product pack changing shape, size, colour or label, smearing or going out of focus; an object that appears or disappears. Name the frames (early, middle, late).\n"
            "2. `anatomy` — in ANY frame, a body that is wrong: a wrong number of limbs, legs or arms of clearly different lengths, hands or feet with the wrong number of fingers or toes, a merged or distorted body, a broken face.\n"
            "3. `collage` — a frame is two or more separate pictures pasted together, or one part of it is at a clearly different scale or perspective from the rest.\n"
            "4. `extra-people` — a person who is not in the description or the cast.\n"
            "5. `missing-people` — someone the description requires is absent.\n"
            "6. `text` — readable words, captions, signs or a logo that the description did not ask for (the product's own printed label on a pack is allowed).\n"
            "7. `mismatch` — the clip shows something clearly different from the description.\n"
            "8. `other` — any other clear defect.\n\n"
            "Return ONLY JSON, no prose and no markdown: {\"verdict\":\"ok\" or \"check\",\"issues\":[{\"id\":\"drift\",\"note\":\"one plain sentence naming what is wrong, where and in which frame\"}],"
            "\"seen\":\"one sentence: what happens across the frames\"}. If the clip is fine, return {\"verdict\":\"ok\",\"issues\":[],\"seen\":\"...\"}. "
            "An issue you are not sure of is not an issue: leave it out.")
    return (
        "You are the quality-control reviewer of a film's storyboard. Look at the attached frame, which is about to be animated into a video clip at real cost. "
        "Report only REAL defects that would make a viewer notice something wrong, measured against what the shot was meant to show. Do not critique style, taste or composition.\n\n"
        f"WHAT THIS SHOT SHOULD SHOW: {desc}\n" + "\n".join(ctx) + "\n\n"
        "CHECK, in order:\n"
        "1. `collage` — the frame is two or more separate pictures pasted together (panels, a reference sheet, a contact sheet), or shows the same person twice at different scales in one frame, "
        "or one part of the frame is at a clearly different scale or perspective from the rest.\n"
        "2. `extra-people` — a person who is not in the description or the cast (a stranger, a duplicate of someone, a figure in the background that should not be there).\n"
        "3. `missing-people` — someone the description requires is absent.\n"
        "4. `anatomy` — a body that is wrong: a wrong number of limbs, legs or arms of clearly different lengths, hands or feet with the wrong number of fingers or toes, a merged or distorted body, a broken face.\n"
        "5. `text` — readable words, captions, signs or a logo that the description did not ask for (the product's own printed label on a pack is allowed).\n"
        "6. `mismatch` — the frame shows something clearly different from the description (another place, another action, the key object missing).\n"
        "7. `other` — any other clear defect (a floating object, an impossible join).\n\n"
        "Return ONLY JSON, no prose and no markdown: {\"verdict\":\"ok\" or \"check\",\"issues\":[{\"id\":\"anatomy\",\"note\":\"one plain sentence naming what is wrong and where\"}],"
        "\"seen\":\"one sentence: what the frame actually shows\"}. If the frame is fine, return {\"verdict\":\"ok\",\"issues\":[],\"seen\":\"...\"}. "
        "An issue you are not sure of is not an issue: leave it out.")


def parse(raw: str):
    """The JSON object a model reply holds, or None. Tolerates markdown fences and prose around the JSON."""
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


def clean_issues(raw, motion: bool = False) -> list[dict]:
    """Issues from a vision reply: only known ids (`drift` too when the look was at several frames), each with a note of real length, at most one per id, at most six."""
    known = MOTION_ISSUE_IDS if motion else ISSUE_IDS
    out, seen = [], set()
    for it in (raw.get("issues") if isinstance(raw, dict) and isinstance(raw.get("issues"), list) else []):
        if not isinstance(it, dict):
            continue
        iid = str(it.get("id") or "").strip().lower().replace("_", "-")
        note = " ".join(str(it.get("note") or "").split())[:240]
        if iid in known and iid not in seen and len(note) >= 8:
            seen.add(iid)
            out.append({"id": iid, "label": ISSUE_LABELS[iid], "verdict": "check", "note": note})
    return out[:6]


def result(raw, motion: bool = False) -> dict:
    """One result for a frame from the parsed reply: {verdict: ok|check, checks: [{id, label, verdict, note}], seen}. `check` exactly when at least one usable issue was named
    (a reply that says `check` but names nothing usable is `ok`: an unexplained flag is not shown to a person)."""
    checks = clean_issues(raw, motion)
    seen = " ".join(str((raw or {}).get("seen") or "").split())[:240] if isinstance(raw, dict) else ""
    return {"verdict": "check" if checks else "ok", "checks": checks, "seen": seen}


def media_type(path: str) -> str:
    return MEDIA_TYPES.get(os.path.splitext(str(path or ""))[1].lower(), "image/jpeg")


def look_many(images: list, mime: str, prompt: str, client=None) -> tuple[str, dict]:
    """The one model call for SEVERAL frames of one clip, in time order, plus the brief (P5.2). Same reply and usage shape as `look`."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    content = [{"type": "image", "source": {"type": "base64", "media_type": mime, "data": base64.b64encode(d).decode("ascii")}} for d in images]
    content.append({"type": "text", "text": prompt})
    resp = client.messages.create(model=model_name(), max_tokens=700, messages=[{"role": "user", "content": content}])
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    u = getattr(resp, "usage", None)
    return text, {"input_tokens": getattr(u, "input_tokens", 0) or 0, "output_tokens": getattr(u, "output_tokens", 0) or 0}


def look(data: bytes, mime: str, prompt: str, client=None) -> tuple[str, dict]:
    """The one model call: the frame plus the brief. Returns (reply text, {input_tokens, output_tokens}). `client` is injectable for tests; otherwise the Anthropic
    client is used (needs ANTHROPIC_API_KEY, which the route checks first)."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    resp = client.messages.create(model=model_name(), max_tokens=700, messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": mime, "data": base64.b64encode(data).decode("ascii")}},
        {"type": "text", "text": prompt}]}])
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    u = getattr(resp, "usage", None)
    return text, {"input_tokens": getattr(u, "input_tokens", 0) or 0, "output_tokens": getattr(u, "output_tokens", 0) or 0}
