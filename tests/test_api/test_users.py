from fastapi.testclient import TestClient


def test_create_user(client: TestClient):
    resp = client.post(
        "/api/users",
        json={"name": "New User", "email": "new@example.com", "role": "drafter"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New User"
    assert data["role"] == "drafter"


def test_create_user_duplicate_email(client: TestClient):
    client.post(
        "/api/users",
        json={"name": "User 1", "email": "dup@example.com", "role": "drafter"},
    )
    resp = client.post(
        "/api/users",
        json={"name": "User 2", "email": "dup@example.com", "role": "reviewer"},
    )
    assert resp.status_code == 409


def test_list_users(client: TestClient):
    client.post(
        "/api/users",
        json={"name": "Listed", "email": "listed@example.com", "role": "admin"},
    )
    resp = client.get("/api/users")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_user(client: TestClient):
    create_resp = client.post(
        "/api/users",
        json={"name": "Fetched", "email": "fetched@example.com", "role": "reviewer"},
    )
    user_id = create_resp.json()["id"]
    resp = client.get(f"/api/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Fetched"


def test_get_user_not_found(client: TestClient):
    resp = client.get("/api/users/nonexistent")
    assert resp.status_code == 404
