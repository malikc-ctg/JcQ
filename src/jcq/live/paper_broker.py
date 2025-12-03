"""Paper trading broker (simulated execution)."""

import pandas as pd
from typing import Dict, Any, List, Optional
import logging
import uuid

from jcq.live.broker import Broker
from jcq.storage.db import get_engine
from jcq.storage.schema import TradeLog
from sqlalchemy import text

logger = logging.getLogger(__name__)


class PaperBroker(Broker):
    """Simulated broker for paper trading."""
    
    def __init__(self, df_bars: Optional[pd.DataFrame] = None):
        """
        Initialize paper broker.
        
        Args:
            df_bars: DataFrame with bars for execution simulation
        """
        self.df_bars = df_bars
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        entry_price: float,
        stop_price: float,
        target_price: float,
    ) -> str:
        """Submit a bracket order (simulated)."""
        order_id = str(uuid.uuid4())
        
        self.orders[order_id] = {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "status": "pending",
        }
        
        logger.info(f"Submitted paper order {order_id}: {side} {qty} {symbol} @ {entry_price}")
        
        # Simulate immediate fill (simplified)
        # In production, would check current bar and simulate fill
        self._simulate_fill(order_id)
        
        return order_id
    
    def _simulate_fill(self, order_id: str) -> None:
        """Simulate order fill using bars."""
        order = self.orders[order_id]
        
        if self.df_bars is None or len(self.df_bars) == 0:
            # No bars, assume fill at entry price
            self._fill_order(order_id, order["entry_price"])
            return
        
        # Get latest bar
        latest_bar = self.df_bars.iloc[-1]
        
        # Check if entry is fillable
        entry = order["entry_price"]
        if order["side"] == "long":
            if latest_bar["low"] <= entry <= latest_bar["high"]:
                fill_price = max(entry, latest_bar["open"])
            else:
                fill_price = entry  # Assume fill
        else:  # short
            if latest_bar["low"] <= entry <= latest_bar["high"]:
                fill_price = min(entry, latest_bar["open"])
            else:
                fill_price = entry
        
        self._fill_order(order_id, fill_price)
    
    def _fill_order(self, order_id: str, fill_price: float) -> None:
        """Fill an order and create position."""
        order = self.orders[order_id]
        order["status"] = "filled"
        order["fill_price"] = fill_price
        
        # Create position
        pos_id = f"{order['symbol']}_{order['side']}"
        self.positions[pos_id] = {
            "symbol": order["symbol"],
            "side": order["side"],
            "qty": order["qty"],
            "entry_price": fill_price,
            "stop_price": order["stop_price"],
            "target_price": order["target_price"],
            "order_id": order_id,
        }
        
        logger.info(f"Filled order {order_id} at {fill_price}")
    
    def cancel_order(self, order_id: str) -> None:
        """Cancel an order."""
        if order_id in self.orders:
            self.orders[order_id]["status"] = "cancelled"
            logger.info(f"Cancelled order {order_id}")
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        return list(self.positions.values())
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get pending orders."""
        return [o for o in self.orders.values() if o["status"] == "pending"]
    
    def update_positions(self, current_bar: pd.Series) -> List[Dict[str, Any]]:
        """
        Update positions and check for stop/target hits.
        
        Args:
            current_bar: Current bar with OHLC
        
        Returns:
            List of closed trades
        """
        closed_trades = []
        
        for pos_id, position in list(self.positions.items()):
            side = position["side"]
            stop = position["stop_price"]
            target = position["target_price"]
            
            # Check stop
            stop_hit = False
            if side == "long" and current_bar["low"] <= stop:
                exit_price = stop
                exit_reason = "stop"
                stop_hit = True
            elif side == "short" and current_bar["high"] >= stop:
                exit_price = stop
                exit_reason = "stop"
                stop_hit = True
            
            # Check target
            target_hit = False
            if not stop_hit:
                if side == "long" and current_bar["high"] >= target:
                    exit_price = target
                    exit_reason = "target"
                    target_hit = True
                elif side == "short" and current_bar["low"] <= target:
                    exit_price = target
                    exit_reason = "target"
                    target_hit = True
            
            if stop_hit or target_hit:
                # Close position
                trade = {
                    "symbol": position["symbol"],
                    "side": side,
                    "qty": position["qty"],
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "stop_price": stop,
                    "target_price": target,
                    "exit_reason": exit_reason,
                }
                
                closed_trades.append(trade)
                del self.positions[pos_id]
                
                logger.info(f"Closed position {pos_id}: {exit_reason} @ {exit_price}")
        
        return closed_trades

