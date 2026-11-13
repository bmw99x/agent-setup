_REPORTS = {
    "r-1": {"id": "r-1", "title": "Quarterly revenue", "rows": [["Q1", 120], ["Q2", 135]]},
    "r-2": {"id": "r-2", "title": "Churn", "rows": [["Jan", 4], ["Feb", 3]]},
}


def get_report(report_id: str) -> dict | None:
    return _REPORTS.get(report_id)
