import streamlit as st

from app_core import auth, store, ui
from app_core.i18n import OPTIONS
from engine import COUNTRIES

st.title("Sign in or register")
st.write("Each of the three fronts gets its own dashboard. Communities follow their requests, "
         "CARES units manage their queue and projects, and funders track their pledges and impact.")
ui.disclaimer()

user = auth.current_user()
if user:
    with st.container(border=True):
        st.markdown(f"**{auth.label(user)}**  \n{user['name']}")
        c1, c2, _ = st.columns([1, 1, 3])
        if c1.button("Go to my dashboard", type="primary"):
            st.switch_page("views/dashboard.py")
        if c2.button("Sign out"):
            auth.sign_out()
            st.rerun()

tab_in, tab_up = st.tabs(["Sign in", "Register"])

ROLE_HELP = {
    "community": "A farmer, cooperative or Village Development Committee asking for help",
    "cares": "A local university unit that designs and supports projects",
    "funder": "A company CSR fund, SME, NGO, development bank or government body",
}

with tab_in:
    role = st.radio("I am a", list(store.ROLES), format_func=store.ROLES.get, horizontal=True, key="in_role",
                    captions=[ROLE_HELP[r] for r in store.ROLES])
    users = store.list_users(role)
    if not users:
        st.info("No profiles yet for this role. Register one.")
    else:
        uid = st.selectbox("Profile", [u["id"] for u in users],
                           format_func=lambda i: next(f"{u['organisation']} · {u['name']}" for u in users if u["id"] == i))
        if st.button("Sign in", type="primary", key="do_sign_in"):
            auth.sign_in(uid)
            st.switch_page("views/dashboard.py")
    st.caption("Demo sign-in without passwords. A real system would use a secure login provider.")

with tab_up:
    role_up = st.radio("Register as", list(store.ROLES), format_func=store.ROLES.get, horizontal=True,
                       key="up_role", captions=[ROLE_HELP[r] for r in store.ROLES])
    up_cc = st.segmented_control("Country", list(COUNTRIES), format_func=lambda c: COUNTRIES[c]["name"],
                                 default="LK", required=True, key="up_country")
    D = COUNTRIES[up_cc]["districts"]
    with st.form("register"):
        name = st.text_input("Your name or role", placeholder="e.g. Secretary, programme officer")
        if role_up == "community":
            c1, c2 = st.columns(2)
            village = c1.text_input("Village or group name")
            district = c2.selectbox("District", D, index=None, placeholder="Choose a district")
            group_type = st.selectbox("Who are you?", list(OPTIONS["who"])[:3])
            langs = COUNTRIES[up_cc]["languages"]
            language = st.radio("Preferred language", list(langs), horizontal=True, format_func=langs.get,
                                index=len(langs) - 1)
            organisation = f"{village} {group_type.lower()}" if village else ""
        elif role_up == "cares":
            organisation = st.text_input("CARES unit (university and department)")
            coverage = st.multiselect("Districts you cover", D)
            language = "en"
        else:
            c1, c2 = st.columns(2)
            organisation = c1.text_input("Organisation")
            funder_type = c2.selectbox("Type", store.FUNDER_TYPES)
            int_d = st.multiselect("Districts of interest (optional)", D)
            int_s = st.multiselect("Solutions of interest (optional)", COUNTRIES[up_cc]["needs"])
            language = "en"
        consent = st.checkbox("I understand this is a demonstration and I will not enter real personal information.")
        done = st.form_submit_button("Create profile and sign in", type="primary")

    if done:
        missing = []
        if not name.strip():
            missing.append("your name or role")
        if role_up == "community" and (not village.strip() or not district):
            missing.append("village and district")
        if role_up == "cares" and (not organisation.strip() or not coverage):
            missing.append("unit name and at least one district")
        if role_up == "funder" and not organisation.strip():
            missing.append("organisation")
        if not consent:
            missing.append("the demonstration check-box")
        if missing:
            st.error("Please add: " + ", ".join(missing) + ".")
        else:
            if role_up == "community":
                uid = store.add_user("community", name.strip(), organisation.strip(), country=up_cc,
                                     village=village.strip(), district=district, group_type=group_type,
                                     language=language)
            elif role_up == "cares":
                uid = store.add_user("cares", name.strip(), organisation.strip(), country=up_cc, coverage=coverage)
            else:
                uid = store.add_user("funder", name.strip(), organisation.strip(), country=up_cc,
                                     funder_type=funder_type, interests={"districts": int_d, "solutions": int_s})
            auth.sign_in(uid)
            st.switch_page("views/dashboard.py")
