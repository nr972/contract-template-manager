from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Contract Template Manager"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///data/app.db"

    # Git template repository
    templates_repo_path: str = "data/templates_repo"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000/api"

    # File upload limits
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB

    # Stale detection
    default_review_interval_days: int = 365

    model_config = {"env_file": ".env", "env_prefix": "CTM_"}

    @property
    def templates_repo(self) -> Path:
        return Path(self.templates_repo_path)


settings = Settings()
