import streamlit as st

from frontend.api_client import APIClient


def render(client: APIClient) -> None:
    st.header("Stale Template Alerts")

    try:
        stale = client.get_stale_templates()
    except Exception as e:
        st.error(f"Error loading stale templates: {e}")
        return

    if not stale:
        st.success("No stale templates. All published templates are within their review period.")
        return

    st.warning(f"{len(stale)} template(s) need review")

    for item in stale:
        days = item.get("days_overdue", 0)
        if days > 90:
            severity = ":red[CRITICAL]"
        elif days > 30:
            severity = ":orange[WARNING]"
        else:
            severity = ":yellow[NOTICE]"

        with st.expander(
            f"{severity} **{item['name']}** — {days} days overdue", expanded=True
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Type:** {item['template_type']}")
                st.write(f"**Owner:** {item.get('owner_name', item.get('owner_id', 'N/A'))}")
            with col2:
                st.write(f"**Review Due:** {item.get('review_due_date', 'N/A')}")
                st.write(f"**Days Overdue:** {days}")
            with col3:
                st.write(f"**Current Version:** {item.get('current_version', 'N/A')}")
                st.write(f"**Last Reviewed:** {item.get('last_reviewed_at') or 'Never'}")
