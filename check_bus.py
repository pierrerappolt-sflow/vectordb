#!/usr/bin/env python
"""Quick script to check which message bus is configured."""

import sys

sys.path.insert(0, "packages/core/src")

from vdb_core.infrastructure.config import load_config_or_default

config = load_config_or_default()
