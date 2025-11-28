"""
Multi-detector anomaly detection ensemble.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class AnomalyDetectorEnsemble:
    """Ensemble of anomaly detectors."""
    
    def __init__(self, config: Dict):
        """
        Initialize detector ensemble.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config.get("anomaly", {})
        self.detectors_config = self.config.get("detectors", {})
        
        # Initialize detectors
        self.model_residual_detector = ModelResidualDetector(
            self.detectors_config.get("model_residual", {})
        )
        
        self.isolation_forest = None
        if self.detectors_config.get("isolation_forest", {}).get("enabled", True):
            iso_config = self.detectors_config.get("isolation_forest", {})
            self.isolation_forest = IsolationForest(
                contamination=iso_config.get("contamination", 0.01),
                n_estimators=iso_config.get("n_estimators", 100),
                random_state=42
            )
        
        self.lof = None
        if self.detectors_config.get("lof", {}).get("enabled", False):
            lof_config = self.detectors_config.get("lof", {})
            self.lof = LocalOutlierFactor(
                n_neighbors=lof_config.get("n_neighbors", 20),
                contamination=lof_config.get("contamination", 0.01),
                novelty=True
            )
        
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def fit(
        self,
        features: np.ndarray,
        residuals: Optional[np.ndarray] = None
    ):
        """
        Fit anomaly detectors.
        
        Args:
            features: Feature matrix for profile summaries
            residuals: Model residuals (optional)
        """
        logger.info("Fitting anomaly detectors...")
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Fit Isolation Forest
        if self.isolation_forest is not None:
            logger.info("  Fitting Isolation Forest...")
            self.isolation_forest.fit(features_scaled)
        
        # Fit LOF
        if self.lof is not None:
            logger.info("  Fitting Local Outlier Factor...")
            self.lof.fit(features_scaled)
        
        # Fit model residual detector
        if residuals is not None:
            logger.info("  Fitting Model Residual Detector...")
            self.model_residual_detector.fit(residuals)
        
        self.is_fitted = True
        logger.info("Anomaly detectors fitted successfully")
    
    def detect(
        self,
        features: np.ndarray,
        predictions: Optional[np.ndarray] = None,
        observations: Optional[np.ndarray] = None,
        weights: Optional[np.ndarray] = None
    ) -> Dict[str, np.ndarray]:
        """
        Detect anomalies using all detectors.
        
        Args:
            features: Feature matrix
            predictions: Model predictions (for residual detector)
            observations: Actual observations (for residual detector)
            weights: Distance weights (for threshold adjustment)
            
        Returns:
            Dictionary of anomaly scores from each detector
        """
        if not self.is_fitted:
            raise ValueError("Detectors not fitted. Call fit() first.")
        
        scores = {}
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Model residual detector
        if predictions is not None and observations is not None:
            residual_scores = self.model_residual_detector.detect(
                predictions, observations
            )
            scores['model_residual'] = residual_scores
        
        # Isolation Forest
        if self.isolation_forest is not None:
            iso_scores = -self.isolation_forest.score_samples(features_scaled)
            # Normalize to [0, 1]
            iso_scores = (iso_scores - iso_scores.min()) / (iso_scores.max() - iso_scores.min() + 1e-10)
            scores['isolation_forest'] = iso_scores
        
        # LOF
        if self.lof is not None:
            lof_scores = -self.lof.score_samples(features_scaled)
            # Normalize to [0, 1]
            lof_scores = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min() + 1e-10)
            scores['lof'] = lof_scores
        
        return scores
    
    def detect_profile(
        self,
        profile_data: pd.DataFrame,
        predictions: pd.DataFrame,
        profile_features: np.ndarray,
        weight: float = 1.0
    ) -> Dict:
        """
        Detect anomalies in a single profile.
        
        Args:
            profile_data: DataFrame with measurements
            predictions: DataFrame with predictions
            profile_features: Profile summary features
            weight: Distance weight for this profile
            
        Returns:
            Dictionary with anomaly scores and flags
        """
        # Compute residuals
        temp_residuals = profile_data['temperature'].values - predictions['temperature_pred'].values
        sal_residuals = profile_data['salinity'].values - predictions['salinity_pred'].values
        
        # Model residual scores
        temp_score = self.model_residual_detector.compute_profile_score(temp_residuals)
        sal_score = self.model_residual_detector.compute_profile_score(sal_residuals)
        residual_score = max(temp_score, sal_score)
        
        scores = {'model_residual': residual_score}
        
        # Isolation Forest score
        if self.isolation_forest is not None:
            features_scaled = self.scaler.transform(profile_features.reshape(1, -1))
            iso_score = -self.isolation_forest.score_samples(features_scaled)[0]
            iso_score = max(0, min(1, (iso_score + 0.5) / 1.0))  # Normalize
            scores['isolation_forest'] = iso_score
        
        # LOF score
        if self.lof is not None:
            features_scaled = self.scaler.transform(profile_features.reshape(1, -1))
            lof_score = -self.lof.score_samples(features_scaled)[0]
            lof_score = max(0, min(1, (lof_score + 2) / 4.0))  # Normalize
            scores['lof'] = lof_score
        
        return scores


class ModelResidualDetector:
    """Detect anomalies based on model residuals."""
    
    def __init__(self, config: Dict):
        """
        Initialize detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.threshold_method = config.get("threshold_method", "quantile")
        self.quantile = config.get("quantile", 0.99)
        self.zscore_threshold = config.get("zscore_threshold", 3.0)
        
        self.residual_mean = None
        self.residual_std = None
        self.residual_threshold = None
    
    def fit(self, residuals: np.ndarray):
        """
        Fit detector on training residuals.
        
        Args:
            residuals: Array of residuals
        """
        self.residual_mean = np.mean(residuals)
        self.residual_std = np.std(residuals)
        
        if self.threshold_method == "quantile":
            self.residual_threshold = np.quantile(np.abs(residuals), self.quantile)
        else:  # zscore
            self.residual_threshold = self.zscore_threshold * self.residual_std
        
        logger.info(f"Residual detector fitted: mean={self.residual_mean:.4f}, "
                   f"std={self.residual_std:.4f}, threshold={self.residual_threshold:.4f}")
    
    def detect(
        self,
        predictions: np.ndarray,
        observations: np.ndarray
    ) -> np.ndarray:
        """
        Detect anomalies based on residuals.
        
        Args:
            predictions: Predicted values
            observations: Observed values
            
        Returns:
            Array of anomaly scores [0, 1]
        """
        residuals = observations - predictions
        
        if self.threshold_method == "quantile":
            scores = np.abs(residuals) / (self.residual_threshold + 1e-10)
        else:  # zscore
            z_scores = np.abs((residuals - self.residual_mean) / (self.residual_std + 1e-10))
            scores = z_scores / self.zscore_threshold
        
        # Clip to [0, 1]
        scores = np.clip(scores, 0, 1)
        
        return scores
    
    def compute_profile_score(self, residuals: np.ndarray) -> float:
        """
        Compute anomaly score for a profile.
        
        Args:
            residuals: Array of residuals for profile
            
        Returns:
            Anomaly score [0, 1]
        """
        # Use RMS of residuals
        rms_residual = np.sqrt(np.mean(residuals**2))
        
        if self.residual_threshold is not None:
            score = rms_residual / (self.residual_threshold + 1e-10)
        else:
            # Fallback: use z-score
            score = rms_residual / (self.residual_std * self.zscore_threshold + 1e-10)
        
        return min(1.0, score)
