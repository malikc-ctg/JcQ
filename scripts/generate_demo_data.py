#!/usr/bin/env python3
"""Generate demo synthetic data."""

import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.data.demo_generator import generate_bars
from jcq.storage.parquet_store import write_bars
from jcq.storage.db import upsert_bars

logger = get_logger(__name__)


def main():
    """Generate demo data."""
    setup_logging()
    logger.info("Generating demo data...")
    
    # Generate 60 trading days of data
    end = pd.Timestamp.now(tz="UTC")
    start = end - pd.Timedelta(days=90)  # ~60 trading days
    
    symbols = ["NQ", "MNQ"]
    timeframe = "1m"
    
    for symbol in symbols:
        logger.info(f"Generating {symbol} bars...")
        df = generate_bars(symbol, start, end, timeframe, seed=42)
        
        if df.empty:
            logger.warning(f"No bars generated for {symbol}")
            continue
        
        # Write to Parquet
        write_bars(df, symbol, timeframe)
        logger.info(f"Wrote {len(df)} bars to Parquet for {symbol}")
        
        # Write to database
        try:
            count = upsert_bars(df, symbol, timeframe)
            logger.info(f"Upserted {count} bars to database for {symbol}")
        except Exception as e:
            logger.warning(f"Failed to upsert to database: {e}")
    
    logger.info("Demo data generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())

