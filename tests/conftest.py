from collections.abc import Generator
from io import BytesIO
from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    TestSession = sessionmaker(bind=test_engine, expire_on_commit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def git_repo(tmp_path: Path):
    from app.services.git_service import GitService

    repo_path = tmp_path / "templates_repo"
    return GitService(repo_path=repo_path)


@pytest.fixture(scope="function")
def client(test_engine, db_session: Session, tmp_path: Path) -> Generator[TestClient, None, None]:
    from app.api.deps import get_db
    from app.api.templates import _get_git_service
    from app.api.versions import _get_git_service as _get_git_service_v
    from app.api.diff import _get_git_service as _get_git_service_d
    from app.services.git_service import GitService
    from app.main import app

    repo_path = tmp_path / "templates_repo"

    def _override_db() -> Generator[Session, None, None]:
        yield db_session

    def _override_git() -> GitService:
        return GitService(repo_path=repo_path)

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[_get_git_service] = _override_git
    app.dependency_overrides[_get_git_service_v] = _override_git
    app.dependency_overrides[_get_git_service_d] = _override_git

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    user = User(name="Test User", email="test@example.com", role="drafter")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def reviewer_user(db_session: Session) -> User:
    user = User(name="Reviewer", email="reviewer@example.com", role="reviewer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def approver_user(db_session: Session) -> User:
    user = User(name="Approver", email="approver@example.com", role="approver")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def make_docx(text: str = "Sample contract content") -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
