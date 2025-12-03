#!/usr/bin/env python3
"""Run live loop (analysis or paper trading)."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.core.config import get_config
from jcq.data.sources.demo import DemoBarsSource
from jcq.models.prob_model import ProbModel
from jcq.live.live_loop import LiveLoop

logger = get_logger(__name__)


def main():
    """Run live loop."""
    setup_logging()
    logger.info("Starting live loop...")
    
    config = get_config()
    
    try:
        # Load model
        model_dir = Path(config.get("app", {}).get("models_dir", "data/models"))
        model_files = list(model_dir.glob("*.joblib"))
        
        if not model_files:
            logger.error("No model found. Run train_model.py first.")
            return 1
        
        model_path = model_files[-1]
        model = ProbModel.load(str(model_path))
        logger.info(f"Loaded model from {model_path}")
        
        # Create data source
        source = DemoBarsSource(seed=42)
        
        # Create live loop
        loop = LiveLoop(source, model, symbol="NQ", timeframe="1m")
        
        # Run
        loop.run()
        
        return 0
    except KeyboardInterrupt:
        logger.info("Stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Live loop failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

