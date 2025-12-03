"""Performance metrics calculation."""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def calculate_metrics(df_trades: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate comprehensive performance metrics.
    
    Args:
        df_trades: DataFrame with trades (must have r_mult column)
    
    Returns:
        Dict of metrics
    """
    if df_trades.empty or "r_mult" not in df_trades.columns:
        return {}
    
    total_r = df_trades["r_mult"].sum()
    win_rate = (df_trades["r_mult"] > 0).mean()
    avg_win_r = df_trades[df_trades["r_mult"] > 0]["r_mult"].mean() if (df_trades["r_mult"] > 0).any() else 0
    avg_loss_r = df_trades[df_trades["r_mult"] < 0]["r_mult"].mean() if (df_trades["r_mult"] < 0).any() else 0
    
    # Profit factor
    gross_profit = df_trades[df_trades["r_mult"] > 0]["r_mult"].sum()
    gross_loss = abs(df_trades[df_trades["r_mult"] < 0]["r_mult"].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    
    # Max drawdown
    equity_curve = df_trades["r_mult"].cumsum()
    running_max = equity_curve.expanding().max()
    drawdown = equity_curve - running_max
    max_drawdown = drawdown.min()
    
    # Sharpe (approximate)
    if len(df_trades) > 1:
        sharpe = df_trades["r_mult"].mean() / df_trades["r_mult"].std() * np.sqrt(252) if df_trades["r_mult"].std() > 0 else 0
    else:
        sharpe = 0
    
    # Calibration metrics (if available)
    brier_score = None
    if "prob_up" in df_trades.columns and "label" in df_trades.columns:
        # Simplified Brier score
        prob_up = df_trades["prob_up"]
        actual = (df_trades["label"] > 0).astype(float)
        brier_score = ((prob_up - actual) ** 2).mean()
    
    return {
        "total_r": float(total_r),
        "win_rate": float(win_rate),
        "avg_win_r": float(avg_win_r),
        "avg_loss_r": float(avg_loss_r),
        "profit_factor": float(profit_factor),
        "max_drawdown": float(max_drawdown),
        "sharpe": float(sharpe),
        "num_trades": len(df_trades),
        "brier_score": float(brier_score) if brier_score is not None else None,
    }

