import streamlit as st

from ctm_frontend.api_client import APIClient


def render(client: APIClient) -> None:
    st.header("Upload Template")

    mode = st.radio("Mode", ["New Template", "New Version of Existing Template"])

    if mode == "New Template":
        _new_template(client)
    else:
        _new_version(client)


def _new_template(client: APIClient) -> None:
    with st.form("new_template_form"):
        name = st.text_input("Template Name", placeholder="e.g., Mutual NDA")
        template_type = st.selectbox(
            "Template Type",
            ["NDA", "MSA", "SOW", "SLA", "Consulting Agreement",
             "Software License", "Employment Agreement", "DPA", "Other"],
        )
        use_case = st.text_input(
            "Use Case (optional)", placeholder="e.g., Vendor onboarding"
        )
        description = st.text_area("Description (optional)")
        review_interval = st.number_input(
            "Review Interval (days)", min_value=1, max_value=3650, value=365
        )
        file = st.file_uploader("Upload .docx file", type=["docx"])
        submitted = st.form_submit_button("Upload Template")

    if submitted:
        if not name:
            st.error("Template name is required.")
            return
        if not file:
            st.error("Please upload a .docx file.")
            return

        metadata = {
            "name": name,
            "template_type": template_type,
            "use_case": use_case or None,
            "description": description or None,
            "review_interval_days": review_interval,
        }

        try:
            result = client.upload_template(file.read(), file.name, metadata)
            st.success(f"Template '{result['name']}' created (v{result['current_version']})")
        except Exception as e:
            st.error(f"Upload failed: {e}")


def _new_version(client: APIClient) -> None:
    try:
        data = client.list_templates(limit=200)
        templates = data.get("templates", [])
    except Exception as e:
        st.error(f"Error loading templates: {e}")
        return

    if not templates:
        st.info("No templates exist yet. Create one first.")
        return

    template_options = {t["id"]: f"{t['name']} (v{t['current_version']})" for t in templates}

    with st.form("new_version_form"):
        selected_id = st.selectbox(
            "Select Template",
            options=list(template_options.keys()),
            format_func=lambda tid: template_options[tid],
        )
        change_summary = st.text_area(
            "Change Summary", placeholder="Describe what changed in this version..."
        )
        file = st.file_uploader("Upload updated .docx file", type=["docx"])
        submitted = st.form_submit_button("Upload New Version")

    if submitted:
        if not file:
            st.error("Please upload a .docx file.")
            return

        try:
            result = client.upload_version(
                selected_id, file.read(), file.name, change_summary or ""
            )
            st.success(f"Version {result['version_number']} uploaded")
        except Exception as e:
            st.error(f"Upload failed: {e}")
