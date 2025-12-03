"""Label generation functions."""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def horizon_return(df: pd.DataFrame, horizon_bars: int = 20) -> pd.Series:
    """
    Compute forward-looking return over horizon.
    
    Args:
        df: DataFrame with 'close' column
        horizon_bars: Number of bars forward
    
    Returns:
        Series of forward returns
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must have 'close' column")
    
    future_close = df["close"].shift(-horizon_bars)
    returns = np.log(future_close / df["close"])
    
    return returns


def binary_label(
    df: pd.DataFrame,
    horizon_bars: int = 20,
    threshold_return: float = 0.001,
) -> pd.Series:
    """
    Create binary label based on threshold return.
    
    Args:
        df: DataFrame with 'close' column
        horizon_bars: Number of bars forward
        threshold_return: Return threshold (e.g., 0.001 = 0.1%)
    
    Returns:
        Series: 1 if return > threshold, 0 if return < -threshold, NaN otherwise
    """
    returns = horizon_return(df, horizon_bars)
    
    labels = pd.Series(np.nan, index=df.index)
    labels[returns > threshold_return] = 1
    labels[returns < -threshold_return] = 0
    
    return labels


def triple_barrier_label(
    df: pd.DataFrame,
    pt: float = 0.002,
    sl: float = 0.001,
    horizon_bars: int = 100,
) -> pd.Series:
    """
    Create triple barrier label (profit target, stop loss, or timeout).
    
    Args:
        df: DataFrame with 'close' column
        pt: Profit target (e.g., 0.002 = 0.2%)
        sl: Stop loss (e.g., 0.001 = 0.1%)
        horizon_bars: Maximum bars to wait
    
    Returns:
        Series: 1 if PT hit first, -1 if SL hit first, 0 if timeout
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must have 'close' column")
    
    labels = pd.Series(0, index=df.index)  # Default: timeout
    
    for i in range(len(df) - 1):
        entry_price = df["close"].iloc[i]
        pt_price = entry_price * (1 + pt)
        sl_price = entry_price * (1 - sl)
        
        # Look forward up to horizon_bars
        future_bars = df.iloc[i+1:min(i+1+horizon_bars, len(df))]
        
        if len(future_bars) == 0:
            continue
        
        # Check if PT or SL hit first
        high_reached = (future_bars["high"] >= pt_price).any()
        low_reached = (future_bars["low"] <= sl_price).any()
        
        if high_reached and low_reached:
            # Check which hit first
            pt_idx = (future_bars["high"] >= pt_price).idxmax()
            sl_idx = (future_bars["low"] <= sl_price).idxmax()
            if pt_idx < sl_idx:
                labels.iloc[i] = 1
            else:
                labels.iloc[i] = -1
        elif high_reached:
            labels.iloc[i] = 1
        elif low_reached:
            labels.iloc[i] = -1
        # else: timeout (0)
    
    return labels


def create_labels(
    df: pd.DataFrame,
    cfg_strategy: Dict[str, Any],
) -> pd.DataFrame:
    """
    Create labels based on strategy configuration.
    
    Args:
        df: DataFrame with features and 'close' column
        cfg_strategy: Strategy configuration
    
    Returns:
        DataFrame with label columns added
    """
    df = df.copy()
    
    horizon_bars = cfg_strategy.get("labels", {}).get("horizon_bars", 20)
    threshold_return = cfg_strategy.get("labels", {}).get("threshold_return", 0.001)
    
    # Binary label
    df["label"] = binary_label(df, horizon_bars, threshold_return)
    
    # Triple barrier (if enabled)
    if cfg_strategy.get("labels", {}).get("triple_barrier", {}).get("enabled", False):
        pt_sl = cfg_strategy.get("labels", {}).get("triple_barrier", {}).get("pt_sl", [0.002, 0.001])
        df["triple_barrier_label"] = triple_barrier_label(df, pt_sl[0], pt_sl[1], horizon_bars)
    
    logger.debug(f"Created labels for {df['label'].notna().sum()} samples")
    
    return df

