import copy

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app_core import auth, store, ui
from app_core.climate import climate_for
from app_core.summary import summary
from engine import (COUNTRIES, GRID_SCHEMES, CostInputs, DesignInputs, FinanceInputs, PVSpec, SiteClimate,
                    design_from_dict, design_to_dict, run_design)
from engine.addons import CATALOG, AddonSpec, catalog_for
from engine.irrigation import PATTERNS, patterns_for
from engine.model import suggest_system
from engine.solar import MONTHS

st.title("CARES: design a solution")
st.write("For the local university team. Open a request, adjust the design using what you know about the place, "
         "check the business case, then publish it for funders. Real sites open as *as-built* models.")
ui.disclaimer()

user = auth.current_user()
is_cares = bool(user and user["role"] == "cares")
projects = store.list_projects()
if is_cares:
    cov = set(user["coverage"] or [])
    st.caption(f"Signed in as **{user['organisation']}** · covering {', '.join(sorted(cov)) if len(cov) < 12 else str(len(cov)) + ' districts'}")
    if st.toggle("Only my districts", value=True, key="cares_only_mine"):
        projects = [p for p in projects if (p["country"] == user["country"] and p["district"] in cov)
                    or p["cares_user_id"] == user["id"]]
else:
    st.page_link("views/account.py", icon=":material/login:",
                 label="Sign in as a CARES unit to save and publish designs (you can explore without signing in)")
if not projects:
    st.info("No requests in your districts yet. Switch off *Only my districts* to see everything.")
    st.stop()

labels = {p["id"]: f"{p['ref']} · {ui.place(p) if p['district'] else p['village'] + ' · ' + COUNTRIES[p['country']]['name']}"
                    f" · {p['status']}" for p in projects}
ids = list(labels)
if "cares_open" in st.session_state:                     # sent here from a dashboard
    st.session_state["cares_select"] = st.session_state.pop("cares_open")
if st.session_state.get("cares_select") not in ids:
    mine = [p["id"] for p in projects if p["ref"] in st.session_state.get("my_refs", [])]
    st.session_state["cares_select"] = mine[-1] if mine else next(
        (p["id"] for p in projects if p["status"] == "New request"), ids[0])
pid = st.selectbox("Request", ids, format_func=labels.get, key="cares_select")
p = store.get_project(pid)
k = lambda name: f"{name}_{pid}"
cc = p["country"]
C = COUNTRIES[cc]
CUR = C["currency"]
as_built = p["kind"] == "real" and p["status"] in ("Operating", "Funded")
locked = p["status"] in ("Partly funded", "Funded", "Operating")

# ------------------------------------------------------------------ the request
with st.container(border=True):
    facts = p["facts"] or {}
    a, b, c, d = st.columns(4)
    a.markdown(f"**{p['village']}**  \n{p['district'] or 'District not published'}, {C['name']}")
    hh = f"{p['households']} households" if p["households"] else "Households not published"
    area_txt = (f"{p['area_local']:g} {C['land_unit']}s (≈ {p['area_local'] * C['ha_per_land_unit']:.1f} ha)"
                if p["area_local"] else "No irrigation area given")
    b.markdown(f"**{hh}**  \n{area_txt}")
    c.markdown(f"**Needs:** {', '.join(p['needs']) or '—'}  \n**Crops:** {', '.join(p['crops'] or []) or '—'}")
    d.markdown(f"**Water:** {p['water_source'] or '—'}  \n**Pump now:** {p['current_pump'] or '—'}"
               + (f", {CUR} {p['energy_spend_month']:,.0f}/month" if p["energy_spend_month"] else ""))
    st.caption(f"From: {p['submitted_by']} · Status: {ui.status_badge(p['status'])} · Location: {p['precision']}"
               + (f" · Note: {p['notes']}" if p["notes"] else ""))
    if p["kind"] == "real":
        if not p["village"].startswith("Proposed"):
            st.markdown(f"**Published facts:** {facts.get('system') or ''} {facts.get('funders') or ''}")
        st.caption("Sources: " + ui.sources_md(facts.get("sources")))

if as_built and not p["design"]:
    st.info("This real site's system size is not published, so it is not modelled. "
            "See its facts on the Real solar villages page.")
    st.page_link("views/villages.py", label="Real solar villages", icon=":material/solar_power:")
    st.stop()
if as_built:
    st.info("**As-built model of a real site**: published size and cost, with the tariff assumption noted. "
            "You can explore changes, but they can't be saved. " + (facts.get("tariff_note") or ""))

