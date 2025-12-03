# JcQ: Quantitative Research & Trading System for NQ/MNQ Futures

## What JcQ Is

JcQ is a production-grade quantitative research, analysis, and optional execution system for NQ (E-mini Nasdaq-100) and MNQ (Micro E-mini Nasdaq-100) futures. It is designed to:

- Continuously study market data 24/5
- Ingest data from multiple sources (CSV, Parquet, REST API, live feeds)
- Compute institutional-grade features
- Train calibrated probabilistic models
- Run walk-forward validation and Monte Carlo risk simulations
- Generate and rank "best entry" candidates by expected value
- Enforce strict risk constraints
- Optionally paper-trade via a simulated broker

## What JcQ Is Not

- **Not financial advice**: This is a research tool. Past performance does not guarantee future results.
- **Not a guaranteed profit system**: All trading involves risk of loss.
- **Not production-ready for live trading without extensive testing**: Paper trade first, validate thoroughly, and understand all risks.
- **Not a replacement for professional trading infrastructure**: This is a research framework.

## ⚠️ Strong Warnings

1. **Paper trade first**: Always test with paper trading before considering live execution.
2. **Risk management is critical**: The system includes risk controls, but you must understand and configure them appropriately.
3. **Not financial advice**: This software is for educational and research purposes only.
4. **Test thoroughly**: Run walk-forward validation, Monte Carlo simulations, and extensive backtests before any live trading consideration.

## Setup

### Prerequisites

- Python 3.11 or higher
- pip or poetry for package management

### Installation

1. **Clone and navigate to the repository**:
```bash
cd jcq
```

2. **Create a virtual environment**:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env and set SUPABASE_DB_URL if using Supabase, or leave empty for SQLite fallback
```

5. **Apply database migrations**:
```bash
python scripts/apply_migrations.py
```

6. **Run the doctor script to verify setup**:
```bash
python scripts/doctor.py
```

## Running the Demo Pipeline

The demo pipeline works entirely with synthetic data and requires no paid APIs. Follow these steps:

### Step 1: Generate Demo Data

Generate 60 trading days of realistic 1-minute NQ and MNQ bars:

```bash
python scripts/generate_demo_data.py
```

This creates Parquet files in `data/bars/` and optionally inserts into the database.

### Step 2: Train a Model

Build features, create labels, and train a calibrated probabilistic model:

```bash
python scripts/train_model.py
```

The model is saved to `data/models/` and the run is recorded in the database.

### Step 3: Run a Backtest

Test the model on historical data:

```bash
python scripts/run_backtest.py
```

Results are written to `data/runs/{run_id}/trades.parquet` and metrics are printed.

### Step 4: Run Monte Carlo Simulation

Simulate many equity curves from trade results:

```bash
python scripts/run_monte_carlo.py
```

Metrics are stored in `data/runs/{run_id}/mc.json` and the database.

### Step 5: Generate Report

Create an HTML report with equity curves, drawdowns, and metrics:

```bash
python scripts/make_report.py
```

The report is saved to `data/runs/{run_id}/report.html`.

### Step 6: Run Live Loop (Analysis Mode)

Start the continuous analysis loop using synthetic data:

```bash
python scripts/run_live.py
```

This runs in analysis-only mode (no execution) by default. It prints top candidates and logs to the database.

## Ingesting Real Data

### CSV Ingestion

```bash
python scripts/ingest_csv_bars.py \
  --path /path/to/bars.csv \
  --symbol NQ \
  --timeframe 1m \
  --timezone America/New_York \
  --source my_source
```

The CSV should have columns: timestamp, open, high, low, close, volume.

### Parquet Ingestion

```bash
python scripts/ingest_parquet_bars.py \
  --path /path/to/bars.parquet \
  --symbol NQ \
  --timeframe 1m \
  --timezone America/New_York \
  --source my_source
