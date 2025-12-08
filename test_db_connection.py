import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def test_connection():
    try:
        print(f"🔍 Testing connection to database: {os.getenv('DB_NAME')}")
        print(f"Host: {os.getenv('DB_HOST', 'localhost')}")
        print(f"Port: {os.getenv('DB_PORT', '5432')}")
        print(f"User: {os.getenv('DB_USERNAME')}")
        
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        print("✅ Successfully connected to database!")
        
        # Check tables
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print("\n📋 Available tables:")
        for table in tables:
            print(f"- {table[0]}")
            
        # Check argo_profiles count
        cursor.execute("SELECT COUNT(*) FROM argo_profiles;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Number of profiles: {count}")
        
        # Check a sample profile with actual column names
        cursor.execute("""
            SELECT float_id, COUNT(*) as profile_count 
            FROM argo_profiles 
            GROUP BY float_id 
            ORDER BY profile_count DESC 
            LIMIT 5;
        """)
        print("\n🔢 Top 5 float IDs by profile count:")
        for row in cursor.fetchall():
            print(f"- {row[0]}: {row[1]} profiles")
            
        # Check measurements with actual column names
        cursor.execute("""
            SELECT 
                COUNT(*) as total_measurements,
                COUNT(CASE WHEN temperature_adjusted IS NOT NULL THEN 1 END) as non_null_temp,
                COUNT(CASE WHEN salinity_adjusted IS NOT NULL THEN 1 END) as non_null_salinity
            FROM argo_measurements;
        """)
        total, non_null_temp, non_null_salinity = cursor.fetchone()
        print("\n📈 Measurements summary:")
        print(f"  - Total measurements: {total}")
        print(f"  - With temperature: {non_null_temp} ({(non_null_temp/total)*100:.1f}%)")
        print(f"  - With salinity: {non_null_salinity} ({(non_null_salinity/total)*100:.1f}%)")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")

if __name__ == "__main__":
    test_connection()