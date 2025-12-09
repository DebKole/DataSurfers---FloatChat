
"""
Groq-Powered SQL Query Generator for FloatChat
Uses Groq API (GPT-OSS 120B) to understand user intent and generate SQL queries dynamically
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import psycopg2
import pandas as pd
from groq import Groq

# Load environment variables
load_dotenv()

class GroqSQLGenerator:
    """AI-powered SQL query generator using Groq"""
    
    def __init__(self):
        """Initialize Groq AI and database connection"""
        # Configure Groq
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("⚠️ GROQ_API_KEY not found in environment variables!")
        
        self.client = Groq(api_key=api_key)
        # Use GPT-OSS 120B as requested, or fallback if env var is set
        self.model_name = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
        print(f"✅ Using Groq Model: {self.model_name}")
        
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
        """Get database schema information for AI context"""
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
                
                # Format schema for AI
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
                
                # Add geographic regions
                schema_text += "GEOGRAPHIC REGIONS (approximate bounds):\n"
                schema_text += "- Arabian Sea: longitude 50-80, latitude 0-30\n"
                schema_text += "- Bay of Bengal: longitude 80-100, latitude 0-30\n"
                schema_text += "- Southern Indian Ocean: longitude 20-120, latitude -40-0\n"
                schema_text += "- Northern Indian Ocean: longitude 20-120, latitude >30\n"
                
                return schema_text
                
        except Exception as e:
            return f"Error getting schema: {str(e)}"
    
    def _extract_database_from_sql(self, sql: str) -> tuple:
        """Extract database name from SQL comment and clean SQL"""
        lines = sql.strip().split('\n')
        database = None
        cleaned_lines = []
        
        for line in lines:
            if line.strip().startswith('-- DATABASE:'):
                db_part = line.split('-- DATABASE:')[1].strip()
                database = db_part
            else:
                cleaned_lines.append(line)
        
        cleaned_sql = '\n'.join(cleaned_lines).strip()
        
        if not database:
            # Infer from query content
            import re
            year_match = re.search(r"'(20\d{2})", cleaned_sql)
            if year_match:
                year = int(year_match.group(1))
                database = f"argo_indian_ocean_{year % 100:02d}"
            else:
                database = "argo_indian_ocean_25"
        
        return database, cleaned_sql
    
    def _is_cross_year_query(self, user_query: str) -> bool:
        """Determine if query spans multiple years"""
        import re
        range_patterns = [
            r'between\s+(\w+)\s+(20\d{2})\s+and\s+(\w+)\s+(20\d{2})',
            r'from\s+(\w+)\s+(20\d{2})\s+to\s+(\w+)\s+(20\d{2})',
            r'(\w+)\s+(20\d{2})\s+to\s+(\w+)\s+(20\d{2})',
            r'(20\d{2})\s*-\s*(20\d{2})',
        ]
        user_query_lower = user_query.lower()
        for pattern in range_patterns:
            match = re.search(pattern, user_query_lower)
            if match:
                years = [int(y) for y in re.findall(r'20\d{2}', match.group(0))]
                if len(years) >= 2 and years[0] != years[1]:
                    return True
        return False
    
    def _extract_year_from_query(self, user_query: str) -> int:
        """Extract year from user query"""
        import re
        # Look for month+year
        month_year_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(20[12][0-9])', user_query.lower())
        if month_year_match:
            try:
                year = int(month_year_match.group(2))
                if 2015 <= year <= 2025: return year
            except: pass
        
        # Look for 4-digit years
        year_match = re.search(r'\b(20[12][0-9])\b', user_query)
        if year_match:
            try:
                year = int(year_match.group(1))
                if 2015 <= year <= 2025: return year
            except: pass
            
        # Default to 2025
        return 2025
    
    def generate_sql_query(self, user_query: str) -> Dict[str, Any]:
        """Generate SQL query from natural language using Groq"""
        
        is_cross_year = self._is_cross_year_query(user_query)
        inferred_year = self._extract_year_from_query(user_query)
        
        if is_cross_year:
            inferred_year = 25  # Use FDW DB
            
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
   - Use database: argo_indian_ocean_25 (main database with FDW views)
   - Use tables: all_years_argo_profiles and all_years_argo_measurements
   - Example: "November 2016 to February 2017" → Use all_years_argo_profiles
3. **SINGLE-YEAR QUERIES** (date range within one year):
   - Use specific year database: argo_indian_ocean_YY (e.g., argo_indian_ocean_16 for 2016)
   - Use regular tables: argo_profiles and argo_measurements
   - Example: "January 2020" → Use argo_indian_ocean_20 with argo_profiles
4. **NEAREST NEIGHBOR SEARCH (CRITICAL)**
   - If the user asks for "near" a location or coordinate:
   - Use a **BROAD** bounding box (e.g., +/- 5 degrees).
   - **CRITICAL**: Sort by distance: `ORDER BY ((latitude - target_lat)^2 + (longitude - target_lon)^2) ASC LIMIT 50`
   
IMPORTANT RULES:
1. Always use proper JOIN syntax when accessing both tables
2. **DEFAULT TO RETURNING RAW DATA** unless user specifically asks for statistics/aggregation
3. **NO REGION SPECIFIED = RETURN ALL DATA** for that date range
4. Always ORDER BY datetime DESC for temporal queries
5. Use proper PostgreSQL date format: 'YYYY-MM-DD'
6. **ALWAYS include QC filters** for measurement queries (default: QC <= 2)
7. **ALWAYS specify database** as first line comment: -- DATABASE: argo_indian_ocean_YY
8. **SELECT ONLY RELEVANT COLUMNS** (Strict Column Rule):
   - **ALWAYS INCLUDE**: global_profile_id, float_id, latitude, longitude, datetime
   - **IF USER ASKS FOR PARAMETER** (e.g., temperature): Include the parameter AND its QC column (e.g., temperature, temperature_adjusted_qc) and pressure.
   - **Example**: SELECT global_profile_id, float_id, latitude, longitude, datetime, pressure, temperature, temperature_adjusted_qc FROM ...
   - **DO NOT** use SELECT * unless explicitly asked.
9. Return ONLY the SQL query with database comment. NO explanations, NO markdown formatting.

USER QUERY: "{user_query}"
QUERY TYPE: {"CROSS-YEAR (use FDW views)" if is_cross_year else "SINGLE-YEAR"}
INFERRED YEAR: {inferred_year}

Generate the SQL query now.
"""
        try:
            # Generate using Groq
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates PostgreSQL queries."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model_name,
                temperature=0.1,
            )
            
            generated_sql = chat_completion.choices[0].message.content.strip()
            
            # Clean up response
            generated_sql = generated_sql.replace('```sql', '').replace('```', '').strip()
            # Remove trailing semicolon
            generated_sql = generated_sql.rstrip().rstrip(';').strip()
            
            # Extract DB
            database, cleaned_sql = self._extract_database_from_sql(generated_sql)
            
            # Validate
            validation_result = self._validate_sql(cleaned_sql)
            
            return {
                "status": "success",
                "sql": cleaned_sql,
                "database": database,
                "user_query": user_query,
                "validation": validation_result,
                "ai_model": self.model_name
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
        
        # Check if SELECT
        if sql_lower.startswith('select') or sql_lower.startswith('-- database'): # allow comment start
             # if started with comment, check next real part
             real_start = sql_lower.split('\n')[-1].strip() if '\n' in sql_lower else sql_lower
             # Heuristic check
             if 'select' in sql_lower:
                 validation["is_select"] = True
                 
        if not validation["is_select"] and 'select' not in sql_lower:
             validation["is_safe"] = False
             validation["warnings"].append("Query is not a SELECT statement")

        # Dangerous keywords
        dangerous = ['drop', 'delete', 'truncate', 'insert', 'update', 'alter', 'create', 'grant', 'revoke']
        import re
        for keyword in dangerous:
            if re.search(r'\b' + keyword + r'\b', sql_lower):
                validation["is_safe"] = False
                validation["warnings"].append(f"Contains dangerous keyword: {keyword}")
        
        if 'limit' in sql_lower:
            validation["has_limit"] = True
        else:
            validation["warnings"].append("Query doesn't have LIMIT clause")
            
        return validation

    def execute_generated_query(self, sql: str, database: str = None) -> Dict[str, Any]:
        """Execute the generated SQL query"""
        try:
            if database and database.startswith("argo_"):
                db_config = {**self.base_db_config, 'database': database}
            else:
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
        """Use Groq to analyze query results and provide insights"""
        if results["status"] != "success" or results["row_count"] == 0:
            return "No data found for your query."
        
        data_summary = self._prepare_data_summary(results)
        
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
2. Mention number of records found, date range, and key parameter trends (temperature, salinity) if available.
3. Keep it concise (2-4 sentences).
4. Use plain text only - NO markdown formatting.
5. Provide your analysis:
"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                temperature=0.3,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Groq analysis failed: {e}")
            return self._generate_basic_summary(user_query, results)

    def _prepare_data_summary(self, results: Dict[str, Any]) -> str:
        """Prepare data summary for analysis"""
        data = results["data"]
        columns = results["columns"]
        summary_parts = []
        
        numeric_cols = ['temperature', 'salinity', 'pressure', 'depth', 'latitude', 'longitude']
        for col in columns:
            col_lower = col.lower()
            if any(nc in col_lower for nc in numeric_cols):
                values = [row[col] for row in data if row.get(col) is not None and isinstance(row.get(col), (int, float))]
                if values:
                    min_val = min(values)
                    max_val = max(values)
                    avg_val = sum(values) / len(values)
                    summary_parts.append(f"- {col}: min={min_val:.2f}, max={max_val:.2f}, avg={avg_val:.2f}")
        
        if len(data) > 0:
            try:
                summary_parts.append(f"\nSample data (first row): {json.dumps(data[0], default=str)}")
            except: pass
            
        return "\n".join(summary_parts)

    def _generate_basic_summary(self, user_query: str, results: Dict[str, Any]) -> str:
        """Fallback summary"""
        row_count = results.get("row_count", 0)
        return f"Found {row_count} records for your query. View the complete data in the table."

    # Backward compatibility wrapper for query_and_execute
    def query_and_execute(self, user_query: str) -> Dict[str, Any]:
        """Combined workflow"""
        print(f"🧠 Processing query using Groq ({self.model_name}): '{user_query}'")
        
        sql_result = self.generate_sql_query(user_query)
        if sql_result["status"] != "success":
            return sql_result
        
        print(f"🔍 Generated SQL: {sql_result['sql']}")
        execution_result = self.execute_generated_query(sql_result['sql'], database=sql_result.get('database'))
        
        analysis = ""
        if execution_result["status"] == "success":
            analysis = self.analyze_results(user_query, sql_result['sql'], execution_result)
        
        return {
            "status": execution_result["status"],
            "user_query": user_query,
            "generated_sql": sql_result['sql'],
            "database": sql_result.get('database'),
            "validation": sql_result.get('validation'),
            "execution": execution_result,
            "analysis": analysis,
            "ai_model": self.model_name
        }

    # For compatibility with tool methods that might call .model
    @property
    def model(self):
        """Mock model property to support generate_content calls if used elsewhere""" 
        # Create a tiny wrapper to mimic genai.GenerativeModel.generate_content
        class MockModel:
            def __init__(self, client, model_name):
                self.client = client
                self.model_name = model_name
            def generate_content(self, prompt):
                try:
                    resp = self.client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=self.model_name
                    )
                    # Return object with .text property
                    class TextResp:
                        def __init__(self, t): self.text = t
                    return TextResp(resp.choices[0].message.content)
                except Exception as e:
                    class ErrorResp:
                        def __init__(self, e): self.text = "" 
                    return ErrorResp(e)
        return MockModel(self.client, self.model_name)
