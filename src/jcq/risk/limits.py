"""Risk limits and daily counters."""

from datetime import date
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RiskLimits:
    """Stateful risk limits tracker."""
    
    def __init__(self, cfg_risk: Dict):
        """
        Initialize risk limits.
        
        Args:
            cfg_risk: Risk configuration dict
        """
        self.cfg = cfg_risk
        self.daily_realized_r: Dict[date, float] = {}
        self.daily_trades: Dict[date, int] = {}
        self.open_risk_r: float = 0.0
    
    def reset_daily(self, trade_date: date) -> None:
        """Reset daily counters (call at start of each day)."""
        if trade_date not in self.daily_realized_r:
            self.daily_realized_r[trade_date] = 0.0
        if trade_date not in self.daily_trades:
            self.daily_trades[trade_date] = 0
    
    def add_realized_r(self, trade_date: date, r: float) -> None:
        """Add realized R to daily counter."""
        self.reset_daily(trade_date)
        self.daily_realized_r[trade_date] += r
    
    def add_trade(self, trade_date: date) -> None:
        """Increment daily trade count."""
        self.reset_daily(trade_date)
        self.daily_trades[trade_date] += 1
    
    def check_daily_max_r(self, trade_date: date) -> tuple[bool, Optional[str]]:
        """Check if daily max R limit would be exceeded."""
        self.reset_daily(trade_date)
        current_r = self.daily_realized_r[trade_date]
        max_r = self.cfg.get("limits", {}).get("daily_max_r", 5.0)
        
        if current_r <= -max_r:
            return False, f"Daily max R limit exceeded: {current_r:.2f} <= -{max_r}"
        return True, None
    
    def check_max_trades(self, trade_date: date) -> tuple[bool, Optional[str]]:
        """Check if max trades per day limit would be exceeded."""
        self.reset_daily(trade_date)
        current_trades = self.daily_trades[trade_date]
        max_trades = self.cfg.get("limits", {}).get("max_trades_day", 10)
        
        if current_trades >= max_trades:
            return False, f"Max trades per day limit exceeded: {current_trades} >= {max_trades}"
        return True, None
    
    def check_max_open_risk(self, additional_r: float) -> tuple[bool, Optional[str]]:
        """Check if max open risk R limit would be exceeded."""
        new_open_risk = self.open_risk_r + additional_r
        max_open = self.cfg.get("limits", {}).get("max_open_risk_r", 3.0)
        
        if new_open_risk > max_open:
            return False, f"Max open risk R limit would be exceeded: {new_open_risk:.2f} > {max_open}"
        return True, None
    
    def add_open_risk(self, r: float) -> None:
        """Add to open risk."""
        self.open_risk_r += r
    
    def remove_open_risk(self, r: float) -> None:
        """Remove from open risk."""
        self.open_risk_r = max(0.0, self.open_risk_r - abs(r))

