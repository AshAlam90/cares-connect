"""
The single entry point of the calculation engine: run_design().

Everything numerical in the app comes from here. Any future AI assistant
would call this function (as a tool) and only explain its output; it would
never produce costs or paybacks itself.

Money is in the local currency of the design's country (Tk or Rs).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import irrigation as irr
from .addons import AddonSpec
from .countries import COUNTRIES
from .solar import DAYS_IN_MONTH, MONTHS, PVSpec, SiteClimate, monthly_pv

CO2_KG_PER_LITRE_DIESEL = 2.68
PEOPLE_PER_HOUSEHOLD = 4.0


@dataclass
class CostInputs:
    pv_per_kwp: float = 65_000
    pump_per_kw: float = 25_000
    fixed_install: float = 450_000          # civil works, borewell, transport
    distribution_per_ha: float = 15_000     # pipes / channels / drip lines
    solar_om_per_year: float = 35_000
    controller_replacement_year: int = 10
    controller_replacement_cost: float = 150_000


@dataclass
class FinanceInputs:
    diesel_price_per_l: float = 110
    diesel_escalation: float = 0.05
    diesel_fuel_to_water_eff: float = 0.15
    diesel_maintenance_per_year: float = 30_000
    discount_rate: float = 0.10
    lifetime_years: int = 20
    funder_grant_share: float = 0.70        # share of capex paid by funders
    cares_design_fee: float = 0.05          # one-off commission paid by funders
    cares_mgmt_share: float = 0.05          # share of yearly net benefit to CARES


@dataclass
class DesignInputs:
    lat: float
    lon: float
    country: str = "BD"
    households: int = 100                   # 0 = not known
    area_ha: float = 15.0
    pattern: str = "boro_aman"
    head_m: float = 18.0
    wire_to_water_eff: float = 0.50
    pump_kw: float = 13.0
    pv: PVSpec = field(default_factory=PVSpec)
    addons: list[AddonSpec] = field(default_factory=list)   # in priority order
    grid_scheme: str = "none"               # none | export_surplus | net_plus
    grid_tariff: float = 4.0                # price received per kWh sold
    grid_tariff_after: float = 4.0          # price after the switch year (older Net-Plus contracts)
    grid_tariff_switch_year: int = 0        # 0 = no change over the lifetime
    grid_buy_price: float = 0.0             # price paid per kWh bought (Net-Plus loads)
    women_share_committee: float = 0.40
    costs: CostInputs = field(default_factory=CostInputs)
    finance: FinanceInputs = field(default_factory=FinanceInputs)


def defaults_for(country: str, lat: float, lon: float, **overrides) -> DesignInputs:
    """A design with the country's default costs, finance and grid rules."""
    c = COUNTRIES[country]
    costs = dict(c["costs"])
    inverter_per_kw = costs.pop("inverter_per_kw", 0)
    di = DesignInputs(lat=lat, lon=lon, country=country,
                      costs=CostInputs(**costs), finance=FinanceInputs(**c["finance"]), **c["grid"])
    di.pv.system_losses = c["pv_losses"]
    for k, v in overrides.items():
        setattr(di, k, v)
    if inverter_per_kw:
        di.costs.controller_replacement_cost = inverter_per_kw * di.pv.kwp
    return di


def design_from_dict(d: dict) -> DesignInputs:
    d = dict(d)
    d["pv"] = PVSpec(**d.get("pv", {}))
    d["addons"] = [AddonSpec(**a) for a in d.get("addons", [])]
    d["costs"] = CostInputs(**d.get("costs", {}))
    d["finance"] = FinanceInputs(**d.get("finance", {}))
    return DesignInputs(**d)


def design_to_dict(di: DesignInputs) -> dict:
    return asdict(di)


def suggest_system(area_ha: float, pattern: str, head_m: float,
                   wire_to_water_eff: float = 0.5, pumping_hours: float = 8.0,
                   pv_to_pump_ratio: float = 2.0) -> tuple[float, float]:
    """First-guess pump (kW) and array (kWp) sizes for the peak irrigation month.

    Pump: peak-month electrical demand spread over `pumping_hours` a day.
    Array: a multiple of pump power, in line with solar pumps in Bangladesh
    (roughly 1.6-2.4 kWp per kW of pump). CARES staff refine both by hand.
    """
    water = irr.monthly_water_m3(area_ha, pattern)
    peak = max(irr.pump_electric_kwh(w, head_m, wire_to_water_eff) / d
               for w, d in zip(water, DAYS_IN_MONTH))
    pump_kw = max(2.0, round(peak / pumping_hours * 2) / 2)
    pv_kwp = round(pump_kw * pv_to_pump_ratio, 1)
    return pump_kw, pv_kwp


# ------------------------------------------------------------- energy balance
def energy_balance(di: DesignInputs, climate: SiteClimate) -> dict:
    """Month by month: where the solar energy goes, and what is bought from the grid.

    - none / export_surplus: solar serves the pump first, then add-ons in priority
      order; what is left is sold (export_surplus) or unused (none).
    - net_plus: every solar kWh is sold to the grid; the pump and add-ons buy
      their electricity from the grid (the Sri Lankan Net-Plus arrangement).
    """
    pv = monthly_pv(climate, di.pv)
    water = irr.monthly_water_m3(di.area_ha, di.pattern)
    net_plus = di.grid_scheme == "net_plus"
    rows = []
    for m in range(12):
        pv_kwh = pv["pv_kwh"][m]
        demand = irr.pump_electric_kwh(water[m], di.head_m, di.wire_to_water_eff)
        pump_cap = di.pump_kw * 10 * DAYS_IN_MONTH[m]       # ~10 pumping hours/day max
        served = min(demand, pump_cap) if net_plus else min(demand, pv_kwh, pump_cap)
        row = {"month": MONTHS[m], "pv_kwh": pv_kwh, "pump_demand_kwh": demand,
               "pump_served_kwh": served, "unmet_kwh": demand - served, "water_m3": water[m]}
        remaining = pv_kwh - (0.0 if net_plus else served)
        bought = served if net_plus else 0.0
        for a in di.addons:
            want = a.kwh_per_day * DAYS_IN_MONTH[m] if (m + 1) in a.months else 0.0
            if net_plus:
                used = want
                bought += used
            else:
                used = min(remaining, want)
                remaining -= used
            row[f"addon:{a.key}"] = used
        if net_plus:
            row["grid_export_kwh"], row["unused_kwh"] = pv_kwh, 0.0
        elif di.grid_scheme == "export_surplus":
            row["grid_export_kwh"], row["unused_kwh"] = remaining, 0.0
        else:
            row["grid_export_kwh"], row["unused_kwh"] = 0.0, remaining
        row["grid_import_kwh"] = bought
        rows.append(row)
    return {"rows": rows, "pv_detail": pv}


# ------------------------------------------------------------- finance
def payback_from_cashflows(initial: float, flows: list[float]) -> float | None:
    """Years until cumulative cash turns positive, interpolated within the year."""
    cum = -initial
    for i, f in enumerate(flows, start=1):
        if cum + f >= 0:
            return i - 1 + (-cum / f if f > 0 else 0)
        cum += f
    return None


def npv(rate: float, initial: float, flows: list[float]) -> float:
    return -initial + sum(f / (1 + rate) ** t for t, f in enumerate(flows, start=1))


def tariff_in_year(di: DesignInputs, year: int) -> float:
    if di.grid_tariff_switch_year and year > di.grid_tariff_switch_year:
        return di.grid_tariff_after
    return di.grid_tariff


