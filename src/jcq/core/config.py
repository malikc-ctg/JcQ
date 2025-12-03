"""Configuration loading and management."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache
from jcq.core.errors import ConfigurationError

_CONFIG: Optional[Dict[str, Any]] = None


def load_config(config_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Load all YAML configuration files.
    
    Args:
        config_dir: Directory containing config files (default: config/ in repo root)
    
    Returns:
        Merged configuration dictionary
    """
    if config_dir is None:
        # Assume we're in repo root or src/jcq
        repo_root = Path(__file__).parent.parent.parent.parent
        config_dir = repo_root / "config"
    
    config_dir = Path(config_dir)
    if not config_dir.exists():
        raise ConfigurationError(f"Config directory not found: {config_dir}")
    
    config_files = [
        "app.yaml",
        "market.yaml",
        "strategy.yaml",
        "risk.yaml",
        "model.yaml",
        "logging.yaml",
    ]
    
    merged = {}
    
    for config_file in config_files:
        config_path = config_dir / config_file
        if config_path.exists():
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f) or {}
                merged.update(file_config)
        else:
            raise ConfigurationError(f"Config file not found: {config_path}")
    
    # Override with environment variables
    _apply_env_overrides(merged)
    
    return merged


def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """Apply environment variable overrides to config."""
    # Database URL
    db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if db_url:
        config.setdefault("database", {})["url"] = db_url
    
    # Execution enabled
    exec_enabled = os.getenv("EXECUTION_ENABLED", "").lower() == "true"
    config.setdefault("execution", {})["enabled"] = exec_enabled
    
    # Log level
    log_level = os.getenv("LOG_LEVEL")
    if log_level:
        config.setdefault("logging", {})["level"] = log_level
        config.setdefault("app", {})["log_level"] = log_level


@lru_cache(maxsize=1)
def get_config() -> Dict[str, Any]:
    """
    Get the global configuration (cached).
    
    Returns:
        Configuration dictionary
    """
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = load_config()
    return _CONFIG


def reload_config() -> Dict[str, Any]:
    """
    Reload configuration from files (clears cache).
    
    Returns:
        Configuration dictionary
    """
    global _CONFIG
    get_config.cache_clear()
    _CONFIG = load_config()
    return _CONFIG

