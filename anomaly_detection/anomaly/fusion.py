"""
Score fusion for multi-detector anomaly detection.
"""

import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ScoreFusion:
    """Fuse scores from multiple anomaly detectors."""
    
    def __init__(self, config: Dict):
        """
        Initialize score fusion.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config.get("anomaly", {})
        self.fusion_config = self.config.get("fusion", {})
        self.detectors_config = self.config.get("detectors", {})
        
        self.method = self.fusion_config.get("method", "weighted_sum")
        self.normalize_scores = self.fusion_config.get("normalize_scores", True)
        
        # Get detector weights
        self.weights = {}
        for detector_name in ['model_residual', 'autoencoder', 'isolation_forest', 'lof']:
            detector_config = self.detectors_config.get(detector_name, {})
            if detector_config.get("enabled", False):
                self.weights[detector_name] = detector_config.get("weight", 0.0)
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v/total_weight for k, v in self.weights.items()}
        
        logger.info(f"Score fusion initialized with weights: {self.weights}")
    
    def fuse(
        self,
        scores_dict: Dict[str, np.ndarray],
        distance_weights: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Fuse anomaly scores from multiple detectors.
        
        Args:
            scores_dict: Dictionary of scores from each detector
            distance_weights: Distance-based weights for threshold adjustment
            
        Returns:
            Fused anomaly scores
        """
        if self.method == "weighted_sum":
            fused_scores = self._weighted_sum(scores_dict)
        elif self.method == "rank_aggregation":
            fused_scores = self._rank_aggregation(scores_dict)
        elif self.method == "voting":
            fused_scores = self._voting(scores_dict)
        else:
            raise ValueError(f"Unknown fusion method: {self.method}")
        
        # Apply distance-based threshold adjustment
        if distance_weights is not None:
            fused_scores = self._adjust_by_distance(fused_scores, distance_weights)
        
        return fused_scores
    
    def _weighted_sum(self, scores_dict: Dict[str, np.ndarray]) -> np.ndarray:
        """Weighted sum fusion."""
        fused = np.zeros(len(next(iter(scores_dict.values()))))
        
        for detector_name, scores in scores_dict.items():
            weight = self.weights.get(detector_name, 0.0)
            fused += weight * scores
        
        if self.normalize_scores:
            fused = np.clip(fused, 0, 1)
        
        return fused
    
    def _rank_aggregation(self, scores_dict: Dict[str, np.ndarray]) -> np.ndarray:
        """Rank aggregation fusion."""
        n_samples = len(next(iter(scores_dict.values())))
        
        # Convert scores to ranks
        rank_sum = np.zeros(n_samples)
        
        for detector_name, scores in scores_dict.items():
            weight = self.weights.get(detector_name, 0.0)
            ranks = np.argsort(np.argsort(scores))  # Rank from 0 to n-1
            rank_sum += weight * ranks
        
        # Normalize ranks to [0, 1]
        fused = rank_sum / (n_samples - 1)
        
        return fused
    
    def _voting(self, scores_dict: Dict[str, np.ndarray], threshold: float = 0.5) -> np.ndarray:
        """Voting fusion."""
        n_samples = len(next(iter(scores_dict.values())))
        
        votes = np.zeros(n_samples)
        
        for detector_name, scores in scores_dict.items():
            weight = self.weights.get(detector_name, 0.0)
            votes += weight * (scores > threshold).astype(float)
        
        # Normalize votes
        fused = votes / sum(self.weights.values())
        
        return fused
    
    def _adjust_by_distance(
        self,
        scores: np.ndarray,
        distance_weights: np.ndarray
    ) -> np.ndarray:
        """
        Adjust anomaly scores based on distance from region centroid.
        
        Points far from centroid get relaxed thresholds.
        
        Args:
            scores: Anomaly scores
            distance_weights: Distance weights [0, 1]
            
        Returns:
            Adjusted scores
        """
        distance_config = self.config.get("distance_adjustment", {})
        
        if not distance_config.get("enabled", True):
            return scores
        
        adjustment_factor = distance_config.get("adjustment_factor", 0.5)
        min_weight_threshold = distance_config.get("min_weight_threshold", 0.3)
        
        # For low-weight samples (far from centroid), reduce anomaly score
        # This makes the detector less sensitive for edge cases
        adjustment = np.ones_like(scores)
        low_weight_mask = distance_weights < min_weight_threshold
        
        if low_weight_mask.any():
            # Reduce scores for low-weight samples
            adjustment[low_weight_mask] = 1.0 - adjustment_factor * (1.0 - distance_weights[low_weight_mask])
            scores = scores * adjustment
        
        return scores
    
    def classify(
        self,
        scores: np.ndarray,
        return_level: bool = True
    ) -> np.ndarray:
        """
        Classify anomalies based on alert levels.
        
        Args:
            scores: Fused anomaly scores
            return_level: If True, return alert level; else return binary flag
            
        Returns:
            Array of classifications
        """
        alert_levels = self.config.get("alert_levels", {
            'info': 0.7,
            'warning': 0.85,
            'critical': 0.95
        })
        
        if return_level:
            classifications = np.full(len(scores), 'normal', dtype=object)
            classifications[scores >= alert_levels['info']] = 'info'
            classifications[scores >= alert_levels['warning']] = 'warning'
            classifications[scores >= alert_levels['critical']] = 'critical'
        else:
            # Binary classification
            classifications = (scores >= alert_levels['info']).astype(int)
        
        return classifications
    
    def fuse_profile_scores(
        self,
        scores_dict: Dict[str, float],
        distance_weight: float = 1.0
    ) -> Tuple[float, str]:
        """
        Fuse scores for a single profile.
        
        Args:
            scores_dict: Dictionary of detector scores
            distance_weight: Distance weight for this profile
            
        Returns:
            Tuple of (fused score, alert level)
        """
        # Weighted sum
        fused_score = 0.0
        for detector_name, score in scores_dict.items():
            weight = self.weights.get(detector_name, 0.0)
            fused_score += weight * score
        
        # Distance adjustment
        if distance_weight < 0.3:
            adjustment = 1.0 - 0.5 * (1.0 - distance_weight)
            fused_score *= adjustment
        
        # Classify
        alert_levels = self.config.get("alert_levels", {
            'info': 0.7,
            'warning': 0.85,
            'critical': 0.95
        })
        
        if fused_score >= alert_levels['critical']:
            level = 'critical'
        elif fused_score >= alert_levels['warning']:
            level = 'warning'
        elif fused_score >= alert_levels['info']:
            level = 'info'
        else:
            level = 'normal'
        
        return fused_score, level
