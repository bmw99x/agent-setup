from app.documents.models import Document

_STORE: dict = {}


def upload_document(filename: str, content_type: str, data: bytes) -> Document:
    document = Document(filename=filename, content_type=content_type, size_bytes=len(data))
    _STORE[document.id] = (document, data)
    return document