base = design_from_dict(p["design"]) if p["design"] else store.default_design_for(p)
base_addons = {a.key: a for a in base.addons}
lat, lon, loc_note = store.model_point(p)

tabs = st.tabs(["1 · Site & solar", "2 · Water & irrigation", "3 · Uses & the grid",
                "4 · Costs & funding", "5 · Results & publish"])

# ================================================================== inputs
with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    live = c1.toggle("Live NASA POWER data", value=True, key=k("live"))
    st.session_state.setdefault(k("kwp"), float(base.pv.kwp))
    kwp = c2.number_input("Solar array (kWp)", 1.0, 500.0, step=0.5, key=k("kwp"))
    tilt = c3.slider("Panel tilt (°, facing south)", 0, 45,
                     int(base.pv.tilt_deg if base.pv.tilt_deg is not None else round(abs(lat))), key=k("tilt"))
    losses = c4.slider("Other losses", 0.05, 0.40, float(base.pv.system_losses), 0.01, key=k("loss"),
                       help="Wiring, dust, shading, orientation, downtime. Sri Lanka uses 26%, calibrated "
                            "against reported output of real 5 kW roofs.")

with tabs[1]:
    def _suggest():
        pump_kw_s, kwp_s = suggest_system(st.session_state[k("area")], st.session_state[k("pattern")],
                                          st.session_state[k("head")], st.session_state[k("eff")])
        st.session_state[k("pump")] = pump_kw_s
        st.session_state[k("kwp")] = max(kwp_s, st.session_state[k("kwp")]) if base.grid_scheme == "net_plus" else kwp_s

    irrigate = st.toggle("Include solar irrigation", value=base.area_ha > 0, key=k("irr"))
    pats = patterns_for(cc)
    c1, c2, c3 = st.columns(3)
    area = c1.number_input(f"Irrigated area (ha) · 1 {C['land_unit']} = {C['ha_per_land_unit']:.3f} ha", 0.0, 500.0,
                           float(base.area_ha) if base.area_ha > 0 else 4.0, 0.5, key=k("area"), disabled=not irrigate)
    pat_opts = [x for x in pats if x != "none"]
    pattern = c2.selectbox("Cropping pattern", pat_opts,
                           index=pat_opts.index(base.pattern) if base.pattern in pat_opts else 0,
                           format_func=lambda x: PATTERNS[x]["label"], key=k("pattern"), disabled=not irrigate)
    head = c3.slider("Total pumping head (m)", 2.0, 60.0, float(base.head_m), 0.5, key=k("head"), disabled=not irrigate,
                     help="Lift from the water level plus pipe losses.")
    c4, c5 = st.columns(2)
    eff = c4.slider("Pump wire-to-water efficiency", 0.30, 0.70, float(base.wire_to_water_eff), 0.01, key=k("eff"),
                    disabled=not irrigate)
    st.session_state.setdefault(k("pump"), float(base.pump_kw) if base.pump_kw else 3.0)
    pump_kw = c5.number_input("Pump size (kW)", 0.5, 100.0, step=0.5, key=k("pump"), disabled=not irrigate)
    st.button("Suggest pump and array sizes", on_click=_suggest, icon=":material/auto_fix_high:", disabled=not irrigate,
              help="Sizes the pump for the busiest irrigation month (8 pumping hours a day) and the array at "
                   "2 kWp per kW of pump.")
    if not irrigate:
        area, pattern, pump_kw = 0.0, "none", 0.0

