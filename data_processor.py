import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

class ArgoDataProcessor:
    def __init__(self, csv_path: str = "argo_demo.csv"):
        """Initialize the Argo data processor with the CSV file."""
        self.df = pd.read_csv(csv_path)
        self.setup_data()
    
    def setup_data(self):
        """Setup and preprocess the data for better querying."""
        # Add derived columns for easier querying
        self.df['depth_range'] = pd.cut(self.df['Level'], 
                                       bins=[0, 50, 100, 200, 500, 1000], 
                                       labels=['Surface (0-50m)', 'Shallow (50-100m)', 
                                              'Mid (100-200m)', 'Deep (200-500m)', 'Very Deep (500m+)'])
        
        # Temperature categories
        self.df['temp_category'] = pd.cut(self.df['TEMP'], 
                                         bins=[-2, 0, 5, 15, 25, 35], 
                                         labels=['Very Cold', 'Cold', 'Cool', 'Warm', 'Very Warm'])
        
        # Salinity categories  
        self.df['salinity_category'] = pd.cut(self.df['SAL'], 
                                             bins=[30, 32, 34, 35, 36, 38], 
                                             labels=['Low', 'Normal-Low', 'Normal', 'High-Normal', 'High'])
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the dataset."""
        return {
            'total_profiles': self.df['Prof_id'].nunique(),
            'total_measurements': len(self.df),
            'depth_range': f"{self.df['Level'].min()}m to {self.df['Level'].max()}m",
            'temperature_range': f"{self.df['TEMP'].min():.2f}°C to {self.df['TEMP'].max():.2f}°C",
            'salinity_range': f"{self.df['SAL'].min():.2f} to {self.df['SAL'].max():.2f}",
            'pressure_range': f"{self.df['PRES'].min():.2f} to {self.df['PRES'].max():.2f} dbar",
            'location': f"Latitude: {self.df['LAT'].iloc[0]:.4f}, Longitude: {self.df['LON'].iloc[0]:.4f}"
        }
    
    def query_by_depth(self, min_depth: float = None, max_depth: float = None) -> pd.DataFrame:
        """Query data by depth range."""
        if min_depth is None and max_depth is None:
            return self.df
        elif min_depth is None:
            return self.df[self.df['Level'] <= max_depth]
        elif max_depth is None:
            return self.df[self.df['Level'] >= min_depth]
        else:
            return self.df[(self.df['Level'] >= min_depth) & (self.df['Level'] <= max_depth)]
    
    def query_by_temperature(self, min_temp: float = None, max_temp: float = None) -> pd.DataFrame:
        """Query data by temperature range."""
        if min_temp is None and max_temp is None:
            return self.df
        elif min_temp is None:
            return self.df[self.df['TEMP'] <= max_temp]
        elif max_temp is None:
            return self.df[self.df['TEMP'] >= min_temp]
        else:
            return self.df[(self.df['TEMP'] >= min_temp) & (self.df['TEMP'] <= max_temp)]
    
    def query_by_salinity(self, min_sal: float = None, max_sal: float = None) -> pd.DataFrame:
        """Query data by salinity range."""
        if min_sal is None and max_sal is None:
            return self.df
        elif min_sal is None:
            return self.df[self.df['SAL'] <= max_sal]
        elif max_sal is None:
            return self.df[self.df['SAL'] >= min_sal]
        else:
            return self.df[(self.df['SAL'] >= min_sal) & (self.df['SAL'] <= max_sal)]
    
    def get_profile_summary(self, profile_id: int = None) -> Dict[str, Any]:
        """Get summary for a specific profile or all profiles."""
        if profile_id is not None:
            data = self.df[self.df['Prof_id'] == profile_id]
            if data.empty:
                return {"error": f"Profile {profile_id} not found"}
        else:
            data = self.df
        
        return {
            'profile_count': data['Prof_id'].nunique() if profile_id is None else 1,
            'depth_levels': len(data),
            'max_depth': data['Level'].max(),
            'surface_temp': data[data['Level'] == data['Level'].min()]['TEMP'].iloc[0] if not data.empty else None,
            'surface_salinity': data[data['Level'] == data['Level'].min()]['SAL'].iloc[0] if not data.empty else None,
            'avg_temperature': data['TEMP'].mean(),
            'avg_salinity': data['SAL'].mean(),
            'temperature_gradient': data['TEMP'].max() - data['TEMP'].min(),
            'salinity_gradient': data['SAL'].max() - data['SAL'].min()
        }
    
    def analyze_depth_profile(self, parameter: str = 'TEMP') -> Dict[str, Any]:
        """Analyze how a parameter changes with depth."""
        if parameter not in ['TEMP', 'SAL', 'PRES']:
            return {"error": f"Parameter {parameter} not available. Use TEMP, SAL, or PRES"}
        
        # Group by depth ranges and calculate statistics
        depth_analysis = self.df.groupby('depth_range', observed=True)[parameter].agg(['mean', 'std', 'min', 'max']).round(3)
        
        return {
            'parameter': parameter,
            'depth_analysis': depth_analysis.to_dict('index'),
            'overall_trend': self._calculate_trend(self.df['Level'], self.df[parameter])
        }
    
    def _calculate_trend(self, x, y) -> str:
        """Calculate if there's an increasing or decreasing trend."""
        correlation = np.corrcoef(x, y)[0, 1]
        if correlation > 0.3:
            return "increasing with depth"
        elif correlation < -0.3:
            return "decreasing with depth"
        else:
            return "relatively stable with depth"
    
    def find_thermocline(self) -> Dict[str, Any]:
        """Find the thermocline (rapid temperature change layer)."""
        # Calculate temperature gradient
        temp_gradient = np.gradient(self.df['TEMP'], self.df['Level'])
        
        # Find the depth with maximum temperature gradient (thermocline)
        max_gradient_idx = np.argmax(np.abs(temp_gradient))
        thermocline_depth = self.df.iloc[max_gradient_idx]['Level']
        thermocline_temp = self.df.iloc[max_gradient_idx]['TEMP']
        
        return {
            'thermocline_depth': thermocline_depth,
            'thermocline_temperature': thermocline_temp,
            'temperature_gradient': temp_gradient[max_gradient_idx],
            'description': f"Strongest temperature change occurs at {thermocline_depth}m depth"
        }
    
    def get_surface_conditions(self) -> Dict[str, Any]:
        """Get surface ocean conditions."""
        surface_data = self.df[self.df['Level'] == self.df['Level'].min()]
        
        return {
            'depth': surface_data['Level'].iloc[0],
            'temperature': surface_data['TEMP'].iloc[0],
            'salinity': surface_data['SAL'].iloc[0],
            'pressure': surface_data['PRES'].iloc[0],
            'location': {
                'latitude': surface_data['LAT'].iloc[0],
                'longitude': surface_data['LON'].iloc[0]
            }
        }
    
    def compare_profiles(self) -> Dict[str, Any]:
        """Compare different profiles if multiple exist."""
        profiles = self.df['Prof_id'].unique()
        
        if len(profiles) <= 1:
            return {"message": "Only one profile available for comparison"}
        
        comparison = {}
        for profile_id in profiles:
            profile_data = self.df[self.df['Prof_id'] == profile_id]
            comparison[f'Profile_{profile_id}'] = {
                'max_depth': profile_data['Level'].max(),
                'surface_temp': profile_data[profile_data['Level'] == profile_data['Level'].min()]['TEMP'].iloc[0],
                'surface_salinity': profile_data[profile_data['Level'] == profile_data['Level'].min()]['SAL'].iloc[0],
                'avg_temp': profile_data['TEMP'].mean(),
                'avg_salinity': profile_data['SAL'].mean()
            }
        
        return comparison