"""Tests for backtest engine."""

import pytest
import pandas as pd
from jcq.backtest.engine import BacktestEngine
from jcq.models.prob_model import ProbModel
from jcq.core.config import get_config


def test_backtest_engine(sample_bars, sample_features):
    """Test backtest engine."""
    config = get_config()
    cfg_strategy = config.get("strategy", {})
    cfg_market = config.get("market", {})
    cfg_risk = config.get("risk", {})
    cfg_model = config.get("model", {})
    
    # Create dummy model
    model = ProbModel(model_type="logistic", config=cfg_model.get("model", {}))
    
    # Fit on sample data
    feature_cols = [c for c in sample_features.columns if c not in ["label"]]
    X = sample_features[feature_cols].iloc[:50]
    y = pd.Series([0, 1] * 25, index=X.index)
    
    if len(X) > 0:
        model.fit(X, y)
    
    # Run backtest
    engine = BacktestEngine(model, cfg_strategy, cfg_market, cfg_risk)
    results = engine.run(sample_bars, "NQ", "1m")
    
    assert "trades" in results
    assert "metrics" in results
    assert isinstance(results["trades"], pd.DataFrame)

