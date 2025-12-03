"""Synthetic bar data generator for demos."""

import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def generate_bars(
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    timeframe: str = "1m",
    seed: int = 42,
    base_price: float = 15000.0,
    volatility: float = 0.001,
) -> pd.DataFrame:
    """
    Generate realistic synthetic futures bars with regimes and volatility clustering.
    
    Args:
        symbol: Symbol (e.g., "NQ", "MNQ")
        start: Start timestamp (UTC)
        end: End timestamp (UTC)
        timeframe: Bar timeframe (e.g., "1m")
        seed: Random seed
        base_price: Starting price
        volatility: Base volatility (daily)
    
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    np.random.seed(seed)
    
    # Parse timeframe
    if timeframe.endswith("m"):
        minutes = int(timeframe[:-1])
    elif timeframe.endswith("h"):
        minutes = int(timeframe[:-1]) * 60
    elif timeframe.endswith("d"):
        minutes = int(timeframe[:-1]) * 24 * 60
    else:
        minutes = 1
    
    # Generate timestamps (only trading hours: 18:00-17:00 ET with maintenance break)
    timestamps = []
    current = start
    
    while current <= end:
        # Skip maintenance break (17:00-18:00 ET)
        current_et = current.tz_convert("America/New_York")
        hour = current_et.hour
        
        if hour != 17:  # Skip maintenance break hour
            timestamps.append(current)
        
        current += timedelta(minutes=minutes)
    
    if not timestamps:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    
    n_bars = len(timestamps)
    
    # Generate price series with regimes
    # Use GARCH-like volatility clustering
    returns = np.zeros(n_bars)
    vol = volatility
    
    # Regime switches (trending vs choppy)
    regime_length = n_bars // 10  # ~10 regimes
    regimes = []
    for i in range(0, n_bars, regime_length):
        regime_type = np.random.choice(["trend", "choppy", "volatile"])
        regimes.extend([regime_type] * min(regime_length, n_bars - i))
    regimes = regimes[:n_bars]
    
    prices = [base_price]
    
    for i in range(1, n_bars):
        regime = regimes[i]
        
        # Adjust volatility based on regime
        if regime == "volatile":
            vol_mult = 2.0
        elif regime == "choppy":
            vol_mult = 0.5
        else:
            vol_mult = 1.0
        
        # Volatility clustering (GARCH-like)
        vol = 0.9 * vol + 0.1 * (abs(returns[i-1]) * vol_mult if i > 0 else volatility)
        vol = max(volatility * 0.1, min(volatility * 3.0, vol))
        
        # Generate return
        if regime == "trend":
            # Add drift
            drift = np.random.normal(0.0001, 0.00005)
            ret = np.random.normal(drift, vol * vol_mult)
        else:
            ret = np.random.normal(0, vol * vol_mult)
        
        returns[i] = ret
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    # Round to tick size (0.25 for NQ/MNQ)
    tick_size = 0.25
    prices = [round(p / tick_size) * tick_size for p in prices]
    
    # Generate OHLC from prices
    bars = []
    for i, ts in enumerate(timestamps):
        close = prices[i]
        
        # Generate realistic OHLC
        # High and low are within a range around close
        range_pct = abs(returns[i]) * 2 + 0.0001  # At least 0.01% range
        high_offset = np.random.uniform(0, range_pct * 0.6)
        low_offset = np.random.uniform(-range_pct * 0.6, 0)
        
        high = close * (1 + high_offset)
        low = close * (1 + low_offset)
        
        # Open is between previous close and current close
        if i > 0:
            open_price = prices[i-1] + (close - prices[i-1]) * np.random.uniform(0.2, 0.8)
        else:
            open_price = close * (1 + np.random.uniform(-0.0001, 0.0001))
        
        # Round to ticks
        open_price = round(open_price / tick_size) * tick_size
        high = round(high / tick_size) * tick_size
        low = round(low / tick_size) * tick_size
        close = round(close / tick_size) * tick_size
        
        # Ensure OHLC relationships
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Generate volume (higher during volatile regimes)
        base_volume = 1000.0
        if regimes[i] == "volatile":
            volume = base_volume * np.random.uniform(1.5, 3.0)
        else:
            volume = base_volume * np.random.uniform(0.5, 1.5)
        
        bars.append({
            "timestamp": ts,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
    
    df = pd.DataFrame(bars)
    logger.info(f"Generated {len(df)} synthetic bars for {symbol} from {start} to {end}")
    
    return df

