"""keyvisual.py — the assembly step POSM never had.

`posm.py` was already rewritten once around a correct idea: generate isolated asset layers (a hero
cut-out on plain white, a pack photograph, the real logo), because a single image-model call asked to
produce a whole finished poster in one shot reliably fails — it cannot set real type, it redraws the
pack slightly wrong every time, and its own attempt at an environment fights the isolation the cut-out
needs (documented in `posm_skill/references/failures.md`). `/posm-image`'s own response already says so
in words: *"This is the hero cut-out, not the finished piece: mask it out of the white and place it on
the flat brand-colour field with the pack, the type and the brand block."*

Nothing ever did that masking and placing. This module is that step — a real compositor, not another
prompt. It takes the layers that already exist (a hero cut-out, a signed-off pack shot, the brand's
logo, a headline, a background) and assembles them onto one canvas with Pillow: real pixels moved and
drawn, not asked for.

**Two backgrounds are both real options, not one "correct" one.** A flat brand-colour field is the
category default this codebase's own research documents (Dabur, Surf Excel, Nivea, Motherdairy — real
Indian FMCG POS, cited in the skill). A generated photographic backdrop (a green backdrop, a home
kitchen) is also a real creative need — some routes are staged in an environment, not on a field. The
past failure this module exists to avoid was never "a photo background is wrong" — it was asking ONE
model call to hold an isolated subject AND an environment AND type AND a logo simultaneously, which is
exactly what generating the backdrop as its own separate, subject-free image (`backdrop_prompt`, in
`posm.py`) and compositing it here in code avoids. The hero is still generated in total isolation —
now on the mid-grey `posm.CUTOUT_BACKDROP` rather than white, because half this brand's subjects ARE
white and a matte needs a backdrop the subject does not contain; only the assembly happens differently
depending on which field is chosen.

**Text is drawn, never asked for.** `posm.cap_fraction()` already computes the real minimum cap height
for a format from trade viewing-distance practice — this module turns that fraction into an actual
rendered headline, sized and positioned in code, not hoped for from a model.

**What this does NOT yet do.** `assets/fonts/` bundles Noto Sans Bold (Latin, Devanagari, Telugu,
Kannada, Tamil) so headline art is always drawn in a real bold face with the right script's glyphs —
see `_font`/`_dominant_script_font` — but there is still no BRAND-specific display face anywhere in this
codebase; `brandprofile.py`'s own `fonts` field docstring still says so ("this studio does not host font
files"), and `KEYVISUAL_FONT_PATH` is an env-var override with nowhere in the product that sets it. The
natural next step is a `font` kind in `library.py`, mirroring `pack`/`logo`, so a brand can upload and
sign off its own Latin display face; the bundled Noto set would stay as the default and as the only
option for scripts a brand font doesn't cover. Pack and logo compositing here also do not perform real
background segmentation (no such model is a dependency) — the pack is placed as its own small card
rather than silhouette-cut from its source photo, which is a conservative, reliable choice over a bad
auto-cutout.
"""
from __future__ import annotations

import io
import os
import re
import uuid
from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageMath

import gemini
import library
import posm
import tenancy

MEDIA_DIR = tenancy.asset_dir("media")

# Which way the light comes from, as a signed horizontal fraction: -1 lights from the right (shadow
# falls left), +1 from the left (shadow falls right). ONE value for the whole studio on purpose. A kit
# is eleven pieces of the same campaign seen together on one shelf, and a shadow whose angle changes
# between them reads as eleven separate jobs — the same coherence argument the skill's governing rule
# makes about the key visual itself. `posm.cutout_prompt` asks for "directional studio lighting"
# without naming a side, so this is the studio's house angle rather than a measurement of any one
# render; light from the upper left is the convention almost every product shot and every one of the
# skill's cited exhibits follows.
LIGHT_DIR = 1.0

# A photographic backdrop is generated in total isolation from the hero, same discipline as the hero
# cut-out itself — no subject, no product, no people, nothing this module will paste over anyway.
def backdrop_prompt(brief: str, style_note: str = "") -> str:
    """A pure environment, meant to receive a cut-out pasted on top of it later.

    Mirrors `posm.cutout_prompt`'s own reasoning in the opposite direction: that function isolates a
    SUBJECT from any environment; this isolates an ENVIRONMENT from any subject. Asking one model call
    for both at once is the failure this whole module exists to avoid.
    """
    brief = str(brief or "").strip().rstrip(".")
    return " ".join(p for p in [
        f"{brief}." if brief else "A plain studio backdrop.",
        "An empty environment or backdrop with NOTHING and NOBODY in it — no person, no product, no "
        "pack, no hands, no animals, no text. Photographic, in sharp focus corner to corner so a "
        "subject can be pasted onto it convincingly. Even, soft lighting with no single hard shadow "
        "that a pasted subject would visibly lack.",
        style_note.strip(),
        "Absolutely no text, lettering, logos or watermarks anywhere in the image.",
    ] if p)


def _http_get(url: str) -> bytes | None:
    try:
        import httpx
        r = httpx.get(url, timeout=20.0, follow_redirects=True)
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return None


def _resolve_bytes(ref: str) -> bytes | None:
    """A library id, a `/library-file/...`/`/media/...`/`/brand-logo/...` URL, or a genuine external
    URL (fal's own CDN) -> raw bytes. One resolver so every caller in this module means the same thing
    by 'a reference'."""
    ref = str(ref or "").strip()
    if not ref:
        return None
    item = library.get(ref)
    if item:
        p = library.local_path(item["file"])
        if p and os.path.exists(p):
            with open(p, "rb") as fh:
                return fh.read()
    if "/library-file/" in ref:
        p = library.local_path(ref.split("/library-file/", 1)[1])
        if p and os.path.exists(p):
            with open(p, "rb") as fh:
                return fh.read()
    if ref.startswith("/brand-logo/"):
        brand_id = ref.rsplit("/", 1)[1]
        d = tenancy.dir("brands")
        for name in os.listdir(d) if os.path.isdir(d) else []:
            if name.startswith(brand_id + "-logo"):
                with open(os.path.join(d, name), "rb") as fh:
                    return fh.read()
        return None
    local = gemini.local_path(ref)
    if local and os.path.exists(local):
        with open(local, "rb") as fh:
            return fh.read()
    if ref.startswith("http://") or ref.startswith("https://"):
        return _http_get(ref)
    return None


def _open_image(ref: str) -> Image.Image | None:
    data = _resolve_bytes(ref)
    if not data:
        return None
    if data[:5] == b"<?xml" or data.lstrip()[:4] == b"<svg":
        try:
            import cairosvg
            data = cairosvg.svg2png(bytestring=data, output_width=800)
        except Exception:
            return None
    try:
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        return None


def looks_like_cutout(img: Image.Image, tol: int = 22) -> bool:
    """Does this image sit on a plain studio backdrop that should be keyed out?

    **Measured from the image, never inferred from how it was generated.** This module used to decide
    by the caller's `mode` flag — `cutout` keys, `scene` does not — and that produced the worst piece
    this tool has made: a studio shot of a pack and a glass, generated in `scene` mode on a seamless
    grey sweep, was placed on the poster UNKEYED, so the backdrop arrived as a grey rectangle sitting in
    the middle of the artwork. The label was right about the generation call and wrong about the
    picture, which is the whole problem with classifying by provenance.

    A photograph of a room has a busy, varied border. A subject on a seamless sweep has a border that is
    all one colour. That difference is directly measurable, so it is measured: sample the frame edge,
    take the median as the candidate plate, and ask what share of the border sits within `tol` of it.
    Above ~88% there is a plate to remove; below it, the picture is its own environment and keying it
    would punch holes in a real scene.
    """
    small = img.convert("RGB")
    small.thumbnail((160, 160))
    sp = small.load()
    sw, sh = small.size
    if sw < 3 or sh < 3:
        return False
    border = [sp[x, y] for x in range(sw) for y in (0, sh - 1)] + \
             [sp[x, y] for y in range(sh) for x in (0, sw - 1)]
    if not border:
        return False
    plate = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    near = sum(1 for c in border if all(abs(c[i] - plate[i]) <= tol for i in range(3)))
    return (near / len(border)) >= 0.88


def _decontaminate(img: Image.Image, plate: tuple[int, int, int]) -> Image.Image:
    """Remove the backdrop's colour from partially-transparent edge pixels.

    Adobe ships this as "Remove White Matte" / "Color Decontaminate" because it is universal, not a
    fluke: an anti-aliased edge pixel is a MIX of subject and backdrop, so it literally contains the
    backdrop's colour. Composite it onto a different field and that colour is still there — a pale halo
    all the way round a subject cut from white, which is what every piece this module made had.

    The fix is algebra, not a filter. The pixel is `C = a·F + (1-a)·B` for backdrop `B` and true
    subject colour `F`; solve for `F = (C - (1-a)·B) / a`. Only edge pixels have `a < 1`, so only they
    change, and fully-opaque interior pixels are untouched.

    Done in `ImageMath` per band because there is no numpy here and a Python loop over a 3500px poster
    is not viable. `a` is floored to avoid dividing by nearly nothing on the outermost pixels, where the
    recovered colour would be pure noise amplified a hundredfold.
    """
    # Pillow 10.3 renamed `ImageMath.eval` to `unsafe_eval`; both exist across the versions this app
    # could be installed against, so bind whichever is present rather than pinning a Pillow release.
    _eval = getattr(ImageMath, "unsafe_eval", None) or ImageMath.eval
    r, g, b, a = img.split()
    out = []
    for ch, bg in zip((r, g, b), plate):
        out.append(_eval(
            # All terms are in 0–255 space, so with `a` also 0–255 the solve is
            #   F = (255·(C − B) + a·B) / a
            # which collapses to F = C at a = 255 (opaque pixels untouched, by construction).
            # The image operand has to come first in min/max — ImageMath dispatches on the left side.
            "convert(min(max((255.0*(c - bg) + af*bg) / af, 0), 255), 'L')",
            c=ch.convert("F"),
            # Floor alpha at ~12%: below that the pixel is almost entirely backdrop and the recovered
            # colour is noise multiplied by a large number.
            af=a.point(lambda v: max(v, 31)).convert("F"), bg=float(bg)))
    return Image.merge("RGBA", (out[0], out[1], out[2], a))


