import copy

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_core import store, ui
from app_core.climate import climate_for
from app_core.store import STATUSES
from engine import COUNTRIES, SiteClimate, run_design

st.title("Overview & scenarios")
st.write("For government and large planners: where communities are asking for help, what they need, what is "
         "already working, and what scaling up would cost and deliver.")
ui.disclaimer()

cc = st.segmented_control("Country", list(COUNTRIES), format_func=lambda c: COUNTRIES[c]["name"],
                          default="LK", required=True, key="ov_country")
C = COUNTRIES[cc]
projects = [p for p in store.list_projects() if p["country"] == cc]

GROUP = {"New request": "Waiting for design", "Designed": "Waiting for design", "Published": "Seeking funding",
         "Partly funded": "Seeking funding", "Funded": "Funded or operating", "Operating": "Funded or operating"}
ORDER = ["Waiting for design", "Seeking funding", "Funded or operating"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Sites and requests", len(projects))
m2.metric("Operating", sum(p["status"] == "Operating" for p in projects))
m3.metric("Seeking funding", sum(p["status"] in store.OPEN_STATUSES for p in projects))
m4.metric("Waiting for a design", sum(p["status"] in ("New request", "Designed") for p in projects))

if projects:
    mapped = [p for p in projects if p["lat"] is not None]
    if mapped:
        df = pd.DataFrame([{"Site": p["village"], "District": p["district"] or "—", "lat": p["lat"], "lon": p["lon"],
                            "Status": p["status"], "Group": GROUP[p["status"]],
                            "Real or demo": "Real site" if p["kind"] == "real" else "Request made in the app"}
                           for p in mapped])
        fig = px.scatter_map(df, lat="lat", lon="lon", color="Group", hover_name="Site",
                             hover_data={"District": True, "Status": True, "Real or demo": True, "lat": False,
                                         "lon": False, "Group": False},
                             category_orders={"Group": ORDER},
                             color_discrete_map={g: ui.slot(i) for i, g in enumerate(ORDER)},
                             zoom=C["zoom"], center={"lat": C["center"][0], "lon": C["center"][1]},
                             map_style="carto-positron", height=520)
        fig.update_traces(marker=dict(size=14))
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), legend=dict(orientation="h", y=1.02, x=0, title=None),
                          title=dict(text=f"Sites and requests in {C['name']} (approximate locations)", x=0,
                                     font=dict(size=15)))
        st.plotly_chart(fig, theme=None)

    c1, c2 = st.columns(2)
    with c1:
        counts = [sum(p["status"] == s for p in projects) for s in STATUSES]
        f2 = go.Figure(go.Bar(x=counts, y=STATUSES, orientation="h", text=counts, textposition="outside",
                              marker=dict(color=ui.stage_colors(), line=dict(width=2, color=ui.ink("surface"))),
                              hovertemplate="%{y}: %{x}<extra></extra>"))
        f2.update_yaxes(autorange="reversed")
        f2.update_xaxes(range=[0, max(counts) * 1.2 + 0.5])
        f2 = ui.base_layout(f2, "Projects at each stage", "", 320)
        f2.update_layout(showlegend=False, hovermode="closest")
        st.plotly_chart(f2, theme=None)
    with c2:
        needs = pd.Series([n for p in projects for n in (p["needs"] or [])]).value_counts()
        if len(needs):
            f3 = go.Figure(go.Bar(x=needs.values, y=needs.index, orientation="h", text=needs.values,
                                  textposition="outside",
                                  marker=dict(color=ui.slot(0), line=dict(width=2, color=ui.ink("surface"))),
                                  hovertemplate="%{y}: %{x}<extra></extra>"))
            f3.update_yaxes(autorange="reversed")
            f3.update_xaxes(range=[0, needs.max() * 1.2 + 0.5])
            f3 = ui.base_layout(f3, "What is being asked for", "", 320)
            f3.update_layout(showlegend=False, hovermode="closest")
            st.plotly_chart(f3, theme=None)
else:
    st.info(f"No sites or requests in {C['name']} yet. Communities can send one from the Locals page.")

# ------------------------------------------------------------------ scenario
st.divider()
clim = SiteClimate(**climate_for(C["center"][0], C["center"][1], cc, True))

if cc == "LK":
    st.subheader("Scenario: scaling up solar villages across Sri Lanka")
    st.write("A national programme of Net-Plus solar roofs, each owned by a Village Development Committee. "
             "Starting values are the real costs and tariffs from the Solar Village report.")
    s1, s2, s3, s4 = st.columns(4)
    n = s1.slider("Number of villages", 10, 1000, 200, 10)
    kw = s2.slider("Roof size per village (kW)", 3, 20, 5)
    tariff = s3.slider("Net-Plus tariff (Rs per unit, 20 years)", 10, 50, 37)
    cost = s4.slider("Installed cost (Rs per kW)", 150_000, 350_000, 240_000, 10_000)
    proto = store.default_design_for({"country": "LK", "lat": C["center"][0], "lon": C["center"][1],
                                      "needs": [C["grid_need"]], "households": 0})
    proto.pv.kwp, proto.costs.pv_per_kwp = float(kw), float(cost)
    proto.costs.controller_replacement_cost = 75_000 * kw
    proto.finance.funder_grant_share, proto.finance.cares_design_fee, proto.finance.cares_mgmt_share = 1.0, 0.0, 0.0

    def run_at(t):
        d = copy.deepcopy(proto)
        d.grid_tariff = d.grid_tariff_after = float(t)
        return run_design(d, clim)

    r = run_at(tariff)
    F, I, E = r["finance"], r["impact"], r["energy"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total investment", ui.fmt_money(F["capex"] * n, "LK"), ui.fmt_gbp(F["capex"] * n, "LK"),
              delta_color="off", delta_arrow="off")
    k2.metric("Village income per year", ui.fmt_money(F["grid_income_year1"] * n, "LK"),
              f"{ui.fmt_money(F['grid_income_year1'] / 12, 'LK')} a month per village", delta_color="off", delta_arrow="off")
    k3.metric("Solar electricity", f"{E['pv_kwh'] * n / 1e6:,.1f} GWh/yr")
    k4.metric("CO₂ avoided", f"{I['co2_t'] * n:,.0f} t/yr", help="At an assumed 0.6 kg CO₂ per kWh of grid electricity")

    ts = list(range(10, 51, 2))
    pb = [run_at(t)["finance"]["simple_payback"] for t in ts]
    fig = go.Figure(go.Scatter(x=ts, y=pb, mode="lines+markers", name="Simple payback",
                               line=dict(width=2, color=ui.slot(0)), marker=dict(size=8),
                               hovertemplate="Rs %{x}/unit: %{y:.1f} years<extra></extra>"))
    for t_ref, label in ((22, "Older Net-Plus terms (Rs 22)"), (37, "Newer terms (Rs 37)")):
        fig.add_vline(x=t_ref, line=dict(color=ui.ink("axis"), width=1),
                      annotation_text=label, annotation_position="top")
    fig.add_hrect(y0=3.5, y1=6.0, fillcolor=ui.ink("grid"), opacity=0.5, line_width=0,
                  annotation_text="Reported payback 3.5-6.0 years", annotation_position="top left")
    fig.update_xaxes(title=dict(text="Net-Plus tariff (Rs per unit)", font=dict(color=ui.ink("muted"))))
    fig = ui.base_layout(fig, "How the tariff decides whether a village roof pays back", "Years", 360)
    fig.update_layout(showlegend=False, hovermode="closest")
    st.plotly_chart(fig, theme=None)
    st.caption(f"Each village modelled as one {kw} kW roof with calibrated losses; sunshine: {clim.note} "
               "Tariff policy is the single biggest lever: the same roof takes far longer to pay back under the "
               "older terms than the newer ones.")
else:
    st.subheader("Scenario: scaling up solar irrigation hubs in Bangladesh")
    st.write("A national programme of solar irrigation pumps whose spare power runs a cold store. "
             "All costs are illustrative.")
    s1, s2, s3 = st.columns(3)
    n = s1.slider("Number of hubs", 10, 2000, 500, 10)
    diesel = s2.slider("Diesel price (Tk/L)", 60, 200, 110, 5)
    subsidy = s3.slider("Government subsidy (share of equipment cost)", 0.0, 0.9, 0.3, 0.05)
    proto = store.default_design_for({"country": "BD", "lat": C["center"][0], "lon": C["center"][1],
                                      "needs": ["Irrigation", "Cold storage"], "crops": ["Boro rice", "Potato"],
                                      "area_local": 100, "water_source": "Groundwater", "households": 120})

    def run_at(s):
        d = copy.deepcopy(proto)
        d.finance.funder_grant_share, d.finance.diesel_price_per_l = float(s), float(diesel)
        return run_design(d, clim)

    r = run_at(subsidy)
    F, I = r["finance"], r["impact"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Government budget", ui.fmt_money(F["grant"] * n, "BD"), ui.fmt_gbp(F["grant"] * n, "BD"),
              delta_color="off", delta_arrow="off")
    k2.metric("Community payback", ui.fmt_years(F["community_payback"]))
    k3.metric("Diesel replaced", f"{I['diesel_l'] * n / 1e6:,.1f} million L/yr")
    k4.metric("CO₂ avoided", f"{I['co2_t'] * n:,.0f} t/yr")
    ss = [x / 20 for x in range(0, 19)]
    pb = [run_at(s)["finance"]["community_payback"] or 0 for s in ss]
    fig = go.Figure(go.Scatter(x=[s * 100 for s in ss], y=pb, mode="lines+markers", line=dict(width=2, color=ui.slot(0)),
                               marker=dict(size=8), hovertemplate="%{x:.0f}% subsidy: %{y:.1f} years<extra></extra>"))
    fig.update_xaxes(title=dict(text="Government subsidy (% of equipment cost)", font=dict(color=ui.ink("muted"))))
    fig = ui.base_layout(fig, "How the subsidy changes the community's payback", "Years", 340)
    fig.update_layout(showlegend=False, hovermode="closest")
    st.plotly_chart(fig, theme=None)
    st.caption(f"Each hub: {proto.area_ha:g} ha of Boro rice and potato, {proto.pv.kwp:g} kWp, {proto.pump_kw:g} kW pump, "
               f"plus a cold store. Sunshine: {clim.note}")
