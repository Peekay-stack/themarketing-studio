"""Tests for made.py and the library.py bucket split — both built this round to close the gap where
what got generated was only visible while the browser tab that made it stayed open.

Uses the `pytest-tenant` disposable tenant (via STUDIO_TENANT) rather than `default`, and cleans up
after itself — see MEMORY.md studio-work-inventory, the synthetic-dicts-write-real-tenant-files lesson.
"""
import os

os.environ["STUDIO_TENANT"] = "pytest-tenant"

import brandprofile  # noqa: E402
import briefstore  # noqa: E402
import learning  # noqa: E402
import library  # noqa: E402
import made  # noqa: E402
import tenancy  # noqa: E402


def _clear():
    for row in made.list_entries(include_approved=True):
        made.remove(row["id"])


def test_record_requires_kind_and_title():
    _clear()
    try:
        made.record("", "x")
        raise AssertionError("should have refused an empty kind")
    except ValueError:
        pass
    try:
        made.record("posm_hero", "")
        raise AssertionError("should have refused an empty title")
    except ValueError:
        pass


def test_record_and_list_round_trip():
    _clear()
    row = made.record("posm_hero", "Test hero cutout", url="/media/a.jpg", brand="Test",
                       route="/posm-image")
    rows = made.list_entries("posm_hero")
    assert row["id"] in [r["id"] for r in rows]
    assert row["approved"] is False
    _clear()


def test_approve_hides_from_default_listing_but_keeps_the_row():
    _clear()
    row = made.record("posm_hero", "Test hero cutout", url="/media/a.jpg")
    made.approve(row["id"], "lib-item-xyz", who="Tester")
    pending = made.list_entries("posm_hero")
    everything = made.list_entries("posm_hero", include_approved=True)
    assert row["id"] not in [r["id"] for r in pending]
    approved = next(r for r in everything if r["id"] == row["id"])
    assert approved["approved"] is True
    assert approved["approved_into"] == "lib-item-xyz"
    _clear()


def test_multiple_candidates_survive_one_approval():
    # The exact bug the design review caught: one row per candidate means approving one candidate
    # must not retire the others.
    _clear()
    a = made.record("cast_candidate", "Candidate 1", url="/media/a.jpg")
    b = made.record("cast_candidate", "Candidate 2", url="/media/b.jpg")
    c = made.record("cast_candidate", "Candidate 3", url="/media/c.jpg")
    made.approve(b["id"], "lib-item-b", who="Tester")
    pending = made.list_entries("cast_candidate")
    pending_ids = {r["id"] for r in pending}
    assert a["id"] in pending_ids and c["id"] in pending_ids
    assert b["id"] not in pending_ids
    _clear()


def test_same_second_tiebreak_orders_by_append_not_just_timestamp():
    _clear()
    r1 = made.record("posm_hero", "First")
    r2 = made.record("posm_hero", "Second")
    rows = made._load()
    for r in rows:
        r["made_at"] = "2026-09-04 12:00:00"
    made._save(rows)
    ordered = made.list_entries("posm_hero")
    assert ordered[0]["id"] == r2["id"], "the later-appended row must sort first on a same-second tie"
    _clear()


def test_library_add_buckets_uploads_and_generated_separately():
    row_upload = library.add(b"fake-bytes-1", "test upload", "pack", filename="x.jpg", source="upload")
    row_generated = library.add(b"fake-bytes-2", "test adopted", "cast", filename="y.jpg",
                                 source="generated")
    assert "/uploaded/" in row_upload["file"]
    assert "/tms-approved/" in row_generated["file"]
    assert os.path.isfile(library.local_path(row_upload["file"]))
    assert os.path.isfile(library.local_path(row_generated["file"]))
    library.remove(row_upload["id"])
    library.remove(row_generated["id"])


def test_library_file_route_path_containment_still_blocks_traversal():
    assert library.local_path("../../.env") == ""
    assert library.local_path("cast/tms-approved/../../../etc/passwd") == ""


def test_briefstore_origin_classifies_drafted_vs_reviewed():
    assert briefstore.origin({"source": ""}) == "drafted"
    assert briefstore.origin({"source": "brand-brief-draft"}) == "drafted"
    assert briefstore.origin({"source": "saved"}) == "reviewed"
    assert briefstore.origin({"source": "typed"}) == "reviewed"


def test_briefstore_snapshot_exposes_origin():
    b = {"id": "x1", "brand": "TestBrand", "canon": {}, "fields": {}, "source": "brand-brief-draft"}
    snap = briefstore.snapshot(b)
    assert snap["origin"] == "drafted"
    b["source"] = "saved"
    snap2 = briefstore.snapshot(b)
    assert snap2["origin"] == "reviewed"


def test_voice_block_includes_fonts_and_dos():
    b = {"name": "Heritage Foods", "fonts": "Display: Epilogue; Body: IBM Plex Sans",
         "dos": ["Show real Indian homes and kitchens"]}
    out = brandprofile.voice_block(b)
    assert "TYPE PAIRING: Display: Epilogue; Body: IBM Plex Sans" in out
    assert "DO: Show real Indian homes and kitchens" in out


def test_voice_block_omits_fonts_and_dos_when_absent():
    out = brandprofile.voice_block({"name": "X"})
    assert "TYPE PAIRING" not in out
    assert "DO:" not in out


def test_learning_kind_registered_in_tenancy():
    assert "learning" in tenancy.KINDS


def test_learning_write_read_round_trip_on_disposable_tenant():
    row = learning.record("script", "approve", subject="test", who="Tester")
    assert row["decision"] == "approve"
    rows = learning.decisions(limit=5)
    assert any(r["id"] == row["id"] for r in rows)
