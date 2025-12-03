"""Cost calculation (slippage and fees)."""

from typing import Dict, Any
import logging

from jcq.risk.contract_specs import get_contract_spec

logger = logging.getLogger(__name__)


def calculate_costs(
    symbol: str,
    qty: int,
    cfg_risk: Dict[str, Any],
    entry: bool = True,
) -> float:
    """
    Calculate costs (slippage + fees) for a trade.
    
    Args:
        symbol: Symbol (e.g., "NQ")
        qty: Number of contracts
        cfg_risk: Risk configuration
        entry: True for entry, False for exit
    
    Returns:
        Total cost in dollars
    """
    spec = get_contract_spec(symbol)
    
    slippage_ticks = cfg_risk.get("costs", {}).get("slippage_ticks_per_side", 0.5)
    fees_per_contract = cfg_risk.get("costs", {}).get("fees_per_contract", 0.50)
    
    slippage_cost = slippage_ticks * spec["tick_value"] * qty
    fees = fees_per_contract * qty
    
    return slippage_cost + fees

