
import psycopg2
import os

DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASS = "1234"
MAIN_DB = "argo_indian_ocean_25"

YEARS = range(15, 25) # 2015 to 2024 (2025 is main)

def setup_fdw():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=MAIN_DB
    )
    conn.autocommit = True
    cur = conn.cursor()

    print(f"🔌 Connected to {MAIN_DB}")

    # 1. Create Server and User Mapping for each year
    for year in YEARS:
        year_str = f"{year:02d}"
        remote_db = f"argo_indian_ocean_{year_str}"
        server_name = f"server_{year_str}"
        
        print(f"🛠️  Setting up FDW for {remote_db}...")
        
        # Create Server
        cur.execute(f"DROP SERVER IF EXISTS {server_name} CASCADE;")
        cur.execute(f"""
            CREATE SERVER {server_name}
            FOREIGN DATA WRAPPER postgres_fdw
            OPTIONS (host '{DB_HOST}', port '{DB_PORT}', dbname '{remote_db}');
        """)
        
        # Create User Mapping
        cur.execute(f"""
            CREATE USER MAPPING FOR {DB_USER}
            SERVER {server_name}
            OPTIONS (user '{DB_USER}', password '{DB_PASS}');
        """)
        
        # Import Schema with manual creation to avoid conflicts
        print(f"   Creating foreign tables for {remote_db}...")
        
        # Profiles - Explicitly casting global_profile_id to TEXT to match local schema
        # Assuming remote might be BIGINT or something else if mismatch occurred
        # But actually, let's just make sure the local definition matches what we expect
        
        cur.execute(f"""
            CREATE FOREIGN TABLE IF NOT EXISTS argo_profiles_{year_str} (
                global_profile_id TEXT,
                source_file TEXT,
                local_profile_id TEXT,
                float_id TEXT,
                cycle_number INTEGER,
                datetime TIMESTAMP WITH TIME ZONE,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                min_pressure DOUBLE PRECISION,
                max_pressure DOUBLE PRECISION,
                measurement_count INTEGER,
                project_name TEXT,
                institution TEXT,
                data_mode TEXT,
                created_at TIMESTAMP WITH TIME ZONE
            )
            SERVER {server_name}
            OPTIONS (schema_name 'public', table_name 'argo_profiles');
        """)

    print("✅ FDW setup complete.")
    
    # 2. Create Partitioned View (or just a UNION ALL view)
    print("🏗️  Creating Unified View 'all_argo_profiles'...")
    
    # Explicitly cast columns in the SELECT to ensure type safety for UNION
    cols = [
        "global_profile_id::text", "source_file::text", "local_profile_id::text", "float_id::text", 
        "cycle_number::integer", "datetime::timestamptz", "latitude::double precision", "longitude::double precision", 
        "min_pressure::double precision", "max_pressure::double precision", "measurement_count::integer", 
        "project_name::text", "institution::text", "data_mode::text", "created_at::timestamptz"
    ]
    cols_str = ", ".join(cols)
    
    # Use column aliases for the first part of UNION to define view schema
    cols_aliases = [
        "global_profile_id", "source_file", "local_profile_id", "float_id", 
        "cycle_number", "datetime", "latitude", "longitude", 
        "min_pressure", "max_pressure", "measurement_count", 
        "project_name", "institution", "data_mode", "created_at"
    ]
    
    # Construct the query carefully
    # Part 1: Local table
    select_local = ", ".join([f"{c} AS {a}" for c, a in zip(cols, cols_aliases)])
    union_parts = [f"SELECT {select_local}, '2025'::text as source_year FROM argo_profiles"]
    
    # Part 2: Remote tables
    for year in YEARS:
        year_str = f"{year:02d}"
        union_parts.append(f"SELECT {cols_str}, '20{year_str}'::text as source_year FROM argo_profiles_{year_str}")
        
    create_view_sql = f"CREATE OR REPLACE VIEW all_argo_profiles AS {' UNION ALL '.join(union_parts)};"
    
    try:
        cur.execute(create_view_sql)
        print("✅ Unified View 'all_argo_profiles' created.")
        
        # Verify count
        cur.execute("SELECT count(*) FROM all_argo_profiles")
        count = cur.fetchone()[0]
        print(f"📊 Total profiles in unified view: {count}")
        
        # Check for the problematic float
        float_id = "2902604"
        cur.execute(f"SELECT count(*), min(datetime), max(datetime) FROM all_argo_profiles WHERE float_id = '{float_id}'")
        res = cur.fetchone()
        if res[0] > 0:
            print(f"🎉 FOUND FLOAT {float_id}! Count: {res[0]}, Range: {res[1]} to {res[2]}")
        else:
            print(f"❌ Still could not find float {float_id} in any database.")
            
    except Exception as e:
        print(f"❌ Failed to create view: {e}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    setup_fdw()
