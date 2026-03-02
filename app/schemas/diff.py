from pydantic import BaseModel


class DiffLine(BaseModel):
    line_number_left: int | None
    line_number_right: int | None
    content_left: str
    content_right: str
    change_type: str


class DiffResponse(BaseModel):
    template_id: str
    from_version: int
    to_version: int
    from_text: str
    to_text: str
    unified_diff: str
    side_by_side: list[DiffLine]
