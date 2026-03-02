import json

from fastapi.testclient import TestClient

from tests.conftest import make_docx


def test_diff_between_versions(client: TestClient, sample_user):
    v1 = make_docx("Original clause about liability.")
    resp = client.post(
        "/api/templates",
        files={"file": ("v1.docx", v1)},
        data={"metadata": json.dumps({"name": "Diff Test", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    template_id = resp.json()["id"]

    v2 = make_docx("Updated clause about indemnification.")
    client.post(
        f"/api/templates/{template_id}/versions",
        files={"file": ("v2.docx", v2)},
        data={"change_summary": "Changed liability to indemnification"},
        headers={"X-User-Id": sample_user.id},
    )

    diff_resp = client.get(
        f"/api/templates/{template_id}/diff",
        params={"from_version": 1, "to_version": 2},
    )
    assert diff_resp.status_code == 200
    data = diff_resp.json()
    assert data["template_id"] == template_id
    assert data["from_version"] == 1
    assert data["to_version"] == 2
    assert len(data["side_by_side"]) > 0
    # Should have at least one non-equal line
    changes = [l for l in data["side_by_side"] if l["change_type"] != "equal"]
    assert len(changes) > 0


def test_diff_nonexistent_version(client: TestClient, sample_user):
    v1 = make_docx("content")
    resp = client.post(
        "/api/templates",
        files={"file": ("v1.docx", v1)},
        data={"metadata": json.dumps({"name": "Diff404", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    template_id = resp.json()["id"]
    diff_resp = client.get(
        f"/api/templates/{template_id}/diff",
        params={"from_version": 1, "to_version": 99},
    )
    assert diff_resp.status_code == 404
