"""Shared pytest fixtures. Uses the live Postgres from the compose/container setup."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault(
    "CCPIP_DATABASE_URL", "postgresql+psycopg2://ccpip:ccpip@localhost:5432/ccpip"
)
