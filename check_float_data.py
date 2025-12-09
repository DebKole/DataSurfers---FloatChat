# save this as check_float_data.py
import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

def check_float_data(float_id):
    try:
        # Connect to the main database which has the FDW views
        db_name = 'argo_indian_ocean_25'
        print(f"🔌 Connecting to database: {db_name}")
        
        conn = psycopg2.connect(
            dbname=db_name,
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        # Get profile count for this float using the ALL YEARS view
        with conn.cursor() as cur:
            print(f"🔍 Checking float {float_id} in all_years_argo_profiles...")
            cur.execute("""
                SELECT COUNT(*) 
                FROM all_years_argo_profiles 
                WHERE float_id = %s
            """, (float_id,))
            profile_count = cur.fetchone()[0]
            print(f"📊 Found {profile_count} profiles for float {float_id} (all years)")
            
            if profile_count == 0:
                print("⚠️ No profiles found. Checking if float exists in any specific year database...")
                # Optional: Check individual years if view is empty (debugging FDW)
                # For now, just exit
                return

            # Get sample of measurements
            print("\n🔍 Fetching sample profiles (2022-2023 focus)...")
            cur.execute("""
                SELECT 
                    p.global_profile_id,
                    p.datetime,
                    COUNT(*) as measurement_count,
                    COUNT(CASE WHEN m.temperature_adjusted IS NOT NULL THEN 1 END) as temp_count,
                    COUNT(CASE WHEN m.salinity_adjusted IS NOT NULL THEN 1 END) as salinity_count
                FROM all_years_argo_profiles p
                LEFT JOIN all_years_argo_measurements m ON p.global_profile_id = m.global_profile_id
                WHERE p.float_id = %s
                AND p.datetime >= '2022-01-01' AND p.datetime <= '2023-12-31'
                GROUP BY p.global_profile_id, p.datetime
                ORDER BY p.datetime DESC
                LIMIT 5
            """, (float_id,))
            
            rows = cur.fetchall()
            if not rows:
                print("⚠️ No profiles found specifically in 2022-2023.")
                print("Fetching most recent profiles instead:")
                cur.execute("""
                    SELECT 
                        p.global_profile_id,
                        p.datetime,
                        COUNT(*) as measurement_count,
                        COUNT(CASE WHEN m.temperature_adjusted IS NOT NULL THEN 1 END) as temp_count,
                        COUNT(CASE WHEN m.salinity_adjusted IS NOT NULL THEN 1 END) as salinity_count
                    FROM all_years_argo_profiles p
                    LEFT JOIN all_years_argo_measurements m ON p.global_profile_id = m.global_profile_id
                    WHERE p.float_id = %s
                    GROUP BY p.global_profile_id, p.datetime
                    ORDER BY p.datetime DESC
                    LIMIT 5
                """, (float_id,))
                rows = cur.fetchall()

            print("\nSample profiles and measurements:")
            for row in rows:
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
                    FROM all_years_argo_measurements
                    WHERE global_profile_id = %s
                """, (row[0],))
                min_temp, max_temp, min_salinity, max_salinity = cur.fetchone()
                print(f"Temperature range: {min_temp} to {max_temp} °C")
                print(f"Salinity range: {min_salinity} to {max_salinity} PSU")
                
        # Create a simple TS plot for the first profile found
        if rows:
            first_profile_id = rows[0][0]
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT temperature_adjusted, salinity_adjusted, pressure_adjusted
                    FROM all_years_argo_measurements
                    WHERE global_profile_id = %s
                    AND temperature_adjusted IS NOT NULL
                    AND salinity_adjusted IS NOT NULL
                    ORDER BY pressure_adjusted
                """, (first_profile_id,))
                
                data = cur.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=['temperature', 'salinity', 'pressure'])
                    plt.figure(figsize=(10, 6))
                    plt.scatter(df['salinity'], df['temperature'], c=df['pressure'], cmap='viridis')
                    plt.colorbar(label='Pressure (dbar)')
                    plt.xlabel('Salinity (PSU)')
                    plt.ylabel('Temperature (°C)')
                    plt.title(f'TS Diagram for float {float_id} (Profile {first_profile_id})')
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
    float_id = "1901744"    # Test with the float ID from the user's query
    check_float_data('1901764')