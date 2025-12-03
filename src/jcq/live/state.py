"""Live loop state management."""

from typing import Dict, Any, Optional
import pandas as pd
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LiveState:
    """State manager for live loop."""
    
    def __init__(self, state_file: str = "data/logs/live_state.json"):
        """
        Initialize state manager.
        
        Args:
            state_file: Path to state file
        """
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    self.state = json.load(f)
                logger.debug(f"Loaded state from {self.state_file}")
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
                self.state = {}
        else:
            self.state = {}
    
    def save(self) -> None:
        """Save state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2, default=str)
            logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        return self.state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set state value."""
        self.state[key] = value
        self.save()
    
    def update_last_bar_time(self, timestamp: pd.Timestamp) -> None:
        """Update last processed bar time."""
        self.set("last_bar_time", timestamp.isoformat())
    
    def get_last_bar_time(self) -> Optional[pd.Timestamp]:
        """Get last processed bar time."""
        ts_str = self.get("last_bar_time")
        if ts_str:
            return pd.Timestamp(ts_str)
        return None

