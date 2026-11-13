class TransientError(Exception):
    """A failure worth retrying: timeouts, connection resets, 503s."""
