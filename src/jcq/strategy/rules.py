"""Rule-based filtering of candidates."""

from typing import List, Dict, Any
import pandas as pd
import logging

from jcq.core.time import is_rth
from jcq.core.config import get_config

logger = logging.getLogger(__name__)


def apply_rules(
    candidates: List[Dict[str, Any]],
    df_features: pd.DataFrame,
    cfg_strategy: Dict[str, Any],
    cfg_market: Dict[str, Any],
    current_timestamp: pd.Timestamp,
) -> List[Dict[str, Any]]:
    """
    Apply rule-based filters to candidates.
    
    Args:
        candidates: List of scored candidates
        df_features: Latest features DataFrame
        cfg_strategy: Strategy configuration
        cfg_market: Market configuration
        current_timestamp: Current timestamp
    
    Returns:
        Filtered list of candidates with rejection reasons logged
    """
    if not candidates:
        return []
    
    filtered = []
    cfg_rules = cfg_strategy.get("rules", {})
    
    for candidate in candidates:
        rejected = False
        reason = None
        
        # Time-based filters
        time_filters = cfg_rules.get("time_filters", {})
        avoid_first = time_filters.get("avoid_first_minutes", 5)
        avoid_last = time_filters.get("avoid_last_minutes", 5)
        
        if is_rth(current_timestamp):
            from jcq.core.time import minutes_since_rth_open
            minutes = minutes_since_rth_open(current_timestamp)
            if minutes is not None:
                if minutes < avoid_first:
                    rejected = True
                    reason = f"Within first {avoid_first} minutes of RTH"
                elif minutes > (16 * 60 - avoid_last):  # 16:00 - avoid_last
                    rejected = True
                    reason = f"Within last {avoid_last} minutes of RTH"
        
        # Trade windows
        trade_windows = cfg_market.get("sessions", {}).get("trade_windows", [])
        if trade_windows:
            in_window = False
            current_et = current_timestamp.tz_convert("America/New_York")
            current_time = current_et.time()
            
            for window in trade_windows:
                from datetime import time as dt_time
                start_time = dt_time.fromisoformat(window["start"])
                end_time = dt_time.fromisoformat(window["end"])
                
                if start_time <= current_time <= end_time:
                    in_window = True
                    break
            
            if not in_window:
                rejected = True
                reason = "Outside configured trade windows"
        
        # Regime constraints
        if cfg_rules.get("regime", {}).get("disable_mean_reversion_in_trend", True):
            if "regime" in df_features.columns:
                latest_regime = df_features.iloc[-1].get("regime", "")
                if "trend" in latest_regime and "vwap" in candidate.get("tags", []):
                    rejected = True
                    reason = "Mean reversion disabled in trend regime"
        
        # Volatility gates
        volatility = cfg_rules.get("volatility", {})
        if "atr_14" in df_features.columns:
            atr = df_features.iloc[-1]["atr_14"]
            atr_percentile = df_features["atr_14"].rolling(100, min_periods=10).quantile(0.5)
            
            min_atr_pct = volatility.get("min_atr_percentile", 10)
            max_atr_pct = volatility.get("max_atr_percentile", 90)
            
            # Simplified check (would need proper percentile calculation)
            if atr < atr_percentile.iloc[-1] * (min_atr_pct / 50):
                rejected = True
                reason = f"ATR below {min_atr_pct}th percentile"
            elif atr > atr_percentile.iloc[-1] * (max_atr_pct / 50):
                rejected = True
                reason = f"ATR above {max_atr_pct}th percentile"
        
        # News blackouts (placeholder)
        if cfg_rules.get("blackouts", {}).get("enabled", False):
            # TODO: Implement schedule-based blackouts
            pass
        
        if not rejected:
            filtered.append(candidate)
        else:
            logger.debug(f"Rejected candidate {candidate.get('tags', [])}: {reason}")
    
    logger.info(f"Filtered {len(candidates)} candidates to {len(filtered)} after rules")
    return filtered

