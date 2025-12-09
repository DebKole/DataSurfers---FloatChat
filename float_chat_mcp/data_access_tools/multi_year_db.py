"""
Multi-year Argo float data access module.
Handles database connections and queries across multiple years of Argo float data.
"""
from typing import Dict, List, Any, Optional, Union
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiYearArgoDB:
    """
    A class to handle database operations across multiple years of Argo float data.
    """
    
    def __init__(self, db_config: Optional[Dict] = None):
        """
        Initialize the MultiYearArgoDB with database configuration.
        
        Args:
            db_config: Dictionary containing database configuration.
                If None, will use environment variables.
        """
        if db_config is None:
            self.db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'user': os.getenv('DB_USERNAME', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'databases': {
                    '2021': os.getenv('DB_NAME_2021', 'argo_indian_ocean_21'),
                    '2022': os.getenv('DB_NAME_2022', 'argo_indian_ocean_22'),
                    '2023': os.getenv('DB_NAME_2023', 'argo_indian_ocean_23'),
                    '2024': os.getenv('DB_NAME_2024', 'argo_indian_ocean_24'),
                    '2025': os.getenv('DB_NAME_2025', 'argo_indian_ocean_25')
                }
            }
        else:
            self.db_config = db_config
            
        self.engines = self._create_engines()
        
    def _create_engines(self) -> Dict[str, Any]:
        """Create SQLAlchemy engines for each database year."""
        engines = {}
        for year, db_name in self.db_config['databases'].items():
            try:
                url = (
                    f"postgresql://{self.db_config['user']}:"
                    f"{self.db_config['password']}@{self.db_config['host']}:"
                    f"{self.db_config['port']}/{db_name}"
                )
                engines[year] = create_engine(url)
                # Test connection
                with engines[year].connect() as conn:
                    conn.execute(text('SELECT 1'))
                logger.info(f"Successfully connected to {db_name}")
            except Exception as e:
                logger.warning(f"Failed to connect to {db_name}: {e}")
        return engines
    
    def query_single_year(self, year: str, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Execute a query on a single year's database.
        
        Args:
            year: The year to query (as string, e.g., '2021')
            query: SQL query to execute
            params: Dictionary of parameters for the query
            
        Returns:
            List of dictionaries containing query results
        """
        if year not in self.engines:
            logger.error(f"No database connection for year {year}")
            return []
            
        try:
            with self.engines[year].connect() as conn:
                df = pd.read_sql(query, conn, params=params)
                return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error querying {year} database: {e}")
            return []
    
    def query_all_years(self, query: str, params: Optional[Dict] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute a query across all available years in parallel.
        
        Args:
            query: SQL query to execute
            params: Dictionary of parameters for the query
            
        Returns:
            Dictionary with years as keys and query results as values
        """
        results = {}
        with ThreadPoolExecutor() as executor:
            # Create a partial function with fixed query and params
            query_func = partial(self.query_single_year, query=query, params=params)
            # Submit all queries in parallel
            future_to_year = {executor.submit(query_func, year): year for year in self.engines}
            
            # Collect results as they complete
            for future in future_to_year:
                year = future_to_year[future]
                try:
                    results[year] = future.result()
                except Exception as e:
                    logger.error(f"Error executing query for year {year}: {e}")
                    results[year] = []
        
        return results
    
    def get_floats_in_region(self, lat: float, lon: float, radius_km: float, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get floats within a specified radius from a center point across all years.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Radius in kilometers
            limit: Maximum number of results per year
            
        Returns:
            List of unique floats with their details
        """
        query = """
        WITH nearby_floats AS (
            SELECT DISTINCT float_id, 
                   MIN(datetime) as first_seen,
                   MAX(datetime) as last_seen,
                   COUNT(DISTINCT global_profile_id) as profile_count,
                   AVG(latitude) as avg_lat,
                   AVG(longitude) as avg_lon
            FROM argo_measurements
            WHERE ST_DWithin(
                ST_MakePoint(longitude, latitude)::geography,
                ST_MakePoint(:lon, :lat)::geography,
                :radius_km * 1000
            )
            GROUP BY float_id
            ORDER BY MIN(datetime)
            LIMIT :limit
        )
        SELECT * FROM nearby_floats
        """
        
        params = {
            'lat': lat,
            'lon': lon,
            'radius_km': radius_km,
            'limit': limit
        }
        
        # Get results from all years
        yearly_results = self.query_all_years(query, params)
        
        # Combine and deduplicate results
        return self.combine_yearly_results(yearly_results)
    
    @staticmethod
    def combine_yearly_results(yearly_results: Dict[str, List[Dict[str, Any]]], 
                             key_column: str = 'float_id') -> List[Dict[str, Any]]:
        """
        Combine results from multiple years, handling duplicates.
        
        Args:
            yearly_results: Dictionary of {year: results}
            key_column: Column to use for identifying duplicates
            
        Returns:
            Combined list of unique items with year information
        """
        seen = set()
        combined = []
        
        # Process years in order
        for year in sorted(yearly_results.keys()):
            for item in yearly_results[year]:
                item_id = str(item.get(key_column))
                if item_id and item_id not in seen:
                    seen.add(item_id)
                    # Add year information to the result
                    combined.append({
                        **item,
                        'first_seen_year': year,
                        'source_years': [year]  # Track all years this float appears in
                    })
                elif item_id in seen:
                    # Update existing entry with additional year info
                    for existing in combined:
                        if str(existing.get(key_column)) == item_id:
                            existing['source_years'].append(year)
                            # Update last_seen if this is a more recent sighting
                            if 'last_seen' in item and 'last_seen' in existing:
                                if item['last_seen'] > existing['last_seen']:
                                    existing['last_seen'] = item['last_seen']
                            break
        
        return combined
    
    def get_float_timeseries(self, float_id: str, parameter: str = 'temperature', 
                           start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get time series data for a specific float across all years.
        
        Args:
            float_id: The float ID to get data for
            parameter: The parameter to retrieve ('temperature', 'salinity', etc.)
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with the time series data
        """
        query = """
        SELECT 
            datetime, 
            latitude, 
            longitude,
            depth,
            """ + parameter + """ as value,
            '{}' as year
        FROM argo_measurements
        WHERE float_id = :float_id
        """
        
        params = {'float_id': float_id}
        
        if start_date:
            query += " AND datetime >= :start_date"
            params['start_date'] = start_date
            
        if end_date:
            query += " AND datetime <= :end_date"
            params['end_date'] = end_date
            
        query += " ORDER BY datetime"
        
        # Get results from all years
        all_data = []
        for year, engine in self.engines.items():
            try:
                with engine.connect() as conn:
                    year_query = query.format(year)
                    df = pd.read_sql(year_query, conn, params=params)
                    if not df.empty:
                        all_data.append(df)
            except Exception as e:
                logger.warning(f"Error getting data for {year}: {e}")
        
        if not all_data:
            return pd.DataFrame()
            
        # Combine all years' data
        combined = pd.concat(all_data, ignore_index=True)
        combined['datetime'] = pd.to_datetime(combined['datetime'])
        return combined.sort_values('datetime')


# Create a singleton instance for convenience
multi_year_db = MultiYearArgoDB()
