import json

from fastapi.testclient import TestClient

from tests.conftest import make_docx


def _create_template(client: TestClient, user_id: str) -> str:
    content = make_docx("Version 1 content")
    resp = client.post(
        "/api/templates",
        files={"file": ("v1.docx", content)},
        data={"metadata": json.dumps({"name": "Versioned", "template_type": "NDA"})},
        headers={"X-User-Id": user_id},
    )
    return resp.json()["id"]


def test_upload_new_version(client: TestClient, sample_user):
    template_id = _create_template(client, sample_user.id)
    v2_content = make_docx("Version 2 content")
    resp = client.post(
        f"/api/templates/{template_id}/versions",
        files={"file": ("v2.docx", v2_content)},
        data={"change_summary": "Updated terms"},
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 201
    assert resp.json()["version_number"] == 2


def test_list_versions(client: TestClient, sample_user):
    template_id = _create_template(client, sample_user.id)
    v2 = make_docx("v2")
    client.post(
        f"/api/templates/{template_id}/versions",
        files={"file": ("v2.docx", v2)},
        data={"change_summary": "v2"},
        headers={"X-User-Id": sample_user.id},
    )
    resp = client.get(f"/api/templates/{template_id}/versions")
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2


def test_download_version_round_trip(client: TestClient, sample_user):
    original = make_docx("Round trip test")
    resp = client.post(
        "/api/templates",
        files={"file": ("rt.docx", original)},
        data={"metadata": json.dumps({"name": "RT", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    template_id = resp.json()["id"]
    dl_resp = client.get(f"/api/templates/{template_id}/versions/1/download")
    assert dl_resp.status_code == 200
    assert dl_resp.content == original


def test_download_nonexistent_version(client: TestClient, sample_user):
    template_id = _create_template(client, sample_user.id)
    resp = client.get(f"/api/templates/{template_id}/versions/999/download")
    assert resp.status_code == 404
