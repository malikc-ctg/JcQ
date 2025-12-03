"""Logging setup and utilities."""

import os
import logging
import logging.config
from pathlib import Path
from typing import Optional
import yaml
from jcq.core.config import get_config


def setup_logging(config_path: Optional[str] = None, log_dir: Optional[str] = None) -> None:
    """
    Set up logging from YAML config or defaults.
    
    Args:
        config_path: Path to logging.yaml (default: config/logging.yaml)
        log_dir: Directory for log files (default: data/logs)
    """
    if config_path is None:
        repo_root = Path(__file__).parent.parent.parent.parent
        config_path = repo_root / "config" / "logging.yaml"
    
    if log_dir is None:
        repo_root = Path(__file__).parent.parent.parent.parent
        log_dir = repo_root / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Update log file paths in config
    if Path(config_path).exists():
        with open(config_path, "r") as f:
            log_config = yaml.safe_load(f)
        
        # Update file handler paths
        if "handlers" in log_config:
            for handler_name, handler_config in log_config["handlers"].items():
                if "filename" in handler_config:
                    # Make path absolute
                    filename = handler_config["filename"]
                    if not Path(filename).is_absolute():
                        filename = str(Path(log_dir) / Path(filename).name)
                    handler_config["filename"] = filename
                    # Ensure directory exists
                    Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        logging.config.dictConfig(log_config)
    else:
        # Fallback to basic config
        log_level = os.getenv("LOG_LEVEL", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    
    # Override log level from environment
    env_log_level = os.getenv("LOG_LEVEL")
    if env_log_level:
        logging.getLogger().setLevel(getattr(logging, env_log_level.upper()))


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

