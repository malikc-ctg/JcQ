"""Event-driven backtest engine."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from datetime import date

from jcq.features.features import build_features
from jcq.strategy.candidates import generate_candidates
from jcq.strategy.scorer import score_candidates, rank_candidates
from jcq.strategy.rules import apply_rules
from jcq.risk.risk_manager import RiskManager
from jcq.backtest.execution_sim import simulate_execution
from jcq.backtest.costs import calculate_costs
from jcq.core.config import get_config

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Event-driven backtest engine."""
    
    def __init__(
        self,
        model,
        cfg_strategy: Dict[str, Any],
        cfg_market: Dict[str, Any],
        cfg_risk: Dict[str, Any],
    ):
        """
        Initialize backtest engine.
        
        Args:
            model: Fitted ProbModel
            cfg_strategy: Strategy configuration
            cfg_market: Market configuration
            cfg_risk: Risk configuration
        """
        self.model = model
        self.cfg_strategy = cfg_strategy
        self.cfg_market = cfg_market
        self.cfg_risk = cfg_risk
        self.risk_manager = RiskManager(cfg_risk)
        self.trades: List[Dict[str, Any]] = []
    
    def run(
        self,
        df_bars: pd.DataFrame,
        symbol: str,
        timeframe: str = "1m",
    ) -> Dict[str, Any]:
        """
        Run backtest.
        
        Args:
            df_bars: DataFrame with bars
            symbol: Symbol (e.g., "NQ")
            timeframe: Timeframe
        
        Returns:
            Dict with trades DataFrame and metrics
        """
        if df_bars.empty:
            return {"trades": pd.DataFrame(), "metrics": {}}
        
        # Build features incrementally (no lookahead)
        df_features = build_features(df_bars, self.cfg_market)
        
        if df_features.empty:
            return {"trades": pd.DataFrame(), "metrics": {}}
        
        # Iterate through bars
        for i in range(100, len(df_features)):  # Start after feature window
            current_bar = df_features.iloc[i]
            current_ts = df_features.index[i]
            
            # Get features up to current bar (no future data)
            features_window = df_features.iloc[:i+1]
            
            # Generate candidates
            candidates = generate_candidates(features_window, self.cfg_strategy, self.cfg_market)
            
            if not candidates:
                continue
            
            # Score candidates
            scored = score_candidates(
                candidates,
                features_window,
                self.model,
                self.cfg_strategy,
            )
            
            if not scored:
                continue
            
            # Rank
            ranked = rank_candidates(scored, top_k=1)
            
            if not ranked:
                continue
            
            # Apply rules
            filtered = apply_rules(
                ranked,
                features_window,
                self.cfg_strategy,
                self.cfg_market,
                current_ts,
            )
            
            if not filtered:
                continue
            
            # Get top candidate
            candidate = filtered[0]
            
            # Risk check
            trade_date = current_ts.date() if hasattr(current_ts, "date") else date.today()
            risk_decision = self.risk_manager.size_position(candidate, symbol, trade_date)
            
            if not risk_decision["allow"]:
                continue
            
            # Simulate execution
            bars_for_exec = df_bars.reset_index() if "timestamp" in df_bars.columns else df_bars
            execution = simulate_execution(
                bars_for_exec,
                candidate["entry"],
                candidate["stop"],
                candidate["target"],
                candidate["side"],
                i,
            )
            
            if execution is None:
                continue
            
            # Calculate PnL
            qty = risk_decision["qty"]
            entry_fill = execution["entry_fill"]
            exit_fill = execution["exit_fill"]
            
            if candidate["side"] == "long":
                pnl_points = exit_fill - entry_fill
            else:
                pnl_points = entry_fill - exit_fill
            
            from jcq.risk.contract_specs import get_contract_spec
            spec = get_contract_spec(symbol)
            pnl_dollars = pnl_points * spec["point_value"] * qty
            
            # Costs
            entry_costs = calculate_costs(symbol, qty, self.cfg_risk, entry=True)
            exit_costs = calculate_costs(symbol, qty, self.cfg_risk, entry=False)
            total_costs = entry_costs + exit_costs
            
            net_pnl = pnl_dollars - total_costs
            
            # R multiple
            risk_points = candidate["risk_points"]
            r_mult = net_pnl / (risk_points * spec["point_value"] * qty) if risk_points > 0 else 0
            
            # Record trade
            exit_ts = df_bars.index[execution["exit_bar_idx"]] if execution["exit_bar_idx"] < len(df_bars.index) else current_ts
            trade = {
                "ts_open": current_ts,
                "ts_close": exit_ts,
                "symbol": symbol,
                "side": candidate["side"],
                "qty": qty,
                "entry_price": entry_fill,
                "exit_price": exit_fill,
                "stop_price": candidate["stop"],
                "target_price": candidate["target"],
                "pnl": net_pnl,
                "r_mult": r_mult,
                "fees": total_costs,
                "slippage": 0.0,  # Included in costs
                "exit_reason": execution["exit_reason"],
                "tags": candidate.get("tags", []),
            }
            
            self.trades.append(trade)
            
            # Update risk limits
            self.risk_manager.limits.add_trade(trade_date)
            self.risk_manager.limits.add_realized_r(trade_date, r_mult)
        
        # Create trades DataFrame
        df_trades = pd.DataFrame(self.trades)
        
        # Calculate metrics
        metrics = self._calculate_metrics(df_trades)
        
        logger.info(f"Backtest completed: {len(df_trades)} trades")
        
        return {
            "trades": df_trades,
            "metrics": metrics,
        }
    
    def _calculate_metrics(self, df_trades: pd.DataFrame) -> Dict[str, Any]:
        """Calculate backtest metrics."""
        if df_trades.empty:
            return {}
        
        total_r = df_trades["r_mult"].sum()
        win_rate = (df_trades["r_mult"] > 0).mean()
        avg_win_r = df_trades[df_trades["r_mult"] > 0]["r_mult"].mean() if (df_trades["r_mult"] > 0).any() else 0
        avg_loss_r = df_trades[df_trades["r_mult"] < 0]["r_mult"].mean() if (df_trades["r_mult"] < 0).any() else 0
        
        # Profit factor
        gross_profit = df_trades[df_trades["r_mult"] > 0]["r_mult"].sum()
        gross_loss = abs(df_trades[df_trades["r_mult"] < 0]["r_mult"].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        
        # Max drawdown
        equity_curve = df_trades["r_mult"].cumsum()
        running_max = equity_curve.expanding().max()
        drawdown = equity_curve - running_max
        max_drawdown = drawdown.min()
        
        # Sharpe (approximate)
        if len(df_trades) > 1:
            sharpe = df_trades["r_mult"].mean() / df_trades["r_mult"].std() * np.sqrt(252) if df_trades["r_mult"].std() > 0 else 0
        else:
            sharpe = 0
        
        return {
            "total_r": float(total_r),
            "win_rate": float(win_rate),
            "avg_win_r": float(avg_win_r),
            "avg_loss_r": float(avg_loss_r),
            "profit_factor": float(profit_factor),
            "max_drawdown": float(max_drawdown),
            "sharpe": float(sharpe),
            "num_trades": len(df_trades),
        }

