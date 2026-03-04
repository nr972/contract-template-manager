from unittest.mock import patch

from fastapi.testclient import TestClient


def test_shutdown_returns_ok(client: TestClient):
    with patch("ctm_app.api.shutdown.os.kill"):
        resp = client.post("/api/v1/shutdown")
        assert resp.status_code == 200
        assert resp.json() == {"status": "shutting_down"}
