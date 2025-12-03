"""Execution simulation for backtesting."""

import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def simulate_execution(
    bars: pd.DataFrame,
    entry_price: float,
    stop_price: float,
    target_price: float,
    side: str,
    entry_bar_idx: int,
) -> Optional[Dict[str, Any]]:
    """
    Simulate bracket order execution.
    
    Assumes:
    - Stop orders have priority (filled first if both triggered)
    - Market orders fill at the worse of open/close (conservative)
    
    Args:
        bars: DataFrame with OHLCV bars
        entry_price: Entry price
        stop_price: Stop loss price
        target_price: Profit target price
        side: "long" or "short"
        entry_bar_idx: Index of entry bar
    
    Returns:
        Dict with: entry_fill, exit_fill, exit_bar_idx, exit_reason, or None if not filled
    """
    if entry_bar_idx >= len(bars):
        return None
    
    entry_bar = bars.iloc[entry_bar_idx]
    
    # Check if entry is filled
    if side == "long":
        if entry_price >= entry_bar["low"] and entry_price <= entry_bar["high"]:
            entry_fill = max(entry_price, entry_bar["open"])  # Conservative: worse of open/entry
        else:
            return None  # Entry not filled
    else:  # short
        if entry_price >= entry_bar["low"] and entry_price <= entry_bar["high"]:
            entry_fill = min(entry_price, entry_bar["open"])  # Conservative
        else:
            return None
    
    # Look forward for stop/target
    for i in range(entry_bar_idx + 1, len(bars)):
        bar = bars.iloc[i]
        
        # Check stop first (priority)
        stop_hit = False
        if side == "long":
            if bar["low"] <= stop_price:
                exit_fill = stop_price  # Stop filled
                stop_hit = True
        else:  # short
            if bar["high"] >= stop_price:
                exit_fill = stop_price
                stop_hit = True
        
        if stop_hit:
            return {
                "entry_fill": entry_fill,
                "exit_fill": exit_fill,
                "exit_bar_idx": i,
                "exit_reason": "stop",
            }
        
        # Check target
        target_hit = False
        if side == "long":
            if bar["high"] >= target_price:
                exit_fill = target_price  # Target filled
                target_hit = True
        else:  # short
            if bar["low"] <= target_price:
                exit_fill = target_price
                target_hit = True
        
        if target_hit:
            return {
                "entry_fill": entry_fill,
                "exit_fill": exit_fill,
                "exit_bar_idx": i,
                "exit_reason": "target",
            }
    
    # Not filled (timeout - would need max bars logic)
    return None

