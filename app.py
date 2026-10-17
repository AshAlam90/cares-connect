import streamlit as st

from app_core import auth, store, ui

st.set_page_config(page_title="CARES Connect", page_icon="☀️", layout="wide", initial_sidebar_state="collapsed")
store.init_db()
st.logo("assets/logo.svg", size="large")
ui.inject_css()

user = auth.current_user()
role = user["role"] if user else None

PAGES = {   # key: (file, title, icon, url)
    "home": ("views/home.py", "Home", ":material/home:", None),
    "dash": ("views/dashboard.py", {"community": "My requests", "cares": "My queue", "funder": "My impact"}
             .get(role, "My dashboard"), ":material/dashboard:", "dashboard"),
    "villages": ("views/villages.py", "Solar villages", ":material/solar_power:", "villages"),
    "ask": ("views/local.py", "Ask for help", ":material/campaign:", "ask"),
    "design": ("views/cares.py", "Design tool", ":material/engineering:", "design"),
    "fund": ("views/funders.py", "Fund a project", ":material/volunteer_activism:", "fund"),
    "plan": ("views/overview.py", "Plan & scenarios", ":material/map:", "plan"),
    "account": ("views/account.py", "Sign in", ":material/login:", "sign-in"),
}
# Each role sees its own pages; every page stays reachable by link
VISIBLE = {
    None: ["home", "villages", "ask", "design", "fund", "plan"],
    "community": ["home", "dash", "ask", "villages"],
    "cares": ["home", "dash", "design", "villages", "plan"],
    "funder": ["home", "dash", "fund", "villages", "plan"],
}[role]
order = VISIBLE + [k for k in PAGES if k not in VISIBLE]
pages = [st.Page(PAGES[k][0], title=PAGES[k][1], icon=PAGES[k][2], url_path=PAGES[k][3], default=(k == "home"),
                 visibility="visible" if k in VISIBLE else "hidden") for k in order]
nav = st.navigation(pages, position="top")

auth.account_menu()
nav.run()

with st.container(key="footer"):
    st.caption(f"{ui.DISCLAIMER} Built on public information from "
               "[Solar Village SDG](https://www.solarvillagesdg.org/projects) and its project report.")
