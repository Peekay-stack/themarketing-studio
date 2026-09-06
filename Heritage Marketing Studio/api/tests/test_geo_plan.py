"""Tests for geo.py's priority-geography vocabulary and plan.py's picker/rollup (round 92).

Uses the `pytest-tenant` disposable tenant (via STUDIO_TENANT), same convention as test_made.py — see
MEMORY.md studio-work-inventory, the synthetic-dicts-write-real-tenant-files lesson. Plans created here
are deleted in a fixture teardown rather than left on disk.
"""
import os

os.environ["STUDIO_TENANT"] = "pytest-tenant"

import execution  # noqa: E402
import geo  # noqa: E402
import plan  # noqa: E402
import prompts  # noqa: E402


def _new_plan():
    return plan.new_plan("Test Brand")


def _cleanup(p):
    path = plan._path(p["id"])
    if os.path.isfile(path):
        os.remove(path)


# --- geo.py: town-class breakdown -----------------------------------------------------------------

def test_town_class_breakdown_sums_to_urban_total():
    for k in geo.URBAN_RURAL:
        bd = geo.town_class_breakdown(k)
        assert bd, f"{k} should have a breakdown"
        assert bd["metro"]["pop"] + bd["tier1"]["pop"] + bd["restofurban"]["pop"] == bd["urban_total"]
        assert not bd["data_quality_flag"], f"{k} rest-of-urban went negative"


def test_metro_is_a_named_list_not_a_threshold():
    mumbai = geo.town_class_breakdown("mh")
    assert any(c["name"] == "Mumbai" for c in mumbai["metro"]["cities"])
    jaipur = geo.town_class_breakdown("rj")
    # Jaipur is a large Class-I city but not one of the eight named metros.
    assert not any(c["name"] == "Jaipur" for c in jaipur["metro"]["cities"])
    assert any(c["name"] == "Jaipur" for c in jaipur["tier1"]["cities"])


def test_state_with_no_seeded_city_still_returns_an_aggregate():
    goa = geo.town_class_breakdown("ga")
    assert goa["metro"]["pop"] == 0 and goa["tier1"]["pop"] == 0
    assert goa["restofurban"]["pop"] == goa["urban_total"]


def test_unknown_state_returns_empty():
    assert geo.town_class_breakdown("not-a-state") == {}


# --- plan.py: set_geography ------------------------------------------------------------------------

def test_set_geography_drops_invalid_states_keeps_the_rest():
    p = _new_plan()
    try:
        p = plan.set_geography(p, [{"state": "not-a-state", "stratum": "urban"},
                                   {"state": "Maharashtra", "stratum": "urban", "town_class": "metro",
                                    "cities": ["Mumbai"]}])
        assert len(p["geography"]) == 1
        assert p["geography"][0]["state"] == "mh"
    finally:
        _cleanup(p)


def test_set_geography_dedupes_identical_rows():
    p = _new_plan()
    try:
        row = {"state": "mh", "stratum": "urban", "town_class": "metro", "cities": ["Mumbai"]}
        p = plan.set_geography(p, [dict(row, id="a"), dict(row, id="b")])
        assert len(p["geography"]) == 1
    finally:
        _cleanup(p)


def test_set_geography_defaults_unknown_town_class_to_restofurban():
    p = _new_plan()
    try:
        p = plan.set_geography(p, [{"state": "mh", "stratum": "urban", "town_class": "nonsense"}])
        assert p["geography"][0]["town_class"] == "restofurban"
    finally:
        _cleanup(p)


def test_set_geography_rural_row_carries_no_town_class_or_cities():
    p = _new_plan()
    try:
        p = plan.set_geography(p, [{"state": "mh", "stratum": "rural", "town_class": "metro",
                                    "cities": ["Mumbai"]}])
        row = p["geography"][0]
        assert row["stratum"] == "rural" and row["town_class"] == "" and row["cities"] == []
    finally:
        _cleanup(p)


# --- plan.py: geography_reach -----------------------------------------------------------------------

