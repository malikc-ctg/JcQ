"""Tradovate data source stub."""

from typing import Generator, Dict, Any
import pandas as pd

from jcq.data.sources.base import BarsSource


class TradovateBarsSource(BarsSource):
    """
    Tradovate data source stub.
    
    This is a placeholder for future Tradovate integration.
    To implement:
    1. Install Tradovate API client
    2. Authenticate with API credentials
    3. Request historical data and subscribe to live bars
    4. Implement fetch_historical and stream_live
    """
    
    def __init__(self, api_key: str, api_secret: str, environment: str = "prod"):
        """
        Initialize Tradovate connection.
        
        Args:
            api_key: Tradovate API key
            api_secret: Tradovate API secret
            environment: Environment (prod, demo)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.environment = environment
        raise NotImplementedError(
            "Tradovate integration not implemented. "
            "Install Tradovate API client and implement connection logic."
        )
    
    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        """Fetch historical bars from Tradovate."""
        raise NotImplementedError("Tradovate historical data not implemented")
    
    def stream_live(
        self,
        symbol: str,
        timeframe: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream live bars from Tradovate."""
        raise NotImplementedError("Tradovate live data not implemented")

