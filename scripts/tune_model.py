#!/usr/bin/env python3
"""Hyperparameter tuning for models."""

import sys
from pathlib import Path
import pandas as pd
from sklearn.model_selection import ParameterGrid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.core.config import get_config
from jcq.storage.db import read_bars
from jcq.storage.parquet_store import read_bars as read_bars_parquet
from jcq.features.features import build_features
from jcq.labels.labels import create_labels
from jcq.models.prob_model import ProbModel
from sklearn.metrics import brier_score_loss

logger = get_logger(__name__)


def main():
    """Tune model hyperparameters."""
    setup_logging()
    logger.info("Tuning model...")
    
    config = get_config()
    cfg_model = config.get("model", {})
    cfg_strategy = config.get("strategy", {})
    cfg_market = config.get("market", {})
    
    # Load data
    symbol = "NQ"
    timeframe = "1m"
    
    df_bars = read_bars_parquet(symbol, timeframe)
    if df_bars.empty:
        df_bars = read_bars(symbol, timeframe)
    
    if df_bars.empty:
        logger.error("No bars found")
        return 1
    
    # Build features and labels
    df_features = build_features(df_bars, cfg_market)
    df_labeled = create_labels(df_features, cfg_strategy)
    
    feature_cols = [c for c in df_labeled.columns if c not in ["label", "timestamp"]]
    X = df_labeled[feature_cols]
    y = df_labeled["label"].dropna()
    
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    if len(X) < 100:
        logger.error("Not enough samples")
        return 1
    
    # Simple grid search for logistic regression
    param_grid = {
        "C": [0.1, 1.0, 10.0],
    }
    
    best_score = float("inf")
    best_params = None
    
    for params in ParameterGrid(param_grid):
        model_config = cfg_model.get("model", {}).copy()
        model_config["logistic"] = {**model_config.get("logistic", {}), **params}
        
        model = ProbModel(model_type="logistic", config={"model": model_config})
        model.fit(X, y)
        
        # Evaluate (simplified - would use proper CV)
        proba = model.predict_proba(X)
        score = brier_score_loss(y, proba[:, 1])
        
        logger.info(f"Params {params}: Brier score = {score:.4f}")
        
        if score < best_score:
            best_score = score
            best_params = params
    
    logger.info(f"Best params: {best_params}, Brier score: {best_score:.4f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

