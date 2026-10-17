import streamlit as st

from app_core import store, ui

st.title("CARES Connect")
st.markdown("#### Connecting rural communities, local university experts and funders, "
            "built on the real Solar Village model in Sri Lanka")
ui.disclaimer()

projects = store.list_projects()
real_sites = [p for p in projects if p["kind"] == "real" and not p["village"].startswith("Proposed")]
st.write(
    "Since 2008, solar villages in Sri Lanka have shown what a small solar asset can do when a community "
    "controls the income: Kaduruwewa's school went from facing closure to ranking second of 186 in its "
    "region, and Nochchiya's Village Development Committee has built savings of over Rs 60 lakhs and sells "
    "clean water to about eight nearby villages. The hard part is not the technology. It is connecting the "
    "people who need it, the people who can design it for local conditions, and the people who can pay for it. "
    "CARES Connect puts all three in one place, and the same engine also works for solar irrigation hubs in "
    "Bangladesh."
)
st.page_link("views/villages.py", label=f"See the {len(real_sites)} real solar villages, with sources",
             icon=":material/solar_power:")

c1, c2, c3 = st.columns(3)
with c1, st.container(border=True):
    st.markdown("### 🧑‍🌾 Communities")
    st.write("Village committees, cooperatives and farmers describe what they need: water, income, "
             "irrigation, schooling, protection from elephants. They can do it on a phone or with a field worker.")
with c2, st.container(border=True):
    st.markdown("### 🎓 CARES")
    st.write("A *Centre for Application of Renewable Energy Sources*: a local university unit that knows the "
             "area and the technology. It sizes the system, tests the business case and publishes a costed project.")
with c3, st.container(border=True):
    st.markdown("### 🤝 Funders")
    st.write("Company CSR budgets, diaspora givers, NGOs, development banks and government compare projects by "
             "cost and impact, see the track record, and pledge support.")

st.subheader("How a project moves")
count = lambda *s: sum(1 for p in projects if p["status"] in s)
m1, m2, m3, m4 = st.columns(4)
m1.metric("1 · Requests waiting for design", count("New request"))
m2.metric("2 · Designs drafted or published", count("Designed", "Published", "Partly funded"))
m3.metric("3 · Funded, being built", count("Funded"))
m4.metric("4 · Operating", count("Operating"))

st.subheader("Try it in two minutes")
st.write("Fictional demo profiles are ready for every role. Switch between them with **Signed in as** in the "
         "sidebar, or register your own.")
st.markdown(
    "1. **As a CARES unit** (try *North & East*) - your dashboard shows requests in your districts, such as the "
    "area the programme is exploring in Batticaloa. Open it: the engine pulls sunshine data for the spot, sizes "
    "a Net-Plus solar roof and any extras (clean water, a smart classroom, an elephant fence), and works out "
    "income, payback and impact. Publish it.\n"
    "2. **As a funder** - your dashboard recommends projects that match your interests and shows the real "
    "track record. Pledge, then see your share of the impact.\n"
    "3. **As a community** - send a request for your village (Sri Lanka, or Bangladesh in Bangla) and follow "
    "it on *My dashboard*.\n"
    "4. **Overview** - every site and request on one map, and a national replication scenario for policymakers."
)
st.page_link("views/account.py", label="Sign in or register", icon=":material/login:")

with st.expander("Where do the numbers come from?"):
    st.write(
        "Every figure comes from one calculation engine (`engine/model.py`, function `run_design`). It models "
        "sunshine on a tilted panel and panel temperature month by month, the energy needed to lift water, "
        "how solar output is used or sold (including Sri Lanka's Net-Plus scheme), and a 20-year cash flow. "
        "Sri Lankan costs and tariffs come from the Solar Village project report, and the solar output is "
        "calibrated against the output reported for real 5 kW roofs. The engine is separate from the screens, "
        "so it can be tested on its own or called by an AI assistant that explains results without "
        "calculating anything itself."
    )

st.divider()
if st.button("Reset demo data", help="Deletes anything you added and restores the real sites and demo profiles"):
    store.reset_db()
    st.session_state.clear()
    st.toast("Demo data restored.")
    st.rerun()
