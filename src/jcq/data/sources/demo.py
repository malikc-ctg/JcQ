"""Demo/synthetic bar data source."""

from typing import Generator, Dict, Any
import pandas as pd
import numpy as np
from datetime import timedelta

from jcq.data.sources.base import BarsSource
from jcq.data.demo_generator import generate_bars


class DemoBarsSource(BarsSource):
    """Synthetic bar data source for testing and demos."""
    
    def __init__(self, seed: int = 42):
        """
        Initialize demo source.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        self._cache: Dict[str, pd.DataFrame] = {}
    
    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        """Fetch historical bars (generates synthetic data)."""
        cache_key = f"{symbol}_{timeframe}_{start}_{end}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generate synthetic bars
        df = generate_bars(
            symbol=symbol,
            start=start,
            end=end,
            timeframe=timeframe,
            seed=self.seed,
        )
        
        self._cache[cache_key] = df
        return df
    
    def stream_live(
        self,
        symbol: str,
        timeframe: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream live bars (generates synthetic data in real-time).
        
        Note: This is a demo implementation that generates bars on-demand.
        """
        # For demo, generate a chunk and yield bars one by one
        end = pd.Timestamp.now(tz="UTC")
        start = end - timedelta(days=1)
        
        df = self.fetch_historical(symbol, timeframe, start, end)
        
        for _, row in df.iterrows():
            yield {
                "timestamp": row["timestamp"],
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }

