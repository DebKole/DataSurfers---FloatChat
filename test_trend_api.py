import requests
import os
from dotenv import load_dotenv
import sys
from typing import Optional

load_dotenv()

def get_float_id_from_db() -> Optional[str]:
    """Get a valid float_id from the database."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT float_id, COUNT(*) as profile_count 
            FROM argo_profiles 
            WHERE EXISTS (
                SELECT 1 
                FROM argo_measurements 
                WHERE argo_measurements.global_profile_id = argo_profiles.global_profile_id
                AND temperature_adjusted IS NOT NULL
                AND salinity_adjusted IS NOT NULL
            )
            GROUP BY float_id 
            ORDER BY profile_count DESC 
            LIMIT 1;
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            float_id = result[0]
            print(f"🔍 Found float ID in database: {float_id} with {result[1]} valid profiles")
            return float_id
        else:
            print("❌ No valid float IDs found in the database")
            return None
            
    except Exception as e:
        print(f"⚠️ Could not get float ID from database: {e}")
        return None

def test_trend_api():
    base_url = "http://localhost:8000"  # Update if your API runs on a different port
    
    # Get a valid float_id with actual data
    float_id = get_float_id_from_db()
    if not float_id:
        print("❌ No valid float ID available for testing")
        return
    
    try:
        # Test TS curve endpoint
        print(f"\n📊 Testing TS curve for float {float_id}...")
        ts_url = f"{base_url}/api/analysis"
        params = {"type": "ts_curve", "float_id": float_id, "limit": 5}

        print(f"  GET {ts_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
        response = requests.get(ts_url, params=params)
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ❌ Error: {response.text}")
            return
            
        data = response.json()
        
        if 'profiles' in data and data['profiles']:
            print(f"✅ Success! Found {len(data['profiles'])} profiles")
            for i, profile in enumerate(data['profiles'][:2], 1):  # Show first 2 profiles
                print(f"\n  Profile {i}:")
                if 'measurements' in profile and profile['measurements']:
                    print(f"  - Measurements: {len(profile['measurements'])}")
                    # Show first and last measurement
                    first = profile['measurements'][0]
                    last = profile['measurements'][-1]
                    print(f"    First: Salinity={first.get('salinity', 'N/A')}, Temp={first.get('temperature', 'N/A')}°C")
                    print(f"    Last:  Salinity={last.get('salinity', 'N/A')}, Temp={last.get('temperature', 'N/A')}°C")
                else:
                    print("  - No measurements found")
        else:
            print(f"  ❌ Unexpected response format: {data}")
        
        # Test TD curve endpoint
        print(f"\n📊 Testing TD curve for float {float_id}...")
        td_url = f"{base_url}/api/analysis"
        params = {"type": "td_curve", "float_id": float_id, "limit": 5}
        print(f"  GET {td_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
        response = requests.get(td_url, params=params)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success!")
        else:
            print(f"  ❌ Error: {response.text}")
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Testing Trend API endpoints")
    test_trend_api()