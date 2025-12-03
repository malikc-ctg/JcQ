"""Tests for candidate generation."""

import pytest
import pandas as pd
from jcq.strategy.candidates import generate_candidates
from jcq.core.config import get_config


def test_generate_candidates(sample_features):
    """Test candidate generation."""
    config = get_config()
    cfg_strategy = config.get("strategy", {})
    cfg_market = config.get("market", {})
    
    candidates = generate_candidates(sample_features, cfg_strategy, cfg_market)
    
    # Should generate some candidates
    assert isinstance(candidates, list)
    
    if candidates:
        candidate = candidates[0]
        assert "entry" in candidate
        assert "stop" in candidate
        assert "target" in candidate
        assert "risk_points" in candidate
        assert "reward_points" in candidate
        assert "side" in candidate

