"""packscene.py — the wording that puts a REAL pack into a generated scene (Social posts, later Carousel).

Why it exists: on 21 Sep the owner's real Nourish+ pack photo was tried in 10 real generations (see
BRAND_GROUNDING_TESTING_LOG.md, "21 Sep -- pack shots"). What the live prompt said then -- "reuse the EXACT same
people from the reference image" -- makes no sense for a pack photo, and it let the pack be held, rotated and its
print garbled. This wording, which tells the model the reference IS the real product, to reproduce it front-on and
place it deliberately, kept the pack faithful and legible in every static placement (side, hero, corner, CTA), in
photo and illustrated styles alike. Two limits the trial also showed, and this module cannot remove:
  * a pack that is handled or poured ("in_use") is rotated and its fine print garbles -- so it is opt-in only;
  * a certification mark (an "fssai" badge) was once ADDED that the reference does not carry -- the line below asks
    the model not to, but an intermittent slip is not proven fixed; every published pack still needs a human eye.

Pure functions, no I/O: `main.scene_still` calls these only when the caller sends a `pack_role`, so every other
caller (Video frames, /shot-reference, POSM) keeps its prompt byte-for-byte.
"""
from __future__ import annotations

import re

# side    the default: secondary to the main subject, in the left or right third
# hero    the scene is ABOUT the pack (Product-only style, or a pack-led post)
# in_use  only when the scene must show the pack being opened or poured (fidelity drops -- see above)
# cta     a Carousel's last slide: upper two-thirds, the lower third kept calm for a headline
# corner  a small element in one corner (Infographic)
# none    no pack in this image -- the caller decides; nothing is attached
ROLES = ("side", "hero", "in_use", "cta", "corner", "none")

# Styles that are photographs of a real pack. Everything else (vector, infographic, claymation, watercolour...)
# shows the pack as an illustration, because "no photographic imagery" and "reproduce the pack exactly" cannot
# both be obeyed.
_PHOTO_STYLES = ("real", "product")

PHOTO_INTRO = ("The pack in the reference image is the real product. Reproduce it exactly: the same container type "
               "and format, the same colours, proportions and label layout, and the brand mark — shown front-on so "
               "its front label reads clearly. Never redraw or reimagine it, and do not invent any new legible text "
               "on it.")
ILLUSTRATED_INTRO = ("Draw the product pack from the reference image in this illustration style: the same container "
                     "type and format, the same colour blocks and layout, and a recognisable brand mark — "
                     "simplified, with no fine print.")
NO_MARKS = (" Do not add any logos, certification marks, licence numbers, badges or extra wording to the pack that "
            "are not already in the reference image.")

# Found in the owner's first real batch (21 Sep, 9 posts): a scene that talked about "checking the nutrition panel"
# produced a pack shown from the BACK with an invented nutrition panel (numbers the model made up -- a compliance
# risk on a published post), and scenes that mention opening or pouring a pouch got a SECOND, blurry, invented
# pouch drawn beside the real one. So: the front only, and exactly one pack -- stated over whatever the scene says.
FRONT_ONLY_ONE_PACK = (" Show only the FRONT of the pack: never its back, its sides, a nutrition panel or an "
                       "ingredients list, even if the scene description mentions one. There is exactly one pack "
                       "in the image; do not draw any other pouch, carton or pack. Show no nutrition table, ingredients list or "
                       "other printed facts anywhere in the image.")

_PLACEMENT = {
    # Live-tested finding (owner's first real batch, 21 Sep): with no size given, "side" placements came back
    # looking large and pasted-on. A frame-fraction fix ("about a quarter of the frame's height") went out
    # the same day and held for that batch's wider, more environmental shots.
    #
    # Live-tested finding (22 Sep, two full carousels run back to back specifically to check this): a FRAME
    # fraction does not travel across compositions -- it held fine in one carousel's wide, full-body shots
    # and came out oversized in another's tight close-ups (a pack held up near a face, a pack close on a
    # table), because 25% of a tightly-cropped frame is a much bigger real object than 25% of a wide one.
    # Replaced with the same real-world, composition-independent anchor already proven on `cta` for the
    # identical reason -- a real pack does not get bigger just because the camera moved closer.
    "side": (" Place the pack to one side of the frame (the left or right third), upright and in the "
             "foreground, no larger than a real pack held in the hand of an average-built adult, at its "
             "true, real-life size -- not enlarged for effect, and the SAME real-world size whether this "
             "shot is a wide scene or a tight close-up -- clearly visible but secondary to the main "
             "subject, and not overlapping anyone's face."),
    "hero": " The pack is the hero of the image, centred and upright, its front label clearly visible.",
    "in_use": " Show the pack naturally in the action of the scene, its front label turned toward the camera.",
    # Live-tested finding (22 Sep, a real Carousel CTA slide): with no size given, the pack came out
    # oversized against the two people holding it -- the owner's own note asked for it "in proportion to
    # the hands... a little smaller than the current." The relative-size wording below helped but did not
    # hold in every composition: a later CTA slide (a man standing, arms extended, presenting the pack)
    # still came out too large -- a more advertising-style pose than the hand-off scene this was tuned on.
    # The owner tested a sharper, concrete anchor live via Adjust ("not larger than the real pack in the
    # hand of an average built man") and confirmed it held on that exact slide; folded in as the primary
    # instruction, with the relative-size wording kept alongside it, not replaced -- both are true and
    # reinforce each other.
    "cta": (" Place the pack upright in the upper two-thirds of the frame, no larger than a real pack "
            "held in the hand of an average-built adult, at its true, real-life size relative to any "
            "hands, people or objects near it -- not enlarged for effect -- with its front label clearly "
            "visible, and keep the lower third of the frame clean and uncluttered so a headline can be "
            "placed there."),
    "corner": " Show the pack as a small element in one corner of the frame, upright, secondary to the main graphic.",
}