def _key_backdrop_to_alpha(img: Image.Image, tolerance: int = 26,
                           defringe: int = 1) -> Image.Image:
    """Key the studio backdrop out of a cut-out — whatever colour that backdrop actually is.

    Was `_key_white_to_alpha`, and the rename is the point: keying *white* is a different operation
    that only works when the subject contains no white. It punched holes through everything white a
    subject legitimately owns — a glass of milk, a splash, a white kurta, a pack's white panel, and the
    white inside a logo's own wordmark. Now the backdrop colour is MEASURED from the frame border, so
    the same code keys the mid-grey `posm.CUTOUT_BACKDROP` asks for today, a legacy white plate, or a
    chroma green, without being told which.

    Three things happen, and each maps to something a retoucher does by hand:

    1. **Border-connected flood fill** — a backdrop is backdrop-coloured AND reachable from the frame
       edge. This is the magic wand, not a colour-range select, and it is what protects interior
       colour that happens to match.
    2. **Defringe (contract)** — the outermost ring of the matte is always a blend of subject and
       backdrop. Eroding the alpha by a pixel bites that ring off. Adobe calls it Defringe; the effect
       at poster scale is a hairline nobody sees, versus a halo everybody does.
    3. **Decontaminate** — the remaining partial pixels still carry backdrop colour, so it is solved
       out of them algebraically (`_decontaminate`).

    Tolerance is a distance in RGB from the measured plate, not a brightness threshold: a grey or green
    backdrop has no meaningful "brightness cut", and distance is what actually separates them.
    """
    img = img.convert("RGBA")
    w, h = img.size
    if w < 2 or h < 2:
        return img

    scale = min(1.0, 420 / max(w, h))
    sw, sh = max(2, int(w * scale)), max(2, int(h * scale))
    small = img.convert("RGB").resize((sw, sh), Image.BILINEAR)
    sp = small.load()

    # The plate is measured, never assumed. Median of the border, per channel — robust to a subject
    # that runs off one edge, and it makes this work for any backdrop colour rather than only white.
    border = [sp[x, y] for x in range(sw) for y in (0, sh - 1)] + \
             [sp[x, y] for y in range(sh) for x in (0, sw - 1)]
    if not border:
        return img
    plate = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))

    # Tolerance adapts to how clean this particular plate is, rather than being one number for every
    # image. A generated JPEG backdrop is noisy and needs slack; a vector logo exported on flat white
    # has none, and giving it slack is destructive — a fixed ±26 ate the white ring inside the Heritage
    # oval, because at that width the ring counted as "plate" and the fill reached it through the gaps
    # between the swoosh and the oval. Measured from the border's own spread: the 90th percentile of
    # each pixel's deviation from the median plate, plus a small margin.
    devs = sorted(max(abs(c[i] - plate[i]) for i in range(3)) for c in border)
    spread = devs[int(len(devs) * 0.90)] if devs else 0
    tol = max(6, min(int(tolerance), spread + 6))

    def _is_plate(x: int, y: int) -> bool:
        r, g, b = sp[x, y]
        return (abs(r - plate[0]) <= tol and abs(g - plate[1]) <= tol
                and abs(b - plate[2]) <= tol)

    seen = bytearray(sw * sh)
    dq = deque()
    for x in range(sw):
        for y in (0, sh - 1):
            if not seen[y * sw + x] and _is_plate(x, y):
                seen[y * sw + x] = 1
                dq.append((x, y))
    for y in range(sh):
        for x in (0, sw - 1):
            if not seen[y * sw + x] and _is_plate(x, y):
                seen[y * sw + x] = 1
                dq.append((x, y))
    while dq:
        x, y = dq.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < sw and 0 <= ny < sh and not seen[ny * sw + nx] and _is_plate(nx, ny):
                seen[ny * sw + nx] = 1
                dq.append((nx, ny))

    mask = Image.frombytes("L", (sw, sh), bytes(255 if v else 0 for v in seen))
    mask = mask.resize((w, h), Image.BILINEAR)
    keep = mask.point(lambda v: 255 - v)
    if defringe > 0:
        # Contract the matte to drop the contaminated outer ring, then re-soften the new edge so the
        # erosion itself does not become a hard jagged line.
        k = defringe * 2 + 1
        keep = keep.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.GaussianBlur(defringe * 0.7))
    img.putalpha(ImageChops.multiply(img.getchannel("A"), keep))
    return _decontaminate(img, plate)


def _contain(img: Image.Image, w: int, h: int) -> Image.Image:
    """Resize to fit inside (w, h), preserving aspect ratio. Never upscales past the box either."""
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        return img
    scale = min(w / iw, h / ih)
    return img.resize((max(1, int(iw * scale)), max(1, int(ih * scale))), Image.LANCZOS)


