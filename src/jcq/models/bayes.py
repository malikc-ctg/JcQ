"""Bayesian probability adjustment based on recent calibration."""

import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BayesianAdjustment:
    """Online probability shrinkage based on recent Brier scores."""
    
    def __init__(self, window: int = 100, shrinkage_factor: float = 0.1):
        """
        Initialize Bayesian adjustment.
        
        Args:
            window: Rolling window for calibration tracking
            shrinkage_factor: How much to shrink toward 0.5 (0.0 = no adjustment, 1.0 = full shrinkage)
        """
        self.window = window
        self.shrinkage_factor = shrinkage_factor
        self.recent_probs = []
        self.recent_outcomes = []
    
    def update(self, prob: float, outcome: Optional[float] = None) -> None:
        """
        Update with new prediction and (optional) outcome.
        
        Args:
            prob: Predicted probability
            outcome: Actual outcome (1.0 for up, 0.0 for down, None if unknown)
        """
        self.recent_probs.append(prob)
        if outcome is not None:
            self.recent_outcomes.append(outcome)
        
        # Keep window size
        if len(self.recent_probs) > self.window:
            self.recent_probs.pop(0)
        if len(self.recent_outcomes) > self.window:
            self.recent_outcomes.pop(0)
    
    def adjust(self, prob: float) -> tuple[float, float]:
        """
        Adjust probability based on recent calibration.
        
        Args:
            prob: Raw probability
        
        Returns:
            (adjusted_prob, confidence) tuple
        """
        if len(self.recent_outcomes) < 10:
            # Not enough data, return as-is
            return prob, 0.5
        
        # Compute Brier score on recent predictions
        recent_probs_window = self.recent_probs[-len(self.recent_outcomes):]
        brier_scores = [
            (p - o) ** 2 for p, o in zip(recent_probs_window, self.recent_outcomes)
        ]
        avg_brier = np.mean(brier_scores)
        
        # Shrink toward 0.5 if calibration is poor (high Brier score)
        # Perfect calibration: Brier = 0.25 (for balanced classes)
        # Poor calibration: Brier > 0.3
        if avg_brier > 0.3:
            shrinkage = self.shrinkage_factor * (avg_brier - 0.25) / 0.25
            adjusted_prob = prob * (1 - shrinkage) + 0.5 * shrinkage
        else:
            adjusted_prob = prob
        
        # Confidence based on calibration quality
        confidence = max(0.0, min(1.0, 1.0 - (avg_brier - 0.25) / 0.25))
        
        return adjusted_prob, confidence

