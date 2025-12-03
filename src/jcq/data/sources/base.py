"""Base interface for bar data sources."""

from typing import Protocol, Generator, Dict, Any
import pandas as pd


class BarsSource(Protocol):
    """Protocol for bar data sources."""
    
    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        """
        Fetch historical bars.
        
        Args:
            symbol: Symbol (e.g., "NQ")
            timeframe: Timeframe (e.g., "1m")
            start: Start timestamp (UTC)
            end: End timestamp (UTC)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        ...
    
    def stream_live(
        self,
        symbol: str,
        timeframe: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream live bars.
        
        Args:
            symbol: Symbol (e.g., "NQ")
            timeframe: Timeframe (e.g., "1m")
        
        Yields:
            Dict with keys: timestamp, open, high, low, close, volume
        """
        ...

