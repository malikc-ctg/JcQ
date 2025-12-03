#!/usr/bin/env python3
"""Generate HTML report."""

import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.core.config import get_config
from jcq.eval.metrics import calculate_metrics
from jcq.dashboard.report import generate_report

logger = get_logger(__name__)


def main():
    """Generate report."""
    setup_logging()
    logger.info("Generating report...")
    
    config = get_config()
    
    try:
        # Load trades from latest backtest run
        runs_dir = Path(config.get("app", {}).get("runs_dir", "data/runs"))
        run_dirs = sorted(runs_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        df_trades = None
        run_id = None
        for run_dir in run_dirs:
            trades_path = run_dir / "trades.parquet"
            if trades_path.exists():
                df_trades = pd.read_parquet(trades_path)
                run_id = run_dir.name
                logger.info(f"Loaded trades from {run_dir}")
                break
        
        if df_trades is None or df_trades.empty:
            logger.error("No trades found")
            return 1
        
        # Calculate metrics
        metrics = calculate_metrics(df_trades)
        
        # Generate report
        report_path = run_dir / "report.html"
        generate_report(df_trades, metrics, str(report_path), run_id)
        
        logger.info(f"Report generated: {report_path}")
        
        return 0
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

