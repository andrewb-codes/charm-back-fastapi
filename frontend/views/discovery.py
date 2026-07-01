from typing import Any

import streamlit as st

from core.api import request, show_error
from core.session import auth_token


def render_candidate_card(candidate: dict[str, Any]) -> None:
    title = " ".join(item for item in [candidate.get("name"), candidate.get("surname")] if item)
    st.subheader(title or f"Profile #{candidate['id']}")

    if candidate.get("age") is not None:
        st.caption(f"{candidate['age']} years old")

    if candidate.get("gender"):
        st.write(candidate["gender"])

    if candidate.get("about"):
        st.write(candidate["about"])

    cols = st.columns(3)
    actions = [("like", "Like"), ("dislike", "Dislike"), ("skip", "Skip")]

    for column, (action, label) in zip(cols, actions, strict=True):
        if column.button(label, use_container_width=True):
            response = request(
                "POST",
                "/api/v1/charm",
                token=auth_token(),
                json={"to_profile_id": candidate["id"], "action": action},
            )
            if response.is_success:
                st.rerun()
            else:
                show_error(response)


def render_charm() -> None:
    st.subheader("Discovery")

    response = request("GET", "/api/v1/charm", token=auth_token())
    if not response.is_success:
        show_error(response)
        return

    candidate = response.json()["profile"]
    if candidate is None:
        st.info("No candidates right now.")
        return

    render_candidate_card(candidate)
