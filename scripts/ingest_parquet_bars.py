#!/usr/bin/env python3
"""Ingest bars from Parquet file."""

import sys
import argparse
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.core.validation import validate_bars_df, ensure_monotonic_timestamps
from jcq.core.time import to_utc
from jcq.storage.parquet_store import write_bars
from jcq.storage.db import upsert_bars

logger = get_logger(__name__)


def main():
    """Ingest Parquet bars."""
    parser = argparse.ArgumentParser(description="Ingest bars from Parquet")
    parser.add_argument("--path", required=True, help="Path to Parquet file")
    parser.add_argument("--symbol", required=True, help="Symbol (e.g., NQ)")
    parser.add_argument("--timeframe", default="1m", help="Timeframe")
    parser.add_argument("--timezone", default="America/New_York", help="Timezone of timestamps")
    parser.add_argument("--source", default="parquet", help="Source name")
    
    args = parser.parse_args()
    
    setup_logging()
    logger.info(f"Ingesting bars from {args.path}")
    
    try:
        # Read Parquet
        df = pd.read_parquet(args.path)
        
        # Ensure timestamp column
        if "timestamp" not in df.columns:
            logger.error("Parquet must have 'timestamp' column")
            return 1
        
        # Convert to UTC
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["timestamp"] = df["timestamp"].apply(lambda ts: to_utc(ts, args.timezone))
        
        # Validate
        validate_bars_df(df)
        df = ensure_monotonic_timestamps(df)
        
        # Write
        write_bars(df, args.symbol, args.timeframe)
        logger.info(f"Wrote {len(df)} bars to Parquet")
        
        upsert_bars(df, args.symbol, args.timeframe)
        logger.info(f"Upserted {len(df)} bars to database")
        
        return 0
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

