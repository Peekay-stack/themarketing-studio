"""catalog.py — enums and presentation metadata taken from the prototype.

Mirrors the front-end's PLAT map (handles, accent colours, sub-labels) so generated
post previews look exactly like The Marketing Studio prototype.
"""

# The prototype's PLAT map. Social Studio = facebook + instagram + linkedin
# ("one idea -> FB, Instagram & LinkedIn with live previews").
PLATFORMS = [
    {"id": "instagram", "name": "Instagram", "accent": "#E1306C",
     "handle": "brand", "sub": "Sponsored", "studio": "social"},
    {"id": "facebook", "name": "Facebook", "accent": "#1877F2",
     "handle": "Brand", "sub": "Sponsored", "studio": "social"},
    {"id": "linkedin", "name": "LinkedIn", "accent": "#0A66C2",
     "handle": "Brand", "sub": "4,80,210 followers · Promoted", "studio": "social"},
    {"id": "youtube", "name": "YouTube", "accent": "#FF0000",
     "handle": "Brand", "sub": "Channel", "studio": "video"},
]
_PLAT_BY_ID = {p["id"]: p for p in PLATFORMS}


def platform_meta(platform_id: str) -> dict:
    # accept either the id ("instagram") or display name ("Instagram")
    key = platform_id.lower()
    if key in _PLAT_BY_ID:
        return _PLAT_BY_ID[key]
    for p in PLATFORMS:
        if p["name"].lower() == key:
            return p
    return {"id": key, "name": platform_id, "accent": "#14331F", "handle": "Brand",
            "sub": "", "studio": "social"}


# Brief 'format' from the prototype (the brief TYPE, not the channel).
BRIEF_TYPES = ["Comms", "IMC", "Media", "Packaging"]

# Deliverable content types from the prototype's createdMeta().
CONTENT_TYPES = ["Post", "Video", "Avatar video", "Campaign"]

# Campaign objectives (the strategic enum).
CAMPAIGN_OBJECTIVES = [
    "Brand awareness", "Product launch", "Festive / seasonal",
    "Performance / DR", "Trust & purity", "Recipe / usage",
]