with tabs[2]:
    st.write("Pick productive uses in **priority order**. With *use solar first*, spare energy goes to the first one first.")
    options = catalog_for(cc)
    chosen = st.multiselect("Productive uses", options, default=[a.key for a in base.addons if a.key in options],
                            format_func=lambda x: CATALOG[x].name, key=k("addons"))
    addon_specs: list[AddonSpec] = []
    for key in chosen:
        src = base_addons.get(key, CATALOG[key])
        with st.expander(f"{CATALOG[key].name}: settings", expanded=False):
            st.caption(CATALOG[key].note)
            e1, e2, e3, e4 = st.columns(4)
            capex_a = e1.number_input(f"Equipment cost ({CUR})", 0, 50_000_000, int(src.capex), 10_000, key=k(f"{key}_capex"))
            kwh_a = e2.number_input("Energy per working day (kWh)", 0.5, 1000.0, float(src.kwh_per_day), 0.5, key=k(f"{key}_kwh"))
            inc_a = e3.number_input(f"Net income per working day ({CUR})", 0, 500_000, int(src.income_per_day), 50, key=k(f"{key}_inc"))
            om_a = e4.number_input(f"Running costs per year ({CUR})", 0, 5_000_000, int(src.om_per_year), 1_000, key=k(f"{key}_om"))
            months_a = st.multiselect("Months it runs", list(range(1, 13)), default=src.months,
                                      format_func=lambda m: MONTHS[m - 1], key=k(f"{key}_months"))
        addon_specs.append(AddonSpec(key=key, name=CATALOG[key].name, name_bn=CATALOG[key].name_bn, capex=capex_a,
                                     kwh_per_day=kwh_a, income_per_day=inc_a, om_per_year=om_a,
                                     months=sorted(months_a), jobs=CATALOG[key].jobs, sdgs=CATALOG[key].sdgs,
                                     note=CATALOG[key].note, country=cc))
    st.markdown("**Grid connection**")
    g0, g1, g2, g3, g4 = st.columns([3, 1, 1, 1, 1])
    scheme = g0.selectbox("How solar output is used", list(GRID_SCHEMES), index=list(GRID_SCHEMES).index(base.grid_scheme),
                          format_func=GRID_SCHEMES.get, key=k("scheme"))
    off = scheme == "none"
    tariff = g1.number_input(f"Sale price ({CUR}/kWh)", 0.0, 100.0, float(base.grid_tariff), 0.5, key=k("tariff"), disabled=off)
    switch = g2.number_input("Price changes after year", 0, 25, int(base.grid_tariff_switch_year), 1, key=k("switch"),
                             disabled=off, help="0 = no change. Older Net-Plus contracts: Rs 22 for 7 years, then Rs 15.")
    after = g3.number_input(f"Then ({CUR}/kWh)", 0.0, 100.0, float(base.grid_tariff_after), 0.5, key=k("after"),
                            disabled=off or switch == 0)
    buy = g4.number_input(f"Buying price ({CUR}/kWh)", 0.0, 100.0, float(base.grid_buy_price), 0.5, key=k("buy"),
                          disabled=scheme != "net_plus", help="What the village pays for electricity it uses under Net-Plus")

with tabs[3]:
    bc, bf = base.costs, base.finance
    st.markdown(f"**Equipment and running costs** ({CUR}; Sri Lankan solar costs from the Solar Village report, "
                "the rest illustrative)")
    c1, c2, c3, c4 = st.columns(4)
    pv_cost = c1.number_input(f"Solar array ({CUR} per kWp, installed)", 1_000, 1_000_000, int(bc.pv_per_kwp), 1_000, key=k("pvc"))
    pump_cost = c2.number_input(f"Pump & controller ({CUR} per kW)", 0, 500_000, int(bc.pump_per_kw), 1_000, key=k("pc"))
    fixed = c3.number_input(f"Civil works, well, transport ({CUR})", 0, 50_000_000, int(bc.fixed_install), 10_000, key=k("fix"))
    dist = c4.number_input(f"Water distribution ({CUR} per ha)", 0, 1_000_000, int(bc.distribution_per_ha), 1_000, key=k("dist"))
    c5, c6, c7 = st.columns(3)
    om = c5.number_input(f"Solar upkeep and cleaning ({CUR}/yr)", 0, 5_000_000, int(bc.solar_om_per_year), 1_000, key=k("om"))
    repl = c6.number_input(f"Inverter/controller replacement in year 10 ({CUR})", 0, 20_000_000,
                           int(bc.controller_replacement_cost), 5_000, key=k("repl"))
    life = c7.slider("Lifetime (years)", 10, 25, int(bf.lifetime_years), key=k("life"))
    if irrigate:
        st.markdown("**Diesel being replaced**")
        d1, d2, d3, d4 = st.columns(4)
        diesel = d1.number_input(f"Diesel price ({CUR}/L)", 10.0, 1000.0, float(bf.diesel_price_per_l), 1.0, key=k("dp"))
        esc = d2.slider("Diesel price rise per year", 0.0, 0.15, float(bf.diesel_escalation), 0.01, key=k("esc"))
        deff = d3.slider("Diesel pump fuel-to-water efficiency", 0.05, 0.30, float(bf.diesel_fuel_to_water_eff), 0.01, key=k("deff"))
        dmaint = d4.number_input(f"Diesel pump upkeep ({CUR}/yr)", 0, 5_000_000, int(bf.diesel_maintenance_per_year), 1_000, key=k("dm"))
    else:
        diesel, esc, deff, dmaint = bf.diesel_price_per_l, bf.diesel_escalation, bf.diesel_fuel_to_water_eff, bf.diesel_maintenance_per_year
    st.markdown("**Who pays, and the CARES model**")
    f1, f2, f3, f4 = st.columns(4)
    grant = f1.slider("Share of equipment paid by funders", 0.0, 1.0, float(bf.funder_grant_share), 0.05, key=k("grant"),
                      help="The rest is the community's share, e.g. through micro-credit or a cooperative loan.")
    dfee = f2.slider("CARES design & facilitation fee (paid by funders)", 0.0, 0.15, float(bf.cares_design_fee), 0.01, key=k("dfee"))
    mfee = f3.slider("CARES share of yearly net benefit", 0.0, 0.20, float(bf.cares_mgmt_share), 0.01, key=k("mfee"))
    disc = f4.slider("Discount rate", 0.0, 0.20, float(bf.discount_rate), 0.01, key=k("disc"))
    women = st.slider("Women on the Village Development Committee", 0.0, 1.0, float(base.women_share_committee), 0.05,
                      key=k("women"), help="The Solar Village model encourages equal numbers of women and men.")

