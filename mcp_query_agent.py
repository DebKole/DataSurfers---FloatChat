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
            'indian ocean', 'show me', 'find', 'get', 'data', 'measurement'
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
            return False
        
        # Action verbs that indicate data retrieval (strong signals)
        action_verbs = [
            'show', 'get', 'find', 'list', 'display', 'retrieve',
            'fetch', 'give me', 'show me', 'get me'
        ]
        
        # If query has action verbs, it's definitely a data query
        if any(verb in query_lower for verb in action_verbs):
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
            return True
        
        # Check for pattern: "what are the [data_term]" (e.g., "what are the profiles")
        # This is different from "what are argo floats" (definition)
        if 'what are the' in query_lower or 'what is the' in query_lower:
            data_nouns = ['profile', 'measurement', 'data', 'temperature', 'salinity', 'pressure']
            if any(noun in query_lower for noun in data_nouns):
                return True
        
        # Default: not a data query
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
                    'show_map': show_map,
                    'map_data': map_data,
                    'raw_result': result,
                    'gemini_powered': self._is_gemini_powered(result),
                    'cache_hit': self._is_cache_hit(result)
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
