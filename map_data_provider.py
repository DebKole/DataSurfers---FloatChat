"""
Map data provider for oceanographic visualizations.
Processes queries and returns appropriate map data for visualization.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re
from data_processor import ArgoDataProcessor

class MapDataProvider:
    def __init__(self, data_processor: ArgoDataProcessor):
        self.processor = data_processor
        self.setup_region_mapping()
    
    def setup_region_mapping(self):
        """Setup region mapping for different ocean areas."""
        self.regions = {
            'north_atlantic': {
                'bounds': {'lat': [60, 80], 'lng': [-80, -20]},
                'description': 'North Atlantic Ocean'
            },
            'indian_ocean': {
                'bounds': {'lat': [-40, 30], 'lng': [20, 120]},
                'description': 'Indian Ocean'
            },
            'pacific': {
                'bounds': {'lat': [-60, 60], 'lng': [120, -80]},
                'description': 'Pacific Ocean'
            },
            'arctic': {
                'bounds': {'lat': [66, 90], 'lng': [-180, 180]},
                'description': 'Arctic Ocean'
            },
            'southern_ocean': {
                'bounds': {'lat': [-90, -60], 'lng': [-180, 180]},
                'description': 'Southern Ocean'
            }
        }
    
    def process_map_query(self, query: str) -> Dict[str, Any]:
        """Process a query and return appropriate map data."""
        query_lower = query.lower()
        
        # Extract parameters and regions from query
        parameter = self._extract_parameter(query_lower)
        region = self._extract_region(query_lower)
        depth_range = self._extract_depth_range(query_lower)
        
        # Get map data based on query
        map_data = self._generate_map_data(parameter, region, depth_range)
        
        # Determine visualization type
        viz_type = self._determine_visualization_type(query_lower)
        
        return {
            'map_data': map_data,
            'parameter': parameter,
            'region': region,
            'depth_range': depth_range,
            'visualization_type': viz_type,
            'metadata': self._get_metadata(parameter, region),
            'should_show_map': self._should_show_map(query_lower)
        }
    
    def _extract_parameter(self, query: str) -> str:
        """Extract the oceanographic parameter from query."""
        if any(word in query for word in ['temperature', 'temp', 'thermal']):
            return 'temperature'
        elif any(word in query for word in ['salinity', 'sal', 'salt']):
            return 'salinity'
        elif any(word in query for word in ['pressure', 'depth']):
            return 'pressure'
        else:
            return 'temperature'  # default
    
    def _extract_region(self, query: str) -> Optional[str]:
        """Extract region information from query."""
        region_keywords = {
            'indian': 'indian_ocean',
            'pacific': 'pacific',
            'atlantic': 'north_atlantic',
            'arctic': 'arctic',
            'southern': 'southern_ocean',
            'north': 'north_atlantic',
            'south': 'southern_ocean'
        }
        
        for keyword, region in region_keywords.items():
            if keyword in query:
                return region
        
        return None
    
    def _extract_depth_range(self, query: str) -> Optional[Tuple[float, float]]:
        """Extract depth range from query."""
        # Look for depth patterns like "at 100m", "between 50 and 200m"
        depth_patterns = [
            r'at (\d+)m',
            r'(\d+) meter',
            r'between (\d+) and (\d+)',
            r'from (\d+) to (\d+)',
            r'surface',
            r'deep'
        ]
        
        for pattern in depth_patterns:
            match = re.search(pattern, query)
            if match:
                if 'surface' in pattern:
                    return (0, 50)
                elif 'deep' in pattern:
                    return (200, 500)
                elif 'between' in pattern or 'from' in pattern:
                    return (float(match.group(1)), float(match.group(2)))
                else:
                    depth = float(match.group(1))
                    return (depth - 25, depth + 25)
        
        return None
    
    def _determine_visualization_type(self, query: str) -> str:
        """Determine the type of visualization needed."""
        if any(word in query for word in ['heatmap', 'heat', 'distribution']):
            return 'heatmap'
        elif any(word in query for word in ['region', 'area', 'zone']):
            return 'region'
        elif any(word in query for word in ['point', 'location', 'station']):
            return 'points'
        else:
            return 'combined'  # default: heatmap + points
    
    def _should_show_map(self, query: str) -> bool:
        """Determine if the query should trigger map visualization."""
        map_triggers = [
            'map', 'show', 'display', 'visualize', 'plot', 'region', 'area',
            'where', 'location', 'distribution', 'heatmap', 'ocean'
        ]
        
        return any(trigger in query for trigger in map_triggers)
    
    def _generate_map_data(self, parameter: str, region: Optional[str], depth_range: Optional[Tuple[float, float]]) -> List[Dict]:
        """Generate map data based on parameters."""
        # Filter data based on depth range if specified
        if depth_range:
            data = self.processor.query_by_depth(depth_range[0], depth_range[1])
        else:
            # Use surface data by default
            data = self.processor.query_by_depth(0, 50)
        
        if data.empty:
            # Return sample data if no real data matches
            return self._get_sample_data(parameter, region)
        
        # Convert to map format
        map_points = []
        for _, row in data.iterrows():
            point = {
                'lat': row['LAT'],
                'lng': row['LON'],
                'value': row[self._get_column_name(parameter)],
                'depth': row['Level'],
                'profile': row['Prof_id'],
                'pressure': row['PRES']
            }
            map_points.append(point)
        
        # Add interpolated points for better visualization if we have few points
        if len(map_points) < 10:
            map_points.extend(self._generate_interpolated_points(map_points, parameter))
        
        return map_points
    
    def _get_column_name(self, parameter: str) -> str:
        """Get the column name for the parameter."""
        column_mapping = {
            'temperature': 'TEMP',
            'salinity': 'SAL',
            'pressure': 'PRES'
        }
        return column_mapping.get(parameter, 'TEMP')
    
    def _get_sample_data(self, parameter: str, region: Optional[str]) -> List[Dict]:
        """Generate sample data for visualization when no real data is available."""
        # Base location (current data location)
        base_lat, base_lng = 73.27, -58.0
        
        # Adjust base location based on region
        if region == 'indian_ocean':
            base_lat, base_lng = -20, 70
        elif region == 'pacific':
            base_lat, base_lng = 0, -150
        elif region == 'north_atlantic':
            base_lat, base_lng = 50, -30
        
        # Generate sample points around the base location
        sample_points = []
        for i in range(8):
            lat_offset = np.random.uniform(-2, 2)
            lng_offset = np.random.uniform(-3, 3)
            
            # Generate realistic values based on parameter
            if parameter == 'temperature':
                value = np.random.uniform(-1, 5) if region != 'indian_ocean' else np.random.uniform(20, 30)
            elif parameter == 'salinity':
                value = np.random.uniform(32, 36)
            else:  # pressure
                value = np.random.uniform(0, 100)
            
            point = {
                'lat': base_lat + lat_offset,
                'lng': base_lng + lng_offset,
                'value': round(value, 2),
                'depth': 0,
                'profile': f'sample_{i}',
                'pressure': np.random.uniform(0, 50)
            }
            sample_points.append(point)
        
        return sample_points
    
    def _generate_interpolated_points(self, existing_points: List[Dict], parameter: str) -> List[Dict]:
        """Generate interpolated points for smoother visualization."""
        if len(existing_points) < 2:
            return []
        
        interpolated = []
        for i in range(len(existing_points) - 1):
            p1 = existing_points[i]
            p2 = existing_points[i + 1]
            
            # Create interpolated point between p1 and p2
            mid_lat = (p1['lat'] + p2['lat']) / 2
            mid_lng = (p1['lng'] + p2['lng']) / 2
            mid_value = (p1['value'] + p2['value']) / 2
            
            interpolated_point = {
                'lat': mid_lat,
                'lng': mid_lng,
                'value': round(mid_value, 2),
                'depth': (p1['depth'] + p2['depth']) / 2,
                'profile': 'interpolated',
                'pressure': (p1['pressure'] + p2['pressure']) / 2
            }
            interpolated.append(interpolated_point)
        
        return interpolated
    
    def _get_metadata(self, parameter: str, region: Optional[str]) -> Dict[str, Any]:
        """Get metadata for the map visualization."""
        metadata = {
            'parameter_info': {
                'temperature': {
                    'unit': '°C',
                    'description': 'Sea surface temperature',
                    'typical_range': '-2 to 30°C'
                },
                'salinity': {
                    'unit': 'PSU',
                    'description': 'Practical salinity units',
                    'typical_range': '30 to 37 PSU'
                },
                'pressure': {
                    'unit': 'dbar',
                    'description': 'Water pressure',
                    'typical_range': '0 to 1000 dbar'
                }
            }.get(parameter, {}),
            'region_info': self.regions.get(region, {}) if region else {},
            'data_source': 'Argo Float Network',
            'last_updated': 'Real-time'
        }
        
        return metadata

    def get_region_bounds(self, region: str) -> Optional[Dict]:
        """Get the geographical bounds for a region."""
        return self.regions.get(region, {}).get('bounds')
    
    def suggest_regions(self, query: str) -> List[str]:
        """Suggest relevant regions based on query."""
        suggestions = []
        query_lower = query.lower()
        
        for region_key, region_info in self.regions.items():
            if any(word in query_lower for word in region_key.split('_')):
                suggestions.append(region_key)
        
        return suggestions if suggestions else ['north_atlantic']  # default suggestion