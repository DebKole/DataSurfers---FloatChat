# save this as check_float_data.py
import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

def check_float_data(float_id):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        # Get profile count for this float
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM argo_profiles 
                WHERE float_id = %s
            """, (float_id,))
            profile_count = cur.fetchone()[0]
            print(f"📊 Found {profile_count} profiles for float {float_id}")
            
            # Get sample of measurements
            cur.execute("""
                SELECT 
                    p.global_profile_id,
                    p.datetime,
                    COUNT(m.measurement_id) as measurement_count,
                    COUNT(CASE WHEN m.temperature_adjusted IS NOT NULL THEN 1 END) as temp_count,
                    COUNT(CASE WHEN m.salinity_adjusted IS NOT NULL THEN 1 END) as salinity_count
                FROM argo_profiles p
                LEFT JOIN argo_measurements m ON p.global_profile_id = m.global_profile_id
                WHERE p.float_id = %s
                GROUP BY p.global_profile_id, p.date_time
                LIMIT 5
            """, (float_id,))
            
            print("\nSample profiles and measurements:")
            for row in cur.fetchall():
                print(f"\nProfile: {row[0]}")
                print(f"Date: {row[1]}")
                print(f"Total measurements: {row[2]}")
                print(f"With temperature: {row[3]}")
                print(f"With salinity: {row[4]}")
                
                # Get min/max values
                cur.execute("""
                    SELECT 
                        MIN(temperature_adjusted) as min_temp,
                        MAX(temperature_adjusted) as max_temp,
                        MIN(salinity_adjusted) as min_salinity,
                        MAX(salinity_adjusted) as max_salinity
                    FROM argo_measurements
                    WHERE global_profile_id = %s
                """, (row[0],))
                min_temp, max_temp, min_salinity, max_salinity = cur.fetchone()
                print(f"Temperature range: {min_temp} to {max_temp} °C")
                print(f"Salinity range: {min_salinity} to {max_salinity} PSU")
                
        # Create a simple TS plot for the first profile
        with conn.cursor() as cur:
            cur.execute("""
                SELECT temperature_adjusted, salinity_adjusted
                FROM argo_measurements
                WHERE global_profile_id IN (
                    SELECT global_profile_id 
                    FROM argo_profiles 
                    WHERE float_id = %s
                    LIMIT 1
                )
                AND temperature_adjusted IS NOT NULL
                AND salinity_adjusted IS NOT NULL
                ORDER BY pressure
            """, (float_id,))
            
            data = cur.fetchall()
            if data:
                df = pd.DataFrame(data, columns=['temperature', 'salinity'])
                plt.figure(figsize=(10, 6))
                plt.scatter(df['salinity'], df['temperature'], c=df.index, cmap='viridis')
                plt.colorbar(label='Measurement index')
                plt.xlabel('Salinity (PSU)')
                plt.ylabel('Temperature (°C)')
                plt.title(f'TS Diagram for float {float_id}')
                plt.grid(True)
                plt.savefig(f'ts_diagram_{float_id}.png')
                print(f"\n✅ Saved TS diagram to ts_diagram_{float_id}.png")
            else:
                print("\n❌ No valid temperature/salinity data found for plotting")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    float_id = "6903139"  # The float ID from the error
    check_float_data(float_id)