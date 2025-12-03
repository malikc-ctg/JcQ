"""Contract specifications for NQ and MNQ."""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

CONTRACT_SPECS = {
    "NQ": {
        "tick_size": 0.25,
        "point_value": 20.0,  # $20 per point
        "tick_value": 5.0,   # $5 per tick
    },
    "MNQ": {
        "tick_size": 0.25,
        "point_value": 2.0,   # $2 per point
        "tick_value": 0.5,   # $0.50 per tick
    },
}


def get_contract_spec(symbol: str) -> Dict[str, Any]:
    """Get contract specifications for a symbol."""
    if symbol not in CONTRACT_SPECS:
        raise ValueError(f"Unknown symbol: {symbol}")
    return CONTRACT_SPECS[symbol].copy()


def tick_to_price(ticks: float, symbol: str) -> float:
    """Convert ticks to price."""
    spec = get_contract_spec(symbol)
    return ticks * spec["tick_size"]


def price_to_tick(price: float, symbol: str) -> float:
    """Convert price to ticks."""
    spec = get_contract_spec(symbol)
    return price / spec["tick_size"]


def dollars_per_point(symbol: str) -> float:
    """Get dollars per point for a symbol."""
    spec = get_contract_spec(symbol)
    return spec["point_value"]


def dollars_per_tick(symbol: str) -> float:
    """Get dollars per tick for a symbol."""
    spec = get_contract_spec(symbol)
    return spec["tick_value"]

