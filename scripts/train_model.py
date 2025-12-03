#!/usr/bin/env python3
"""Train a probabilistic model."""

import sys
import uuid
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.core.config import get_config
from jcq.storage.db import read_bars
from jcq.storage.parquet_store import read_bars as read_bars_parquet
from jcq.features.features import build_features
from jcq.labels.labels import create_labels
from jcq.models.prob_model import ProbModel
from jcq.models.registry import register_model_run, update_run_status

logger = get_logger(__name__)


def main():
    """Train model."""
    setup_logging()
    logger.info("Training model...")
    
    config = get_config()
    cfg_model = config.get("model", {})
    cfg_strategy = config.get("strategy", {})
    cfg_market = config.get("market", {})
    
    # Register run
    run_id = register_model_run("train", status="running")
    
    try:
        # Load data
        symbol = "NQ"
        timeframe = "1m"
        
        # Try Parquet first, then DB
        df_bars = read_bars_parquet(symbol, timeframe)
        if df_bars.empty:
            df_bars = read_bars(symbol, timeframe)
        
        if df_bars.empty:
            logger.error("No bars found")
            return 1
        
        logger.info(f"Loaded {len(df_bars)} bars")
        
        # Build features
        df_features = build_features(df_bars, cfg_market)
        logger.info(f"Built {len(df_features)} feature rows")
        
        # Create labels
        df_labeled = create_labels(df_features, cfg_strategy)
        
        # Prepare training data
        feature_cols = [c for c in df_labeled.columns if c not in ["label", "timestamp"]]
        X = df_labeled[feature_cols]
        y = df_labeled["label"].dropna()
        
        # Align X and y
        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]
        
        if len(X) < 100:
            logger.error("Not enough samples for training")
            return 1
        
        logger.info(f"Training on {len(X)} samples")
        
        # Train model
        model_type = cfg_model.get("model", {}).get("type", "logistic")
        model = ProbModel(model_type=model_type, config=cfg_model.get("model", {}))
        model.fit(X, y)
        
        # Save model
        model_dir = Path(config.get("app", {}).get("models_dir", "data/models"))
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / f"model_{run_id}.joblib"
        model.save(str(model_path))
        
        logger.info(f"Model saved to {model_path}")
        
        # Update run status
        update_run_status(run_id, "completed", {"model_path": str(model_path)})
        
        return 0
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        update_run_status(run_id, "failed", {"error": str(e)})
        return 1


if __name__ == "__main__":
    sys.exit(main())

