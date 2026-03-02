from io import BytesIO

from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import FileValidationError


def validate_docx_upload(file: UploadFile, content: bytes) -> None:
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise FileValidationError("File must have a .docx extension")

    if len(content) > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes // (1024 * 1024)
        raise FileValidationError(f"File exceeds maximum size of {max_mb} MB")

    if len(content) < 4:
        raise FileValidationError("File is too small to be a valid .docx document")

    # .docx files are ZIP archives — check ZIP magic bytes (PK\x03\x04)
    if content[:4] != b"PK\x03\x04":
        raise FileValidationError("File content is not a valid .docx document")

    # Verify parseable with python-docx
    try:
        from docx import Document

        Document(BytesIO(content))
    except Exception:
        raise FileValidationError("File is not a valid Word document")
