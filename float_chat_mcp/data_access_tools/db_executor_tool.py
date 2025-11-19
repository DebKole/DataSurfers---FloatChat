"""
Database Executor Tool for FloatChat MCP Server
Executes SQL queries on PostgreSQL Argo databases
"""

import os
import psycopg2
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import json
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class DatabaseExecutorTool:
    """SQL execution tool for Argo float databases"""
    
    def __init__(self, enable_cache: bool = True):
        """
        Initialize database connections
        
        Args:
            enable_cache: Whether to enable caching (for future use)
        """
        self.main_db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'database': 'floatchat_argo'  # January data
        }
        
        self.live_db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'database': 'floatchat_argo_live'  # Live data
        }
        
        self.logger = logging.getLogger(__name__)
        self.cache = None  # Placeholder for future caching implementation
    
    def execute_query(
        self, 
        sql: str, 
        database: str = "main",
        return_format: str = "dict",
        use_cache: bool = True,
        user_query: str = None,
        analysis: str = None
    ) -> Dict[str, Any]:
        """
        Execute SQL query on specified database
        
        Args:
            sql: SQL query string
            database: "main" (January data) or "live" (current data)
            return_format: "dict", "dataframe", or "json"
            use_cache: Whether to use cache for this query
            user_query: Original user query (optional, for context)
            analysis: Gemini analysis of results (optional)
            
        Returns:
            Query results with metadata
        """
        try:
            # Validate SQL for safety
            if not self._is_safe_query(sql):
                return {
                    "status": "error",
                    "error": "Unsafe SQL query detected",
                    "sql": sql
                }
            
            # Choose database configuration
            db_config = self.main_db_config if database == "main" else self.live_db_config
            
            # Execute query
            with psycopg2.connect(**db_config) as conn:
                df = pd.read_sql(sql, conn)
            
            # Format results
            result = {
                "status": "success",
                "database": database,
                "sql": sql,
                "row_count": len(df),
                "columns": list(df.columns),
                "execution_time": "< 1s",
                "cache_hit": False
            }
            
            # Add Gemini analysis if provided
            if analysis:
                result["analysis"] = analysis
            
            # Add user query context if provided
            if user_query:
                result["user_query"] = user_query
            
            # Add data in requested format
            if return_format == "dataframe":
                result["data"] = df
            elif return_format == "json":
                result["data"] = df.to_json(orient="records", date_format="iso")
            else:  # dict format
                result["data"] = df.to_dict(orient="records")
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "sql": sql,
                "database": database
            }
    
    def get_profiles_by_region(
        self, 
        region: str,
        database: str = "main",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get profiles by geographic region"""
        
        # Define region boundaries
        regions = {
            "Arabian Sea": {"lat": (0, 30), "lng": (50, 80)},
            "Bay of Bengal": {"lat": (0, 30), "lng": (80, 100)},
            "Southern Indian Ocean": {"lat": (-40, 0), "lng": (20, 120)},
            "Northern Indian Ocean": {"lat": (30, 90), "lng": (20, 120)},
            "Indian Ocean": {"lat": (-40, 30), "lng": (20, 120)}
        }
        
        if region not in regions:
            return {
                "status": "error",
                "error": f"Unknown region: {region}. Available: {list(regions.keys())}"
            }
        
        bounds = regions[region]
        
        sql = f"""
        SELECT 
            global_profile_id,
            float_id,
            cycle_number,
            datetime,
            latitude,
            longitude,
            min_pressure,
            max_pressure,
            measurement_count,
            institution,
            data_mode
        FROM argo_profiles
        WHERE latitude BETWEEN {bounds['lat'][0]} AND {bounds['lat'][1]}
          AND longitude BETWEEN {bounds['lng'][0]} AND {bounds['lng'][1]}
        ORDER BY datetime DESC
        LIMIT {limit};
        """
        
        return self.execute_query(sql, database)
    
    def get_profiles_by_float_id(
        self,
        float_id: str,
        database: str = "main",
        include_measurements: bool = False,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get profiles for a specific float"""
        
        if include_measurements:
            sql = f"""
            SELECT 
                ap.float_id,
                ap.cycle_number,
                ap.datetime AS profile_datetime,
                ap.latitude AS profile_latitude,
                ap.longitude AS profile_longitude,
                am.level,
                am.pressure,
                am.temperature,
                am.salinity,
                am.datetime AS measurement_datetime
            FROM argo_profiles ap
            JOIN argo_measurements am ON ap.global_profile_id = am.global_profile_id
            WHERE ap.float_id = '{float_id}'
            ORDER BY ap.datetime DESC, am.level ASC
            LIMIT {limit};
            """
        else:
            sql = f"""
            SELECT *
            FROM argo_profiles
            WHERE float_id = '{float_id}'
            ORDER BY datetime DESC
            LIMIT {limit};
            """
        
        return self.execute_query(sql, database)
    
    def get_database_stats(self, database: str = "main") -> Dict[str, Any]:
        """Get database statistics"""
        
        sql = """
        SELECT 
            'profiles' AS table_name,
            COUNT(*) AS row_count,
            COUNT(DISTINCT float_id) AS unique_floats,
            MIN(datetime) AS earliest_date,
            MAX(datetime) AS latest_date
        FROM argo_profiles
        UNION ALL
        SELECT 
            'measurements' AS table_name,
            COUNT(*) AS row_count,
            NULL AS unique_floats,
            MIN(datetime) AS earliest_date,
            MAX(datetime) AS latest_date
        FROM argo_measurements;
        """
        
        return self.execute_query(sql, database)
    
    def get_measurements_by_profile_ids(
        self,
        profile_ids: List[int],
        parameters: List[str] = None,
        database: str = "main"
    ) -> Dict[str, Any]:
        """Get measurements for specific profile IDs"""
        
        if not profile_ids:
            return {
                "status": "error",
                "error": "No profile IDs provided"
            }
        
        # Default to all parameters
        if not parameters:
            parameters = ["temperature", "salinity", "pressure"]
        
        # Build column list
        param_cols = ", ".join([f"am.{p}" for p in parameters if p in ["temperature", "salinity", "pressure"]])
        
        # Build query
        profile_ids_str = ", ".join(str(pid) for pid in profile_ids[:100])  # Limit to 100 profiles
        
        sql = f"""
        SELECT 
            ap.global_profile_id,
            ap.float_id,
            ap.datetime AS profile_datetime,
            ap.latitude,
            ap.longitude,
            am.level,
            am.pressure,
            {param_cols}
        FROM argo_profiles ap
        JOIN argo_measurements am ON ap.global_profile_id = am.global_profile_id
        WHERE ap.global_profile_id IN ({profile_ids_str})
        ORDER BY ap.datetime DESC, am.level ASC;
        """
        
        return self.execute_query(sql, database)
    
    def _is_safe_query(self, sql: str) -> bool:
        """Validate SQL query for safety"""
        sql_lower = sql.lower().strip()
        
        # Must be a SELECT query
        if not sql_lower.startswith('select'):
            return False
        
        # Check for dangerous keywords
        dangerous_keywords = ['drop', 'delete', 'truncate', 'insert', 'update', 'alter', 'create', 'exec']
        
        import re
        for keyword in dangerous_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_lower):
                return False
        
        return True


def test_db_executor():
    """Test the database executor tool"""
    print("🧪 Testing Database Executor Tool...")
    
    executor = DatabaseExecutorTool()
    
    # Test 1: Get database stats
    print("\n1. Testing database stats...")
    result = executor.get_database_stats()
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Rows: {result['row_count']}")
    
    # Test 2: Get profiles by region
    print("\n2. Testing regional query...")
    result = executor.get_profiles_by_region("Arabian Sea", limit=5)
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Rows: {result['row_count']}")
    
    # Test 3: Get profiles by float ID
    print("\n3. Testing float ID query...")
    result = executor.get_profiles_by_float_id("1902482", limit=5)
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Rows: {result['row_count']}")
    
    print("\n✅ Database Executor Tool testing complete!")


if __name__ == "__main__":
    test_db_executor()
