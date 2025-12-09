# test_january_data.py
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

def test_january_data(float_id='1901745'):
    try:
        # Create connection to january_data database
        conn = psycopg2.connect(
            dbname="january_data",  # Changed to january_data
            user="postgres",
            password="parv12345",
            host="localhost",
            port="5432"
        )
        
        print("✅ Successfully connected to the january_data database")
        
        with conn.cursor() as cur:
            # Check if argo_profiles table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'argo_profiles'
                );
            """)
            if not cur.fetchone()[0]:
                print("❌ Error: argo_profiles table does not exist")
                return
                
            # Check if argo_measurements table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'argo_measurements'
                );
            """)
            if not cur.fetchone()[0]:
                print("❌ Error: argo_measurements table does not exist")
                return
            
            # Check profiles count
            cur.execute("""
                SELECT COUNT(*) 
                FROM argo_profiles 
                WHERE float_id = %s
            """, (float_id,))
            profile_count = cur.fetchone()[0]
            print(f"\nFound {profile_count} profiles for float {float_id}")
            
            if profile_count == 0:
                print("\nAvailable float_ids in the database:")
                cur.execute("""
                    SELECT DISTINCT float_id 
                    FROM argo_profiles 
                    LIMIT 10
                """)
                print("Sample float_ids:", [row[0] for row in cur.fetchall()])
                return
            
            # Check measurements count
            cur.execute("""
                SELECT COUNT(*)
                FROM argo_measurements m
                JOIN argo_profiles p ON m.global_profile_id = p.global_profile_id
                WHERE p.float_id = %s
            """, (float_id,))
            measurement_count = cur.fetchone()[0]
            print(f"Found {measurement_count} measurements for float {float_id}")
            
            # Get sample data
            if measurement_count > 0:
                print("\nSample data:")
                cur.execute("""
                    SELECT p.cycle_number, m.level, m.pressure, m.temperature, m.salinity
                    FROM argo_measurements m
                    JOIN argo_profiles p ON m.global_profile_id = p.global_profile_id
                    WHERE p.float_id = %s
                    ORDER BY p.cycle_number, m.level
                    LIMIT 5
                """, (float_id,))
                print("\nCycle | Level | Pressure | Temperature | Salinity")
                print("-" * 50)
                for row in cur.fetchall():
                    print(f"{row[0]:<6} | {row[1]:<5} | {row[2]:<8.2f} | {row[3]:<11.2f} | {row[4]:.2f}")
            
            # Check column names and types
            print("\nTable structure:")
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'argo_measurements'
                ORDER BY ordinal_position
            """)
            print("\nargo_measurements columns:")
            for col in cur.fetchall():
                print(f"  {col[0]:<20} {col[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_january_data()