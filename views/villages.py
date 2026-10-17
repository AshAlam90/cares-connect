import pandas as pd
import plotly.express as px
import streamlit as st

from app_core import real_sites as RS
from app_core import store, ui
from app_core.climate import climate_for
from engine import COUNTRIES, SiteClimate, defaults_for, run_design

st.title("Real solar villages in Sri Lanka")
st.write("CARES Connect is built on the Solar Village model, pioneered by Prof. I. M. Dharmadasa and piloted at "
         "Kaduruwewa in 2008. Each village gets a clean-energy asset, usually a solar roof that earns income from "
         "the grid, and a Village Development Committee turns that income into water, schooling, micro-credit "
         "and local enterprise.")
st.caption("Facts below come from public sources, linked on each site. Numbers marked *modelled* are estimates "
           "from this app's engine, not reported figures.")

with st.container(border=True):
    st.markdown("**The model in brief, as reported**")
    st.markdown("\n".join(f"- {f}" for f in RS.PROGRAMME_FACTS))
    st.caption("Sources: " + ui.sources_md([list(RS.S[k]) for k in RS.PROGRAMME_SOURCES]))

real = [p for p in store.list_projects() if p["kind"] == "real"]
proposed = [p for p in real if p["village"].startswith("Proposed")]
sites = [p for p in real if p not in proposed]
operating = [p for p in sites if p["status"] == "Operating"]
building = [p for p in sites if p["status"] == "Funded"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Sites described as operating", len(operating),
          help="Counted from the individual site descriptions. The programme itself spoke of seven established "
               "villages in March 2025.")
m2.metric("Being built", len(building))
m3.metric("Published solar roof capacity", f"{sum((p['facts'] or {}).get('kw') or 0 for p in operating):g} kW",
          help="Operating sites whose roof size is published; sizes are not published for every site")
m4.metric("Areas being explored", len(proposed))

# ------------------------------------------------------------------ map
GROUP = lambda p: "Operating" if p["status"] == "Operating" else ("Being built" if p in building else "Being explored")
ORDER = ["Operating", "Being built", "Being explored"]
mapped = [p for p in real if p["lat"] is not None]
df = pd.DataFrame([{"Site": p["village"], "District": p["district"] or "—", "lat": p["lat"], "lon": p["lon"],
                    "Status": GROUP(p), "Location": p["precision"]} for p in mapped])
fig = px.scatter_map(df, lat="lat", lon="lon", color="Status", hover_name="Site",
                     hover_data={"District": True, "Location": True, "lat": False, "lon": False, "Status": False},
                     category_orders={"Status": ORDER}, color_discrete_map={g: ui.slot(i) for i, g in enumerate(ORDER)},
                     zoom=6.3, center={"lat": 7.85, "lon": 80.75}, map_style="carto-positron", height=560)
fig.update_traces(marker=dict(size=14))
fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), legend=dict(orientation="h", y=1.02, x=0, title=None),
                  title=dict(text="Where the solar villages are (approximate locations)", x=0, font=dict(size=15)))
st.plotly_chart(fig, theme=None)
hidden = [p["village"] for p in real if p["lat"] is None]
if hidden:
    st.caption(f"Not on the map because their location is not published: {', '.join(hidden)}. "
               "Every marker is approximate; see each site for how precise it is.")

# ------------------------------------------------------------------ model check
st.subheader("Checking the model against field reports")
lat, lon = 7.83, 80.27   # Maho area, home of the pilot
clim = SiteClimate(**climate_for(lat, lon, "LK", True))
std = defaults_for("LK", lat, lon, area_ha=0.0, pattern="none", pump_kw=0.0)
std.pv.kwp, std.pv.system_losses = 5.0, 0.14
std.costs.controller_replacement_cost = 375_000
cal = defaults_for("LK", lat, lon, area_ha=0.0, pattern="none", pump_kw=0.0)
cal.pv.kwp = 5.0
cal.costs.controller_replacement_cost = 375_000
for d in (std, cal):
    d.finance.funder_grant_share, d.finance.cares_design_fee, d.finance.cares_mgmt_share = 1.0, 0.0, 0.0
r_std, r_cal = run_design(std, clim), run_design(cal, clim)
rows = [
    ("Output of a 5 kW roof (kWh per month)", "500-600",
     f"{r_std['energy']['pv_kwh_per_month']:,.0f}", f"{r_cal['energy']['pv_kwh_per_month']:,.0f}"),
    ("Net-Plus income at Rs 37/unit (Rs per month)", "at least 18,500",
     f"{r_std['finance']['grid_income_year1'] / 12:,.0f}", f"{r_cal['finance']['grid_income_year1'] / 12:,.0f}"),
    ("Simple payback of a Rs 1.2 million roof (years)", "3.5-6.0",
     f"{r_std['finance']['simple_payback']:.1f}", f"{r_cal['finance']['simple_payback']:.1f}"),
]
st.dataframe(pd.DataFrame(rows, columns=["Measure", "Reported", "Model, textbook 14% losses",
                                         f"Model, calibrated {COUNTRIES['LK']['pv_losses']:.0%} losses"]),
             hide_index=True)
over = r_std["energy"]["pv_kwh_per_month"] / 550 - 1
st.caption(f"Sunshine: {clim.note} With textbook losses the model over-predicts the reported midpoint "
           f"(550 kWh/month) by about {over:.0%}, which points to real-world losses such as roof orientation, "
           "shading, dust, heat and grid downtime. All Sri Lankan designs in this app therefore use the "
           "calibrated value. With metered data from each roof, the calibration could be done site by site. "
           "Reported figures: " + ui.sources_md([list(RS.S["report"])]))

# ------------------------------------------------------------------ the sites
st.subheader("The sites")
tab_a, tab_b = st.tabs([f"Operating and being built ({len(sites)})", f"Being explored ({len(proposed)})"])


def site_card(p: dict) -> None:
    f = p["facts"] or {}
    with st.container(border=True):
        st.markdown(f"#### {p['village']}")
        st.caption(f"{'🔨 Funded, being built' if p['status'] == 'Funded' else ui.status_badge(p['status'])}"
                   f"{' · since ' + p['year'] if p['year'] else ''} · {p['district'] or 'District not published'}"
                   f" · {p['precision']}")
        st.markdown(f"**System:** {f.get('system') or 'Not published.'}  \n"
                    f"**Who benefits:** {f.get('beneficiaries') or 'Not published.'}  \n"
                    f"**Funded by:** {f.get('funders') or 'Not published.'}  \n"
                    f"**Partners:** {f.get('partners') or 'Not published.'}")
        if f.get("outcomes"):
            st.markdown("**Reported outcomes**\n" + "\n".join(f"- {o}" for o in f["outcomes"]))
        if p["results"]:
            R = p["results"]
            st.markdown(f"**Modelled:** {R['energy']['pv_kwh_per_month']:,.0f} kWh a month · "
                        f"{ui.fmt_money(R['finance']['grid_income_year1'], 'LK')} grid income in year 1 · "
                        f"simple payback {ui.fmt_years(R['finance']['simple_payback'])} · "
                        f"{R['impact']['co2_t']:.1f} t CO₂ a year avoided")
            notes = [f.get("tariff_note")]
            notes.append(f"Cost used: {'published Rs ' + format(f['cost'], ',') if f.get('cost') else 'typical Rs 240,000 per kW (report)'}.")
            if p["lat"] is None:
                notes.append("Location not published, so modelled with central Sri Lankan climate.")
            st.caption(" ".join(n for n in notes if n))
        else:
            st.caption("System size not published, so this site is not modelled.")
        st.caption("Sources: " + ui.sources_md(f.get("sources")))


with tab_a:
    cols = st.columns(2)
    for i, p in enumerate(sites):
        with cols[i % 2]:
            site_card(p)
with tab_b:
    st.write("The programme says it is exploring these areas and looking for local coordinators. "
             "No village has been chosen yet, so each appears as a district-level request that a CARES unit "
             "can turn into an indicative design.")
    for p in proposed:
        with st.container(border=True):
            st.markdown(f"**{p['village']}** · {p['district']} · {ui.status_badge(p['status'])}")
            st.caption(p["notes"] + " Sources: " + ui.sources_md((p["facts"] or {}).get("sources")))