# Replaces the generic "no on-screen text ... logos" line when a pack is in the image: that line forbade logos and
# text outright, which fights the pack's own brand mark and wording.
TAIL = (" No added text, captions, watermarks or borders anywhere in the frame — the only writing in the image is "
        "what is already printed on the pack.")

# The opening sentence when the pack is the ONLY reference. Today's prompts open "Generate the next shot of the same
# film, reusing the EXACT same people from the reference image", which is nonsense for a pack photo.
PACK_ONLY_OPENING = "Create the image for a marketing post."


def normalise_role(role) -> str:
    """A role the caller sent, or '' when absent/unknown (so a bad value never changes anyone's prompt)."""
    r = str(role or "").strip().lower().replace("-", "_")
    return r if r in ROLES else ""


def is_illustrated(style: str) -> bool:
    return str(style or "").strip().lower() not in _PHOTO_STYLES


def pack_clause(style: str, role: str) -> str:
    """The sentence(s) that say what the pack is and where it goes. Leading space, so it can be dropped into a
    prompt. '' for role 'none' or an unknown role."""
    role = normalise_role(role)
    if not role or role == "none":
        return ""
    intro = ILLUSTRATED_INTRO if is_illustrated(style) else PHOTO_INTRO
    return " " + intro + NO_MARKS + FRONT_ONLY_ONE_PACK + _PLACEMENT[role]


# ---- the scene text itself ---------------------------------------------------------------------------------------
# Trial of 21 Sep (T9-T11): the wording above keeps the PACK front-only, but an image model also obeys what the SCENE
# says. A scene that asked for "the nutrition panel visible" got it moved onto a background jar, with an invented
# table (protein 15 g, beside a pack that says 18g). Wording cannot overrule the scene, so the request is taken out of
# the scene before it is sent. Deliberately narrow -- only requests for the pack's back / nutrition / ingredients,
# which are compliance-risky and can be dropped without damaging the picture. Opening or pouring from a pouch is NOT
# touched: that is what a "pack in use" post is, and the role selector already labels it as lower fidelity.
_RISKY = re.compile(r"nutrition\w*|ingredient\w*|\bback\s+(?:of|panel)\b|\bbackside\b|\breverse\s+(?:side|of)\b|"
                    r"\bside\s+panel\b|\bflip(?:s|ped|ping)?\s+(?:the\s+)?(?:pack|pouch|packet)\b", re.IGNORECASE)
_FALLBACK_SCENE = "a bright, uncluttered everyday scene"


def clean_scene(text: str, role) -> tuple[str, bool]:
    """`(scene, changed)`. Drops each comma/semicolon/sentence-delimited chunk that asks for the pack's back, a
    nutrition panel or an ingredients list. Unchanged (and `changed` False) when nothing matches, when the role is
    'in_use' (the pack is handled on purpose) or when no pack role applies."""
    role = normalise_role(role)
    text = str(text or "")
    if not text or role in ("", "none", "in_use") or not _RISKY.search(text):
        return text, False
    parts = re.split(r"([,;.])", text)
    kept = []
    for k in range(0, len(parts), 2):
        chunk = parts[k]
        delim = parts[k + 1] if k + 1 < len(parts) else ""
        if _RISKY.search(chunk):
            continue
        kept.append(chunk + delim)
    cleaned = "".join(kept).strip(" ,;")
    if not re.sub(r"[\s.,;]", "", cleaned):
        cleaned = _FALLBACK_SCENE
    return cleaned, cleaned != text
