"""Candidate generation for trade entries."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def generate_candidates(
    df_features: pd.DataFrame,
    cfg_strategy: Dict[str, Any],
    cfg_market: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate trade entry candidates.
    
    Args:
        df_features: DataFrame with features
        cfg_strategy: Strategy configuration
        cfg_market: Market configuration
    
    Returns:
        List of candidate dicts with: entry, stop, target, risk_points, reward_points, tags, context
    """
    if df_features.empty:
        return []
    
    # Get latest bar
    latest = df_features.iloc[-1]
    current_price = latest.get("close", latest.get("close", 0))
    
    if current_price == 0:
        return []
    
    candidates = []
    cfg_candidates = cfg_strategy.get("candidates", {})
    
    # VWAP-based candidates
    if cfg_candidates.get("vwap", {}).get("enabled", True):
        if "session_vwap" in latest and "atr_14" in latest and pd.notna(latest["session_vwap"]):
            vwap = latest["session_vwap"]
            atr = latest["atr_14"]
            
            multipliers = cfg_candidates.get("vwap", {}).get("atr_multipliers", [0.5, 1.0, 1.5, 2.0])
            
            for k in multipliers:
                # Long: price near VWAP - k*ATR
                entry_long = vwap - k * atr
                stop_long = entry_long - atr * 0.5
                target_long = entry_long + atr * (k + 1.0)
                
                if stop_long < current_price < target_long:
                    risk_points = abs(entry_long - stop_long)
                    reward_points = abs(target_long - entry_long)
                    rr = reward_points / risk_points if risk_points > 0 else 0
                    
                    if cfg_strategy.get("candidates", {}).get("min_rr", 1.5) <= rr <= cfg_strategy.get("candidates", {}).get("max_rr", 5.0):
                        candidates.append({
                            "entry": entry_long,
                            "stop": stop_long,
                            "target": target_long,
                            "risk_points": risk_points,
                            "reward_points": reward_points,
                            "side": "long",
                            "tags": ["vwap", f"vwap-{k}atr"],
                            "context": {"vwap": vwap, "atr": atr, "k": k},
                        })
                
                # Short: price near VWAP + k*ATR
                entry_short = vwap + k * atr
                stop_short = entry_short + atr * 0.5
                target_short = entry_short - atr * (k + 1.0)
                
                if target_short < current_price < stop_short:
                    risk_points = abs(entry_short - stop_short)
                    reward_points = abs(entry_short - target_short)
                    rr = reward_points / risk_points if risk_points > 0 else 0
                    
                    if cfg_strategy.get("candidates", {}).get("min_rr", 1.5) <= rr <= cfg_strategy.get("candidates", {}).get("max_rr", 5.0):
                        candidates.append({
                            "entry": entry_short,
                            "stop": stop_short,
                            "target": target_short,
                            "risk_points": risk_points,
                            "reward_points": reward_points,
                            "side": "short",
                            "tags": ["vwap", f"vwap+{k}atr"],
                            "context": {"vwap": vwap, "atr": atr, "k": k},
                        })
    
    # Opening range retests
    if cfg_candidates.get("opening_range", {}).get("enabled", True):
        if "opening_range_high" in latest and "opening_range_low" in latest:
            orh = latest["opening_range_high"]
            orl = latest["opening_range_low"]
            tolerance = cfg_candidates.get("opening_range", {}).get("tolerance_ticks", 2) * 0.25  # Convert to price
            
            if pd.notna(orh) and pd.notna(orl):
                # Long: retest of ORL
                if abs(current_price - orl) <= tolerance:
                    stop = orl - atr * 0.5 if "atr_14" in latest else orl - (orh - orl) * 0.5
                    target = orh
                    risk_points = abs(orl - stop)
                    reward_points = abs(target - orl)
                    rr = reward_points / risk_points if risk_points > 0 else 0
                    
                    if rr >= cfg_strategy.get("candidates", {}).get("min_rr", 1.5):
                        candidates.append({
                            "entry": orl,
                            "stop": stop,
                            "target": target,
                            "risk_points": risk_points,
                            "reward_points": reward_points,
                            "side": "long",
                            "tags": ["opening_range", "orl_retest"],
                            "context": {"orh": orh, "orl": orl},
                        })
                
                # Short: retest of ORH
                if abs(current_price - orh) <= tolerance:
                    stop = orh + atr * 0.5 if "atr_14" in latest else orh + (orh - orl) * 0.5
                    target = orl
                    risk_points = abs(orh - stop)
                    reward_points = abs(orh - target)
                    rr = reward_points / risk_points if risk_points > 0 else 0
                    
                    if rr >= cfg_strategy.get("candidates", {}).get("min_rr", 1.5):
                        candidates.append({
                            "entry": orh,
                            "stop": stop,
                            "target": target,
                            "risk_points": risk_points,
                            "reward_points": reward_points,
                            "side": "short",
                            "tags": ["opening_range", "orh_retest"],
                            "context": {"orh": orh, "orl": orl},
                        })
    
    # Prior session levels
    if cfg_candidates.get("prior_session", {}).get("enabled", True):
        if "prior_high" in latest and "prior_low" in latest:
            ph = latest["prior_high"]
            pl = latest["prior_low"]
            tolerance = cfg_candidates.get("prior_session", {}).get("tolerance_ticks", 2) * 0.25
            
            if pd.notna(ph) and pd.notna(pl):
                atr = latest.get("atr_14", (ph - pl) * 0.1)
                
                # Long: retest of prior low
                if abs(current_price - pl) <= tolerance:
                    stop = pl - atr * 0.5
                    target = ph
                    risk_points = abs(pl - stop)
                    reward_points = abs(target - pl)
                    rr = reward_points / risk_points if risk_points > 0 else 0
                    
                    if rr >= cfg_strategy.get("candidates", {}).get("min_rr", 1.5):
                        candidates.append({
                            "entry": pl,
                            "stop": stop,
                            "target": target,
                            "risk_points": risk_points,
                            "reward_points": reward_points,
                            "side": "long",
                            "tags": ["prior_session", "prior_low"],
                            "context": {"prior_high": ph, "prior_low": pl},
                        })
                
                # Short: retest of prior high
                if abs(current_price - ph) <= tolerance:
                    stop = ph + atr * 0.5
                    target = pl
                    risk_points = abs(ph - stop)
                    reward_points = abs(ph - target)
                    rr = reward_points / risk_points if risk_points > 0 else 0
                    
                    if rr >= cfg_strategy.get("candidates", {}).get("min_rr", 1.5):
                        candidates.append({
                            "entry": ph,
                            "stop": stop,
                            "target": target,
                            "risk_points": risk_points,
                            "reward_points": reward_points,
                            "side": "short",
                            "tags": ["prior_session", "prior_high"],
                            "context": {"prior_high": ph, "prior_low": pl},
                        })
    
    # Simple swing high/low (pivot-based)
    if cfg_candidates.get("swing", {}).get("enabled", True):
        lookback = cfg_candidates.get("swing", {}).get("pivot_lookback", 5)
        min_swing_atr = cfg_candidates.get("swing", {}).get("min_swing_size_atr", 1.0)
        
        if len(df_features) > lookback * 2 and "atr_14" in latest:
            atr = latest["atr_14"]
            recent = df_features.iloc[-lookback*2:]
            
            # Find swing high
            for i in range(lookback, len(recent) - lookback):
                if recent.iloc[i]["high"] == recent.iloc[i-lookback:i+lookback+1]["high"].max():
                    swing_high = recent.iloc[i]["high"]
                    if swing_high - current_price >= min_swing_atr * atr:
                        # Short candidate
                        stop = swing_high + atr * 0.5
                        target = current_price - (swing_high - current_price) * 1.5
                        risk_points = abs(swing_high - stop)
                        reward_points = abs(swing_high - target)
                        rr = reward_points / risk_points if risk_points > 0 else 0
                        
                        if rr >= cfg_strategy.get("candidates", {}).get("min_rr", 1.5):
                            candidates.append({
                                "entry": swing_high,
                                "stop": stop,
                                "target": target,
                                "risk_points": risk_points,
                                "reward_points": reward_points,
                                "side": "short",
                                "tags": ["swing", "swing_high"],
                                "context": {"swing_high": swing_high},
                            })
            
            # Find swing low
            for i in range(lookback, len(recent) - lookback):
                if recent.iloc[i]["low"] == recent.iloc[i-lookback:i+lookback+1]["low"].min():
                    swing_low = recent.iloc[i]["low"]
                    if current_price - swing_low >= min_swing_atr * atr:
                        # Long candidate
                        stop = swing_low - atr * 0.5
                        target = current_price + (current_price - swing_low) * 1.5
                        risk_points = abs(swing_low - stop)
                        reward_points = abs(target - swing_low)
                        rr = reward_points / risk_points if risk_points > 0 else 0
                        
                        if rr >= cfg_strategy.get("candidates", {}).get("min_rr", 1.5):
                            candidates.append({
                                "entry": swing_low,
                                "stop": stop,
                                "target": target,
                                "risk_points": risk_points,
                                "reward_points": reward_points,
                                "side": "long",
                                "tags": ["swing", "swing_low"],
                                "context": {"swing_low": swing_low},
                            })
    
    logger.debug(f"Generated {len(candidates)} candidates")
    return candidates

