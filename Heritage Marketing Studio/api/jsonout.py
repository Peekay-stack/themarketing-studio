"""jsonout.py — get the JSON object out of a model reply, whatever it is wrapped in.

Six generators each carried the same four lines:

    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    i = raw.find("{")
    if i > 0: raw = raw[i:]
    data = json.loads(raw)

That works most of the time, which is what made it dangerous. It fails when the model adds a closing
sentence after the object, when the fence is not at the start of a line, when it writes `Here is the
JSON:` and then the object, or when it emits two objects. The user sees *"Offer options for this layer"*
do nothing, once in every several tries, with no way to tell why — and a feature that works four times in
five is reported as broken, correctly.

`extract()` finds the outermost balanced `{…}` by scanning, so trailing prose, leading prose and stray
fences are all irrelevant. It understands strings and escapes, so a `}` inside a value does not end the
object early.

`ask_json()` adds the other half: one retry with a blunter instruction. Models comply on the second ask
far more often than a first failure suggests, and a silent single attempt turns a recoverable hiccup into
a dead button.
"""
from __future__ import annotations

import json
import os
import re

_FENCE = re.compile(r"```[a-zA-Z]*")


def extract(raw: str) -> tuple[dict | None, str]:
    """Pull the first complete JSON object out of `raw`. Returns (data, error)."""
    if not raw or not str(raw).strip():
        return None, "the model returned nothing"
    text = _FENCE.sub("", str(raw)).strip()

    start = text.find("{")
    if start < 0:
        return None, f"no JSON object in the reply (began {text[:60]!r})"

    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blob = text[start:i + 1]
                try:
                    return json.loads(blob), ""
                except ValueError as e:
                    # A balanced object that still will not parse is usually a trailing comma or a
                    # smart quote. Worth one repair pass before giving up on somebody's click.
                    repaired = re.sub(r",(\s*[}\]])", r"\1", blob)
                    repaired = (repaired.replace("“", '"').replace("”", '"')
                                        .replace("‘", "'").replace("’", "'"))
                    try:
                        return json.loads(repaired), ""
                    except ValueError:
                        return None, f"the JSON was malformed: {e}"
    return None, "the JSON object was never closed — the reply was probably cut short"


def ask_json(prompt: str, *, max_tokens: int = 4000, model: str | None = None,
             tries: int = 2) -> tuple[dict | None, str]:
    """Ask for JSON and insist on getting it. Returns (data, error).

    The retry is not politeness — it is the difference between a button that works and a button that
    works most of the time. The second attempt says plainly what went wrong with the first, because a
    model told "return only JSON" again behaves no differently from one told it once.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, "no ANTHROPIC_API_KEY"
    import anthropic
    client = anthropic.Anthropic()
    mdl = model or os.environ.get("GEN_MODEL", "claude-opus-4-8")
    last = ""
    for attempt in range(max(1, tries)):
        ask = prompt if attempt == 0 else (
            prompt + "\n\n---\nYour previous reply could not be parsed: " + last +
            "\nReturn ONLY the JSON object. No prose before it, no sentence after it, no code fence. "
            "Start your reply with { and end it with }.")
        try:
            msg = client.messages.create(model=mdl, max_tokens=max_tokens,
                                         messages=[{"role": "user", "content": ask}])
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"
        raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        data, err = extract(raw)
        if data is not None:
            return data, ""
        last = err
        if msg.stop_reason == "max_tokens":
            # Retrying an answer that was cut off just cuts it off again.
            return None, ("the reply was longer than the token budget and was cut off — ask for fewer "
                          "options, or shorten the note you added")
    return None, last
