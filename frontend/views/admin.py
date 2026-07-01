import streamlit as st

from core.api import request, show_error
from core.session import auth_token


def refresh_admin_profiles() -> None:
    st.session_state.pop("admin_profiles", None)
    st.rerun()


def render_admin_profile_controls(profile: dict[str, object]) -> None:
    profile_id = profile["id"]
    version = profile["version"]

    status_column, role_column = st.columns(2)

    with status_column:
        with st.form(f"admin_status_form_{profile_id}_{version}"):
            statuses = ["ACTIVE", "INACTIVE"]
            current_status = str(profile["status"])
            status = st.selectbox(
                "Status",
                statuses,
                index=statuses.index(current_status),
                key=f"admin_status_{profile_id}",
            )
            submitted = st.form_submit_button("Update status")

        if submitted:
            response = request(
                "PATCH",
                f"/api/v1/admin/profiles/{profile_id}/status",
                token=auth_token(),
                json={"status": status, "version": version},
            )
            if response.is_success:
                st.success("Status updated.")
                refresh_admin_profiles()
            else:
                show_error(response)

    with role_column:
        with st.form(f"admin_role_form_{profile_id}_{version}"):
            roles = ["ADMIN", "USER"]
            current_role = str(profile["role"])
            role = st.selectbox(
                "Role",
                roles,
                index=roles.index(current_role),
                key=f"admin_role_{profile_id}",
            )
            submitted = st.form_submit_button("Update role")

        if submitted:
            response = request(
                "PATCH",
                f"/api/v1/admin/profiles/{profile_id}/role",
                token=auth_token(),
                json={"role": role, "version": version},
            )
            if response.is_success:
                st.success("Role updated.")
                refresh_admin_profiles()
            else:
                show_error(response)


def render_admin_profiles() -> None:
    st.subheader("Profiles")

    with st.form("admin_profiles_filters"):
        email_starts_with = st.text_input("Email starts with")
        name_starts_with = st.text_input("Name starts with")
        surname_starts_with = st.text_input("Surname starts with")
        role = st.selectbox("Role", ["", "ADMIN", "USER"])
        status = st.selectbox("Status", ["", "ACTIVE", "INACTIVE"])
        page = st.number_input("Page", min_value=1, value=1)
        page_size = st.number_input("Page size", min_value=1, max_value=100, value=20)
        submitted = st.form_submit_button("Search")

    params = {
        "email_starts_with": email_starts_with or None,
        "name_starts_with": name_starts_with or None,
        "surname_starts_with": surname_starts_with or None,
        "role": role or None,
        "status": status or None,
        "page": page,
        "page_size": page_size,
    }
    params = {key: value for key, value in params.items() if value is not None}

    if submitted or "admin_profiles" not in st.session_state:
        response = request(
            "GET",
            "/api/v1/admin/profiles",
            token=auth_token(),
            params=params,
        )
        if response.is_success:
            st.session_state.admin_profiles = response.json()
        else:
            show_error(response)
            return

    result = st.session_state.admin_profiles
    profiles = result["items"]

    if not profiles:
        st.info("No profiles found.")
        return

    for item in profiles:
        title = item["email"]
        if item.get("name") or item.get("surname"):
            title = f"{item.get('name') or ''} {item.get('surname') or ''}".strip()

        with st.container(border=True):
            st.write(title)
            st.caption(f"ID {item['id']} | {item['email']} | {item['role']} | {item['status']}")
            if item.get("age") is not None:
                st.write(f"Age: {item['age']}")
            if item.get("about"):
                st.write(item["about"])
            st.caption(f"Version: {item['version']}")
            render_admin_profile_controls(item)

    if result["has_next"]:
        st.info("There are more profiles. Increase page or page size to continue.")
