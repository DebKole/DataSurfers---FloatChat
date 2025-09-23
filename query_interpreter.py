import re
from typing import Dict, Any, List, Optional, Tuple
from data_processor import ArgoDataProcessor
from map_data_provider import MapDataProvider

class QueryInterpreter:
    def __init__(self, data_processor: ArgoDataProcessor):
        self.processor = data_processor
        self.map_provider = MapDataProvider(data_processor)
        self.setup_patterns()
    
    def setup_patterns(self):
        """Setup regex patterns for different types of queries."""
        self.patterns = {
            'temperature_query': [
                r'temperature.*at.*(\d+).*m',
                r'temp.*at.*depth.*(\d+)',
                r'what.*temperature.*(\d+).*meter',
                r'temperature.*(\d+).*depth',
                r'temp.*surface',
                r'surface.*temperature',
                r'temperature.*range',
                r'temp.*profile'
            ],
            'salinity_query': [
                r'salinity.*at.*(\d+).*m',
                r'sal.*at.*depth.*(\d+)',
                r'what.*salinity.*(\d+).*meter',
                r'salinity.*(\d+).*depth',
                r'sal.*surface',
                r'surface.*salinity',
                r'salinity.*range',
                r'sal.*profile'
            ],
            'depth_query': [
                r'data.*at.*(\d+).*m',
                r'depth.*(\d+)',
                r'(\d+).*meter.*depth',
                r'conditions.*at.*(\d+)',
                r'what.*at.*(\d+).*m'
            ],
            'surface_query': [
                r'surface.*conditions',
                r'surface.*data',
                r'top.*layer',
                r'surface.*temp.*sal',
                r'what.*surface'
            ],
            'profile_query': [
                r'profile.*(\d+)',
                r'show.*profile',
                r'profile.*summary',
                r'profile.*data'
            ],
            'comparison_query': [
                r'compare.*profiles',
                r'difference.*between',
                r'compare.*data',
                r'profiles.*comparison'
            ],
            'thermocline_query': [
                r'thermocline',
                r'temperature.*layer',
                r'temp.*gradient',
                r'thermal.*structure'
            ],
            'stats_query': [
                r'statistics',
                r'summary',
                r'overview',
                r'basic.*info',
                r'dataset.*info',
                r'data.*summary'
            ],
            'map_query': [
                r'show.*map',
                r'display.*map',
                r'map.*view',
                r'visualize.*map',
                r'plot.*map',
                r'heatmap',
                r'region.*map',
                r'ocean.*map',
                r'where.*is',
                r'location.*map',
                r'distribution.*map'
            ],
            'pollution_query': [
                r'pollution',
                r'acidification',
                r'ph.*level',
                r'oxygen.*level',
                r'chemical.*analysis',
                r'ocean.*acidification',
                r'pollution.*detection',
                r'environmental.*impact',
                r'water.*quality',
                r'contamination'
            ],
            'climate_query': [
                r'climate.*change',
                r'heat.*content',
                r'warming',
                r'temperature.*anomaly',
                r'climate.*impact',
                r'global.*warming',
                r'thermal.*expansion',
                r'sea.*level',
                r'climate.*analysis'
            ],
            'organism_query': [
                r'organism',
                r'marine.*life',
                r'fluorescent.*matter',
                r'mesopelagic',
                r'biological.*activity',
                r'organism.*detection',
                r'marine.*biology',
                r'deep.*sea.*life',
                r'plankton',
                r'biomass'
            ],
            'range_query': [
                r'between.*(\d+).*and.*(\d+)',
                r'from.*(\d+).*to.*(\d+)',
                r'range.*(\d+).*(\d+)'
            ]
        }
    
    def interpret_query(self, query: str) -> Dict[str, Any]:
        """Interpret a natural language query and return appropriate response."""
        query_lower = query.lower()
        
        # Check for different query types
        if self._matches_pattern(query_lower, 'stats_query'):
            return self._handle_stats_query()
        
        elif self._matches_pattern(query_lower, 'surface_query'):
            return self._handle_surface_query()
        
        elif self._matches_pattern(query_lower, 'thermocline_query'):
            return self._handle_thermocline_query()
        
        elif self._matches_pattern(query_lower, 'comparison_query'):
            return self._handle_comparison_query()
        
        elif self._matches_pattern(query_lower, 'temperature_query'):
            return self._handle_temperature_query(query_lower)
        
        elif self._matches_pattern(query_lower, 'salinity_query'):
            return self._handle_salinity_query(query_lower)
        
        elif self._matches_pattern(query_lower, 'depth_query'):
            return self._handle_depth_query(query_lower)
        
        elif self._matches_pattern(query_lower, 'profile_query'):
            return self._handle_profile_query(query_lower)
        
        elif self._matches_pattern(query_lower, 'map_query'):
            return self._handle_map_query(query)
        
        elif self._matches_pattern(query_lower, 'pollution_query'):
            return self._handle_pollution_query(query)
        
        elif self._matches_pattern(query_lower, 'climate_query'):
            return self._handle_climate_query(query)
        
        elif self._matches_pattern(query_lower, 'organism_query'):
            return self._handle_organism_query(query)
        
        else:
            return self._handle_general_query(query)
    
    def _matches_pattern(self, query: str, pattern_type: str) -> bool:
        """Check if query matches any pattern of given type."""
        patterns = self.patterns.get(pattern_type, [])
        return any(re.search(pattern, query) for pattern in patterns)
    
    def _extract_numbers(self, query: str) -> List[float]:
        """Extract numbers from query."""
        numbers = re.findall(r'\d+\.?\d*', query)
        return [float(num) for num in numbers]
    
    def _handle_stats_query(self) -> Dict[str, Any]:
        """Handle requests for basic statistics."""
        stats = self.processor.get_basic_stats()
        
        response = f"""📊 **Dataset Overview**
        
🔢 **Basic Statistics:**
• Total Profiles: {stats['total_profiles']}
• Total Measurements: {stats['total_measurements']}
• Depth Range: {stats['depth_range']}

🌡️ **Temperature Range:** {stats['temperature_range']}
🧂 **Salinity Range:** {stats['salinity_range']}
📍 **Location:** {stats['location']}
💧 **Pressure Range:** {stats['pressure_range']}

This data represents oceanographic measurements from Argo floats in the specified region."""
        
        return {
            'response': response,
            'data': stats,
            'query_type': 'statistics'
        }
    
    def _handle_surface_query(self) -> Dict[str, Any]:
        """Handle surface conditions queries."""
        surface = self.processor.get_surface_conditions()
        
        response = f"""🌊 **Surface Ocean Conditions**
        
📏 **Depth:** {surface['depth']}m
🌡️ **Temperature:** {surface['temperature']:.2f}°C
🧂 **Salinity:** {surface['salinity']:.2f}
💧 **Pressure:** {surface['pressure']:.2f} dbar

📍 **Location:**
• Latitude: {surface['location']['latitude']:.4f}°
• Longitude: {surface['location']['longitude']:.4f}°

The surface conditions show typical oceanographic parameters for this region."""
        
        return {
            'response': response,
            'data': surface,
            'query_type': 'surface_conditions'
        }
    
    def _handle_thermocline_query(self) -> Dict[str, Any]:
        """Handle thermocline-related queries."""
        thermocline = self.processor.find_thermocline()
        
        response = f"""🌡️ **Thermocline Analysis**
        
📏 **Thermocline Depth:** {thermocline['thermocline_depth']}m
🌡️ **Temperature at Thermocline:** {thermocline['thermocline_temperature']:.2f}°C
📈 **Temperature Gradient:** {thermocline['temperature_gradient']:.4f}°C/m

ℹ️ **Description:** {thermocline['description']}

The thermocline is the layer where temperature changes most rapidly with depth, typically separating warmer surface waters from cooler deep waters."""
        
        return {
            'response': response,
            'data': thermocline,
            'query_type': 'thermocline'
        }
    
    def _handle_temperature_query(self, query: str) -> Dict[str, Any]:
        """Handle temperature-specific queries."""
        numbers = self._extract_numbers(query)
        
        if 'surface' in query:
            surface = self.processor.get_surface_conditions()
            response = f"🌡️ **Surface Temperature:** {surface['temperature']:.2f}°C at {surface['depth']}m depth"
            return {'response': response, 'data': surface, 'query_type': 'temperature'}
        
        elif 'profile' in query or 'range' in query:
            analysis = self.processor.analyze_depth_profile('TEMP')
            response = f"""🌡️ **Temperature Profile Analysis**
            
The temperature shows a **{analysis['overall_trend']}** pattern.

**By Depth Ranges:**"""
            
            for depth_range, stats in analysis['depth_analysis'].items():
                response += f"\n• **{depth_range}:** Avg {stats['mean']:.2f}°C (Range: {stats['min']:.2f}-{stats['max']:.2f}°C)"
            
            return {'response': response, 'data': analysis, 'query_type': 'temperature_profile'}
        
        elif numbers:
            depth = numbers[0]
            data = self.processor.query_by_depth(depth-5, depth+5)  # ±5m range
            if not data.empty:
                avg_temp = data['TEMP'].mean()
                response = f"🌡️ **Temperature near {depth}m depth:** {avg_temp:.2f}°C"
            else:
                response = f"❌ No data available near {depth}m depth"
            
            return {'response': response, 'data': data.to_dict('records') if not data.empty else {}, 'query_type': 'temperature_at_depth'}
        
        else:
            stats = self.processor.get_basic_stats()
            response = f"🌡️ **Temperature Information:** {stats['temperature_range']}"
            return {'response': response, 'data': stats, 'query_type': 'temperature_general'}
    
    def _handle_salinity_query(self, query: str) -> Dict[str, Any]:
        """Handle salinity-specific queries."""
        numbers = self._extract_numbers(query)
        
        if 'surface' in query:
            surface = self.processor.get_surface_conditions()
            response = f"🧂 **Surface Salinity:** {surface['salinity']:.2f} at {surface['depth']}m depth"
            return {'response': response, 'data': surface, 'query_type': 'salinity'}
        
        elif 'profile' in query or 'range' in query:
            analysis = self.processor.analyze_depth_profile('SAL')
            response = f"""🧂 **Salinity Profile Analysis**
            
The salinity shows a **{analysis['overall_trend']}** pattern.

**By Depth Ranges:**"""
            
            for depth_range, stats in analysis['depth_analysis'].items():
                response += f"\n• **{depth_range}:** Avg {stats['mean']:.2f} (Range: {stats['min']:.2f}-{stats['max']:.2f})"
            
            return {'response': response, 'data': analysis, 'query_type': 'salinity_profile'}
        
        elif numbers:
            depth = numbers[0]
            data = self.processor.query_by_depth(depth-5, depth+5)
            if not data.empty:
                avg_sal = data['SAL'].mean()
                response = f"🧂 **Salinity near {depth}m depth:** {avg_sal:.2f}"
            else:
                response = f"❌ No data available near {depth}m depth"
            
            return {'response': response, 'data': data.to_dict('records') if not data.empty else {}, 'query_type': 'salinity_at_depth'}
        
        else:
            stats = self.processor.get_basic_stats()
            response = f"🧂 **Salinity Information:** {stats['salinity_range']}"
            return {'response': response, 'data': stats, 'query_type': 'salinity_general'}
    
    def _handle_depth_query(self, query: str) -> Dict[str, Any]:
        """Handle depth-specific queries."""
        numbers = self._extract_numbers(query)
        
        if numbers:
            depth = numbers[0]
            data = self.processor.query_by_depth(depth-5, depth+5)
            
            if not data.empty:
                avg_temp = data['TEMP'].mean()
                avg_sal = data['SAL'].mean()
                avg_pres = data['PRES'].mean()
                
                response = f"""📏 **Conditions near {depth}m depth:**
                
🌡️ **Temperature:** {avg_temp:.2f}°C
🧂 **Salinity:** {avg_sal:.2f}
💧 **Pressure:** {avg_pres:.2f} dbar

📊 **Data points:** {len(data)} measurements"""
            else:
                response = f"❌ No data available near {depth}m depth"
            
            return {'response': response, 'data': data.to_dict('records') if not data.empty else {}, 'query_type': 'depth_conditions'}
        
        else:
            stats = self.processor.get_basic_stats()
            response = f"📏 **Depth Information:** {stats['depth_range']}"
            return {'response': response, 'data': stats, 'query_type': 'depth_general'}
    
    def _handle_profile_query(self, query: str) -> Dict[str, Any]:
        """Handle profile-specific queries."""
        numbers = self._extract_numbers(query)
        
        if numbers:
            profile_id = int(numbers[0])
            summary = self.processor.get_profile_summary(profile_id)
        else:
            summary = self.processor.get_profile_summary()
        
        if 'error' in summary:
            response = f"❌ {summary['error']}"
        else:
            response = f"""📊 **Profile Summary**
            
🔢 **Profile Count:** {summary['profile_count']}
📏 **Depth Levels:** {summary['depth_levels']}
🏔️ **Maximum Depth:** {summary['max_depth']}m

🌡️ **Surface Temperature:** {summary['surface_temp']:.2f}°C
🧂 **Surface Salinity:** {summary['surface_salinity']:.2f}

📈 **Averages:**
• Temperature: {summary['avg_temperature']:.2f}°C
• Salinity: {summary['avg_salinity']:.2f}

📊 **Gradients:**
• Temperature: {summary['temperature_gradient']:.2f}°C
• Salinity: {summary['salinity_gradient']:.2f}"""
        
        return {'response': response, 'data': summary, 'query_type': 'profile_summary'}
    
    def _handle_comparison_query(self) -> Dict[str, Any]:
        """Handle profile comparison queries."""
        comparison = self.processor.compare_profiles()
        
        if 'message' in comparison:
            response = f"ℹ️ {comparison['message']}"
        else:
            response = "📊 **Profile Comparison**\n\n"
            for profile_name, data in comparison.items():
                response += f"**{profile_name}:**\n"
                response += f"• Max Depth: {data['max_depth']}m\n"
                response += f"• Surface Temp: {data['surface_temp']:.2f}°C\n"
                response += f"• Surface Salinity: {data['surface_salinity']:.2f}\n"
                response += f"• Avg Temp: {data['avg_temp']:.2f}°C\n"
                response += f"• Avg Salinity: {data['avg_salinity']:.2f}\n\n"
        
        return {'response': response, 'data': comparison, 'query_type': 'profile_comparison'}
    
    def _handle_map_query(self, query: str) -> Dict[str, Any]:
        """Handle map visualization queries."""
        map_result = self.map_provider.process_map_query(query)
        
        parameter = map_result['parameter']
        region = map_result['region']
        viz_type = map_result['visualization_type']
        
        # Create response text
        response = f"""🗺️ **Map Visualization Ready**
        
📊 **Parameter:** {parameter.title()}
🌍 **Region:** {region.replace('_', ' ').title() if region else 'Current Data Location'}
📈 **Visualization:** {viz_type.title()}

🔍 **Data Points:** {len(map_result['map_data'])} measurements
📏 **Depth Range:** {map_result['depth_range'] if map_result['depth_range'] else 'Surface (0-50m)'}

Click the map view to see the interactive visualization with heatmap overlay and data points."""
        
        return {
            'response': response,
            'data': map_result,
            'query_type': 'map_visualization',
            'show_map': True,
            'map_data': map_result['map_data'],
            'map_parameter': parameter,
            'map_region': region
        }
    
    def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries that don't match specific patterns."""
        # Provide a helpful response with available options
        response = """🤖 **I can help you with oceanographic data queries!**

Here are some things you can ask me:

🌡️ **Temperature queries:**
• "What's the surface temperature?"
• "Temperature at 100m depth"
• "Show temperature profile"

🧂 **Salinity queries:**
• "What's the surface salinity?"
• "Salinity at 50m depth"
• "Show salinity profile"

📊 **General queries:**
• "Show dataset statistics"
• "Surface conditions"
• "Find thermocline"
• "Compare profiles"

🆕 **Innovation Features:**
• "Analyze ocean pollution"
• "Show climate change impact"
• "Detect marine organisms"
• "Ocean acidification analysis"
• "Heat content analysis"

Try asking me something specific about the oceanographic data!"""
        
        return {
            'response': response,
            'data': {},
            'query_type': 'help'
        }
    
    def _handle_pollution_query(self, query: str) -> Dict[str, Any]:
        """Handle pollution detection and ocean acidification queries."""
        pollution_analysis = self.processor.analyze_ocean_acidification()
        
        ph_data = pollution_analysis['ph_analysis']
        oxygen_data = pollution_analysis['oxygen_analysis']
        indicators = pollution_analysis['pollution_indicators']
        
        response = f"""🏭 **Ocean Pollution Analysis**
        
🧪 **pH Analysis (Ocean Acidification):**
• Mean pH: {ph_data['mean_ph']:.2f}
• Minimum pH: {ph_data['min_ph']:.2f}
• Acidified Areas: {ph_data['acidified_percentage']:.1f}%

💨 **Dissolved Oxygen Analysis:**
• Mean Oxygen: {oxygen_data['mean_oxygen']:.2f} mg/L
• Minimum Oxygen: {oxygen_data['min_oxygen']:.2f} mg/L
• Low Oxygen Areas: {oxygen_data['low_oxygen_percentage']:.1f}%

⚠️ **Pollution Indicators:**
• Severity Level: **{indicators['severity']}**
• Risk Assessment: **{indicators['risk_level']}**
• Acidification Trend: {indicators['acidification_trend']}
• Oxygen Depletion: {indicators['oxygen_depletion']}

📋 **Recommendations:**"""
        
        for i, rec in enumerate(pollution_analysis['recommendations'], 1):
            response += f"\n{i}. {rec}"
        
        # Generate map data for pollution visualization
        map_data = self._generate_pollution_map_data(pollution_analysis)
        
        return {
            'response': response,
            'data': pollution_analysis,
            'query_type': 'pollution_analysis',
            'show_map': True,
            'map_data': map_data,
            'map_parameter': 'pollution',
            'map_region': None
        }
    
    def _handle_climate_query(self, query: str) -> Dict[str, Any]:
        """Handle climate change and heat content analysis queries."""
        heat_analysis = self.processor.analyze_heat_content()
        
        climate_indicators = heat_analysis['climate_indicators']
        climate_impact = heat_analysis['climate_impact']
        
        response = f"""🌡️ **Climate Change Analysis**
        
🔥 **Ocean Heat Content:**
• Total Heat Content: {heat_analysis['total_heat_content']:.2e} J/m²
• Surface Temperature: {heat_analysis['surface_temperature']:.2f}°C
• Temperature Anomaly: {heat_analysis['temperature_anomaly']:.2f}°C

📊 **Heat Distribution by Depth:**"""
        
        for layer, data in heat_analysis['layer_analysis'].items():
            response += f"\n• **{layer.title()} ({data['depth_range']}):** {data['temperature']:.2f}°C, Heat: {data['heat_content']:.2e} J/m²"
        
        response += f"""

🌍 **Climate Indicators:**
• Warming Trend: **{climate_indicators['warming_trend']}**
• Heat Absorption: {climate_indicators['heat_absorption']}
• Thermal Stratification: {climate_indicators['thermal_stratification']}

🌊 **Climate Impact Assessment:**
• Impact Level: **{climate_impact['impact_level']}**
• Sea Level Contribution: {climate_impact['sea_level_contribution']}
• Ecosystem Stress: {climate_impact['ecosystem_stress']}
• Weather Pattern Influence: {climate_impact['weather_pattern_influence']}

This analysis shows the ocean's role in climate change through heat absorption and thermal expansion."""
        
        # Generate map data for heat content visualization
        map_data = self._generate_heat_content_map_data(heat_analysis)
        
        return {
            'response': response,
            'data': heat_analysis,
            'query_type': 'climate_analysis',
            'show_map': True,
            'map_data': map_data,
            'map_parameter': 'heat_content',
            'map_region': None
        }
    
    def _handle_organism_query(self, query: str) -> Dict[str, Any]:
        """Handle mesopelagic organism detection queries."""
        organism_analysis = self.processor.detect_mesopelagic_organisms()
        
        if 'message' in organism_analysis:
            response = f"ℹ️ {organism_analysis['message']}"
            return {
                'response': response,
                'data': organism_analysis,
                'query_type': 'organism_detection'
            }
        
        fluor_data = organism_analysis['fluorescence_analysis']
        insights = organism_analysis['organism_insights']
        
        response = f"""🐟 **Mesopelagic Organism Detection**
        
📊 **Detection Summary:**
• Total Detections: {organism_analysis['total_detections']}
• Detection Rate: {organism_analysis['detection_rate']:.1f}%
• Organism Density: {insights['organism_density']}

🔬 **Fluorescence Analysis:**
• Chlorophyll Mean: {fluor_data['chlorophyll_mean']:.3f}
• Chlorophyll Max: {fluor_data['chlorophyll_max']:.3f}
• CDOM Mean: {fluor_data['cdom_mean']:.3f}
• CDOM Max: {fluor_data['cdom_max']:.3f}

📏 **Depth Distribution:**"""
        
        for depth_range, count in organism_analysis['depth_distribution'].items():
            response += f"\n• {depth_range}: {count} detections"
        
        response += f"""

🔍 **Organism Insights:**
• Most Active Depth: {insights.get('most_active_depth_range', 'N/A')}
• High Confidence Detections: {insights['high_confidence_detections']}
• Migration Pattern: {insights['migration_pattern']}
• Ecological Significance: {insights['ecological_significance']}

⚠️ **Note:** These detections are based on fluorescent matter spikes and provide approximate organism presence indicators."""
        
        # Generate map data for organism visualization
        map_data = self._generate_organism_map_data(organism_analysis)
        
        return {
            'response': response,
            'data': organism_analysis,
            'query_type': 'organism_detection',
            'show_map': True,
            'map_data': map_data,
            'map_parameter': 'organisms',
            'map_region': None
        }
    
    def _generate_pollution_map_data(self, pollution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate map data for pollution visualization."""
        surface_data = self.processor.df[self.processor.df['Level'] <= 50]
        ph_values = pollution_data['ph_analysis']['ph_values']
        oxygen_values = pollution_data['oxygen_analysis']['oxygen_values']
        
        map_points = []
        for i, (_, row) in enumerate(surface_data.iterrows()):
            if i < len(ph_values):
                # Determine pollution level based on pH and oxygen
                ph_val = ph_values[i]
                oxy_val = oxygen_values[i]
                
                if ph_val < 7.9 or oxy_val < 4.0:
                    pollution_level = "High"
                    severity_score = 0.8
                elif ph_val < 8.0 or oxy_val < 5.0:
                    pollution_level = "Medium"
                    severity_score = 0.5
                else:
                    pollution_level = "Low"
                    severity_score = 0.2
                
                map_points.append({
                    'lat': row['LAT'],
                    'lng': row['LON'],
                    'value': severity_score,
                    'ph': ph_val,
                    'oxygen': oxy_val,
                    'pollution_level': pollution_level,
                    'depth': row['Level'],
                    'profile': row['Prof_id']
                })
        
        return map_points
    
    def _generate_heat_content_map_data(self, heat_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate map data for heat content visualization."""
        surface_data = self.processor.df[self.processor.df['Level'] <= 50]
        
        map_points = []
        for _, row in surface_data.iterrows():
            # Calculate normalized heat content value
            temp = row['TEMP']
            heat_intensity = max(0, min(1, (temp + 2) / 7))  # Normalize to 0-1
            
            # Determine heat level
            if temp > 3:
                heat_level = "High"
            elif temp > 1:
                heat_level = "Medium"
            else:
                heat_level = "Low"
            
            map_points.append({
                'lat': row['LAT'],
                'lng': row['LON'],
                'value': heat_intensity,
                'temperature': temp,
                'heat_level': heat_level,
                'depth': row['Level'],
                'profile': row['Prof_id']
            })
        
        return map_points
    
    def _generate_organism_map_data(self, organism_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate map data for organism detection visualization."""
        map_points = []
        
        # Add organism detection points
        for detection in organism_data['organism_locations']:
            map_points.append({
                'lat': detection['latitude'],
                'lng': detection['longitude'],
                'value': 0.8 if detection['confidence'] == 'High' else 0.5,
                'depth': detection['depth'],
                'chlorophyll_spike': detection['chlorophyll_spike'],
                'cdom_spike': detection['cdom_spike'],
                'confidence': detection['confidence'],
                'organism_detected': True,
                'profile': f"organism_{len(map_points)}"
            })
        
        # Add some background points from surface data
        surface_data = self.processor.df[self.processor.df['Level'] <= 50]
        for _, row in surface_data.iterrows():
            map_points.append({
                'lat': row['LAT'],
                'lng': row['LON'],
                'value': 0.1,  # Low background value
                'depth': row['Level'],
                'organism_detected': False,
                'profile': row['Prof_id']
            })
        
        return map_points