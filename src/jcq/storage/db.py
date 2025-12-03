"""Database operations with SQLAlchemy."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import logging

from jcq.core.config import get_config
from jcq.core.retry import retry_with_backoff
from jcq.storage.schema import Base

logger = logging.getLogger(__name__)

_ENGINE: Optional[Engine] = None


def get_engine() -> Engine:
    """
    Get or create the database engine.
    
    Uses SUPABASE_DB_URL or DATABASE_URL if set, otherwise falls back to SQLite.
    
    Returns:
        SQLAlchemy engine
    """
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    
    config = get_config()
    db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or config.get("database", {}).get("url")
    
    if db_url:
        # Postgres connection
        pool_size = config.get("database", {}).get("pool_size", 5)
        max_overflow = config.get("database", {}).get("max_overflow", 10)
        pool_timeout = config.get("database", {}).get("pool_timeout", 30)
        echo = config.get("database", {}).get("echo", False)
        
        _ENGINE = create_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            echo=echo,
            pool_pre_ping=True,  # Verify connections before using
        )
        logger.info("Connected to Postgres database")
    else:
        # SQLite fallback
        repo_root = Path(__file__).parent.parent.parent.parent
        db_path = repo_root / "data" / "jcq.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{db_path}"
        
        _ENGINE = create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False},  # SQLite-specific
        )
        logger.info(f"Using SQLite database: {db_path}")
    
    return _ENGINE


def ensure_schema() -> None:
    """Create all tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database schema ensured")


def upsert_bars(df: pd.DataFrame, symbol: str, timeframe: str = "1m") -> int:
    """
    Upsert market bars to database.
    
    Args:
        df: DataFrame with columns: timestamp, open, high, low, close, volume
        symbol: Symbol (e.g., "NQ")
        timeframe: Timeframe (e.g., "1m")
    
    Returns:
        Number of rows inserted/updated
    """
    if df.empty:
        return 0
    
    engine = get_engine()
    
    # Ensure timestamp is timezone-aware UTC
    if "timestamp" in df.columns:
        df = df.copy()
        if df["timestamp"].dtype == "object" or not hasattr(df["timestamp"].dtype, "tz"):
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        elif df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        else:
            df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
    
    # Prepare data
    records = []
    for _, row in df.iterrows():
        records.append({
            "ts": row["timestamp"],
            "symbol": symbol,
            "timeframe": timeframe,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        })
    
    # Batch upsert (Postgres: ON CONFLICT, SQLite: REPLACE)
    def _upsert():
        with engine.begin() as conn:
            if "postgresql" in str(engine.url):
                # Postgres upsert
                from sqlalchemy.dialects.postgresql import insert
                stmt = insert(Base.metadata.tables["market_bars"]).values(records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["ts", "symbol", "timeframe"],
                    set_=dict(
                        open=stmt.excluded.open,
                        high=stmt.excluded.high,
                        low=stmt.excluded.low,
                        close=stmt.excluded.close,
                        volume=stmt.excluded.volume,
                    ),
                )
                result = conn.execute(stmt)
            else:
                # SQLite replace
                conn.execute(
                    text("""
                        INSERT OR REPLACE INTO market_bars 
                        (ts, symbol, timeframe, open, high, low, close, volume)
                        VALUES (:ts, :symbol, :timeframe, :open, :high, :low, :close, :volume)
                    """),
                    records,
                )
                result = conn.execute(text("SELECT changes()"))
                return result.scalar()
            return result.rowcount
    
    try:
        count = retry_with_backoff(_upsert, max_attempts=3)
        logger.debug(f"Upserted {count} bars for {symbol} {timeframe}")
        return count
    except Exception as e:
        logger.error(f"Failed to upsert bars: {e}")
        raise


def read_bars(
    symbol: str,
    timeframe: str = "1m",
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Read market bars from database.
    
    Args:
        symbol: Symbol (e.g., "NQ")
        timeframe: Timeframe (e.g., "1m")
        start: Start timestamp (UTC)
        end: End timestamp (UTC)
    
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    engine = get_engine()
    
    query = """
        SELECT ts as timestamp, open, high, low, close, volume
        FROM market_bars
        WHERE symbol = :symbol AND timeframe = :timeframe
    """
    params = {"symbol": symbol, "timeframe": timeframe}
    
    if start is not None:
        query += " AND ts >= :start"
        params["start"] = start
    
    if end is not None:
        query += " AND ts <= :end"
        params["end"] = end
    
    query += " ORDER BY ts"
    
    try:
        df = pd.read_sql(query, engine, params=params, parse_dates=["timestamp"])
        if not df.empty and df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        return df
    except Exception as e:
        logger.error(f"Failed to read bars: {e}")
        raise


def upsert_features(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str = "1m",
    features_col: str = "features",
) -> int:
    """
    Upsert features to database.
    
    Args:
        df: DataFrame with timestamp index and features column (dict or JSON-serializable)
        symbol: Symbol (e.g., "NQ")
        timeframe: Timeframe (e.g., "1m")
        features_col: Name of column containing features dict
    
    Returns:
        Number of rows inserted/updated
    """
    if df.empty:
        return 0
    
    engine = get_engine()
    
    # Prepare data
    records = []
    for ts, row in df.iterrows():
        if isinstance(ts, pd.Timestamp):
            if ts.tz is None:
                ts = ts.tz_localize("UTC")
            else:
                ts = ts.tz_convert("UTC")
        
        features = row[features_col]
        if isinstance(features, dict):
            import json
            features = json.dumps(features)
        
        records.append({
            "ts": ts,
            "symbol": symbol,
            "timeframe": timeframe,
            "features": features,
        })
    
    def _upsert():
        with engine.begin() as conn:
            if "postgresql" in str(engine.url):
                from sqlalchemy.dialects.postgresql import insert
                stmt = insert(Base.metadata.tables["features_store"]).values(records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["ts", "symbol", "timeframe"],
                    set_=dict(features=stmt.excluded.features),
                )
                result = conn.execute(stmt)
            else:
                conn.execute(
                    text("""
                        INSERT OR REPLACE INTO features_store 
                        (ts, symbol, timeframe, features)
                        VALUES (:ts, :symbol, :timeframe, :features)
                    """),
                    records,
                )
                result = conn.execute(text("SELECT changes()"))
                return result.scalar()
            return result.rowcount
    
    try:
        count = retry_with_backoff(_upsert, max_attempts=3)
        logger.debug(f"Upserted {count} feature rows for {symbol} {timeframe}")
        return count
    except Exception as e:
        logger.error(f"Failed to upsert features: {e}")
        raise


def read_features(
    symbol: str,
    timeframe: str = "1m",
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Read features from database.
    
    Args:
        symbol: Symbol (e.g., "NQ")
        timeframe: Timeframe (e.g., "1m")
        start: Start timestamp (UTC)
        end: End timestamp (UTC)
    
    Returns:
        DataFrame with timestamp index and features column (dict)
    """
    engine = get_engine()
    
    query = """
        SELECT ts, features
        FROM features_store
        WHERE symbol = :symbol AND timeframe = :timeframe
    """
    params = {"symbol": symbol, "timeframe": timeframe}
    
    if start is not None:
        query += " AND ts >= :start"
        params["start"] = start
    
    if end is not None:
        query += " AND ts <= :end"
        params["end"] = end
    
    query += " ORDER BY ts"
    
    try:
        df = pd.read_sql(query, engine, params=params, parse_dates=["ts"])
        df = df.set_index("ts")
        
        # Parse JSON features
        import json
        df["features"] = df["features"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        
        return df
    except Exception as e:
        logger.error(f"Failed to read features: {e}")
        raise

