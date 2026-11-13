from review_lib import Site, assert_found, assert_not_flagged, problems

EXPORT = "app/reports/export.py"
OCCUPANCY = "app/reports/occupancy.py"
CANCELLATION = "app/rooms/cancellation.py"
SCRIPT = "scripts/send_january_occupancy_to_finance.py"
MAX_FINDINGS = 7


def test_review_lists_findings_with_locations():
    assert problems(), "REVIEW.md has no bullet findings starting with path:line"


def test_unrequested_export_formats_flagged_as_yagni():
    assert_found(
        [
            Site(EXPORT, "class ExportFormat", "PDF = "),
            Site(EXPORT, "class Exporter(ABC)", "def export(self, rows: list[Any]) -> bytes: ..."),
            Site(EXPORT, "class XlsxExporter", 'raise NotImplementedError("PDF'),
            Site(EXPORT, "EXPORTERS: dict", "return exporter.export"),
        ],
        r"yagni|you aren.?t gonna|speculative|premature|not (yet )?(needed|required|asked)|nobody|no one|"
        r"only (one|csv)|single (format|implementation)|unused|future|over-?engineer|"
        r"NotImplementedError|stub|placeholder|planned",
        "XLSX/PDF formats, exporter hierarchy and options for a CSV-only ticket",
    )


def test_cancellation_notice_change_flagged_as_scope_creep():
    assert_found(
        [Site(CANCELLATION, "FREE_CANCELLATION_NOTICE = ")],
        r"scope|unrelated|not related|nothing to do|separate (MR|PR|merge request|pull request|change|commit|ticket|branch)|"
        r"not (part of|in) (the |this )?(ticket|task|change|ROOMS-142)|doesn.?t (relate|belong|trace)|"
        r"own (MR|PR|ticket|change)|ROOMS-142|sneak|smuggl|hidden|unannounced|unmentioned",
        "free-cancellation notice changed 24h -> 48h on an export branch",
    )


def test_report_builder_flagged_as_long_method():
    assert_found(
        [Site(OCCUPANCY, "def build_occupancy_report(", "return rows")],
        r"long|composed method|extract|abstraction|responsibilit|does (too much|several|many|multiple|three|four)|"
        r"(fetch|load|query).{0,60}(aggregat|total|transform|shape|format|rows)|"
        r"section|comment.{0,40}(method|function)|split|smaller (functions|methods)|decompos",
        "build_occupancy_report: window, fetch, aggregate and shape in one function",
    )


def test_one_off_script_not_flagged_for_being_scrappy():
    # The script may still be flagged for real defects (committed despite "run once, then delete",
    # no entry point); only complaints that it should be tidier/more general count against the review.
    assert_not_flagged(
        Site(SCRIPT, "def main(", 'print("wrote"'),
        "one-off finance script",
        concern=r"extract|refactor|duplicat|abstraction|rename|clean ?up|structure|parametri[sz]|argparse|"
        r"generali[sz]|reusab|too long|nested",
    )