def test_reach_sums_only_the_selected_cities_not_the_whole_tier():
    # Nagpur is tier-1 (a seeded Maharashtra city, not one of the eight named metros) — Pune IS a named
    # metro (see METRO_CITIES) so it would be the wrong fixture for "not the whole tier1 total".
    p = _new_plan()
    try:
        p = plan.set_geography(p, [{"state": "mh", "stratum": "urban", "town_class": "tier1",
                                    "cities": ["Nagpur"]}])
        reach = plan.geography_reach(p)
        nagpur_pop = next(c["pop"] for c in geo.town_class_breakdown("mh")["tier1"]["cities"]
                          if c["name"] == "Nagpur")
        assert reach["total_population"] == nagpur_pop
        assert nagpur_pop < geo.town_class_breakdown("mh")["tier1"]["pop"]
    finally:
        _cleanup(p)


def test_reach_dedupes_the_same_city_picked_across_two_different_rows():
    p = _new_plan()
    try:
        p = plan.set_geography(p, [
            {"state": "mh", "stratum": "urban", "town_class": "tier1", "cities": ["Nagpur", "Nashik"]},
            {"state": "mh", "stratum": "urban", "town_class": "tier1", "cities": ["Nagpur"]},
        ])
        reach = plan.geography_reach(p)
        by_name = {c["name"]: c["pop"] for c in geo.town_class_breakdown("mh")["tier1"]["cities"]}
        assert reach["total_population"] == by_name["Nagpur"] + by_name["Nashik"]
    finally:
        _cleanup(p)


def test_reach_restofurban_and_rural_return_the_whole_aggregate():
    p = _new_plan()
    try:
        p = plan.set_geography(p, [
            {"state": "ga", "stratum": "urban", "town_class": "restofurban"},
            {"state": "ga", "stratum": "rural"},
        ])
        reach = plan.geography_reach(p)
        bd = geo.town_class_breakdown("ga")
        assert reach["total_population"] == bd["restofurban"]["pop"] + bd["rural"]["pop"]
    finally:
        _cleanup(p)


def test_reach_reports_a_per_state_breakdown_and_share():
    p = _new_plan()
    try:
        p = plan.set_geography(p, [
            {"state": "mh", "stratum": "urban", "town_class": "metro", "cities": ["Mumbai"]},
            {"state": "ka", "stratum": "urban", "town_class": "metro", "cities": ["Bengaluru"]},
        ])
        reach = plan.geography_reach(p)
        assert len(reach["by_state"]) == 2
        assert abs(sum(x["share"] for x in reach["by_state"]) - 100) < 0.2
    finally:
        _cleanup(p)


def test_reach_surfaces_language_gap_for_a_selected_state():
    p = _new_plan()
    try:
        # Goa's principal language is Konkani, which this studio holds no code for (geo.py's own data).
        p = plan.set_geography(p, [{"state": "ga", "stratum": "rural"}])
        reach = plan.geography_reach(p)
        assert any(g["state"] == "ga" for g in reach["language_gaps"])
    finally:
        _cleanup(p)


def test_reach_with_no_rows_is_zero_not_an_error():
    p = _new_plan()
    try:
        reach = plan.geography_reach(p)
        assert reach["total_population"] == 0
        assert reach["by_state"] == []
        assert reach["caveat"] == ""
    finally:
        _cleanup(p)


# --- execution.brief_from / prompts._execution_block (round 92, item 3 phase A) --------------------

def _save_synthetic_execution(brief):
    e = {"id": "test-exec-geo", "kind": "social", "plan": "x", "brief": brief, "status": "briefed"}
    return execution.save(e)


def _cleanup_execution(eid):
    path = execution._path(eid)
    if os.path.isfile(path):
        os.remove(path)


def test_execution_block_names_priority_states_and_asks_for_their_idiom():
    _save_synthetic_execution({
        "audience": {"audience": "Test audience"},
        "geography": {"by_state": [{"state": "mh", "label": "Maharashtra", "population": 100, "share": 100}],
                      "language_gaps": []},
    })
    try:
        block = prompts._execution_block("test-exec-geo")
        assert "Maharashtra" in block
        assert "idiom" in block
    finally:
        _cleanup_execution("test-exec-geo")


