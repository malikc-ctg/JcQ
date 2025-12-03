"""Tests for risk management."""

import pytest
from datetime import date
from jcq.risk.contract_specs import get_contract_spec, dollars_per_point
from jcq.risk.risk_manager import RiskManager
from jcq.core.config import get_config


def test_contract_specs():
    """Test contract specifications."""
    nq_spec = get_contract_spec("NQ")
    assert nq_spec["tick_size"] == 0.25
    assert nq_spec["point_value"] == 20.0
    assert nq_spec["tick_value"] == 5.0
    
    mnq_spec = get_contract_spec("MNQ")
    assert mnq_spec["point_value"] == 2.0
    assert mnq_spec["tick_value"] == 0.5


def test_risk_manager_sizing():
    """Test position sizing."""
    config = get_config()
    cfg_risk = config.get("risk", {})
    
    manager = RiskManager(cfg_risk)
    
    candidate = {
        "entry": 15000.0,
        "stop": 14995.0,
        "risk_points": 5.0,
    }
    
    decision = manager.size_position(candidate, "NQ", date.today())
    
    # Should calculate position size
    assert "qty" in decision
    assert decision["qty"] > 0

