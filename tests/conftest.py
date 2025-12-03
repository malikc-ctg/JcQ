"""Pytest configuration and fixtures."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_bars():
    """Sample bars DataFrame for testing."""
    dates = pd.date_range("2024-01-01", periods=100, freq="1min", tz="UTC")
    np.random.seed(42)
    prices = 15000 + np.cumsum(np.random.randn(100) * 10)
    
    return pd.DataFrame({
        "timestamp": dates,
        "open": prices + np.random.randn(100) * 2,
        "high": prices + np.abs(np.random.randn(100) * 5),
        "low": prices - np.abs(np.random.randn(100) * 5),
        "close": prices,
        "volume": np.random.randint(1000, 10000, 100),
    })


@pytest.fixture
def sample_features(sample_bars):
    """Sample features DataFrame."""
    from jcq.features.features import build_features
    from jcq.core.config import get_config
    
    config = get_config()
    cfg_market = config.get("market", {})
    return build_features(sample_bars, cfg_market)

