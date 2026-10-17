"""Checks that the engine's physics and arithmetic are right."""
import math

import pytest

from engine import DesignInputs, fallback_climate, run_design
from engine import irrigation as irr
from engine import solar
from engine.addons import default_addons_for_needs
from engine.model import npv, payback_from_cashflows


# ------------------------------------------------------------ solar geometry
def test_declination_at_june_solstice():
    assert solar.declination_deg(172) == pytest.approx(23.45, abs=0.05)


def test_extraterrestrial_at_equator_equinox():
    # H0 = (24/pi) * 1.367 * (1+0.033cos) * 1  ~= 10.4 kWh/m2/day
    assert solar.extraterrestrial_daily_kwh(0.0, 81) == pytest.approx(10.4, abs=0.15)


def test_flat_panel_receives_horizontal_irradiation():
    for m, n in enumerate(solar.KLEIN_DAYS):
        h = solar.FALLBACK_GHI[m]
        assert solar.tilted_daily_kwh(h, 23.9, 0.0, n, albedo=0.2) == pytest.approx(h, rel=1e-9)


def test_tilt_helps_in_winter_not_summer():
    lat = 23.9
    winter = solar.tilted_daily_kwh(4.0, lat, 24, solar.KLEIN_DAYS[11]) / 4.0
    summer = solar.tilted_daily_kwh(4.55, lat, 24, solar.KLEIN_DAYS[5]) / 4.55
    assert winter > 1.15 and summer < 1.0


def test_specific_yield_is_realistic_for_bangladesh():
    c = fallback_climate(23.9, 89.1)
    pv = solar.monthly_pv(c, solar.PVSpec(kwp=1.0))
    assert 1250 < sum(pv["pv_kwh"]) < 1600


# ------------------------------------------------------------ water and diesel
def test_hydraulic_energy_hand_check():
    # 1,000 m3 lifted 10 m = 1000*9.81*1000*10 J = 27.25 kWh
    assert irr.hydraulic_kwh(1000, 10) == pytest.approx(27.25, abs=0.01)


def test_bigha_conversion():
    assert 7.475 * irr.HECTARE_PER_BIGHA == pytest.approx(1.0)


def test_diesel_litres():
    # 12 kWh of hydraulic work at 15% fuel-to-water efficiency, 10 kWh/L -> 8 L
    assert irr.diesel_litres_for_hydraulic(12, 0.15) == pytest.approx(8.0)


# ------------------------------------------------------------ finance helpers
def test_payback_interpolates_within_year():
    assert payback_from_cashflows(2_500_000, [428_500] * 10) == pytest.approx(5.834, abs=0.001)


def test_payback_never():
    assert payback_from_cashflows(100, [1, 1, 1]) is None


def test_npv_simple_case():
    assert npv(0.10, 100, [110]) == pytest.approx(0.0)


# ------------------------------------------------------------ whole model
@pytest.fixture
def result():
    c = fallback_climate(23.9, 89.12)
    di = DesignInputs(lat=23.9, lon=89.12, households=120,
                      addons=default_addons_for_needs(["Cold storage", "E-rickshaw charging"]))
    return di, run_design(di, c)


def test_energy_balance_closes_every_month(result):
    di, r = result
    for row in r["monthly"]:
        used = (row["pump_served_kwh"] + row["grid_export_kwh"] + row["unused_kwh"]
                + sum(row[f"addon:{a.key}"] for a in di.addons))
        assert used == pytest.approx(row["pv_kwh"], rel=1e-9)


def test_pump_never_serves_more_than_demand(result):
    _, r = result
    for row in r["monthly"]:
        assert row["pump_served_kwh"] <= row["pump_demand_kwh"] + 1e-9


def test_capex_adds_up(result):
    di, r = result
    f, c = r["finance"], di.costs
    solar_capex = (di.pv.kwp * c.pv_per_kwp + di.pump_kw * c.pump_per_kw
                   + c.fixed_install + di.area_ha * c.distribution_per_ha)
    assert f["capex_solar"] == pytest.approx(solar_capex)
    assert f["grant"] + f["community_share"] == pytest.approx(f["capex"])


def test_more_expensive_diesel_shortens_payback():
    c = fallback_climate(23.9, 89.12)
    base = DesignInputs(lat=23.9, lon=89.12)
    dear = DesignInputs(lat=23.9, lon=89.12)
    dear.finance.diesel_price_per_l = 150
    assert run_design(dear, c)["finance"]["simple_payback"] < run_design(base, c)["finance"]["simple_payback"]


def test_co2_matches_diesel(result):
    _, r = result
    assert r["impact"]["co2_t"] == pytest.approx(r["impact"]["diesel_l"] * 2.68 / 1000)


# ------------------------------------------------------------ Sri Lanka Net-Plus
def test_net_plus_sells_all_solar_and_buys_loads():
    from engine import defaults_for
    from engine.addons import default_addons_for_needs
    c = fallback_climate(8.31, 80.40, country="LK")
    di = defaults_for("LK", 8.31, 80.40, area_ha=0.0, pattern="none",
                      addons=default_addons_for_needs(["Drinking water"], "LK"))
    di.pv.kwp = 5.0
    r = run_design(di, c)
    for row in r["monthly"]:
        assert row["grid_export_kwh"] == pytest.approx(row["pv_kwh"])
        assert row["grid_import_kwh"] == pytest.approx(row["addon:water_lk"])
    # year-1 grid income = all solar output x Rs 37
    assert r["finance"]["grid_income_year1"] == pytest.approx(r["energy"]["pv_kwh"] * 37)


def test_five_kw_roof_output_close_to_field_reports():
    """Solar Village report: a 5 kW roof makes 500-600 kWh a month. Allow 15% model margin."""
    from engine import defaults_for
    c = fallback_climate(7.82, 80.28, country="LK")
    di = defaults_for("LK", 7.82, 80.28, area_ha=0.0, pattern="none")
    di.pv.kwp = 5.0
    monthly = run_design(di, c)["energy"]["pv_kwh_per_month"]
    assert 500 * 0.85 < monthly < 600 * 1.15


def test_old_net_plus_contract_switches_tariff():
    from engine import defaults_for
    from engine.model import tariff_in_year
    di = defaults_for("LK", 8.0, 80.5, grid_tariff=22.0, grid_tariff_after=15.0, grid_tariff_switch_year=7)
    assert tariff_in_year(di, 7) == 22.0 and tariff_in_year(di, 8) == 15.0


def test_inverter_replacement_scales_with_roof_size():
    from engine import defaults_for
    from engine.solar import PVSpec
    di = defaults_for("LK", 8.0, 80.5, pv=PVSpec(kwp=5.0))
    assert di.costs.controller_replacement_cost == pytest.approx(375_000)
