"""Probabilistic model wrapper with calibration."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import joblib
import logging

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score

from jcq.core.config import get_config

logger = logging.getLogger(__name__)


class ProbModel:
    """Probabilistic model with calibration."""
    
    def __init__(self, model_type: str = "logistic", config: Optional[Dict[str, Any]] = None):
        """
        Initialize model.
        
        Args:
            model_type: "logistic", "xgboost", or "lightgbm"
            config: Model configuration dict
        """
        self.model_type = model_type
        self.config = config or {}
        self.scaler = StandardScaler()
        self.model = None
        self.calibrated_model = None
        self.is_fitted = False
    
    def _create_model(self):
        """Create the underlying model."""
        if self.model_type == "logistic":
            cfg = self.config.get("logistic", {})
            self.model = LogisticRegression(
                C=cfg.get("C", 1.0),
                class_weight=cfg.get("class_weight", "balanced"),
                max_iter=cfg.get("max_iter", 1000),
                random_state=cfg.get("random_state", 42),
            )
        elif self.model_type == "xgboost":
            try:
                import xgboost as xgb
                cfg = self.config.get("xgboost", {})
                self.model = xgb.XGBClassifier(
                    n_estimators=cfg.get("n_estimators", 100),
                    max_depth=cfg.get("max_depth", 6),
                    learning_rate=cfg.get("learning_rate", 0.1),
                    subsample=cfg.get("subsample", 0.8),
                    colsample_bytree=cfg.get("colsample_bytree", 0.8),
                    random_state=cfg.get("random_state", 42),
                )
            except ImportError:
                logger.warning("XGBoost not available, falling back to logistic")
                self.model_type = "logistic"
                self._create_model()
        elif self.model_type == "lightgbm":
            try:
                import lightgbm as lgb
                cfg = self.config.get("lightgbm", {})
                self.model = lgb.LGBMClassifier(
                    n_estimators=cfg.get("n_estimators", 100),
                    max_depth=cfg.get("max_depth", 6),
                    learning_rate=cfg.get("learning_rate", 0.1),
                    subsample=cfg.get("subsample", 0.8),
                    colsample_bytree=cfg.get("colsample_bytree", 0.8),
                    random_state=cfg.get("random_state", 42),
                )
            except ImportError:
                logger.warning("LightGBM not available, falling back to logistic")
                self.model_type = "logistic"
                self._create_model()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "ProbModel":
        """
        Fit the model with calibration.
        
        Args:
            X: Feature DataFrame
            y: Target labels (0/1)
        
        Returns:
            Self
        """
        if self.model is None:
            self._create_model()
        
        # Remove NaNs
        mask = ~(X.isna().any(axis=1) | y.isna())
        X_clean = X[mask]
        y_clean = y[mask]
        
        if len(X_clean) == 0:
            raise ValueError("No valid samples after removing NaNs")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_clean)
        
        # Fit model
        self.model.fit(X_scaled, y_clean)
        
        # Calibrate
        cfg = self.config.get("calibration", {})
        self.calibrated_model = CalibratedClassifierCV(
            self.model,
            method=cfg.get("method", "isotonic"),
            cv=cfg.get("cv", 5),
        )
        self.calibrated_model.fit(X_scaled, y_clean)
        
        self.is_fitted = True
        logger.info(f"Fitted {self.model_type} model on {len(X_clean)} samples")
        
        return self
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities.
        
        Args:
            X: Feature DataFrame
        
        Returns:
            Array of shape (n_samples, 2) with [prob_down, prob_up]
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Predict
        proba = self.calibrated_model.predict_proba(X_scaled)
        
        return proba
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.model,
            "calibrated_model": self.calibrated_model,
            "scaler": self.scaler,
            "model_type": self.model_type,
            "config": self.config,
            "is_fitted": self.is_fitted,
        }, path)
        logger.info(f"Saved model to {path}")
    
    @classmethod
    def load(cls, path: str) -> "ProbModel":
        """Load model from disk."""
        data = joblib.load(path)
        model = cls(model_type=data["model_type"], config=data["config"])
        model.model = data["model"]
        model.calibrated_model = data["calibrated_model"]
        model.scaler = data["scaler"]
        model.is_fitted = data["is_fitted"]
        logger.info(f"Loaded model from {path}")
        return model

