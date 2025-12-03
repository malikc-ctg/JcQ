#!/usr/bin/env python3
"""Run REST API server."""

import sys
import uvicorn
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.api.app import create_app

logger = get_logger(__name__)


def main():
    """Run API server."""
    setup_logging()
    logger.info("Starting API server...")
    
    app = create_app()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

