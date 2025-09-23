"""
Global Argo Float Data Generator
Creates synthetic Argo float data across different ocean regions for enhanced demonstration
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import random

class GlobalFloatDataGenerator:
    def __init__(self):
        """Initialize the global float data generator."""
        self.setup_ocean_regions()
        
    def setup_ocean_regions(self):
        """Setup different ocean regions with their characteristics."""
        self.ocean_regions = {
            'north_atlantic': {
                'lat_range': (40, 70),
                'lng_range': (-60, -10),
                'temp_range': (-1, 15),
                'sal_range': (32, 36),
                'description': 'North Atlantic Ocean',
                'float_count': 8
            },
            'tropical_pacific': {
                'lat_range': (-10, 10),
                'lng_range': (120, -120),
                'temp_range': (25, 30),
                'sal_range': (34, 36),
                'description': 'Tropical Pacific Ocean',
                'float_count': 12
            },
            'indian_ocean': {
                'lat_range': (-30, 20),
                'lng_range': (40, 120),
                'temp_range': (20, 29),
                'sal_range': (33, 37),
                'description': 'Indian Ocean',
                'float_count': 10
            },
            'southern_ocean': {
                'lat_range': (-60, -40),
                'lng_range': (-180, 180),
                'temp_range': (-2, 8),
                'sal_range': (33, 35),
                'description': 'Southern Ocean',
                'float_count': 6
            },
            'arctic_ocean': {
                'lat_range': (70, 85),
                'lng_range': (-180, 180),
                'temp_range': (-2, 2),
                'sal_range': (30, 34),
                'description': 'Arctic Ocean',
                'float_count': 4
            },
            'mediterranean': {
                'lat_range': (30, 45),
                'lng_range': (-5, 35),
                'temp_range': (15, 25),
                'sal_range': (36, 39),
                'description': 'Mediterranean Sea',
                'float_count': 5
            }
        }
    
    def generate_global_dataset(self) -> pd.DataFrame:
        """Generate a comprehensive global Argo float dataset."""
        all_data = []
        profile_id = 0
        
        for region_name, region_info in self.ocean_regions.items():
            region_data = self._generate_region_data(region_name, region_info, profile_id)
            all_data.extend(region_data)
            profile_id += region_info['float_count']
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        return df.sort_values(['Prof_id', 'Level']).reset_index(drop=True)
    
    def _generate_region_data(self, region_name: str, region_info: Dict, start_profile_id: int) -> List[Dict]:
        """Generate data for a specific ocean region."""
        region_data = []
        
        for i in range(region_info['float_count']):
            profile_id = start_profile_id + i
            
            # Generate random location within region
            lat = np.random.uniform(region_info['lat_range'][0], region_info['lat_range'][1])
            lng = np.random.uniform(region_info['lng_range'][0], region_info['lng_range'][1])
            
            # Handle longitude wrapping for Pacific
            if lng > 180:
                lng = lng - 360
            
            # Generate depth profile for this float
            profile_data = self._generate_depth_profile(profile_id, lat, lng, region_info)
            region_data.extend(profile_data)
        
        return region_data
    
    def _generate_depth_profile(self, profile_id: int, lat: float, lng: float, region_info: Dict) -> List[Dict]:
        """Generate a realistic depth profile for a single float."""
        # Define depth levels (0 to 2000m)
        depths = [0, 5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 
                 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
        
        profile_data = []
        
        # Surface temperature and salinity
        surface_temp = np.random.uniform(region_info['temp_range'][0], region_info['temp_range'][1])
        surface_sal = np.random.uniform(region_info['sal_range'][0], region_info['sal_range'][1])
        
        for depth in depths:
            # Calculate temperature with depth (thermocline effect)
            if depth <= 50:
                # Surface mixed layer
                temp = surface_temp + np.random.normal(0, 0.5)
            elif depth <= 200:
                # Thermocline - rapid temperature decrease
                temp_decrease = (depth - 50) / 150 * (surface_temp * 0.6)
                temp = surface_temp - temp_decrease + np.random.normal(0, 0.3)
            else:
                # Deep water - slow temperature decrease
                deep_temp = surface_temp * 0.4
                additional_decrease = (depth - 200) / 1800 * deep_temp * 0.5
                temp = deep_temp - additional_decrease + np.random.normal(0, 0.2)
            
            # Ensure temperature doesn't go below freezing point of seawater
            temp = max(temp, -1.8)
            
            # Calculate salinity with depth
            if depth <= 100:
                sal = surface_sal + np.random.normal(0, 0.1)
            elif depth <= 500:
                # Halocline
                sal = surface_sal + (depth - 100) / 400 * 0.5 + np.random.normal(0, 0.1)
            else:
                # Deep water salinity
                sal = surface_sal + 0.5 + np.random.normal(0, 0.05)
            
            # Calculate pressure (approximately 1 dbar per meter)
            pressure = depth * 1.02 + np.random.normal(0, 0.1)
            
            profile_data.append({
                'Prof_id': profile_id,
                'Level': depth,
                'TEMP': round(temp, 5),
                'PRES': round(pressure, 3),
                'SAL': round(sal, 5),
                'LAT': round(lat, 4),
                'LON': round(lng, 4)
            })
        
        return profile_data
    
    def add_bgc_parameters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add BGC (Biogeochemical) parameters for innovation features."""
        # Add pH values (typical ocean pH: 7.8-8.2)
        np.random.seed(42)
        df['PH'] = np.random.normal(8.0, 0.15, len(df))
        df['PH'] = np.clip(df['PH'], 7.5, 8.5)
        
        # Add dissolved oxygen (mg/L)
        df['OXYGEN'] = np.random.normal(6.5, 1.2, len(df))
        df['OXYGEN'] = np.clip(df['OXYGEN'], 2.0, 12.0)
        
        # Add chlorophyll fluorescence (relative units)
        df['CHLA_FLUOR'] = np.random.exponential(0.5, len(df))
        df['CHLA_FLUOR'] = np.clip(df['CHLA_FLUOR'], 0, 3.0)
        
        # Add CDOM fluorescence (relative units)
        df['CDOM_FLUOR'] = np.random.exponential(0.3, len(df))
        df['CDOM_FLUOR'] = np.clip(df['CDOM_FLUOR'], 0, 2.0)
        
        # Add nitrate concentration (μmol/kg)
        df['NITRATE'] = np.random.normal(15, 5, len(df))
        df['NITRATE'] = np.clip(df['NITRATE'], 0, 40)
        
        return df
    
    def save_enhanced_dataset(self, filename: str = "enhanced_argo_demo.csv"):
        """Generate and save the enhanced global dataset."""
        print("Generating global Argo float dataset...")
        
        # Generate base dataset
        df = self.generate_global_dataset()
        
        # Add BGC parameters
        df = self.add_bgc_parameters(df)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        
        print(f"Enhanced dataset saved to {filename}")
        print(f"Total profiles: {df['Prof_id'].nunique()}")
        print(f"Total measurements: {len(df)}")
        print(f"Depth range: {df['Level'].min()}m to {df['Level'].max()}m")
        print(f"Geographic coverage: {len(self.ocean_regions)} ocean regions")
        
        return df
    
    def get_region_summary(self, df: pd.DataFrame) -> Dict:
        """Get summary statistics by region."""
        summary = {}
        
        for region_name, region_info in self.ocean_regions.items():
            # Filter data for this region
            lat_min, lat_max = region_info['lat_range']
            lng_min, lng_max = region_info['lng_range']
            
            if lng_max < lng_min:  # Handle Pacific crossing
                region_data = df[
                    (df['LAT'] >= lat_min) & (df['LAT'] <= lat_max) &
                    ((df['LON'] >= lng_min) | (df['LON'] <= lng_max))
                ]
            else:
                region_data = df[
                    (df['LAT'] >= lat_min) & (df['LAT'] <= lat_max) &
                    (df['LON'] >= lng_min) & (df['LON'] <= lng_max)
                ]
            
            if not region_data.empty:
                summary[region_name] = {
                    'profiles': region_data['Prof_id'].nunique(),
                    'measurements': len(region_data),
                    'avg_temp': region_data['TEMP'].mean(),
                    'avg_salinity': region_data['SAL'].mean(),
                    'temp_range': f"{region_data['TEMP'].min():.1f} to {region_data['TEMP'].max():.1f}°C",
                    'depth_range': f"{region_data['Level'].min()}m to {region_data['Level'].max()}m"
                }
        
        return summary

if __name__ == "__main__":
    # Generate the enhanced global dataset
    generator = GlobalFloatDataGenerator()
    df = generator.save_enhanced_dataset()
    
    # Print region summary
    print("\n" + "="*50)
    print("REGION SUMMARY")
    print("="*50)
    
    region_summary = generator.get_region_summary(df)
    for region, stats in region_summary.items():
        print(f"\n{region.upper().replace('_', ' ')}:")
        print(f"  Profiles: {stats['profiles']}")
        print(f"  Measurements: {stats['measurements']}")
        print(f"  Avg Temperature: {stats['avg_temp']:.2f}°C")
        print(f"  Avg Salinity: {stats['avg_salinity']:.2f}")
        print(f"  Temperature Range: {stats['temp_range']}")
