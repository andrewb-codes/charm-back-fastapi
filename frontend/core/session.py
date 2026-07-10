from typing import Any, cast

import streamlit as st

from frontend.core.api import request, show_error


def auth_token() -> str | None:
    token = st.session_state.get("access_token")
    return token if isinstance(token, str) else None


def login(token: str) -> None:
    st.session_state.access_token = token
    st.rerun()


def logout() -> None:
    st.session_state.pop("access_token", None)
    st.session_state.pop("current_profile", None)
    st.session_state.pop("admin_profiles", None)
    st.rerun()


def load_profile() -> dict[str, Any] | None:
    token = auth_token()
    if token is None:
        return None

    response = request("GET", "/api/v1/profile", token=token)
    if response is None:
        return None

    if response.is_success:
        profile = cast(dict[str, Any], response.json())
        st.session_state.current_profile = profile
        return profile

    if response.status_code == 401:
        logout()
    show_error(response)

    return None
