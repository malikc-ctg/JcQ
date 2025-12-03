"""Feature engineering functions."""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from jcq.core.config import get_config
from jcq.features.sessions import is_rth, minutes_since_rth_open, label_session, session_day

logger = logging.getLogger(__name__)


def build_features(df_bars: pd.DataFrame, cfg_market: Dict[str, Any]) -> pd.DataFrame:
    """
    Build institutional-grade features from bars.
    
    Args:
        df_bars: DataFrame with columns: timestamp, open, high, low, close, volume
        cfg_market: Market configuration dict
    
    Returns:
        DataFrame with timestamp index and feature columns
    """
    if df_bars.empty:
        return pd.DataFrame()
    
    df = df_bars.copy()
    
    # Ensure timestamp is index
    if "timestamp" in df.columns:
        df = df.set_index("timestamp")
    
    # Ensure timezone-aware
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    
    df = df.sort_index()
    
    # Price/volatility features
    df["log_ret_1"] = np.log(df["close"] / df["close"].shift(1))
    df["log_ret_5"] = np.log(df["close"] / df["close"].shift(5))
    df["log_ret_10"] = np.log(df["close"] / df["close"].shift(10))
    
    # Realized volatility
    df["rv_10"] = df["log_ret_1"].rolling(10).std() * np.sqrt(252 * 24 * 60)  # Annualized
    df["rv_30"] = df["log_ret_1"].rolling(30).std() * np.sqrt(252 * 24 * 60)
    
    # ATR
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift(1))
    low_close = np.abs(df["low"] - df["close"].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    
    # Range and body
    df["range"] = df["high"] - df["low"]
    df["body"] = np.abs(df["close"] - df["open"])
    df["wick_up"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["wick_down"] = df[["open", "close"]].min(axis=1) - df["low"]
    
    # VWAP (session-based)
    df["session_date"] = df.index.map(lambda ts: session_day(ts))
    df["session_vwap"] = (
        df.groupby("session_date")
        .apply(lambda g: (g["close"] * g["volume"]).cumsum() / g["volume"].cumsum())
        .reset_index(level=0, drop=True)
    )
    
    # VWAP distance
    df["vwap_dist_points"] = df["close"] - df["session_vwap"]
    df["vwap_dist_atr"] = df["vwap_dist_points"] / df["atr_14"].replace(0, np.nan)
    df["vwap_dist_z50"] = df["vwap_dist_points"] / (df["close"].rolling(50).std().replace(0, np.nan))
    
    # Opening range
    opening_range_minutes = cfg_market.get("opening_range", {}).get("minutes", 30)
    df["is_rth"] = df.index.map(is_rth)
    df["minutes_since_rth"] = df.index.map(minutes_since_rth_open)
    
    def get_opening_range(group):
        rth_bars = group[group["is_rth"] & (group["minutes_since_rth"] <= opening_range_minutes)]
        if len(rth_bars) > 0:
            return pd.Series({
                "opening_range_high": rth_bars["high"].max(),
                "opening_range_low": rth_bars["low"].min(),
            }, index=group.index)
        else:
            return pd.Series({
                "opening_range_high": np.nan,
                "opening_range_low": np.nan,
            }, index=group.index)
    
    opening_ranges = df.groupby("session_date").apply(get_opening_range)
    if isinstance(opening_ranges, pd.DataFrame):
        df["opening_range_high"] = opening_ranges["opening_range_high"]
        df["opening_range_low"] = opening_ranges["opening_range_low"]
    else:
        df["opening_range_high"] = np.nan
        df["opening_range_low"] = np.nan
    
    df["dist_orh"] = df["close"] - df["opening_range_high"]
    df["dist_orl"] = df["close"] - df["opening_range_low"]
    
    # Prior session levels
    prior_session = df.groupby("session_date").agg({
        "high": "max",
        "low": "min",
        "close": "last",
    }).shift(1)
    
    df["prior_high"] = df["session_date"].map(prior_session["high"])
    df["prior_low"] = df["session_date"].map(prior_session["low"])
    df["prior_close"] = df["session_date"].map(prior_session["close"])
    
    df["dist_prior_high"] = df["close"] - df["prior_high"]
    df["dist_prior_low"] = df["close"] - df["prior_low"]
    df["dist_prior_close"] = df["close"] - df["prior_close"]
    
    # Trend features
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema20_slope"] = df["ema_20"].diff()
    df["ema50_slope"] = df["ema_50"].diff()
    
    # Time features
    df["day_of_week"] = df.index.dayofweek
    df["session_code"] = df.index.map(label_session)
    
    # Drop helper columns
    df = df.drop(columns=["session_date", "is_rth", "minutes_since_rth"], errors="ignore")
    
    # Drop NaNs (from rolling windows and shifts)
    df = df.dropna()
    
    logger.debug(f"Built {len(df.columns)} features for {len(df)} bars")
    
    return df

