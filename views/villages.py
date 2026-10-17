import pandas as pd
import plotly.express as px
import streamlit as st

from app_core import auth, store, ui
from app_core import real_sites as RS
from app_core.climate import climate_for
from engine import COUNTRIES, SiteClimate, defaults_for, run_design

st.title("Solar villages")
st.markdown("The real sites behind CARES Connect. Each village owns a solar asset, and its Village Development "
            "Committee turns the income into water, schooling and local enterprise.")

real = [p for p in store.list_projects() if p["kind"] == "real"]
proposed = [p for p in real if p["village"].startswith("Proposed")]
sites = [p for p in real if p not in proposed]
operating = [p for p in sites if p["status"] == "Operating"]
building = [p for p in sites if p["status"] == "Funded"]

m1, m2, m3, m4 = st.container(key="kpis_villages").columns(4)
m1.metric("Operating", len(operating), border=True,
          help="Counted from the individual site descriptions. The programme spoke of seven established "
               "villages in March 2025.")
m2.metric("Being built", len(building), border=True)
m3.metric("Published roof capacity", f"{sum((p['facts'] or {}).get('kw') or 0 for p in operating):g} kW", border=True,
          help="Operating sites whose roof size is published; not every site publishes it")
m4.metric("Areas being explored", len(proposed), border=True)

# ------------------------------------------------------------------ map + fact sheet
left, right = st.columns([3, 2], gap="medium")
with left:
    GROUP = lambda p: "Operating" if p["status"] == "Operating" else ("Being built" if p in building else "Being explored")
    ORDER = ["Operating", "Being built", "Being explored"]
    COL = {"Operating": "#E0A800", "Being built": "#1E9E5A", "Being explored": "#6DA7EC"}
    mapped = [p for p in real if p["lat"] is not None]
    df = pd.DataFrame([{"Site": p["village"], "District": p["district"] or "—", "lat": p["lat"], "lon": p["lon"],
                        "Status": GROUP(p), "Location": p["precision"]} for p in mapped])
    fig = px.scatter_map(df, lat="lat", lon="lon", color="Status", hover_name="Site",
                         hover_data={"District": True, "Location": True, "lat": False, "lon": False, "Status": False},
                         category_orders={"Status": ORDER}, color_discrete_map=COL,
                         zoom=6.3, center={"lat": 7.85, "lon": 80.75}, map_style=ui.MAP_STYLE, height=520)
    fig.update_traces(marker=dict(size=15))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(title=None, x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.9)",
                                  font=dict(family="Noto Sans, sans-serif", color="#163A63")))
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False})
    hidden = [p["village"] for p in real if p["lat"] is None]
    st.caption("Approximate locations." + (f" Not shown (location not published): {', '.join(hidden)}." if hidden else ""))

with right, ui.card("factsheet"):
    st.subheader("The model, as reported", anchor=False)
    FACTS = [
        ("2008", "First solar village, Kaduruwewa, funded by Prof. I. M. Dharmadasa"),
        ("Rs 1.2 m", "Typical 5 kW roof, installed; 500–600 kWh a month"),
        ("Rs 37/unit", "Newer Net-Plus contracts, 20 years (older: Rs 22, then Rs 15)"),
        ("3.5–6 yrs", "Reported simple payback"),
        ("Women = men", "Encouraged on every Village Development Committee"),
    ]
    for value, text in FACTS:
        a, b = st.columns([2, 5], vertical_alignment="center")
        a.markdown(f"**{value}**")
        b.markdown(text)
    st.caption("Now run by Solar Village SDG CIC. Sources: "
               + ui.sources_md([list(RS.S[k]) for k in RS.PROGRAMME_SOURCES]))

# ------------------------------------------------------------------ model check
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

