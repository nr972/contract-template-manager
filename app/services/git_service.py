import re
from pathlib import Path

import git
from filelock import FileLock

from app.config import settings

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


class GitService:
    def __init__(self, repo_path: Path | None = None) -> None:
        self.repo_path = repo_path or settings.templates_repo
        self._lock = FileLock(str(self.repo_path / ".git.lock"))
        self.repo = self._ensure_repo()

    def _ensure_repo(self) -> git.Repo:
        if not (self.repo_path / ".git").exists():
            self.repo_path.mkdir(parents=True, exist_ok=True)
            repo = git.Repo.init(self.repo_path)
            gitkeep = self.repo_path / ".gitkeep"
            gitkeep.touch()
            repo.index.add([".gitkeep"])
            repo.index.commit("Initialize template repository")
            return repo
        return git.Repo(self.repo_path)

    def _validate_template_id(self, template_id: str) -> None:
        if not UUID_PATTERN.match(template_id):
            raise ValueError(f"Invalid template ID format: {template_id}")

    def store_file(
        self,
        template_id: str,
        content: bytes,
        commit_message: str,
        author_name: str,
    ) -> str:
        self._validate_template_id(template_id)
        with self._lock:
            template_dir = self.repo_path / template_id
            template_dir.mkdir(parents=True, exist_ok=True)
            file_path = template_dir / "template.docx"
            file_path.write_bytes(content)
            self.repo.index.add([f"{template_id}/template.docx"])
            actor = git.Actor(author_name, "")
            commit = self.repo.index.commit(commit_message, author=actor)
            return str(commit.hexsha)

    def retrieve_file(self, template_id: str, commit_sha: str) -> bytes:
        self._validate_template_id(template_id)
        try:
            commit = self.repo.commit(commit_sha)
            blob = commit.tree / template_id / "template.docx"
            return blob.data_stream.read()
        except (git.exc.BadName, KeyError, ValueError) as e:
            raise FileNotFoundError(
                f"File not found for template {template_id} at commit {commit_sha}"
            ) from e

    def get_file_history(self, template_id: str) -> list[dict]:
        self._validate_template_id(template_id)
        file_path = f"{template_id}/template.docx"
        commits = list(self.repo.iter_commits(paths=file_path))
        return [
            {
                "sha": str(c.hexsha),
                "message": c.message,
                "author": str(c.author),
                "date": c.committed_datetime.isoformat(),
            }
            for c in commits
        ]
