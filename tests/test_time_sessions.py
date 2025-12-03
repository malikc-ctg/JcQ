"""Tests for time and session utilities."""

import pytest
import pandas as pd
from jcq.core.time import to_utc, session_day, is_rth, minutes_since_rth_open


def test_to_utc():
    """Test UTC conversion."""
    ts = pd.Timestamp("2024-01-01 09:30", tz="America/New_York")
    utc = to_utc(ts, "America/New_York")
    assert utc.tz.zone == "UTC"


def test_session_day():
    """Test session day mapping."""
    # Bar at 19:00 ET on Jan 1 belongs to Jan 2 session
    ts = pd.Timestamp("2024-01-01 19:00", tz="America/New_York")
    session = session_day(ts)
    assert session.date() == pd.Timestamp("2024-01-02").date()


def test_is_rth():
    """Test RTH detection."""
    # 10:00 ET is RTH
    ts = pd.Timestamp("2024-01-01 10:00", tz="America/New_York")
    assert is_rth(ts) is True
    
    # 20:00 ET is not RTH
    ts = pd.Timestamp("2024-01-01 20:00", tz="America/New_York")
    assert is_rth(ts) is False


def test_minutes_since_rth_open():
    """Test minutes since RTH open."""
    ts = pd.Timestamp("2024-01-01 10:00", tz="America/New_York")
    minutes = minutes_since_rth_open(ts)
    assert minutes == 30  # 30 minutes after 09:30

