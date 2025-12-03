"""Broker interface."""

from typing import Protocol, Dict, Any, Optional


class Broker(Protocol):
    """Protocol for broker implementations."""
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        entry_price: float,
        stop_price: float,
        target_price: float,
    ) -> str:
        """
        Submit a bracket order.
        
        Args:
            symbol: Symbol (e.g., "NQ")
            side: "long" or "short"
            qty: Number of contracts
            entry_price: Entry price
            stop_price: Stop loss price
            target_price: Profit target price
        
        Returns:
            Order ID
        """
        ...
    
    def cancel_order(self, order_id: str) -> None:
        """Cancel an order."""
        ...
    
    def get_positions(self) -> list[Dict[str, Any]]:
        """Get current positions."""
        ...
    
    def get_orders(self) -> list[Dict[str, Any]]:
        """Get pending orders."""
        ...

