"""Seed the database with sample data by calling the API."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

API_BASE = os.environ.get("CTM_API_BASE_URL", "http://localhost:8000/api")
SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample"
SEED_DATA = SAMPLE_DIR / "seed_data.json"


def main() -> None:
    # Check API is running
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        resp.raise_for_status()
    except Exception:
        print(f"ERROR: Cannot connect to API at {API_BASE}")
        print("Start the API first: uvicorn ctm_app.main:app --port 8000")
        sys.exit(1)

    # Check sample docs exist
    if not (SAMPLE_DIR / "nda_template_v1.docx").exists():
        print("Sample .docx files not found. Generating them...")
        from scripts.create_sample_docx import (
            create_nda_v1,
            create_nda_v2,
            create_consulting_agreement,
            create_software_license,
        )
        SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
        create_nda_v1()
        create_nda_v2()
        create_consulting_agreement()
        create_software_license()

    with open(SEED_DATA) as f:
        data = json.load(f)

    # Create users
    users_by_email: dict[str, dict] = {}
    for u in data["users"]:
        resp = requests.post(f"{API_BASE}/users", json=u, timeout=10)
        if resp.status_code == 409:
            # User already exists, find them
            all_users = requests.get(f"{API_BASE}/users", timeout=10).json()
            existing = next((x for x in all_users if x["email"] == u["email"]), None)
            if existing:
                users_by_email[u["email"]] = existing
                print(f"  User already exists: {u['name']}")
                continue
        resp.raise_for_status()
        users_by_email[u["email"]] = resp.json()
        print(f"  Created user: {u['name']}")

    # Create templates
    for t in data["templates"]:
        owner = users_by_email[t["owner_email"]]
        file_path = SAMPLE_DIR / t["file"]

        metadata = {
            "name": t["name"],
            "template_type": t["template_type"],
            "use_case": t.get("use_case"),
            "description": t.get("description"),
            "review_interval_days": t.get("review_interval_days", 365),
        }

        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{API_BASE}/templates",
                files={"file": (file_path.name, f)},
                data={"metadata": json.dumps(metadata)},
                headers={"X-User-Id": owner["id"]},
                timeout=30,
            )
        resp.raise_for_status()
        template = resp.json()
        print(f"  Created template: {t['name']} (ID: {template['id']})")

        # Upload additional versions
        for v in t.get("versions", []):
            version_file = SAMPLE_DIR / v["file"]
            with open(version_file, "rb") as f:
                resp = requests.post(
                    f"{API_BASE}/templates/{template['id']}/versions",
                    files={"file": (version_file.name, f)},
                    data={"change_summary": v.get("change_summary", "")},
                    headers={"X-User-Id": owner["id"]},
                    timeout=30,
                )
            resp.raise_for_status()
            print(f"    Uploaded version: {v['file']}")

        # Run workflow transitions
        for wf in t.get("workflow", []):
            actor = users_by_email[wf["by_email"]]
            resp = requests.post(
                f"{API_BASE}/templates/{template['id']}/workflow/transition",
                json={"to_status": wf["to_status"], "comment": wf.get("comment")},
                headers={
                    "X-User-Id": actor["id"],
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            resp.raise_for_status()
            print(f"    Transitioned to {wf['to_status']} by {actor['name']}")

        # Force stale if specified (directly update DB)
        if "force_stale_days" in t:
            _force_stale(template["id"], t["force_stale_days"])

    print("\nSeed data loaded successfully!")


def _force_stale(template_id: str, days_ago: int) -> None:
    """Directly update the DB to make a template appear stale."""
    from sqlalchemy import create_engine, text

    db_url = os.environ.get("CTM_DATABASE_URL", "sqlite:///data/app.db")
    engine = create_engine(db_url)
    stale_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE templates SET last_reviewed_at = :date WHERE id = :id"),
            {"date": stale_date.isoformat(), "id": template_id},
        )
    print(f"    Set last_reviewed_at to {days_ago} days ago (stale for demo)")


if __name__ == "__main__":
    main()
