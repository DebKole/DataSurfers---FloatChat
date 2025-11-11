"""
Set up live PostgreSQL database for real-time Argo float data
Separate from main development database
"""

import psycopg2
import pandas as pd
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Live database configuration
LIVE_DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USERNAME', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'database': 'floatchat_argo_live'  # Separate live database
}

def create_live_database():
    """Create the live database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not specific database)
        conn = psycopg2.connect(
            host=LIVE_DB_CONFIG['host'],
            port=LIVE_DB_CONFIG['port'],
            user=LIVE_DB_CONFIG['user'],
            password=LIVE_DB_CONFIG['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (LIVE_DB_CONFIG['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {LIVE_DB_CONFIG['database']}")
            print(f"✅ Live database '{LIVE_DB_CONFIG['database']}' created successfully")
        else:
            print(f"✅ Live database '{LIVE_DB_CONFIG['database']}' already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating live database: {e}")
        return False
    
    return True

def create_live_tables():
    """Create the argo_profiles and argo_measurements tables in live database"""
    
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # Create automation tracking table
    automation_table_sql = """
    CREATE TABLE IF NOT EXISTS automation_log (
        id SERIAL PRIMARY KEY,
        run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        files_checked INTEGER DEFAULT 0,
        files_downloaded INTEGER DEFAULT 0,
        files_processed INTEGER DEFAULT 0,
        profiles_added INTEGER DEFAULT 0,
        measurements_added INTEGER DEFAULT 0,
        status VARCHAR(50) DEFAULT 'running',
        error_message TEXT,
        duration_seconds DECIMAL(10, 2),
        data_source VARCHAR(100)
    );
    """
    
    try:
        conn = psycopg2.connect(**LIVE_DB_CONFIG)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute(profiles_table_sql)
        cursor.execute(measurements_table_sql)
        cursor.execute(automation_table_sql)
        
        conn.commit()
        print("✅ Live database tables created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating live tables: {e}")
        return False
    
    return True

def create_live_indexes():
    """Create indexes for optimal query performance in live database"""
    
    indexes_sql = [
        # Spatial queries
        "CREATE INDEX IF NOT EXISTS idx_live_profiles_location ON argo_profiles(latitude, longitude);",
        "CREATE INDEX IF NOT EXISTS idx_live_measurements_location ON argo_measurements(latitude, longitude);",
        
        # Temporal queries
        "CREATE INDEX IF NOT EXISTS idx_live_profiles_datetime ON argo_profiles(datetime);",
        "CREATE INDEX IF NOT EXISTS idx_live_measurements_datetime ON argo_measurements(datetime);",
        "CREATE INDEX IF NOT EXISTS idx_live_profiles_updated ON argo_profiles(updated_at);",
        
        # Depth/pressure queries
        "CREATE INDEX IF NOT EXISTS idx_live_measurements_pressure ON argo_measurements(pressure);",
        
        # Temperature and salinity queries
        "CREATE INDEX IF NOT EXISTS idx_live_measurements_temp ON argo_measurements(temperature);",
        "CREATE INDEX IF NOT EXISTS idx_live_measurements_salinity ON argo_measurements(salinity);",
        
        # Float-specific queries
        "CREATE INDEX IF NOT EXISTS idx_live_profiles_float_id ON argo_profiles(float_id);",
        "CREATE INDEX IF NOT EXISTS idx_live_profiles_cycle ON argo_profiles(cycle_number);",
        
        # Composite indexes for common query patterns
        "CREATE INDEX IF NOT EXISTS idx_live_measurements_location_pressure ON argo_measurements(latitude, longitude, pressure);",
        "CREATE INDEX IF NOT EXISTS idx_live_measurements_temp_depth ON argo_measurements(temperature, pressure);",
        
        # Automation tracking
        "CREATE INDEX IF NOT EXISTS idx_automation_log_timestamp ON automation_log(run_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_automation_log_status ON automation_log(status);"
    ]
    
    try:
        conn = psycopg2.connect(**LIVE_DB_CONFIG)
        cursor = conn.cursor()
        
        for index_sql in indexes_sql:
            cursor.execute(index_sql)
            index_name = index_sql.split('idx_live_')[1].split(' ')[0] if 'idx_live_' in index_sql else index_sql.split('idx_')[1].split(' ')[0]
            print(f"✅ Created index: {index_name}")
        
        conn.commit()
        print("✅ All live database indexes created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating live indexes: {e}")
        return False
    
    return True

def test_live_database():
    """Test the live database connection and basic functionality"""
    
    try:
        conn = psycopg2.connect(**LIVE_DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n🔍 Live Database Test Results:")
        print("=" * 50)
        
        # Test basic connectivity
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL Version: {version.split(',')[0]}")
        
        # Test tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('argo_profiles', 'argo_measurements', 'automation_log')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Tables created: {', '.join(tables)}")
        
        # Test initial counts
        cursor.execute("SELECT COUNT(*) FROM argo_profiles;")
        profile_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_measurements;")
        measurement_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM automation_log;")
        log_count = cursor.fetchone()[0]
        
        print(f"📊 Current data:")
        print(f"   • Profiles: {profile_count:,}")
        print(f"   • Measurements: {measurement_count:,}")
        print(f"   • Automation runs: {log_count}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing live database: {e}")
        return False

def get_live_db_config():
    """Return the live database configuration for use by other scripts"""
    return LIVE_DB_CONFIG

def main():
    """Main setup function for live database"""
    print("🚀 Setting up Live PostgreSQL database for FloatChat...")
    print("=" * 60)
    
    # Step 1: Create database
    if not create_live_database():
        return
    
    # Step 2: Create tables
    if not create_live_tables():
        return
    
    # Step 3: Create indexes
    if not create_live_indexes():
        return
    
    # Step 4: Test database
    if not test_live_database():
        return
    
    print("\n" + "=" * 60)
    print("🎉 LIVE DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print(f"Database: {LIVE_DB_CONFIG['database']}")
    print(f"Host: {LIVE_DB_CONFIG['host']}:{LIVE_DB_CONFIG['port']}")
    print("Tables: argo_profiles, argo_measurements, automation_log")
    print("Indexes: Optimized for real-time queries")
    print("\n✅ Your FloatChat live automation system is ready!")
    print("🔄 Next step: Run the live automation pipeline")

if __name__ == "__main__":
    main()