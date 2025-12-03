"""Live trading loop (24/5 analysis, optional execution)."""

import time
import signal
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import logging

from jcq.core.config import get_config, reload_config
from jcq.core.logging import setup_logging, get_logger
from jcq.data.sources.demo import DemoBarsSource
from jcq.features.features import build_features
from jcq.strategy.candidates import generate_candidates
from jcq.strategy.scorer import score_candidates, rank_candidates
from jcq.strategy.rules import apply_rules
from jcq.risk.risk_manager import RiskManager
from jcq.models.prob_model import ProbModel
from jcq.live.paper_broker import PaperBroker
from jcq.live.state import LiveState
from jcq.storage.db import get_engine, ensure_schema
from jcq.storage.schema import ModelOutput
from sqlalchemy import text

logger = get_logger(__name__)


class LiveLoop:
    """Live trading loop."""
    
    def __init__(
        self,
        source,
        model: ProbModel,
        symbol: str = "NQ",
        timeframe: str = "1m",
    ):
        """
        Initialize live loop.
        
        Args:
            source: BarsSource instance
            model: Fitted ProbModel
            symbol: Symbol to trade
            timeframe: Bar timeframe
        """
        self.source = source
        self.model = model
        self.symbol = symbol
        self.timeframe = timeframe
        self.config = get_config()
        self.cfg_strategy = self.config.get("strategy", {})
        self.cfg_market = self.config.get("market", {})
        self.cfg_risk = self.config.get("risk", {})
        self.risk_manager = RiskManager(self.cfg_risk)
        self.state = LiveState()
        self.broker: Optional[PaperBroker] = None
        self.running = False
        self.df_bars = pd.DataFrame()
        self.df_features = pd.DataFrame()
        
        # Setup broker if execution enabled
        exec_enabled = self.config.get("execution", {}).get("enabled", False)
        if exec_enabled:
            self.broker = PaperBroker(self.df_bars)
            logger.warning("EXECUTION ENABLED - Paper trading mode")
        else:
            logger.info("Execution disabled - analysis only")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal, stopping...")
        self.running = False
        sys.exit(0)
    
    def _check_kill_switch(self) -> bool:
        """Check for kill switch file."""
        kill_file = Path("data/logs/KILL")
        if kill_file.exists():
            logger.warning("Kill switch detected, stopping...")
            return True
        return False
    
    def _update_heartbeat(self) -> None:
        """Update heartbeat file."""
        heartbeat_file = Path("data/logs/heartbeat.txt")
        heartbeat_file.parent.mkdir(parents=True, exist_ok=True)
        with open(heartbeat_file, "w") as f:
            f.write(f"{pd.Timestamp.now(tz='UTC').isoformat()}\n")
    
    def run(self) -> None:
        """Run the live loop."""
        logger.info(f"Starting live loop for {self.symbol} {self.timeframe}")
        self.running = True
        
        # Load initial data
        end = pd.Timestamp.now(tz="UTC")
        start = end - pd.Timedelta(days=5)
        
        try:
            self.df_bars = self.source.fetch_historical(self.symbol, self.timeframe, start, end)
            if self.df_bars.empty:
                logger.error("No bars fetched, exiting")
                return
            
            # Build features
            self.df_features = build_features(self.df_bars, self.cfg_market)
            
            logger.info(f"Loaded {len(self.df_bars)} bars and {len(self.df_features)} feature rows")
        except Exception as e:
            logger.error(f"Failed to load initial data: {e}")
            return
        
        # Main loop
        while self.running:
            try:
                if self._check_kill_switch():
                    break
                
                # Get new bars (from stream or re-fetch)
                # For demo, we'll simulate by advancing time
                # In production, would use source.stream_live()
                
                # Process latest bar
                if len(self.df_bars) > 0:
                    self._process_bar()
                
                # Update heartbeat
                self._update_heartbeat()
                
                # Sleep (1 minute for 1m bars)
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in live loop: {e}", exc_info=True)
                time.sleep(10)  # Wait before retry
        
        logger.info("Live loop stopped")
    
    def _process_bar(self) -> None:
        """Process the latest bar."""
        if self.df_features.empty:
            return
        
        latest_features = self.df_features.iloc[-1:]
        current_ts = self.df_features.index[-1]
        
        # Generate candidates
        candidates = generate_candidates(self.df_features, self.cfg_strategy, self.cfg_market)
        
        if not candidates:
            return
        
        # Score
        scored = score_candidates(candidates, self.df_features, self.model, self.cfg_strategy)
        
        if not scored:
            return
        
        # Rank
        ranked = rank_candidates(scored, top_k=1)
        
        if not ranked:
            return
        
        # Apply rules
        filtered = apply_rules(ranked, self.df_features, self.cfg_strategy, self.cfg_market, current_ts)
        
        if not filtered:
            return
        
        top_candidate = filtered[0]
        
        # Log to database
        self._log_model_output(current_ts, top_candidate)
        
        # Print top candidate
        logger.info(
            f"Top candidate: {top_candidate.get('side')} @ {top_candidate.get('entry')} "
            f"(EV_R={top_candidate.get('ev_r', 0):.2f}, P(win)={top_candidate.get('p_win', 0):.2f})"
        )
        
        # Execute if enabled
        if self.broker and top_candidate.get("ev_r", 0) > 0:
            trade_date = current_ts.date() if hasattr(current_ts, "date") else pd.Timestamp.now().date()
            risk_decision = self.risk_manager.size_position(top_candidate, self.symbol, trade_date)
            
            if risk_decision["allow"]:
                self.broker.submit_order(
                    self.symbol,
                    top_candidate["side"],
                    risk_decision["qty"],
                    top_candidate["entry"],
                    top_candidate["stop"],
                    top_candidate["target"],
                )
    
    def _log_model_output(self, ts: pd.Timestamp, candidate: Dict) -> None:
        """Log model output to database."""
        try:
            engine = get_engine()
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO model_outputs 
                        (ts, symbol, timeframe, prob_up, prob_down, expected_r, ev_r, meta)
                        VALUES (:ts, :symbol, :timeframe, :prob_up, :prob_down, :expected_r, :ev_r, :meta)
                        ON CONFLICT (ts, symbol, timeframe) DO UPDATE SET
                            prob_up = EXCLUDED.prob_up,
                            prob_down = EXCLUDED.prob_down,
                            expected_r = EXCLUDED.expected_r,
                            ev_r = EXCLUDED.ev_r,
                            meta = EXCLUDED.meta
                    """),
                    {
                        "ts": ts,
                        "symbol": self.symbol,
                        "timeframe": self.timeframe,
                        "prob_up": candidate.get("prob_up", 0.5),
                        "prob_down": candidate.get("prob_down", 0.5),
                        "expected_r": candidate.get("expected_r", 0.0),
                        "ev_r": candidate.get("ev_r", 0.0),
                        "meta": candidate.get("context", {}),
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to log model output: {e}")

