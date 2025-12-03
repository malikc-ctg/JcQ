#!/usr/bin/env python3
"""Run backtest."""

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
from jcq.models.prob_model import ProbModel
from jcq.backtest.engine import BacktestEngine
from jcq.models.registry import register_model_run, update_run_status

logger = get_logger(__name__)


def main():
    """Run backtest."""
    setup_logging()
    logger.info("Running backtest...")
    
    config = get_config()
    cfg_strategy = config.get("strategy", {})
    cfg_market = config.get("market", {})
    cfg_risk = config.get("risk", {})
    
    # Register run
    run_id = register_model_run("backtest", status="running")
    
    try:
        # Load model
        model_dir = Path(config.get("app", {}).get("models_dir", "data/models"))
        model_files = list(model_dir.glob("*.joblib"))
        
        if not model_files:
            logger.error("No model found")
            return 1
        
        model_path = model_files[-1]  # Use latest
        model = ProbModel.load(str(model_path))
        logger.info(f"Loaded model from {model_path}")
        
        # Load data
        symbol = "NQ"
        timeframe = "1m"
        
        df_bars = read_bars_parquet(symbol, timeframe)
        if df_bars.empty:
            df_bars = read_bars(symbol, timeframe)
        
        if df_bars.empty:
            logger.error("No bars found")
            return 1
        
        logger.info(f"Loaded {len(df_bars)} bars")
        
        # Run backtest
        engine = BacktestEngine(model, cfg_strategy, cfg_market, cfg_risk)
        results = engine.run(df_bars, symbol, timeframe)
        
        df_trades = results["trades"]
        metrics = results["metrics"]
        
        logger.info(f"Backtest completed: {len(df_trades)} trades")
        logger.info(f"Metrics: {metrics}")
        
        # Save results
        runs_dir = Path(config.get("app", {}).get("runs_dir", "data/runs"))
        run_dir = runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        trades_path = run_dir / "trades.parquet"
        df_trades.to_parquet(trades_path)
        logger.info(f"Saved trades to {trades_path}")
        
        # Update run status
        update_run_status(run_id, "completed", {"metrics": metrics, "num_trades": len(df_trades)})
        
        return 0
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        update_run_status(run_id, "failed", {"error": str(e)})
        return 1


if __name__ == "__main__":
    sys.exit(main())

