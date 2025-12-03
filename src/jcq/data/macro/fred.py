"""FRED API client."""

import pandas as pd
from typing import Optional
import logging
import requests

from jcq.storage.parquet_store import write_macro
from jcq.storage.db import get_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


def fetch_fred_series(series_id: str, api_key: str) -> pd.DataFrame:
    """
    Fetch FRED series data.
    
    Args:
        series_id: FRED series ID (e.g., "FEDFUNDS")
        api_key: FRED API key
    
    Returns:
        DataFrame with date index and value column
    """
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": "2020-01-01",
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        observations = data.get("observations", [])
        if not observations:
            logger.warning(f"No observations for {series_id}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        records = []
        for obs in observations:
            if obs.get("value") != ".":  # FRED uses "." for missing
                records.append({
                    "date": pd.to_datetime(obs["date"]).date(),
                    "value": float(obs["value"]),
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df = df.set_index("date")
        
        # Store
        write_macro(df, series_id)
        
        # Store in database
        try:
            engine = get_engine()
            with engine.begin() as conn:
                for date, row in df.iterrows():
                    conn.execute(
                        text("""
                            INSERT INTO macro_series (date, series, value)
                            VALUES (:date, :series, :value)
                            ON CONFLICT (date, series) DO UPDATE SET value = EXCLUDED.value
                        """),
                        {"date": date, "series": series_id, "value": float(row["value"])},
                    )
        except Exception as e:
            logger.warning(f"Failed to store in database: {e}")
        
        logger.info(f"Fetched and stored {len(df)} points for {series_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch FRED series {series_id}: {e}")
        return pd.DataFrame()

