from typing import Any, cast

import streamlit as st

from core.api import request, show_error


def auth_token() -> str | None:
    return st.session_state.get("access_token")


def logout() -> None:
    st.session_state.pop("access_token", None)
    st.session_state.pop("current_profile", None)
    st.rerun()


def load_profile() -> dict[str, Any] | None:
    token = auth_token()
    if not token:
        return None

    response = request("GET", "/api/v1/profile", token=token)
    if response.is_success:
        profile = cast(dict[str, Any], response.json())
        st.session_state.current_profile = profile
        return profile

    if response.status_code == 401:
        logout()
    else:
        show_error(response)

    return None
