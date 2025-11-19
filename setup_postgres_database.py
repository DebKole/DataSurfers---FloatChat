"""
Set up PostgreSQL database for Argo float data
Creates tables, imports CSV data, and sets up indexes
"""

import psycopg2
import pandas as pd
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USERNAME', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'floatchat_argo')
}

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not specific database)
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_CONFIG['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print(f"Database '{DB_CONFIG['database']}' created successfully")
        else:
            print(f"Database '{DB_CONFIG['database']}' already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    
    return True

def create_tables():
    """Create the argo_profiles and argo_measurements tables"""
    
    profiles_table_sql = """
    CREATE TABLE IF NOT EXISTS argo_profiles (
        global_profile_id BIGINT PRIMARY KEY,
        source_file VARCHAR(255) NOT NULL,
        local_profile_id INTEGER NOT NULL,
        float_id VARCHAR(50) NOT NULL,
        cycle_number INTEGER,
        datetime TIMESTAMP,
        latitude DECIMAL(10, 6),
        longitude DECIMAL(10, 6),
        min_pressure DECIMAL(10, 3),
        max_pressure DECIMAL(10, 3),
        measurement_count INTEGER,
        project_name VARCHAR(100),
        institution VARCHAR(255),
        data_mode VARCHAR(10),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    measurements_table_sql = """
    CREATE TABLE IF NOT EXISTS argo_measurements (
        global_profile_id BIGINT NOT NULL,
        level INTEGER NOT NULL,
        pressure DECIMAL(10, 3) NOT NULL,
        temperature DECIMAL(8, 5) NOT NULL,
        salinity DECIMAL(8, 5) NOT NULL,
        latitude DECIMAL(10, 6),
        longitude DECIMAL(10, 6),
        datetime TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        PRIMARY KEY (global_profile_id, level),
        FOREIGN KEY (global_profile_id) REFERENCES argo_profiles(global_profile_id)
    );
    """
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute(profiles_table_sql)
        cursor.execute(measurements_table_sql)
        
        conn.commit()
        print("Tables created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
    
    return True

def create_indexes():
    """Create indexes for optimal query performance"""
    
    indexes_sql = [
        # Spatial queries
        "CREATE INDEX IF NOT EXISTS idx_profiles_location ON argo_profiles(latitude, longitude);",
        "CREATE INDEX IF NOT EXISTS idx_measurements_location ON argo_measurements(latitude, longitude);",
        
        # Temporal queries
        "CREATE INDEX IF NOT EXISTS idx_profiles_datetime ON argo_profiles(datetime);",
        "CREATE INDEX IF NOT EXISTS idx_measurements_datetime ON argo_measurements(datetime);",
        
        # Depth/pressure queries
        "CREATE INDEX IF NOT EXISTS idx_measurements_pressure ON argo_measurements(pressure);",
        
        # Temperature and salinity queries
        "CREATE INDEX IF NOT EXISTS idx_measurements_temp ON argo_measurements(temperature);",
        "CREATE INDEX IF NOT EXISTS idx_measurements_salinity ON argo_measurements(salinity);",
        
        # Float-specific queries
        "CREATE INDEX IF NOT EXISTS idx_profiles_float_id ON argo_profiles(float_id);",
        "CREATE INDEX IF NOT EXISTS idx_profiles_cycle ON argo_profiles(cycle_number);",
        
        # Composite indexes for common query patterns
        "CREATE INDEX IF NOT EXISTS idx_measurements_location_pressure ON argo_measurements(latitude, longitude, pressure);",
        "CREATE INDEX IF NOT EXISTS idx_measurements_temp_depth ON argo_measurements(temperature, pressure);"
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for index_sql in indexes_sql:
            cursor.execute(index_sql)
            print(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
        
        conn.commit()
        print("All indexes created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating indexes: {e}")
        return False
    
    return True

def import_csv_data(csv_dir="./processed_data/"):
    """Import CSV data into PostgreSQL tables"""
    
    profiles_file = os.path.join(csv_dir, "argo_profiles.csv")
    measurements_file = os.path.join(csv_dir, "argo_measurements.csv")
    
    if not os.path.exists(profiles_file) or not os.path.exists(measurements_file):
        print(f"CSV files not found in {csv_dir}")
        print("Please run process_netcdf_to_postgres.py first")
        return False
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("TRUNCATE TABLE argo_measurements CASCADE;")
        cursor.execute("TRUNCATE TABLE argo_profiles CASCADE;")
        
        # Import profiles
        print("Importing profiles data...")
        with open(profiles_file, 'r') as f:
            cursor.copy_expert(
                "COPY argo_profiles (global_profile_id, source_file, local_profile_id, float_id, cycle_number, datetime, latitude, longitude, min_pressure, max_pressure, measurement_count, project_name, institution, data_mode) FROM STDIN WITH CSV HEADER",
                f
            )
        
        # Import measurements
        print("Importing measurements data...")
        with open(measurements_file, 'r') as f:
            cursor.copy_expert(
                "COPY argo_measurements (global_profile_id, level, pressure, temperature, salinity, latitude, longitude, datetime) FROM STDIN WITH CSV HEADER",
                f
            )
        
        conn.commit()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM argo_profiles;")
        profile_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_measurements;")
        measurement_count = cursor.fetchone()[0]
        
        print(f"Data imported successfully:")
        print(f"  Profiles: {profile_count:,} records")
        print(f"  Measurements: {measurement_count:,} records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error importing data: {e}")
        return False
    
    return True

def test_database():
    """Test the database with some sample queries"""
    
    test_queries = [
        ("Total profiles", "SELECT COUNT(*) FROM argo_profiles;"),
        ("Total measurements", "SELECT COUNT(*) FROM argo_measurements;"),
        ("Unique floats", "SELECT COUNT(DISTINCT float_id) FROM argo_profiles;"),
        ("Date range", "SELECT MIN(datetime), MAX(datetime) FROM argo_profiles WHERE datetime IS NOT NULL;"),
        ("Depth range", "SELECT MIN(pressure), MAX(pressure) FROM argo_measurements;"),
        ("Temperature range", "SELECT MIN(temperature), MAX(temperature) FROM argo_measurements;")
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\nDatabase Test Results:")
        print("=" * 40)
        
        for description, query in test_queries:
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"{description}: {result[0] if len(result) == 1 else result}")
        
        # Sample data
        print("\nSample Profile Data:")
        cursor.execute("SELECT global_profile_id, float_id, latitude, longitude, measurement_count FROM argo_profiles LIMIT 3;")
        for row in cursor.fetchall():
            print(f"  Profile {row[0]}: Float {row[1]} at ({row[2]:.2f}, {row[3]:.2f}) with {row[4]} measurements")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error testing database: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("Setting up PostgreSQL database for FloatChat...")
    print("=" * 50)
    
    # Step 1: Create database
    if not create_database():
        return
    
    # Step 2: Create tables
    if not create_tables():
        return
    
    # Step 3: Import data
    if not import_csv_data():
        return
    
    # Step 4: Create indexes
    if not create_indexes():
        return
    
    # Step 5: Test database
    if not test_database():
        return
    
    print("\n" + "=" * 50)
    print("DATABASE SETUP COMPLETE!")
    print("=" * 50)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("Tables: argo_profiles, argo_measurements")
    print("Indexes: Optimized for spatial, temporal, and depth queries")
    print("\nYour FloatChat app can now connect to PostgreSQL!")

if __name__ == "__main__":
    main()