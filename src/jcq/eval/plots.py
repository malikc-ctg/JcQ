"""Plotting utilities for reports."""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_equity_curve(df_trades: pd.DataFrame) -> pd.DataFrame:
    """Create equity curve from trades."""
    if df_trades.empty or "r_mult" not in df_trades.columns:
        return pd.DataFrame()
    
    equity = df_trades["r_mult"].cumsum()
    return pd.DataFrame({"equity_r": equity})


def create_drawdown_curve(df_trades: pd.DataFrame) -> pd.DataFrame:
    """Create drawdown curve from trades."""
    if df_trades.empty or "r_mult" not in df_trades.columns:
        return pd.DataFrame()
    
    equity = df_trades["r_mult"].cumsum()
    running_max = equity.expanding().max()
    drawdown = equity - running_max
    
    return pd.DataFrame({"drawdown_r": drawdown})

