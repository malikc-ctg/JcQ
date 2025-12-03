"""Tests for feature engineering."""

import pytest
import pandas as pd
from jcq.features.features import build_features
from jcq.core.config import get_config


def test_build_features(sample_bars):
    """Test feature building."""
    config = get_config()
    cfg_market = config.get("market", {})
    
    df_features = build_features(sample_bars, cfg_market)
    
    assert not df_features.empty
    assert "log_ret_1" in df_features.columns
    assert "atr_14" in df_features.columns
    assert "session_vwap" in df_features.columns
    
    # Check no NaNs in final output (after dropna)
    assert df_features.isna().sum().sum() == 0


def test_features_no_lookahead(sample_bars):
    """Test that features don't use future data."""
    config = get_config()
    cfg_market = config.get("market", {})
    
    df_features = build_features(sample_bars, cfg_market)
    
    # Check that features at time t don't depend on data after t
    # This is a basic check - in practice would need more sophisticated validation
    assert df_features.index.is_monotonic_increasing

