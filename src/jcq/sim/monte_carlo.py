"""Monte Carlo risk simulation."""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def run_monte_carlo(
    df_trades: pd.DataFrame,
    n_simulations: int = 1000,
    confidence_levels: list = [0.95, 0.99],
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation on trade R stream.
    
    Args:
        df_trades: DataFrame with trades (must have r_mult column)
        n_simulations: Number of simulations
        confidence_levels: Confidence levels for VaR/CVaR
    
    Returns:
        Dict with metrics: final_r_dist, max_dd_dist, var, cvar
    """
    if df_trades.empty or "r_mult" not in df_trades.columns:
        return {}
    
    r_stream = df_trades["r_mult"].values
    
    final_r_results = []
    max_dd_results = []
    
    for _ in range(n_simulations):
        # Bootstrap sample
        sample = np.random.choice(r_stream, size=len(r_stream), replace=True)
        
        # Equity curve
        equity = np.cumsum(sample)
        final_r = equity[-1]
        final_r_results.append(final_r)
        
        # Max drawdown
        running_max = np.maximum.accumulate(equity)
        drawdown = equity - running_max
        max_dd = np.min(drawdown)
        max_dd_results.append(max_dd)
    
    final_r_results = np.array(final_r_results)
    max_dd_results = np.array(max_dd_results)
    
    # VaR and CVaR
    var_results = {}
    cvar_results = {}
    
    for cl in confidence_levels:
        alpha = 1 - cl
        var = np.percentile(final_r_results, alpha * 100)
        cvar = final_r_results[final_r_results <= var].mean()
        var_results[f"var_{int(cl*100)}"] = float(var)
        cvar_results[f"cvar_{int(cl*100)}"] = float(cvar)
    
    return {
        "final_r_mean": float(np.mean(final_r_results)),
        "final_r_std": float(np.std(final_r_results)),
        "final_r_min": float(np.min(final_r_results)),
        "final_r_max": float(np.max(final_r_results)),
        "max_dd_mean": float(np.mean(max_dd_results)),
        "max_dd_std": float(np.std(max_dd_results)),
        "max_dd_min": float(np.min(max_dd_results)),
        "max_dd_max": float(np.max(max_dd_results)),
        **var_results,
        **cvar_results,
    }

