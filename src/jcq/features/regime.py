"""Regime detection (volatility and trend)."""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def compute_regime(df_features: pd.DataFrame, cfg_strategy: Dict[str, Any]) -> pd.Series:
    """
    Compute regime labels (volatility and trend).
    
    Args:
        df_features: DataFrame with features (must have atr_14, ema_20, ema_50)
        cfg_strategy: Strategy configuration
    
    Returns:
        Series with regime labels: "low_vol", "normal_vol", "high_vol", "trend_up", "trend_down", "choppy"
    """
    if df_features.empty or "atr_14" not in df_features.columns:
        return pd.Series(dtype=str, index=df_features.index)
    
    regimes = []
    
    # Volatility regime
    atr = df_features["atr_14"]
    atr_percentiles = atr.rolling(100, min_periods=10).quantile([0.33, 0.67])
    
    vol_regime = pd.Series("normal_vol", index=df_features.index)
    if isinstance(atr_percentiles, pd.DataFrame):
        vol_regime[atr < atr_percentiles[0.33]] = "low_vol"
        vol_regime[atr > atr_percentiles[0.67]] = "high_vol"
    else:
        # Fallback
        atr_median = atr.rolling(100, min_periods=10).median()
        vol_regime[atr < atr_median * 0.7] = "low_vol"
        vol_regime[atr > atr_median * 1.3] = "high_vol"
    
    # Trend regime
    trend_regime = pd.Series("choppy", index=df_features.index)
    
    if "ema_20" in df_features.columns and "ema_50" in df_features.columns:
        ema20 = df_features["ema_20"]
        ema50 = df_features["ema_50"]
        
        # Trend strength: alignment and slope
        ema_aligned = (ema20 > ema50) & (ema20.shift(1) > ema50.shift(1))
        ema_slope = ema20.diff()
        
        # Strong uptrend
        trend_regime[ema_aligned & (ema_slope > 0)] = "trend_up"
        
        # Strong downtrend
        trend_regime[~ema_aligned & (ema_slope < 0)] = "trend_down"
    
    # Combine
    combined = vol_regime + "_" + trend_regime
    
    logger.debug(f"Computed regimes: {combined.value_counts().to_dict()}")
    
    return combined

