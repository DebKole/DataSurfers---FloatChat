"""
MCP Query Agent for FloatChat
Connects LangGraph agent to MCP server tools
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from float_chat_mcp.data_access_tools.data_access_orchestrator import DataAccessOrchestrator
from float_chat_mcp.data_access_tools.redis_cache_manager import RedisCacheManager


class MCPQueryAgent:
    """Agent that uses MCP tools to answer oceanographic queries"""
    
    def __init__(self):
        """Initialize MCP tools"""
        self.orchestrator = DataAccessOrchestrator(use_gemini=True, enable_cache=True)
        self.cache_manager = RedisCacheManager(enabled=True)
        
        # Keywords that indicate data queries
        self.data_keywords = [
            'temperature', 'temp', 'salinity', 'sal', 'depth', 'surface', 
            'profile', 'thermocline', 'ocean', 'water', 'argo', 'float', 
            'pressure', 'statistics', 'summary', 'conditions', 'compare', 
            'analysis', 'gradient', 'arabian sea', 'bay of bengal', 
            'indian ocean', 'show me', 'find', 'get', 'data', 'measurement',
            'trend', 'curve', 't-s', 't-d', 'ts', 'td', 'vertical profile'
        ]
    
    def is_data_query(self, query: str) -> bool:
        """Check if query is about oceanographic data (not informational questions)"""
        query_lower = query.lower()
        
        # Pure informational patterns - check these FIRST before data keywords
        pure_informational_patterns = [
            'what is argo', 'what are argo floats', 'what is an argo',
            'tell me about argo', 'explain argo', 'describe argo',
            'do you have information about argo', 'information about argo',
            'can you explain argo', 'how does argo work', 'how do argo floats work',
            'what data do you have', 'what can you do', 'what are your capabilities'
        ]
        
        # If it's a pure informational question, route to LLM immediately
        if any(pattern in query_lower for pattern in pure_informational_patterns):
            print(f"   ℹ️ Detected informational query, routing to LLM")
            return False
        
        # Action verbs that indicate data retrieval (strong signals)
        action_verbs = [
            'show', 'get', 'find', 'list', 'display', 'retrieve',
            'fetch', 'give me', 'show me', 'get me', 'give'
        ]
        
        # If query has action verbs, it's definitely a data query
        if any(verb in query_lower for verb in action_verbs):
            print(f"   ✅ Detected data query (action verb: {[v for v in action_verbs if v in query_lower]})")
            return True
        
        # Data-specific terms with context (profiles, measurements, specific IDs)
        data_specific_terms = [
            'float id', 'float 1', 'float 2',  # Specific float IDs
            'profile', 'measurement', 'data from',
            'temperature in', 'salinity in', 'pressure in',  # Parameter + location
            'latest', 'recent', 'historical',
            'arabian sea', 'bay of bengal', 'indian ocean'  # Specific regions
        ]
        
        # If query has data-specific terms with context, it's a data query
        if any(term in query_lower for term in data_specific_terms):
            print(f"   ✅ Detected data query (data-specific term)")
            return True
        
        # Check for pattern: "what are the [data_term]" (e.g., "what are the profiles")
        # This is different from "what are argo floats" (definition)
        if 'what are the' in query_lower or 'what is the' in query_lower:
            data_nouns = ['profile', 'measurement', 'data', 'temperature', 'salinity', 'pressure']
            if any(noun in query_lower for noun in data_nouns):
                print(f"   ✅ Detected data query (what are the...)")
                return True
        
        # Default: not a data query
        print(f"   ❌ Not detected as data query, routing to LLM")
        return False
    
    def execute_query(self, query: str) -> dict:
        """
        Execute query using MCP tools
        
        Args:
            query: Natural language query from user
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Use MCP orchestrator (Gemini AI + Redis + PostgreSQL)
            result = self.orchestrator.execute_query(query)
            
            if result['status'] == 'success':
                # Format response for user
                response = self._format_response(result, query)
                
                # Extract table data for frontend display
                table_data = self._extract_table_data(result)
                
                # Determine if map should be shown
                show_map = self._should_show_map(result)
                
                # Extract map data only if map should be shown
                map_data = self._extract_map_data(result) if show_map else {
                    'points': [],
                    'parameter': 'temperature',
                    'region': None,
                    'enabled': False
                }
                
                return {
                    'status': 'success',
                    'response': response,
                    'query_type': result.get('strategy', 'unknown'),
                    'has_data': True,

                    'table_data': table_data,  # Add structured table data
                    'chart_data': self._extract_chart_data(result),  # Add chart data
                    'show_map': show_map,
                    'map_data': map_data,
                    'float_ids': self._extract_float_ids(result), # Add float IDs
                    'raw_result': result,
                    'gemini_powered': self._is_gemini_powered(result),
                    'cache_hit': self._is_cache_hit(result),
                    'analysis_type': result.get('analysis_type')
                }
            else:
                return {
                    'status': 'error',
                    'response': f"I encountered an error: {result.get('error', 'Unknown error')}",
                    'query_type': 'error',
                    'has_data': False
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'response': f"I encountered an error processing your query: {str(e)}",
                'query_type': 'error',
                'has_data': False
            }
    
    def _format_response(self, result: dict, query: str) -> str:
        """Format MCP result into user-friendly response"""
        
        # Check if this is an analysis result
        if result.get('strategy') == 'analysis':
            return self._format_analysis_response(result, query)
        
        # Check if we have Gemini analysis from the SQL generator
        # Try multiple possible locations for the analysis
        for res in result.get('results', []):
            if isinstance(res, dict):
                # Check for Gemini-powered analysis in multiple locations
                if res.get('gemini_powered'):
                    # Location 1: result.result.analysis
                    if 'result' in res:
                        inner = res['result']
                        if isinstance(inner, dict) and inner.get('analysis'):
                            print(f"   ✅ Using Gemini analysis from result.result.analysis")
                            return inner['analysis']
                    
                    # Location 2: result.params.analysis
                    if 'params' in res:
                        params = res['params']
                        if isinstance(params, dict) and params.get('analysis'):
                            print(f"   ✅ Using Gemini analysis from result.params.analysis")
                            return params['analysis']
                    
                    # Location 3: result.precomputed_result.analysis
                    if 'precomputed_result' in res:
                        precomputed = res['precomputed_result']
                        if isinstance(precomputed, dict) and precomputed.get('analysis'):
                            print(f"   ✅ Using Gemini analysis from result.precomputed_result.analysis")
                            return precomputed['analysis']
                    
                    # If we have Gemini-powered result but no analysis, log it
                    print(f"   ⚠️ Gemini-powered result found but no analysis extracted")
        
        # Fallback: Extract data and create basic summary
        total_rows = 0
        data_sources = result.get('data_sources', [])
        strategy = result.get('strategy', 'unknown')
        actual_data = []
        
        for res in result.get('results', []):
            if isinstance(res, dict):
                if 'result' in res and isinstance(res['result'], dict):
                    inner = res['result']
                    total_rows += inner.get('row_count', 0)
                    if 'data' in inner and inner['data']:
                        actual_data.extend(inner['data'])
                elif 'row_count' in res:
                    total_rows += res['row_count']
        
        # Build response
        if total_rows > 0:
            # Tailored, concise summary
            summary_parts = []
            if actual_data:
                sample = actual_data[0]
                
                # Check if this is just metadata (like database stats) - avoid showing it
                metadata_only_keys = {'table_name', 'row_count', 'column_count', 'table_schema'}
                sample_keys = set(sample.keys())
                is_metadata = len(sample_keys & metadata_only_keys) > 0 and len(sample_keys) < 5
                
                if is_metadata:
                    # This is database metadata, not actual data - treat as no results
                    response = """I couldn't find specific data for that query. Here are some ways you can ask for data:

Regional queries: "Show me temperature in the Arabian Sea" or "Salinity patterns in Bay of Bengal"
Float-specific: "Get data from float 1902482" or "Show me float 2902746"
Temporal: "Latest temperature measurements" or "Recent profiles from January 2025"
Depth analysis: "Temperature trends by depth" or "Surface conditions"

For general information about Argo floats or the system, try asking "What are Argo floats?" or "What data do you have?"""
                    return response
                
                # Unique floats
                unique_floats = len({str(d.get('float_id')) for d in actual_data if d.get('float_id')})
                if unique_floats:
                    summary_parts.append(f"{unique_floats} floats")

                # Profiles or rows
                if 'global_profile_id' in sample:
                    profiles = len({str(d.get('global_profile_id')) for d in actual_data if d.get('global_profile_id')})
                    if profiles:
                        summary_parts.append(f"{profiles} profiles")
                elif 'float_id' in sample and not unique_floats:
                    # If we only have float_ids (like a DISTINCT query), count them
                    summary_parts.append(f"{total_rows} floats")
                else:
                    summary_parts.append(f"{total_rows} records")

                # Region bounds
                if 'latitude' in sample and 'longitude' in sample:
                    try:
                        lats = [float(d['latitude']) for d in actual_data if d.get('latitude') is not None]
                        lngs = [float(d['longitude']) for d in actual_data if d.get('longitude') is not None]
                        if lats and lngs:
                            summary_parts.append(f"lat {min(lats):.1f}–{max(lats):.1f}, lon {min(lngs):.1f}–{max(lngs):.1f}")
                    except Exception:
                        pass

                # Time span
                if 'datetime' in sample:
                    try:
                        from datetime import datetime as _dt
                        def _parse_dt(x):
                            if isinstance(x, str):
                                try:
                                    return _dt.fromisoformat(x.replace('Z',''))
                                except Exception:
                                    return None
                            return x
                        dts = [ _parse_dt(d.get('datetime')) for d in actual_data ]
                        dts = [dt for dt in dts if dt is not None]
                        if dts:
                            summary_parts.append(f"{min(dts).date()} to {max(dts).date()}")
                    except Exception:
                        pass

                # Parameter stats
                if 'temperature' in sample:
                    temps = [d.get('temperature') for d in actual_data if isinstance(d.get('temperature'), (int,float))]
                    if temps:
                        summary_parts.append(f"T {min(temps):.1f}–{max(temps):.1f}°C")
                if 'salinity' in sample:
                    sals = [d.get('salinity') for d in actual_data if isinstance(d.get('salinity'), (int,float))]
                    if sals:
                        summary_parts.append(f"S {min(sals):.1f}–{max(sals):.1f} PSU")

            summary = "; ".join(summary_parts) if summary_parts else f"{total_rows} records"
            response = f"Found {summary}. See the table for details."
            
        else:
            # More helpful fallback message
            response = """I couldn't find specific data for that query. Here are some ways you can ask for data:

Regional queries: "Show me temperature in the Arabian Sea" or "Salinity patterns in Bay of Bengal"
Float-specific: "Get data from float 1902482" or "Show me float 2902746"
Temporal: "Latest temperature measurements" or "Recent profiles from January 2025"
Depth analysis: "Temperature trends by depth" or "Surface conditions"

For general information about Argo floats or the system, try asking "What are Argo floats?" or "What data do you have?"""
        
        return response
    
    def _format_analysis_response(self, result: dict, query: str) -> str:
        """Format analysis results into user-friendly response"""
        
        analysis_type = result.get('analysis_type', 'unknown')
        analysis_result = result.get('analysis_result', {})
        
        # Check if analysis failed
        if result.get('status') == 'error':
            return f"Analysis failed: {result.get('error', 'Unknown error')}"
        
        # Format based on analysis type
        if analysis_type == 'temp_trend':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                count = len(profiles[0]['measurements'])
                return f"I generated a temperature trend analysis with {count} smoothed data points. The trend shows temperature variations over time for your query."
        
        elif analysis_type == 'sal_trend':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                count = len(profiles[0]['measurements'])
                return f"I generated a salinity trend analysis with {count} smoothed data points. The trend shows salinity variations over time for your query."
        
        elif analysis_type == 'ts_curve':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                count = len(profiles[0]['measurements'])
                return f"I generated a Temperature-Salinity (T-S) curve with {count} data points. This chart visualizes the relationship between temperature and salinity for the requested float."
        
        elif analysis_type == 'td_curve':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                count = len(profiles[0]['measurements'])
                return f"I generated a Temperature-Depth (T-D) profile with {count} data points. This profile shows how temperature varies with depth."
        
        elif analysis_type == 'comparison':
            profiles = analysis_result.get('profiles', [])
            if profiles:
                labels = [p.get('label', 'Unknown') for p in profiles]
                return f"I compared {len(profiles)} datasets: {', '.join(labels)}. The comparison includes statistical summaries and curve data for each dataset."
        
        elif analysis_type == 'statistics':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                variables = [m.get('variable') for m in profiles[0]['measurements']]
                return f"I computed statistical summaries for {', '.join(variables)}. The analysis includes count, mean, median, standard deviation, min, and max values."
        
        # Default response
        return f"I completed the {analysis_type} analysis. Check the results in the table on the right."
    
    def _should_show_map(self, result: dict) -> bool:
        """Determine if results should be shown on map"""
        # Only show map for reasonable number of points (not too many, not too few)
        # and when user query seems to be asking for spatial visualization
        
        for res in result.get('results', []):
            if isinstance(res, dict) and 'result' in res:
                inner = res['result']
                if isinstance(inner, dict):
                    row_count = inner.get('row_count', 0)
                    columns = inner.get('columns', [])
                    
                    # Only show map if:
                    # 1. We have lat/lon data
                    # 2. Reasonable number of points (5-500)
                    # 3. Not just a list of IDs
                    if 'latitude' in columns and 'longitude' in columns:
                        if 5 <= row_count <= 500:
                            # Don't show map if it's just a simple list (like float IDs only)
                            if len(columns) > 2:  # More than just lat/lon
                                return True
        return False
    
    def _extract_table_data(self, result: dict) -> dict:
        """Extract data for table display in frontend"""
        table_data = {
            'columns': [],
            'rows': [],
            'total_rows': 0
        }
        
        # Handle analysis results
        if result.get('strategy') == 'analysis':
            analysis_result = result.get('analysis_result', {})
            profiles = analysis_result.get('profiles', [])
            
            all_measurements = []
            for profile in profiles:
                if profile.get('measurements'):
                    # Add profile metadata to measurements if missing
                    measurements = profile['measurements']
                    for m in measurements:
                        # Ensure float_id and cycle_number are present for grouping
                        if 'float_id' not in m and 'float_id' in profile:
                            m['float_id'] = profile['float_id']
                        if 'cycle_number' not in m and 'cycle_number' in profile:
                            m['cycle_number'] = profile['cycle_number']
                    
                    all_measurements.extend(measurements)
            
            if all_measurements:
                table_data['columns'] = list(all_measurements[0].keys())
                table_data['rows'] = all_measurements
                table_data['total_rows'] = len(all_measurements)
                return table_data
        
        # Handle regular data results
        for res in result.get('results', []):
            if isinstance(res, dict) and 'result' in res:
                inner = res['result']
                if isinstance(inner, dict) and 'data' in inner:
                    data = inner['data']
                    
                    if data and len(data) > 0:
                        # Check if this is database metadata (not actual data)
                        first_row = data[0]
                        metadata_keys = {'table_name', 'row_count', 'column_count', 'table_schema', 'table_catalog'}
                        if set(first_row.keys()) & metadata_keys:
                            # Skip metadata, continue looking for actual data
                            continue
                        
                        # Get columns from first row
                        table_data['columns'] = list(first_row.keys())
                        table_data['rows'] = data
                        table_data['total_rows'] = len(data)
                        break  # Use first result with data
        
        return table_data
    
    def _extract_chart_data(self, result: dict) -> dict:
        """Extract data for chart visualization in frontend"""
        chart_data = None
        
        # Handle analysis results
        if result.get('strategy') == 'analysis':
            analysis_type = result.get('analysis_type', 'unknown')
            analysis_result = result.get('analysis_result', {})
            profiles = analysis_result.get('profiles', [])
            
            if profiles and profiles[0].get('measurements'):
                measurements = profiles[0]['measurements']
                
                # Map analysis type to chart type
                chart_data = {
                    'type': analysis_type,
                    'data': measurements,
                    'title': self._get_chart_title(analysis_type),
                    'xLabel': self._get_x_label(analysis_type),
                    'yLabel': self._get_y_label(analysis_type)
                }
        
        return chart_data
    
    def _get_chart_title(self, analysis_type: str) -> str:
        """Get chart title based on analysis type"""
        titles = {
            'temp_trend': 'Temperature Trend Over Time',
            'sal_trend': 'Salinity Trend Over Time',
            'ts_curve': 'Temperature-Salinity Curve',
            'td_curve': 'Temperature-Depth Profile',
            'comparison': 'Data Comparison',
            'statistics': 'Statistical Summary'
        }
        return titles.get(analysis_type, 'Data Visualization')
    
    def _get_x_label(self, analysis_type: str) -> str:
        """Get X-axis label based on analysis type"""
        labels = {
            'temp_trend': 'Date',
            'sal_trend': 'Date',
            'ts_curve': 'Temperature (°C)',
            'td_curve': 'Temperature (°C)',
            'comparison': 'Variable',
            'statistics': 'Variable'
        }
        return labels.get(analysis_type, 'X')
    
    def _get_y_label(self, analysis_type: str) -> str:
        """Get Y-axis label based on analysis type"""
        labels = {
            'temp_trend': 'Temperature (°C)',
            'sal_trend': 'Salinity (PSU)',
            'ts_curve': 'Salinity (PSU)',
            'td_curve': 'Depth (m)',
            'comparison': 'Value',
            'statistics': 'Value'
        }
        return labels.get(analysis_type, 'Y')
    
    def _extract_map_data(self, result: dict) -> dict:
        """Extract data for map visualization"""
        map_data = {
            'points': [],
            'parameter': 'temperature',
            'region': None,
            'enabled': False  # Frontend can check this flag
        }
        
        for res in result.get('results', []):
            if isinstance(res, dict) and 'result' in res:
                inner = res['result']
                if isinstance(inner, dict) and 'data' in inner:
                    data = inner['data']
                    
                    # Extract points with lat/lon (limit to 100 for performance)
                    for point in data[:100]:
                        if 'latitude' in point and 'longitude' in point:
                            try:
                                map_point = {
                                    'lat': float(point['latitude']),
                                    'lng': float(point['longitude']),
                                    'temperature': point.get('temperature'),
                                    'salinity': point.get('salinity'),
                                    'float_id': point.get('float_id'),
                                    'datetime': str(point.get('datetime', ''))
                                }
                                map_data['points'].append(map_point)
                            except (ValueError, TypeError):
                                # Skip points with invalid lat/lon
                                continue
        
        # Only enable map if we have valid points
        if len(map_data['points']) > 0:
            map_data['enabled'] = True
        
        return map_data
    
    def _extract_float_ids(self, result: dict) -> list:
        """Extract unique float IDs from result data"""
        float_ids = set()
        
        # Check intent entities first
        if 'query_metadata' in result:
            entities = result['query_metadata'].get('intent_analysis', {}).get('entities', {})
            if entities.get('float_ids'):
                float_ids.update(str(f) for f in entities['float_ids'])
        
        # Check actual data results
        for res in result.get('results', []):
            if isinstance(res, dict) and 'result' in res:
                inner = res['result']
                if isinstance(inner, dict) and 'data' in inner:
                    data = inner['data']
                    for item in data:
                        if 'float_id' in item:
                            float_ids.add(str(item['float_id']))
                        elif 'FLOAT_ID' in item:
                            float_ids.add(str(item['FLOAT_ID']))
                            
        return list(float_ids)

    def _is_gemini_powered(self, result: dict) -> bool:
        """Check if query used Gemini AI"""
        for res in result.get('results', []):
            if isinstance(res, dict) and res.get('gemini_powered'):
                return True
        return False
    
    def _is_cache_hit(self, result: dict) -> bool:
        """Check if result came from cache"""
        for res in result.get('results', []):
            if isinstance(res, dict) and 'result' in res:
                if res['result'].get('cache_hit'):
                    return True
        return False
    
    def get_system_status(self) -> dict:
        """Get status of MCP system"""
        return self.orchestrator.get_system_status()
    
    def get_recent_queries(self, limit: int = 10) -> list:
        """Get recent queries from cache"""
        return self.cache_manager.get_recent_queries(limit=limit)


# Test function
def test_mcp_agent():
    """Test the MCP query agent"""
    print("🧪 Testing MCP Query Agent\n")
    
    agent = MCPQueryAgent()
    
    test_queries = [
        "Show me temperature data from Arabian Sea",
        "Find data from float 1902482",
        "What's the latest oceanographic data?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 60)
        
        result = agent.execute_query(query)
        
        print(f"Status: {result['status']}")
        print(f"Response: {result['response'][:200]}...")
        print(f"Gemini powered: {result.get('gemini_powered', False)}")
        print(f"Cache hit: {result.get('cache_hit', False)}")
        print(f"Show map: {result.get('show_map', False)}")
    
    print("\n✅ MCP Query Agent test complete!")


if __name__ == "__main__":
    test_mcp_agent()
