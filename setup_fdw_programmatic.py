"""
Setup Foreign Data Wrapper (FDW) for Cross-Database Queries
This script sets up FDW to allow querying multiple year databases from a single connection
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USERNAME', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '1234')
}

# Main database (where FDW will be set up)
MAIN_DATABASE = 'argo_indian_ocean_25'

# Years to set up FDW for
YEARS = list(range(2015, 2025))  # 2015-2024 (2025 is local)

def setup_fdw():
    """Setup Foreign Data Wrapper for cross-database queries"""
    
    print("🔧 Setting up Foreign Data Wrapper for cross-database queries...")
    print(f"📊 Main database: {MAIN_DATABASE}")
    print(f"📅 Years: {YEARS}")
    
    try:
        # Connect to main database
        conn = psycopg2.connect(**DB_CONFIG, database=MAIN_DATABASE)
        conn.autocommit = True
        cur = conn.cursor()
        
        # 1. Enable postgres_fdw extension
        print("\n1️⃣ Enabling postgres_fdw extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgres_fdw;")
        print("   ✅ Extension enabled")
        
        # 2. Create foreign servers
        print("\n2️⃣ Creating foreign servers...")
        for year in YEARS:
            year_suffix = year % 100  # Convert 2016 -> 16
            db_name = f"argo_indian_ocean_{year_suffix:02d}"
            server_name = f"argo_{year}_server"
            
            try:
                cur.execute(f"""
                    CREATE SERVER IF NOT EXISTS {server_name}
                    FOREIGN DATA WRAPPER postgres_fdw
                    OPTIONS (host '{DB_CONFIG['host']}', port '{DB_CONFIG['port']}', dbname '{db_name}');
                """)
                print(f"   ✅ Created server: {server_name} -> {db_name}")
            except Exception as e:
                print(f"   ⚠️  Server {server_name} might already exist: {e}")
        
        # 3. Create user mappings
        print("\n3️⃣ Creating user mappings...")
        for year in YEARS:
            server_name = f"argo_{year}_server"
            try:
                cur.execute(f"""
                    CREATE USER MAPPING IF NOT EXISTS FOR CURRENT_USER
                    SERVER {server_name}
                    OPTIONS (user '{DB_CONFIG['user']}', password '{DB_CONFIG['password']}');
                """)
                print(f"   ✅ Created user mapping for: {server_name}")
            except Exception as e:
                print(f"   ⚠️  User mapping for {server_name} might already exist: {e}")
        
        # 4. Create foreign schemas
        print("\n4️⃣ Creating foreign schemas...")
        for year in YEARS:
            schema_name = f"argo_{year}"
            try:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
                print(f"   ✅ Created schema: {schema_name}")
            except Exception as e:
                print(f"   ⚠️  Schema {schema_name} might already exist: {e}")
        
        # 5. Import foreign tables
        print("\n5️⃣ Importing foreign tables...")
        for year in YEARS:
            server_name = f"argo_{year}_server"
            schema_name = f"argo_{year}"
            try:
                cur.execute(f"""
                    IMPORT FOREIGN SCHEMA public
                    LIMIT TO (argo_profiles, argo_measurements)
                    FROM SERVER {server_name} INTO {schema_name};
                """)
                print(f"   ✅ Imported tables into: {schema_name}")
            except Exception as e:
                print(f"   ⚠️  Tables in {schema_name} might already exist: {e}")
        
        # 6. Create unified views
        print("\n6️⃣ Creating unified views...")
        
        # Build UNION ALL query for profiles
        profiles_unions = []
        for year in YEARS:
            schema_name = f"argo_{year}"
            profiles_unions.append(f"SELECT *, {year} as data_year FROM {schema_name}.argo_profiles")
        profiles_unions.append(f"SELECT *, 2025 as data_year FROM public.argo_profiles")
        
        profiles_view_sql = f"""
        CREATE OR REPLACE VIEW all_years_argo_profiles AS
        {' UNION ALL '.join(profiles_unions)};
        """
        cur.execute(profiles_view_sql)
        print("   ✅ Created view: all_years_argo_profiles")
        
        # Build UNION ALL query for measurements
        measurements_unions = []
        for year in YEARS:
            schema_name = f"argo_{year}"
            measurements_unions.append(f"SELECT *, {year} as data_year FROM {schema_name}.argo_measurements")
        measurements_unions.append(f"SELECT *, 2025 as data_year FROM public.argo_measurements")
        
        measurements_view_sql = f"""
        CREATE OR REPLACE VIEW all_years_argo_measurements AS
        {' UNION ALL '.join(measurements_unions)};
        """
        cur.execute(measurements_view_sql)
        print("   ✅ Created view: all_years_argo_measurements")
        
        # 7. Grant permissions
        print("\n7️⃣ Granting permissions...")
        schema_list = ', '.join([f"argo_{year}" for year in YEARS])
        cur.execute(f"GRANT USAGE ON SCHEMA {schema_list} TO PUBLIC;")
        for year in YEARS:
            schema_name = f"argo_{year}"
            cur.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema_name} TO PUBLIC;")
        print("   ✅ Permissions granted")
        
        # 8. Test the setup
        print("\n8️⃣ Testing the setup...")
        cur.execute("SELECT COUNT(*) FROM all_years_argo_profiles;")
        total_profiles = cur.fetchone()[0]
        print(f"   ✅ Total profiles across all years: {total_profiles:,}")
        
        cur.execute("SELECT data_year, COUNT(*) FROM all_years_argo_profiles GROUP BY data_year ORDER BY data_year;")
        year_counts = cur.fetchall()
        print("\n   📊 Profiles by year:")
        for year, count in year_counts:
            print(f"      {year}: {count:,} profiles")
        
        # Test cross-year query
        print("\n   🧪 Testing cross-year query (Nov 2016 - Feb 2017)...")
        cur.execute("""
            SELECT COUNT(*) FROM all_years_argo_profiles 
            WHERE datetime >= '2016-11-01' AND datetime <= '2017-02-28';
        """)
        cross_year_count = cur.fetchone()[0]
        print(f"   ✅ Found {cross_year_count:,} profiles in Nov 2016 - Feb 2017")
        
        cur.close()
        conn.close()
        
        print("\n✅ FDW setup complete!")
        print("\n📝 You can now use these views for cross-database queries:")
        print("   - all_years_argo_profiles")
        print("   - all_years_argo_measurements")
        print("\n💡 Example query:")
        print("   SELECT * FROM all_years_argo_profiles")
        print("   WHERE datetime >= '2016-11-01' AND datetime <= '2017-02-28'")
        print("   ORDER BY datetime;")
        
    except Exception as e:
        print(f"\n❌ Error setting up FDW: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_fdw()
