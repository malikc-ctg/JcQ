"""SQLAlchemy schema definitions."""

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Double,
    DateTime,
    Date,
    JSON,
    Text,
    Index,
    PrimaryKeyConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class MarketBar(Base):
    """Market bars table."""
    
    __tablename__ = "market_bars"
    
    ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    symbol = Column(Text, nullable=False, primary_key=True)
    timeframe = Column(Text, nullable=False, default="1m", primary_key=True)
    open = Column(Double, nullable=False)
    high = Column(Double, nullable=False)
    low = Column(Double, nullable=False)
    close = Column(Double, nullable=False)
    volume = Column(Double, nullable=False)
    
    __table_args__ = (
        Index("idx_market_bars_symbol_ts", "symbol", "ts"),
    )


class FeaturesStore(Base):
    """Features store table."""
    
    __tablename__ = "features_store"
    
    ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    symbol = Column(Text, nullable=False, primary_key=True)
    timeframe = Column(Text, nullable=False, primary_key=True)
    features = Column(JSON, nullable=False)
    
    __table_args__ = (
        Index("idx_features_store_symbol_ts", "symbol", "ts"),
    )


class ModelOutput(Base):
    """Model outputs table."""
    
    __tablename__ = "model_outputs"
    
    ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    symbol = Column(Text, nullable=False, primary_key=True)
    timeframe = Column(Text, nullable=False, primary_key=True)
    prob_up = Column(Double)
    prob_down = Column(Double)
    expected_r = Column(Double)
    ev_r = Column(Double)
    meta = Column(JSON)
    
    __table_args__ = (
        Index("idx_model_outputs_symbol_ts", "symbol", "ts"),
    )


class TradeLog(Base):
    """Trade log table."""
    
    __tablename__ = "trade_log"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_open = Column(DateTime(timezone=True), nullable=False)
    ts_close = Column(DateTime(timezone=True))
    symbol = Column(Text, nullable=False)
    side = Column(Text, nullable=False)  # "long" or "short"
    qty = Column(BigInteger, nullable=False)
    entry_price = Column(Double)
    exit_price = Column(Double)
    stop_price = Column(Double)
    target_price = Column(Double)
    pnl = Column(Double)
    r_mult = Column(Double)  # PnL in units of R
    fees = Column(Double)
    slippage = Column(Double)
    meta = Column(JSON)
    
    __table_args__ = (
        Index("idx_trade_log_symbol_ts_open", "symbol", "ts_open"),
    )


class SimRun(Base):
    """Simulation runs table."""
    
    __tablename__ = "sim_runs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_time = Column(DateTime(timezone=True), server_default=func.now())
    metrics = Column(JSON, nullable=False)


class MacroSeries(Base):
    """Macro series table."""
    
    __tablename__ = "macro_series"
    
    date = Column(Date, nullable=False, primary_key=True)
    series = Column(Text, nullable=False, primary_key=True)
    value = Column(Double)
    
    __table_args__ = (
        Index("idx_macro_series_series_date", "series", "date"),
    )


class RunRegistry(Base):
    """Run registry table."""
    
    __tablename__ = "run_registry"
    
    run_id = Column(Text, primary_key=True)
    run_type = Column(Text, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    status = Column(Text, nullable=False)  # "running", "completed", "failed"
    meta = Column(JSON)
    
    __table_args__ = (
        Index("idx_run_registry_run_type_status", "run_type", "status"),
    )

