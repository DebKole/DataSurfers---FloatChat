import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

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
            'total_profiles': int(self.df['Prof_id'].nunique()),
            'total_measurements': int(len(self.df)),
            'depth_range': f"{float(self.df['Level'].min())}m to {float(self.df['Level'].max())}m",
            'temperature_range': f"{float(self.df['TEMP'].min()):.2f}°C to {float(self.df['TEMP'].max()):.2f}°C",
            'salinity_range': f"{float(self.df['SAL'].min()):.2f} to {float(self.df['SAL'].max()):.2f}",
            'pressure_range': f"{float(self.df['PRES'].min()):.2f} to {float(self.df['PRES'].max()):.2f} dbar",
            'location': f"Latitude: {float(self.df['LAT'].iloc[0]):.4f}, Longitude: {float(self.df['LON'].iloc[0]):.4f}"
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
            'profile_count': int(data['Prof_id'].nunique()) if profile_id is None else 1,
            'depth_levels': int(len(data)),
            'max_depth': float(data['Level'].max()),
            'surface_temp': float(data[data['Level'] == data['Level'].min()]['TEMP'].iloc[0]) if not data.empty else None,
            'surface_salinity': float(data[data['Level'] == data['Level'].min()]['SAL'].iloc[0]) if not data.empty else None,
            'avg_temperature': float(data['TEMP'].mean()),
            'avg_salinity': float(data['SAL'].mean()),
            'temperature_gradient': float(data['TEMP'].max() - data['TEMP'].min()),
            'salinity_gradient': float(data['SAL'].max() - data['SAL'].min())
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
        thermocline_depth = float(self.df.iloc[max_gradient_idx]['Level'])
        thermocline_temp = float(self.df.iloc[max_gradient_idx]['TEMP'])
        
        return {
            'thermocline_depth': thermocline_depth,
            'thermocline_temperature': thermocline_temp,
            'temperature_gradient': float(temp_gradient[max_gradient_idx]),
            'description': f"Strongest temperature change occurs at {thermocline_depth}m depth"
        }
    
    def get_surface_conditions(self) -> Dict[str, Any]:
        """Get surface ocean conditions."""
        surface_data = self.df[self.df['Level'] == self.df['Level'].min()]
        
        return {
            'depth': float(surface_data['Level'].iloc[0]),
            'temperature': float(surface_data['TEMP'].iloc[0]),
            'salinity': float(surface_data['SAL'].iloc[0]),
            'pressure': float(surface_data['PRES'].iloc[0]),
            'location': {
                'latitude': float(surface_data['LAT'].iloc[0]),
                'longitude': float(surface_data['LON'].iloc[0])
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
            comparison[f'Profile_{int(profile_id)}'] = {
                'max_depth': float(profile_data['Level'].max()),
                'surface_temp': float(profile_data[profile_data['Level'] == profile_data['Level'].min()]['TEMP'].iloc[0]),
                'surface_salinity': float(profile_data[profile_data['Level'] == profile_data['Level'].min()]['SAL'].iloc[0]),
                'avg_temp': float(profile_data['TEMP'].mean()),
                'avg_salinity': float(profile_data['SAL'].mean())
            }
        
        return comparison
    
    def analyze_ocean_acidification(self) -> Dict[str, Any]:
        """Analyze ocean acidification using pH, oxygen, and chemical data."""
        # Simulate BGC Argo data for pH and oxygen
        # In real implementation, this would use actual BGC data
        surface_data = self.df[self.df['Level'] <= 50]
        
        # Simulate pH values (typical ocean pH: 7.8-8.2)
        np.random.seed(42)  # For consistent results
        ph_values = np.random.normal(8.0, 0.15, len(surface_data))
        
        # Simulate dissolved oxygen (typical: 4-8 mg/L)
        oxygen_values = np.random.normal(6.5, 1.2, len(surface_data))
        
        # Calculate acidification indicators
        acidified_areas = np.sum(ph_values < 7.9) / len(ph_values) * 100
        low_oxygen_areas = np.sum(oxygen_values < 4.0) / len(oxygen_values) * 100
        
        # Determine pollution severity
        if acidified_areas > 30 or low_oxygen_areas > 25:
            severity = "High"
            risk_level = "Critical"
        elif acidified_areas > 15 or low_oxygen_areas > 15:
            severity = "Medium"
            risk_level = "Moderate"
        else:
            severity = "Low"
            risk_level = "Normal"
        
        return {
            'ph_analysis': {
                'mean_ph': float(np.mean(ph_values)),
                'min_ph': float(np.min(ph_values)),
                'acidified_percentage': float(acidified_areas),
                'ph_values': ph_values.tolist()
            },
            'oxygen_analysis': {
                'mean_oxygen': float(np.mean(oxygen_values)),
                'min_oxygen': float(np.min(oxygen_values)),
                'low_oxygen_percentage': float(low_oxygen_areas),
                'oxygen_values': oxygen_values.tolist()
            },
            'pollution_indicators': {
                'severity': severity,
                'risk_level': risk_level,
                'acidification_trend': 'Increasing' if acidified_areas > 20 else 'Stable',
                'oxygen_depletion': 'Yes' if low_oxygen_areas > 20 else 'No'
            },
            'recommendations': self._get_pollution_recommendations(severity, acidified_areas, low_oxygen_areas)
        }
    
    def analyze_heat_content(self) -> Dict[str, Any]:
        """Analyze ocean heat content for climate change assessment."""
        # Calculate heat content using temperature and depth data
        # Heat content = ρ * Cp * T * depth (simplified)
        # ρ (density) ≈ 1025 kg/m³, Cp (specific heat) ≈ 3850 J/(kg·K)
        
        rho = 1025  # kg/m³
        cp = 3850   # J/(kg·K)
        
        # Calculate heat content for different depth layers
        depth_layers = {
            'surface': (0, 50),
            'upper': (50, 200),
            'intermediate': (200, 500),
            'deep': (500, 1000)
        }
        
        heat_content_analysis = {}
        total_heat_content = 0
        
        for layer_name, (min_depth, max_depth) in depth_layers.items():
            layer_data = self.df[(self.df['Level'] >= min_depth) & (self.df['Level'] < max_depth)]
            
            if not layer_data.empty:
                avg_temp = layer_data['TEMP'].mean()
                layer_thickness = max_depth - min_depth
                
                # Calculate heat content (simplified)
                heat_content = rho * cp * avg_temp * layer_thickness
                heat_content_analysis[layer_name] = {
                    'temperature': float(avg_temp),
                    'thickness': layer_thickness,
                    'heat_content': float(heat_content),
                    'depth_range': f"{min_depth}-{max_depth}m"
                }
                total_heat_content += heat_content
        
        # Analyze temperature anomalies
        surface_temp = self.df[self.df['Level'] <= 10]['TEMP'].mean()
        temp_anomaly = surface_temp - 2.0  # Assuming 2°C baseline
        
        # Climate change indicators
        warming_trend = "Significant" if temp_anomaly > 1.5 else "Moderate" if temp_anomaly > 0.5 else "Minimal"
        
        return {
            'total_heat_content': float(total_heat_content),
            'layer_analysis': heat_content_analysis,
            'temperature_anomaly': float(temp_anomaly),
            'surface_temperature': float(surface_temp),
            'climate_indicators': {
                'warming_trend': warming_trend,
                'heat_absorption': 'High' if total_heat_content > 1e12 else 'Moderate',
                'thermal_stratification': self._analyze_thermal_stratification()
            },
            'climate_impact': self._assess_climate_impact(temp_anomaly, total_heat_content)
        }
    
    def detect_mesopelagic_organisms(self) -> Dict[str, Any]:
        """Detect mesopelagic organisms using fluorescent matter analysis."""
        # Simulate fluorescence data (chlorophyll-a and CDOM)
        # Mesopelagic zone: 200-1000m depth
        mesopelagic_data = self.df[(self.df['Level'] >= 200) & (self.df['Level'] <= 1000)]
        
        if mesopelagic_data.empty:
            return {'message': 'No mesopelagic depth data available'}
        
        # Simulate fluorescence values
        np.random.seed(123)
        chlorophyll_fluor = np.random.exponential(0.5, len(mesopelagic_data))
        cdom_fluor = np.random.exponential(0.3, len(mesopelagic_data))
        
        # Detect spikes (potential organism presence)
        chlor_threshold = np.percentile(chlorophyll_fluor, 85)
        cdom_threshold = np.percentile(cdom_fluor, 85)
        
        organism_detections = []
        for i, (idx, row) in enumerate(mesopelagic_data.iterrows()):
            if chlorophyll_fluor[i] > chlor_threshold or cdom_fluor[i] > cdom_threshold:
                organism_detections.append({
                    'depth': float(row['Level']),
                    'latitude': float(row['LAT']),
                    'longitude': float(row['LON']),
                    'chlorophyll_spike': float(chlorophyll_fluor[i]),
                    'cdom_spike': float(cdom_fluor[i]),
                    'confidence': 'High' if chlorophyll_fluor[i] > chlor_threshold and cdom_fluor[i] > cdom_threshold else 'Medium'
                })
        
        # Analyze organism distribution
        depth_distribution = {}
        for detection in organism_detections:
            depth_bin = int(detection['depth'] // 100) * 100
            depth_key = f"{depth_bin}-{depth_bin + 100}m"
            depth_distribution[depth_key] = depth_distribution.get(depth_key, 0) + 1
        
        return {
            'total_detections': len(organism_detections),
            'detection_rate': float(len(organism_detections) / len(mesopelagic_data) * 100),
            'organism_locations': organism_detections,
            'depth_distribution': depth_distribution,
            'fluorescence_analysis': {
                'chlorophyll_mean': float(np.mean(chlorophyll_fluor)),
                'chlorophyll_max': float(np.max(chlorophyll_fluor)),
                'cdom_mean': float(np.mean(cdom_fluor)),
                'cdom_max': float(np.max(cdom_fluor)),
                'spike_threshold_chlor': float(chlor_threshold),
                'spike_threshold_cdom': float(cdom_threshold)
            },
            'organism_insights': self._generate_organism_insights(organism_detections, depth_distribution)
        }
    
    def _get_pollution_recommendations(self, severity: str, acidification: float, oxygen_depletion: float) -> List[str]:
        """Generate recommendations based on pollution analysis."""
        recommendations = []
        
        if severity == "High":
            recommendations.extend([
                "Immediate monitoring of industrial discharge in the area",
                "Implement emergency marine protection measures",
                "Alert local environmental agencies"
            ])
        
        if acidification > 20:
            recommendations.append("Monitor CO2 absorption rates and implement carbon reduction strategies")
        
        if oxygen_depletion > 15:
            recommendations.append("Investigate nutrient pollution sources causing eutrophication")
        
        recommendations.append("Continue regular BGC-Argo float monitoring")
        return recommendations
    
    def _analyze_thermal_stratification(self) -> str:
        """Analyze thermal stratification patterns."""
        surface_temp = self.df[self.df['Level'] <= 50]['TEMP'].mean()
        deep_temp = self.df[self.df['Level'] >= 200]['TEMP'].mean()
        
        temp_gradient = abs(surface_temp - deep_temp)
        
        if temp_gradient > 3:
            return "Strong stratification"
        elif temp_gradient > 1.5:
            return "Moderate stratification"
        else:
            return "Weak stratification"
    
    def _assess_climate_impact(self, temp_anomaly: float, heat_content: float) -> Dict[str, str]:
        """Assess climate change impact based on temperature and heat content."""
        impact_level = "Low"
        
        if temp_anomaly > 2.0 or heat_content > 2e12:
            impact_level = "High"
        elif temp_anomaly > 1.0 or heat_content > 1e12:
            impact_level = "Moderate"
        
        return {
            'impact_level': impact_level,
            'sea_level_contribution': 'Significant' if temp_anomaly > 1.5 else 'Moderate',
            'ecosystem_stress': 'High' if temp_anomaly > 2.0 else 'Moderate',
            'weather_pattern_influence': 'Strong' if heat_content > 1.5e12 else 'Moderate'
        }
    
    def _generate_organism_insights(self, detections: List[Dict], depth_dist: Dict) -> Dict[str, Any]:
        """Generate insights about detected organisms."""
        if not detections:
            return {'message': 'No significant organism activity detected'}
        
        # Find most active depth range
        most_active_depth = max(depth_dist.keys(), key=lambda k: depth_dist[k]) if depth_dist else None
        
        # Analyze confidence levels
        high_confidence = sum(1 for d in detections if d['confidence'] == 'High')
        
        return {
            'most_active_depth_range': most_active_depth,
            'high_confidence_detections': high_confidence,
            'organism_density': 'High' if len(detections) > 10 else 'Moderate' if len(detections) > 5 else 'Low',
            'migration_pattern': 'Vertical migration detected' if len(depth_dist) > 2 else 'Localized activity',
            'ecological_significance': 'Important carbon pump activity' if high_confidence > 3 else 'Normal biological activity'
        }