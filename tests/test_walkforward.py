"""Tests for walk-forward validation."""

import pytest
import pandas as pd
from jcq.eval.walk_forward import WalkForwardValidator
from jcq.core.config import get_config


def test_walk_forward_splits(sample_bars):
    """Test walk-forward splits."""
    config = get_config()
    cfg_strategy = config.get("strategy", {})
    cfg_market = config.get("market", {})
    cfg_risk = config.get("risk", {})
    cfg_model = config.get("model", {})
    
    validator = WalkForwardValidator(cfg_strategy, cfg_market, cfg_risk, cfg_model)
    
    # Run with small windows for testing
    results = validator.run(sample_bars, "NQ", train_days=10, test_days=5, step_days=5)
    
    assert isinstance(results, pd.DataFrame)

