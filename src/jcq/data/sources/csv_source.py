"""CSV/Parquet replay source for historical data."""

from typing import Generator, Dict, Any, Optional
import pandas as pd
import time
from pathlib import Path

from jcq.data.sources.base import BarsSource
from jcq.storage.parquet_store import read_bars


class CsvReplaySource(BarsSource):
    """Replay source that reads from Parquet/CSV and streams with speed control."""
    
    def __init__(
        self,
        parquet_path: Optional[str] = None,
        csv_path: Optional[str] = None,
        speed_multiplier: float = 1.0,
    ):
        """
        Initialize replay source.
        
        Args:
            parquet_path: Path to Parquet directory or file
            csv_path: Path to CSV file (alternative to parquet_path)
            speed_multiplier: Speed multiplier (1.0 = real-time, 10.0 = 10x speed)
        """
        self.parquet_path = parquet_path
        self.csv_path = csv_path
        self.speed_multiplier = speed_multiplier
        self._data: Dict[str, pd.DataFrame] = {}
    
    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        """Fetch historical bars from stored files."""
        cache_key = f"{symbol}_{timeframe}"
        
        if cache_key not in self._data:
            # Load data
            if self.parquet_path:
                # Try to read from parquet store
                df = read_bars(symbol, timeframe, start, end)
                if df.empty:
                    # Try direct path
                    path = Path(self.parquet_path)
                    if path.is_file():
                        df = pd.read_parquet(path)
                    elif path.is_dir():
                        # Try partitioned read
                        import pyarrow.parquet as pq
                        dataset = pq.ParquetDataset(path)
                        df = dataset.read_pandas().to_pandas()
            elif self.csv_path:
                df = pd.read_csv(self.csv_path, parse_dates=["timestamp"])
            else:
                raise ValueError("Either parquet_path or csv_path must be provided")
            
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
                df = df.sort_values("timestamp")
            
            self._data[cache_key] = df
        
        df = self._data[cache_key]
        
        # Filter by time range
        if "timestamp" in df.columns:
            mask = (df["timestamp"] >= start) & (df["timestamp"] <= end)
            df = df[mask].copy()
        
        return df
    
    def stream_live(
        self,
        symbol: str,
        timeframe: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream bars with speed control (replay mode).
        
        Yields bars at the configured speed multiplier.
        """
        # Load all data
        df = self.fetch_historical(
            symbol,
            timeframe,
            pd.Timestamp("2020-01-01", tz="UTC"),
            pd.Timestamp.now(tz="UTC"),
        )
        
        if df.empty:
            return
        
        # Calculate time deltas
        df = df.sort_values("timestamp")
        df["delta"] = df["timestamp"].diff().dt.total_seconds()
        df["delta"] = df["delta"].fillna(0)
        
        last_time = time.time()
        
        for _, row in df.iterrows():
            # Wait for the appropriate time (adjusted by speed multiplier)
            delta = row["delta"] / self.speed_multiplier
            if delta > 0:
                time.sleep(delta)
            
            yield {
                "timestamp": row["timestamp"],
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }

