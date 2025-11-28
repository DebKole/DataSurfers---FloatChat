"""
Distance-based weighting for regional model training.
"""

import numpy as np
import pandas as pd
from shapely.geometry import Point
from typing import Dict, Tuple, Optional, Callable
from scipy.spatial.distance import cdist
import logging

logger = logging.getLogger(__name__)


class DistanceWeighting:
    """Compute distance-based weights for training samples."""
    
    def __init__(self, config: Dict):
        """
        Initialize distance weighting.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config.get("geo", {}).get("distance_weights", {})
        
        # Weight function parameters
        self.method = self.config.get("method", "gaussian")
        self.gaussian_sigma_factor = self.config.get("gaussian_sigma_factor", 0.5)
        self.power_alpha = self.config.get("power_alpha", 2.0)
        self.exponential_lambda_factor = self.config.get("exponential_lambda_factor", 0.3)
        self.min_weight = self.config.get("min_weight", 0.05)
        self.normalize_per_region = self.config.get("normalize_per_region", True)
        
        # Vertical weighting
        self.use_vertical_weight = self.config.get("use_vertical_weight", False)
        self.vertical_method = self.config.get("vertical_method", "mahalanobis")
    
    def compute_horizontal_weights(
        self,
        lons: np.ndarray,
        lats: np.ndarray,
        centroid_lon: float,
        centroid_lat: float,
        max_dist_km: float
    ) -> np.ndarray:
        """
        Compute horizontal (geographic) distance weights.
        
        Args:
            lons: Array of longitudes
            lats: Array of latitudes
            centroid_lon: Region centroid longitude
            centroid_lat: Region centroid latitude
            max_dist_km: Maximum distance in region (km)
            
        Returns:
            Array of weights
        """
        # Compute distances from centroid
        distances_km = self._haversine_distance(
            lons, lats, centroid_lon, centroid_lat
        )
        
        # Compute weights based on method
        if self.method == "gaussian":
            weights = self._gaussian_weight(distances_km, max_dist_km)
        elif self.method == "power":
            weights = self._power_weight(distances_km, max_dist_km)
        elif self.method == "inverse":
            weights = self._inverse_weight(distances_km, max_dist_km)
        elif self.method == "exponential":
            weights = self._exponential_weight(distances_km, max_dist_km)
        else:
            raise ValueError(f"Unknown weighting method: {self.method}")
        
        # Apply minimum weight
        weights = np.maximum(weights, self.min_weight)
        
        return weights
    
    def _haversine_distance(
        self,
        lon1: np.ndarray,
        lat1: np.ndarray,
        lon2: float,
        lat2: float
    ) -> np.ndarray:
        """
        Compute Haversine distance between points.
        
        Args:
            lon1: Array of longitudes
            lat1: Array of latitudes
            lon2: Reference longitude
            lat2: Reference latitude
            
        Returns:
            Array of distances in km
        """
        # Convert to radians
        lon1_rad = np.radians(lon1)
        lat1_rad = np.radians(lat1)
        lon2_rad = np.radians(lon2)
        lat2_rad = np.radians(lat2)
        
        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth radius in km
        R = 6371.0
        
        return R * c
    
    def _gaussian_weight(
        self,
        distances: np.ndarray,
        max_dist: float
    ) -> np.ndarray:
        """
        Gaussian weighting: w = exp(-(d^2)/(2*sigma^2))
        
        Args:
            distances: Array of distances
            max_dist: Maximum distance for sigma calculation
            
        Returns:
            Array of weights
        """
        sigma = max_dist * self.gaussian_sigma_factor
        weights = np.exp(-(distances**2) / (2 * sigma**2))
        return weights
    
    def _power_weight(
        self,
        distances: np.ndarray,
        max_dist: float
    ) -> np.ndarray:
        """
        Power weighting: w = max(0, 1 - (d/max_dist)^alpha)
        
        Args:
            distances: Array of distances
            max_dist: Maximum distance
            
        Returns:
            Array of weights
        """
        normalized_dist = distances / max_dist
        weights = np.maximum(0, 1 - normalized_dist**self.power_alpha)
        return weights
    
    def _inverse_weight(
        self,
        distances: np.ndarray,
        max_dist: float
    ) -> np.ndarray:
        """
        Inverse distance weighting: w = 1 / (1 + d/d0)
        
        Args:
            distances: Array of distances
            max_dist: Characteristic distance scale
            
        Returns:
            Array of weights
        """
        d0 = max_dist * 0.5  # Characteristic scale
        weights = 1.0 / (1.0 + distances / d0)
        return weights
    
    def _exponential_weight(
        self,
        distances: np.ndarray,
        max_dist: float
    ) -> np.ndarray:
        """
        Exponential decay: w = exp(-d/lambda)
        
        Args:
            distances: Array of distances
            max_dist: Maximum distance for lambda calculat
