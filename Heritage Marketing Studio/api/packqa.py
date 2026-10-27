"""packqa.py -- does the product pack in a generated frame still have the proportions of the real pack?

Why this exists: on 27 Oct 2026 the same video prompt was run with and without "almost square, never stretched" and the
pouch in the clip kept the proportions of the STARTING FRAME either way (printed-panel aspect: real pack 1.30, scene B
frame 1.76, its clips 1.72-1.77; scene A frame 2.06, clips 2.16-2.25). The shape is decided at the frame stage, so this is
where it is checked.

How: find the pack's own colour from the reference photo (its dominant saturated hue, so any brand's pack works, not
just an orange one), take the largest blob of that colour in the frame, and compare the blob's long:short axis ratio
(principal axes) with the same measure on the reference. It is a MEASURE of the printed panel, not a verdict on the
whole frame: a hand over the pouch, a tilt or a second pack lowers the confidence, and then the answer is "unclear",
never a false "stretched". Pure numpy/scipy/PIL, no network.

Calibrated on the real Heritage pouch: reference 1.30; trial frames B 1.76, A 2.06 (see tools/test_packqa.py).
"""
from __future__ import annotations

import io
import sys

# How far from the reference ratio a frame may be before it is called out. The trial frames that visibly looked wrong
# were 1.35x and 1.58x the reference ratio; ordinary generation noise on a clean, front-facing pouch is a few percent.
STRETCH_AT = 1.25      # frame is this much longer-and-thinner than the real pack -> "elongated"
SQUASH_AT = 0.80       # ... or this much squarer -> "squashed"
MIN_FILL = 0.72        # blob area / area of its own principal-axes rectangle; a hand or a hole drops it below this
MIN_AREA = 0.004       # blob must cover at least this share of the frame to be measured at all
WORK = (1280, 720)


def _np():
    import numpy as np
    from PIL import Image
    import scipy.ndimage as ndi
    return np, Image, ndi


def _open(data: bytes):
    _, Image, _ = _np()
    img = Image.open(io.BytesIO(data))
    img.load()
    return img.convert("RGB")


def _hsv(np, rgb):
    a = rgb.astype("float32")
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = np.maximum(mx - mn, 1e-6)
    v = mx / 255.0
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0.0)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    return h, s, v


