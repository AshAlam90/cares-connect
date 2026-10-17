"""Demo sign-in: the signed-in profile lives in the browser session.

There are deliberately no passwords. A real system would use a secure login
provider (e.g. OpenID Connect) and keep personal data under a
data-protection plan agreed with partners.
"""
from __future__ import annotations

import streamlit as st

from . import store

ROLE_ICON = {"community": "🧑‍🌾", "cares": "🎓", "funder": "🤝"}
ROLE_MATERIAL = {"community": ":material/agriculture:", "cares": ":material/school:",
                 "funder": ":material/volunteer_activism:"}
# Which fictional demo profile each "try a role" button opens
DEMO_PICK = {"community": "Demo village committee", "cares": "North & East", "funder": "Example Climate Foundation"}


def current_user() -> dict | None:
    uid = st.session_state.get("user_id")
    user = store.get_user(uid) if uid else None
    if uid and not user:                   # data was reset
        st.session_state.pop("user_id", None)
    return user


def sign_in(uid: int) -> None:
    st.session_state["user_id"] = uid


def sign_out() -> None:
    st.session_state.pop("user_id", None)


def label(u: dict) -> str:
    return f"{ROLE_ICON[u['role']]} {store.ROLES[u['role']]} · {u['organisation']}"


def short_org(u: dict, n: int = 30) -> str:
    org = u["organisation"].replace(" (fictional)", "").replace("Demo CARES unit · ", "")
    return org if len(org) <= n else org[: n - 1] + "…"


def demo_user(role: str) -> dict | None:
    users = store.list_users(role)
    want = DEMO_PICK[role]
    return next((u for u in users if want in u["organisation"]), users[0] if users else None)


def sign_in_demo(role: str) -> bool:
    u = demo_user(role)
    if u:
        sign_in(u["id"])
    return bool(u)


def account_menu() -> None:
    """Top-right account menu: who you are, your dashboard, and one-click demo roles."""
    user = current_user()
    with st.container(horizontal=True, horizontal_alignment="right", key="account_bar"):
        text = f"{short_org(user, 26)}" if user else "Try a role"
        icon = ROLE_MATERIAL[user["role"]] if user else ":material/person:"
        with st.popover(text, icon=icon):
            if user:
                st.markdown(f"**{user['organisation']}**  \n{store.ROLES[user['role']]} · {user['name']}")
                c1, c2 = st.columns(2)
                if c1.button("Dashboard", icon=":material/dashboard:", type="primary", width="stretch"):
                    st.switch_page("views/dashboard.py")
                if c2.button("Sign out", icon=":material/logout:", width="stretch"):
                    sign_out()
                    st.switch_page("views/home.py")
                st.divider()
            st.markdown("**See the app as…**")
            st.caption("Fictional demo profiles, no password needed.")
            for role, name in (("community", "A village committee"), ("cares", "A university CARES unit"),
                               ("funder", "A funder")):
                current = bool(user and user["id"] == (demo_user(role) or {}).get("id"))
                if st.button(name, icon=ROLE_MATERIAL[role], key=f"demo_{role}", width="stretch", disabled=current):
                    sign_in_demo(role)
                    st.switch_page("views/dashboard.py")
            st.page_link("views/account.py", label="Other profiles, or register your own", icon=":material/badge:")
