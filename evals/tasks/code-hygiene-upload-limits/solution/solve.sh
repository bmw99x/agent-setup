#!/bin/bash
set -e
cat > /app/app/documents/service.py <<'PY'
from app.documents.errors import UploadRejected
from app.documents.models import Document
from app.documents.preview import PREVIEWABLE_CONTENT_TYPES

MAX_UPLOAD_MB = 25

_STORE: dict = {}


def upload_document(filename: str, content_type: str, data: bytes) -> Document:
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise UploadRejected(f"Files must be {MAX_UPLOAD_MB} MB or smaller.")
    if content_type not in PREVIEWABLE_CONTENT_TYPES:
        raise UploadRejected("Only PDF, PNG and JPEG files can be uploaded.")
    document = Document(filename=filename, content_type=content_type, size_bytes=len(data))
    _STORE[document.id] = (document, data)
    return document
PY
