#!/usr/bin/env python3
"""Ingest FRED macro data."""

import sys
import os
import argparse
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.data.macro.fred import fetch_fred_series

logger = get_logger(__name__)


def main():
    """Ingest FRED data."""
    parser = argparse.ArgumentParser(description="Ingest FRED macro data")
    parser.add_argument("--series", nargs="+", default=["FEDFUNDS", "WALCL", "RRPONTSYD"], help="FRED series IDs")
    
    args = parser.parse_args()
    
    setup_logging()
    
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        logger.error("FRED_API_KEY environment variable not set")
        logger.info("Get a free API key from: https://fred.stlouisfed.org/docs/api/api_key.html")
        return 1
    
    logger.info("Fetching FRED data...")
    
    try:
        for series_id in args.series:
            df = fetch_fred_series(series_id, api_key)
            if not df.empty:
                logger.info(f"Fetched {len(df)} points for {series_id}")
            else:
                logger.warning(f"No data for {series_id}")
        
        return 0
    except Exception as e:
        logger.error(f"FRED ingestion failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