with ui.card("modelcheck"):
    st.subheader("Does the model match the field?", anchor=False)
    st.markdown(ui.badge("Within the reported range", "green", ":material/check_circle:") + "  \n"
                f"A 5 kW roof: reported **500–600 kWh a month**, calibrated model "
                f"**{r_cal['energy']['pv_kwh_per_month']:,.0f}**. Payback: reported **3.5–6 years**, model "
                f"**{r_cal['finance']['simple_payback']:.1f}**.")
    with st.expander("How the model was checked"):
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
        st.caption(f"With textbook losses the model over-predicts the reported midpoint by about {over:.0%}. That "
                   "points to real-world losses (orientation, shading, dust, heat, grid downtime), so Sri Lankan "
                   "designs use the calibrated value. Metered data would allow site-by-site calibration. "
                   f"Sunshine: {clim.note} Reported figures: " + ui.sources_md([list(RS.S["report"])]))

# ------------------------------------------------------------------ the sites
st.header("The sites", anchor=False)
tab_a, tab_b = st.tabs([f"Operating and being built ({len(sites)})", f"Being explored ({len(proposed)})"])


def site_card(p: dict) -> None:
    f = p["facts"] or {}
    with ui.card(f"site_{p['id']}", height="stretch"):
        st.subheader(p["village"], anchor=False)
        ui.badges(ui.status_badge(p["status"], ui.status_label(p)),
                  ui.badge(f"Since {p['year']}") if p["year"] else "",
                  ui.badge(p["district"] or "District not published", "gray", ":material/location_on:"))
        system = f.get("system")
        st.markdown(system if system and system != "Not published." else "System details not published.")
        if p["results"]:
            R = p["results"]
            st.markdown(f"**{R['energy']['pv_kwh_per_month']:,.0f}** kWh a month · "
                        f"**{ui.fmt_money(R['finance']['grid_income_year1'], 'LK')}** a year · "
                        f"payback **{ui.fmt_years(R['finance']['simple_payback'])}**")
            st.caption("Modelled estimate, not a reported figure.")
        with st.expander("Outcomes, funders and sources"):
            if f.get("outcomes"):
                st.markdown("\n".join(f"- {o}" for o in f["outcomes"]))
            st.markdown(f"**Who benefits:** {f.get('beneficiaries') or 'Not published.'}  \n"
                        f"**Funded by:** {f.get('funders') or 'Not published.'}  \n"
                        f"**Partners:** {f.get('partners') or 'Not published.'}  \n"
                        f"**Location:** {p['precision']}")
            notes = []
            if p["results"]:
                notes.append(f.get("tariff_note"))
                notes.append(f"Cost used: {'published Rs ' + format(f['cost'], ',') if f.get('cost') else 'typical Rs 240,000 per kW (report)'}.")
                if p["lat"] is None:
                    notes.append("Modelled with central Sri Lankan climate.")
            else:
                notes.append("System size not published, so not modelled.")
            st.caption(" ".join(n for n in notes if n) + " Sources: " + ui.sources_md(f.get("sources")))


with tab_a:
    order = sorted(sites, key=lambda p: (p["status"] != "Operating", p["year"] or "9999"))   # oldest first
    for row in range(0, len(order), 3):
        cols = st.columns(3)
        for col, p in zip(cols, order[row:row + 3]):
            with col:
                site_card(p)

with tab_b:
    st.markdown("The programme is exploring these areas. No village is chosen yet, so each is a district-level "
                "request that a CARES unit can turn into an indicative design.")
    user = auth.current_user()
    cols = st.columns(len(proposed) or 1)
    for col, p in zip(cols, proposed):
        with col, ui.card(f"prop_{p['id']}", height="stretch"):
            st.subheader(p["district"], anchor=False)
            st.markdown(ui.status_badge(p["status"]))
            st.caption(p["notes"])
            if user and user["role"] == "cares" and st.button("Open in design tool", key=f"prop_open_{p['id']}"):
                st.session_state["cares_open"] = p["id"]
                st.switch_page("views/cares.py")
    st.caption("Source: " + ui.sources_md([list(RS.S[k]) for k in RS.PROPOSED_SOURCES]))
