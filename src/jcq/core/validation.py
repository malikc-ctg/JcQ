"""Data validation utilities."""

import pandas as pd
from typing import List, Optional
from jcq.core.errors import DataError


def validate_bars_df(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> None:
    """
    Validate a bars DataFrame has required columns and valid data.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required columns (default: ohlcv + timestamp)
    
    Raises:
        DataError: If validation fails
    """
    if required_columns is None:
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
    
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise DataError(f"Missing required columns: {missing}")
    
    if df.empty:
        raise DataError("DataFrame is empty")
    
    # Check for required OHLCV columns
    ohlcv = ["open", "high", "low", "close", "volume"]
    if all(col in df.columns for col in ohlcv):
        # Validate OHLC relationships
        invalid_high = df["high"] < df[["open", "close"]].max(axis=1)
        if invalid_high.any():
            raise DataError(f"Found {invalid_high.sum()} bars where high < max(open, close)")
        
        invalid_low = df["low"] > df[["open", "close"]].min(axis=1)
        if invalid_low.any():
            raise DataError(f"Found {invalid_low.sum()} bars where low > min(open, close)")
        
        if (df["volume"] < 0).any():
            raise DataError("Found negative volume values")
    
    # Check for duplicates if timestamp exists
    if "timestamp" in df.columns:
        duplicates = df["timestamp"].duplicated()
        if duplicates.any():
            raise DataError(f"Found {duplicates.sum()} duplicate timestamps")


def ensure_monotonic_timestamps(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """
    Ensure timestamps are monotonic and sorted.
    
    Args:
        df: DataFrame with timestamp column
        timestamp_col: Name of timestamp column
    
    Returns:
        DataFrame sorted by timestamp with duplicates removed
    """
    if timestamp_col not in df.columns:
        raise DataError(f"Column '{timestamp_col}' not found")
    
    df = df.sort_values(timestamp_col).drop_duplicates(subset=[timestamp_col], keep="last")
    return df.reset_index(drop=True)

