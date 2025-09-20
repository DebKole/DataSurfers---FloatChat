import re
from typing import Dict, Any, List, Optional, Tuple
from data_processor import ArgoDataProcessor

class QueryInterpreter:
    def __init__(self, data_processor: ArgoDataProcessor):
        self.processor = data_processor
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

Try asking me something specific about the oceanographic data!"""
        
        return {
            'response': response,
            'data': {},
            'query_type': 'help'
        }