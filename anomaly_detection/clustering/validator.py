"""
Cluster validation metrics and visualization.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ClusterValidator:
    """Validate clustering quality."""
    
    @staticmethod
    def compute_metrics(
        X: np.ndarray,
        labels: np.ndarray,
        metric_names: Optional[list] = None
    ) -> Dict[str, float]:
        """
        Compute clustering validation metrics.
        
        Args:
            X: Feature matrix
            labels: Cluster labels
            metric_names: List of metrics to compute
            
        Returns:
            Dictionary of metric values
        """
        if metric_names is None:
            metric_names = ['silhouette', 'davies_bouldin', 'calinski_harabasz']
        
        # Filter out outliers (-1 labels)
        valid_mask = labels >= 0
        X_valid = X[valid_mask]
        labels_valid = labels[valid_mask]
        
        if len(np.unique(labels_valid)) < 2:
            logger.warning("Less than 2 clusters, cannot compute metrics")
            return {}
        
        metrics = {}
        
        if 'silhouette' in metric_names:
            try:
                metrics['silhouette'] = silhouette_score(X_valid, labels_valid)
                logger.info(f"Silhouette score: {metrics['silhouette']:.3f}")
            except Exception as e:
                logger.warning(f"Could not compute silhouette score: {e}")
        
        if 'davies_bouldin' in metric_names:
            try:
                metrics['davies_bouldin'] = davies_bouldin_score(X_valid, labels_valid)
                logger.info(f"Davies-Bouldin score: {metrics['davies_bouldin']:.3f}")
            except Exception as e:
                logger.warning(f"Could not compute Davies-Bouldin score: {e}")
        
        if 'calinski_harabasz' in metric_names:
            try:
                metrics['calinski_harabasz'] = calinski_harabasz_score(X_valid, labels_valid)
                logger.info(f"Calinski-Harabasz score: {metrics['calinski_harabasz']:.3f}")
            except Exception as e:
                logger.warning(f"Could not compute Calinski-Harabasz score: {e}")
        
        return metrics
    
    @staticmethod
    def plot_cluster_map(
        features_df: pd.DataFrame,
        cluster_labels: np.ndarray,
        save_path: Optional[str] = None
    ):
        """
        Plot clusters on a map.
        
        Args:
            features_df: DataFrame with latitude, longitude
            cluster_labels: Cluster assignments
            save_path: Path to save figure
        """
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot each cluster
        unique_labels = np.unique(cluster_labels[cluster_labels >= 0])
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))
        
        for i, label in enumerate(unique_labels):
            mask = cluster_labels == label
            cluster_data = features_df[mask]
            
            ax.scatter(
                cluster_data['longitude'],
                cluster_data['latitude'],
                c=[colors[i]],
                label=f'Cluster {label}',
                s=10,
                alpha=0.5
            )
        
        # Plot outliers if any
        outlier_mask = cluster_labels == -1
        if outlier_mask.any():
            outlier_data = features_df[outlier_mask]
            ax.scatter(
                outlier_data['longitude'],
                outlier_data['latitude'],
                c='gray',
                label='Outliers',
                s=5,
                alpha=0.3
            )
        
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title('Cluster Spatial Distribution')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Cluster map saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    @staticmethod
    def plot_ts_diagram(
        features_df: pd.DataFrame,
        cluster_labels: np.ndarray,
        save_path: Optional[str] = None
    ):
        """
        Plot T-S diagram colored by cluster.
        
        Args:
            features_df: DataFrame with temp_surface, salinity_surface
            cluster_labels: Cluster assignments
            save_path: Path to save figure
        """
        import matplotlib.pyplot as plt
        
        if 'temp_surface' not in features_df.columns or 'salinity_surface' not in features_df.columns:
            logger.warning("T-S data not available")
            return
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        unique_labels = np.unique(cluster_labels[cluster_labels >= 0])
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))
        
        for i, label in enumerate(unique_labels):
            mask = cluster_labels == label
            cluster_data = features_df[mask]
            
            ax.scatter(
                cluster_data['salinity_surface'],
                cluster_data['temp_surface'],
                c=[colors[i]],
                label=f'Cluster {label}',
                s=10,
                alpha=0.5
            )
        
        ax.set_xlabel('Salinity (PSU)')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('T-S Diagram by Cluster')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"T-S diagram saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
