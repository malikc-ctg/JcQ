"""Tests for Monte Carlo simulation."""

import pytest
import pandas as pd
from jcq.sim.monte_carlo import run_monte_carlo


def test_monte_carlo():
    """Test Monte Carlo simulation."""
    # Create sample trades
    df_trades = pd.DataFrame({
        "r_mult": [1.0, -0.5, 2.0, -1.0, 0.5] * 20,  # 100 trades
    })
    
    results = run_monte_carlo(df_trades, n_simulations=100)
    
    assert "final_r_mean" in results
    assert "max_dd_mean" in results
    assert "var_95" in results
    assert "cvar_95" in results

