from accounts.sessions import is_expired, start_session


def test_new_session_is_not_expired():
    assert not is_expired(start_session("u-1"))