# ================================================================== run the engine
clim_d = climate_for(lat, lon, cc, live)
if loc_note:
    clim_d = {**clim_d, "note": clim_d["note"] + " " + loc_note}
climate = SiteClimate(**clim_d)
di = DesignInputs(
    lat=lat, lon=lon, country=cc, households=p["households"] or 0, area_ha=area, pattern=pattern, head_m=head,
    wire_to_water_eff=eff, pump_kw=pump_kw, pv=PVSpec(kwp=kwp, tilt_deg=tilt, system_losses=losses),
    addons=addon_specs, grid_scheme=scheme, grid_tariff=tariff, grid_tariff_after=after if switch else tariff,
    grid_tariff_switch_year=switch, grid_buy_price=buy, women_share_committee=women,
    costs=CostInputs(pv_per_kwp=pv_cost, pump_per_kw=pump_cost, fixed_install=fixed, distribution_per_ha=dist,
                     solar_om_per_year=om, controller_replacement_cost=repl),
    finance=FinanceInputs(diesel_price_per_l=diesel, diesel_escalation=esc, diesel_fuel_to_water_eff=deff,
                          diesel_maintenance_per_year=dmaint, discount_rate=disc, lifetime_years=life,
                          funder_grant_share=grant, cares_design_fee=dfee, cares_mgmt_share=mfee))
res = run_design(di, climate)
E, F, I = res["energy"], res["finance"], res["impact"]
pvd = res["pv_detail"]
addon_labels = {a.key: CATALOG[a.key].name.split(" (")[0] for a in addon_specs}
money = lambda x: ui.fmt_money(x, cc)

# ================================================================== outputs
with tabs[0]:
    (st.success if climate.source == "nasa_power" else st.warning)(climate.note)
    st.plotly_chart(ui.sun_chart(res["climate"], pvd["poa_kwh_m2_day"]), theme=None)
    m1, m2, m3 = st.columns(3)
    m1.metric("Solar output", f"{E['pv_kwh_per_month']:,.0f} kWh/month")
    m2.metric("Yearly output per kWp", f"{E['specific_yield_kwh_per_kwp']:,.0f} kWh")
    m3.metric("Hottest panel (monthly average)", f"{max(pvd['cell_temp_c']):.0f} °C")
    if cc == "LK":
        st.caption(f"Field check: real 5 kW roofs report 500-600 kWh a month. This design gives "
                   f"{E['pv_kwh_per_month'] / kwp * 5:,.0f} kWh a month per 5 kW.")
    with st.expander("Table view and method"):
        st.dataframe(pd.DataFrame({
            "Month": MONTHS, "Sunshine, flat (kWh/m²/day)": climate.ghi,
            "Sunshine, tilted (kWh/m²/day)": pvd["poa_kwh_m2_day"], "Air temp (°C)": climate.t2m,
            "Panel temp (°C)": pvd["cell_temp_c"], "Heat loss factor": pvd["temp_factor"],
            "Solar output (kWh)": pvd["pv_kwh"]}).round(2), hide_index=True)
        st.caption("Tilted-panel sunshine: Klein (1977) monthly method with the Erbs et al. (1982) diffuse "
                   "fraction and an isotropic sky. Panel temperature: NOCT model using the energy-weighted "
                   "irradiance of a half-sine day; output falls 0.4% per °C above 25 °C.")

