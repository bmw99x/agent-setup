from review_lib import Site, assert_found, assert_not_flagged, problems

FREEZES = "app/memberships/freezes.py"
MODELS = "app/memberships/models.py"
NOTIFICATIONS = "app/memberships/notifications.py"


def test_review_lists_findings_with_locations():
    assert problems(), "REVIEW.md has no bullet findings starting with path:line"


def test_client_and_generic_names_flagged_as_domain_language_drift():
    assert_found(
        [
            Site(FREEZES, "class ClientFreezeService"),
            Site(FREEZES, "def process(self, client_id"),
            Site(FREEZES, 'raise FreezeNotAllowed(f"client'),
        ],
        r"\bclients?\b.{0,120}\bmembers?\b|\bmembers?\b.{0,120}\bclients?\b|ubiquitous|"
        r"domain (language|term|name|vocabulary|concept)|two names|same (concept|thing)|"
        r"inconsistent(ly)? nam|naming|rename|vague|generic|meaningless|says nothing|"
        r"intention[- ]revealing|what (it|the method) does",
        "ClientFreezeService.process(client_id, data) for a member freezing a membership",
    )


def test_freeze_eligibility_flagged_as_feature_envy():
    assert_found(
        [Site(FREEZES, "class ClientFreezeService", "return used_days + ")],
        r"feature envy|envy|tell[ ,-]*don.?t[ ,-]*ask|demeter|"
        r"move.{0,60}(on|in)?to.{0,20}`?Membership|belongs (on|in|to).{0,20}`?Membership|"
        r"(?-i:\bMembership(\.can_|`?\s+(itself|model|class|object|dataclass|method)))|"
        r"method on .{0,10}Membership|only (uses|touches|reads) .{0,20}membership",
        "_can_freeze decides from Membership's data only",
    )


def test_freeze_period_dates_flagged_as_data_clump():
    assert_found(
        [
            Site(MODELS, "freezes: list[tuple[date, date]]"),
            Site(FREEZES, "def _can_freeze("),
            Site(FREEZES, "membership.freezes.append((starts_on, ends_on))"),
            Site(FREEZES, "def _check_period(", "raise FreezeNotAllowed(f\"a freeze lasts"),
            Site(FREEZES, "def _freeze_length_days("),
            Site(NOTIFICATIONS, "def freeze_confirmation("),
        ],
        r"data clump|primitive obsession|value object|parameter object|"
        r"travel together|(passed|go|appear|move)\w* (around )?together|always together|"
        r"(?-i:`?Freeze`?\s+(type|class|dataclass|value)|\bFreeze(Period|Window|Range|Dates)\b|\bDateRange\b|\bPeriod\b)|domain (type|object)|"
        r"tuple.{0,40}(dataclass|type|class|object)|introduce (a|an) .{0,20}(type|class|dataclass)",
        "(starts_on, ends_on) travel together as loose dates and a tuple",
    )


def test_formatter_level_line_length_not_flagged():
    assert_not_flagged(Site(NOTIFICATIONS, "FREEZE_CONFIRMATION = '"), "long single-quoted constant")


def test_why_comment_not_flagged():
    assert_not_flagged(Site(FREEZES, "# Club rules s4.2"), "comment explaining why")
