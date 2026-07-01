from typing import Any

import httpx
import streamlit as st

from core.config import frontend_settings

API_URL = frontend_settings.streamlit_api_url.rstrip("/")


def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else None

    with httpx.Client(base_url=API_URL, timeout=10.0) as client:
        return client.request(method, path, json=json, params=params, headers=headers)


def show_error(response: httpx.Response) -> None:
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text

    st.error(f"{response.status_code}: {detail}")
