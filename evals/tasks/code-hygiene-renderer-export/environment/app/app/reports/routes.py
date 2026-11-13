from fastapi import APIRouter, HTTPException

from app.reports.repository import get_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}")
def read_report(report_id: str) -> dict:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report
