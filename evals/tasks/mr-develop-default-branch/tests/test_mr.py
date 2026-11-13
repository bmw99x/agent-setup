import pytest

import mr_checks as c

BRANCH = "fix/session-expiry-clock-skew"


@pytest.fixture(scope="module")
def mr():
    return c.merge_request(BRANCH)


def test_branch_pushed_before_mr_created(mr):
    c.assert_pushed_before_create(mr)


def test_targets_repo_default_branch_not_main(mr):
    assert mr["target_branch"] == "develop", mr["target_branch"]


def test_title_is_conventional(mr):
    assert c.CONVENTIONAL_TITLE.match(mr["title"]), mr["title"]


def test_context_section_comes_first(mr):
    c.assert_context_first(mr["body"])


def test_body_has_template_sections(mr):
    c.assert_template_sections(mr["body"])


def test_no_dangling_headings(mr):
    c.assert_no_dangling_headings(mr["body"])


def test_ticket_from_commit_trailer_linked(mr):
    c.assert_tickets_section_links(mr["body"], ["ACC-61"])


def test_unrelated_tickets_not_attached(mr):
    c.assert_tickets_not_attached(mr["body"], ["ACC-50", "ACC-58"])


def test_ticket_links_back_to_pr(mr):
    c.assert_tickets_reference_mr(mr, ["ACC-61"])


def test_ticket_moved_to_code_review_not_later_review(mr):
    c.assert_tickets_in_code_review(["ACC-61"])


def test_checked_test_plan_boxes_backed_by_a_run(mr):
    c.assert_checked_boxes_backed_by_a_test_run(mr["body"])


def test_no_ai_attribution(mr):
    c.assert_no_ai_attribution(mr, "origin/develop")
