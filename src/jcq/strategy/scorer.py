"""Candidate scoring by expected value."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging

from jcq.models.prob_model import ProbModel
from jcq.models.bayes import BayesianAdjustment

logger = logging.getLogger(__name__)


def score_candidates(
    candidates: List[Dict[str, Any]],
    df_features: pd.DataFrame,
    model: ProbModel,
    cfg_strategy: Dict[str, Any],
    bayesian_adjuster: Optional[BayesianAdjustment] = None,
) -> List[Dict[str, Any]]:
    """
    Score candidates by expected value.
    
    Args:
        candidates: List of candidate dicts
        df_features: Latest features DataFrame
        model: Fitted ProbModel
        cfg_strategy: Strategy configuration
        bayesian_adjuster: Optional Bayesian adjustment
    
    Returns:
        List of scored candidates with prob_up, prob_down, ev_r, expected_r
    """
    if not candidates or df_features.empty:
        return []
    
    # Get latest features
    latest_features = df_features.iloc[-1:].drop(columns=["label"], errors="ignore")
    
    # Predict probabilities
    try:
        proba = model.predict_proba(latest_features)
        prob_down = proba[0, 0]
        prob_up = proba[0, 1]
    except Exception as e:
        logger.error(f"Failed to predict probabilities: {e}")
        return []
    
    scored = []
    
    for candidate in candidates:
        side = candidate["side"]
        risk_points = candidate["risk_points"]
        reward_points = candidate["reward_points"]
        
        if risk_points <= 0:
            continue
        
        # Get P(win) based on side
        if side == "long":
            p_win = prob_up
        else:
            p_win = prob_down
        
        # Apply Bayesian adjustment if enabled
        if bayesian_adjuster and cfg_strategy.get("scoring", {}).get("use_bayesian_adjustment", False):
            p_win, confidence = bayesian_adjuster.adjust(p_win)
            candidate["confidence"] = confidence
        else:
            candidate["confidence"] = 1.0
        
        # Check min/max prob thresholds
        min_prob = cfg_strategy.get("scoring", {}).get("min_prob", 0.45)
        max_prob = cfg_strategy.get("scoring", {}).get("max_prob", 0.95)
        
        if p_win < min_prob or p_win > max_prob:
            continue
        
        # Compute R ratios
        R_target = reward_points / risk_points
        
        # Expected value in R: P(win) * R_target - (1 - P(win)) * 1.0
        ev_r = p_win * R_target - (1 - p_win) * 1.0
        
        # Expected R (expected return in R units)
        expected_r = p_win * R_target - (1 - p_win) * 1.0
        
        candidate["prob_up"] = prob_up
        candidate["prob_down"] = prob_down
        candidate["p_win"] = p_win
        candidate["R_target"] = R_target
        candidate["ev_r"] = ev_r
        candidate["expected_r"] = expected_r
        
        scored.append(candidate)
    
    logger.debug(f"Scored {len(scored)} candidates")
    return scored


def rank_candidates(
    candidates: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Rank candidates by EV_R, then prob, then confidence.
    
    Args:
        candidates: List of scored candidates
        top_k: Number of top candidates to return
    
    Returns:
        Ranked list of top candidates
    """
    if not candidates:
        return []
    
    # Sort by: EV_R desc, then p_win desc, then confidence desc
    ranked = sorted(
        candidates,
        key=lambda c: (c.get("ev_r", -999), c.get("p_win", 0), c.get("confidence", 0)),
        reverse=True,
    )
    
    return ranked[:top_k]

