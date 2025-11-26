"""
Gemini-Powered SQL Query Generator for FloatChat
Uses Google Gemini AI to understand user intent and generate SQL queries dynamically
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
import psycopg2
import pandas as pd
import json
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

class GeminiSQLGenerator:
    """AI-powered SQL query generator using Gemini"""
    
    def __init__(self):
        """Initialize Gemini AI and database connection"""
        # Configure Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # Latest model
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME')
        }
        
        # Get database schema
        self.schema_info = self._get_database_schema()
        
    def _get_database_schema(self) -> str:
        """Get database schema information for Gemini context"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                # Get table structures
                schema_query = """
                SELECT 
                    table_name,
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name IN ('argo_profiles', 'argo_measurements')
                ORDER BY table_name, ordinal_position;
                """
                
                df = pd.read_sql(schema_query, conn)
                
                # Format schema for Gemini
                schema_text = "DATABASE SCHEMA:\n\n"
                
                for table in ['argo_profiles', 'argo_measurements']:
                    table_cols = df[df['table_name'] == table]
                    schema_text += f"Table: {table}\n"
                    for _, row in table_cols.iterrows():
                        nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
                        schema_text += f"  - {row['column_name']}: {row['data_type']} ({nullable})\n"
                    schema_text += "\n"
                
                # Add sample data context
                sample_query = """
                SELECT 
                    COUNT(*) as total_profiles,
                    COUNT(DISTINCT float_id) as unique_floats,
                    MIN(datetime) as earliest_date,
                    MAX(datetime) as latest_date,
                    MIN(latitude) as min_lat,
                    MAX(latitude) as max_lat,
                    MIN(longitude) as min_lng,
                    MAX(longitude) as max_lng
                FROM argo_profiles;
                """
                
                sample_df = pd.read_sql(sample_query, conn)
                sample_info = sample_df.iloc[0]
                
                schema_text += "DATA OVERVIEW:\n"
                schema_text += f"- Total profiles: {sample_info['total_profiles']}\n"
                schema_text += f"- Unique floats: {sample_info['unique_floats']}\n"
                schema_text += f"- Date range: {sample_info['earliest_date']} to {sample_info['latest_date']}\n"
                schema_text += f"- Latitude range: {sample_info['min_lat']:.2f} to {sample_info['max_lat']:.2f}\n"
                schema_text += f"- Longitude range: {sample_info['min_lng']:.2f} to {sample_info['max_lng']:.2f}\n\n"
                
                # Add geographic context
                schema_text += "GEOGRAPHIC REGIONS (approximate bounds):\n"
                schema_text += "- Arabian Sea: longitude 50-80, latitude 0-30\n"
                schema_text += "- Bay of Bengal: longitude 80-100, latitude 0-30\n"
                schema_text += "- Southern Indian Ocean: longitude 20-120, latitude -40-0\n"
                schema_text += "- Northern Indian Ocean: longitude 20-120, latitude >30\n\n"
                
                return schema_text
                
        except Exception as e:
            return f"Error getting schema: {str(e)}"
    
    def generate_sql_query(self, user_query: str) -> Dict[str, Any]:
        """
        Generate SQL query from natural language using Gemini
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary with generated SQL and metadata
        """
        
        # Create comprehensive prompt for Gemini
        prompt = f"""
You are an expert SQL query generator for oceanographic Argo float data. 

{self.schema_info}

RELATIONSHIPS:
- argo_profiles contains profile metadata (one row per profile)
- argo_measurements contains measurement data (many rows per profile)
- Join on: argo_profiles.global_profile_id = argo_measurements.global_profile_id

IMPORTANT RULES:
1. Always use proper JOIN syntax when accessing both tables
2. **DEFAULT TO RETURNING RAW DATA** unless user specifically asks for statistics/aggregation
3. Always ORDER BY datetime DESC for temporal queries
4. Use BETWEEN for coordinate ranges
5. Use ILIKE for case-insensitive text matching
6. Return only SELECT queries (no INSERT/UPDATE/DELETE)
7. Handle potential NULL values appropriately
8. For date queries without year, assume 2025 (current year in the dataset)
9. Use proper PostgreSQL date format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
10. For date ranges, use: datetime >= '2025-01-01' AND datetime <= '2025-01-15'

QUERY STRATEGY - WHEN TO USE RAW DATA vs AGGREGATION:

**USE RAW DATA (return actual rows):**
- "show me data" / "get data" / "find data" / "data of profiles" / "available data"
- "show me profiles" / "get profiles" / "find profiles" / "profiles in region"
- "show me temperature" / "get temperature" / "temperature data"
- "data from float 123456"
- "latest" or "recent" data
- "what data is available"
- **DEFAULT**: If unclear, return raw data

**USE AGGREGATION (COUNT, AVG, MIN, MAX, GROUP BY):**
- "how many" / "count" / "number of"
- "average" / "mean" / "typical"
- "maximum" / "minimum" / "range"
- "statistics" / "summary" / "overview"
- "patterns" / "trends" / "compare"
- User explicitly asks for aggregated metrics

**EXAMPLES:**
- "show me data of profiles in Arabian Sea" → SELECT * FROM argo_profiles WHERE ...
- "get temperature data from region X" → SELECT * FROM argo_profiles WHERE ...
- "data available in region 10N-18N" → SELECT * FROM argo_profiles WHERE ...
- "how many profiles in Arabian Sea" → SELECT COUNT(*) FROM argo_profiles WHERE ...
- "average temperature in region" → SELECT AVG(temperature) FROM argo_measurements WHERE ...

COMMON QUERY PATTERNS:

**RAW DATA QUERIES (most common):**
- Regional data: SELECT * FROM argo_profiles WHERE latitude BETWEEN X AND Y AND longitude BETWEEN A AND B ORDER BY datetime DESC
- Float lookup: SELECT * FROM argo_profiles WHERE float_id = 'XXXXXX' ORDER BY datetime DESC
- Temporal data: SELECT * FROM argo_profiles WHERE datetime >= '2025-01-01' AND datetime <= '2025-01-15' ORDER BY datetime DESC
- Temperature data: SELECT * FROM argo_profiles WHERE latitude BETWEEN X AND Y ORDER BY datetime DESC
- Latest data: SELECT * FROM argo_profiles ORDER BY datetime DESC
- Institution data: SELECT * FROM argo_profiles WHERE institution ILIKE '%keyword%'

**AGGREGATION QUERIES (only when explicitly requested):**
- Count profiles: SELECT COUNT(*) as profile_count FROM argo_profiles WHERE ...
- Average temperature: SELECT AVG(temperature) as avg_temp FROM argo_measurements WHERE ...
- Statistics: SELECT COUNT(*), MIN(datetime), MAX(datetime) FROM argo_profiles WHERE ...
- Grouped analysis: SELECT region, COUNT(*) FROM argo_profiles GROUP BY region

**DATE HANDLING:**
- Date range (assume 2025 if year not specified): "1st january to 15th january" → '2025-01-01' to '2025-01-15'

TEMPORAL QUERY EXAMPLES:
- "salinity from 1st january to 15th january" → WHERE datetime >= '2025-01-01' AND datetime <= '2025-01-15'
- "data from January 2025" → WHERE datetime >= '2025-01-01' AND datetime < '2025-02-01'
- "latest data" → ORDER BY datetime DESC LIMIT 50

USER QUERY: "{user_query}"

Generate a PostgreSQL query that answers this question intelligently. 

IMPORTANT: 
- Return ONLY the SQL query
- NO explanations or markdown formatting
- NO semicolon at the end (we'll add it if needed)
- Just the raw SQL statement
"""

        try:
            # Generate SQL using Gemini
            response = self.model.generate_content(prompt)
            generated_sql = response.text.strip()
            
            # Clean up the response (remove any markdown formatting)
            if generated_sql.startswith('```sql'):
                generated_sql = generated_sql.replace('```sql', '').replace('```', '').strip()
            elif generated_sql.startswith('```'):
                generated_sql = generated_sql.replace('```', '').strip()
            
            # Remove trailing semicolon (we'll add LIMIT before it if needed)
            generated_sql = generated_sql.rstrip().rstrip(';').strip()
            
            # Validate the query
            validation_result = self._validate_sql(generated_sql)
            
            return {
                "status": "success",
                "sql": generated_sql,
                "user_query": user_query,
                "validation": validation_result,
                "ai_model": "gemini-2.0-flash-exp"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "user_query": user_query
            }
    
    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """Validate generated SQL query"""
        validation = {
            "is_safe": True,
            "is_select": False,
            "has_limit": False,
            "warnings": []
        }
        
        sql_lower = sql.lower().strip()
        
        # Check if it's a SELECT query
        if sql_lower.startswith('select'):
            validation["is_select"] = True
        else:
            validation["is_safe"] = False
            validation["warnings"].append("Query is not a SELECT statement")
        
        # Check for dangerous keywords (as separate words, not substrings)
        dangerous_keywords = ['drop', 'delete', 'truncate', 'insert', 'update', 'alter', 'create']
        import re
        for keyword in dangerous_keywords:
            # Use word boundaries to avoid false positives like "created_at"
            if re.search(r'\b' + keyword + r'\b', sql_lower):
                validation["is_safe"] = False
                validation["warnings"].append(f"Contains dangerous keyword: {keyword}")
        
        # Check for LIMIT clause
        if 'limit' in sql_lower:
            validation["has_limit"] = True
        else:
            validation["warnings"].append("Query doesn't have LIMIT clause - may return large result set")
        
        return validation
    
    def execute_generated_query(self, sql: str) -> Dict[str, Any]:
        """Execute the generated SQL query"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                df = pd.read_sql(sql, conn)
                
                return {
                    "status": "success",
                    "sql": sql,
                    "row_count": len(df),
                    "columns": list(df.columns),
                    "data": df.to_dict(orient="records")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "sql": sql
            }
    
    def analyze_results(self, user_query: str, sql: str, results: Dict[str, Any]) -> str:
        """
        Use Gemini to analyze query results and provide oceanographic insights
        
        Args:
            user_query: Original user query
            sql: SQL query that was executed
            results: Query execution results
            
        Returns:
            Natural language analysis of the results
        """
        if results["status"] != "success" or results["row_count"] == 0:
            return "No data found for your query. Try adjusting the region, time period, or parameters."
        
        # Prepare data summary for Gemini
        data_summary = self._prepare_data_summary(results)
        
        # Create analysis prompt
        prompt = f"""
