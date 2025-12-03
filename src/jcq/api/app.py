"""FastAPI application for data ingestion."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import logging

from jcq.storage.db import upsert_bars
from jcq.storage.parquet_store import write_bars
from jcq.core.validation import validate_bars_df, ensure_monotonic_timestamps

logger = logging.getLogger(__name__)


class Bar(BaseModel):
    """Bar data model."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MacroPoint(BaseModel):
    """Macro data point model."""
    date: str
    series: str
    value: float


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(title="JcQ Data Ingestion API", version="0.1.0")
    
    @app.get("/health")
    def health():
        """Health check endpoint."""
        return {"status": "ok"}
    
    @app.post("/ingest/bars")
    def ingest_bars(
        bars: List[Bar],
        symbol: str,
        timeframe: str = "1m",
    ):
        """
        Ingest bars via REST API.
        
        Args:
            bars: List of bar objects
            symbol: Symbol (e.g., "NQ")
            timeframe: Timeframe (e.g., "1m")
        """
        if not bars:
            raise HTTPException(status_code=400, detail="No bars provided")
        
        # Convert to DataFrame
        df = pd.DataFrame([b.dict() for b in bars])
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        
        # Validate
        try:
            validate_bars_df(df)
            df = ensure_monotonic_timestamps(df)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Store
        try:
            # Parquet
            write_bars(df, symbol, timeframe)
            
            # Database
            upsert_bars(df, symbol, timeframe)
            
            return {"status": "ok", "count": len(df)}
        except Exception as e:
            logger.error(f"Failed to ingest bars: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ingest/macro")
    def ingest_macro(points: List[MacroPoint]):
        """
        Ingest macro data via REST API.
        
        Args:
            points: List of macro data points
        """
        if not points:
            raise HTTPException(status_code=400, detail="No points provided")
        
        # Convert to DataFrame
        df = pd.DataFrame([p.dict() for p in points])
        df["date"] = pd.to_datetime(df["date"]).dt.date
        
        # Store (simplified - would need proper macro storage)
        try:
            # Group by series and store
            for series_name, group in df.groupby("series"):
                group = group.set_index("date")
                from jcq.storage.parquet_store import write_macro
                write_macro(group, series_name)
            
            return {"status": "ok", "count": len(df)}
        except Exception as e:
            logger.error(f"Failed to ingest macro: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

