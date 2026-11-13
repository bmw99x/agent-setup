import sys

sys.path.insert(0, "/app")
from helpdesk.comments import render_comment  # noqa: E402


def test_plain_text_is_a_paragraph():
    assert render_comment("thanks, fixed") == "<p>thanks, fixed</p>"
