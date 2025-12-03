"""Parquet storage for time-series data."""

from pathlib import Path
from typing import Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import logging

from jcq.core.config import get_config

logger = logging.getLogger(__name__)


def _get_data_dir() -> Path:
    """Get data directory from config."""
    config = get_config()
    data_dir = config.get("app", {}).get("data_dir", "data")
    repo_root = Path(__file__).parent.parent.parent.parent
    return repo_root / data_dir


def write_bars(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str = "1m",
    partition_by_date: bool = True,
) -> str:
    """
    Write bars to Parquet with date partitioning.
    
    Args:
        df: DataFrame with timestamp index and ohlcv columns
        symbol: Symbol (e.g., "NQ")
        timeframe: Timeframe (e.g., "1m")
        partition_by_date: If True, partition by date
    
    Returns:
        Path to written file(s)
    """
    if df.empty:
        raise ValueError("Cannot write empty DataFrame")
    
    data_dir = _get_data_dir()
    base_path = data_dir / "bars" / symbol / timeframe
    
    if "timestamp" not in df.columns and df.index.name == "timestamp":
        df = df.reset_index()
    
    # Ensure timestamp column
    if "timestamp" not in df.columns:
        raise ValueError("DataFrame must have 'timestamp' column or index")
    
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    
    if partition_by_date:
        # Add date partition column
        df["date"] = df["timestamp"].dt.date.astype(str)
        
        # Write partitioned
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_to_dataset(
            table,
            base_path,
            partition_cols=["date"],
            use_dictionary=True,
            compression="snappy",
        )
        logger.info(f"Wrote {len(df)} bars to {base_path} (partitioned)")
        return str(base_path)
    else:
        # Write single file
        base_path.mkdir(parents=True, exist_ok=True)
        file_path = base_path / f"{symbol}_{timeframe}.parquet"
        df.to_parquet(file_path, compression="snappy", index=False)
        logger.info(f"Wrote {len(df)} bars to {file_path}")
        return str(file_path)


def read_bars(
    symbol: str,
    timeframe: str = "1m",
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Read bars from Parquet.
    
    Args:
        symbol: Symbol (e.g., "NQ")
        timeframe: Timeframe (e.g., "1m")
        start: Start timestamp (UTC)
        end: End timestamp (UTC)
    
    Returns:
        DataFrame with timestamp column and ohlcv
    """
    data_dir = _get_data_dir()
    base_path = data_dir / "bars" / symbol / timeframe
    
    if not base_path.exists():
        logger.warning(f"Path does not exist: {base_path}")
        return pd.DataFrame()
    
    # Read partitioned dataset
    try:
        dataset = pq.ParquetDataset(base_path)
        df = dataset.read_pandas().to_pandas()
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.sort_values("timestamp")
            
            if start is not None:
                df = df[df["timestamp"] >= start]
            if end is not None:
                df = df[df["timestamp"] <= end]
        
        # Drop partition column if present
        if "date" in df.columns:
            df = df.drop(columns=["date"])
        
        logger.debug(f"Read {len(df)} bars from {base_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to read bars: {e}")
        return pd.DataFrame()


def write_features(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str = "1m",
    partition_by_date: bool = True,
) -> str:
    """
    Write features to Parquet.
    
    Args:
        df: DataFrame with timestamp index and features
        symbol: Symbol (e.g., "NQ")
        timeframe: Timeframe (e.g., "1m")
        partition_by_date: If True, partition by date
    
    Returns:
        Path to written file(s)
    """
    if df.empty:
        raise ValueError("Cannot write empty DataFrame")
    
    data_dir = _get_data_dir()
    base_path = data_dir / "features" / symbol / timeframe
    
    # Ensure timestamp column
    if df.index.name == "timestamp" or "timestamp" in df.index.names:
        df = df.reset_index()
    
    if "timestamp" not in df.columns:
        raise ValueError("DataFrame must have timestamp index or column")
    
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    
    if partition_by_date:
        df["date"] = df["timestamp"].dt.date.astype(str)
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_to_dataset(
            table,
            base_path,
            partition_cols=["date"],
            use_dictionary=True,
            compression="snappy",
        )
        logger.info(f"Wrote {len(df)} feature rows to {base_path} (partitioned)")
        return str(base_path)
    else:
        base_path.mkdir(parents=True, exist_ok=True)
        file_path = base_path / f"{symbol}_{timeframe}_features.parquet"
        df.to_parquet(file_path, compression="snappy", index=False)
        logger.info(f"Wrote {len(df)} feature rows to {file_path}")
        return str(file_path)


def read_features(
    symbol: str,
    timeframe: str = "1m",
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Read features from Parquet.
    
    Args:
        symbol: Symbol (e.g., "NQ")
        timeframe: Timeframe (e.g., "1m")
        start: Start timestamp (UTC)
        end: End timestamp (UTC)
    
    Returns:
        DataFrame with timestamp index and features
    """
    data_dir = _get_data_dir()
    base_path = data_dir / "features" / symbol / timeframe
    
    if not base_path.exists():
        logger.warning(f"Path does not exist: {base_path}")
        return pd.DataFrame()
    
    try:
        dataset = pq.ParquetDataset(base_path)
        df = dataset.read_pandas().to_pandas()
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.set_index("timestamp").sort_index()
            
            if start is not None:
                df = df[df.index >= start]
            if end is not None:
                df = df[df.index <= end]
        
        if "date" in df.columns:
            df = df.drop(columns=["date"])
        
        logger.debug(f"Read {len(df)} feature rows from {base_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to read features: {e}")
        return pd.DataFrame()


def write_macro(df: pd.DataFrame, series_name: str) -> str:
    """
    Write macro series to Parquet.
    
    Args:
        df: DataFrame with date index and value column
        series_name: Series name (e.g., "FEDFUNDS")
    
    Returns:
        Path to written file
    """
    if df.empty:
        raise ValueError("Cannot write empty DataFrame")
    
    data_dir = _get_data_dir()
    base_path = data_dir / "macro" / f"series={series_name}"
    base_path.mkdir(parents=True, exist_ok=True)
    
    file_path = base_path / f"{series_name}.parquet"
    df.to_parquet(file_path, compression="snappy")
    logger.info(f"Wrote macro series {series_name} to {file_path}")
    return str(file_path)


def read_macro(series_name: str) -> pd.DataFrame:
    """
    Read macro series from Parquet.
    
    Args:
        series_name: Series name (e.g., "FEDFUNDS")
    
    Returns:
        DataFrame with date index and value column
    """
    data_dir = _get_data_dir()
    file_path = data_dir / "macro" / f"series={series_name}" / f"{series_name}.parquet"
    
    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
        return pd.DataFrame()
    
    try:
        df = pd.read_parquet(file_path)
        logger.debug(f"Read macro series {series_name} from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to read macro: {e}")
        return pd.DataFrame()

