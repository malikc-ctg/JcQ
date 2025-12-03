-- JcQ Database Schema Migration 001
-- Creates all core tables for market data, features, models, trades, and runs

-- Market bars table
CREATE TABLE IF NOT EXISTS market_bars (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL DEFAULT '1m',
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (ts, symbol, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_ts ON market_bars(symbol, ts);

-- Features store table
CREATE TABLE IF NOT EXISTS features_store (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    features JSONB NOT NULL,
    PRIMARY KEY (ts, symbol, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_features_store_symbol_ts ON features_store(symbol, ts);

-- Model outputs table
CREATE TABLE IF NOT EXISTS model_outputs (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    prob_up DOUBLE PRECISION,
    prob_down DOUBLE PRECISION,
    expected_r DOUBLE PRECISION,
    ev_r DOUBLE PRECISION,
    meta JSONB,
    PRIMARY KEY (ts, symbol, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_model_outputs_symbol_ts ON model_outputs(symbol, ts);

-- Trade log table
CREATE TABLE IF NOT EXISTS trade_log (
    id BIGSERIAL PRIMARY KEY,
    ts_open TIMESTAMPTZ NOT NULL,
    ts_close TIMESTAMPTZ,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty INTEGER NOT NULL,
    entry_price DOUBLE PRECISION,
    exit_price DOUBLE PRECISION,
    stop_price DOUBLE PRECISION,
    target_price DOUBLE PRECISION,
    pnl DOUBLE PRECISION,
    r_mult DOUBLE PRECISION,
    fees DOUBLE PRECISION,
    slippage DOUBLE PRECISION,
    meta JSONB
);

CREATE INDEX IF NOT EXISTS idx_trade_log_symbol_ts_open ON trade_log(symbol, ts_open);

-- Simulation runs table
CREATE TABLE IF NOT EXISTS sim_runs (
    id BIGSERIAL PRIMARY KEY,
    run_time TIMESTAMPTZ DEFAULT NOW(),
    metrics JSONB NOT NULL
);

-- Macro series table
CREATE TABLE IF NOT EXISTS macro_series (
    date DATE NOT NULL,
    series TEXT NOT NULL,
    value DOUBLE PRECISION,
    PRIMARY KEY (date, series)
);

CREATE INDEX IF NOT EXISTS idx_macro_series_series_date ON macro_series(series, date);

-- Run registry table
CREATE TABLE IF NOT EXISTS run_registry (
    run_id TEXT PRIMARY KEY,
    run_type TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    meta JSONB
);

CREATE INDEX IF NOT EXISTS idx_run_registry_run_type_status ON run_registry(run_type, status);

