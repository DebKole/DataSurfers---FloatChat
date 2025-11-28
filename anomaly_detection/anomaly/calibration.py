"""
Threshold calibration for anomaly detection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ThresholdCalibrator:
    """Calibrate anomaly detection thresholds."""
    
    def __init__(self, config: Dict):
        """
        Initialize calibrator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config.get("validation", {}).get("synthetic_anomalies", {})
        self.thresholds = {}
        
    def inject_synthetic_anomalies(
        self,
        measurements: pd.DataFrame,
        anomaly_types: List[str] = None,
        magnitudes: List[float] = None
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Inject synthetic anomalies into data.
        
        Args:
            measurements: Clean measurements
            anomaly_types: Types of anomalies to inject
            magnitudes: Anomaly magnitudes
            
        Returns:
            Tuple of (measurements with anomalies, anomaly labels)
        """
        if anomaly_types is None:
            anomaly_types = self.config.get("types", [
                "temperature_spike", "salinity_spike"
            ])
        
        if magnitudes is None:
            magnitudes = self.config.get("magnitudes", [1.0, 2.0, 3.0])
        
        logger.info(f"Injecting synthetic anomalies: {anomaly_types}")
        
        measurements_copy = measurements.copy()
        labels = np.zeros(len(measurements_copy))
        
        # Randomly select 5% of profiles for anomaly injection
        unique_profiles = measurements_copy['global_profile_id'].unique()
        n_anomalies = int(0.05 * len(unique_profiles))
        anomaly_profiles = np.random.choice(unique_profiles, n_anomalies, replace=False)
        
        for profile_id in anomaly_profiles:
            profile_mask = measurements_copy['global_profile_id'] == profile_id
            
            # Random anomaly type and magnitude
            anomaly_type = np.random.choice(anomaly_types)
            magnitude = np.random.choice(magnitudes)
            
            if anomaly_type == "temperature_spike":
                measurements_copy.loc[profile_mask, 'temperature'] += magnitude
            elif anomaly_type == "salinity_spike":
                measurements_copy.loc[profile_mask, 'salinity'] += magnitude
            
            labels[profile_mask] = 1
        
        logger.info(f"Injected {n_anomalies} anomalous profiles ({n_anomalies/len(unique_profiles):.1%})")
        
        return measurements_copy, labels
    
    def calibrate_thresholds(
        self,
        scores: np.ndarray,
        labels: np.ndarray,
        target_fpr: float = 0.01
    ) -> Dict[str, float]:
        """
        Calibrate thresholds to achieve target false positive rate.
        
        Args:
            scores: Anomaly scores
            labels: True labels (0=normal, 1=anomaly)
            target_fpr: Target false positive rate
            
        Returns:
            Dictionary with calibrated thresholds
        """
        logger.info(f"Calibrating thresholds for FPR={target_fpr}")
        
        # Sort scores
        sorted_scores = np.sort(scores[labels == 0])  # Normal samples only
        
        # Find threshold that gives target FPR
        threshold_idx = int((1 - target_fpr) * len(sorted_scores))
        threshold = sorted_scores[threshold_idx]
        
        thresholds = {
            'info': threshold * 0.7,
            'warning': threshold * 0.85,
            'critical': threshold
        }
        
        logger.info(f"Calibrated thresholds: {thresholds}")
        
        return thresholds