```

### REST API Ingestion

Start the API server:

```bash
python scripts/run_api.py
```

Then POST bars to `/ingest/bars`:

```bash
curl -X POST http://localhost:8000/ingest/bars \
  -H "Content-Type: application/json" \
  -d '[{"timestamp": "2024-01-01T09:30:00Z", "open": 15000, "high": 15010, "low": 14995, "close": 15005, "volume": 1000}]'
```

### Macro Data (FRED)

If you have a FRED API key:

```bash
export FRED_API_KEY=your_key_here
python scripts/ingest_fred.py
```

This fetches Federal Reserve data series and stores them.

## Replaying Data as if Live

Use the CSV replay source to simulate live data from historical files:

```python
# In your custom script or modify run_live.py
from jcq.data.sources.csv_source import CsvReplaySource

source = CsvReplaySource(
    parquet_path="data/bars/NQ/1m/",
    speed_multiplier=1.0  # 1.0 = real-time, 10.0 = 10x speed
)
```

## Enabling Execution (Paper Trading)

**⚠️ WARNING: Only enable after extensive testing and validation.**

1. Set the environment variable:
```bash
export EXECUTION_ENABLED=true
```

2. Configure trade windows in `config/strategy.yaml`:
```yaml
trade_windows:
  - start: "09:30"
    end: "15:45"
    timezone: "America/New_York"
```

3. Run the live loop:
```bash
python scripts/run_live.py
```

The system uses `PaperBroker` which simulates bracket order execution using historical bars. All trades are logged to the database.

## Extending with Real Broker Adapters

To integrate a real broker:

1. Implement the `Broker` interface from `src/jcq/live/broker.py`
2. Add your adapter in `src/jcq/live/` (e.g., `ibkr_broker.py`)
3. Update `live_loop.py` to use your broker when `EXECUTION_ENABLED=true`

Example stubs are provided for IBKR and Tradovate in `src/jcq/data/sources/`.

## Architecture

### Core Components

- **Storage**: Supabase Postgres (with SQLite fallback) + Parquet for time-series
- **Features**: Price/volatility, VWAP, session structure, regime detection
- **Models**: Calibrated probabilistic models (LogisticRegression baseline, optional XGBoost/LightGBM)
- **Strategy**: Candidate generation, EV-based scoring, rule-based filtering
- **Risk**: Contract specs, position sizing, daily limits, open risk limits
- **Backtest**: Event-driven engine with slippage and fee simulation
- **Evaluation**: Walk-forward validation, Monte Carlo risk simulation
- **Live**: 24/5 analysis loop with optional paper execution

### Data Flow

1. **Ingestion** → Parquet + Database
2. **Feature Engineering** → Features stored in Parquet + Database
3. **Model Training** → Model artifacts in `data/models/`
4. **Candidate Generation** → Scored by EV, filtered by rules
5. **Risk Check** → Position sizing and limit enforcement
6. **Execution** (if enabled) → Paper broker simulates fills
7. **Logging** → All trades and model outputs to database

## Configuration

Configuration files are in `config/`:

- `app.yaml`: General application settings
- `market.yaml`: Market hours, sessions, instruments
- `strategy.yaml`: Candidate generation, scoring, rules
- `risk.yaml`: Risk limits, position sizing
- `model.yaml`: Model hyperparameters
- `logging.yaml`: Logging configuration

## Testing

Run the test suite:

```bash
pytest tests/
```

Tests include:
- Time/session mapping correctness
- Feature engineering validation
- Risk management logic
- Backtest engine invariants
- Walk-forward split correctness
- Monte Carlo outputs

## Observability

- **Structured logs**: JSON logs in `data/logs/`
- **Heartbeat**: `data/logs/heartbeat.txt` updated each cycle
- **Doctor script**: `python scripts/doctor.py` checks system health
- **Kill switch**: Create `data/logs/KILL` to gracefully stop the live loop

## License

See LICENSE file for details.

## Support

This is a research framework. For issues, please check:
1. The doctor script output
2. Log files in `data/logs/`
3. Database connectivity (if using Supabase)
4. Configuration file syntax

## Contributing

This is a personal research project. Contributions should maintain the production-grade standards: type hints, docstrings, tests, and safe-by-default design.

