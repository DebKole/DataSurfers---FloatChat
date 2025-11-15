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
            'database': 'floatchat_argo'
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
2. Use LIMIT to prevent huge result sets (default 100, max 1000)
3. Always ORDER BY datetime DESC for temporal queries
4. Use BETWEEN for coordinate ranges
5. Use ILIKE for case-insensitive text matching
6. Return only SELECT queries (no INSERT/UPDATE/DELETE)
7. Handle potential NULL values appropriately

COMMON QUERY PATTERNS:
- Float lookup: WHERE float_id = 'XXXXXX'
- Regional: WHERE latitude BETWEEN X AND Y AND longitude BETWEEN A AND B
- Temporal: WHERE datetime >= 'YYYY-MM-DD' AND datetime <= 'YYYY-MM-DD'
- Parameter-specific: WHERE temperature IS NOT NULL (or salinity, pressure)
- Institution: WHERE institution ILIKE '%keyword%'

USER QUERY: "{user_query}"

Generate a PostgreSQL query that answers this question. Return ONLY the SQL query, no explanations or markdown formatting.
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
            print(f"⚠️ Warnings: {', '.join(validation['warnings'])}")
        
        # Step 2: Execute if safe
        if not validation["is_safe"]:
            return {
                "status": "error",
                "error": "Generated SQL failed safety validation",
                "sql": generated_sql,
                "validation": validation
            }
        
        # Add LIMIT if missing
        if not validation["has_limit"] and "limit" not in generated_sql.lower():
            generated_sql += " LIMIT 100"
            print("🔧 Added LIMIT 100 for safety")
        
        # Step 3: Execute query
        execution_result = self.execute_generated_query(generated_sql)
        
        # Combine results
        return {
            "status": execution_result["status"],
            "user_query": user_query,
            "generated_sql": generated_sql,
            "validation": validation,
            "execution": execution_result,
            "ai_model": "gemini-2.0-flash-exp"
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