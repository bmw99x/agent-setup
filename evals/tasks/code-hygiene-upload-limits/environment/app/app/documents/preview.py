from app.documents.models import Document

PREVIEWABLE_CONTENT_TYPES = ("application/pdf", "image/png", "image/jpeg")


def can_preview(document: Document) -> bool:
    return document.content_type in PREVIEWABLE_CONTENT_TYPES


def preview_url(document: Document) -> str | None:
    if not can_preview(document):
        return None
    return f"/documents/{document.id}/preview"
