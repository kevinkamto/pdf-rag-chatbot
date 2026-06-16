"""Test configuration: provide required settings before app modules import."""

from __future__ import annotations

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("MANAGEMENT_SECRET", "test-secret")
os.environ.setdefault("USE_DEMO_CORPUS", "false")
