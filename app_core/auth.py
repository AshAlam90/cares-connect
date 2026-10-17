"""Demo sign-in: the signed-in profile lives in the browser session.

There are deliberately no passwords. A real system would use a secure login
provider (e.g. OpenID Connect) and keep personal data under a
data-protection plan agreed with partners.
"""
from __future__ import annotations

import streamlit as st

from . import store

ROLE_ICON = {"community": "🧑‍🌾", "cares": "🎓", "funder": "🤝"}


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


def sidebar_switcher() -> None:
    """Quick profile switcher, so a demo can move between the three fronts in seconds."""
    users = store.list_users()
    cur = st.session_state.get("user_id")
    options = [None] + [u["id"] for u in users]
    names = {u["id"]: label(u) for u in users}
    key = f"switch_{cur}"           # new widget whenever the user changes elsewhere

    def _changed():
        v = st.session_state[key]
        sign_out() if v is None else sign_in(v)

    st.selectbox("Signed in as (demo switch)", options,
                 index=options.index(cur) if cur in options else 0,
                 format_func=lambda x: "Not signed in" if x is None else names[x],
                 key=key, on_change=_changed)
