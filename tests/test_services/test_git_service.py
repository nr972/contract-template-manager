import uuid

import pytest

from ctm_app.services.git_service import GitService


def test_store_and_retrieve(git_repo: GitService):
    template_id = str(uuid.uuid4())
    content = b"test docx content"
    sha = git_repo.store_file(template_id, content, "test commit", "Test Author")
    assert len(sha) == 40

    retrieved = git_repo.retrieve_file(template_id, sha)
    assert retrieved == content


def test_multiple_versions(git_repo: GitService):
    template_id = str(uuid.uuid4())
    sha1 = git_repo.store_file(template_id, b"v1", "version 1", "Author")
    sha2 = git_repo.store_file(template_id, b"v2", "version 2", "Author")
    assert sha1 != sha2

    assert git_repo.retrieve_file(template_id, sha1) == b"v1"
    assert git_repo.retrieve_file(template_id, sha2) == b"v2"


def test_invalid_template_id(git_repo: GitService):
    with pytest.raises(ValueError, match="Invalid template ID"):
        git_repo.store_file("../evil/path", b"bad", "hack", "Hacker")


def test_retrieve_nonexistent(git_repo: GitService):
    template_id = str(uuid.uuid4())
    with pytest.raises(FileNotFoundError):
        git_repo.retrieve_file(template_id, "0" * 40)


def test_file_history(git_repo: GitService):
    template_id = str(uuid.uuid4())
    git_repo.store_file(template_id, b"v1", "first", "Author")
    git_repo.store_file(template_id, b"v2", "second", "Author")
    history = git_repo.get_file_history(template_id)
    assert len(history) == 2
    assert "second" in history[0]["message"]
