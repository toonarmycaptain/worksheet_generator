"""Shared test setup."""

import reportlab.rl_config

# Fixed PDF timestamp and document id, so the same seed gives the same bytes.
# The golden tests (CLI and web) depend on it.
reportlab.rl_config.invariant = 1
