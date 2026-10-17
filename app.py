"""CARES Connect - entry point.  Run with:  streamlit run app.py"""
import streamlit as st

from app_core import auth, store
from app_core.ui import DISCLAIMER

st.set_page_config(page_title="CARES Connect", page_icon="☀️", layout="wide")
store.init_db()

pages = {
    "": [st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
         st.Page("views/villages.py", title="Real solar villages", icon=":material/solar_power:")],
    "My account": [
        st.Page("views/dashboard.py", title="My dashboard", icon=":material/dashboard:"),
        st.Page("views/account.py", title="Sign in or register", icon=":material/login:"),
    ],
    "The three fronts": [
        st.Page("views/local.py", title="1 · Locals: ask for help", icon=":material/agriculture:"),
        st.Page("views/cares.py", title="2 · CARES: design a solution", icon=":material/engineering:"),
        st.Page("views/funders.py", title="3 · Funders: back a project", icon=":material/volunteer_activism:"),
    ],
    "For government": [
        st.Page("views/overview.py", title="4 · Overview & scenarios", icon=":material/map:"),
    ],
}
nav = st.navigation(pages)
with st.sidebar:
    auth.sidebar_switcher()
    st.caption(DISCLAIMER)
nav.run()
