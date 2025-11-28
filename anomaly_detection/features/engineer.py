"""
Main Feature Engineering Pipeline

Integrates oceanographic and temporal features into a unified pipeline.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import pickle

from .oceanographic import OceanographicFeatures
from .temporal import TemporalFeatures

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Main feature engineering pipeline for Argo profiles."""
    
    def __init__(self, config: Dict):
        """
        Initialize feature engineer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.feature_config = config.get('features', {})
        self.standard_depths = self.feature_config.get(
            'standard_depths',
            [0, 10, 20, 30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500,
             600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1750, 2000]
        )
        
        self.ocean_features = OceanographicFeatures()
        self.temporal_features = TemporalFeatures()
        
        # Feature names
        self.feature_names = []
        
    def process_profile(
        self,
        profile_data: pd.DataFrame,
        profile_metadata: pd.Series
    ) -> Optional[Dict]:
        """
        Process a single profile and extract all features.
        
        Args:
            profile_data: Measurements for one profile (T, S, P)
            profile_metadata: Profile metadata (lat, lon, date, etc.)
            
        Returns:
            Dictionary of features or None if processing fails
        """
        try:
            # Sort by pressure
            profile_data = profile_data.sort_values('pressure')
            
            # Extract basic data
            temp = profile_data['temperature'].values
            sal = profile_data['salinity'].values
            pres = profile_data['pressure'].values
            lat = profile_metadata['latitude']
            lon = profile_metadata['longitude']
            date = pd.to_datetime(profile_metadata['date'])
            
            # Check minimum requirements
            if len(temp) < 5 or np.isnan(temp).sum() > len(temp) * 0.5:
                return None
            
            features = {}
            
            # ===== Metadata Features =====
            features['latitude'] = lat
            features['longitude'] = lon
            features['profile_id'] = profile_metadata.get('global_profile_id', '')
            
            # ===== Temporal Features =====
            temp_feats = self.temporal_features.extract_temporal_features(
                pd.Series([date])
            ).iloc[0]
            
            for col in temp_feats.index:
                features[f'temporal_{col}'] = temp_feats[col]
            
            # ===== Oceanographic Features =====
            
            # Density
            density = self.ocean_features.compute_density(temp, sal, pres, lat, lon)
            features['surface_density'] = density[0] if len(density) > 0 else np.nan
            features['mean_density'] = np.nanmean(density)
            
            # Spice
            spice = self.ocean_features.compute_spice(temp, sal, pres)
            features['surface_spice'] = spice[0] if len(spice) > 0 else np.nan
            features['mean_spice'] = np.nanmean(spice)
            
            # Mixed layer depth
            mld = self.ocean_features.compute_mld(temp, sal, pres, lat, lon)
            features['mld'] = mld
            
            # Thermocline depth
            therm_depth = self.ocean_features.compute_thermocline_depth(temp, pres)
            features['thermocline_depth'] = therm_depth
            
            # Buoyancy frequency
            n2 = self.ocean_features.compute_buoyancy_frequency(temp, sal, pres, lat, lon)
            features['max_n2'] = np.nanmax(n2) if len(n2) > 0 else np.nan
            features['mean_n2'] = np.nanmean(n2)
            
            # Vertical gradients
            dt_dz, ds_dz = self.ocean_features.compute_vertical_gradients(temp, sal, pres)
            features['max_dt_dz'] = np.nanmax(np.abs(dt_dz)) if len(dt_dz) > 0 else np.nan
            features['max_ds_dz'] = np.nanmax(np.abs(ds_dz)) if len(ds_dz) > 0 else np.nan
            
            # Profile statistics
            features['max_pressure'] = pres.max()
            features['n_levels'] = len(pres)
            features['temp_range'] = temp.max() - temp.min()
            features['sal_range'] = sal.max() - sal.min()
            
            # Surface values
            features['surface_temp'] = temp[0]
            features['surface_sal'] = sal[0]
            
            # ===== Interpolated Standard Depths =====
            if self.feature_config.get('include_standard_depths', True):
                temp_interp, sal_interp = self.ocean_features.interpolate_to_standard_depths(
                    temp, sal, pres, self.standard_depths
                )
                
                for i, depth in enumerate(self.standard_depths):
                    if i < len(temp_interp):
                        features[f'temp_{depth}m'] = temp_interp[i]
                        features[f'sal_{depth}m'] = sal_interp[i]
            
            return features
            
        except Exception as e:
            logger.warning(f"Error processing profile: {e}")
            return None
    
    def process_profiles_batch(
        self,
        profiles_df: pd.DataFrame,
        measurements_df: pd.DataFrame,
        profile_id_col: str = 'global_profile_id'
    ) -> pd.DataFrame:
        """
        Process multiple profiles in batch.
        
        Args:
            profiles_df: DataFrame with profile metadata
            measurements_df: DataFrame with measurements
            profile_id_col: Column name for profile ID
            
        Returns:
            DataFrame with extracted features
        """
        logger.info(f"Processing {len(profiles_df)} profiles...")
        
        all_features = []
        
        for idx, profile_meta in profiles_df.iterrows():
            profile_id = profile_meta[profile_id_col]
            
            # Get measurements for this profile
            profile_data = measurements_df[
                measurements_df[profile_id_col] == profile_id
            ]
            
            if len(profile_data) == 0:
                continue
            
            # Extract features
            features = self.process_profile(profile_data, profile_meta)
            
            if features is not None:
                all_features.append(features)
            
            if (len(all_features) % 1000) == 0:
                logger.info(f"Processed {len(all_features)} profiles...")
        
        logger.info(f"Successfully processed {len(all_features)} profiles")
        
        # Convert to DataFrame
        features_df = pd.DataFrame(all_features)
        
        # Store feature names
        self.feature_names = [col for col in features_df.columns 
                             if col not in ['profile_id', 'latitude', 'longitude']]
        
        return features_df
    
    def get_feature_matrix(
        self,
        features_df: pd.DataFrame,
        exclude_cols: List[str] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Get feature matrix for modeling.
        
        Args:
            features_df: DataFrame with features
            exclude_cols: Columns to exclude
            
        Returns:
            Tuple of (feature_matrix, feature_names)
        """
        if exclude_cols is None:
            exclude_cols = ['profile_id', 'latitude', 'longitude']
        
        # Select numeric columns
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        # Extract matrix
        X = features_df[feature_cols].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        return X, feature_cols
    
    def save_features(
        self,
        features_df: pd.DataFrame,
        output_path: str
    ):
        """
        Save features to file.
        
        Args:
            features_df: DataFrame with features
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix == '.parquet':
            features_df.to_parquet(output_path, index=False)
        elif output_path.suffix == '.csv':
            features_df.to_csv(output_path, index=False)
        else:
            # Default to pickle
            with open(output_path, 'wb') as f:
                pickle.dump(features_df, f)
        
        logger.info(f"Saved features to {output_path}")
    
    def load_features(self, input_path: str) -> pd.DataFrame:
        """
        Load features from file.
        
        Args:
            input_path: Input file path
            
        Returns:
            DataFrame with features
        """
        input_path = Path(input_path)
        
        if input_path.suffix == '.parquet':
            features_df = pd.read_parquet(input_path)
        elif input_path.suffix == '.csv':
            features_df = pd.read_csv(input_path)
        else:
            with open(input_path, 'rb') as f:
                features_df = pickle.load(f)
        
        logger.info(f"Loaded features from {input_path}")
        return features_df
    
    def compute_feature_importance_stats(
        self,
        features_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute basic statistics for feature importance analysis.
        
        Args:
            features_df: DataFrame with features
            
        Returns:
            DataFrame with feature statistics
        """
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        
        stats = []
        for col in numeric_cols:
            if col in ['profile_id', 'latitude', 'longitude']:
                continue
            
            values = features_df[col].values
            values = values[~np.isnan(values)]
            
            if len(values) == 0:
                continue
            
            stats.append({
                'feature': col,
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'missing_rate': np.isnan(features_df[col]).sum() / len(features_df),
                'unique_values': len(np.unique(values))
            })
        
        return pd.DataFrame(stats).sort_values('std', ascending=False)


def create_feature_pipeline(config: Dict) -> FeatureEngineer:
    """
    Factory function to create feature engineering pipeline.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        FeatureEngineer instance
    """
    return FeatureEngineer(config)
