import streamlit as st

from charm.frontend.core.api import request, show_error
from charm.frontend.core.session import auth_token


def render_matches() -> None:
    st.subheader("Matches")

    response = request(
        "GET",
        "/api/v1/matches",
        token=auth_token(),
        params={"page": 1, "page_size": 20},
    )
    if response is None:
        return
    if not response.is_success:
        show_error(response)
        return

    matches = response.json()["items"]
    if not matches:
        st.info("No matches yet.")
        return

    for profile in matches:
        title = " ".join(item for item in [profile.get("name"), profile.get("surname")] if item)
        with st.container(border=True):
            st.write(title or f"Profile #{profile['id']}")
            if profile.get("age") is not None:
                st.caption(f"{profile['age']} years old")
            if profile.get("about"):
                st.write(profile["about"])