ion
            
        Returns:
            Array of weights
        """
        lambda_param = max_dist * self.exponential_lambda_factor
        weights = np.exp(-distances / lambda_param)
        return weights
    
    def compute_vertical_weights(
        self,
        features: np.ndarray,
        cluster_center: np.ndarray,
        covariance: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute vertical (feature space) weights.
        
        Args:
            features: Array of feature vectors (n_samples, n_features)
            cluster_center: Cluster center in feature space
            covariance: Covariance matrix (for Mahalanobis distance)
            
        Returns:
            Array of weights
        """
        if self.vertical_method == "euclidean":
            # Euclidean distance in feature space
            distances = np.linalg.norm(features - cluster_center, axis=1)
            max_dist = np.percentile(distances, 95)
            weights = self._gaussian_weight(distances, max_dist)
            
        elif self.vertical_method == "mahalanobis":
            # Mahalanobis distance
            if covariance is None:
                # Compute covariance from data
                covariance = np.cov(features.T)
            
            try:
                inv_cov = np.linalg.inv(covariance)
                diff = features - cluster_center
                distances = np.sqrt(np.sum(diff @ inv_cov * diff, axis=1))
                max_dist = np.percentile(distances, 95)
                weights = self._gaussian_weight(distances, max_dist)
            except np.linalg.LinAlgError:
                logger.warning("Singular covariance matrix, using Euclidean distance")
                distances = np.linalg.norm(features - cluster_center, axis=1)
                max_dist = np.percentile(distances, 95)
                weights = self._gaussian_weight(distances, max_dist)
        else:
            raise ValueError(f"Unknown vertical weighting method: {self.vertical_method}")
        
        return weights
    
    def compute_combined_weights(
        self,
        lons: np.ndarray,
        lats: np.ndarray,
        centroid_lon: float,
        centroid_lat: float,
        max_dist_km: float,
        features: Optional[np.ndarray] = None,
        cluster_center: Optional[np.ndarray] = None,
        covariance: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute combined horizontal and vertical weights.
        
        Args:
            lons: Array of longitudes
            lats: Array of latitudes
            centroid_lon: Region centroid longitude
            centroid_lat: Region centroid latitude
            max_dist_km: Maximum distance in region
            features: Feature vectors (optional)
            cluster_center: Cluster center (optional)
            covariance: Covariance matrix (optional)
            
        Returns:
            Array of combined weights
        """
        # Horizontal weights
        h_weights = self.compute_horizontal_weights(
            lons, lats, centroid_lon, centroid_lat, max_dist_km
        )
        
        # Vertical weights (if requested and data available)
        if self.use_vertical_weight and features is not None and cluster_center is not None:
            v_weights = self.compute_vertical_weights(features, cluster_center, covariance)
            
            # Combine weights (multiplicative)
            weights = h_weights * v_weights
        else:
            weights = h_weights
        
        # Normalize if requested
        if self.normalize_per_region:
            weights = self._normalize_weights(weights)
        
        return weights
    
    def _normalize_weights(self, weights: np.ndarray) -> np.ndarray:
        """
        Normalize weights to mean = 1.
        
        Args:
            weights: Array of weights
            
        Returns:
            Normalized weights
        """
        mean_weight = np.mean(weights)
        if mean_weight > 0:
            weights = weights / mean_weight
        return weights
    
    def compute_weights_for_region(
        self,
        data_df: pd.DataFrame,
        region_metadata: pd.Series,
        features: Optional[np.ndarray] = None,
        cluster_center: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute weights for all samples in a region.
        
        Args:
            data_df: DataFrame with longitude, latitude columns
            region_metadata: Series with region metadata
            features: Feature matrix (optional)
            cluster_center: Cluster center (optional)
            
        Returns:
            Array of weights
        """
        lons = data_df['longitude'].values
        lats = data_df['latitude'].values
        
        centroid_lon = region_metadata['centroid_lon']
        centroid_lat = region_metadata['centroid_lat']
        max_dist_km = region_metadata['max_dist_km']
        
        weights = self.compute_combined_weights(
            lons, lats,
            centroid_lon, centroid_lat,
            max_dist_km,
            features, cluster_center
        )
        
        logger.info(f"Computed weights for {len(weights)} samples")
        logger.info(f"  Weight range: [{weights.min():.3f}, {weights.max():.3f}]")
        logger.info(f"  Weight mean: {weights.mean():.3f}")
        logger.info(f"  Weight std: {weights.std():.3f}")
        
        return weights
    
    def visualize_weights(
        self,
        lons: np.ndarray,
        lats: np.ndarray,
        weights: np.ndarray,
        centroid_lon: float,
        centroid_lat: float,
        save_path: Optional[str] = None
    ):
        """
        Visualize weight distribution.
        
        Args:
            lons: Array of longitudes
            lats: Array of latitudes
            weights: Array of weights
            centroid_lon: Centroid longitude
            centroid_lat: Centroid latitude
            save_path: Path to save figure (optional)
        """
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Spatial distribution
        scatter = ax1.scatter(
            lons, lats, c=weights,
            cmap='viridis', s=20, alpha=0.6
        )
        ax1.plot(centroid_lon, centroid_lat, 'r*', markersize=20, label='Centroid')
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')
        ax1.set_title('Spatial Weight Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax1, label='Weight')
        
        # Weight histogram
        ax2.hist(weights, bins=50, edgecolor='black', alpha=0.7)
        ax2.axvline(weights.mean(), color='r', linestyle='--', label=f'Mean: {weights.mean():.3f}')
        ax2.axvline(self.min_weight, color='g', linestyle='--', label=f'Min: {self.min_weight}')
        ax2.set_xlabel('Weight')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Weight Distribution')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Visualization saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
