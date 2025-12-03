"""Risk manager for position sizing and limit enforcement."""

import math
from datetime import date
from typing import Dict, Any, Optional
import logging

from jcq.risk.contract_specs import get_contract_spec, dollars_per_point
from jcq.risk.limits import RiskLimits

logger = logging.getLogger(__name__)


class RiskManager:
    """Risk manager for position sizing and limit checks."""
    
    def __init__(self, cfg_risk: Dict[str, Any]):
        """
        Initialize risk manager.
        
        Args:
            cfg_risk: Risk configuration dict
        """
        self.cfg = cfg_risk
        self.limits = RiskLimits(cfg_risk)
    
    def size_position(
        self,
        candidate: Dict[str, Any],
        symbol: str,
        trade_date: date,
    ) -> Dict[str, Any]:
        """
        Size position and check all risk limits.
        
        Args:
            candidate: Candidate dict with entry, stop, risk_points
            symbol: Symbol (e.g., "NQ")
            trade_date: Trade date
        
        Returns:
            Dict with: allow (bool), reason (str), qty (int), risk_r (float), costs_estimate (float)
        """
        from datetime import date as date_type
        
        if not isinstance(trade_date, date_type):
            # Try to convert
            if hasattr(trade_date, "date"):
                trade_date = trade_date.date()
            else:
                trade_date = date.today()
        
        # Get risk points
        risk_points = candidate.get("risk_points", 0)
        if risk_points <= 0:
            return {
                "allow": False,
                "reason": "Invalid risk_points",
                "qty": 0,
                "risk_r": 0.0,
                "costs_estimate": 0.0,
            }
        
        # Get contract spec
        spec = get_contract_spec(symbol)
        dollars_per_r = self.cfg.get("position_sizing", {}).get("dollars_per_r", 100.0)
        
        # Calculate position size
        dollars_at_risk = dollars_per_r * 1.0  # 1R
        dollars_per_point = spec["point_value"]
        contracts = math.floor(dollars_at_risk / (risk_points * dollars_per_point))
        
        if contracts <= 0:
            return {
                "allow": False,
                "reason": "Position size too small (contracts <= 0)",
                "qty": 0,
                "risk_r": 0.0,
                "costs_estimate": 0.0,
            }
        
        # Prefer micro if enabled
        prefer_micro = self.cfg.get("position_sizing", {}).get("prefer_micro", True)
        if prefer_micro and symbol == "NQ":
            # Check if MNQ would work
            mnq_spec = get_contract_spec("MNQ")
            mnq_contracts = math.floor(dollars_at_risk / (risk_points * mnq_spec["point_value"]))
            if mnq_contracts >= 1:
                # Use MNQ instead
                symbol = "MNQ"
                spec = mnq_spec
                contracts = mnq_contracts
        
        # Check limits
        risk_r = 1.0  # This trade risks 1R
        
        # Daily max R
        allow, reason = self.limits.check_daily_max_r(trade_date)
        if not allow:
            return {
                "allow": False,
                "reason": reason,
                "qty": contracts,
                "risk_r": risk_r,
                "costs_estimate": 0.0,
            }
        
        # Max trades
        allow, reason = self.limits.check_max_trades(trade_date)
        if not allow:
            return {
                "allow": False,
                "reason": reason,
                "qty": contracts,
                "risk_r": risk_r,
                "costs_estimate": 0.0,
            }
        
        # Max open risk
        allow, reason = self.limits.check_max_open_risk(risk_r)
        if not allow:
            return {
                "allow": False,
                "reason": reason,
                "qty": contracts,
                "risk_r": risk_r,
                "costs_estimate": 0.0,
            }
        
        # Estimate costs
        slippage_ticks = self.cfg.get("costs", {}).get("slippage_ticks_per_side", 0.5)
        fees_per_contract = self.cfg.get("costs", {}).get("fees_per_contract", 0.50)
        round_trip = self.cfg.get("costs", {}).get("round_trip_fees", True)
        
        slippage_cost = slippage_ticks * spec["tick_value"] * contracts
        fees = fees_per_contract * contracts * (2 if round_trip else 1)
        costs_estimate = slippage_cost + fees
        
        return {
            "allow": True,
            "reason": None,
            "qty": contracts,
            "risk_r": risk_r,
            "costs_estimate": costs_estimate,
            "symbol": symbol,  # May have changed to MNQ
        }

