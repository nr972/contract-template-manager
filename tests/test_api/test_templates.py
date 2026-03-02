import json

from fastapi.testclient import TestClient

from tests.conftest import make_docx


def test_create_template(client: TestClient, sample_user):
    content = make_docx("NDA content")
    resp = client.post(
        "/api/templates",
        files={"file": ("test.docx", content)},
        data={"metadata": json.dumps({"name": "Test NDA", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test NDA"
    assert data["template_type"] == "NDA"
    assert data["status"] == "draft"
    assert data["current_version"] == 1


def test_create_template_missing_metadata(client: TestClient, sample_user):
    content = make_docx()
    resp = client.post(
        "/api/templates",
        files={"file": ("test.docx", content)},
        data={"metadata": json.dumps({"name": "Test"})},
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 400
    assert "template_type" in resp.json()["detail"]


def test_create_template_invalid_file(client: TestClient, sample_user):
    resp = client.post(
        "/api/templates",
        files={"file": ("test.txt", b"not a docx file")},
        data={"metadata": json.dumps({"name": "Bad", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 400


def test_list_templates(client: TestClient, sample_user):
    content = make_docx()
    client.post(
        "/api/templates",
        files={"file": ("a.docx", content)},
        data={"metadata": json.dumps({"name": "Template A", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    resp = client.get("/api/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["templates"]) >= 1


def test_list_templates_search(client: TestClient, sample_user):
    content = make_docx()
    client.post(
        "/api/templates",
        files={"file": ("a.docx", content)},
        data={"metadata": json.dumps({"name": "Special NDA", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    resp = client.get("/api/templates", params={"q": "Special"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_get_template(client: TestClient, sample_user):
    content = make_docx()
    create_resp = client.post(
        "/api/templates",
        files={"file": ("a.docx", content)},
        data={"metadata": json.dumps({"name": "Get Test", "template_type": "MSA"})},
        headers={"X-User-Id": sample_user.id},
    )
    template_id = create_resp.json()["id"]
    resp = client.get(f"/api/templates/{template_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Test"


def test_get_template_not_found(client: TestClient):
    resp = client.get("/api/templates/nonexistent-id")
    assert resp.status_code == 404


def test_update_template(client: TestClient, sample_user):
    content = make_docx()
    create_resp = client.post(
        "/api/templates",
        files={"file": ("a.docx", content)},
        data={"metadata": json.dumps({"name": "Original", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    template_id = create_resp.json()["id"]
    resp = client.put(
        f"/api/templates/{template_id}",
        json={"name": "Updated Name"},
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_delete_template_soft_deletes(client: TestClient, sample_user):
    content = make_docx()
    create_resp = client.post(
        "/api/templates",
        files={"file": ("a.docx", content)},
        data={"metadata": json.dumps({"name": "To Delete", "template_type": "NDA"})},
        headers={"X-User-Id": sample_user.id},
    )
    template_id = create_resp.json()["id"]
    resp = client.delete(
        f"/api/templates/{template_id}",
        headers={"X-User-Id": sample_user.id},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "retired"
