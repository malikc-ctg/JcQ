"""Time and session utilities for market data."""

from datetime import datetime, time as dt_time, timedelta
from typing import Optional
import pytz
import pandas as pd
from jcq.core.config import get_config


def to_utc(ts: pd.Timestamp | datetime, tz: str | pytz.BaseTzInfo) -> pd.Timestamp:
    """
    Convert a timestamp to UTC.
    
    Args:
        ts: Timestamp to convert
        tz: Timezone name (e.g., "America/New_York") or pytz timezone object
    
    Returns:
        Timestamp in UTC
    """
    if isinstance(ts, pd.Timestamp):
        if ts.tz is None:
            # Assume naive timestamp is in the given timezone
            if isinstance(tz, str):
                tz = pytz.timezone(tz)
            return pd.Timestamp(ts).tz_localize(tz).tz_convert("UTC")
        else:
            return ts.tz_convert("UTC")
    else:
        # datetime
        if isinstance(tz, str):
            tz = pytz.timezone(tz)
        if ts.tzinfo is None:
            ts = tz.localize(ts)
        return pd.Timestamp(ts.astimezone(pytz.UTC))


def session_day(ts: pd.Timestamp | datetime, tz: str = "America/New_York") -> pd.Timestamp:
    """
    Map a timestamp to its Globex session date.
    
    Globex runs from 18:00 previous day to 17:00 current day ET.
    So a bar at 19:00 ET on Jan 1 belongs to the Jan 2 session.
    
    Args:
        ts: Timestamp (assumed UTC if timezone-aware)
        tz: Timezone for session logic (default: America/New_York)
    
    Returns:
        Date of the session (as Timestamp at midnight UTC)
    """
    cfg = get_config()
    market_tz = cfg.get("market", {}).get("sessions", {}).get("timezone", tz)
    
    if isinstance(ts, datetime):
        ts = pd.Timestamp(ts)
    
    # Convert to market timezone
    if ts.tz is None:
        market_tz_obj = pytz.timezone(market_tz)
        ts_market = market_tz_obj.localize(ts.to_pydatetime())
    else:
        ts_market = ts.tz_convert(market_tz)
    
    # Get the hour in market time
    hour = ts_market.hour
    
    # If hour >= 18:00 (6 PM), this bar belongs to the next day's session
    if hour >= 18:
        session_date = (ts_market + timedelta(days=1)).date()
    else:
        session_date = ts_market.date()
    
    # Return as UTC midnight
    return pd.Timestamp(session_date).tz_localize("UTC")


def is_rth(ts: pd.Timestamp | datetime, tz: str = "America/New_York") -> bool:
    """
    Check if timestamp is within Regular Trading Hours (RTH).
    
    RTH: 09:30 to 16:00 ET.
    
    Args:
        ts: Timestamp (assumed UTC if timezone-aware)
        tz: Timezone for session logic (default: America/New_York)
    
    Returns:
        True if within RTH
    """
    cfg = get_config()
    market_tz = cfg.get("market", {}).get("sessions", {}).get("timezone", tz)
    rth_start = cfg.get("market", {}).get("sessions", {}).get("rth", {}).get("start", "09:30")
    rth_end = cfg.get("market", {}).get("sessions", {}).get("rth", {}).get("end", "16:00")
    
    if isinstance(ts, datetime):
        ts = pd.Timestamp(ts)
    
    # Convert to market timezone
    if ts.tz is None:
        market_tz_obj = pytz.timezone(market_tz)
        ts_market = market_tz_obj.localize(ts.to_pydatetime())
    else:
        ts_market = ts.tz_convert(market_tz)
    
    time_market = ts_market.time()
    start_time = dt_time.fromisoformat(rth_start)
    end_time = dt_time.fromisoformat(rth_end)
    
    return start_time <= time_market <= end_time


def minutes_since_rth_open(ts: pd.Timestamp | datetime, tz: str = "America/New_York") -> Optional[float]:
    """
    Calculate minutes since RTH open for a given timestamp.
    
    Args:
        ts: Timestamp (assumed UTC if timezone-aware)
        tz: Timezone for session logic (default: America/New_York)
    
    Returns:
        Minutes since RTH open, or None if before RTH open
    """
    cfg = get_config()
    market_tz = cfg.get("market", {}).get("sessions", {}).get("timezone", tz)
    rth_start = cfg.get("market", {}).get("sessions", {}).get("rth", {}).get("start", "09:30")
    
    if isinstance(ts, datetime):
        ts = pd.Timestamp(ts)
    
    # Convert to market timezone
    if ts.tz is None:
        market_tz_obj = pytz.timezone(market_tz)
        ts_market = market_tz_obj.localize(ts.to_pydatetime())
    else:
        ts_market = ts.tz_convert(market_tz)
    
    # Get RTH open time for this date
    rth_start_time = dt_time.fromisoformat(rth_start)
    rth_open = market_tz_obj.localize(
        datetime.combine(ts_market.date(), rth_start_time)
    )
    
    if ts_market < rth_open:
        return None
    
    delta = ts_market - rth_open
    return delta.total_seconds() / 60.0


def label_session(ts: pd.Timestamp | datetime, tz: str = "America/New_York") -> str:
    """
    Label a timestamp with session code: Asia, Europe, or US.
    
    Simple heuristic based on hour in market timezone.
    
    Args:
        ts: Timestamp (assumed UTC if timezone-aware)
        tz: Timezone for session logic (default: America/New_York)
    
    Returns:
        Session code: "Asia", "Europe", or "US"
    """
    if isinstance(ts, datetime):
        ts = pd.Timestamp(ts)
    
    # Convert to market timezone
    if ts.tz is None:
        market_tz_obj = pytz.timezone(tz)
        ts_market = market_tz_obj.localize(ts.to_pydatetime())
    else:
        ts_market = ts.tz_convert(tz)
    
    hour = ts_market.hour
    
    # Rough heuristic (can be improved)
    if 0 <= hour < 8:
        return "Asia"
    elif 8 <= hour < 16:
        return "Europe"
    else:
        return "US"

