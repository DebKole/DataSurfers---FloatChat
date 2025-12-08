import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "argo_indian_ocean_25")

# Try connecting with the env password first
print(f"Attempting connection to {DB_NAME} with password from .env...")
try:
    db_url = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)
    
    query = text("SELECT count(*) FROM argo_profiles WHERE float_id = '1901910'")
    with engine.connect() as conn:
        result = conn.execute(query).scalar()
        print(f"Connection successful! Count of profiles for float 1901910: {result}")
        
        if result > 0:
            print("Float found!")
            # Check measurements
            m_query = text("""
            SELECT count(*) 
            FROM argo_measurements m 
            JOIN argo_profiles p ON m.global_profile_id = p.global_profile_id 
            WHERE p.float_id = '1901910'
            """)
            m_result = conn.execute(m_query).scalar()
            print(f"Count of measurements for float 1901910: {m_result}")
        else:
            print("Float NOT found in this database.")
            
except Exception as e:
    print(f"Connection failed: {e}")
    
    # Fallback: Try with 'parv12345'
    print("\nAttempting connection with fallback password 'parv12345'...")
    try:
        db_url = f"postgresql+psycopg2://{DB_USERNAME}:parv12345@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            result = conn.execute(query).scalar()
            print(f"Connection successful! Count of profiles for float 1901910: {result}")
    except Exception as e2:
        print(f"Fallback connection failed: {e2}")
