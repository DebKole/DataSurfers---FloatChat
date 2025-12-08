import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = "argo_indian_ocean_25"

print(f"Connecting to {DB_NAME}...")
try:
    db_url = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Get columns of argo_measurements
        print("\nColumns in argo_measurements:")
        query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'argo_measurements'
            ORDER BY ordinal_position
        """)
        columns = conn.execute(query).fetchall()
        for col in columns:
            print(f"- {col[0]} ({col[1]})")
            
        # Check data in temperature vs temperature_adjusted
        print("\nChecking data content for float 1901910:")
        check_query = text("""
            SELECT 
                m.pressure, m.pressure_adjusted,
                m.temperature, m.temperature_adjusted,
                m.salinity, m.salinity_adjusted
            FROM argo_measurements m
            JOIN argo_profiles p ON m.global_profile_id = p.global_profile_id
            WHERE p.float_id = '1901910'
            LIMIT 5
        """)
        try:
            rows = conn.execute(check_query).fetchall()
            if rows:
                print("Sample rows:")
                for row in rows:
                    print(row)
            else:
                print("No rows returned for this float.")
        except Exception as e:
            print(f"Error querying data: {e}")

except Exception as e:
    print(f"Connection failed: {e}")
