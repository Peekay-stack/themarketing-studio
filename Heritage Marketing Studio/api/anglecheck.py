"""anglecheck.py -- did a coverage shot's frame actually change the angle, or is it a near-copy of the master?

Why: in the 27 Oct trial (VIDEO_COVERAGE_PLAN.md section 11) asking the image model for an "over-the-shoulder" or a "medium" shot of a
master frame twice returned the master almost unchanged. Measured on a 96x54 greyscale of each frame against its master:
near-copies correlated at 1.00 (mean difference about 3 of 255); every genuine angle, close-up, detail and wide, at 0.80 or lower.
So a single threshold separates them with room to spare, and the check is deterministic: no model, no network.

Advisory only, like packqa: it never blocks or changes a frame. It says "same" so the shot tile can offer a regenerate, "different" when
the angle changed, and "unclear" when it cannot tell (an unreadable image, or a flat frame with nothing to correlate).
"""
from __future__ import annotations

import io
import sys

SAME_AT = 0.95          # correlation at or above this => the frame is the master again (measured: copies 1.00, real angles <= 0.80)
SIZE = (96, 54)


def _gray(data: bytes):
    import numpy as np
    from PIL import Image
    img = Image.open(io.BytesIO(data))
    img.load()
    return np.asarray(img.convert("L").resize(SIZE)).astype("float32")


def correlation(a: bytes, b: bytes):
    """Pearson correlation of the two images' small greyscale versions, or None when either cannot be read or has no variation."""
    try:
        import numpy as np
        x, y = _gray(a), _gray(b)
        if x.std() < 1e-3 or y.std() < 1e-3:
            return None
        return float(((x - x.mean()) * (y - y.mean())).mean() / (x.std() * y.std()))
    except Exception as e:  # noqa: BLE001 -- QA must never break a render
        print(f"[anglecheck] could not compare: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return None


def check(frame: bytes, master: bytes) -> dict:
    """{verdict: same|different|unclear, correlation, note}."""
    c = correlation(frame, master)
    if c is None:
        return {"verdict": "unclear", "note": "the two frames could not be compared"}
    c = round(c, 3)
    if c >= SAME_AT:
        return {"verdict": "same", "correlation": c,
                "note": "This looks the same as shot 1 — the angle did not change."}
    return {"verdict": "different", "correlation": c, "note": "The angle differs from shot 1."}
