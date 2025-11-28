"""
Tests for feature engineering modules.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from features.oceanographic import OceanographicFeatures
from features.temporal import TemporalFeatures
from features.engineer import FeatureEngineer


class TestOceanographicFeatures:
    """Test oceanographic feature extraction."""
    
    def test_compute_density(self):
        """Test density computation."""
        temp = np.array([15.0, 10.0, 5.0])
        sal = np.array([35.0, 35.0, 35.0])
        pres = np.array([0, 100, 500])
        lat, lon = 30.0, -60.0
        
        density = OceanographicFeatures.compute_density(temp, sal, pres, lat, lon)
        
        assert len(density) == 3
        assert np.all(density > 1020)  # Reasonable seawater density
        assert np.all(density < 1030)
        assert density[0] < density[2]  # Density increases with depth
    
    def test_compute_mld(self):
        """Test mixed layer depth computation."""
        # Create profile with clear mixed layer
        temp = np.array([20.0, 19.9, 19.8, 15.0, 10.0, 5.0])
        sal = np.array([35.0, 35.0, 35.0, 35.0, 35.0, 35.0])
        pres = np.array([0, 10, 20, 50, 100, 200])
        lat, lon = 0.0, 0.0
        
        mld = OceanographicFeatures.compute_mld(temp, sal, pres, lat, lon)
        
        assert mld > 0
        assert mld < pres.max()
        assert 20 < mld < 60  # Should be around 50 dbar
    
    def test_compute_thermocline_depth(self):
        """Test thermocline depth computation."""
        temp = np.array([20.0, 19.0, 15.0, 10.0, 5.0, 4.0])
        pres = np.array([0, 20, 50, 100, 200, 300])
        
        therm_depth = OceanographicFeatures.compute_thermocline_depth(temp, pres)
        
        assert therm_depth > 0
        assert therm_depth < pres.max()
    
    def test_interpolate_to_standard_depths(self):
        """Test interpolation to standard depths."""
        temp = np.array([20.0, 15.0, 10.0, 5.0])
        sal = np.array([35.0, 35.2, 35.4, 35.6])
        pres = np.array([0, 50, 100, 200])
        standard_depths = [0, 25, 50, 100, 150]
        
        temp_interp, sal_interp = OceanographicFeatures.interpolate_to_standard_depths(
            temp, sal, pres, standard_depths
        )
        
        assert len(temp_interp) == len(standard_depths)
        assert len(sal_interp) == len(standard_depths)
        assert np.isclose(temp_interp[0], 20.0)  # Surface value preserved
        assert np.isclose(temp_interp[2], 15.0)  # 50m value preserved


class TestTemporalFeatures:
    """Test temporal feature extraction."""
    
    def test_encode_cyclical(self):
        """Test cyclical encoding."""
        values = np.array([0, 91.25, 182.5, 273.75])  # 0°, 90°, 180°, 270°
        period = 365.0
        
        sin_vals, cos_vals = TemporalFeatures.encode_cyclical(values, period)
        
        assert len(sin_vals) == 4
        assert len(cos_vals) == 4
        assert np.isclose(sin_vals[0], 0.0, atol=0.01)
        assert np.isclose(cos_vals[0], 1.0, atol=0.01)
    
    def test_extract_temporal_features(self):
        """Test temporal feature extraction."""
        dates = pd.Series([
            datetime(2019, 1, 15),
            datetime(2019, 6, 15),
            datetime(2019, 12, 15)
        ])
        
        features = TemporalFeatures.extract_temporal_features(dates)
        
        assert len(features) == 3
        assert 'year' in features.columns
        assert 'month' in features.columns
        assert 'doy_sin' in features.columns
        assert 'doy_cos' in features.columns
        assert 'month_sin' in features.columns
        assert 'month_cos' in features.columns
        
        # Check values
        assert features['month'].iloc[0] == 1
        assert features['month'].iloc[1] == 6
        assert features['month'].iloc[2] == 12
    
    def test_get_seasonal_weights(self):
        """Test seasonal weighting."""
        dates = pd.Series([
            datetime(2019, 1, 1),
            datetime(2019, 1, 15),
            datetime(2019, 6, 1)
        ])
        target_date = datetime(2019, 1, 10)
        
        weights = TemporalFeatures.get_seasonal_weights(dates, target_date)
        
        assert len(weights) == 3
        assert np.all(weights >= 0)
        assert np.all(weights <= 1)
        assert weights[1] > weights[0]  # Jan 15 closer than Jan 1
        assert weights[1] > weights[2]  # Jan 15 closer than Jun 1


class TestFeatureEngineer:
    """Test main feature engineering pipeline."""
    
    @pytest.fixture
    def config(self):
        """Sample configuration."""
        return {
            'features': {
                'standard_depths': [0, 50, 100, 200],
                'include_standard_depths': True
            }
        }
    
    @pytest.fixture
    def sample_profile(self):
        """Sample profile data."""
        profile_data = pd.DataFrame({
            'temperature': [20.0, 15.0, 10.0, 5.0],
            'salinity': [35.0, 35.2, 35.4, 35.6],
            'pressure': [0, 50, 100, 200]
        })
        
        profile_meta = pd.Series({
            'latitude': 30.0,
            'longitude': -60.0,
            'date': datetime(2019, 1, 15),
            'global_profile_id': 'test_001'
        })
        
        return profile_data, profile_meta
    
    def test_process_profile(self, config, sample_profile):
        """Test single profile processing."""
        engineer = FeatureEngineer(config)
        profile_data, profile_meta = sample_profile
        
        features = engineer.process_profile(profile_data, profile_meta)
        
        assert features is not None
        assert 'latitude' in features
        assert 'longitude' in features
        assert 'surface_temp' in features
        assert 'surface_sal' in features
        assert 'mld' in features
        assert 'thermocline_depth' in features
        
        # Check temporal features
        assert 'temporal_year' in features
        assert 'temporal_month' in features
        assert 'temporal_doy_sin' in features
        
        # Check standard depth features
        assert 'temp_0m' in features
        assert 'sal_0m' in features
    
    def test_get_feature_matrix(self, config, sample_profile):
        """Test feature matrix extraction."""
        engineer = FeatureEngineer(config)
        profile_data, profile_meta = sample_profile
        
        features = engineer.process_profile(profile_data, profile_meta)
        features_df = pd.DataFrame([features])
        
        X, feature_names = engineer.get_feature_matrix(features_df)
        
        assert X.shape[0] == 1
        assert X.shape[1] == len(feature_names)
        assert 'profile_id' not in feature_names
        assert 'latitude' not in feature_names
        assert 'longitude' not in feature_names


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
