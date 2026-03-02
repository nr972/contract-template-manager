from datetime import datetime

from pydantic import BaseModel


class VersionResponse(BaseModel):
    id: str
    template_id: str
    version_number: int
    filename: str
    change_summary: str | None
    uploaded_by_id: str
    uploaded_by_name: str | None = None
    file_size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}
