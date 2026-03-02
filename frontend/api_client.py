import os

import requests


class APIClient:
    def __init__(self) -> None:
        self.base_url = os.environ.get("CTM_API_BASE_URL", "http://localhost:8000/api")
        self._user_id: str | None = None

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @user_id.setter
    def user_id(self, value: str) -> None:
        self._user_id = value

    def _headers(self) -> dict:
        headers = {}
        if self._user_id:
            headers["X-User-Id"] = self._user_id
        return headers

    def list_users(self) -> list[dict]:
        resp = requests.get(f"{self.base_url}/users", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def create_user(self, name: str, email: str, role: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/users",
            json={"name": name, "email": email, "role": role},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def list_templates(self, **params) -> dict:
        resp = requests.get(
            f"{self.base_url}/templates",
            params={k: v for k, v in params.items() if v is not None},
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_template(self, template_id: str) -> dict:
        resp = requests.get(
            f"{self.base_url}/templates/{template_id}",
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def upload_template(self, file_bytes: bytes, filename: str, metadata: dict) -> dict:
        import json

        resp = requests.post(
            f"{self.base_url}/templates",
            files={"file": (filename, file_bytes)},
            data={"metadata": json.dumps(metadata)},
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def upload_version(
        self, template_id: str, file_bytes: bytes, filename: str, change_summary: str
    ) -> dict:
        resp = requests.post(
            f"{self.base_url}/templates/{template_id}/versions",
            files={"file": (filename, file_bytes)},
            data={"change_summary": change_summary},
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def list_versions(self, template_id: str) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/templates/{template_id}/versions",
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def download_version(self, template_id: str, version_number: int) -> bytes:
        resp = requests.get(
            f"{self.base_url}/templates/{template_id}/versions/{version_number}/download",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.content

    def transition_workflow(
        self, template_id: str, to_status: str, comment: str | None = None
    ) -> dict:
        resp = requests.post(
            f"{self.base_url}/templates/{template_id}/workflow/transition",
            json={"to_status": to_status, "comment": comment},
            headers={**self._headers(), "Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_workflow_history(self, template_id: str) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/templates/{template_id}/workflow/history",
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_available_transitions(self, template_id: str) -> dict:
        resp = requests.get(
            f"{self.base_url}/templates/{template_id}/workflow/available-transitions",
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_diff(self, template_id: str, from_version: int, to_version: int) -> dict:
        resp = requests.get(
            f"{self.base_url}/templates/{template_id}/diff",
            params={"from_version": from_version, "to_version": to_version},
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_stale_templates(self) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/templates/stale",
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
