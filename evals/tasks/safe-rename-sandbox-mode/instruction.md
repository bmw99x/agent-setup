# Rename test mode to sandbox mode

Product has renamed the gateway's "test mode" to "sandbox mode" (support kept confusing it with our own test suite). Rename `test_mode` to `sandbox_mode` across the repo in `/app` — code, tests and docs — so nothing still refers to the old name.

Keep behaviour the same. I'll review the diff before committing, so don't commit.
