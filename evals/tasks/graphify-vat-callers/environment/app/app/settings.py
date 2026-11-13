"""Deployment settings."""

DEFAULT_COUNTRY = "GB"

# Modules whose @command functions the CLI exposes.
JOB_MODULES = (
    "app.jobs.reissue",
    "app.jobs.purge_drafts",
)
