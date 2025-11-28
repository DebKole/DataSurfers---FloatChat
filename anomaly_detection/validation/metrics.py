"""
Validation metrics for model evaluation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    precision_score, recall_score, f1_score, roc_auc_score
)
import logging

logger = logging.getLogger(__name__)


class ValidationMetrics:
    """Compute validation metrics."""
    
    @staticmethod
    def compute_regression_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        sample_weight: np.ndarray = None
    ) -> Dict[str, float]:
        """
        Compute regression metrics.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            sample_weight: Sample weights (optional)
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # RMSE
        metrics['rmse'] = np.sqrt(mean_squared_error(
            y_true, y_pred, sample_weight=sample_weight
        ))
        
        # MAE
        metrics['mae'] = mean_absolute_error(
            y_true, y_pred, sample_weight=sample_weight
        )
        
        # Bias
        residuals = y_true - y_pred
        if sample_weight is not None:
            metrics['bias'] = np.average(residuals, weights=sample_weight)
        else:
            metrics['bias'] = np.mean(residuals)
        
        # R²
        metrics['r2'] = r2_score(
            y_true, y_pred, sample_weight=sample_weight
        )
        
        # Correlation
        metrics['correlation'] = np.corrcoef(y_true, y_pred)[0, 1]
        
        return metrics
    
    @staticmethod
    def compute_skill_score(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_baseline: np.ndarray
    ) -> float:
        """
        Compute skill score relative to baseline.
        
        SS = 1 - MSE_model / MSE_baseline
        
        Args:
            y_true: True values
            y_pred: Model predictions
            y_baseline: Baseline predictions (e.g., climatology)
            
        Returns:
            Skill score
        """
        mse_model = mean_squared_error(y_true, y_pred)
        mse_baseline = mean_squared_error(y_true, y_baseline)
        
        skill_score = 1.0 - (mse_model / (mse_baseline + 1e-10))
        
        return skill_score
    
    @staticmethod
    def compute_depth_stratified_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        depths: np.ndarray,
        depth_bins: list = None
    ) -> pd.DataFrame:
        """
        Compute metrics stratified by depth.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            depths: Depth values
            depth_bins: Depth bin edges
            
        Returns:
            DataFrame with metrics per depth bin
        """
        if depth_bins is None:
            depth_bins = [0, 200, 500, 1000, 2000, 6000]
        
        results = []
        
        for i in range(len(depth_bins) - 1):
            depth_min = depth_bins[i]
            depth_max = depth_bins[i + 1]
            
            mask = (depths >= depth_min) & (depths < depth_max)
            
            if mask.sum() == 0:
                continue
            
            metrics = ValidationMetrics.compute_regression_metrics(
                y_true[mask], y_pred[mask]
            )
            
            metrics['depth_min'] = depth_min
            metrics['depth_max'] = depth_max
            metrics['n_samples'] = mask.sum()
            
            results.append(metrics)
        
        return pd.DataFrame(results)
    
    @staticmethod
    def compute_anomaly_detection_metrics(
        y_true: np.ndarray,
        y_scores: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, float]:
        """
        Compute anomaly detection metrics.
        
        Args:
            y_true: True labels (0=normal, 1=anomaly)
            y_scores: Anomaly scores [0, 1]
            threshold: Classification threshold
            
        Returns:
            Dictionary of metrics
        """
        y_pred = (y_scores >= threshold).astype(int)
        
        metrics = {}
        
        # Precision, Recall, F1
        metrics['precision'] = precision_score(y_true, y_pred, zero_division=0)
        metrics['recall'] = recall_score(y_true, y_pred, zero_division=0)
        metrics['f1'] = f1_score(y_true, y_pred, zero_division=0)
        
        # ROC AUC
        if len(np.unique(y_true)) > 1:
            metrics['roc_auc'] = roc_auc_score(y_true, y_scores)
        else:
            metrics['roc_auc'] = np.nan
        
        # True/False Positives/Negatives
        metrics['tp'] = ((y_true == 1) & (y_pred == 1)).sum()
        metrics['fp'] = ((y_true == 0) & (y_pred == 1)).sum()
        metrics['tn'] = ((y_true == 0) & (y_pred == 0)).sum()
        metrics['fn'] = ((y_true == 1) & (y_pred == 0)).sum()
        
        # False Positive Rate
        metrics['fpr'] = metrics['fp'] / (metrics['fp'] + metrics['tn'] + 1e-10)
        
        return metrics
    
    @staticmethod
    def compute_prediction_interval_coverage(
        y_true: np.ndarray,
        y_lower: np.ndarray,
        y_upper: np.ndarray,
        nominal_coverage: float = 0.9
    ) -> Dict[str, float]:
        """
        Compute prediction interval coverage.
        
        Args:
            y_true: True values
            y_lower: Lower bound of prediction interval
            y_upper: Upper bound of prediction interval
            nominal_coverage: Nominal coverage (e.g., 0.9 for 90% PI)
            
        Returns:
            Dictionary with coverage metrics
        """
        # Check if true values fall within interval
        within_interval = (y_true >= y_lower) & (y_true <= y_upper)
        
        actual_coverage = within_interval.mean()
        
        # Interval width
        interval_width = y_upper - y_lower
        mean_width = interval_width.mean()
        
        metrics = {
            'nominal_coverage': nominal_coverage,
            'actual_coverage': actual_coverage,
            'coverage_error': actual_coverage - nominal_coverage,
            'mean_interval_width': mean_width
        }
        
        return metrics
