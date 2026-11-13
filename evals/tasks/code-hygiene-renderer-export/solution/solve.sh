#!/bin/bash
set -e
python3 - <<'PY'
from pathlib import Path
p = Path("/app/app/config.py")
p.write_text(p.read_text().replace(
    '    billing_api_url: str = "http://billing.internal:8000"\n',
    '    billing_api_url: str = "http://billing.internal:8000"\n'
    '    renderer_url: str = "http://renderer.internal:8080"\n'
    '    renderer_timeout_seconds: float = 60\n',
))
PY
cat > /app/app/reports/renderer.py <<'PY'
from app.clients.http import post_json
from app.config import get_settings


def render_pdf(report: dict) -> bytes:
    settings = get_settings()
    return post_json(
        f"{settings.renderer_url}/render",
        {"title": report["title"], "rows": report["rows"]},
        timeout=settings.renderer_timeout_seconds,
    )
PY
cat > /app/app/reports/routes.py <<'PY'
from fastapi import APIRouter, HTTPException, Response

from app.clients.http import UpstreamError
from app.reports.renderer import render_pdf
from app.reports.repository import get_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}")
def read_report(report_id: str) -> dict:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.post("/{report_id}/export")
def export_report(report_id: str) -> Response:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    try:
        pdf = render_pdf(report)
    except UpstreamError:
        raise HTTPException(
            status_code=503,
            detail="PDF export is temporarily unavailable. Please try again in a few minutes.",
        ) from None
    return Response(content=pdf, media_type="application/pdf")
PY
