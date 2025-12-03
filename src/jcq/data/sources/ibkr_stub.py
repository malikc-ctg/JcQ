"""Interactive Brokers data source stub."""

from typing import Generator, Dict, Any
import pandas as pd

from jcq.data.sources.base import BarsSource


class IBKRBarsSource(BarsSource):
    """
    Interactive Brokers data source stub.
    
    This is a placeholder for future IBKR integration.
    To implement:
    1. Install ib_insync or ibapi
    2. Connect to TWS/IB Gateway
    3. Request historical data and subscribe to live bars
    4. Implement fetch_historical and stream_live
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        """
        Initialize IBKR connection.
        
        Args:
            host: TWS/IB Gateway host
            port: TWS/IB Gateway port
            client_id: Client ID
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        raise NotImplementedError(
            "IBKR integration not implemented. "
            "Install ib_insync and implement connection logic."
        )
    
    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        """Fetch historical bars from IBKR."""
        raise NotImplementedError("IBKR historical data not implemented")
    
    def stream_live(
        self,
        symbol: str,
        timeframe: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream live bars from IBKR."""
        raise NotImplementedError("IBKR live data not implemented")

