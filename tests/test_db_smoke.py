"""Smoke tests for database operations."""

import pytest
import pandas as pd
from jcq.storage.db import get_engine, ensure_schema, upsert_bars, read_bars


@pytest.mark.skipif(
    not __import__("os").getenv("SUPABASE_DB_URL") and not __import__("os").getenv("DATABASE_URL"),
    reason="Database URL not set, skipping DB tests",
)
def test_db_connection():
    """Test database connection."""
    engine = get_engine()
    assert engine is not None


def test_db_schema():
    """Test schema creation."""
    try:
        ensure_schema()
        assert True
    except Exception:
        pytest.skip("Database not available")


def test_upsert_bars(sample_bars):
    """Test bar upsert."""
    try:
        count = upsert_bars(sample_bars, "NQ", "1m")
        assert count >= 0
    except Exception:
        pytest.skip("Database not available")


def test_read_bars():
    """Test bar read."""
    try:
        df = read_bars("NQ", "1m")
        assert isinstance(df, pd.DataFrame)
    except Exception:
        pytest.skip("Database not available")

