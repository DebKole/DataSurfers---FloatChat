"""
Regional clustering using GMM and HDBSCAN.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, List
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import hdbscan
import logging

logger = logging.getLogger(__name__)


class RegionalClusterer:
    """Cluster ocean profiles into geographic regions."""
    
    def __init__(self, config: Dict):
        """
        Initialize clusterer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config.get("clustering", {})
        self.scaler = StandardScaler()
        self.pca = None
        self.best_model = None
        self.cluster_labels = None
        self.cluster_probs = None
        
    def prepare_features(
        self,
        features_df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features for clustering.
        
        Args:
            features_df: DataFrame with features
            feature_cols: List of feature columns to use
            
        Returns:
            Tuple of (scaled features, feature names)
        """
        if feature_cols is None:
            feature_cols = self.config.get("features_for_clustering", [
                "temp_surface", "temp_200m", "salinity_surface", "salinity_200m",
                "thermocline_depth", "mld", "density_surface",
                "latitude_scaled", "longitude_scaled"
            ])
        
        # Filter to available columns
        available_cols = [col for col in feature_cols if col in features_df.columns]
        
        if not available_cols:
            raise ValueError(f"No clustering features found in DataFrame. "
                           f"Expected: {feature_cols}")
        
        logger.info(f"Using {len(available_cols)} features for clustering: {available_cols}")
        
        # Extract features
        X = features_df[available_cols].values
        
        # Remove rows with NaN
        valid_mask = ~np.isnan(X).any(axis=1)
        X_clean = X[valid_mask]
        
        logger.info(f"Removed {(~valid_mask).sum()} rows with NaN values")
        logger.info(f"Clustering on {len(X_clean)} samples")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_clean)
        
        return X_scaled, available_cols, valid_mask
    
    def apply_pca(
        self,
        X: np.ndarray,
        n_components: Optional[int] = None
    ) -> np.ndarray:
        """
        Apply PCA dimensionality reduction.
        
        Args:
            X: Input features
            n_components: Number of components (None = from config)
            
        Returns:
            Transformed features
        """
        if n_components is None:
            n_components = self.config.get("pca", {}).get("n_components", 6)
        
        whiten = self.config.get("pca", {}).get("whiten", True)
        
        self.pca = PCA(n_components=n_components, whiten=whiten)
        X_pca = self.pca.fit_transform(X)
        
        explained_var = self.pca.explained_variance_ratio_
        cumulative_var = np.cumsum(explained_var)
        
        logger.info(f"PCA: {n_components} components explain "
                   f"{cumulative_var[-1]:.2%} of variance")
        
        for i, (var, cum_var) in enumerate(zip(explained_var, cumulative_var)):
            logger.info(f"  PC{i+1}: {var:.3f} (cumulative: {cum_var:.3f})")
        
        return X_pca
    
    def fit_gmm(
        self,
        X: np.ndarray,
        n_clusters_range: Optional[Tuple[int, int]] = None
    ) -> Tuple[GaussianMixture, Dict]:
        """
        Fit GMM with automatic cluster selection.
        
        Args:
            X: Input features
            n_clusters_range: (min, max) number of clusters
            
        Returns:
            Tuple of (best model, selection statistics)
        """
        if n_clusters_range is None:
            n_clusters_range = self.config.get("gmm", {}).get(
                "n_clusters_range", [6, 12]
            )
        
        covariance_type = self.config.get("gmm", {}).get("covariance_type", "full")
        n_init = self.config.get("gmm", {}).get("n_init", 10)
        criterion = self.config.get("gmm", {}).get("selection_criterion", "bic")
        
        logger.info(f"Fitting GMM for {n_clusters_range[0]}-{n_clusters_range[1]} clusters")
        
        results = []
        models = []
        
        for n_clusters in range(n_clusters_range[0], n_clusters_range[1] + 1):
            logger.info(f"  Fitting GMM with {n_clusters} clusters...")
            
            gmm = GaussianMixture(
                n_components=n_clusters,
                covariance_type=covariance_type,
                n_init=n_init,
                random_state=42
            )
            
            gmm.fit(X)
            
            bic = gmm.bic(X)
            aic = gmm.aic(X)
            log_likelihood = gmm.score(X) * len(X)
            
            results.append({
                'n_clusters': n_clusters,
                'bic': bic,
                'aic': aic,
                'log_likelihood': log_likelihood,
                'converged': gmm.converged_
            })
            
            models.append(gmm)
            
            logger.info(f"    BIC: {bic:.2f}, AIC: {aic:.2f}, "
                       f"LogLik: {log_likelihood:.2f}")
        
        # Select best model
        results_df = pd.DataFrame(results)
        
        if criterion == "bic":
            best_idx = results_df['bic'].idxmin()
        else:  # aic
            best_idx = results_df['aic'].idxmin()
        
        best_model = models[best_idx]
        best_n_clusters = results_df.loc[best_idx, 'n_clusters']
        
        logger.info(f"Selected {best_n_clusters} clusters based on {criterion.upper()}")
        
        stats = {
            'selection_results': results_df,
            'best_n_clusters': best_n_clusters,
            'criterion': criterion
        }
        
        return best_model, stats
    
    def fit_hdbscan(
        self,
        X: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """
        Fit HDBSCAN for outlier detection.
        
        Args:
            X: Input features
            
        Returns:
            Tuple of (cluster labels, statistics)
        """
        min_cluster_size = self.config.get("hdbscan", {}).get("min_cluster_size", 500)
        min_samples = self.config.get("hdbscan", {}).get("min_samples", 50)
        cluster_selection_epsilon = self.config.get("hdbscan", {}).get(
            "cluster_selection_epsilon", 0.5
        )
        
        logger.info("Fitting HDBSCAN for outlier detection...")
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            cluster_selection_epsilon=cluster_selection_epsilon,
            metric='euclidean'
        )
        
        labels = clusterer.fit_predict(X)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_outliers = (labels == -1).sum()
        
        logger.info(f"HDBSCAN found {n_clusters} clusters and {n_outliers} outliers "
                   f"({n_outliers/len(labels):.2%})")
        
        stats = {
            'n_clusters': n_clusters,
            'n_outliers': n_outliers,
            'outlier_rate': n_outliers / len(labels),
            'cluster_sizes': pd.Series(labels[labels != -1]).value_counts().to_dict()
        }
        
        return labels, stats
    
    def fit(
        self,
        features_df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None,
        use_pca: bool = True,
        use_hdbscan: bool = True
    ) -> Dict:
        """
        Fit clustering model.
        
        Args:
            features_df: DataFrame with features
            feature_cols: List of feature columns
            use_pca: Whether to apply PCA
            use_hdbscan: Whether to run HDBSCAN for outliers
            
        Returns:
            Dictionary with clustering results
        """
        # Prepare features
        X_scaled, feature_names, valid_mask = self.prepare_features(
            features_df, feature_cols
        )
        
        # Apply PCA if requested
        if use_pca:
            X_transformed = self.apply_pca(X_scaled)
        else:
            X_transformed = X_scaled
        
        # Fit GMM
        self.best_model, gmm_stats = self.fit_gmm(X_transformed)
        
        # Get cluster assignments and probabilities
        cluster_labels = self.best_model.predict(X_transformed)
        cluster_probs = self.best_model.predict_proba(X_transformed)
        
        # Fit HDBSCAN for outliers
        hdbscan_labels = None
        hdbscan_stats = None
        if use_hdbscan:
            hdbscan_labels, hdbscan_stats = self.fit_hdbscan(X_transformed)
        
        # Store results (map back to original indices)
        self.cluster_labels = np.full(len(features_df), -1, dtype=int)
        self.cluster_labels[valid_mask] = cluster_labels
        
        self.cluster_probs = np.zeros((len(features_df), self.best_model.n_components))
        self.cluster_probs[valid_mask] = cluster_probs
        
        # Compute cluster statistics
        cluster_stats = self._compute_cluster_stats(
            features_df, cluster_labels, valid_mask
        )
        
        results = {
            'n_clusters': self.best_model.n_components,
            'cluster_labels': self.cluster_labels,
            'cluster_probs': self.cluster_probs,
            'gmm_stats': gmm_stats,
            'hdbscan_labels': hdbscan_labels,
            'hdbscan_stats': hdbscan_stats,
            'cluster_stats': cluster_stats,
            'feature_names': feature_names,
            'valid_mask': valid_mask
        }
        
        logger.info("Clustering complete!")
        
        return results
    
    def _compute_cluster_stats(
        self,
        features_df: pd.DataFrame,
        cluster_labels: np.ndarray,
        valid_mask: np.ndarray
    ) -> pd.DataFrame:
        """Compute statistics for each cluster."""
        stats_list = []
        
        for cluster_id in range(self.best_model.n_components):
            cluster_mask = valid_mask.copy()
            cluster_mask[valid_mask] = (cluster_labels == cluster_id)
            
            cluster_data = features_df[cluster_mask]
            
            if len(cluster_data) == 0:
                continue
            
            stats = {
                'cluster_id': cluster_id,
                'n_profiles': len(cluster_data),
                'lat_mean': cluster_data['latitude'].mean(),
                'lat_std': cluster_data['latitude'].std(),
                'lon_mean': cluster_data['longitude'].mean(),
                'lon_std': cluster_data['longitude'].std(),
                'lat_min': cluster_data['latitude'].min(),
                'lat_max': cluster_data['latitude'].max(),
                'lon_min': cluster_data['longitude'].min(),
                'lon_max': cluster_data['longitude'].max(),
            }
            
            # Add feature means if available
            for col in ['temp_surface', 'salinity_surface', 'mld', 'thermocline_depth']:
                if col in cluster_data.columns:
                    stats[f'{col}_mean'] = cluster_data[col].mean()
                    stats[f'{col}_std'] = cluster_data[col].std()
            
            stats_list.append(stats)
        
        return pd.DataFrame(stats_list)
    
    def predict(
        self,
        features_df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict cluster assignments for new data.
        
        Args:
            features_df: DataFrame with features
            feature_cols: List of feature columns
            
        Returns:
            Tuple of (cluster labels, cluster probabilities)
        """
        if self.best_model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Prepare features
        X_scaled, _, valid_mask = self.prepare_features(features_df, feature_cols)
        
        # Apply PCA if it was used during training
        if self.pca is not None:
            X_transformed = self.pca.transform(X_scaled)
        else:
            X_transformed = X_scaled
        
        # Predict
        cluster_labels = np.full(len(features_df), -1, dtype=int)
        cluster_labels[valid_mask] = self.best_model.predict(X_transformed)
        
        cluster_probs = np.zeros((len(features_df), self.best_model.n_components))
        cluster_probs[valid_mask] = self.best_model.predict_proba(X_transformed)
        
        return cluster_labels, cluster_probs
    
    def save(self, filepath: str):
        """Save clusterer to file."""
        import joblib
        
        state = {
            'config': self.config,
            'scaler': self.scaler,
            'pca': self.pca,
            'best_model': self.best_model,
        }
        
        joblib.dump(state, filepath)
        logger.info(f"Clusterer saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'RegionalClusterer':
        """Load clusterer from file."""
        import joblib
        
        state = joblib.load(filepath)
        
        clusterer = cls(state['config'])
        clusterer.scaler = state['scaler']
        clusterer.pca = state['pca']
        clusterer.best_model = state['best_model']
        
        logger.info(f"Clusterer loaded from {filepath}")
        
        return clusterer
