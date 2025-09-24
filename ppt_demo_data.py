"""
Demo data generator for PPT visualization with realistic global Argo float distribution
"""

import json
import numpy as np
from typing import List, Dict, Any

class PPTDemoDataGenerator:
    def __init__(self):
        self.setup_realistic_locations()
    
    def setup_realistic_locations(self):
        """Setup realistic Argo float locations based on actual deployment patterns"""
        # Major ocean basins with realistic Argo float concentrations
        self.ocean_regions = {
            'north_atlantic': {
                'center': [45, -30],
                'spread': [15, 25],
                'float_count': 12,
                'temp_range': [8, 18],
                'sal_range': [34.5, 36.2]
            },
            'south_atlantic': {
                'center': [-25, -15],
                'spread': [20, 20],
                'float_count': 8,
                'temp_range': [15, 25],
                'sal_range': [34.8, 36.5]
            },
            'north_pacific': {
                'center': [35, -150],
                'spread': [25, 40],
                'float_count': 15,
                'temp_range': [5, 20],
                'sal_range': [33.5, 35.0]
            },
            'south_pacific': {
                'center': [-20, -120],
                'spread': [30, 35],
                'float_count': 10,
                'temp_range': [18, 28],
                'sal_range': [34.0, 36.0]
            },
            'indian_ocean': {
                'center': [-15, 75],
                'spread': [25, 30],
                'float_count': 9,
                'temp_range': [22, 30],
                'sal_range': [34.5, 36.8]
            },
            'southern_ocean': {
                'center': [-55, 0],
                'spread': [10, 60],
                'float_count': 7,
                'temp_range': [-1, 8],
                'sal_range': [33.8, 34.7]
            },
            'mediterranean': {
                'center': [38, 15],
                'spread': [8, 15],
                'float_count': 5,
                'temp_range': [16, 26],
                'sal_range': [37.5, 39.0]
            },
            'arctic_atlantic': {
                'center': [70, -10],
                'spread': [8, 20],
                'float_count': 4,
                'temp_range': [-1, 4],
                'sal_range': [34.0, 35.0]
            }
        }
    
    def generate_global_float_network(self) -> List[Dict[str, Any]]:
        """Generate a realistic global network of Argo floats for PPT demo"""
        all_floats = []
        float_id = 4900000  # Starting with realistic Argo float ID format
        
        for region_name, region_data in self.ocean_regions.items():
            center_lat, center_lng = region_data['center']
            lat_spread, lng_spread = region_data['spread']
            count = region_data['float_count']
            temp_range = region_data['temp_range']
            sal_range = region_data['sal_range']
            
            for i in range(count):
                # Generate realistic coordinates with some clustering
                lat = np.random.normal(center_lat, lat_spread/3)
                lng = np.random.normal(center_lng, lng_spread/3)
                
                # Ensure coordinates are within valid ranges
                lat = np.clip(lat, -80, 80)
                lng = np.clip(lng, -180, 180)
                
                # Generate realistic oceanographic values
                temp = np.random.uniform(temp_range[0], temp_range[1])
                salinity = np.random.uniform(sal_range[0], sal_range[1])
                
                # Add some depth variation
                depth = np.random.choice([0, 10, 20, 50, 100, 200], p=[0.3, 0.2, 0.2, 0.15, 0.1, 0.05])
                pressure = depth * 1.02  # Approximate pressure from depth
                
                float_data = {
                    'float_id': int(float_id + i),
                    'lat': round(float(lat), 3),
                    'lng': round(float(lng), 3),
                    'temperature': round(float(temp), 1),
                    'salinity': round(float(salinity), 2),
                    'depth': int(depth),
                    'pressure': round(float(pressure), 1),
                    'region': region_name,
                    'status': 'active',
                    'last_transmission': '2024-01-15',
                    'cycle_number': int(np.random.randint(50, 300))
                }
                all_floats.append(float_data)
            
            float_id += 100  # Increment base ID for next region
        
        return all_floats
    
    def generate_pollution_hotspots(self) -> List[Dict[str, Any]]:
        """Generate pollution detection points for demo"""
        pollution_spots = [
            {
                'lat': 31.2, 'lng': 121.5,  # Shanghai coast
                'pollution_level': 'high',
                'contaminants': ['plastic', 'industrial'],
                'severity': 8.5
            },
            {
                'lat': 34.0, 'lng': -118.2,  # Los Angeles coast
                'pollution_level': 'medium',
                'contaminants': ['urban runoff', 'microplastics'],
                'severity': 6.2
            },
            {
                'lat': 40.7, 'lng': -74.0,  # New York harbor
                'pollution_level': 'medium',
                'contaminants': ['sewage', 'chemicals'],
                'severity': 5.8
            },
            {
                'lat': 51.5, 'lng': 1.3,  # Thames estuary
                'pollution_level': 'low',
                'contaminants': ['agricultural runoff'],
                'severity': 3.2
            },
            {
                'lat': -23.5, 'lng': -46.6,  # São Paulo coast
                'pollution_level': 'high',
                'contaminants': ['industrial', 'sewage'],
                'severity': 7.8
            }
        ]
        return pollution_spots
    
    def generate_organism_detections(self) -> List[Dict[str, Any]]:
        """Generate mesopelagic organism detection points"""
        organism_spots = [
            {
                'lat': 36.0, 'lng': -140.0,  # North Pacific
                'depth_range': [200, 800],
                'species': ['lanternfish', 'bristlemouth'],
                'biomass_density': 'high',
                'migration_pattern': 'diel_vertical'
            },
            {
                'lat': -10.0, 'lng': 65.0,  # Indian Ocean
                'depth_range': [300, 600],
                'species': ['hatchetfish', 'squid'],
                'biomass_density': 'medium',
                'migration_pattern': 'seasonal'
            },
            {
                'lat': 45.0, 'lng': -25.0,  # North Atlantic
                'depth_range': [150, 700],
                'species': ['krill', 'copepods'],
                'biomass_density': 'very_high',
                'migration_pattern': 'diel_vertical'
            },
            {
                'lat': -35.0, 'lng': 150.0,  # Tasman Sea
                'depth_range': [250, 500],
                'species': ['myctophids', 'siphonophores'],
                'biomass_density': 'medium',
                'migration_pattern': 'ontogenetic'
            },
            {
                'lat': -50.0, 'lng': -60.0,  # Southern Ocean
                'depth_range': [100, 400],
                'species': ['antarctic_krill', 'salps'],
                'biomass_density': 'high',
                'migration_pattern': 'seasonal'
            }
        ]
        return organism_spots
    
    def generate_complete_demo_dataset(self) -> Dict[str, Any]:
        """Generate complete dataset for PPT demonstration"""
        return {
            'argo_floats': self.generate_global_float_network(),
            'pollution_hotspots': self.generate_pollution_hotspots(),
            'organism_detections': self.generate_organism_detections(),
            'metadata': {
                'total_floats': sum(region['float_count'] for region in self.ocean_regions.values()),
                'ocean_coverage': list(self.ocean_regions.keys()),
                'data_types': ['temperature', 'salinity', 'pressure', 'pollution', 'organisms'],
                'last_updated': '2024-01-15T12:00:00Z',
                'demo_purpose': 'SIH PPT Presentation'
            }
        }
    
    def export_for_leaflet_map(self) -> str:
        """Export data in format ready for Leaflet map visualization"""
        demo_data = self.generate_complete_demo_dataset()
        
        # Format for JavaScript/Leaflet consumption
        leaflet_data = {
            'floatMarkers': [
                {
                    'lat': float_data['lat'],
                    'lng': float_data['lng'],
                    'temperature': float_data['temperature'],
                    'salinity': float_data['salinity'],
                    'depth': float_data['depth'],
                    'floatId': str(float_data['float_id']),
                    'region': float_data['region'],
                    'popup': f"Float {float_data['float_id']}<br/>Temp: {float_data['temperature']}°C<br/>Salinity: {float_data['salinity']} PSU"
                }
                for float_data in demo_data['argo_floats']
            ],
            'pollutionMarkers': [
                {
                    'lat': spot['lat'],
                    'lng': spot['lng'],
                    'level': spot['pollution_level'],
                    'severity': spot['severity'],
                    'popup': f"Pollution Level: {spot['pollution_level']}<br/>Severity: {spot['severity']}/10"
                }
                for spot in demo_data['pollution_hotspots']
            ],
            'organismMarkers': [
                {
                    'lat': spot['lat'],
                    'lng': spot['lng'],
                    'biomass': spot['biomass_density'],
                    'depth': f"{spot['depth_range'][0]}-{spot['depth_range'][1]}m",
                    'popup': f"Organisms: {', '.join(spot['species'])}<br/>Depth: {spot['depth_range'][0]}-{spot['depth_range'][1]}m<br/>Biomass: {spot['biomass_density']}"
                }
                for spot in demo_data['organism_detections']
            ]
        }
        
        return json.dumps(leaflet_data, indent=2)

if __name__ == "__main__":
    # Generate demo data
    generator = PPTDemoDataGenerator()
    demo_data = generator.generate_complete_demo_dataset()
    
    print(f"Generated {len(demo_data['argo_floats'])} Argo floats across {len(generator.ocean_regions)} ocean regions")
    print(f"Generated {len(demo_data['pollution_hotspots'])} pollution detection points")
    print(f"Generated {len(demo_data['organism_detections'])} organism detection zones")
    
    # Export for web visualization
    leaflet_export = generator.export_for_leaflet_map()
    
    # Save to file for PPT demo
    with open('ppt_demo_map_data.json', 'w') as f:
        f.write(leaflet_export)
    
    print("Demo data exported to 'ppt_demo_map_data.json'")