with tabs[1]:
    if irrigate:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=MONTHS, y=[r["pv_kwh"] for r in res["monthly"]], name="Solar output",
                             marker=dict(color=ui.slot(0), line=dict(width=2, color=ui.ink("surface"))),
                             hovertemplate="%{y:,.0f} kWh"))
        fig.add_trace(go.Scatter(x=MONTHS, y=[r["pump_demand_kwh"] for r in res["monthly"]], name="Pump needs",
                                 mode="lines+markers", line=dict(width=2, color=ui.ink("primary")),
                                 marker=dict(size=8), hovertemplate="%{y:,.0f} kWh"))
        st.plotly_chart(ui.base_layout(fig, "Solar output against what the pump needs", "kWh per month", 320), theme=None)
        m1, m2, m3 = st.columns(3)
        m1.metric("Water lifted per year", f"{sum(r['water_m3'] for r in res['monthly']):,.0f} m³")
        m2.metric("Diesel replaced", f"{I['diesel_l']:,.0f} L/yr")
        m3.metric("Irrigation need not met", f"{E['pump_unmet_kwh']:,.0f} kWh")
        if E["deficit_months"]:
            st.warning(f"In **{', '.join(E['deficit_months'])}** the pump cannot meet all irrigation needs. "
                       "Consider a larger pump or array, a smaller area, or water-saving irrigation.")
    else:
        st.caption("No irrigation in this design. Switch it on above if the community needs it.")

with tabs[2]:
    st.plotly_chart(ui.energy_chart(res["monthly"], addon_specs, addon_labels, scheme), theme=None)
    m1, m2, m3 = st.columns(3)
    if scheme == "net_plus":
        m1.metric("Grid income, year 1", money(F["grid_income_year1"]), f"{money(F['grid_income_year1'] / 12)} a month",
                  delta_color="off", delta_arrow="off")
        m2.metric("Electricity bought for village loads", money(F["grid_cost_year1"]) + "/yr")
        m3.metric("Income from productive uses", money(F["addon_income"]) + "/yr")
    else:
        m1.metric("Solar energy put to use", f"{E['utilisation']:.0%}")
        m2.metric("Income from productive uses and sales", money(F["addon_income"] + F["grid_income_year1"]) + "/yr")
        m3.metric("Energy still unused", f"{E['unused_kwh']:,.0f} kWh/yr")
    with st.expander("Table view"):
        tbl = pd.DataFrame({"Month": MONTHS, "Solar (kWh)": [r["pv_kwh"] for r in res["monthly"]],
                            "Irrigation": [r["pump_served_kwh"] for r in res["monthly"]]})
        for a in addon_specs:
            tbl[addon_labels[a.key]] = [r[f"addon:{a.key}"] for r in res["monthly"]]
        tbl["Sold to grid"] = [r["grid_export_kwh"] for r in res["monthly"]]
        tbl["Bought from grid"] = [r["grid_import_kwh"] for r in res["monthly"]]
        tbl["Unused"] = [r["unused_kwh"] for r in res["monthly"]]
        st.dataframe(tbl.round(0), hide_index=True)
    st.caption("Monthly energy balance. It ignores timing within the day: night-time loads off-grid would "
               "need batteries, which a fuller model would add.")

with tabs[3]:
    items = [("Solar array", kwp * pv_cost)]
    if irrigate:
        items += [("Pump & controller", pump_kw * pump_cost), ("Water distribution", area * dist)]
    items += [("Civil works, well, transport", fixed), *[(addon_labels[a.key], a.capex) for a in addon_specs],
              ("Total equipment cost", F["capex"]), ("CARES design & facilitation fee", F["cares_design_fee"])]
    st.dataframe(pd.DataFrame(items, columns=["Item", CUR]).assign(**{CUR: lambda x: x[CUR].round(0)}), hide_index=True)

