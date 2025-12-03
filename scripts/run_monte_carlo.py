#!/usr/bin/env python3
"""Run Monte Carlo simulation."""

import sys
import json
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.core.config import get_config
from jcq.sim.monte_carlo import run_monte_carlo
from jcq.storage.db import get_engine
from jcq.storage.schema import SimRun
from sqlalchemy import text

logger = get_logger(__name__)


def main():
    """Run Monte Carlo simulation."""
    setup_logging()
    logger.info("Running Monte Carlo simulation...")
    
    config = get_config()
    
    try:
        # Load trades from latest backtest run
        runs_dir = Path(config.get("app", {}).get("runs_dir", "data/runs"))
        run_dirs = sorted(runs_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        df_trades = None
        for run_dir in run_dirs:
            trades_path = run_dir / "trades.parquet"
            if trades_path.exists():
                df_trades = pd.read_parquet(trades_path)
                logger.info(f"Loaded trades from {run_dir}")
                break
        
        if df_trades is None or df_trades.empty:
            logger.error("No trades found")
            return 1
        
        # Run Monte Carlo
        metrics = run_monte_carlo(df_trades, n_simulations=1000)
        
        logger.info(f"Monte Carlo results: {metrics}")
        
        # Save results
        if df_trades is not None and len(df_trades) > 0:
            run_id = run_dir.name
            mc_path = run_dir / "mc.json"
            with open(mc_path, "w") as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Saved Monte Carlo results to {mc_path}")
            
            # Store in database
            try:
                engine = get_engine()
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO sim_runs (metrics)
                            VALUES (:metrics)
                        """),
                        {"metrics": json.dumps(metrics)},
                    )
                logger.info("Stored Monte Carlo results in database")
            except Exception as e:
                logger.warning(f"Failed to store in database: {e}")
        
        return 0
    except Exception as e:
        logger.error(f"Monte Carlo simulation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

