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
            # Use MCP orchestrator (Groq AI + Redis + PostgreSQL)
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
                
                # Location 4: Top-level analysis in the result object
                if res.get('analysis'):
                     print(f"   ✅ Using Gemini analysis from result.analysis")
                     return res['analysis']
        
        # Check for explicit AI errors in the result
        if result.get('status') == 'error' and any(word in str(result.get('error', '')).lower() for word in ['gemini', 'groq', 'rate limit']):
            return "I'm currently experiencing high traffic with my AI brain (rate limit reached). 🧠💤 I've switched to my standard data retrieval mode to still get you the data you need, but my responses might be a bit less conversational for a moment."
        
        # Check for vector search results with LLM summary
        if result.get('strategy') == 'vector_only':
            # Debug: log what we have
            print(f"   🔍 Vector result keys: {result.keys()}")
            print(f"   🔍 Has llm_summary: {bool(result.get('llm_summary'))}")
            if result.get('llm_summary'):
                print(f"   🔍 LLM summary preview: {result['llm_summary'][:100]}...")
            
            # First check for top-level llm_summary (correct location)
            if result.get('llm_summary'):
                print(f"   ✅ Using LLM summary from vector search (top-level)")
                return result['llm_summary']
            
            # Legacy check: look in results array (shouldn't be needed but kept for safety)
            for res in result.get('results', []):
                if isinstance(res, dict) and res.get('llm_summary'):
                    print(f"   ✅ Using LLM summary from vector search (results array)")
                    return res['llm_summary']
                
                # Fallback: if we have vector results but no summary, try to use the first result
                # BUT ONLY if the query is specifically about a float (has float ID or specific metadata keywords)
                if isinstance(res, dict) and res.get('results') and len(res['results']) > 0:
                    # Only use metadata fallback for specific float queries
                    query_lower = query.lower()
                    is_specific_float_query = (
                        'float' in query_lower and any(char.isdigit() for char in query) or
                        ('pi' in query_lower and 'for' in query_lower) or
                        ('sensor' in query_lower and 'float' in query_lower) or
                        ('project' in query_lower and 'float' in query_lower)
                    )
                    
                    if not is_specific_float_query:
                        # This is a general question, don't use metadata fallback
                        print(f"   ⚠️ General question detected, skipping metadata fallback")
                        continue
                    
                    top_hit = res['results'][0]
                    # Check if this looks like metadata
                    meta = top_hit.get('metadata', {})
                    if meta:
                        # Construct a simple answer from metadata if relevant keys exist
                        if 'PI_NAME' in meta and ('pi' in query_lower or 'investigator' in query_lower):
                            return f"The Principal Investigator (PI) for this float is {meta['PI_NAME']}."
                        if 'PROJECT_NAME' in meta and 'project' in query_lower:
                            return f"This float belongs to the {meta['PROJECT_NAME']} project."
                        if 'SENSOR' in meta and 'sensor' in query_lower:
                             return f"This float carries: {meta['SENSOR']}."
                        if 'DEPLOYMENT_PLATFORM' in meta and 'deployed' in query_lower:
                             return f"This float was deployed by {meta['DEPLOYMENT_PLATFORM']}."
                    
                    # Generic fallback
                    desc = top_hit.get('description', '')
                    if desc:
                        return f"Here is what I found: {desc}"

        # Fallback: Extract data and create basic summary
        total_rows = 0
        data_sources = result.get('data_sources', [])
        strategy = result.get('strategy', 'unknown')
        actual_data = []
        
        for res in result.get('results', []):
            # Handle Vector Search results (list of docs) for table data
            if isinstance(res, dict) and 'results' in res and isinstance(res['results'], list):
                 hits = res['results']
                 if hits:
                     # Add to actual_data for summary stats
                     # Flatten metadata for processing
                     for hit in hits:
                         row = hit.get('metadata', {}).copy()
                         row['description'] = hit.get('description')
                         # Add standard fields if missing
                         if 'float_id' not in row and hit.get('float_id'):
                             row['float_id'] = hit['float_id']
                         actual_data.append(row)
                     total_rows += len(hits)
                     continue

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
                
                # Check if the user asked for a list of floats (e.g. "List floats...")
                is_list_query = "list" in query.lower() or "what floats" in query.lower() or "which floats" in query.lower()
                
                if is_list_query and unique_floats > 0:
                     # If it's a list query, give a direct answer
                    float_ids = sorted(list({str(d.get('float_id')) for d in actual_data if d.get('float_id')}))
                    if len(float_ids) <= 10:
                        response = f"I found {len(float_ids)} floats matching your criteria: {', '.join(float_ids)}. 🚢"
                    else:
                        response = f"I found {len(float_ids)} floats matching your criteria, including {', '.join(float_ids[:5])} and others. 🚢"
                    response += " You can see the full list in the table."
                    return response

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
                        summary_parts.append(f"temperatures from {min(temps):.1f} to {max(temps):.1f}°C")
                if 'salinity' in sample:
                    sals = [d.get('salinity') for d in actual_data if isinstance(d.get('salinity'), (int,float))]
                    if sals:
                        summary_parts.append(f"salinity from {min(sals):.1f} to {max(sals):.1f} PSU")

            # Construct conversational response
            response = f"I found data for {unique_floats} floats! 🌊 "
            
            details = []
            if profiles:
                details.append(f"{profiles} profiles")
            
            if dts:
                details.append(f"covering {min(dts).date()} to {max(dts).date()}")
                
            if details:
                response += f"Here are the details for {', '.join(details)}. "
            else:
                response += "Here are the details. "
                
            response += "Check out the table on the right for the full dataset. 📊"
            
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
                return f"I've analyzed the temperature trends for you! 🌡️ The chart on the right shows how temperature has changed over time, based on {count} data points. It's a great way to spot warming or cooling patterns."
        
        elif analysis_type == 'sal_trend':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                count = len(profiles[0]['measurements'])
                return f"Here is the salinity trend analysis you requested. 🧂 I used {count} data points to visualize salinity variations over time. Take a look at the chart to see the patterns."
        
        elif analysis_type == 'ts_curve':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                # Count total measurements across all profiles for a more impressive number
                total_count = sum(len(p.get('measurements', [])) for p in profiles)
                return f"I've generated the T-S curve for you! 📉 This diagram plots Temperature vs. Salinity using {total_count} data points across {len(profiles)} profiles. It's essential for identifying water masses and understanding density layers."
        
        elif analysis_type == 'td_curve':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                total_count = sum(len(p.get('measurements', [])) for p in profiles)
                return f"Here is the Temperature-Depth profile! 🌊 I've plotted {total_count} points to show how temperature changes as you go deeper. You can clearly see the thermocline and other vertical structures."
        
        elif analysis_type == 'comparison':
            profiles = analysis_result.get('profiles', [])
            if profiles:
                labels = [p.get('label', 'Unknown') for p in profiles]
                return f"Comparison complete! ⚖️ I've analyzed {len(profiles)} datasets: {', '.join(labels)}. Check out the side-by-side statistics and curves to see how they differ."
        
        elif analysis_type == 'statistics':
            profiles = analysis_result.get('profiles', [])
            if profiles and profiles[0].get('measurements'):
                variables = [m.get('variable') for m in profiles[0]['measurements']]
                return f"I've crunched the numbers! 🔢 Here are the statistical summaries for {', '.join(variables)}, including mean, median, and extremes. It gives you a quick snapshot of the data distribution."
        
        # Default response
        return f"Analysis complete! ✅ I've processed the {analysis_type} data for you. You can explore the detailed results in the table and charts on the right."
    
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
            # Handle Vector Search results (list of docs) for table data
            if isinstance(res, dict) and 'results' in res and isinstance(res['results'], list):
                 hits = res['results']
                 if hits:
                     # Flatten metadata for table
                     table_rows = []
                     for hit in hits:
                         row = {'description': hit.get('description')}
                         row.update(hit.get('metadata', {}))
                         table_rows.append(row)
                     
                     table_data['columns'] = list(table_rows[0].keys())
                     table_data['rows'] = table_rows
                     table_data['total_rows'] = len(table_rows)
                     return table_data

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
        
        points_requiring_lookup = []
        
        for res in result.get('results', []):
            if isinstance(res, dict) and 'result' in res:
                inner = res['result']
                if isinstance(inner, dict) and 'data' in inner:
                    data = inner['data']
                    
                    # Extract points with lat/lon (limit to 100 for performance)
                    for point in data[:100]:
                        if 'latitude' in point and 'longitude' in point:
                            try:
                                lat = float(point['latitude'])
                                lng = float(point['longitude'])
                                float_id = point.get('float_id')

                                map_point = {
                                    'lat': lat,
                                    'lng': lng,
                                    'temperature': point.get('temperature'),
                                    'salinity': point.get('salinity'),
                                    'float_id': float_id,
                                    'datetime': str(point.get('datetime', ''))
                                }
                                
                                # If float_id is missing, mark for lookup
                                if not float_id:
                                    points_requiring_lookup.append(map_point)
                                
                                map_data['points'].append(map_point)
                            except (ValueError, TypeError):
                                # Skip points with invalid lat/lon
                                continue
        
        # Perform batched lookup for missing float IDs
        if points_requiring_lookup:
            try:
                # We need to find float IDs that match these lat/lon coordinates
                # This is a bit tricky as coordinates might slightly vary, but we'll try exact match first
                
                # Gather all unique coordinates to lookup
                unique_coords = {(p['lat'], p['lng']) for p in points_requiring_lookup}
                
                # We'll use the orchestrator's db_tool to execute a custom query
                if unique_coords:
                    # Create a temporary table representation for values
                    values_list = ", ".join([f"({lat}, {lng})" for lat, lng in unique_coords])
                    
                    lookup_query = f"""
                    SELECT DISTINCT p.float_id, m.latitude, m.longitude
                    FROM argo_measurements m
                    JOIN argo_profiles p ON m.global_profile_id = p.global_profile_id
                    WHERE (m.latitude, m.longitude) IN ({values_list})
                    LIMIT {len(unique_coords) * 2}
                    """
                    
                    import pandas as pd
                    # Access the engine from the db_tool
                    engine = self.orchestrator.db_tool.engine
                    
                    with engine.connect() as conn:
                        df = pd.read_sql(lookup_query, conn)
                        
                        # measurements floats map
                        coord_float_map = {}
                        for _, row in df.iterrows():
                            # Create a key
                            key = (float(row['latitude']), float(row['longitude']))
                            coord_float_map[key] = str(row['float_id'])
                        
                        # Update points
                        for p in map_data['points']:
                            key = (p['lat'], p['lng'])
                            if not p['float_id'] and key in coord_float_map:
                                p['float_id'] = coord_float_map[key]
                                
            except Exception as e:
                print(f"Error performing float ID lookup: {e}")
        
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
