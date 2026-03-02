import streamlit as st

from frontend.api_client import APIClient

st.set_page_config(page_title="Contract Template Manager", layout="wide")


@st.cache_resource
def get_client() -> APIClient:
    return APIClient()


def main() -> None:
    client = get_client()

    st.sidebar.title("Contract Template Manager")

    # User selector
    try:
        users = client.list_users()
    except Exception:
        st.error("Cannot connect to the API. Is the backend running on port 8000?")
        st.stop()

    if not users:
        st.warning("No users found. Create users via the API first, or run the seed script.")
        st.stop()

    user_options = {u["id"]: f"{u['name']} ({u['role']})" for u in users}
    selected_id = st.sidebar.selectbox(
        "Acting as:",
        options=list(user_options.keys()),
        format_func=lambda uid: user_options[uid],
    )
    client.user_id = selected_id
    st.session_state["current_user"] = next(u for u in users if u["id"] == selected_id)

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Template Registry", "Upload Template", "Stale Alerts"],
    )

    if page == "Template Registry":
        from frontend.pages.template_registry import render

        render(client)
    elif page == "Upload Template":
        from frontend.pages.upload_template import render

        render(client)
    elif page == "Stale Alerts":
        from frontend.pages.stale_alerts import render

        render(client)


if __name__ == "__main__":
    main()
