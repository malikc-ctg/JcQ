"""Calibration utilities (re-exported for convenience)."""

from jcq.models.prob_model import ProbModel

# CalibratedProbModel is just ProbModel with calibration built-in
CalibratedProbModel = ProbModel

__all__ = ["CalibratedProbModel"]

