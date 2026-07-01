import streamlit as st

from core.api import request, show_error


def render_auth() -> None:
    st.title("Charm")

    login_tab, registration_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")

        if submitted:
            response = request(
                "POST",
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            if response.is_success:
                st.session_state.access_token = response.json()["access_token"]
                st.rerun()
            else:
                show_error(response)

    with registration_tab:
        with st.form("registration"):
            email = st.text_input("Email", key="registration_email")
            password = st.text_input("Password", type="password", key="registration_password")
            submitted = st.form_submit_button("Create account")

        if submitted:
            response = request(
                "POST",
                "/api/v1/registration",
                json={"email": email, "password": password},
            )
            if response.is_success:
                st.success("Account created. You can login now.")
            else:
                show_error(response)