You are an expert oceanographer analyzing Argo float data. Provide a concise, insightful analysis of the query results.

USER QUERY: "{user_query}"

SQL EXECUTED: {sql}

DATA SUMMARY:
- Total data points: {results['row_count']}
- Columns: {', '.join(results['columns'])}

{data_summary}

ANALYSIS GUIDELINES:
1. Start with a direct answer to the user's question
2. For RAW DATA queries, mention: number of records found, date range, geographic coverage, and key parameters available
3. For list queries (like float IDs), mention the count and provide examples
4. For measurement queries, provide oceanographic context (what do these values mean?)
5. Mention any notable patterns, ranges, or anomalies
6. Keep it concise (2-4 sentences)
7. Use plain text only - NO markdown formatting, NO bold, NO headers, NO asterisks
8. Be conversational and informative
9. Always mention that the data is available in the table for detailed viewing

EXAMPLES:
- For "data of profiles in region": "Found 49 Argo profiles in this region (10N-18N, 85E-100E) collected by 16 unique floats from January 2019 to January 2025. The profiles cover depths from surface to 2031 dbar with temperature and salinity measurements. View the complete data in the table."
- For "get float IDs": "Found 16 unique floats operating in this region. These include floats 2902746, 2902747, and 14 others collecting oceanographic data."
- For "temperature data": "Retrieved 100 temperature profiles from this region ranging from 15.2°C to 28.5°C across various depths. The data shows typical tropical ocean stratification with warmer surface waters. See the table for detailed measurements."
- For "how many profiles": "There are 49 Argo profiles in this region collected by 16 unique floats, providing comprehensive coverage from surface to 2031 dbar depth."

