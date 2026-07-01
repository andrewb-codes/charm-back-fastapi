from typing import Any

import streamlit as st

from core.api import request, show_error
from core.session import auth_token, logout
from core.utils import parse_birthdate


def render_profile(profile: dict[str, Any]) -> None:
    st.subheader("Profile")

    with st.form("profile_form"):
        name = st.text_input("Name", value=profile.get("name") or "")
        surname = st.text_input("Surname", value=profile.get("surname") or "")
        birthdate = st.text_input(
            "Birthdate",
            value=profile.get("birthdate") or "",
            placeholder="YYYY-MM-DD or DD.MM.YYYY",
        )
        gender = st.selectbox(
            "Gender",
            ["", "MALE", "FEMALE", "OTHER"],
            index=["", "MALE", "FEMALE", "OTHER"].index(profile.get("gender") or ""),
        )
        about = st.text_area("About", value=profile.get("about") or "")
        submitted = st.form_submit_button("Save")

    if submitted:
        try:
            parsed_birthdate = parse_birthdate(birthdate)
        except ValueError as exc:
            st.error(str(exc))
            return

        payload = {
            "name": name or None,
            "surname": surname or None,
            "birthdate": parsed_birthdate,
            "gender": gender or None,
            "about": about or None,
            "version": profile["version"],
        }
        response = request(
            "PATCH",
            "/api/v1/profile",
            token=auth_token(),
            json=payload,
        )
        if response.is_success:
            st.session_state.current_profile = response.json()
            st.success("Profile updated.")
            st.rerun()
        else:
            show_error(response)


def render_account_settings(profile: dict[str, Any]) -> None:
    st.subheader("Account")

    with st.form("change_email_form"):
        new_email = st.text_input("New email", value=profile["email"])
        current_password = st.text_input(
            "Current password", type="password", key="email_current_password"
        )
        submitted = st.form_submit_button("Change email")

    if submitted:
        response = request(
            "PATCH",
            "/api/v1/profile/email",
            token=auth_token(),
            json={
                "new_email": new_email,
                "current_password": current_password,
                "version": profile["version"],
            },
        )
        if response.is_success:
            st.session_state.current_profile = response.json()
            st.success("Email updated.")
            st.rerun()
        else:
            show_error(response)

    with st.form("change_password_form"):
        current_password = st.text_input(
            "Current password", type="password", key="password_current_password"
        )
        new_password = st.text_input("New password", type="password")
        submitted = st.form_submit_button("Change password")

    if submitted:
        response = request(
            "PATCH",
            "/api/v1/profile/password",
            token=auth_token(),
            json={
                "current_password": current_password,
                "new_password": new_password,
                "version": profile["version"],
            },
        )
        if response.is_success:
            st.session_state.current_profile = response.json()
            st.success("Password updated.")
            st.rerun()
        else:
            show_error(response)

    with st.form("delete_account_form"):
        confirmed = st.checkbox("I understand this will permanently delete my account.")
        submitted = st.form_submit_button("Delete account")

    if submitted:
        if not confirmed:
            st.error("Confirm account deletion first.")
            return

        response = request("DELETE", "/api/v1/profile", token=auth_token())
        if response.is_success:
            logout()
        else:
            show_error(response)
