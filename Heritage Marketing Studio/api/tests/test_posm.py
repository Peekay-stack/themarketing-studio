"""Tests for the pure logic in posm.py and producers.py — no server, no API keys, no network.

These formalize the manual verification done live while building the hero-drop-tier fix and the
custom-format resolver (see MEMORY.md studio-work-inventory, round 85): calling the real functions
with synthetic inputs and checking the output, the same way it was done by hand in a throwaway
script at the time. The point of writing it here instead is that it keeps running.
"""
import posm
import producers


# ---------- posm.dropped_layers / tier_for — which formats lose the photographic hero ----------

def test_mark_only_and_minimal_formats_drop_the_hero():
    # Formats whose own tier says "drop the hero" — confirmed live these were rendering a full
    # photographic hero anyway before the assemble()/artwork_svg() gate was fixed to check this.
    for fmt in ("wobbler", "unipole", "bunting", "tin-plate", "hoarding", "backing-sheet", "entry-arch"):
        assert "hero" in posm.dropped_layers(fmt), f"{fmt} should drop the hero"


def test_full_and_reduced_formats_keep_the_hero():
    for fmt in ("poster-a3", "standee", "dealer-board"):
        assert "hero" not in posm.dropped_layers(fmt), f"{fmt} should keep the hero"


def test_mark_only_formats_also_drop_the_line():
    # "Pack silhouette and brand block, no line" — dropping the hero without also dropping the type
    # leaves floating text with nothing to anchor it, which is its own bug (fixed alongside the hero
    # gate, not before it).
    for fmt in ("wobbler", "unipole", "entry-arch"):
        assert "type" in posm.dropped_layers(fmt), f"{fmt} should drop the line too"


def test_bunting_and_tin_plate_disagree_with_their_own_aspect_band():
    # The exact mismatch the round-85 fix exists for: a mild aspect delta ("near" band) that would
    # have kept the hero under the old band-only gate, even though the tier table says drop it.
    for fmt in ("bunting", "tin-plate"):
        band = posm.reflow(fmt).get("band")
        assert band != "violent", f"{fmt} is expected to have a non-violent band for this test to mean anything"
        assert "hero" in posm.dropped_layers(fmt)


# ---------- posm.resolve_format / custom_format — arbitrary sizes, safely ----------

def test_custom_format_canvas_matches_the_requested_aspect():
    # `custom_format`'s own ratio is deliberately NOT provider-safe-clamped — this pipeline never
    # asks the image provider for the custom shape directly, it renders the master once at the
    # always-safe 3:4 and re-flows in Pillow onto `canvas_px()`'s real pixel dimensions. That's the
    # invariant worth testing here: the resulting canvas actually has the requested proportions.
    import keyvisual
    for w, h in [(3, 2), (2, 1), (1, 2), (1, 5), (16, 9)]:
        key, err = posm.resolve_format("custom", f"{w}:{h}")
        assert err == ""
        px_w, px_h = keyvisual.canvas_px(key)
        assert px_w > 0 and px_h > 0
        assert abs((px_w / px_h) - (w / h)) < 0.01


def test_custom_format_is_idempotent():
    key1, _ = posm.resolve_format("custom", "3:2")
    key2, _ = posm.resolve_format("custom", "3:2")
    assert key1 == key2


def test_custom_format_rejects_bad_ratios():
    for bad in ("bogus", "0:5", "5:0", ""):
        key, err = posm.resolve_format("custom", bad)
        assert key == ""
        assert err != ""


def test_custom_format_extreme_ratio_infers_minimal_tier():
    key, err = posm.resolve_format("custom", "1:5")
    assert err == ""
    assert posm.tier_for(key) == "minimal"


def test_custom_format_near_square_ratio_infers_full_tier():
    key, err = posm.resolve_format("custom", "3:4")
    assert err == ""
    assert posm.tier_for(key) == "full"


def test_named_format_passes_through_resolve_format_unchanged():
    key, err = posm.resolve_format("poster-a3", "")
    assert key == "poster-a3"
    assert err == ""


def test_unknown_format_with_no_custom_ratio_errors():
    key, err = posm.resolve_format("not-a-real-format", "")
    assert key == ""
    assert err != ""


def test_custom_format_has_no_print_size_until_measured():
    # No `mm` on a custom size — canvas_px(dpi=...) / artwork_svg both correctly refuse a print
    # export for it rather than inventing a sheet size for a shape nobody measured.
    key, _ = posm.resolve_format("custom", "3:2")
    assert posm.FORMATS[key]["mm"] is None


# ---------- producers.stands_on — the direct-briefing override ----------
# Real shape `stands_on` reads: `platform.get("expressions", {}).get(kind)` first, then
# `platform.get("idea")` — not "expr"/"line", which would silently make the platform arg inert and
# turn these into tests of the wrong thing.

def test_stands_on_platform_wins_by_default():
    platform = {"idea": "Platform line"}
    text, src = producers.stands_on("posm", house=None, platform=platform, typed="Typed brief")
    assert text == "Platform line"
    assert src == "the idea platform"


def test_stands_on_force_typed_overrides_platform():
    platform = {"idea": "Platform line"}
    text, src = producers.stands_on("posm", house=None, platform=platform, typed="Typed brief",
                                     force_typed=True)
    assert text == "Typed brief"
    assert "set aside" in src


def test_stands_on_force_typed_with_no_typed_text_falls_through():
    # force_typed only overrides when there IS typed text — an empty override shouldn't silently
    # blank out a real platform.
    platform = {"idea": "Platform line"}
    text, src = producers.stands_on("posm", house=None, platform=platform, typed="",
                                     force_typed=True)
    assert text == "Platform line"


def test_stands_on_expression_beats_plain_idea_line():
    platform = {"idea": "Plain line", "expressions": {"posm": "POSM-specific expression"}}
    text, src = producers.stands_on("posm", house=None, platform=platform, typed="")
    assert text == "POSM-specific expression"
    assert src == "the idea platform, expressed for posm"


# ---------- producers.OG_ELEMENT_SIZES — every ratio has to be provider-safe ----------

def test_og_element_sizes_are_all_provider_safe_ratios():
    for element, opts in producers.OG_ELEMENT_SIZES.items():
        for key, label, ratio in opts:
            assert ratio in posm.RENDER_RATIOS, f"{element}/{key} uses unsupported ratio {ratio!r}"