def _cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Resize to fill (w, h), preserving aspect ratio, and centre-crop the overflow."""
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        return img
    scale = max(w / iw, h / ih)
    rw, rh = max(1, int(iw * scale)), max(1, int(ih * scale))
    img = img.resize((rw, rh), Image.LANCZOS)
    x0, y0 = (rw - w) // 2, (rh - h) // 2
    return img.crop((x0, y0, x0 + w, y0 + h))


_FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

# One bold face per script this brand's own market actually uses (the brief names South India —
# Telangana, Andhra Pradesh — as the strongest market, so Telugu is not an edge case here), all from the
# same Noto Sans family so a bilingual headline reads as one consistent design rather than two typefaces
# stapled together. Each file is a variable font; `_font` selects its heaviest named instance rather than
# needing a separate static-weight file per script. Devanagari/Tamil/Telugu/Kannada checked in that order
# only to keep the range table below readable — `_dominant_script_font` scores every character, order
# doesn't bias the result.
_SCRIPT_RANGES = [
    ("devanagari", 0x0900, 0x097F, "NotoSansDevanagari.ttf"),
    ("tamil",      0x0B80, 0x0BFF, "NotoSansTamil.ttf"),
    ("telugu",     0x0C00, 0x0C7F, "NotoSansTelugu.ttf"),
    ("kannada",    0x0C80, 0x0CFF, "NotoSansKannada.ttf"),
]
_LATIN_FONT_FILE = "NotoSans.ttf"


def _dominant_script_font(text: str) -> str:
    """Which bundled face covers most of this text, by counting each script's own Unicode block.

    A headline is drawn in ONE face, not per-character — mixing faces mid-line is a bigger legibility
    problem than the rare embedded Latin brand name inside an Indian-script line, and every face here
    already carries basic Latin/digits/punctuation as a Noto family guarantee. Ties, pure-Latin and
    pure-punctuation text all fall back to the Latin face.
    """
    counts: dict[str, int] = {}
    for ch in text:
        cp = ord(ch)
        for _name, lo, hi, fname in _SCRIPT_RANGES:
            if lo <= cp <= hi:
                counts[fname] = counts.get(fname, 0) + 1
                break
    return max(counts, key=counts.get) if counts else _LATIN_FONT_FILE


_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

# Override point for a real brand display face once one is uploaded (see the module docstring) — Latin
# only: a brand's own Latin logotype face has no reason to carry Devanagari/Telugu/Kannada/Tamil glyphs,
# which is exactly what the bundled Noto set exists to cover instead.
BRAND_FONT_PATH = os.environ.get("KEYVISUAL_FONT_PATH", "")


def _font(size: int, text: str = "") -> ImageFont.FreeTypeFont:
    """A bold, script-correct face for `text`, at `size` pixels.

    Headline art has to be bold and legible at a distance, not merely present — Pillow's own bundled
    default face is a thin utility face, never meant for display type, which is what made every POS
    headline this module drew before read as a caption rather than art. Every bundled face is set to its
    heaviest named instance ('Black', falling back to 'Bold') rather than drawn at its default Regular
    weight.
    """
    size = max(10, int(size))
    fname = _dominant_script_font(text)
    path = (BRAND_FONT_PATH if fname == _LATIN_FONT_FILE and BRAND_FONT_PATH
            and os.path.exists(BRAND_FONT_PATH) else os.path.join(_FONT_DIR, fname))
    key = (path, size)
    if key not in _FONT_CACHE:
        try:
            font = ImageFont.truetype(path, size)
            get_names = getattr(font, "get_variation_names", None)
            names = {n.decode() if isinstance(n, bytes) else n for n in get_names()} if get_names else set()
            for weight in ("Black", "Bold"):
                if weight in names:
                    font.set_variation_by_name(weight)
                    break
        except OSError:
            # A brand override path that doesn't resolve, or a non-variable font — either way this
            # falls back to the bundled Latin face rather than Pillow's thin default, since that default
            # is the exact problem this function exists to get away from.
            font = ImageFont.truetype(os.path.join(_FONT_DIR, _LATIN_FONT_FILE), size) \
                if path != os.path.join(_FONT_DIR, _LATIN_FONT_FILE) else ImageFont.load_default(size=size)
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _rel_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance — gamma-corrected, unlike the plain weighted average below."""
    def _lin(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (_lin(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """WCAG contrast ratio between two colours, 1.0 (identical) to 21.0 (black on white).

    The skill asks type to "contrast perfectly against the background" and gives no number, so this
    module was choosing ink with a coin-flip on a crude luminance average — which is how a headline
    ended up white over a bright sky. WCAG's floor for LARGE text is **3:1** (4.5:1 for body), and a POS
    headline is large text by any definition. Having the number means the choice can be made by
    measurement and, more importantly, that a field which cannot carry either ink can be *reported*
    rather than silently shipped.
    """
    l1, l2 = _rel_luminance(a), _rel_luminance(b)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def _tracked_width(draw: ImageDraw.ImageDraw, text: str, font, track: float) -> float:
    if not text:
        return 0.0
    return draw.textlength(text, font=font) + track * (len(text) - 1)


def _draw_tracked(draw: ImageDraw.ImageDraw, xy: tuple, text: str, font, fill, track: float) -> None:
    """Draw text with letter-spacing applied, without throwing the font's kerning away.

    Display type "frequently benefits from slight negative tracking to counter the looseness that
    creeps in at large sizes" — and a POS headline runs 110–170px here, which is squarely display size.
    Pillow has no tracking parameter, and the obvious workaround (draw each glyph at its own advance)
    silently discards kerning, which at this size is a worse defect than the looseness being fixed.

    So each glyph is positioned at the measured advance of the string PREFIX before it — which is the
    kerned advance, since `textlength` applies the font's kern table — plus the accumulated tracking.
    Kerning is preserved and tracking is applied on top of it.
    """
    if not text:
        return
    x, y = xy
    if not track:
        draw.text((x, y), text, font=font, fill=fill)
        return
    for i, ch in enumerate(text):
        draw.text((x + draw.textlength(text[:i], font=font) + i * track, y), ch, font=font, fill=fill)


def _wrap_tracked(draw: ImageDraw.ImageDraw, text: str, font, max_w: int, track: float) -> list[str]:
    """`_wrap`, but measuring the width the text will actually be DRAWN at.

    Wrapping against the untracked width and then drawing tracked is how a line that "fits" comes out
    a few pixels over the zone — negative tracking pulls it in, positive pushes it out, and either way
    the measurement has to match the drawing.
    """
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if _tracked_width(draw, trial, font, track) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (c / 255.0 for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


_HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")


def _hex_to_rgb(hex_str: str, default=(230, 227, 218)) -> tuple[int, int, int]:
    m = _HEX.match(str(hex_str or "").strip())
    if not m:
        return default
    h = m.group(1)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _avg_rgb(img: Image.Image, box: tuple) -> tuple[int, int, int]:
    """The real mean colour of a region — measured, not assumed.

    Replaces a hardcoded `(128, 128, 128)` "unknown average" that made every headline over a photographic
    field come out white: mid-grey scores 0.502 on `_luminance`, the contrast test asks for > 0.55, so the
    guess failed the test every single time and picked the light colour on every backdrop, bright or dark.
    """
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return (128, 128, 128)
    crop = img.crop((x0, y0, x1, y1)).convert("RGB")
    crop.thumbnail((32, 32))          # sampling, not averaging every pixel of a 1600px canvas
    px = list(crop.getdata()) or [(128, 128, 128)]
    n = len(px)
    return (sum(p[0] for p in px) // n, sum(p[1] for p in px) // n, sum(p[2] for p in px) // n)


def _shade(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Darken (<1) or lighten (>1) a colour, staying in gamut. Used for the base band and devices, which
    are tones of the field rather than new colours — a POS piece is built from a brand's own palette."""
    if factor <= 1:
        return tuple(max(0, min(255, int(c * factor))) for c in rgb)
    return tuple(max(0, min(255, int(c + (255 - c) * (factor - 1)))) for c in rgb)


def _split_emphasis(line: str, emphasis: str = "") -> tuple[str, str, str]:
    """Break a headline into (before, EMPHASIS, after) for a multi-weight setting.

    `references/key-visual.md` lists this first in its type-device vocabulary and states the rule flatly:
    *"Multi-weight headline. One word or phrase very large, the rest smaller. **Never one uniform size.**"*
    The compositor set one uniform size, which is why a correctly-worded line still read as a caption.

    An explicit `emphasis` from the route always wins. Otherwise: the clause before a comma carries the
    idea ("Real strength, every day." -> "Real strength"), and failing that the longest word does
    ("The Heritage Headstart" -> "Headstart"; "Strength you can pour every morning" -> "Strength").
    """
    line = (line or "").strip()
    if not line:
        return "", "", ""
    if emphasis:
        low, elow = line.lower(), emphasis.strip().lower()
        if elow and elow in low:
            i = low.index(elow)
            return line[:i].strip(), line[i:i + len(elow)].strip(), line[i + len(elow):].strip()
    if "," in line:
        head, rest = line.split(",", 1)
        if head.strip():
            return "", head.strip(), rest.strip()
    words = [w for w in line.split() if w.strip(".,!?;:")]
    if len(words) <= 1:
        return "", line, ""
    best = max(words, key=lambda w: len(w.strip(".,!?;:")))
    i = line.index(best)
    return line[:i].strip(), best.strip(), line[i + len(best):].strip()


def squint(canvas: Image.Image, zones: dict, field_rgb: tuple) -> dict:
    """The two-metre test, performed rather than asked for.

    The skill's own final checklist says: *"Squint at it as a thumbnail. One shape, one contrast, the
    brand. If it becomes mush, it fails at two metres too."* That is the single best check in the whole
    document and it has always been an instruction to a human who is not in the loop — so a piece could
    fail it and still ship. This runs it: shrink hard, blur away every detail, and measure what is left.

    Two numbers come out. **Contrast index** is the spread of tone once detail is gone — a piece that
    flattens toward one value is the "mush" the checklist names. **Dominance** is the visual mass of
    each zone (how far it departs from the field colour), which answers the question a squint is
    actually for: does one thing lead, or are two things competing? A poster where the hero and the
    headline carry equal mass has no hierarchy, whatever either looks like close up.

    Reported, never enforced. A piece that reads as mush at thumbnail size is usually wrong, but "one
    dominant element" is a judgement about intent — a range array is *supposed* to be a rhythm of equal
    packs — and this module does not get to overrule the route on that.
    """
    small = canvas.convert("L").resize((48, max(1, round(48 * canvas.height / canvas.width))),
                                       Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.2))
    px = list(small.getdata())
    n = len(px) or 1
    mean = sum(px) / n
    contrast_index = (sum((p - mean) ** 2 for p in px) / n) ** 0.5

    field_l = _luminance(field_rgb) * 255
    sx, sy = small.width / canvas.width, small.height / canvas.height
    masses = {}
    for name, box in zones.items():
        if not box:
            continue
        x0, y0, x1, y1 = (round(box[0] * sx), round(box[1] * sy), round(box[2] * sx), round(box[3] * sy))
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(small.width, x1), min(small.height, y1)
        if x1 <= x0 or y1 <= y0:
            continue
        vals = [px[yy * small.width + xx] for yy in range(y0, y1) for xx in range(x0, x1)]
        masses[name] = round(sum(abs(v - field_l) for v in vals) / max(1, len(vals)), 1)

    order = sorted(masses.items(), key=lambda kv: -kv[1])
    lead, second = (order[0] if order else ("", 0.0)), (order[1] if len(order) > 1 else ("", 0.0))
    ratio = (lead[1] / second[1]) if second[1] > 0.5 else None
    notes = []
    if contrast_index < 18:
        notes.append("Reads as mush at thumbnail size — there is no single shape or contrast carrying "
                     "it, so it will not survive two metres either.")
    if ratio is not None and ratio < 1.25:
        notes.append(f"No clear lead: {lead[0]} and {second[0]} carry almost the same visual weight "
                     f"({lead[1]} vs {second[1]}). One of them should dominate.")
    return {"contrast_index": round(contrast_index, 1), "mass": masses,
            "dominant": lead[0], "dominance_ratio": round(ratio, 2) if ratio else None,
            "notes": notes, "passes": not notes}


def palette_from(ref: str, n: int = 5) -> list[dict]:
    """The brand's real colours, measured off a signed-off asset instead of guessed from a name.

    `brandprofile`'s own `palette` docstring makes the case ("a colour NAME on its own is not enough —
    'Ghee gold' tells a model nothing and renders no swatch"), and for this brand the field is empty
    while `colours` holds three names. The pack shot is the one place the real colours provably exist:
    it is signed-off ground truth, and it is what the shopper matches the piece against on shelf.

    Quantised rather than clustered — `Image.quantize` is doing k-means-ish work in C, and the ranking
    that matters is "how much of the pack is this colour", which is exactly what the palette counts give.
    Near-white and near-black are dropped: they are the photographer's backdrop and the type, not brand
    colours, and offering them as swatches is how a field ends up white.
    """
    img = _open_image(ref)
    if not img:
        return []
    rgb = Image.new("RGB", img.size, (255, 255, 255))
    rgb.paste(img, mask=img.getchannel("A"))
    rgb.thumbnail((220, 220))
    q = rgb.quantize(colors=max(4, n * 4), method=Image.MEDIANCUT)
    pal = q.getpalette() or []
    counts = sorted(q.getcolors() or [], key=lambda c: -c[0])
    out, seen = [], []
    total = sum(c for c, _i in counts) or 1
    for count, idx in counts:
        r, g, b = pal[idx * 3:idx * 3 + 3]
        mx, mn = max(r, g, b), min(r, g, b)
        if mn >= 232 or mx <= 26:                  # the backdrop and the ink, not the brand
            continue
        if mx - mn < 18:                           # no hue at all — a grey, at any brightness. A brand
            continue                               # colour has a hue; paper and shadow do not.
        if any(abs(r - pr) + abs(g - pg) + abs(b - pb) < 60 for pr, pg, pb in seen):
            continue                               # near-duplicates of a colour already taken
        seen.append((r, g, b))
        out.append({"hex": f"#{r:02X}{g:02X}{b:02X}", "rgb": [r, g, b],
                    "share": round(100.0 * count / total, 1),
                    "luminance": round(_luminance((r, g, b)), 3)})
        if len(out) >= n:
            break
    return out


def canvas_px(fmt: str, long_edge: int = 1600, dpi: int = 0) -> tuple[int, int]:
    """Working pixel size for a format, at the format's real aspect ratio.

    Two modes. Without `dpi` this is a PREVIEW: `long_edge` bounds it to something a browser and this
    module can move around quickly. With `dpi` it is the real TRIM SIZE at that resolution, computed
    from the format's own millimetres — 297×420mm at 300dpi is 3508×4961px, which is the artwork a
    printer actually needs and which this module could not produce until now.

    A format with no `mm` on file cannot have a print size, because its dimensions are the thing that
    "must be measured, never assumed" (`posm.adaptation`'s own `missing` list says so). Asking for dpi
    on one of those raises rather than inventing a sheet size.
    """
    row = posm.FORMATS.get(fmt) or {}
    mm = row.get("mm")
    if dpi:
        if not mm:
            raise ValueError(
                f"{row.get('label', fmt)!r} has no real dimensions on file, so there is no print size to "
                f"render. This format has to be measured on site — ask the vendor or the store for the "
                f"bay dimensions, then set them before exporting artwork.")
        return (max(1, round(mm[0] / 25.4 * dpi)), max(1, round(mm[1] / 25.4 * dpi)))
    if mm:
        rw, rh = mm
    else:
        rw, rh = posm.ratio_num(str(row.get("ratio") or posm.MASTER_RATIO)), 1.0
        rw, rh = (rw or 0.75), 1.0
    if rw >= rh:
        return long_edge, max(1, round(long_edge * rh / rw))
    return max(1, round(long_edge * rw / rh)), long_edge


def assemble(*, hero_url: str, fmt: str, headline: str = "",
             type_position: str = "type-locked-base", backdrop_url: str = "",
             field_hex: str = "", pack_url: str = "", logo_url: str = "",
             hero_is_cutout: bool | None = None, headline_emphasis: str = "", device: str = "rule",
             support_line: str = "", mandatories: tuple = (), field_hex_2: str = "",
             type_pct: float | None = None, dpi: int = 0, report: dict | None = None) -> bytes:
    """Layer everything onto one canvas and return PNG bytes — the nine-layer stack
    `posm_skill/SKILL.md` describes, not a photograph with words on top.

    Layers, back to front, matching the skill's own table: (1) field, flat brand colour or a hard split,
    (2) field graphics, (3) hero cut-out, (4) pack cut-out, (5) type blocks, (6) devices, (7) brand
    block, (8) base band, (9) mandatories. `type_position` decides where the hero sits and where the type
    goes — the same five zones `posm.TYPE_POSITIONS` already names.

    **A backdrop photograph never goes full-bleed, and never hosts type.** It is composited into a hard
    split — "Photograph or hero above, flat colour below carrying type and pack", the first and safest
    field-division device in `references/key-visual.md`, cited to a real Mother Dairy piece. This is the
    correction that fixes the "not bold enough / unreadable headline" failure at its cause rather than
    its symptom: the skill explicitly refuses the obvious patch, and it is worth quoting because the
    obvious patch is what everyone reaches for, this module's author included —

      *"Any technique that drops a translucent band over a full-bleed image to make room for a headline
      is a symptom of building the wrong thing... A line dropped onto a full-bleed image inside a
      translucent slab is not a layout; it is a subtitle."*

    So there is no scrim, no vignette and no translucent plate here by design. Type sits on flat colour,
    which is why it needs no rescuing.

    `hero_is_cutout` gates the white-to-alpha key. A hero generated by `posm.cutout_prompt` (or
    `/studio-shot` in `cutout` mode) is a subject isolated on plain white and MUST be keyed. A `scene`
    shot is a finished photograph whose white pixels are real content, and keying it destroys the
    picture — found live: a styled pack shot with a glass of milk and a splash came back with the milk,
    the splash and the pack's own white label punched through to the background behind it.
    """
    w, h = canvas_px(fmt, dpi=dpi)
    canvas = Image.new("RGBA", (w, h), (255, 255, 255, 255))

    band = posm.reflow(fmt).get("band", "")
    # Real bug found live: this used to gate the hero on `band` alone — a pure aspect-ratio-delta
    # number — while `posm.TIERS`/`dropped_layers` names a SEPARATE, deliberate rule for which formats
    # cannot carry a photographic hero at all (Wobbler, Unipole, a bunting flag, tin plate...), keyed to
    # the format itself rather than its shape. The two disagree on roughly half the `minimal`/`mark-only`
    # formats — a bunting flag's aspect delta lands in the mild "near" band even though its own tier says
    # "drop the hero entirely" — so those pieces kept getting a full photographic hero their own spec
    # sheet says they cannot carry. `dropped_layers` is the authority on WHICH layers a format keeps;
    # `band` still decides how hard the surviving ones get re-cropped.
    dropped = set(posm.dropped_layers(fmt))
    use_hero = bool(hero_url) and band != "violent" and "hero" not in dropped
    wide = w >= h
    margin = round(min(w, h) * 0.04)

    # 8/9's strip is reserved FIRST so the type zone is computed against what is actually left, rather
    # than the band being drawn over type that already used the space.
    has_band = bool(str(support_line).strip() or [m for m in mandatories if str(m).strip()])
    band_h = round(h * 0.085) if (has_band and band != "violent" and h >= 400) else 0
    avail_h = h - band_h

    # The TYPE's space is reserved next, before the hero takes what is left — and that ordering is the
    # whole point. Doing it the other way (hero gets a fixed 70% of the canvas, type squeezes into the
    # remainder minus the band) refused "Ahead by breakfast" — three words — on an A3 poster while a
    # 900px-tall hero sat above it with room to spare. Reading distance sets the type size and the type
    # size sets the space it needs; the picture is what flexes, because it is the only layer that can.
    # The same split fraction `scamp()` computes and returns as `type_pct` — a chosen scamp carries its
    # own `type_pct` back through `/posm-assemble` so the render's hero/type proportions are provably
    # the ones an art director signed off on, not a fresh 0.30/0.40 that happens to look similar.
    if type_position == "type-over-top":
        pct = type_pct if type_pct is not None else 0.30
        type_zone = (margin, margin, w - margin, margin + round(avail_h * pct))
    elif type_position == "type-beside":
        pct = type_pct if type_pct is not None else 0.40
        type_zone = (margin, margin, round(w * pct), avail_h - margin)
    elif type_position in ("type-only", "product-only"):
        type_zone = (margin, round(avail_h * 0.60), w - margin, avail_h - margin)
    else:  # type-locked-base
        pct = type_pct if type_pct is not None else 0.30
        _zh = round(avail_h * pct)
        type_zone = (margin, avail_h - margin - _zh, w - margin, avail_h - margin)

    # 1. Field — flat colour, or two colours split. Never a photograph across the whole piece.
    field_rgb = _hex_to_rgb(field_hex)
    field2_rgb = _hex_to_rgb(field_hex_2, field_rgb) if field_hex_2 else _shade(field_rgb, 0.88)
    canvas.paste(Image.new("RGBA", (w, h), field_rgb + (255,)), (0, 0))

    # The photograph's own zone under a hard split — everything outside it stays flat colour, and the
    # type zone below is chosen from that flat half.
    backdrop = _open_image(backdrop_url) if backdrop_url else None
    photo_box = None
    if backdrop:
        # Bounded by the type zone, never across it — the hard split the skill's field-division table
        # names first ("Photograph or hero above, flat colour below carrying type and pack").
        if type_position == "type-over-top":
            photo_box = (0, type_zone[3] + margin, w, avail_h)
        elif type_position == "type-beside":
            photo_box = (round(w * 0.42), 0, w, avail_h)
        elif type_position in ("type-only", "product-only"):
            photo_box = None                      # these layouts are the flat field itself
        else:                                     # type-locked-base
            photo_box = (0, 0, w, type_zone[1] - margin)
        if photo_box:
            pw, ph = photo_box[2] - photo_box[0], photo_box[3] - photo_box[1]
            canvas.paste(_cover(backdrop, pw, ph), (photo_box[0], photo_box[1]))

    draw = ImageDraw.Draw(canvas)

    # 2. Field graphics — a low-contrast tonal wedge behind where the hero will stand, the skill's
    # "radiating streaks / glow... to lift it off the field". Kept subtle and skipped on a photo field,
    # where there is already tonal variation to sit against.
    if not photo_box and use_hero and band != "violent":
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        cx, cy = w // 2, round(h * 0.42)
        rr = round(max(w, h) * 0.42)
        gd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=_shade(field_rgb, 1.10) + (150,))
        glow = glow.filter(ImageFilter.GaussianBlur(round(max(w, h) * 0.05)))
        canvas.alpha_composite(glow, (0, 0))

    # `posm.reflow` already names the formats a photographic hero cannot survive at all — "the substrate
    # cannot carry a photographic hero" / "nothing croppable survives" — the same rule `dropped_layers`
    # already applies to the hero at the smallest tiers. A 12:1 shelf strip forcing a full figure into a
    # 130px-tall canvas is not a layout bug to patch per format; it is this module ignoring a rule the
    # codebase already computed. Below that band, this falls back to the minimal layout: logo one side,
    # pack the other, the line in between — same shape `posm.TIERS["minimal"]` already describes.
    hero_box = None
    if use_hero:
        # 3. Hero cut-out, boxed per the chosen type position — the same five zones `posm.TYPE_POSITIONS`
        # already names, inset from the base band when there is one.
        hero = _open_image(hero_url)
        if hero:
            # Decided from the PICTURE unless the caller insists. `None` (the default) means look at the
            # image and see whether it sits on a plain backdrop — see `looks_like_cutout` for why the
            # old provenance-based flag was wrong and what it cost.
            if hero_is_cutout is None:
                hero_is_cutout = looks_like_cutout(hero)
            if report is not None:
                report["hero_keyed"] = bool(hero_is_cutout)
            if hero_is_cutout:
                hero = _key_backdrop_to_alpha(hero)
            # Whatever the type did not take, bounded by the band. The hero is the flexible layer.
            if type_position == "type-over-top":
                hero_box = (margin, type_zone[3] + margin, w - margin, avail_h - margin)
            elif type_position == "type-beside":
                hero_box = (type_zone[2] + margin, margin, w - margin, avail_h - margin)
            elif type_position in ("type-only", "product-only"):
                hero_box = (round(w * 0.28), round(avail_h * 0.10), round(w * 0.72),
                            type_zone[1] - margin)
            else:  # type-locked-base (default) — hero fills the upper field, type band along the base.
                hero_box = (margin, margin, w - margin, type_zone[1] - margin)
            bw, bh = hero_box[2] - hero_box[0], hero_box[3] - hero_box[1]
            # **Fit the SUBJECT, not the file.** A generated cut-out carries a wide transparent margin —
            # measured on a real one, the subject filled 90% of the width but only 49% of the height and
            # 43% of the area. Fitting the whole image to the hero box therefore rendered the subject at
            # roughly half the size the layout had allocated, and the rest of the piece was void. That
            # is the single biggest reason a finished piece looked empty, and it is a one-line fix:
            # crop to the alpha bounding box first, so "fill this box" means the subject fills it.
            if hero_is_cutout:
                _bb = hero.getchannel("A").getbbox()
                if _bb:
                    hero = hero.crop(_bb)
            # A cut-out is CONTAINED — cropping a masked subject cuts a person's head off, and its
            # transparent margin is what lets the field show around it. A scene photograph is a panel
            # and COVERS its box the way any placed photograph does; contained, a 16:9 still in a tall
            # box left a band of empty field above and below it that read as a mistake.
            fitted = _contain(hero, bw, bh) if hero_is_cutout else _cover(hero, bw, bh)
            # Rule of thirds, but only where it buys something. A cut-out sharing the frame with the
            # pack sits off-centre so the two make a diagonal rather than a stack. Centred when alone,
            # because a lone subject off-centre on a flat field just looks misaligned.
            bias = 0.5
            if hero_is_cutout and pack_url and bw > fitted.width:
                bias = 0.38
            x = hero_box[0] + round((bw - fitted.width) * bias)
            # **Optical centre, not mathematical.** The eye reads the centre of a rectangle as sitting
            # slightly above the measured middle (~46% down), which is why a sign hung dead-centre looks
            # a little low and why a picture mount is cut deeper at the bottom. Only applied to a
            # cut-out: a photo panel COVERS its box and has no slack to shift within.
            y = (hero_box[1] + round((bh - fitted.height) * 0.46) if hero_is_cutout
                 else hero_box[1] + (bh - fitted.height) // 2)

            # Seat the cut-out. Layer 3 of the skill's own stack is "the subject, masked out of its
            # background, hard-edged, **shadowed to seat it**", and until now that was one soft ellipse,
            # which is neither of the two things a real shadow is made of.
            #
            # A physically-behaved shadow is two elements and retouchers separate them deliberately:
            #   * **ambient occlusion** — very dark, tight and sharp, exactly where the object meets the
            #     surface. This is what actually grounds an object, and it is present regardless of how
            #     diffuse the light is.
            #   * **cast shadow** — broader and much softer, thrown away from the light, fading as it
            #     goes. This one carries the light DIRECTION.
            # Missing occlusion, or a cast shadow disagreeing with the light, is what reads as "pasted".
            #
            # `LIGHT_DIR` is deliberately a module constant rather than a per-piece choice: across a kit
            # of eleven pieces, a shadow that changes angle piece to piece looks chaotic however good
            # each one is on its own — the same coherence argument the whole skill is built on.
            if hero_is_cutout:
                bbox = fitted.getchannel("A").getbbox()
                if bbox:
                    sx0, _sy0, sx1, sy1 = bbox
                    span = max(8, sx1 - sx0)
                    cx_ = x + (sx0 + sx1) // 2
                    cy_ = y + sy1
                    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                    sd = ImageDraw.Draw(shadow)
                    # Cast: wider, offset along the light direction, very soft, weak.
                    cast_w = round(span * 1.05)
                    cast_h = max(6, round(h * 0.032))
                    off = round(span * 0.16 * LIGHT_DIR)
                    sd.ellipse([cx_ + off - cast_w // 2, cy_ - cast_h // 2,
                                cx_ + off + cast_w // 2, cy_ + cast_h // 2], fill=(0, 0, 0, 70))
                    shadow = shadow.filter(ImageFilter.GaussianBlur(max(6, round(cast_h * 0.9))))
                    # Occlusion: narrow, tight to the contact line, dark, barely blurred.
                    ao = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                    ao_w = round(span * 0.62)
                    ao_h = max(3, round(h * 0.010))
                    ImageDraw.Draw(ao).ellipse(
                        [cx_ - ao_w // 2, cy_ - ao_h // 2, cx_ + ao_w // 2, cy_ + ao_h // 2],
                        fill=(0, 0, 0, 150))
                    shadow.alpha_composite(ao.filter(ImageFilter.GaussianBlur(max(2, round(ao_h * 0.5)))))
                    canvas.alpha_composite(shadow, (0, 0))
            canvas.alpha_composite(fitted, (x, y))

    # 4. Pack cut-out — the real pack, masked out of its own shot and OVERLAPPING the hero.
    #
    # Two rules the skill states plainly and this module was not following. `references/key-visual.md`
    # specifies the pack as "Lower third, **15–30% of height**, front-facing and level, **overlapping
    # the hero slightly so the two read as one group rather than two pasted layers**." It was sized off
    # the canvas WIDTH (16%) and docked into a corner with a clear gap, so on a tall poster it came out
    # small and separate — two objects sharing a page instead of one arrangement.
    #
    # The overlap is not decoration: proximity is the Gestalt mechanism by which the eye reads separate
    # shapes as a single group, and it is the difference between a composed piece and a collage.
    #
    # It is also a real cut-out now rather than a white card. The card existed because keying could not
    # be trusted; now that the matte is measured, defringed and decontaminated, the pack can be masked
    # like every other element — and a card would reintroduce exactly the white rectangle the logo fix
    # just removed.
    pack = _open_image(pack_url) if pack_url else None
    if pack:
        pack = _key_backdrop_to_alpha(pack)
        _pb = pack.getchannel("A").getbbox()
        if _pb:
            pack = pack.crop(_pb)
        # 22% of HEIGHT — the middle of the skill's 15–30% band. Width follows from the pack's own
        # aspect so a tall pouch and a squat tub both land at the same visual weight.
        pack_h = round(h * (0.26 if not use_hero else 0.22))
        pack_w = max(1, round(pack_h * pack.width / max(1, pack.height)))
        if pack_w > w * 0.42:                       # never let a wide pack dominate the frame
            pack_w = round(w * 0.42)
            pack_h = max(1, round(pack_w * pack.height / max(1, pack.width)))
        fitted_pack = pack.resize((pack_w, pack_h), Image.LANCZOS)

        if hero_box:
            # Tucked into the hero's lower edge and pulled INTO it, so the silhouettes touch.
            px_ = min(hero_box[2], w - margin) - pack_w
            py_ = hero_box[3] - round(pack_h * 0.82)
        elif wide:
            px_, py_ = w - margin - pack_w, (h - band_h - pack_h) // 2
        else:
            px_, py_ = (w - pack_w) // 2, h - band_h - margin - pack_h
        py_ = min(py_, h - band_h - pack_h)         # never let it slide under the base band

        # The pack gets the same two-part shadow as the hero, from the same light — a kit where the
        # hero is lit from one side and the pack from another is the incoherence this exists to avoid.
        ps = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        psd = ImageDraw.Draw(ps)
        base_y = py_ + pack_h
        cw_ = round(pack_w * 1.0)
        ch_ = max(4, round(h * 0.018))
        psd.ellipse([px_ + pack_w // 2 + round(pack_w * 0.16 * LIGHT_DIR) - cw_ // 2, base_y - ch_ // 2,
                     px_ + pack_w // 2 + round(pack_w * 0.16 * LIGHT_DIR) + cw_ // 2, base_y + ch_ // 2],
                    fill=(0, 0, 0, 65))
        ps = ps.filter(ImageFilter.GaussianBlur(max(4, round(ch_ * 0.9))))
        pao = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        aw_, ah_ = round(pack_w * 0.6), max(2, round(h * 0.007))
        ImageDraw.Draw(pao).ellipse(
            [px_ + pack_w // 2 - aw_ // 2, base_y - ah_ // 2,
             px_ + pack_w // 2 + aw_ // 2, base_y + ah_ // 2], fill=(0, 0, 0, 140))
        ps.alpha_composite(pao.filter(ImageFilter.GaussianBlur(max(2, round(ah_ * 0.6)))))
        canvas.alpha_composite(ps, (0, 0))
        canvas.alpha_composite(fitted_pack, (px_, py_))

    # 5. Type blocks — sized from `posm.cap_fraction`, the real trade-practice minimum for this format, not
    # a guessed font size. Falls back to a reasonable preview default when the format has no mm (a bay
    # that has to be measured on site, per `posm.cap_fraction`'s own docstring).
    # `mark-only` (Wobbler, Unipole, Entry arch) drops the hero AND the line — "pack silhouette and
    # brand block, no line" per `posm.TIERS`. Without this, fixing the hero-drop above just swapped one
    # wrong picture (a full photo that doesn't fit) for another (a headline floating with nothing to
    # anchor it) on exactly the three formats whose own spec says neither belongs.
    if headline.strip() and "type" not in dropped:
        frac = posm.cap_fraction(fmt) or 0.09
        cap_px = frac * h
        base_size = max(14, round(cap_px / 0.7))
        # Multi-weight, per `references/key-visual.md`: "One word or phrase very large, the rest
        # smaller. Never one uniform size." The supporting words stay AT the reading-distance minimum
        # and the emphasis goes above it — so nothing on the piece drops below the legibility floor
        # `posm.cap_fraction` computes, and the hierarchy is bought with size rather than taken from it.
        small_size, big_size = base_size, round(base_size * 1.5)
        if not use_hero:
            # Minimal layout: logo and pack each take a side slot (see below), the line owns the middle.
            side = round(w * 0.24) if wide else round(h * 0.24)
            zone = ((margin + side, margin, w - margin - side, avail_h - margin) if wide else
                    (margin, margin + side, w - margin, avail_h - margin - side))
        else:
            zone = type_zone          # reserved above, before the hero was given anything
        zone_w, zone_h = zone[2] - zone[0], zone[3] - zone[1]

        # Contrast is decided against the colour actually behind the type, sampled from the canvas as
        # composited. The old code read `field_rgb`, which was hardcoded to mid-grey whenever a backdrop
        # existed — and mid-grey fails the > 0.55 test, so a headline over a photographic field came out
        # white every time regardless of the picture. That is the white-on-bright-sky failure exactly.
        behind = _avg_rgb(canvas, zone)
        # Chosen by MEASURED contrast against what is actually behind the type, not by a luminance
        # coin-flip. WCAG's floor for large text is 3:1; both candidates are scored and the better one
        # wins, so a mid-tone field gets the ink that actually works rather than the one a threshold
        # happened to pick. If even the winner is under 3:1 the field cannot carry type at all — that
        # is reported rather than papered over with a slab, which the skill refuses.
        # The convention decides first, the ratio VERIFIES it. On a mid-to-dark brand field POS knocks
        # the headline out in white — that is what every exhibit in the skill does — and on a light
        # field it sets dark. Picking purely by highest ratio overrides that for no gain: on Heritage
        # green, charcoal measures 4.5:1 against white's 3.6:1, so a pure-maximum rule would set a dairy
        # poster in near-black and lose the category's own look while both options clear the floor
        # comfortably. So: take the conventional ink, and only switch if it fails WCAG's 3:1 for large
        # text — at which point the field itself is the problem and the report says so.
        _dark, _white = (24, 24, 24), (250, 250, 250)
        text_rgb = _white if _rel_luminance(behind) < 0.35 else _dark
        _best_ratio = contrast_ratio(text_rgb, behind)
        _other = _dark if text_rgb is _white else _white
        if _best_ratio < 3.0 and contrast_ratio(_other, behind) > _best_ratio:
            text_rgb = _other
            _best_ratio = contrast_ratio(text_rgb, behind)
        if report is not None:
            report["contrast_ratio"] = round(_best_ratio, 2)
            report["contrast_ok"] = _best_ratio >= 3.0
            report["behind_type"] = "#%02X%02X%02X" % behind
            if _best_ratio < 3.0:
                report.setdefault("notes", []).append(
                    f"The headline sits at {_best_ratio:.1f}:1 against the field behind it, under the "
                    f"3:1 floor for large type. Choose a lighter or darker field colour — a slab behind "
                    f"the words is not the fix here.")

        before, emph, after = _split_emphasis(headline.strip(), headline_emphasis)
        blocks = []                                   # (text, font, size, is_emphasis, track)
        for txt, sz, is_e in ((before, small_size, False), (emph, big_size, True),
                              (after, small_size, False)):
            if not txt:
                continue
            f = _font(sz, txt)
            # Negative tracking, scaled to the size. Type set at 110–170px is display type, and display
            # type opens up: spacing that reads correctly at 16px reads loose and weak at 10× that. The
            # emphasis line is the largest and gets the most correction.
            track = -sz * (0.024 if is_e else 0.012)
            for ln in _wrap_tracked(draw, txt, f, zone_w, track):
                blocks.append((ln, f, sz, is_e, track))

        # 1.15 leading for display type — the standard for headlines, and tighter than the 1.22 used
        # before. Large type needs proportionally LESS leading than body text, not more: the lines are
        # already far apart in absolute terms and generous leading breaks them into separate objects
        # instead of one block of voice.
        total_h = sum(sz * 1.15 for _t, _f, sz, _e, _tr in blocks)
        # Real bug found live: with no check here, a headline that wraps to more lines than the zone
        # holds at this format's mandated cap height just kept drawing downward past the zone and off
        # the bottom of the canvas — the tail of the line silently vanished (no error, no warning),
        # which is exactly the "silently shipping N words onto a gondola header" failure
        # `posm.adaptation()`'s own docstring already names and refuses to do at the word-count stage.
        # That gate lives in a different function and nothing enforces it here — `/posm-assemble` draws
        # whatever headline it is given, at whatever length, so this is the one place that actually has
        # to refuse rather than the pixels making the call by running out of canvas.
        if total_h > zone_h:
            label = (posm.FORMATS.get(fmt) or {}).get("label", fmt)
            words = len(headline.split())
            raise ValueError(
                f"This line ({words} words) sets to {len(blocks)} lines at {label}'s minimum legible "
                f"cap height and does not fit the type band — the last line would run off the piece. "
                f"Write a shorter version of the same line for this format, or choose a bigger piece.")

        centred = type_position != "type-beside"
        # Optical centre again: a block of type centred mathematically in its zone reads low.
        ty = zone[1] + max(0, (zone_h - total_h) * 0.46)
        for txt, f, sz, is_e, track in blocks:
            tw = _tracked_width(draw, txt, f, track)
            tx = zone[0] + (zone_w - tw) / 2 if centred else zone[0]
            line_h = sz * 1.15
            # 6. Devices — "Type on POS is not set on a background; it is built", and a headline
            # floating alone on a field is listed in the skill's own checklist as a defect. The
            # emphasis block gets a highlight box behind it or a rule under it; the rest stays plain.
            if is_e and device == "highlight":
                pad_x, pad_y = round(sz * 0.22), round(sz * 0.10)
                box_rgb = _shade(behind, 0.55) if _luminance(behind) > 0.55 else _shade(behind, 1.6)
                draw.rounded_rectangle(
                    [tx - pad_x, ty - pad_y, tx + tw + pad_x, ty + line_h - pad_y * 0.5],
                    radius=round(sz * 0.16), fill=box_rgb + (255,))
                on_box = (24, 24, 24) if contrast_ratio((24, 24, 24), box_rgb) >= \
                    contrast_ratio((250, 250, 250), box_rgb) else (250, 250, 250)
                _draw_tracked(draw, (tx, ty), txt, f, on_box, track)
                ty += line_h
                continue
            if is_e and device == "rule":
                ry = ty + line_h * 0.92
                draw.rectangle([tx, ry, tx + tw, ry + max(3, round(sz * 0.075))],
                               fill=text_rgb + (255,))
            _draw_tracked(draw, (tx, ty), txt, f, text_rgb, track)
            ty += line_h

    # 7. Brand block — sized to a consistent share of the piece, inside the format's own safe margin so it is
    # never closer to the trim than `posm.bleed_safe` says a mark should be. Docked opposite the pack in
    # the minimal layout so the two side slots don't compete for the same corner; a fixed corner
    # otherwise, since a hero box always leaves that corner free by construction.
    logo = _open_image(logo_url) if logo_url else None
    if logo:
        # Logo artwork is almost always supplied on a white plate rather than with real transparency
        # (the brand's own signed-off file here is a white-background PNG). Un-keyed, that plate is a
        # white rectangle sitting on the brand's colour field — visible on every piece made until now.
        logo = _key_backdrop_to_alpha(logo)
        safe = posm.bleed_safe(fmt)
        row = posm.FORMATS.get(fmt) or {}
        mm = row.get("mm")
        safe_px = round((safe["safe_mm"] / mm[1]) * h) if mm else margin
        logo_w = round(w * (0.18 if not use_hero else 0.14))
        logo_fit = _contain(logo, logo_w, round(logo_w * 0.6))
        if not use_hero:
            lx, ly = ((safe_px, (h - logo_fit.height) // 2) if wide else
                      ((w - logo_fit.width) // 2, safe_px))
        else:
            lx, ly = safe_px, safe_px
        canvas.alpha_composite(logo_fit, (lx, ly))

    # 8/9. Base band and mandatories — the two layers the stack ends on, and the two that were missing
    # from every piece this module has ever produced. The mandatories are not decoration: a dairy piece
    # without the FSSAI mark and licence number is not a design choice, it is a piece that cannot legally
    # be printed, and `brandprofile`'s `mandatories` field has held them the whole time with nothing
    # reading it. "Flat strip: tagline, footnote strip" / "Smallest, in the base band."
    if band_h:
        band_rgb = _shade(field_rgb, 0.72) if _luminance(field_rgb) > 0.45 else _shade(field_rgb, 1.35)
        by = h - band_h
        canvas.paste(Image.new("RGBA", (w, band_h), band_rgb + (255,)), (0, by))
        band_fg = (24, 24, 24) if _luminance(band_rgb) > 0.55 else (245, 245, 245)
        tag = str(support_line).strip()
        marks = " · ".join(str(m).strip() for m in mandatories if str(m).strip())
        # The tagline is the larger of the two and sits on the optical centre line of the band; the
        # mandatories are deliberately the smallest type on the piece, tucked under it.
        if tag:
            tf = _font(max(11, round(band_h * (0.38 if marks else 0.46))), tag)
            tw = draw.textlength(tag, font=tf)
            draw.text(((w - tw) / 2, by + band_h * (0.14 if marks else 0.26)), tag, font=tf, fill=band_fg)
        if marks:
            mf = _font(max(9, round(band_h * 0.22)), marks)
            mw = draw.textlength(marks, font=mf)
            draw.text(((w - mw) / 2, by + band_h * (0.62 if tag else 0.38)), marks, font=mf, fill=band_fg)

    # The two-metre test, run on the finished piece rather than left as an instruction to somebody who
    # is not in the loop. Reported, never enforced — see `squint`.
    if report is not None:
        try:
            report["squint"] = squint(canvas, {"hero": hero_box, "type": type_zone,
                                               "pack": None}, field_rgb)
            for note in report["squint"].get("notes", []):
                report.setdefault("notes", []).append(note)
        except Exception:
            pass          # a diagnostic must never be the reason a piece fails to render
        report.setdefault("notes", [])
        report["light_dir"] = "left" if LIGHT_DIR > 0 else "right"

    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG")
    return out.getvalue()


def type_over_photo(*, photo_url: str, fmt: str, headline: str = "",
                     type_position: str = "type-locked-base", headline_emphasis: str = "",
                     device: str = "rule", support_line: str = "", mandatories: tuple = (),
                     field_hex: str = "", type_pct: float | None = None, dpi: int = 0,
                     report: dict | None = None) -> bytes:
    """Real type, laid over a finished photograph — deliberately the one slice of `assemble()`'s job
    worth keeping once the picture is no longer separately-layered hero/pack/field but one baked scene
    from a studio shot. No flat field, no hero box, no pack corner card, no keying: the photo already
    IS the composed picture.

    Fits the photo to the format's own canvas, reserves a type zone using the same `type_pct` geometry
    `assemble()` and `scamp()` already share, and sets the line in the same script-aware bold type
    against the same measured-contrast, WCAG-floor logic `assemble()` uses. That logic samples the
    actual pixels behind the type rather than assuming a flat colour, so it needs no change to work on
    a photographic background — no translucent scrim, the thing the skill explicitly refuses ("a line
    dropped onto a full-bleed image inside a translucent slab is not a layout; it is a subtitle").

    Refuses (ValueError) on the same overflow `assemble()` refuses on — a headline that does not fit
    this format's legibility floor is a worse failure silently truncated than named and stopped.
    """
    w, h = canvas_px(fmt, dpi=dpi)
    photo = _open_image(photo_url)
    if not photo:
        raise ValueError(f"Could not open the photo to set type on ({photo_url!r}).")
    canvas = _cover(photo, w, h).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    band = posm.reflow(fmt).get("band", "")
    margin = round(min(w, h) * 0.04)
    has_band = bool(str(support_line).strip() or [m for m in mandatories if str(m).strip()])
    band_h = round(h * 0.085) if (has_band and band != "violent" and h >= 400) else 0
    avail_h = h - band_h

    if type_position == "type-over-top":
        pct = type_pct if type_pct is not None else 0.30
        type_zone = (margin, margin, w - margin, margin + round(avail_h * pct))
    elif type_position == "type-beside":
        pct = type_pct if type_pct is not None else 0.40
        type_zone = (margin, margin, round(w * pct), avail_h - margin)
    elif type_position in ("type-only", "product-only"):
        type_zone = (margin, round(avail_h * 0.60), w - margin, avail_h - margin)
    else:  # type-locked-base
        pct = type_pct if type_pct is not None else 0.30
        zh = round(avail_h * pct)
        type_zone = (margin, avail_h - margin - zh, w - margin, avail_h - margin)

    if not headline.strip():
        raise ValueError("No line to set — pass a headline.")

    frac = posm.cap_fraction(fmt) or 0.09
    cap_px = frac * h
    base_size = max(14, round(cap_px / 0.7))
    small_size, big_size = base_size, round(base_size * 1.5)
    zone_w, zone_h = type_zone[2] - type_zone[0], type_zone[3] - type_zone[1]

    # Contrast measured against what is actually behind the type — a photo, here, not a flat field —
    # same logic `assemble()` already uses, unmodified. See that function's own comment for why the
    # conventional ink (white on dark, dark on light) is tried first and only overridden when it fails
    # the 3:1 floor, rather than always taking the mathematically highest ratio.
    behind = _avg_rgb(canvas, type_zone)
    _dark, _white = (24, 24, 24), (250, 250, 250)
    text_rgb = _white if _rel_luminance(behind) < 0.35 else _dark
    _best_ratio = contrast_ratio(text_rgb, behind)
    _other = _dark if text_rgb is _white else _white
    if _best_ratio < 3.0 and contrast_ratio(_other, behind) > _best_ratio:
        text_rgb = _other
        _best_ratio = contrast_ratio(text_rgb, behind)
    if report is not None:
        report["contrast_ratio"] = round(_best_ratio, 2)
        report["contrast_ok"] = _best_ratio >= 3.0
        report["behind_type"] = "#%02X%02X%02X" % behind
        if _best_ratio < 3.0:
            report.setdefault("notes", []).append(
                f"The headline sits at {_best_ratio:.1f}:1 against the photo behind it, under the 3:1 "
                f"floor for large type. The composition needs a clearer patch behind the type zone — "
                f"regenerate with more headroom there, or move the type zone.")

    before, emph, after = _split_emphasis(headline.strip(), headline_emphasis)
    blocks = []                                       # (text, font, size, is_emphasis, track)
    for txt, sz, is_e in ((before, small_size, False), (emph, big_size, True),
                          (after, small_size, False)):
        if not txt:
            continue
        f = _font(sz, txt)
        track = -sz * (0.024 if is_e else 0.012)
        for ln in _wrap_tracked(draw, txt, f, zone_w, track):
            blocks.append((ln, f, sz, is_e, track))

    total_h = sum(sz * 1.15 for _t, _f, sz, _e, _tr in blocks)
    if total_h > zone_h:
        label = (posm.FORMATS.get(fmt) or {}).get("label", fmt)
        words = len(headline.split())
        raise ValueError(
            f"This line ({words} words) sets to {len(blocks)} lines at {label}'s minimum legible cap "
            f"height and does not fit the type band — the last line would run off the piece. Write a "
            f"shorter version of the same line for this format, or choose a bigger piece.")

    centred = type_position != "type-beside"
    ty = type_zone[1] + max(0, (zone_h - total_h) * 0.46)
    for txt, f, sz, is_e, track in blocks:
        tw = _tracked_width(draw, txt, f, track)
        tx = type_zone[0] + (zone_w - tw) / 2 if centred else type_zone[0]
        line_h = sz * 1.15
        if is_e and device == "highlight":
            pad_x, pad_y = round(sz * 0.22), round(sz * 0.10)
            box_rgb = _shade(behind, 0.55) if _luminance(behind) > 0.55 else _shade(behind, 1.6)
            draw.rounded_rectangle(
                [tx - pad_x, ty - pad_y, tx + tw + pad_x, ty + line_h - pad_y * 0.5],
                radius=round(sz * 0.16), fill=box_rgb + (255,))
            on_box = (24, 24, 24) if contrast_ratio((24, 24, 24), box_rgb) >= \
                contrast_ratio((250, 250, 250), box_rgb) else (250, 250, 250)
            _draw_tracked(draw, (tx, ty), txt, f, on_box, track)
            ty += line_h
            continue
        if is_e and device == "rule":
            ry = ty + line_h * 0.92
            draw.rectangle([tx, ry, tx + tw, ry + max(3, round(sz * 0.075))], fill=text_rgb + (255,))
        _draw_tracked(draw, (tx, ty), txt, f, text_rgb, track)
        ty += line_h

    # The base band — a SOLID opaque strip over the photo's bottom edge, same convention `assemble()`
    # already uses, not a translucent scrim. `field_hex` is the same brand-colour input `assemble()`
    # takes, resolved the same way by the caller; absent, a neutral dark grey stands in.
    if band_h:
        field_rgb = _hex_to_rgb(field_hex) if field_hex else (60, 60, 60)
        band_rgb = _shade(field_rgb, 0.72) if _luminance(field_rgb) > 0.45 else _shade(field_rgb, 1.35)
        by = h - band_h
        canvas.paste(Image.new("RGBA", (w, band_h), band_rgb + (255,)), (0, by))
        band_fg = (24, 24, 24) if _luminance(band_rgb) > 0.55 else (245, 245, 245)
        tag = str(support_line).strip()
        marks = " · ".join(str(m).strip() for m in mandatories if str(m).strip())
        if tag:
            tf = _font(max(11, round(band_h * (0.38 if marks else 0.46))), tag)
            tw2 = draw.textlength(tag, font=tf)
            draw.text(((w - tw2) / 2, by + band_h * (0.14 if marks else 0.26)), tag, font=tf, fill=band_fg)
        if marks:
            mf = _font(max(9, round(band_h * 0.22)), marks)
            mw = draw.textlength(marks, font=mf)
            draw.text(((w - mw) / 2, by + band_h * (0.62 if tag else 0.38)), marks, font=mf, fill=band_fg)

    if report is not None:
        report.setdefault("notes", [])

    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG")
    return out.getvalue()


def type_over_photo_and_store(**kwargs) -> str:
    """`type_over_photo()`, written to the served media folder. Returns the `/media/...` URL."""
    data = type_over_photo(**kwargs)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    name = f"kv-type-{uuid.uuid4().hex[:10]}.png"
    with open(os.path.join(MEDIA_DIR, name), "wb") as fh:
        fh.write(data)
    return f"/media/{name}"


def scamp(fmt: str, type_position: str, field_hex: str = "", *, long_edge: int = 320,
          headline: str = "", with_pack: bool = True, type_pct: float | None = None) -> dict:
    """A thumbnail scamp: where the layers sit, drawn as blocks. No model call, no cost, milliseconds.

    The step this product skipped entirely. A studio settles composition on 2×2-inch thumbnails first —
    "quick, raw drawings mapped out in seconds to figure out placement and visual hierarchy" — precisely
    because deciding layout with finished artwork is slow and expensive. Here the equivalent mistake was
    worse than slow: every layout comparison cost a real image generation, so in practice nobody
    compared, they accepted whatever the first render gave them.

    Deliberately crude. A scamp that looks finished invites a verdict on the picture, and the only
    question at this stage is whether the ARRANGEMENT works — where the eye lands, whether the type has
    room, whether the pack and hero make a group. Squinting at this is the same two-metre test the
    skill's own final check asks for ("squint at it as a thumbnail... if it becomes mush, it fails at
    two metres too"), applied before the render instead of after it.

    `type_pct` is the one number that actually gets approved here: the share of the split dimension the
    type zone takes (default 0.30 for a top/base split, 0.40 for a side split — the same defaults
    `assemble()` uses). Returned alongside the image so a chosen scamp can carry it forward as a real,
    numeric contract — `assemble()` takes the identical parameter and the identical formula, so a
    render's hero/type split is provably the one that was signed off here, not just visually similar to
    it. Returns `{"bytes", "hero_box", "type_zone", "type_pct"}` rather than raw bytes for that reason.
    """
    w, h = canvas_px(fmt, long_edge=long_edge)
    field = _hex_to_rgb(field_hex)
    img = Image.new("RGB", (w, h), field)
    d = ImageDraw.Draw(img)
    ink = (24, 24, 24) if _luminance(field) > 0.55 else (245, 245, 245)
    # Same fraction `assemble()` uses (0.04) — a scamp that were on a looser margin would be approving
    # an arrangement the final render then doesn't actually match.
    margin = max(3, round(min(w, h) * 0.04))

    band_h = round(h * 0.085)
    avail = h - band_h
    pct_used = None
    if type_position == "type-over-top":
        pct_used = type_pct if type_pct is not None else 0.30
        tz = (margin, margin, w - margin, margin + round(avail * pct_used))
        hz = (margin, tz[3] + margin, w - margin, avail - margin)
    elif type_position == "type-beside":
        pct_used = type_pct if type_pct is not None else 0.40
        tz = (margin, margin, round(w * pct_used), avail - margin)
        hz = (tz[2] + margin, margin, w - margin, avail - margin)
    elif type_position in ("type-only", "product-only"):
        tz = (margin, round(avail * 0.60), w - margin, avail - margin)
        hz = (round(w * 0.28), round(avail * 0.10), round(w * 0.72), tz[1] - margin)
    else:
        pct_used = type_pct if type_pct is not None else 0.30
        zh = round(avail * pct_used)
        tz = (margin, avail - margin - zh, w - margin, avail - margin)
        hz = (margin, margin, w - margin, tz[1] - margin)

    # Hero: an outlined block with a diagonal, the universal "picture goes here" mark.
    d.rectangle(list(hz), outline=ink, width=max(1, round(w / 200)))
    d.line([hz[0], hz[3], hz[2], hz[1]], fill=ink, width=1)
    d.line([hz[0], hz[1], hz[2], hz[3]], fill=ink, width=1)

    # Type: solid bars at the real weight hierarchy — one fat bar for the emphasis, a thin one under.
    # Bar thickness is capped against the zone's WIDTH as well as its height: `type-beside` gives the
    # type a tall narrow column, and a bar sized only off that height renders as a block rather than as
    # a line of type, which reads as a completely different layout.
    # `product-only` carries no line at all (posm.TYPE_POSITIONS: "No line at all. The pack and the
    # brand mark only"), so drawing a headline into it would scamp a layout that cannot exist.
    if type_position != "product-only":
        tw_, th_ = tz[2] - tz[0], tz[3] - tz[1]
        big = max(3, min(round(th_ * 0.34), round(tw_ * 0.15)))
        small = max(2, round(big * 0.42))
        y_big = tz[1] + round(th_ * 0.10)
        d.rectangle([tz[0], y_big, tz[0] + round(tw_ * 0.72), y_big + big], fill=ink)
        y_small = y_big + round(big * 1.9)
        d.rectangle([tz[0], y_small, tz[0] + round(tw_ * 0.50), y_small + small], fill=ink)

    # Pack, brand block and base band — the fixed furniture, so the arrangement is judged complete.
    if with_pack:
        pw = round(w * 0.17)
        ph = round(pw * 1.25)
        d.rectangle([hz[2] - pw, hz[3] - ph, hz[2], hz[3]], fill=ink)
    lw_ = round(w * 0.16)
    d.rounded_rectangle([margin, margin, margin + lw_, margin + round(lw_ * 0.42)],
                        radius=max(2, round(w / 90)), outline=ink, width=max(1, round(w / 240)))
    d.rectangle([0, h - band_h, w, h], fill=_shade(field, 0.72 if _luminance(field) > 0.45 else 1.35))

    out = io.BytesIO()
    img.save(out, format="PNG")
    return {"bytes": out.getvalue(), "hero_box": hz, "type_zone": tz, "type_pct": pct_used}


def scamp_set(fmt: str, field_hex: str = "", positions: tuple = (), *,
              type_pct: float | None = None, with_pack: bool = True) -> list[dict]:
    """One scamp per candidate layout, so the arrangement is chosen by comparison rather than by
    accepting whichever one the first expensive render happened to produce.

    `type_pct` — see `scamp()` — is a single override applied to whichever positions in `positions`
    use it, meant for the one-scamp "adjust this layout" path (a single-item `positions` tuple), not a
    setting for the whole comparison grid.
    """
    positions = positions or tuple(posm.TYPE_POSITIONS.keys())
    out = []
    for p in positions:
        try:
            data = scamp(fmt, p, field_hex, with_pack=with_pack, type_pct=type_pct)
        except Exception:
            continue
        os.makedirs(MEDIA_DIR, exist_ok=True)
        name = f"scamp-{uuid.uuid4().hex[:10]}.png"
        with open(os.path.join(MEDIA_DIR, name), "wb") as fh:
            fh.write(data["bytes"])
        out.append({"id": p, "type_position": p, "url": f"/media/{name}",
                    "note": posm.TYPE_POSITIONS.get(p, ""), "type_pct": data["type_pct"],
                    "hero_box": data["hero_box"], "type_zone": data["type_zone"]})
    return out


def _with_bleed_and_marks(art: Image.Image, fmt: str, dpi: int,
                          field_rgb: tuple) -> tuple[Image.Image, dict]:
    """Add the printer's bleed and crop marks around finished trim-size artwork.

    Bleed is not decoration and not a margin: presses drift, guillotines drift, and a piece trimmed
    1mm off with no bleed shows a white hairline down one edge. The artwork is extended PAST the trim
    so the drift eats artwork instead of paper. `posm.bleed_safe` has computed the right millimetres
    per format since it was written and nothing ever applied them to a rendered file.

    The field is a flat colour, so extending it is exact rather than a guess — this is the one case
    where bleed needs no mirroring or content-aware fill.
    """
    bs = posm.bleed_safe(fmt)
    bleed_px = max(1, round(float(bs["bleed_mm"]) / 25.4 * dpi))
    mark_len = max(6, round(3.0 / 25.4 * dpi))          # 3mm crop marks, trade standard
    gap = max(2, round(1.0 / 25.4 * dpi))               # marks never touch the trim edge
    pad = bleed_px + mark_len + gap

    W, H = art.width + pad * 2, art.height + pad * 2
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    # Flood the bleed zone with the field colour, then lay the artwork on top of it.
    sheet.paste(Image.new("RGB", (art.width + bleed_px * 2, art.height + bleed_px * 2), field_rgb),
                (pad - bleed_px, pad - bleed_px))
    sheet.paste(art.convert("RGB"), (pad, pad))

    d = ImageDraw.Draw(sheet)
    lw = max(1, round(dpi / 600))
    x0, y0, x1, y1 = pad, pad, pad + art.width, pad + art.height
    for (mx, my, dx, dy) in ((x0, y0, -1, -1), (x1, y0, 1, -1), (x0, y1, -1, 1), (x1, y1, 1, 1)):
        # An L per corner, sitting outside the bleed so it is cut away with the waste.
        sx = mx + dx * (bleed_px + gap)
        sy = my + dy * (bleed_px + gap)
        d.line([(sx, my), (sx + dx * mark_len, my)], fill=(0, 0, 0), width=lw)
        d.line([(mx, sy), (mx, sy + dy * mark_len)], fill=(0, 0, 0), width=lw)
    return sheet, {"bleed_mm": bs["bleed_mm"], "safe_mm": bs["safe_mm"], "bleed_px": bleed_px,
                   "trim_px": [art.width, art.height], "sheet_px": [W, H]}


def assemble_print(*, fmt: str, dpi: int = 300, colour: str = "cmyk", **kwargs) -> tuple[bytes, str, dict]:
    """Print-ready artwork: real trim size at real resolution, with bleed, crop marks and CMYK.

    Everything this module made before was explicitly a comp — `canvas_px`'s own docstring said "a
    preview render, not a print file", and a 1600px RGB PNG is not something a printer can accept for
    an A3 poster. This is the export that closes that gap, and it is the difference between the skill's
    promise ("something a printer can produce") and a picture on a screen.

    **CMYK is a conversion, not a colour management system.** Pillow's RGB→CMYK is a naive formula with
    no ICC profile, so the numbers are a starting point a pre-press operator will re-separate against
    the actual press and stock. That is honest and still useful — a CMYK TIFF at trim size with bleed
    and marks is a file a printer can open and quote from, where a screen PNG is not. Say so when
    handing it over rather than implying a colour-accurate separation. `colour='rgb'` keeps it in RGB
    for digital/large-format vendors who prefer it, which many wide-format shops do.
    """
    art = Image.open(io.BytesIO(assemble(fmt=fmt, dpi=dpi, **kwargs))).convert("RGB")
    field_rgb = _hex_to_rgb(str(kwargs.get("field_hex") or ""))
    sheet, meta = _with_bleed_and_marks(art, fmt, dpi, field_rgb)

    out = io.BytesIO()
    if colour == "cmyk":
        sheet.convert("CMYK").save(out, format="TIFF", dpi=(dpi, dpi), compression="tiff_lzw")
        ext, mode = "tif", "CMYK"
    else:
        sheet.save(out, format="TIFF", dpi=(dpi, dpi), compression="tiff_lzw")
        ext, mode = "tif", "RGB"
    meta.update({"dpi": dpi, "colour": mode, "format": fmt,
                 "mm": list((posm.FORMATS.get(fmt) or {}).get("mm") or []),
                 "note": ("CMYK here is Pillow's un-profiled conversion — usable to quote and "
                          "proof from, but pre-press should re-separate against the real press "
                          "and stock." if mode == "CMYK" else
                          "RGB at trim size with bleed and crop marks, for wide-format vendors "
                          "who prefer it.")})
    return out.getvalue(), ext, meta


def assemble_print_and_store(**kwargs) -> dict:
    data, ext, meta = assemble_print(**kwargs)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    name = f"kv-print-{uuid.uuid4().hex[:10]}.{ext}"
    with open(os.path.join(MEDIA_DIR, name), "wb") as fh:
        fh.write(data)
    meta["url"] = f"/media/{name}"
    meta["bytes"] = len(data)
    return meta


def _svg_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _data_uri(ref: str, *, key: bool = False) -> str:
    """A library/media reference as an embedded data URI, optionally keyed first.

    Embedded rather than linked on purpose: a handover file with linked images is a file that arrives
    broken. The artworker gets one self-contained document.
    """
    img = _open_image(ref)
    if not img:
        return ""
    if key:
        img = _key_backdrop_to_alpha(img)
        bb = img.getchannel("A").getbbox()
        if bb:
            img = img.crop(bb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    import base64
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def artwork_svg(*, fmt: str, headline: str = "", hero_url: str = "", pack_url: str = "",
                logo_url: str = "", field_hex: str = "", headline_emphasis: str = "",
                type_position: str = "type-locked-base", support_line: str = "",
                mandatories: tuple = (), device: str = "rule",
                hero_is_cutout: bool | None = None) -> str:
    """The piece as an editable vector document — layered, with live text. Opens in Illustrator.

    **This is the deliverable; the PNG is a preview of it.** Everything this module made before was
    baked pixels: correct, and dead. A designer could not move the headline two millimetres, change a
    word, swap the field colour or restyle the type without asking for a whole new render — which is
    the opposite of how a key visual is supposed to work. A key visual is a MASTER that gets adapted
    eleven times; if adapting it means regenerating it, the studio is doing the one thing the skill's
    governing rule forbids.

    So the layers are real layers (`<g>` with Illustrator's own `data-name`, which it reads as layer
    names on import), the type is real `<text>` the artworker can retype and rekern, the images are
    embedded and masked rather than flattened into the background, and the geometry is in millimetres
    at true trim size rather than in preview pixels.

    What stays raster, honestly: the hero and pack are photographs, so they are embedded bitmaps inside
    vector frames — that is what they are in Illustrator too. The masking is already applied (measured,
    defringed, decontaminated) because there is no path-tracing here; an artworker who wants a hand-cut
    silhouette still has one job to do, and it is a job they would want to do themselves anyway.
    """
    row = posm.FORMATS.get(fmt) or {}
    mm = row.get("mm")
    if not mm:
        raise ValueError(
            f"{row.get('label', fmt)!r} has no real dimensions on file, so there is no artboard to "
            f"build. This format has to be measured on site before artwork exists for it.")
    # This function never had ANY hero/type gate at all — not even the aspect-band check `assemble()`
    # had before its own fix. So the editable-artwork export was the worst-affected of the three (the
    # raster preview at least dropped the hero on a "violent" shape); a Wobbler's SVG would embed a
    # full photographic hero layer regardless. Same authority as the raster fix: `dropped_layers` names
    # which layers a format's own tier keeps, independent of its shape.
    dropped = set(posm.dropped_layers(fmt))
    W, H = float(mm[0]), float(mm[1])
    field = _hex_to_rgb(field_hex)
    field_css = "#%02X%02X%02X" % field
    bs = posm.bleed_safe(fmt)
    bleed, safe = float(bs["bleed_mm"]), float(bs["safe_mm"])

    band_h = H * 0.085 if (str(support_line).strip() or [m for m in mandatories if str(m).strip()]) else 0.0
    avail = H - band_h
    margin = min(W, H) * 0.04
    if type_position == "type-over-top":
        tz = (margin, margin, W - margin, margin + avail * 0.30)
    elif type_position == "type-beside":
        tz = (margin, margin, W * 0.40, avail - margin)
    elif type_position in ("type-only", "product-only"):
        tz = (margin, avail * 0.60, W - margin, avail - margin)
    else:
        zh = avail * 0.30
        tz = (margin, avail - margin - zh, W - margin, avail - margin)
    hero_box = ((margin, tz[3] + margin, W - margin, avail - margin) if type_position == "type-over-top"
                else (tz[2] + margin, margin, W - margin, avail - margin) if type_position == "type-beside"
                else (margin, margin, W - margin, tz[1] - margin))

    # Cap height from reading distance, exactly as the raster path computes it.
    cap_mm = posm.cap_height_mm(fmt) or (H * 0.05)
    small = cap_mm / 0.7
    big = small * 1.5
    before, emph, after = _split_emphasis(headline.strip(), headline_emphasis)
    ink = "#FAFAFA" if _rel_luminance(field) < 0.35 else "#181818"

    def _img_layer(name: str, ref: str, box: tuple, keyed: bool) -> str:
        uri = _data_uri(ref, key=keyed)
        if not uri:
            return ""
        x0, y0, x1, y1 = box
        return (f'  <g data-name="{name}" id="{name}">\n'
                f'    <image x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}" '
                f'preserveAspectRatio="xMidYMid meet" xlink:href="{uri}"/>\n  </g>\n')

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
        f'  <title>{_svg_escape(row.get("label", fmt))} — key visual</title>\n'
        f'  <desc>Trim {W}×{H}mm · bleed {bleed}mm · safe {safe}mm · '
        f'cap height {cap_mm:.1f}mm from {row.get("read_at", "?")}m reading distance. '
        f'Layers follow the nine-layer POS stack. Type is live text.</desc>\n',
        # 1. Field
        f'  <g data-name="1-field" id="field">\n'
        f'    <rect x="0" y="0" width="{W}" height="{H}" fill="{field_css}"/>\n  </g>\n',
    ]
    # 3/4. Photographic layers
    if hero_url and "hero" not in dropped:
        keyed = looks_like_cutout(_open_image(hero_url)) if hero_is_cutout is None else hero_is_cutout
        parts.append(_img_layer("3-hero", hero_url, hero_box, bool(keyed)))
    if pack_url:
        ph = H * 0.22
        pw = ph * 0.85
        parts.append(_img_layer("4-pack", pack_url,
                                (hero_box[2] - pw, hero_box[3] - ph * 0.82,
                                 hero_box[2], hero_box[3] + ph * 0.18), True))
    # 5/6. Type and devices — live text. `mark-only` (Wobbler, Unipole, Entry arch) drops this too —
    # "pack silhouette and brand block, no line" — so dropping the hero above without also dropping the
    # line here would leave live headline text floating with nothing to anchor it on exactly the three
    # formats whose own tier says neither belongs.
    if headline.strip() and "type" not in dropped:
        ty = tz[1] + max(0.0, ((tz[3] - tz[1]) - (small * 1.15 * (bool(before) + bool(after))
                                                  + big * 1.15 * bool(emph))) * 0.46)
        anchor, tx = ("middle", (tz[0] + tz[2]) / 2) if type_position != "type-beside" else ("start", tz[0])
        type_layer = ['  <g data-name="5-type" id="type">\n']
        for txt, sz, is_e in ((before, small, False), (emph, big, True), (after, small, False)):
            if not txt:
                continue
            ty += sz
            type_layer.append(
                f'    <text x="{tx:.2f}" y="{ty:.2f}" font-family="Noto Sans, Arial, sans-serif" '
                f'font-weight="800" font-size="{sz:.2f}" letter-spacing="{-sz*(0.024 if is_e else 0.012):.3f}" '
                f'fill="{ink}" text-anchor="{anchor}">{_svg_escape(txt)}</text>\n')
            if is_e and device == "rule":
                rw = len(txt) * sz * 0.52
                rx = tx - rw / 2 if anchor == "middle" else tx
                type_layer.append(
                    f'    <rect data-name="6-device-rule" x="{rx:.2f}" y="{ty + sz*0.16:.2f}" '
                    f'width="{rw:.2f}" height="{sz*0.075:.2f}" fill="{ink}"/>\n')
            ty += sz * 0.15
        type_layer.append('  </g>\n')
        parts.append("".join(type_layer))
    # 7. Brand block
    if logo_url:
        lw = W * 0.14
        parts.append(_img_layer("7-brand-block", logo_url, (safe, safe, safe + lw, safe + lw * 0.6), True))
    # 8/9. Base band and mandatories
    if band_h:
        band_rgb = _shade(field, 0.72 if _luminance(field) > 0.45 else 1.35)
        band_css = "#%02X%02X%02X" % band_rgb
        band_ink = "#181818" if _luminance(band_rgb) > 0.55 else "#F5F5F5"
        marks = " · ".join(str(m).strip() for m in mandatories if str(m).strip())
        band = ['  <g data-name="8-base-band" id="base-band">\n',
                f'    <rect x="0" y="{H-band_h:.2f}" width="{W}" height="{band_h:.2f}" fill="{band_css}"/>\n']
        if str(support_line).strip():
            band.append(
                f'    <text x="{W/2:.2f}" y="{H-band_h*0.55:.2f}" font-family="Noto Sans, Arial, sans-serif" '
                f'font-weight="700" font-size="{band_h*0.38:.2f}" fill="{band_ink}" '
                f'text-anchor="middle">{_svg_escape(support_line)}</text>\n')
        if marks:
            band.append(
                f'    <text data-name="9-mandatories" x="{W/2:.2f}" y="{H-band_h*0.20:.2f}" '
                f'font-family="Noto Sans, Arial, sans-serif" font-size="{band_h*0.22:.2f}" '
                f'fill="{band_ink}" text-anchor="middle">{_svg_escape(marks)}</text>\n')
        band.append('  </g>\n')
        parts.append("".join(band))
    # Guides — outside the artwork, on their own layer so they can be hidden or deleted.
    parts.append(
        f'  <g data-name="0-guides" id="guides" opacity="0.5">\n'
        f'    <rect x="{-bleed}" y="{-bleed}" width="{W+bleed*2}" height="{H+bleed*2}" fill="none" '
        f'stroke="#FF00FF" stroke-width="0.2" stroke-dasharray="2 2"/>\n'
        f'    <rect x="{safe}" y="{safe}" width="{W-safe*2}" height="{H-safe*2}" fill="none" '
        f'stroke="#00AAFF" stroke-width="0.2" stroke-dasharray="2 2"/>\n  </g>\n')
    parts.append("</svg>\n")
    return "".join(parts)


def artwork_svg_and_store(**kwargs) -> dict:
    svg = artwork_svg(**kwargs)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    name = f"kv-artwork-{uuid.uuid4().hex[:10]}.svg"
    with open(os.path.join(MEDIA_DIR, name), "w", encoding="utf-8") as fh:
        fh.write(svg)
    row = posm.FORMATS.get(kwargs.get("fmt") or "") or {}
    return {"url": f"/media/{name}", "bytes": len(svg.encode("utf-8")),
            "mm": list(row.get("mm") or []), "format": kwargs.get("fmt"),
            "layers": ["0-guides", "1-field", "3-hero", "4-pack", "5-type", "6-device",
                       "7-brand-block", "8-base-band", "9-mandatories"],
            "note": "Editable vector at true trim size in millimetres. Type is live text; photographs "
                    "are embedded and masked. Opens in Illustrator with named layers."}


def assemble_and_store(**kwargs) -> str:
    """`assemble()`, written to the served media folder. Returns the `/media/...` URL, same convention
    every other generated asset in this app already uses."""
    data = assemble(**kwargs)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    name = f"kv-{uuid.uuid4().hex[:10]}.png"
    with open(os.path.join(MEDIA_DIR, name), "wb") as fh:
        fh.write(data)
    return f"/media/{name}"
