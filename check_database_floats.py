#!/usr/bin/env python3
"""
Check what float data exists in the database
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USERNAME', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'floatchat_argo')
}

print("=" * 70)
print("DATABASE FLOAT DATA CHECK")
print("=" * 70)

try:
    conn = psycopg2.connect(**db_config)
    print(f"✓ Connected to database: {db_config['database']}")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check if tables exist
        print("\n1. Checking tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('argo_profiles', 'argo_measurements')
        """)
        tables = cur.fetchall()
        print(f"   Tables found: {[t['table_name'] for t in tables]}")
        
        if not tables:
            print("   ⚠️  No Argo tables found!")
            print("   Run: python setup_postgres_database.py")
            exit(1)
        
        # Check profile count
        print("\n2. Checking profile data...")
        cur.execute("SELECT COUNT(*) as count FROM argo_profiles")
        profile_count = cur.fetchone()['count']
        print(f"   Total profiles: {profile_count:,}")
        
        if profile_count == 0:
            print("   ⚠️  No profiles in database!")
            print("   Run: python process_netcdf_to_postgres.py")
            print("   Then: python setup_postgres_database.py")
            exit(1)
        
        # Check date range
        print("\n3. Checking date range...")
        cur.execute("""
            SELECT 
                MIN(datetime) as min_date,
                MAX(datetime) as max_date
            FROM argo_profiles
            WHERE datetime IS NOT NULL
        """)
        dates = cur.fetchone()
        print(f"   Date range: {dates['min_date']} to {dates['max_date']}")
        
        # Check geographic distribution
        print("\n4. Checking geographic distribution...")
        cur.execute("""
            SELECT 
                MIN(latitude) as min_lat,
                MAX(latitude) as max_lat,
                MIN(longitude) as min_lon,
                MAX(longitude) as max_lon,
                COUNT(*) as count
            FROM argo_profiles
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)
        geo = cur.fetchone()
        print(f"   Latitude range: {geo['min_lat']:.2f}° to {geo['max_lat']:.2f}°")
        print(f"   Longitude range: {geo['min_lon']:.2f}° to {geo['max_lon']:.2f}°")
        print(f"   Profiles with location: {geo['count']:,}")
        
        # Determine region
        if geo['min_lat'] and geo['max_lat']:
            avg_lat = (float(geo['min_lat']) + float(geo['max_lat'])) / 2
            avg_lon = (float(geo['min_lon']) + float(geo['max_lon'])) / 2
            
            print(f"\n   Center point: ({avg_lat:.2f}°, {avg_lon:.2f}°)")
            
            # Identify region
            if -40 <= avg_lat <= 30 and 20 <= avg_lon <= 120:
                region = "Indian Ocean"
            elif 60 <= avg_lat <= 80 and -80 <= avg_lon <= -20:
                region = "North Atlantic / Greenland"
            elif -60 <= avg_lat <= 60 and 120 <= avg_lon or avg_lon <= -80:
                region = "Pacific Ocean"
            else:
                region = "Other"
            
            print(f"   Detected region: {region}")
        
        # Check unique floats
        print("\n5. Checking unique floats...")
        cur.execute("""
            SELECT COUNT(DISTINCT float_id) as count
            FROM argo_profiles
            WHERE float_id IS NOT NULL AND float_id != 'unknown'
        """)
        float_count = cur.fetchone()['count']
        print(f"   Unique floats: {float_count}")
        
        # Show sample floats
        print("\n6. Sample float data...")
        cur.execute("""
            SELECT 
                float_id,
                latitude,
                longitude,
                datetime,
                measurement_count
            FROM argo_profiles
            WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL
                AND float_id IS NOT NULL
            ORDER BY datetime DESC
            LIMIT 5
        """)
        samples = cur.fetchall()
        
        for i, sample in enumerate(samples, 1):
            print(f"   {i}. Float {sample['float_id']}: "
                  f"({sample['latitude']:.2f}°, {sample['longitude']:.2f}°) "
                  f"- {sample['datetime']} - {sample['measurement_count']} measurements")
        
        # Check January 2025 data specifically
        print("\n7. Checking January 2025 data...")
        cur.execute("""
            SELECT COUNT(*) as count
            FROM argo_profiles
            WHERE datetime >= '2025-01-01' AND datetime < '2025-02-01'
        """)
        jan_count = cur.fetchone()['count']
        print(f"   January 2025 profiles: {jan_count:,}")
        
        if jan_count == 0:
            print("   ⚠️  No January 2025 data found!")
            print("   Your data is from a different time period.")
            print("   Update the date filter in float_location_service.py")
        
        # Recommendations
        print("\n" + "=" * 70)
        print("RECOMMENDATIONS")
        print("=" * 70)
        
        if region == "North Atlantic / Greenland":
            print("✓ Your data is from Greenland/North Atlantic region")
            print("  Update float_location_service.py:")
            print("  - Change date filter to match your data range")
            print("  - Update get_indian_ocean_floats() to get_north_atlantic_floats()")
            print("  - Change bounds: lat [60, 80], lon [-80, -20]")
        elif region == "Indian Ocean":
            print("✓ Your data is from Indian Ocean region")
            print("  The service should work as-is")
        else:
            print(f"✓ Your data is from {region}")
            print("  Update the geographic bounds in float_location_service.py")
        
        if jan_count == 0 and dates['max_date']:
            print(f"\n✓ Your data is from {dates['min_date']} to {dates['max_date']}")
            print("  Update date filters in queries to match this range")
        
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nCheck your .env file:")
    print("  DB_HOST=localhost")
    print("  DB_PORT=5432")
    print("  DB_USERNAME=postgres")
    print("  DB_PASSWORD=your_password")
    print("  DB_NAME=floatchat_argo")

print("\n" + "=" * 70)