def run_design(di: DesignInputs, climate: SiteClimate) -> dict:
    eb = energy_balance(di, climate)
    rows = eb["rows"]
    c, f = di.costs, di.finance

    # --- annual energy totals
    tot = lambda k: sum(r[k] for r in rows)
    pv_total = tot("pv_kwh")
    served_total = tot("pump_served_kwh")
    unmet_total = tot("unmet_kwh")
    export_total = tot("grid_export_kwh")
    import_total = tot("grid_import_kwh")
    unused_total = tot("unused_kwh")
    addon_kwh = {a.key: tot(f"addon:{a.key}") for a in di.addons}

    # --- diesel avoided (only water the new pump actually lifts)
    hydraulic_served = served_total * di.wire_to_water_eff
    diesel_l = irr.diesel_litres_for_hydraulic(hydraulic_served, f.diesel_fuel_to_water_eff)
    co2_t = diesel_l * CO2_KG_PER_LITRE_DIESEL / 1000

    # --- capital costs
    capex_solar = (di.pv.kwp * c.pv_per_kwp + (di.pump_kw * c.pump_per_kw if di.area_ha > 0 else 0)
                   + c.fixed_install + di.area_ha * c.distribution_per_ha)
    capex_addons = sum(a.capex for a in di.addons)
    capex = capex_solar + capex_addons
    cares_design_fee = capex * f.cares_design_fee
    grant = capex * f.funder_grant_share
    community_share = capex - grant
    funder_total = grant + cares_design_fee

    # --- yearly cash flows
    addon_income = sum(addon_kwh[a.key] * a.income_per_kwh for a in di.addons)
    addon_om = sum(a.om_per_year for a in di.addons)
    import_cost = import_total * di.grid_buy_price
    diesel_share = served_total / (served_total + unmet_total) if (served_total + unmet_total) else 0
    flows, mgmt_fees, rows_cf = [], [], []
    for y in range(1, f.lifetime_years + 1):
        diesel_cost = diesel_l * f.diesel_price_per_l * (1 + f.diesel_escalation) ** (y - 1)
        diesel_maint = f.diesel_maintenance_per_year * diesel_share if di.area_ha > 0 else 0.0
        export_income = export_total * tariff_in_year(di, y)
        gross = (diesel_cost + diesel_maint + addon_income + export_income
                 - c.solar_om_per_year - addon_om - import_cost)
        mgmt = max(0.0, gross) * f.cares_mgmt_share
        net = gross - mgmt
        if y == c.controller_replacement_year:
            net -= c.controller_replacement_cost
        flows.append(net)
        mgmt_fees.append(mgmt)
        rows_cf.append({"year": y, "diesel_saving": diesel_cost + diesel_maint,
                        "grid_income": export_income, "addon_income": addon_income,
                        "running_costs": c.solar_om_per_year + addon_om + import_cost,
                        "cares_fee": mgmt, "net": net})

    simple_pb = capex / flows[0] if flows[0] > 0 else None
    disc_flows = [x / (1 + f.discount_rate) ** t for t, x in enumerate(flows, start=1)]
    disc_pb = payback_from_cashflows(capex, disc_flows)
    project_npv = npv(f.discount_rate, capex, flows)
    community_pb = payback_from_cashflows(community_share, flows) if community_share > 0 else 0.0
    cum, cum_list = -capex, []
    for x in flows:
        cum += x
        cum_list.append(cum)

    # --- impact
    jobs = sum(a.jobs for a in di.addons) + (1 if di.area_ha > 0 else 0)
    sdgs = {7, 13}
    if di.area_ha > 0:
        sdgs.add(2)
    if di.grid_scheme == "net_plus":
        sdgs.update({1, 11})                # income for the community; sustainable communities
    for a in di.addons:
        sdgs.update(a.sdgs)
    if di.women_share_committee >= 0.3:
        sdgs.add(5)
    # CO2: diesel replaced plus grid electricity displaced by exported solar
    grid_ef = GRID_EF_KG_PER_KWH.get(di.country, 0.0)
    co2_t += export_total * grid_ef / 1000
    lifetime_co2 = co2_t * f.lifetime_years

    return {
        "monthly": rows,
        "pv_detail": eb["pv_detail"],
        "climate_source": climate.source,
        "climate_note": climate.note,
        "climate": {"lat": climate.lat, "lon": climate.lon, "ghi": climate.ghi, "t2m": climate.t2m,
                    "source": climate.source, "note": climate.note},
        "energy": {
            "pv_kwh": pv_total, "pv_kwh_per_month": pv_total / 12,
            "specific_yield_kwh_per_kwp": pv_total / di.pv.kwp,
            "pump_served_kwh": served_total, "pump_unmet_kwh": unmet_total,
            "addon_kwh": addon_kwh, "grid_export_kwh": export_total, "grid_import_kwh": import_total,
            "unused_kwh": unused_total,
            "irrigation_share": served_total / pv_total if pv_total and di.grid_scheme != "net_plus" else 0,
            "utilisation": (pv_total - unused_total) / pv_total if pv_total else 0,
            "deficit_months": [r["month"] for r in rows if r["unmet_kwh"] > 1],
        },
        "finance": {
            "capex_solar": capex_solar, "capex_addons": capex_addons, "capex": capex,
            "grant": grant, "community_share": community_share,
            "cares_design_fee": cares_design_fee, "funder_total": funder_total,
            "year1_net": flows[0], "addon_income": addon_income,
            "grid_income_year1": rows_cf[0]["grid_income"], "grid_cost_year1": import_cost,
            "simple_payback": simple_pb, "discounted_payback": disc_pb,
            "community_payback": community_pb, "npv": project_npv,
            "cares_mgmt_year1": mgmt_fees[0], "cares_income_lifetime": cares_design_fee + sum(mgmt_fees),
            "cashflow": rows_cf, "cumulative": cum_list,
        },
        "impact": {
            "diesel_l": diesel_l, "co2_t": co2_t, "lifetime_co2_t": lifetime_co2,
            "households": di.households, "people": di.households * PEOPLE_PER_HOUSEHOLD,
            "jobs": jobs, "women_share_committee": di.women_share_committee,
            "sdgs": sorted(sdgs),
            "grant_per_household": grant / di.households if di.households else None,
            "grant_per_t_co2": grant / lifetime_co2 if lifetime_co2 else None,
        },
    }


# Grid emission factors used to credit exported solar (kg CO2 per kWh).
# Sri Lanka's grid relies heavily on coal and oil; 0.6 is an assumed round
# figure to be replaced with the official factor.
GRID_EF_KG_PER_KWH = {"LK": 0.6}
