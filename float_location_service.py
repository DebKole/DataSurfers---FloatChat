"""
Float Location Service
Fetches real Argo float locations from the database within a specified radius
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import math

load_dotenv()

class FloatLocationService:
    """Service to fetch and filter Argo float locations from database"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME', 'floatchat_argo')
        }
    
    def _connect(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_config)
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth (in km)
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        r = 6371
        
        return c * r
    
    def get_floats_in_radius(
        self, 
        center_lat: float, 
        center_lon: float, 
        radius_km: float = 10,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all floats within a specified radius from a center point
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers (default: 10km)
            limit: Maximum number of floats to return
            
        Returns:
            List of float locations with metadata
        """
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get unique float locations (latest position for each float)
                query = """
                WITH latest_profiles AS (
                    SELECT DISTINCT ON (float_id)
                        float_id,
                        latitude,
                        longitude,
                        datetime,
                        global_profile_id,
                        cycle_number,
                        measurement_count
                    FROM argo_profiles
                    WHERE latitude IS NOT NULL 
                        AND longitude IS NOT NULL
                        AND datetime >= '2025-01-01'  -- January 2025 data
                    ORDER BY float_id, datetime DESC
                )
                SELECT 
                    float_id,
                    latitude,
                    longitude,
                    datetime,
                    global_profile_id,
                    cycle_number,
                    measurement_count
                FROM latest_profiles
                WHERE latitude BETWEEN %s AND %s
                    AND longitude BETWEEN %s AND %s
                LIMIT %s
                """
                
                # Calculate bounding box (approximate, for initial filtering)
                # 1 degree latitude ≈ 111 km
                # 1 degree longitude ≈ 111 km * cos(latitude)
                lat_delta = radius_km / 111.0
                lon_delta = radius_km / (111.0 * math.cos(math.radians(float(center_lat))))
                
                min_lat = float(center_lat) - lat_delta
                max_lat = float(center_lat) + lat_delta
                min_lon = float(center_lon) - lon_delta
                max_lon = float(center_lon) + lon_delta
                
                cur.execute(query, (min_lat, max_lat, min_lon, max_lon, limit * 2))
                results = cur.fetchall()
                
                # Filter by exact distance using Haversine formula
                floats_in_radius = []
                for row in results:
                    distance = self.haversine_distance(
                        center_lat, center_lon,
                        float(row['latitude']), float(row['longitude'])
                    )
                    
                    if distance <= radius_km:
                        float_data = dict(row)
                        float_data['distance_km'] = round(distance, 2)
                        floats_in_radius.append(float_data)
                
                # Sort by distance and limit
                floats_in_radius.sort(key=lambda x: x['distance_km'])
                return floats_in_radius[:limit]
                
        finally:
            conn.close()
    
    def get_float_with_measurements(
        self, 
        float_id: str, 
        depth_range: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed float information including recent measurements
        
        Args:
            float_id: Float identifier
            depth_range: Optional tuple of (min_pressure, max_pressure)
            
        Returns:
            Dictionary with float profile and measurements
        """
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get latest profile for this float
                profile_query = """
                SELECT *
                FROM argo_profiles
                WHERE float_id = %s
                    AND datetime >= '2025-01-01'
                ORDER BY datetime DESC
                LIMIT 1
                """
                cur.execute(profile_query, (float_id,))
                profile = cur.fetchone()
                
                if not profile:
                    return None
                
                # Get measurements for this profile
                if depth_range:
                    measurements_query = """
                    SELECT *
                    FROM argo_measurements
                    WHERE global_profile_id = %s
                        AND pressure BETWEEN %s AND %s
                    ORDER BY pressure
                    LIMIT 100
                    """
                    cur.execute(measurements_query, (profile['global_profile_id'], depth_range[0], depth_range[1]))
                else:
                    measurements_query = """
                    SELECT *
                    FROM argo_measurements
                    WHERE global_profile_id = %s
                    ORDER BY pressure
                    LIMIT 100
                    """
                    cur.execute(measurements_query, (profile['global_profile_id'],))
                
                measurements = cur.fetchall()
                
                return {
                    'profile': dict(profile),
                    'measurements': [dict(m) for m in measurements]
                }
                
        finally:
            conn.close()
    
    def get_indian_ocean_floats(self, radius_km: float = 10, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get floats in the Indian Ocean region
        
        Indian Ocean approximate bounds:
        - Latitude: -40° to 30°
        - Longitude: 20° to 120°
        
        Args:
            radius_km: Radius for clustering nearby floats
            limit: Maximum number of floats
            
        Returns:
            List of float locations
        """
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                WITH latest_profiles AS (
                    SELECT DISTINCT ON (float_id)
                        float_id,
                        latitude,
                        longitude,
                        datetime,
                        global_profile_id,
                        cycle_number,
                        measurement_count
                    FROM argo_profiles
                    WHERE latitude IS NOT NULL 
                        AND longitude IS NOT NULL
                        AND datetime >= '2025-01-01'
                        AND latitude BETWEEN -40 AND 30
                        AND longitude BETWEEN 20 AND 120
                    ORDER BY float_id, datetime DESC
                )
                SELECT 
                    float_id,
                    latitude,
                    longitude,
                    datetime,
                    global_profile_id,
                    cycle_number,
                    measurement_count
                FROM latest_profiles
                ORDER BY datetime DESC
                LIMIT %s
                """
                
                cur.execute(query, (limit,))
                results = cur.fetchall()
                
                return [dict(row) for row in results]
                
        finally:
            conn.close()
    
    def get_all_active_floats(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all active floats from January 2025 data
        
        Args:
            limit: Maximum number of floats
            
        Returns:
            List of float locations
        """
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                WITH latest_profiles AS (
                    SELECT DISTINCT ON (float_id)
                        float_id,
                        latitude,
                        longitude,
                        datetime,
                        global_profile_id,
                        cycle_number,
                        measurement_count
                    FROM argo_profiles
                    WHERE latitude IS NOT NULL 
                        AND longitude IS NOT NULL
                        AND datetime >= '2025-01-01'
                    ORDER BY float_id, datetime DESC
                )
                SELECT 
                    float_id,
                    latitude,
                    longitude,
                    datetime,
                    global_profile_id,
                    cycle_number,
                    measurement_count
                FROM latest_profiles
                ORDER BY datetime DESC
                LIMIT %s
                """
                
                cur.execute(query, (limit,))
                results = cur.fetchall()
                
                return [dict(row) for row in results]
                
        finally:
            conn.close()
    
    def get_trajectories_in_radius(
        self, 
        center_lat: float, 
        center_lon: float, 
        radius_km: float = 10,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get trajectory data (all positions over time) for floats within radius
        Returns all profiles for each float to show movement path
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers
            limit: Maximum number of floats (not profiles)
            
        Returns:
            List of trajectory points with format:
            {
                "profileId": global_profile_id,
                "lat": latitude,
                "lon": longitude,
                "floatId": float_id,
                "cycleNumber": cycle_number,
                "datetime": datetime
            }
        """
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Step 1: Get floats within radius (latest position)
                lat_delta = radius_km / 111.0
                lon_delta = radius_km / (111.0 * math.cos(math.radians(float(center_lat))))
                
                min_lat = float(center_lat) - lat_delta
                max_lat = float(center_lat) + lat_delta
                min_lon = float(center_lon) - lon_delta
                max_lon = float(center_lon) + lon_delta
                
                # Get floats within bounding box
                floats_query = """
                WITH latest_profiles AS (
                    SELECT DISTINCT ON (float_id)
                        float_id,
                        latitude,
                        longitude
                    FROM argo_profiles
                    WHERE latitude IS NOT NULL 
                        AND longitude IS NOT NULL
                        AND datetime >= '2025-01-01'
                        AND latitude BETWEEN %s AND %s
                        AND longitude BETWEEN %s AND %s
                    ORDER BY float_id, datetime DESC
                )
                SELECT float_id, latitude, longitude
                FROM latest_profiles
                LIMIT %s
                """
                
                cur.execute(floats_query, (min_lat, max_lat, min_lon, max_lon, limit * 2))
                candidate_floats = cur.fetchall()
                
                # Filter by exact distance
                floats_in_radius = []
                for row in candidate_floats:
                    distance = self.haversine_distance(
                        center_lat, center_lon,
                        float(row['latitude']), float(row['longitude'])
                    )
                    if distance <= radius_km:
                        floats_in_radius.append(row['float_id'])
                
                if not floats_in_radius:
                    return []
                
                # Limit to requested number of floats
                floats_in_radius = floats_in_radius[:limit]
                
                # Step 2: Get ALL profiles for these floats (trajectory data)
                trajectory_query = """
                SELECT 
                    global_profile_id as "profileId",
                    latitude as lat,
                    longitude as lon,
                    float_id as "floatId",
                    cycle_number as "cycleNumber",
                    datetime
                FROM argo_profiles
                WHERE float_id = ANY(%s)
                    AND latitude IS NOT NULL
                    AND longitude IS NOT NULL
                    AND datetime >= '2025-01-01'
                ORDER BY float_id, datetime
                """
                
                cur.execute(trajectory_query, (floats_in_radius,))
                trajectories = cur.fetchall()
                
                # Convert to list of dicts with proper format
                result = []
                for row in trajectories:
                    result.append({
                        "profileId": row['profileId'],
                        "lat": float(row['lat']),
                        "lon": float(row['lon']),
                        "floatId": row['floatId'],
                        "cycleNumber": row['cycleNumber'],
                        "datetime": str(row['datetime']) if row['datetime'] else None
                    })
                
                return result
                
        finally:
            conn.close()


# Test function
def test_float_location_service():
    """Test the float location service"""
    print("🧪 Testing Float Location Service\n")
    
    service = FloatLocationService()
    
    # Test 1: Get all Indian Ocean floats
    print("1. Getting Indian Ocean floats...")
    indian_ocean_floats = service.get_indian_ocean_floats(limit=10)
    print(f"   Found {len(indian_ocean_floats)} floats in Indian Ocean")
    if indian_ocean_floats:
        print(f"   Sample: Float {indian_ocean_floats[0]['float_id']} at "
              f"({indian_ocean_floats[0]['latitude']:.2f}, {indian_ocean_floats[0]['longitude']:.2f})")
    
    # Test 2: Get floats within radius
    if indian_ocean_floats:
        center_float = indian_ocean_floats[0]
        print(f"\n2. Getting floats within 10km of Float {center_float['float_id']}...")
        nearby_floats = service.get_floats_in_radius(
            center_float['latitude'],
            center_float['longitude'],
            radius_km=10
        )
        print(f"   Found {len(nearby_floats)} floats within 10km")
        for f in nearby_floats[:3]:
            print(f"   - Float {f['float_id']}: {f['distance_km']}km away")
    
    # Test 3: Get all active floats
    print("\n3. Getting all active floats...")
    all_floats = service.get_all_active_floats(limit=20)
    print(f"   Found {len(all_floats)} active floats")
    
    print("\n✅ Float Location Service test complete!")


if __name__ == "__main__":
    test_float_location_service()
