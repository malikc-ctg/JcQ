"""Tests for EV scoring."""

import pytest
import pandas as pd
from jcq.strategy.scorer import score_candidates, rank_candidates
from jcq.models.prob_model import ProbModel
from jcq.core.config import get_config


def test_score_candidates(sample_features):
    """Test candidate scoring."""
    config = get_config()
    cfg_strategy = config.get("strategy", {})
    cfg_model = config.get("model", {})
    
    # Create dummy model
    model = ProbModel(model_type="logistic", config=cfg_model.get("model", {}))
    
    # Fit on sample data (simplified)
    feature_cols = [c for c in sample_features.columns if c not in ["label"]]
    X = sample_features[feature_cols].iloc[:50]
    y = pd.Series([0, 1] * 25, index=X.index)
    
    if len(X) > 0:
        model.fit(X, y)
    
    candidates = [{
        "entry": 15000.0,
        "stop": 14995.0,
        "target": 15010.0,
        "risk_points": 5.0,
        "reward_points": 10.0,
        "side": "long",
        "tags": ["test"],
    }]
    
    scored = score_candidates(candidates, sample_features, model, cfg_strategy)
    
    if scored:
        candidate = scored[0]
        assert "ev_r" in candidate
        assert "p_win" in candidate


def test_rank_candidates():
    """Test candidate ranking."""
    candidates = [
        {"ev_r": 0.5, "p_win": 0.6},
        {"ev_r": 1.0, "p_win": 0.7},
        {"ev_r": 0.3, "p_win": 0.5},
    ]
    
    ranked = rank_candidates(candidates, top_k=2)
    
    assert len(ranked) == 2
    assert ranked[0]["ev_r"] >= ranked[1]["ev_r"]

