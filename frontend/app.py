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

    # Shutdown button
    st.sidebar.markdown("---")
    if st.sidebar.button("Shutdown", type="secondary", use_container_width=True):
        client.shutdown()
        import streamlit.components.v1 as components

        components.html(
            """<script>
            (function() {
                var doc = window.parent.document;
                doc.open();
                doc.write(
                    '<!DOCTYPE html><html lang="en"><head>' +
                    '<meta charset="UTF-8">' +
                    '<meta name="viewport" content="width=device-width,initial-scale=1.0">' +
                    '<title>App Shut Down</title>' +
                    '<style>' +
                    '* { margin:0; padding:0; box-sizing:border-box; }' +
                    'body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;' +
                    ' display:flex; align-items:center; justify-content:center;' +
                    ' min-height:100vh; background:#f8f9fa; color:#333; }' +
                    '.c { text-align:center; padding:2rem; }' +
                    'h1 { font-size:1.5rem; margin-bottom:0.75rem; }' +
                    'p  { font-size:1rem; color:#666; }' +
                    '</style></head><body>' +
                    '<div class="c"><h1>App has been shut down.</h1>' +
                    '<p>You can close this tab.</p></div>' +
                    '</body></html>'
                );
                doc.close();
            })();
            </script>""",
            height=0,
            scrolling=False,
        )
        st.stop()

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
