from review_lib import Site, assert_found, assert_not_flagged, problems

LABELS = "app/shipping/labels.py"
NOTIFICATIONS = "app/shipping/notifications.py"
MANIFEST = "app/shipping/manifest.py"
RETURNS = "app/shipping/returns.py"


def test_review_lists_findings_with_locations():
    assert problems(), "REVIEW.md has no bullet findings starting with path:line"


def test_boolean_switched_shared_label_flagged_as_wrong_abstraction():
    assert_found(
        [
            Site(LABELS, "def render_label(", "footer = "),
            Site(RETURNS, "label=render_label(shipment, is_return=True)"),
        ],
        r"wrong abstraction|boolean|\bflag|is_return|inline|diverg|two (different )?(things|functions|labels|jobs|concerns)|"
        r"separate (function|render|label)|split|conditional|branch(es|ing)|polymorph|strategy",
        "render_label(is_return=...) switches between two callers",
    )


def test_third_copy_of_address_block_flagged_as_duplication():
    assert_found(
        [
            Site(NOTIFICATIONS, "warehouse = shipment.sender", "address_lines.append(warehouse.country"),
            Site(LABELS, "address_lines = [addressee.name.upper()", "address_lines.append(addressee.country"),
            Site(MANIFEST, "address_lines = [recipient.name.upper()", "address_lines.append(recipient.country"),
        ],
        r"(?=.*address)"
        r"(?=.*(duplicat|copy|copied|copies|same (block|code|logic|formatting|lines)|repeat|once and only once|"
        r"\bDRY\b|third|three|extract|shared (helper|function)|reuse))",
        "address formatting now exists three times",
    )


def test_second_copy_of_weight_total_not_flagged():
    assert_not_flagged(Site(RETURNS, "weight_kg = round(sum("), "weight total (second occurrence only)")


def test_untouched_routing_code_not_flagged():
    assert_not_flagged(
        Site(LABELS, "def _carrier_routing_code(", "return code"),
        "_carrier_routing_code (unchanged on this branch)",
    )
