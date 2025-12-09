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
        
        # Base database configuration
        self.base_db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Ensure password is loaded
        if not self.base_db_config['password']:
            print("⚠️ DB_PASSWORD not found in environment, attempting to reload .env...")
            load_dotenv(override=True)
            self.base_db_config['password'] = os.getenv('DB_PASSWORD')
            
        if not self.base_db_config['password']:
            print("❌ ERROR: DB_PASSWORD is still missing after reload. Database connections will likely fail.")
        else:
            print(f"✅ DB Config loaded: user={self.base_db_config['user']}, password_set=True")
        
        # Year-based databases: argo_indian_ocean_15 through argo_indian_ocean_25
        self.year_databases = {
            year: f"argo_indian_ocean_{year}" 
            for year in range(15, 26)  # 2015-2025
        }
        
        # Get database schema (using most recent database as reference)
        self.schema_info = self._get_database_schema()
        
    def _get_database_schema(self) -> str:
        """Get database schema information for Gemini context"""
        try:
            # Use the most recent database (2025) as schema reference
            db_config = {**self.base_db_config, 'database': self.year_databases[25]}
            with psycopg2.connect(**db_config) as conn:
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
                
                # Add multi-database information with FDW
                schema_text += "MULTI-DATABASE STRUCTURE (Foreign Data Wrapper):\n"
                schema_text += "- Data is split across year-based databases: argo_indian_ocean_15 through argo_indian_ocean_25\n"
                schema_text += "- **IMPORTANT**: For cross-year queries, use the unified FDW views:\n"
                schema_text += "  * all_years_argo_profiles - combines argo_profiles from all years (2015-2025)\n"
                schema_text += "  * all_years_argo_measurements - combines argo_measurements from all years (2015-2025)\n"
                schema_text += "- These views include a 'data_year' column to identify which year the data is from\n"
                schema_text += "- **USE CASE**: When user asks for date ranges spanning multiple years (e.g., 'November 2016 to February 2017')\n"
                schema_text += "- **SINGLE YEAR**: For single-year queries, you can still use regular tables in specific databases\n"
                schema_text += "- Year range: 2015-2025 (all years available)\n\n"
                
                # Add quality control information
                schema_text += "QUALITY CONTROL (QC) FLAGS:\n"
                schema_text += "- All measurements use ADJUSTED values (quality-controlled)\n"
                schema_text += "- QC flag columns: pressure_adjusted_qc, temperature_adjusted_qc, salinity_adjusted_qc\n"
                schema_text += "- QC flag values: 1 = best quality, 2 = good quality, 3 = acceptable, >3 = poor/bad\n"
                schema_text += "- Recommendation: Filter for QC flags <= 2 for high-quality data, <= 3 for acceptable data\n"
                schema_text += "- Example: WHERE temperature_adjusted_qc <= 2 (for best quality temperature data)\n\n"
                
                # Add geographic context
                schema_text += "GEOGRAPHIC REGIONS (approximate bounds):\n"
                schema_text += "- Arabian Sea: longitude 50-80, latitude 0-30\n"
                schema_text += "- Bay of Bengal: longitude 80-100, latitude 0-30\n"
                schema_text += "- Southern Indian Ocean: longitude 20-120, latitude -40-0\n"
                schema_text += "- Northern Indian Ocean: longitude 20-120, latitude >30\n\n"
                
                return schema_text
                
        except Exception as e:
            return f"Error getting schema: {str(e)}"
    
    def _extract_database_from_sql(self, sql: str) -> tuple:
        """
        Extract database name from SQL comment and clean SQL
        
        Args:
            sql: SQL query with optional database comment
            
        Returns:
            Tuple of (database_name, cleaned_sql)
        """
        lines = sql.strip().split('\n')
        database = None
        cleaned_lines = []
        
        for line in lines:
            if line.strip().startswith('-- DATABASE:'):
                # Extract database name
                db_part = line.split('-- DATABASE:')[1].strip()
                database = db_part
            else:
                cleaned_lines.append(line)
        
        cleaned_sql = '\n'.join(cleaned_lines).strip()
        
        # If no database specified, try to infer from query
        if not database:
            # Look for year mentions in the SQL
            import re
            year_match = re.search(r"'(20\d{2})", cleaned_sql)
            if year_match:
                year = int(year_match.group(1))
                database = f"argo_indian_ocean_{year % 100:02d}"
            else:
                # Default to most recent
                database = "argo_indian_ocean_25"
        
        return database, cleaned_sql
    
    def _is_cross_year_query(self, user_query: str) -> bool:
        """
        Determine if query spans multiple years
        
        Args:
            user_query: Natural language query
            
        Returns:
            True if query spans multiple years
        """
        import re
        
        # Look for date range patterns
        range_patterns = [
            r'between\s+.*?(20\d{2})\s+and\s+.*?(20\d{2})',  # between ... 2022 and ... 2023
            r'from\s+.*?(20\d{2})\s+to\s+.*?(20\d{2})',      # from ... 2022 to ... 2023
            r'(20\d{2})\s*-\s*(20\d{2})',                    # 2022-2023
            r'(20\d{2})\s+to\s+(20\d{2})',                   # 2022 to 2023
        ]
        
        for pattern in range_patterns:
            match = re.search(pattern, user_query.lower())
            if match:
                # Extract years from the match
                years = [int(y) for y in match.groups()]
                if len(years) >= 2 and years[0] != years[1]:
                    return True
        
        return False
    
    def _extract_year_from_query(self, user_query: str) -> int:
        """
        Extract year from user query
        
        Args:
            user_query: Natural language query
            
        Returns:
            Year as integer (defaults to 2025 if not found)
        """
        import re
        
        # Look for 4-digit years (2015-2025)
        # Find all matches and take the first valid one, or the most recent one if multiple?
        # Usually the first mentioned year is a good anchor.
        year_matches = re.findall(r'\b(20[12][0-9])\b', user_query)
        for y_str in year_matches:
            year = int(y_str)
            if 2015 <= year <= 2025:
                return year
        
        # Look for month names with years (e.g., "November 2016", "February 2017")
        month_year_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(20[12][0-9])', user_query.lower())
        if month_year_match:
            year = int(month_year_match.group(2))
            if 2015 <= year <= 2025:
                return year
        
        # Look for 2-digit years
        year_match = re.search(r'\b([12][0-9])\b', user_query)
        if year_match:
            year = int(year_match.group(1))
            if 15 <= year <= 25:
                return 2000 + year
        
        # Default to 2025
        return 2025
    
    def generate_sql_query(self, user_query: str) -> Dict[str, Any]:
        """
        Generate SQL query from natural language using Gemini
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary with generated SQL and metadata
        """
        
        # Check if this is a cross-year query
        is_cross_year = self._is_cross_year_query(user_query)
        
        # Extract year from query for context
        inferred_year = self._extract_year_from_query(user_query)
        
        # For cross-year queries, always use main database with FDW views
        if is_cross_year:
            inferred_year = 25  # Use main database (2025) which has FDW views
        
        # Create comprehensive prompt for Gemini
        prompt = f"""
You are an expert SQL query generator for oceanographic Argo float data. 

{self.schema_info}

RELATIONSHIPS:
- argo_profiles contains profile metadata (one row per profile)
- argo_measurements contains measurement data (many rows per profile)
- Join on: argo_profiles.global_profile_id = argo_measurements.global_profile_id

FOREIGN DATA WRAPPER (FDW) VIEWS:
- **all_years_argo_profiles**: Unified view of argo_profiles across ALL years (2015-2025)
- **all_years_argo_measurements**: Unified view of argo_measurements across ALL years (2015-2025)
- Both views include a 'data_year' column (integer) indicating the source year
- **USE THESE VIEWS** when query spans multiple years (e.g., "November 2016 to February 2017")
- These views are available in the main database (argo_indian_ocean_25)

DATABASE SELECTION RULES (with Foreign Data Wrapper):
1. **CRITICAL**: Determine which year(s) the user is asking about
2. **CROSS-YEAR QUERIES** (date range spans multiple years):
   - **MANDATORY**: Use database `argo_indian_ocean_25` (main database with FDW views)
   - **MANDATORY**: Use tables `all_years_argo_profiles` and `all_years_argo_measurements`
   - Example: "November 2016 to February 2017" → Use `all_years_argo_profiles`
   - These views automatically query across all year databases (2015-2025)
   - **DO NOT** try to join tables from different databases manually. Use the views.
3. **SINGLE-YEAR QUERIES** (date range within one year):
   - Use specific year database: argo_indian_ocean_YY (e.g., argo_indian_ocean_16 for 2016)
   - Use regular tables: argo_profiles and argo_measurements
   - Example: "January 2020" → Use argo_indian_ocean_20 with argo_profiles
4. **NEAREST NEIGHBOR SEARCH (CRITICAL)**
   - If the user asks for data "near" a specific location (e.g., "near Mumbai", "near 19N 72E"), and you have a center point:
   - **DO NOT** use a small bounding box (e.g., +/- 0.5 degrees) if it risks excluding data.
   - Instead, use a **BROAD** bounding box (e.g., +/- 5 degrees) to filter candidates.
   - **CRITICAL**: Sort by distance from the center point using the Pythagorean theorem approximation.
   - Example: `ORDER BY ((latitude - 19.07)^2 + (longitude - 72.87)^2) ASC LIMIT 50`
   - This ensures we find the closest available data even if it's slightly offshore.
5. **Use 'argo_indian_ocean_24'** for 2024 data, 'argo_indian_ocean_25' for 2025.
6. **Join `argo_profiles` (ap) and `argo_measurements` (am)** on `global_profile_id`.
7. **Select ONLY relevant columns**.
8. Database naming: argo_indian_ocean_YY where YY is 2-digit year (15=2015, 16=2016, 23=2023, 25=2025)
9. **ALL YEARS AVAILABLE**: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
10. If no year specified, assume most recent data (2025) or use argo_indian_ocean_25
11. Return the database name as a comment at the top: -- DATABASE: argo_indian_ocean_YY

QUALITY CONTROL RULES:
1. All measurement columns use ADJUSTED values (pressure_adjusted, temperature_adjusted, salinity_adjusted)
2. Each measurement has QC flags: pressure_adjusted_qc, temperature_adjusted_qc, salinity_adjusted_qc
3. QC flag meanings: 1=best, 2=good, 3=acceptable, 4+=poor/bad
4. **DEFAULT**: Filter for QC <= 2 (best and good quality) unless user asks for all data
5. If user asks for "high quality" or "best quality", use QC = 1
6. If user asks for "all data" or doesn't mention quality, use QC <= 3
7. Example filter: WHERE temperature_adjusted_qc <= 2 AND salinity_adjusted_qc <= 2

IMPORTANT RULES:
1. Always use proper JOIN syntax when accessing both tables
2. **DEFAULT TO RETURNING RAW DATA** unless user specifically asks for statistics/aggregation
3. **NO REGION SPECIFIED = RETURN ALL DATA** for that date range (don't ask for clarification)
4. Always ORDER BY datetime DESC for temporal queries
5. Use BETWEEN for coordinate ranges
6. Use ILIKE for case-insensitive text matching
7. Return only SELECT queries (no INSERT/UPDATE/DELETE)
8. Handle potential NULL values appropriately
9. For date queries without year, assume 2025 (current year in the dataset)
10. Use proper PostgreSQL date format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
11. For date ranges, use: datetime >= '2025-01-01' AND datetime <= '2025-01-15'
12. **ALWAYS include QC filters** for measurement queries (default: QC <= 2)
13. **ALWAYS specify database** as first line comment: -- DATABASE: argo_indian_ocean_YY
14. **GENERATE SQL, DON'T ASK FOR CLARIFICATION** - if region not specified, query all regions

HANDLING HISTORICAL EVENTS & DISASTERS:
1. **Identify Named Events**: If the user mentions a named event (e.g., "Cyclone Amphan", "2004 Tsunami", "Cyclone Ockhi"), use your internal knowledge to determine the event's date range.
2. **Determine Date Range**:
   - Find the start and end dates of the event.
   - Add a buffer (e.g., +/- 2-5 days) to capture relevant data before and after.
3. **Apply Filters**:
   - Use `datetime` filters to restrict data to this period.
   - If the event spans multiple years, use the FDW views (`all_years_argo_profiles`).
   - If the event is localized, apply approximate latitude/longitude filters if known (optional but helpful).
4. **Example**: "Cyclone Amphan" (May 2020) → WHERE datetime >= '2020-05-15' AND datetime <= '2020-05-25'

QUERY STRATEGY - COLUMN SELECTION:

**CRITICAL: SELECT ONLY RELEVANT COLUMNS**
- **DO NOT use `SELECT *`** unless the user explicitly asks for "all data" or "full profile".
- Select ONLY the columns necessary to answer the user's question.
- Always include `datetime`, `latitude`, `longitude` for context.
- Always include `float_id` and `cycle_number` (or `global_profile_id`) for identification.
- **Example**: If user asks for "temperature", SELECT `datetime`, `latitude`, `longitude`, `float_id`, `temperature_adjusted`, `temperature_adjusted_qc`. DO NOT select salinity or pressure.

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
- "show me data of profiles in Arabian Sea" → SELECT global_profile_id, float_id, datetime, latitude, longitude FROM argo_profiles WHERE latitude BETWEEN ... AND longitude BETWEEN ...
- "get temperature data from region X" → SELECT ap.datetime, ap.latitude, ap.longitude, ap.float_id, am.temperature_adjusted, am.temperature_adjusted_qc FROM argo_profiles ap JOIN argo_measurements am ON ap.global_profile_id = am.global_profile_id WHERE ...
- "data available in region 10N-18N" → SELECT global_profile_id, float_id, datetime, latitude, longitude FROM argo_profiles WHERE latitude BETWEEN 10 AND 18
- "give temperature data between november 2016 and february 2017" → SELECT ap.datetime, ap.latitude, ap.longitude, ap.float_id, am.temperature_adjusted, am.temperature_adjusted_qc FROM all_years_argo_profiles ap JOIN all_years_argo_measurements am ON ap.global_profile_id = am.global_profile_id WHERE ap.datetime >= '2016-11-01' AND ap.datetime <= '2017-02-28'
- "how many profiles in Arabian Sea" → SELECT COUNT(*) FROM argo_profiles WHERE ...
- "average temperature in region" → SELECT AVG(temperature) FROM argo_measurements WHERE ...
- "salinity during Cyclone Amphan" → SELECT ap.datetime, ap.latitude, ap.longitude, ap.float_id, am.salinity_adjusted, am.salinity_adjusted_qc FROM argo_profiles ap JOIN argo_measurements am ON ap.global_profile_id = am.global_profile_id WHERE ap.datetime >= '2020-05-15' AND ap.datetime <= '2020-05-25'

COMMON QUERY PATTERNS:

**CROSS-YEAR QUERIES (date range spans multiple years):**
- Date range across years (Nov 2016 - Feb 2017), no region specified:
  -- DATABASE: argo_indian_ocean_25
  SELECT global_profile_id, float_id, datetime, latitude, longitude FROM all_years_argo_profiles 
  WHERE datetime >= '2016-11-01' AND datetime <= '2017-02-28' 
  ORDER BY datetime DESC
  
- Temperature data across years with measurements:
  -- DATABASE: argo_indian_ocean_25
  SELECT ap.datetime, ap.latitude, ap.longitude, ap.float_id, am.temperature_adjusted, am.temperature_adjusted_qc
  FROM all_years_argo_profiles ap
  JOIN all_years_argo_measurements am ON ap.global_profile_id = am.global_profile_id
  WHERE ap.datetime >= '2016-11-01' AND ap.datetime <= '2017-02-28'
    AND am.temperature_adjusted_qc <= 2
  ORDER BY ap.datetime DESC

**RAW DATA QUERIES (single year):**
- Regional data (2023): 
  -- DATABASE: argo_indian_ocean_23
  SELECT global_profile_id, float_id, datetime, latitude, longitude FROM argo_profiles WHERE latitude BETWEEN X AND Y AND longitude BETWEEN A AND B ORDER BY datetime DESC
  
- Float lookup with measurements (2020):
  -- DATABASE: argo_indian_ocean_20
  SELECT ap.datetime, ap.latitude, ap.longitude, ap.float_id, am.pressure_adjusted, am.temperature_adjusted, am.salinity_adjusted, 
         am.temperature_adjusted_qc, am.salinity_adjusted_qc
  FROM argo_profiles ap
  JOIN argo_measurements am ON ap.global_profile_id = am.global_profile_id
  WHERE ap.float_id = 'XXXXXX' AND am.temperature_adjusted_qc <= 2 AND am.salinity_adjusted_qc <= 2
  ORDER BY ap.datetime DESC
  
- High-quality temperature data (2022):
  -- DATABASE: argo_indian_ocean_22
  SELECT ap.datetime, ap.latitude, ap.longitude, ap.float_id, am.temperature_adjusted, am.temperature_adjusted_qc
  FROM argo_profiles ap
  JOIN argo_measurements am ON ap.global_profile_id = am.global_profile_id
  WHERE latitude BETWEEN X AND Y AND am.temperature_adjusted_qc = 1
  ORDER BY ap.datetime DESC
  
- Latest data (2025):
  -- DATABASE: argo_indian_ocean_25
  SELECT global_profile_id, float_id, datetime, latitude, longitude FROM argo_profiles ORDER BY datetime DESC LIMIT 50

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

QUERY TYPE: {"CROSS-YEAR (use FDW views)" if is_cross_year else "SINGLE-YEAR"}
INFERRED YEAR: {inferred_year} (use database: argo_indian_ocean_{inferred_year % 100:02d})
{"**IMPORTANT**: Use all_years_argo_profiles and all_years_argo_measurements views for this cross-year query" if is_cross_year else ""}

Generate a PostgreSQL query that answers this question intelligently. 

**CRITICAL INSTRUCTIONS:**
1. **ALWAYS GENERATE SQL** - Never respond with text asking for clarification
2. **NO REGION = ALL REGIONS** - If user doesn't specify region, query all data for that date range
3. **FIRST LINE MUST BE**: -- DATABASE: argo_indian_ocean_YY (where YY is the 2-digit year)
4. Include QC filters for measurement queries (default: QC <= 2)
5. Return ONLY the SQL query with database comment
6. NO explanations, NO questions, NO markdown formatting
7. NO semicolon at the end (we'll add it if needed)
8. Just the database comment + raw SQL statement
9. **SELECT ONLY RELEVANT COLUMNS** - Do not use SELECT * unless explicitly requested.
10. **DO NOT PREFIX TABLE NAMES** with the database name. Use `argo_profiles`, NOT `argo_indian_ocean_20.argo_profiles`.

EXAMPLE OUTPUT FORMAT:
-- DATABASE: argo_indian_ocean_25
SELECT global_profile_id, float_id, datetime, latitude, longitude FROM all_years_argo_profiles WHERE datetime >= '2016-11-01' AND datetime <= '2017-02-28' ORDER BY datetime DESC
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
            
            # Extract database name from SQL comment
            database, cleaned_sql = self._extract_database_from_sql(generated_sql)
            
            # Validate the query
            validation_result = self._validate_sql(cleaned_sql)
            
            return {
                "status": "success",
                "sql": cleaned_sql,
                "database": database,
                "user_query": user_query,
                "validation": validation_result,
                "ai_model": "gemini-2.5-flash"
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
    
    def execute_generated_query(self, sql: str, database: str = None) -> Dict[str, Any]:
        """Execute the generated SQL query on specified database"""
        try:
            # Determine database config
            if database and database.startswith("argo_"):
                db_config = {**self.base_db_config, 'database': database}
            else:
                # Default to most recent database
                db_config = {**self.base_db_config, 'database': self.year_databases[25]}
            
            with psycopg2.connect(**db_config) as conn:
                df = pd.read_sql(sql, conn)
                
                return {
                    "status": "success",
                    "sql": sql,
                    "database": db_config['database'],
                    "row_count": len(df),
                    "columns": list(df.columns),
                    "data": df.to_dict(orient="records")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "sql": sql,
                "database": database
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
                "database": sql_result.get("database"),
                "validation": validation,
                "execution": {"status": "error", "row_count": 0},
                "analysis": ""
            }
        
        # Get database from SQL result
        target_database = sql_result.get("database", "argo_indian_ocean_25")
        print(f"🗄️ Target database: {target_database}")
        
        # Previously: auto-appended LIMIT 100 for safety on non-aggregated queries.
        # Requirement: return complete datasets for CSV export; UI will handle preview slicing.
        # However, returning 70k+ rows (full float history) causes the server to hang/timeout.
        # We MUST impose a reasonable limit for the chat interface.
        # If the user needs full data, we should implement a specific export flow.
        # For now, limit to 2500 rows to prevent freezing.
        
        sql_lower = generated_sql.lower()
        if 'limit' not in sql_lower:
            print("⚠️ No LIMIT clause found. Appending LIMIT 2500 for safety.")
            generated_sql += " LIMIT 2500"
        else:
            print("ℹ️ No LIMIT appended; returning full result set by request")
            
        # Execute the query
        print(f"🚀 Executing query on {target_database}...")
        execution_result = self.execute_generated_query(generated_sql, target_database)
        
        # Analyze results
        print("🧠 Analyzing results with Gemini AI...")
        analysis = self.analyze_results(user_query, generated_sql, execution_result)
        print(f"✅ Analysis: {analysis[:100]}...")
        

        
        # Combine results
        return {
            "status": execution_result["status"],
            "user_query": user_query,
            "generated_sql": generated_sql,
            "database": execution_result.get("database", target_database),
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