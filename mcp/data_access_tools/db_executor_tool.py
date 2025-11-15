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
    
    def __init__(self):
        """Initialize database connections"""
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
    
    def execute_query(
        self, 
        sql: str, 
        database: str = "main",
        return_format: str = "dict"
    ) -> Dict[str, Any]:
        """
        Execute SQL query on specified database
        
        Args:
            sql: SQL query string
            database: "main" (January data) or "live" (current data)
            return_format: "dict", "dataframe", or "json"
            
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
                "execution_time": "< 1s"  # Could add actual timing
            }
            
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
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get profiles filtered by geographic region"""
        
        region_bounds = {
            "Arabian Sea": "longitude BETWEEN 50 AND 80 AND latitude BETWEEN 0 AND 30",
            "Bay of Bengal": "longitude BETWEEN 80 AND 100 AND latitude BETWEEN 0 AND 30", 
            "Southern Indian Ocean": "longitude BETWEEN 20 AND 120 AND latitude BETWEEN -40 AND 0",
            "Northern Indian Ocean": "longitude BETWEEN 20 AND 120 AND latitude > 30"
        }
        
        bounds = region_bounds.get(region)
        if not bounds:
            return {
                "status": "error",
                "error": f"Unknown region: {region}",
                "available_regions": list(region_bounds.keys())
            }
        
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
        WHERE {bounds}
        ORDER BY datetime DESC
        LIMIT {limit}
        """
        
        result = self.execute_query(sql, database)
        # Add the SQL query to the result for debugging
        if isinstance(result, dict):
            result["sql"] = sql
        return result
    
    def get_profiles_by_float_id(
        self, 
        float_id: str,
        database: str = "main",
        include_measurements: bool = False
    ) -> Dict[str, Any]:
        """Get all profiles from a specific float"""
        
        if include_measurements:
            sql = f"""
            SELECT 
                p.*,
                m.pressure,
                m.temperature,
                m.salinity
            FROM argo_profiles p
            LEFT JOIN argo_measurements m ON p.global_profile_id = m.global_profile_id
            WHERE p.float_id = '{float_id}'
            ORDER BY p.cycle_number, m.pressure
            """
        else:
            sql = f"""
            SELECT * FROM argo_profiles 
            WHERE float_id = '{float_id}'
            ORDER BY cycle_number
            """
        
        result = self.execute_query(sql, database)
        # Add the SQL query to the result for debugging
        if isinstance(result, dict):
            result["sql"] = sql
        return result
    
    def get_profiles_by_date_range(
        self, 
        start_date: str,
        end_date: str,
        database: str = "main",
        limit: int = 200
    ) -> Dict[str, Any]:
        """Get profiles within date range"""
        
        sql = f"""
        SELECT 
            global_profile_id,
            float_id,
            datetime,
            latitude,
            longitude,
            measurement_count,
            institution
        FROM argo_profiles 
        WHERE datetime >= '{start_date}' 
          AND datetime <= '{end_date}'
        ORDER BY datetime DESC
        LIMIT {limit}
        """
        
        return self.execute_query(sql, database)
    
    def get_measurements_by_profile_ids(
        self, 
        profile_ids: List[int],
        database: str = "main",
        parameters: List[str] = None
    ) -> Dict[str, Any]:
        """Get measurements for specific profile IDs"""
        
        if not profile_ids:
            return {
                "status": "error",
                "error": "No profile IDs provided"
            }
        
        # Default parameters
        if parameters is None:
            parameters = ["pressure", "temperature", "salinity"]
        
        # Build column selection
        columns = ["global_profile_id"] + parameters
        column_str = ", ".join(columns)
        
        # Build ID list
        id_list = ",".join(map(str, profile_ids))
        
        sql = f"""
        SELECT {column_str}
        FROM argo_measurements 
        WHERE global_profile_id IN ({id_list})
        ORDER BY global_profile_id, pressure
        """
        
        return self.execute_query(sql, database)
    
    def get_database_stats(self, database: str = "main") -> Dict[str, Any]:
        """Get database statistics"""
        
        sql = """
        SELECT 
            'profiles' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT float_id) as unique_floats,
            MIN(datetime) as earliest_date,
            MAX(datetime) as latest_date
        FROM argo_profiles
        
        UNION ALL
        
        SELECT 
            'measurements' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT global_profile_id) as unique_profiles,
            NULL as earliest_date,
            NULL as latest_date
        FROM argo_measurements
        """
        
        return self.execute_query(sql, database)
    
    def search_profiles_by_criteria(
        self,
        criteria: Dict[str, Any],
        database: str = "main",
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search profiles using multiple criteria"""
        
        conditions = []
        
        # Build WHERE conditions
        if criteria.get('min_lat') and criteria.get('max_lat'):
            conditions.append(f"latitude BETWEEN {criteria['min_lat']} AND {criteria['max_lat']}")
        
        if criteria.get('min_lng') and criteria.get('max_lng'):
            conditions.append(f"longitude BETWEEN {criteria['min_lng']} AND {criteria['max_lng']}")
        
        if criteria.get('start_date'):
            conditions.append(f"datetime >= '{criteria['start_date']}'")
        
        if criteria.get('end_date'):
            conditions.append(f"datetime <= '{criteria['end_date']}'")
        
        if criteria.get('institution'):
            conditions.append(f"institution ILIKE '%{criteria['institution']}%'")
        
        if criteria.get('min_measurements'):
            conditions.append(f"measurement_count >= {criteria['min_measurements']}")
        
        # Build SQL
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
        SELECT 
            global_profile_id,
            float_id,
            cycle_number,
            datetime,
            latitude,
            longitude,
            measurement_count,
            institution
        FROM argo_profiles 
        WHERE {where_clause}
        ORDER BY datetime DESC
        LIMIT {limit}
        """
        
        return self.execute_query(sql, database)
    
    def _is_safe_query(self, sql: str) -> bool:
        """Basic SQL safety validation"""
        sql_lower = sql.lower().strip()
        
        # Block dangerous operations
        dangerous_keywords = [
            'drop', 'delete', 'truncate', 'insert', 'update', 
            'alter', 'create', 'grant', 'revoke'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False
        
        # Must be a SELECT query
        if not sql_lower.startswith('select'):
            return False
        
        return True

def test_db_executor():
    """Test the database executor tool"""
    print("🧪 Testing Database Executor Tool...")
    
    tool = DatabaseExecutorTool()
    
    # Test 1: Database stats
    print("\n1. Testing database stats...")
    stats = tool.get_database_stats("main")
    if stats["status"] == "success":
        print(f"   Found {stats['row_count']} rows")
        for row in stats["data"]:
            print(f"   {row['table_name']}: {row['row_count']} rows")
    else:
        print(f"   Error: {stats['error']}")
    
    # Test 2: Regional search
    print("\n2. Testing regional search...")
    results = tool.get_profiles_by_region("Arabian Sea", limit=5)
    if results["status"] == "success":
        print(f"   Found {results['row_count']} Arabian Sea profiles")
    else:
        print(f"   Error: {results['error']}")
    
    # Test 3: Float ID search
    print("\n3. Testing float ID search...")
    if results["status"] == "success" and results["data"]:
        float_id = results["data"][0]["float_id"]
        float_results = tool.get_profiles_by_float_id(float_id)
        if float_results["status"] == "success":
            print(f"   Found {float_results['row_count']} profiles for float {float_id}")
        else:
            print(f"   Error: {float_results['error']}")
    
    print("\n✅ Database Executor Tool testing complete!")

if __name__ == "__main__":
    test_db_executor()