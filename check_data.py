import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'testing_2025'),
        user=os.getenv('DB_USERNAME', 'postgres'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    cur = conn.cursor()
    
    # Check if float exists in argo_profiles
    cur.execute("""
        SELECT p.float_id, p.global_profile_id, COUNT(m.*) as measurement_count
        FROM argo_profiles p
        LEFT JOIN argo_measurements m ON p.global_profile_id = m.global_profile_id
        WHERE p.float_id = '5907086'
        GROUP BY p.float_id, p.global_profile_id;
    """)
    profiles = cur.fetchall()

    if not profiles:
        print('No profiles found for float_id 5907086')
    else:
        print('Profiles found:')
        for float_id, profile_id, count in profiles:
            print(f'Profile ID: {profile_id}, Measurements: {count}')
            
            # Check for null values with correct column names
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN temperature_adjusted IS NULL THEN 1 END) as null_temp,
                    COUNT(CASE WHEN salinity_adjusted IS NULL THEN 1 END) as null_salinity
                FROM argo_measurements 
                WHERE global_profile_id = %s;
            """, (profile_id,))
            total, null_temp, null_salinity = cur.fetchone()
            print(f'  - Total measurements: {total}')
            print(f'  - Null temperatures: {null_temp}')
            print(f'  - Null salinity: {null_salinity}')
            
            # Show sample data
            if total > 0:
                cur.execute("""
                    SELECT temperature_adjusted, salinity_adjusted
                    FROM argo_measurements
                    WHERE global_profile_id = %s
                    AND temperature_adjusted IS NOT NULL
                    AND salinity_adjusted IS NOT NULL
                    LIMIT 5;
                """, (profile_id,))
                print("\nSample measurements (temperature_adjusted, salinity_adjusted):")
                for temp, sal in cur.fetchall():
                    print(f"  - Temp: {temp}, Salinity: {sal}")

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    if 'conn' in locals():
        conn.close()