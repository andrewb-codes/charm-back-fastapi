import streamlit as st

from core.session import load_profile, logout
from views.admin import render_admin_profiles
from views.auth import render_auth
from views.discovery import render_charm
from views.matches import render_matches
from views.profile import render_account_settings, render_profile


def render_app() -> None:
    profile = load_profile()
    if profile is None:
        render_auth()
        return

    st.sidebar.title("Charm")
    st.sidebar.write(profile["email"])
    if st.sidebar.button("Logout"):
        logout()

    tab_names = ["Profile", "Account", "Discovery", "Matches"]
    if profile["role"] == "ADMIN":
        tab_names.append("Admin")

    tabs = st.tabs(tab_names)
    profile_tab, account_tab, charm_tab, matches_tab = tabs[:4]

    with profile_tab:
        render_profile(profile)
    with account_tab:
        render_account_settings(profile)
    with charm_tab:
        render_charm()
    with matches_tab:
        render_matches()
    if profile["role"] == "ADMIN":
        with tabs[4]:
            render_admin_profiles()


st.set_page_config(page_title="Charm", page_icon="CH", layout="centered")
render_app()
