import pandas as pd
import plotly.express as px
import streamlit as st

from app_core import auth, store, ui
from app_core import real_sites as RS

projects = store.list_projects()
real = [p for p in projects if p["kind"] == "real"]
count = lambda *s: sum(1 for p in projects if p["status"] in s)

# ------------------------------------------------------------------ hero
with st.container(key="hero"):
    left, right = st.columns([11, 9], gap="large", vertical_alignment="center")
    with left:
        st.html('<span class="cc-eyebrow">Built on the real Solar Village model</span>')
        st.title("Solar power that villages own")
        with st.container(key="lede"):
            st.markdown("Communities ask for what they need. Local university teams design it. "
                        "Funders back what works. One tool connects all three.")
        with st.container(horizontal=True):
            if st.button("Ask for help", type="primary", icon=":material/campaign:"):
                st.switch_page("views/local.py")
            if st.button("Design as a university team", icon=":material/engineering:"):
                auth.sign_in_demo("cares")
                st.switch_page("views/dashboard.py")
            if st.button("Fund a project", icon=":material/volunteer_activism:"):
                auth.sign_in_demo("funder")
                st.switch_page("views/funders.py")
        st.caption("No sign-up: the buttons open fictional demo profiles. Sri Lanka and Bangladesh.")
    with right:
        GROUP = lambda p: ("Operating" if p["status"] == "Operating" else
                           "Being built" if p["status"] == "Funded" else "Being explored")
        ORDER = ["Operating", "Being built", "Being explored"]
        COL = {"Operating": "#F2B705", "Being built": "#3FBF7F", "Being explored": "#86B6EF"}
        df = pd.DataFrame([{"Site": p["village"], "lat": p["lat"], "lon": p["lon"], "Status": GROUP(p)}
                           for p in real if p["lat"] is not None])
        fig = px.scatter_map(df, lat="lat", lon="lon", color="Status", hover_name="Site",
                             hover_data={"lat": False, "lon": False, "Status": True},
                             category_orders={"Status": ORDER}, color_discrete_map=COL,
                             zoom=5.9, center={"lat": 7.9, "lon": 80.75}, map_style=ui.MAP_STYLE, height=380)
        fig.update_traces(marker=dict(size=15))
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                          legend=dict(title=None, x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.9)",
                                      font=dict(family="Noto Sans, sans-serif", size=12, color="#163A63")))
        st.plotly_chart(fig, theme=None, config={"displayModeBar": False})

# ------------------------------------------------------------------ how it works
st.header("How it works", anchor=False)
STEPS = [
    ("1", "Communities ask", "A village committee or farmer group says what it needs, on a phone or with a field worker.",
     ui.badge(f"{count('New request')} waiting for a design", "gray"), "views/local.py", "Ask for help"),
    ("2", "CARES units design", "A Centre for Application of Renewable Energy Sources at a local university sizes "
     "the system with live sunshine data and tests the business case.",
     ui.badge(f"{count('Designed', 'Published', 'Partly funded')} designs drafted or open", "violet"),
     "views/cares.py", "Open the design tool"),
    ("3", "Funders back it", "CSR funds, diaspora givers, NGOs and banks compare costed projects and pledge.",
     ui.badge(f"{count(*store.OPEN_STATUSES)} seeking funding", "blue"), "views/funders.py", "See open projects"),
    ("4", "Government plans", "Planners see demand on a map and test what scaling up would cost and deliver.",
     ui.badge(f"{count('Operating')} villages operating", "yellow", ":material/wb_sunny:"), "views/overview.py",
     "Plan & scenarios"),
]
for col, (n, title, text, badge, page, link) in zip(st.columns(4), STEPS):
    with col, ui.card(f"step{n}", height="stretch"):
        st.html(f'<span class="cc-step">{n}</span>')
        st.subheader(title, anchor=False)
        st.markdown(text)
        st.markdown(badge)
        st.page_link(page, label=link, icon=":material/arrow_forward:")

# ------------------------------------------------------------------ evidence
st.header("What solar villages have already done", anchor=False)
src = lambda *keys: ui.sources_md([list(RS.S[k]) for k in keys])
EVIDENCE = [
    ("20 → 85 pupils", "Kaduruwewa school, Kurunegala",
     "Facing closure in 2007. Since its solar village began in 2008, it has grown and now ranks "
     "2nd of 186 primary schools in its region.", src("whatwedo", "report")),
    ("Rs 60 lakh+", "Saved by Nochchiya's village committee",
     "From a 7 kW solar roof since 2017. The village also sells clean water to about eight nearby villages.",
     src("nochchiya", "report")),
    ("3.5–6 years", "Reported payback of a village roof",
     "A 5 kW roof costs about Rs 1.2 million and produces 500–600 kWh a month, all sold to the grid.",
     src("report")),
]
for col, (value, label, text, sources) in zip(st.columns(3), EVIDENCE):
    with col, ui.card(f"ev_{label[:8]}", height="stretch"):
        ui.big_number(value, label)
        st.markdown(text)
        st.caption("Source: " + sources)
st.page_link("views/villages.py", label=f"See all {len([p for p in real if not p['village'].startswith('Proposed')])} "
             "real sites, with sources", icon=":material/solar_power:")

# ------------------------------------------------------------------ about
with st.expander("About this prototype and its data"):
    st.markdown(
        "- **Real sites** come from public sources only. Sizes, households and locations are left out where "
        "a source does not give them, and every location is approximate.\n"
        "- **Every number comes from one engine** (`engine/model.py`): sunshine on a tilted panel, panel heat, "
        "pumping energy, Sri Lanka's Net-Plus scheme and a 20-year cash flow. Sri Lankan output is calibrated "
        "against the output reported for real 5 kW roofs.\n"
        "- **Demo profiles and pledges are fictional.** No pledges are attributed to real organisations.\n"
        "- The engine is separate from the screens, so an AI assistant could explain results without "
        "calculating anything itself.")
    if st.button("Reset demo data", icon=":material/restart_alt:",
                 help="Deletes anything you added and restores the real sites and demo profiles"):
        store.reset_db()
        st.session_state.clear()
        st.toast("Demo data restored.")
        st.rerun()
