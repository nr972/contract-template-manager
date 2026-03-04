import streamlit as st

from ctm_frontend.api_client import APIClient


def render(client: APIClient) -> None:
    st.header("Template Registry")

    # Search and filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("Search", placeholder="Search by name or description...")
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "draft", "review", "approved", "published", "retired"],
        )
    with col3:
        type_filter = st.text_input("Template Type", placeholder="e.g., NDA, MSA...")

    params: dict = {}
    if search:
        params["q"] = search
    if status_filter != "All":
        params["status"] = status_filter
    if type_filter:
        params["template_type"] = type_filter

    try:
        data = client.list_templates(**params)
    except Exception as e:
        st.error(f"Error loading templates: {e}")
        return

    templates = data.get("templates", [])
    total = data.get("total", 0)

    st.caption(f"{total} template(s) found")

    if not templates:
        st.info("No templates found. Upload one to get started.")
        return

    for t in templates:
        status_colors = {
            "draft": ":gray[Draft]",
            "review": ":orange[In Review]",
            "approved": ":blue[Approved]",
            "published": ":green[Published]",
            "retired": ":red[Retired]",
        }
        status_badge = status_colors.get(t["status"], t["status"])
        stale_indicator = " :red[STALE]" if t.get("is_stale") else ""

        with st.expander(f"**{t['name']}** — {status_badge}{stale_indicator}", expanded=False):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Type:** {t['template_type']}")
                st.write(f"**Use Case:** {t.get('use_case') or 'N/A'}")
                st.write(f"**Owner:** {t.get('owner_name') or t['owner_id']}")
            with col_b:
                st.write(f"**Version:** {t['current_version']}")
                st.write(f"**Status:** {t['status']}")
                st.write(f"**Last Reviewed:** {t.get('last_reviewed_at') or 'Never'}")

            if t.get("description"):
                st.write(f"**Description:** {t['description']}")

            if st.button("View Details", key=f"view_{t['id']}"):
                st.session_state["selected_template_id"] = t["id"]
                st.session_state["show_detail"] = True
                st.rerun()

    # Template detail view
    if st.session_state.get("show_detail"):
        _render_detail(client, st.session_state["selected_template_id"])


def _render_detail(client: APIClient, template_id: str) -> None:
    st.divider()
    st.subheader("Template Details")

    if st.button("Back to Registry"):
        st.session_state["show_detail"] = False
        st.rerun()

    try:
        template = client.get_template(template_id)
        versions = client.list_versions(template_id)
    except Exception as e:
        st.error(f"Error loading template: {e}")
        return

    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", template["status"].upper())
        st.write(f"**Type:** {template['template_type']}")
        st.write(f"**Owner:** {template.get('owner_name', template['owner_id'])}")
    with col2:
        st.metric("Current Version", template["current_version"])
        st.write(f"**Use Case:** {template.get('use_case') or 'N/A'}")
        st.write(f"**Review Interval:** {template['review_interval_days']} days")
    with col3:
        stale_text = "YES" if template.get("is_stale") else "No"
        st.metric("Stale", stale_text)
        st.write(f"**Last Reviewed:** {template.get('last_reviewed_at') or 'Never'}")
        if template.get("days_until_review_due") is not None:
            days = template["days_until_review_due"]
            label = f"{abs(days)} days {'overdue' if days < 0 else 'remaining'}"
            st.write(f"**Review Due:** {label}")

    if template.get("description"):
        st.write(f"**Description:** {template['description']}")

    # Workflow actions
    st.subheader("Workflow")
    try:
        transitions = client.get_available_transitions(template_id)
        available = transitions.get("available_transitions", [])
    except Exception:
        available = []

    if available:
        col_w1, col_w2 = st.columns([1, 2])
        with col_w1:
            target = st.selectbox("Transition to:", available)
        with col_w2:
            comment = st.text_input("Comment (optional)", key="wf_comment")

        if st.button("Execute Transition"):
            try:
                client.transition_workflow(template_id, target, comment or None)
                st.success(f"Transitioned to {target}")
                st.rerun()
            except Exception as e:
                st.error(f"Transition failed: {e}")
    else:
        st.info("No transitions available for your role in the current status.")

    # Workflow history
    try:
        history = client.get_workflow_history(template_id)
    except Exception:
        history = []

    if history:
        st.subheader("Workflow History")
        for h in history:
            st.write(
                f"**{h['from_status']}** -> **{h['to_status']}** "
                f"by {h.get('transitioned_by_name', 'Unknown')} "
                f"— {h.get('comment', '')}"
            )

    # Version history
    st.subheader("Versions")
    for v in versions:
        col_v1, col_v2, col_v3 = st.columns([2, 2, 1])
        with col_v1:
            st.write(
                f"**v{v['version_number']}** — {v.get('uploaded_by_name', 'Unknown')}"
            )
        with col_v2:
            st.write(v.get("change_summary") or "No summary")
        with col_v3:
            if st.button("Download", key=f"dl_{v['id']}"):
                file_bytes = client.download_version(template_id, v["version_number"])
                st.download_button(
                    "Save File",
                    data=file_bytes,
                    file_name=v["filename"],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"save_{v['id']}",
                )

    # Diff viewer
    if len(versions) >= 2:
        st.subheader("Compare Versions")
        version_nums = [v["version_number"] for v in versions]
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            v_from = st.selectbox("From version:", sorted(version_nums), key="diff_from")
        with col_d2:
            v_to = st.selectbox(
                "To version:",
                sorted(version_nums),
                index=min(1, len(version_nums) - 1),
                key="diff_to",
            )

        if st.button("Compare"):
            if v_from == v_to:
                st.warning("Select two different versions to compare.")
            else:
                st.session_state["diff_data"] = {
                    "template_id": template_id,
                    "from_version": v_from,
                    "to_version": v_to,
                }
                st.rerun()

    if "diff_data" in st.session_state:
        _render_diff(client, st.session_state["diff_data"])


def _render_diff(client: APIClient, diff_params: dict) -> None:
    try:
        diff = client.get_diff(
            diff_params["template_id"],
            diff_params["from_version"],
            diff_params["to_version"],
        )
    except Exception as e:
        st.error(f"Error computing diff: {e}")
        return

    st.subheader(f"Diff: Version {diff_params['from_version']} vs {diff_params['to_version']}")

    side_by_side = diff.get("side_by_side", [])
    changes = [l for l in side_by_side if l["change_type"] != "equal"]
    st.caption(f"{len(changes)} change(s) found")

    col_left, col_right = st.columns(2)
    with col_left:
        st.write(f"**Version {diff_params['from_version']}**")
    with col_right:
        st.write(f"**Version {diff_params['to_version']}**")

    for line in side_by_side:
        ct = line["change_type"]
        left = line["content_left"]
        right = line["content_right"]

        col_l, col_r = st.columns(2)
        if ct == "equal":
            col_l.text(left)
            col_r.text(right)
        elif ct == "delete":
            col_l.markdown(f":red[~~{left}~~]")
            col_r.text("")
        elif ct == "insert":
            col_l.text("")
            col_r.markdown(f":green[{right}]")
        elif ct == "replace":
            col_l.markdown(f":red[{left}]" if left else "")
            col_r.markdown(f":green[{right}]" if right else "")

    if st.button("Close Diff"):
        del st.session_state["diff_data"]
        st.rerun()
