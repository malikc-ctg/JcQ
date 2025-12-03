# JcQ Directory Tree

```
jcq/
├── config/
│   ├── app.yaml
│   ├── market.yaml
│   ├── strategy.yaml
│   ├── risk.yaml
│   ├── model.yaml
│   └── logging.yaml
├── migrations/
│   └── 001_init.sql
├── scripts/
│   ├── apply_migrations.py
│   ├── generate_demo_data.py
│   ├── ingest_csv_bars.py
│   ├── ingest_parquet_bars.py
│   ├── ingest_fred.py
│   ├── train_model.py
│   ├── tune_model.py
│   ├── run_walkforward.py (placeholder - use run_backtest.py)
│   ├── run_backtest.py
│   ├── run_monte_carlo.py
│   ├── make_report.py
│   ├── run_live.py
│   ├── run_api.py
│   └── doctor.py
├── src/
│   └── jcq/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   ├── time.py
│       │   ├── validation.py
│       │   ├── retry.py
│       │   └── errors.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── db.py
│       │   ├── schema.py
│       │   ├── parquet_store.py
│       │   └── supabase_storage.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── ingest.py
│       │   ├── demo_generator.py
│       │   ├── sources/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── demo.py
│       │   │   ├── csv_source.py
│       │   │   ├── ibkr_stub.py
│       │   │   └── tradovate_stub.py
│       │   └── macro/
│       │       ├── __init__.py
│       │       └── fred.py
│       ├── features/
│       │   ├── __init__.py
│       │   ├── sessions.py
│       │   ├── features.py
│       │   ├── regime.py
│       │   ├── internals.py
│       │   └── options_features.py
│       ├── labels/
│       │   ├── __init__.py
│       │   └── labels.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── prob_model.py
│       │   ├── calibration.py
│       │   ├── bayes.py
│       │   └── registry.py
│       ├── strategy/
│       │   ├── __init__.py
│       │   ├── candidates.py
│       │   ├── scorer.py
│       │   └── rules.py
│       ├── risk/
│       │   ├── __init__.py
│       │   ├── contract_specs.py
│       │   ├── limits.py
│       │   └── risk_manager.py
│       ├── backtest/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── execution_sim.py
│       │   └── costs.py
│       ├── eval/
│       │   ├── __init__.py
│       │   ├── walk_forward.py
│       │   ├── metrics.py
│       │   └── plots.py
│       ├── sim/
│       │   ├── __init__.py
│       │   └── monte_carlo.py
│       ├── live/
│       │   ├── __init__.py
│       │   ├── live_loop.py
│       │   ├── broker.py
│       │   ├── paper_broker.py
│       │   └── state.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── app.py
│       └── dashboard/
│           ├── __init__.py
│           └── report.py
├── tests/
│   ├── conftest.py
│   ├── test_time_sessions.py
│   ├── test_features.py
│   ├── test_labels.py (covered in test_features)
│   ├── test_risk.py
│   ├── test_candidates.py
│   ├── test_scorer_ev.py
│   ├── test_backtest_engine.py
│   ├── test_walkforward.py
│   ├── test_montecarlo.py
│   └── test_db_smoke.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── data/
│   ├── bars/
│   ├── features/
│   ├── macro/
│   ├── options/
│   ├── runs/
│   ├── models/
│   └── logs/
├── requirements.txt
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
└── LICENSE
```

## Key Components

### Configuration (config/)
- YAML configuration files for all system components
- Environment variable overrides supported

### Scripts (scripts/)
- Database migrations
- Data ingestion (CSV, Parquet, FRED)
- Model training and tuning
- Backtesting and walk-forward validation
- Monte Carlo simulation
- Report generation
- Live loop execution
- REST API server
- System health check (doctor)

### Core Modules (src/jcq/)
- **core/**: Configuration, logging, time utilities, validation, retry logic
- **storage/**: Database (Postgres/SQLite) and Parquet storage
- **data/**: Data ingestion, synthetic data generation, source interfaces
- **features/**: Feature engineering (price, volatility, VWAP, sessions, regime)
- **labels/**: Label generation for supervised learning
- **models/**: Probabilistic models with calibration
- **strategy/**: Candidate generation, EV scoring, rule-based filtering
- **risk/**: Position sizing, risk limits, contract specifications
- **backtest/**: Event-driven backtest engine with execution simulation
- **eval/**: Performance metrics, walk-forward validation
- **sim/**: Monte Carlo risk simulation
- **live/**: 24/5 live loop with paper trading
- **api/**: REST API for data ingestion
- **dashboard/**: HTML report generation with Plotly

### Tests (tests/)
- Comprehensive test suite covering all major components
- Database smoke tests (skip if DB not available)

### CI/CD (.github/workflows/)
- Automated testing on push/PR
- Python 3.11 and 3.12 support