Provide your analysis:
"""
        
        try:
            response = self.model.generate_content(prompt)
            analysis = response.text.strip()
            
            # Clean up any markdown that might have slipped through
            analysis = analysis.replace('**', '').replace('*', '').replace('#', '')
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Gemini analysis failed: {e}")
            # Fallback to basic summary
            return self._generate_basic_summary(user_query, results)
    
    def _prepare_data_summary(self, results: Dict[str, Any]) -> str:
        """Prepare a concise summary of the data for Gemini analysis"""
        data = results["data"]
        columns = results["columns"]
        
        summary_parts = []
        
        # Analyze numeric columns
        numeric_cols = ['temperature', 'salinity', 'pressure', 'depth', 'latitude', 'longitude']
        
        for col in columns:
            col_lower = col.lower()
            if any(nc in col_lower for nc in numeric_cols):
                values = [row[col] for row in data if row.get(col) is not None and isinstance(row.get(col), (int, float))]
                if values:
                    min_val = min(values)
                    max_val = max(values)
                    avg_val = sum(values) / len(values)
                    summary_parts.append(
                        f"- {col}: min={min_val:.2f}, max={max_val:.2f}, "
                        f"avg={avg_val:.2f}, count={len(values)}"
                    )
        
        # Add sample data (first row only, safely)
        if len(data) > 0:
            try:
                summary_parts.append(f"\nSample data (first row): {json.dumps(data[0], default=str)}")
            except:
                summary_parts.append(f"\nSample data available: {len(data)} rows")
        
        return "\n".join(summary_parts)
    
    def _generate_basic_summary(self, user_query: str, results: Dict[str, Any]) -> str:
        """Generate a basic summary when Gemini analysis fails"""
        data = results.get("data", [])
        row_count = results.get("row_count", 0)
        
        if row_count == 0:
            return "No data found for your query. Try adjusting the region, time period, or parameters."
        
        # Try to extract key metrics
        summary_parts = []
        
        if data and len(data) > 0:
            first_row = data[0]
            
            # Check if this is a simple list query (like float IDs)
            if len(first_row) == 1:
                col_name = list(first_row.keys())[0]
                if 'float' in col_name.lower() or 'id' in col_name.lower():
                    summary = f"Found {row_count} unique {col_name}(s) in the specified region. "
                    if row_count <= 20:
                        values = [str(row[col_name]) for row in data[:10]]
                        summary += f"Examples: {', '.join(values[:5])}"
                        if row_count > 5:
                            summary += f" (and {row_count - 5} more)"
                    summary += " View the complete list in the table."
                    return summary
            
            # For raw data queries (profiles, measurements, etc.)
            # Check for date range
            if 'datetime' in first_row:
                try:
                    from datetime import datetime as _dt
                    def _parse_dt(x):
                        if isinstance(x, str):
                            try:
                                return _dt.fromisoformat(x.replace('Z',''))
                            except Exception:
                                return None
                        return x
                    dts = [_parse_dt(d.get('datetime')) for d in data]
                    dts = [dt for dt in dts if dt is not None]
                    if dts:
                        summary_parts.append(f"from {min(dts).date()} to {max(dts).date()}")
                except Exception:
                    pass
            
            # Check for geographic coverage
            if 'latitude' in first_row and 'longitude' in first_row:
                try:
                    lats = [float(d['latitude']) for d in data if d.get('latitude') is not None]
                    lngs = [float(d['longitude']) for d in data if d.get('longitude') is not None]
                    if lats and lngs:
                        summary_parts.append(f"covering {min(lats):.1f}°N-{max(lats):.1f}°N, {min(lngs):.1f}°E-{max(lngs):.1f}°E")
                except Exception:
                    pass
            
            # Check for floats
            if 'float_id' in first_row:
                unique_floats = len(set(str(row.get('float_id')) for row in data if row.get('float_id')))
                summary_parts.append(f"from {unique_floats} unique floats")
            
            # Check for profiles
            if 'global_profile_id' in first_row:
                unique_profiles = len(set(str(row.get('global_profile_id')) for row in data if row.get('global_profile_id')))
                if unique_profiles != row_count:
                    summary_parts.append(f"{unique_profiles} unique profiles")
            
            # Check for temperature
            if 'temperature' in first_row:
                temps = [row['temperature'] for row in data if row.get('temperature') is not None and isinstance(row.get('temperature'), (int, float))]
                if temps:
                    summary_parts.append(f"temperature {min(temps):.1f}°C to {max(temps):.1f}°C")
            
            # Check for salinity
            if 'salinity' in first_row:
                sals = [row['salinity'] for row in data if row.get('salinity') is not None and isinstance(row.get('salinity'), (int, float))]
                if sals:
                    summary_parts.append(f"salinity {min(sals):.1f}-{max(sals):.1f} PSU")
            
            # Check for depth/pressure
            if 'max_pressure' in first_row or 'min_pressure' in first_row:
                try:
                    max_pressures = [row.get('max_pressure') for row in data if row.get('max_pressure') is not None]
                    if max_pressures:
                        summary_parts.append(f"depths to {max(max_pressures):.0f} dbar")
                except Exception:
                    pass
        
        # Build final summary
        if summary_parts:
            summary = f"Found {row_count} profile records " + ", ".join(summary_parts) + ". View the complete data in the table."
        else:
            summary = f"Found {row_count} records for your query. View the complete data in the table."
        
        return summary
    
    def query_and_execute(self, user_query: str) -> Dict[str, Any]:
        """Complete workflow: generate SQL and execute it"""
        print(f"🧠 Processing query: '{user_query}'")
        
        # Step 1: Generate SQL
        sql_result = self.generate_sql_query(user_query)
        
        if sql_result["status"] != "success":
            return sql_result
        
        generated_sql = sql_result["sql"]
        validation = sql_result["validation"]
        
        print(f"🔍 Generated SQL: {generated_sql}")
        print(f"✅ Validation: Safe={validation['is_safe']}, SELECT={validation['is_select']}")
        
        if validation["warnings"]:
            print(f"ℹ️ Warnings (non-blocking): {', '.join(validation['warnings'])}")
        
        # Step 2: Execute if safe
        if not validation["is_safe"]:
            return {
                "status": "error",
                "error": "Generated SQL failed safety validation",
                "sql": generated_sql,
                "validation": validation,
                "execution": {"status": "error", "row_count": 0},
                "analysis": ""
            }
        
        # Previously: auto-appended LIMIT 100 for safety on non-aggregated queries.
        # Requirement: return complete datasets for CSV export; UI will handle preview slicing.
        # Therefore, do NOT append a LIMIT here.
        sql_lower = generated_sql.lower()
        has_aggregation = any(keyword in sql_lower for keyword in ['group by', 'avg(', 'sum(', 'count(', 'min(', 'max('])
        if has_aggregation:
            print("✅ Aggregated query - no LIMIT added")
        else:
            print("ℹ️ No LIMIT appended; returning full result set by request")
        
        # Step 3: Execute query
        execution_result = self.execute_generated_query(generated_sql)
        
        # Step 4: Analyze results with Gemini (always attempt, even if no data)
        analysis = ""
        if execution_result["status"] == "success":
            print("🧠 Analyzing results with Gemini AI...")
            analysis = self.analyze_results(user_query, generated_sql, execution_result)
            if analysis:
                print(f"✅ Analysis: {analysis[:100]}...")
            else:
                print("⚠️ No analysis generated, using fallback")
                analysis = self._generate_basic_summary(user_query, execution_result)
        else:
            print(f"❌ Query execution failed: {execution_result.get('error', 'Unknown error')}")
        
        # Combine results - ensure execution has proper structure
        if "row_count" not in execution_result:
            execution_result["row_count"] = 0
        if "data" not in execution_result:
            execution_result["data"] = []
        if "columns" not in execution_result:
            execution_result["columns"] = []
        
        # Add analysis to execution result for easier access
        execution_result["analysis"] = analysis
        
        # Combine results
        return {
            "status": execution_result["status"],
            "user_query": user_query,
            "generated_sql": generated_sql,
            "validation": validation,
            "execution": execution_result,
            "analysis": analysis,  # Top-level analysis
            "ai_model": "gemini-2.5-flash"
        }

def demo_gemini_sql_generator():
    """Demonstrate the Gemini SQL generator"""
    print("🚀 Gemini SQL Generator Demo")
    print("=" * 50)
    
    generator = GeminiSQLGenerator()
    
    # Test queries
    test_queries = [
        "Show me data from float 1902482",
        "Find all profiles in the Arabian Sea",
        "What are the temperature measurements from January 2025?",
        "Show me the deepest measurements we have",
        "Find profiles from French institutions",
        "What floats were active in winter 2025?",
        "Show me salinity data between 10N and 20N latitude",
        "Find the most recent 10 profiles"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test Query {i}: '{query}'")
        print("-" * 40)
        
        result = generator.query_and_execute(query)
        
        print(f"Status: {result['status']}")
        
        if result["status"] == "success":
            execution = result["execution"]
            print(f"📊 Results: {execution['row_count']} rows")
            print(f"📋 Columns: {', '.join(execution['columns'][:5])}{'...' if len(execution['columns']) > 5 else ''}")
            
            if execution['row_count'] > 0:
                sample_data = execution['data'][0]
                print(f"📄 Sample: {list(sample_data.keys())[:3]} = {list(sample_data.values())[:3]}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        print()
    
    print("🎉 Gemini SQL Generator Demo Complete!")

if __name__ == "__main__":
    demo_gemini_sql_generator()