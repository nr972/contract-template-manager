from io import BytesIO
from unittest.mock import MagicMock

import pytest
from docx import Document

from ctm_app.core.exceptions import FileValidationError
from ctm_app.services.file_validator import validate_docx_upload


def _make_upload(filename: str, content: bytes) -> MagicMock:
    mock = MagicMock()
    mock.filename = filename
    return mock


def _make_docx() -> bytes:
    doc = Document()
    doc.add_paragraph("test")
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_valid_docx():
    content = _make_docx()
    upload = _make_upload("test.docx", content)
    validate_docx_upload(upload, content)  # Should not raise


def test_wrong_extension():
    content = _make_docx()
    upload = _make_upload("test.pdf", content)
    with pytest.raises(FileValidationError, match="extension"):
        validate_docx_upload(upload, content)


def test_too_small():
    upload = _make_upload("test.docx", b"ab")
    with pytest.raises(FileValidationError, match="too small"):
        validate_docx_upload(upload, b"ab")


def test_not_zip():
    content = b"this is not a zip file at all and it is long enough"
    upload = _make_upload("test.docx", content)
    with pytest.raises(FileValidationError, match="not a valid"):
        validate_docx_upload(upload, content)


def test_zip_but_not_docx():
    # Create a valid ZIP that isn't a docx
    import zipfile
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.txt", "hello")
    content = buf.getvalue()
    upload = _make_upload("test.docx", content)
    with pytest.raises(FileValidationError, match="not a valid Word"):
        validate_docx_upload(upload, content)
