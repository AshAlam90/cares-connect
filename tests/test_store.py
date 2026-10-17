"""Checks the seeded real sites and the request -> design -> pledge cycle."""
import pytest

from app_core import real_sites as RS
from app_core import store


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test.db")
    store.init_db()


def test_every_real_site_is_seeded_with_sources():
    real = [p for p in store.list_projects() if p["kind"] == "real"]
    assert len(real) == len(RS.SITES) + len(RS.PROPOSED)
    for p in real:
        assert p["facts"]["sources"], p["village"]
        for _, url in p["facts"]["sources"]:
            assert url.startswith("https://")


def test_only_sites_with_published_size_are_modelled():
    for p in store.list_projects():
        if p["kind"] == "real" and not p["village"].startswith("Proposed"):
            site = next(s for s in RS.SITES if s["village"] == p["village"])
            assert bool(p["results"]) == bool(site["kw"])
            if site["kw"]:
                assert p["design"]["pv"]["kwp"] == site["kw"]


def test_published_costs_are_used():
    nochchiya = next(p for p in store.list_projects() if p["village"] == "Nochchiya")
    assert nochchiya["results"]["finance"]["capex"] == pytest.approx(1_800_000)
    assert nochchiya["design"]["grid_tariff_switch_year"] == 7


def test_no_pledges_are_invented_for_real_sites():
    for p in store.list_projects():
        if p["kind"] == "real":
            assert store.pledges_for(p["id"]) == []


def test_demo_profiles_are_marked_fictional():
    for u in store.list_users():
        assert "(fictional)" in u["organisation"] or "(demo)" in u["name"]


def test_request_design_pledge_cycle_in_sri_lanka():
    community = store.add_user("community", "Test", "Test village committee", country="LK", village="Test",
                               district="Anuradhapura")
    ref = store.add_request(dict(country="LK", village="Test", district="Anuradhapura", lat=8.31, lon=80.40,
                                 households=80, area_local=0, needs=["Community income from a solar roof",
                                                                     "Drinking water"],
                                 submitted_by="Village Development Committee"), user_id=community)
    pid = int(ref.split("-")[-1])
    p = store.get_project(pid)
    unit = store.cares_unit_for("Anuradhapura", "LK")
    from engine import design_to_dict, fallback_climate, run_design
    di = store.default_design_for(p)
    assert di.grid_scheme == "net_plus" and di.pv.kwp == 5.0 and [a.key for a in di.addons] == ["water_lk"]
    res = run_design(di, fallback_climate(p["lat"], p["lon"], country="LK"))
    store.save_design(pid, design_to_dict(di), res, publish=True, cares_unit=unit["organisation"],
                      cares_user_id=unit["id"])
    assert store.get_project(pid)["status"] == "Published"
    funder = store.list_users("funder")[0]
    target = res["finance"]["funder_total"]
    assert store.add_pledge(pid, funder["organisation"], funder["funder_type"], target / 2, funder["id"]) == "Partly funded"
    assert store.add_pledge(pid, funder["organisation"], funder["funder_type"], target / 2, funder["id"]) == "Funded"
