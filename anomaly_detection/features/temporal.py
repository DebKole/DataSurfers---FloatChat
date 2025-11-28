"""
Temporal Feature Engineering for Argo Profiles

This module provides temporal feature extraction including:
- Seasonal encoding (sin/cos)
- Year trends
- Day of year features
- Time-based aggregations
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple


class TemporalFeatures:
    """Extract temporal features from datetime information."""
    
    def __init__(self):
        """Initialize temporal feature extractor."""
        pass
    
    @staticmethod
    def encode_cyclical(values: np.ndarray, period: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Encode cyclical features using sin/cos transformation.
        
        Args:
            values: Array of values to encode
            period: Period of the cycle (e.g., 365 for day of year)
            
        Returns:
            Tuple of (sin_encoded, cos_encoded)
        """
        angle = 2 * np.pi * values / period
        return np.sin(angle), np.cos(angle)
    
    @staticmethod
    def extract_temporal_features(
        dates: pd.Series,
        reference_year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Extract comprehensive temporal features from dates.
        
        Args:
            dates: Series of datetime objects
            reference_year: Reference year for trend calculation (default: min year)
            
        Returns:
            DataFrame with temporal features
        """
        dates = pd.to_datetime(dates)
        
        if reference_year is None:
            reference_year = dates.dt.year.min()
        
        features = pd.DataFrame(index=dates.index)
        
        # Basic temporal components
        features['year'] = dates.dt.year
        features['month'] = dates.dt.month
        features['day_of_year'] = dates.dt.dayofyear
        features['day_of_month'] = dates.dt.day
        features['week_of_year'] = dates.dt.isocalendar().week
        
        # Year trend (normalized)
        features['year_trend'] = (dates.dt.year - reference_year).astype(float)
        
        # Seasonal encoding (day of year)
        doy_sin, doy_cos = TemporalFeatures.encode_cyclical(
            features['day_of_year'].values, 365.25
        )
        features['doy_sin'] = doy_sin
        features['doy_cos'] = doy_cos
        
        # Monthly seasonal encoding
        month_sin, month_cos = TemporalFeatures.encode_cyclical(
            features['month'].values, 12
        )
        features['month_sin'] = month_sin
        features['month_cos'] = month_cos
        
        # Season (meteorological)
        features['season'] = ((dates.dt.month % 12 + 3) // 3).astype(int)
        
        # Quarter
        features['quarter'] = dates.dt.quarter
        
        # Is summer/winter (Northern Hemisphere)
        features['is_summer'] = features['month'].isin([6, 7, 8]).astype(int)
        features['is_winter'] = features['month'].isin([12, 1, 2]).astype(int)
        
        return features
    
    @staticmethod
    def compute_temporal_distance(
        date1: pd.Series,
        date2: pd.Series,
        scale_days: float = 30.0
    ) -> np.ndarray:
        """
        Compute temporal distance between dates.
        
        Args:
            date1: First set of dates
            date2: Second set of dates
            scale_days: Scale parameter in days
            
        Returns:
            Array of temporal distances
        """
        date1 = pd.to_datetime(date1)
        date2 = pd.to_datetime(date2)
        
        delta_days = np.abs((date1 - date2).dt.total_seconds() / 86400)
        return delta_days / scale_days
    
    @staticmethod
    def get_seasonal_weights(
        dates: pd.Series,
        target_date: datetime,
        sigma_days: float = 45.0
    ) -> np.ndarray:
        """
        Compute Gaussian weights based on seasonal proximity.
        
        Args:
            dates: Series of dates
            target_date: Target date for weighting
            sigma_days: Standard deviation in days
            
        Returns:
            Array of weights
        """
        dates = pd.to_datetime(dates)
        target_date = pd.to_datetime(target_date)
        
        # Compute day of year for all dates
        doy = dates.dt.dayofyear.values
        target_doy = target_date.dayofyear
        
        # Handle year wrap-around (circular distance)
        delta = np.abs(doy - target_doy)
        delta = np.minimum(delta, 365 - delta)
        
        # Gaussian weighting
        weights = np.exp(-0.5 * (delta / sigma_days) ** 2)
        
        return weights
    
    @staticmethod
    def aggregate_by_season(
        df: pd.DataFrame,
        date_column: str,
        value_columns: list,
        agg_funcs: list = ['mean', 'std', 'count']
    ) -> pd.DataFrame:
        """
        Aggregate data by season.
        
        Args:
            df: Input dataframe
            date_column: Name of date column
            value_columns: Columns to aggregate
            agg_funcs: Aggregation functions
            
        Returns:
            Aggregated dataframe
        """
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        df['season'] = ((df[date_column].dt.month % 12 + 3) // 3).astype(int)
        
        agg_dict = {col: agg_funcs for col in value_columns}
        result = df.groupby('season').agg(agg_dict)
        
        return result
    
    @staticmethod
    def compute_climatology(
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        window_days: int = 15
    ) -> pd.DataFrame:
        """
        Compute climatological mean and std for each day of year.
        
        Args:
            df: Input dataframe
            date_column: Name of date column
            value_column: Column to compute climatology for
            window_days: Window size for smoothing
            
        Returns:
            DataFrame with climatology (doy, mean, std)
        """
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        df['doy'] = df[date_column].dt.dayofyear
        
        # Group by day of year
        clim = df.groupby('doy')[value_column].agg(['mean', 'std', 'count'])
        clim = clim.reset_index()
        
        # Smooth with rolling window (handle wrap-around)
        if window_days > 1:
            # Extend for wrap-around
            extended = pd.concat([
                clim.tail(window_days),
                clim,
                clim.head(window_days)
            ])
            
            # Rolling mean
            extended['mean_smooth'] = extended['mean'].rolling(
                window=window_days, center=True
            ).mean()
            extended['std_smooth'] = extended['std'].rolling(
                window=window_days, center=True
            ).mean()
            
            # Extract middle part
            clim['mean'] = extended['mean_smooth'].iloc[window_days:-window_days].values
            clim['std'] = extended['std_smooth'].iloc[window_days:-window_days].values
        
        return clim
    
    @staticmethod
    def compute_anomaly_from_climatology(
        values: np.ndarray,
        dates: pd.Series,
        climatology: pd.DataFrame
    ) -> np.ndarray:
        """
        Compute anomalies relative to climatology.
        
        Args:
            values: Array of values
            dates: Corresponding dates
            climatology: Climatology dataframe (from compute_climatology)
            
        Returns:
            Array of anomalies (standardized)
        """
        dates = pd.to_datetime(dates)
        doy = dates.dt.dayofyear.values
        
        # Create lookup dictionary
        clim_dict = climatology.set_index('doy')[['mean', 'std']].to_dict('index')
        
        anomalies = np.zeros_like(values, dtype=float)
        
        for i, (val, d) in enumerate(zip(values, doy)):
            if d in clim_dict:
                mean = clim_dict[d]['mean']
                std = clim_dict[d]['std']
                if std > 0:
                    anomalies[i] = (val - mean) / std
                else:
                    anomalies[i] = 0.0
            else:
                anomalies[i] = 0.0
        
        return anomalies


class TemporalAggregator:
    """Aggregate profiles over temporal windows."""
    
    def __init__(self, window_days: int = 30):
        """
        Initialize temporal aggregator.
        
        Args:
            window_days: Size of temporal window
        """
        self.window_days = window_days
    
    def aggregate_profiles(
        self,
        df: pd.DataFrame,
        date_column: str,
        spatial_key: str,
        value_columns: list,
        agg_funcs: Dict[str, list] = None
    ) -> pd.DataFrame:
        """
        Aggregate profiles within temporal windows.
        
        Args:
            df: Input dataframe
            date_column: Name of date column
            spatial_key: Column for spatial grouping (e.g., 'cluster_id')
            value_columns: Columns to aggregate
            agg_funcs: Dictionary mapping columns to aggregation functions
            
        Returns:
            Aggregated dataframe
        """
        if agg_funcs is None:
            agg_funcs = {col: ['mean', 'std', 'min', 'max', 'count'] 
                        for col in value_columns}
        
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.sort_values(date_column)
        
        # Create temporal bins
        df['time_bin'] = df[date_column].dt.floor(f'{self.window_days}D')
        
        # Group by spatial key and time bin
        result = df.groupby([spatial_key, 'time_bin']).agg(agg_funcs)
        result = result.reset_index()
        
        return result
    
    def compute_temporal_trends(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        spatial_key: str
    ) -> pd.DataFrame:
        """
        Compute temporal trends for each spatial region.
        
        Args:
            df: Input dataframe
            date_column: Name of date column
            value_column: Column to compute trend for
            spatial_key: Column for spatial grouping
            
        Returns:
            DataFrame with trend statistics
        """
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        df['days_since_start'] = (
            df[date_column] - df[date_column].min()
        ).dt.total_seconds() / 86400
        
        trends = []
        
        for region_id in df[spatial_key].unique():
            region_data = df[df[spatial_key] == region_id]
            
            if len(region_data) < 10:
                continue
            
            # Linear regression
            x = region_data['days_since_start'].values
            y = region_data[value_column].values
            
            # Remove NaNs
            mask = ~(np.isnan(x) | np.isnan(y))
            x = x[mask]
            y = y[mask]
            
            if len(x) < 10:
                continue
            
            # Fit linear trend
            coeffs = np.polyfit(x, y, 1)
            slope = coeffs[0]
            intercept = coeffs[1]
            
            # Compute R²
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            trends.append({
                spatial_key: region_id,
                'slope': slope,
                'intercept': intercept,
                'r2': r2,
                'n_samples': len(x),
                'mean_value': y.mean(),
                'std_value': y.std()
            })
        
        return pd.DataFrame(trends)