with tabs[4]:
    r1 = st.columns(4)
    r1[0].metric("Total equipment cost", money(F["capex"]), ui.fmt_gbp(F["capex"], cc), delta_color="off",
                 delta_arrow="off", border=True)
    r1[1].metric("Asked of funders", money(F["funder_total"]), help="Funders' share of equipment plus the CARES fee", border=True)
    r1[2].metric("Community's share", money(F["community_share"]), border=True)
    r1[3].metric("Net benefit in year 1", money(F["year1_net"]), border=True)
    r2 = st.columns(4)
    r2[0].metric("Simple payback", ui.fmt_years(F["simple_payback"]), border=True)
    r2[1].metric("Payback with discounting", ui.fmt_years(F["discounted_payback"]), border=True)
    r2[2].metric("Community payback", ui.fmt_years(F["community_payback"]) if F["community_share"] else "No share",
                 help=None if F["community_share"] else "Funders pay for all the equipment", border=True)
    r2[3].metric("CO₂ avoided", f"{I['co2_t']:.1f} t/yr", border=True,
                 help="Diesel replaced, plus grid electricity displaced by exported solar (Sri Lanka: assumed 0.6 kg/kWh)")
    st.plotly_chart(ui.cashflow_chart(F["cumulative"], F["capex"], cc), theme=None)
    st.caption(f"Net present value over {life} years at {disc:.0%}: **{money(F['npv'])}**. "
               f"CARES unit income over the lifetime: {money(F['cares_income_lifetime'])}.")

    st.markdown("**What if our assumptions are wrong?**")
    def _variant(fn):
        v = copy.deepcopy(di)
        fn(v)
        return run_design(v, climate)["finance"]
    cases = {"As designed": lambda v: None}
    if scheme != "none":
        cases["Sale price 20% lower"] = lambda v: (setattr(v, "grid_tariff", tariff * 0.8),
                                                   setattr(v, "grid_tariff_after", (after if switch else tariff) * 0.8))
    if cc == "LK" and scheme == "net_plus" and tariff != 22:
        cases["Older Net-Plus terms (Rs 22, then Rs 15)"] = lambda v: (setattr(v, "grid_tariff", 22.0),
                                                                       setattr(v, "grid_tariff_after", 15.0),
                                                                       setattr(v, "grid_tariff_switch_year", 7))
    if irrigate:
        cases["Diesel 20% cheaper"] = lambda v: setattr(v.finance, "diesel_price_per_l", diesel * 0.8)
    cases["Equipment 20% dearer"] = lambda v: (setattr(v.costs, "pv_per_kwp", pv_cost * 1.2),
                                               setattr(v.costs, "pump_per_kw", pump_cost * 1.2),
                                               [setattr(a, "capex", a.capex * 1.2) for a in v.addons])
    cases["Solar output 10% lower"] = lambda v: setattr(v.pv, "system_losses", min(0.6, losses + 0.1 * (1 - losses)))
    if addon_specs:
        cases["Productive-use income 20% lower"] = lambda v: [setattr(a, "income_per_day", a.income_per_day * 0.8)
                                                              for a in v.addons]
    sens = []
    for name, fn in cases.items():
        fv = _variant(fn)
        sens.append({"Scenario": name, "Simple payback (yrs)": fv["simple_payback"],
                     "Community payback (yrs)": fv["community_payback"] if fv["community_share"] else None,
                     f"NPV ({CUR} lakh)": fv["npv"] / 1e5})
    st.dataframe(pd.DataFrame(sens).round(1), hide_index=True)

    st.markdown("**Plain-language summary**")
    design_dict = design_to_dict(di)
    if cc == "BD":
        s1, s2 = st.columns(2)
        s1.info(summary(ui.short_name(p), design_dict, res, "en"))
        s2.info(summary(ui.short_name(p), design_dict, res, "bn"))
    else:
        st.info(summary(ui.short_name(p), design_dict, res, "en"))

    st.divider()
    if as_built:
        st.caption("As-built model of a real site: nothing to save.")
    else:
        if is_cares:
            unit = user["organisation"]
            st.markdown(f"Saving as **{unit}**")
            if p["district"] not in set(user["coverage"] or []):
                st.caption("Note: this community is outside the districts your unit covers.")
        else:
            unit = None
            st.info("Only a signed-in CARES unit can save or publish a design. Use the sidebar switch or the "
                    "sign-in page; everything above can be explored freely.")
        if p["kind"] == "real":
            st.caption("This is an area the real programme is exploring: any design here is indicative only.")
        b1, b2, _ = st.columns([1, 1, 3])
        if b1.button("Save draft", key=k("save"), disabled=locked or not is_cares):
            store.save_design(pid, design_dict, res, publish=False, cares_unit=unit, cares_user_id=user["id"])
            st.toast("Design saved.")
            st.rerun()
        if b2.button("Publish to funders", type="primary", key=k("pub"), disabled=locked or not is_cares):
            store.save_design(pid, design_dict, res, publish=True, cares_unit=unit, cares_user_id=user["id"])
            st.toast("Published. Funders can now see this project.")
            st.rerun()
        if locked:
            st.caption("This project already has pledges, so its published design is locked.")