def test_execution_block_states_the_language_gap_plainly():
    _save_synthetic_execution({
        "audience": {"audience": "Test audience"},
        "geography": {"by_state": [{"state": "ga", "label": "Goa", "population": 100, "share": 100}],
                      "language_gaps": [{"state": "ga", "label": "Goa",
                                        "gap": "Konkani is the official language and the studio has "
                                               "no code for it."}]},
    })
    try:
        block = prompts._execution_block("test-exec-geo")
        assert "LANGUAGE GAP" in block
        assert "Konkani" in block
    finally:
        _cleanup_execution("test-exec-geo")


# --- plan.py approval gate (round 92, item 1) --------------------------------------------------

HIERARCHY = [{"level": 1, "title": "Brand Manager", "primary_user_id": "ravi", "backup_user_id": "meera"},
             {"level": 2, "title": "CMO", "primary_user_id": "ananya", "backup_user_id": ""}]


def test_submit_refuses_with_no_hierarchy():
    p = _new_plan()
    try:
        p2, err = plan.submit_for_approval(p, [], "puneet")
        assert p2 is None and "hierarchy" in err
    finally:
        _cleanup(p)


def test_submit_locks_the_plan_at_level_one():
    p = _new_plan()
    try:
        p, err = plan.submit_for_approval(p, HIERARCHY, "puneet")
        assert not err
        assert plan.is_locked(p)
        assert p["pending_approval"]["level"] == 1
        assert p["pending_approval"]["title"] == "Brand Manager"
    finally:
        _cleanup(p)


def test_approve_refuses_the_wrong_user():
    p = _new_plan()
    try:
        p, _ = plan.submit_for_approval(p, HIERARCHY, "puneet")
        p2, err = plan.approve(p, HIERARCHY, "ananya", "Ananya")  # ananya is level 2, not level 1
        assert p2 is None
        assert "not the assigned approver" in err
    finally:
        _cleanup(p)


def test_approve_accepts_the_backup_and_advances_to_next_level():
    p = _new_plan()
    try:
        p, _ = plan.submit_for_approval(p, HIERARCHY, "puneet")
        p, err = plan.approve(p, HIERARCHY, "meera", "Meera")  # meera is level 1's backup
        assert not err
        assert plan.is_locked(p)
        assert p["pending_approval"]["level"] == 2
    finally:
        _cleanup(p)


def test_approve_at_last_level_fully_approves_and_unlocks():
    p = _new_plan()
    try:
        p, _ = plan.submit_for_approval(p, HIERARCHY, "puneet")
        p, _ = plan.approve(p, HIERARCHY, "ravi", "Ravi")
        p, err = plan.approve(p, HIERARCHY, "ananya", "Ananya")
        assert not err
        assert not plan.is_locked(p)
        assert p["status"] == "approved"
        assert len(p["approval_log"]) == 3  # submitted + 2 approvals
    finally:
        _cleanup(p)


def test_reject_requires_a_reason_and_unlocks_on_success():
    p = _new_plan()
    try:
        p, _ = plan.submit_for_approval(p, HIERARCHY, "puneet")
        p2, err = plan.reject(p, "ravi", "Ravi", "")
        assert p2 is None and "why" in err
        p, err = plan.reject(p, "ravi", "Ravi", "Balance doesn't reconcile.")
        assert not err
        assert not plan.is_locked(p)
        assert p["status"] == "draft"
    finally:
        _cleanup(p)


def test_execution_block_omits_geography_lines_when_plan_has_none():
    _save_synthetic_execution({"audience": {"audience": "Test audience"}})
    try:
        block = prompts._execution_block("test-exec-geo")
        assert "Priority geography" not in block
        assert "LANGUAGE GAP" not in block
    finally:
        _cleanup_execution("test-exec-geo")