def colour_profile(ref_bytes: bytes) -> dict | None:
    """The pack's own colour, read from its reference photo: {hue, tol} in degrees, or None when the photo has no
    saturated colour to speak of (a white or grey pack cannot be separated from a kitchen by colour)."""
    try:
        np, _, _ = _np()
        img = _open(ref_bytes).resize((400, 300))
        h, s, v = _hsv(np, np.asarray(img))
        sel = (s > 0.45) & (v > 0.35)
        if sel.mean() < 0.02:
            return None
        hist, edges = np.histogram(h[sel], bins=72, range=(0, 360))
        # circular smoothing so a hue that straddles 0/360 (reds) is one peak, not two
        k = np.array([1, 2, 3, 2, 1], dtype="float32")
        sm = np.convolve(np.concatenate([hist[-2:], hist, hist[:2]]).astype("float32"), k, mode="valid")
        centre = (int(np.argmax(sm)) + 0.5) * 5.0
        return {"hue": float(centre), "tol": 14.0}
    except Exception as e:  # noqa: BLE001 -- QA must never break a render
        print(f"[packqa] colour profile failed: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return None


def _mask(np, ndi, rgb, prof):
    h, s, v = _hsv(np, rgb)
    dh = np.abs((h - prof["hue"] + 180.0) % 360.0 - 180.0)
    m = (dh <= prof["tol"]) & (s > 0.55) & (v > 0.45)
    return ndi.binary_closing(m, iterations=3)


def measure(img_bytes: bytes, prof: dict) -> dict:
    """{found, aspect, fill, area} for the largest blob of the pack colour. aspect = long:short of the blob's
    principal axes (sqrt of the eigenvalue ratio), so a tilted pouch reads the same as an upright one."""
    try:
        np, _, ndi = _np()
        img = _open(img_bytes)
        img.thumbnail(WORK)          # scale DOWN keeping the aspect ratio: a resize to a fixed box would stretch a pack photo
        rgb = np.asarray(img)
        m = _mask(np, ndi, rgb, prof)
        lab, n = ndi.label(m)
        if n == 0:
            return {"found": False}
        sizes = ndi.sum(m, lab, range(1, n + 1))
        k = int(np.argmax(sizes)) + 1
        mk = lab == k
        area = float(mk.sum())
        ys, xs = np.nonzero(mk)
        if len(xs) < 50:
            return {"found": False}
        cov = np.cov(np.vstack([xs, ys]))
        ev = np.sort(np.linalg.eigvalsh(cov))
        if ev[0] <= 1e-6:
            return {"found": False}
        aspect = float(np.sqrt(ev[1] / ev[0]))
        rect_area = 12.0 * float(np.sqrt(ev[0] * ev[1]))      # area of a uniform rectangle with these principal variances
        h, w = rgb.shape[0], rgb.shape[1]
        mx, my = max(3, int(0.025 * w)), max(3, int(0.025 * h))     # a pack this near the edge is almost certainly cut by it
        clipped = bool(xs.min() <= mx or ys.min() <= my or xs.max() >= w - 1 - mx or ys.max() >= h - 1 - my)
        return {"found": True, "aspect": round(aspect, 3), "fill": round(min(1.0, area / rect_area), 3),
                "area": round(area / float(h * w), 4), "clipped": clipped}
    except Exception as e:  # noqa: BLE001
        print(f"[packqa] measure failed: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return {"found": False}


def check(frame_bytes: bytes, ref_bytes: bytes) -> dict:
    """Compare the pack in a generated frame with the real pack photo.

    Returns {verdict, ref_aspect, frame_aspect, ratio, fill, note}. verdict is one of:
      ok         the printed panel has the real pack's proportions (within tolerance)
      elongated  longer and thinner than the real pack (the failure seen on 27 Oct)
      squashed   squarer than the real pack
      unclear    the pack could not be measured with confidence (hand over it, tilted, no colour to key on, too small)
    A frame is NEVER blocked or changed by this; the caller reports it and the person decides.
    """
    prof = colour_profile(ref_bytes)
    if not prof:
        return {"verdict": "unclear", "note": "the pack photo has no distinct colour to measure by"}
    ref = measure(ref_bytes, prof)
    if not ref.get("found") or ref.get("fill", 0) < MIN_FILL:
        return {"verdict": "unclear", "note": "the pack photo could not be measured cleanly"}
    fr = measure(frame_bytes, prof)
    base = {"ref_aspect": ref["aspect"]}
    if not fr.get("found") or fr.get("area", 0) < MIN_AREA:
        return {**base, "verdict": "unclear", "note": "no clear pack in this frame to measure"}
    ratio = round(fr["aspect"] / ref["aspect"], 3)
    out = {**base, "frame_aspect": fr["aspect"], "ratio": ratio, "fill": fr["fill"]}
    if fr.get("clipped"):
        return {**out, "verdict": "unclear", "note": "the pack is cut off by the edge of the frame, so it cannot be measured"}
    if fr["fill"] < MIN_FILL:
        return {**out, "verdict": "unclear", "note": "the pack is partly hidden or tilted, so it cannot be measured with confidence"}
    if ratio >= STRETCH_AT:
        pct = int(round((ratio - 1.0) * 100))
        return {**out, "verdict": "elongated",
                "note": f"the pack looks about {pct}% longer and thinner than the real one"}
    if ratio <= SQUASH_AT:
        pct = int(round((1.0 / ratio - 1.0) * 100))
        return {**out, "verdict": "squashed",
                "note": f"the pack looks about {pct}% squarer than the real one"}
    return {**out, "verdict": "ok", "note": "the pack's proportions match the real pack"}
