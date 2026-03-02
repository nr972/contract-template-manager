import json

from fastapi.testclient import TestClient

from tests.conftest import make_docx


def _create_template(client: TestClient, user_id: str) -> str:
    content = make_docx()
    resp = client.post(
        "/api/templates",
        files={"file": ("t.docx", content)},
        data={"metadata": json.dumps({"name": "WF Test", "template_type": "NDA"})},
        headers={"X-User-Id": user_id},
    )
    return resp.json()["id"]


def test_full_workflow_lifecycle(client: TestClient, sample_user, reviewer_user, approver_user):
    template_id = _create_template(client, sample_user.id)

    # draft -> review (drafter)
    resp = client.post(
        f"/api/templates/{template_id}/workflow/transition",
        json={"to_status": "review", "comment": "Ready"},
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 201
    assert resp.json()["to_status"] == "review"

    # review -> approved (reviewer)
    resp = client.post(
        f"/api/templates/{template_id}/workflow/transition",
        json={"to_status": "approved"},
        headers={"X-User-Id": reviewer_user.id},
    )
    assert resp.status_code == 201

    # approved -> published (approver)
    resp = client.post(
        f"/api/templates/{template_id}/workflow/transition",
        json={"to_status": "published"},
        headers={"X-User-Id": approver_user.id},
    )
    assert resp.status_code == 201

    # Verify final status
    tmpl = client.get(f"/api/templates/{template_id}").json()
    assert tmpl["status"] == "published"
    assert tmpl["last_reviewed_at"] is not None


def test_invalid_transition(client: TestClient, sample_user):
    template_id = _create_template(client, sample_user.id)
    # Can't go draft -> published
    resp = client.post(
        f"/api/templates/{template_id}/workflow/transition",
        json={"to_status": "published"},
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 400


def test_insufficient_role(client: TestClient, sample_user, reviewer_user, approver_user):
    template_id = _create_template(client, sample_user.id)
    # Transition to review first
    client.post(
        f"/api/templates/{template_id}/workflow/transition",
        json={"to_status": "review"},
        headers={"X-User-Id": sample_user.id},
    )
    client.post(
        f"/api/templates/{template_id}/workflow/transition",
        json={"to_status": "approved"},
        headers={"X-User-Id": reviewer_user.id},
    )
    # Drafter can't publish
    resp = client.post(
        f"/api/templates/{template_id}/workflow/transition",
        json={"to_status": "published"},
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 403


def test_workflow_history(client: TestClient, sample_user, reviewer_user):
    template_id = _create_template(client, sample_user.id)
    client.post(
        f"/api/templates/{template_id}/workflow/transition",
        json={"to_status": "review", "comment": "Please review"},
        headers={"X-User-Id": sample_user.id},
    )
    resp = client.get(f"/api/templates/{template_id}/workflow/history")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 1
    assert history[0]["from_status"] == "draft"
    assert history[0]["to_status"] == "review"


def test_available_transitions(client: TestClient, sample_user):
    template_id = _create_template(client, sample_user.id)
    resp = client.get(
        f"/api/templates/{template_id}/workflow/available-transitions",
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "review" in data["available_transitions"]
