#!/usr/bin/env python3
"""
Quick test to verify BGC integration is working
Run this to check everything at once
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_environment():
    """Test 1: Check environment variables"""
    print_section("TEST 1: Environment Variables")
    
    required = ['DB_HOST', 'DB_PORT', 'DB_USERNAME', 'DB_PASSWORD', 'DB_NAME']
    all_set = True
    
    for var in required:
        value = os.getenv(var)
        if value:
            display = '***' if 'PASSWORD' in var else value
            print(f"  ✅ {var}: {display}")
        else:
            print(f"  ❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def test_bgc_files():
    """Test 2: Check if BGC files exist"""
    print_section("TEST 2: BGC Files")
    
    bgc_dir = "./data/bgc_downloads"
    
    if not os.path.exists(bgc_dir):
        print(f"  ❌ Directory not found: {bgc_dir}")
        print(f"  → Create it: mkdir -p {bgc_dir}")
        return False
    
    nc_files = [f for f in os.listdir(bgc_dir) if f.endswith('.nc')]
    
    if not nc_files:
        print(f"  ❌ No NetCDF files found in {bgc_dir}")
        print(f"  → Download files first or check the directory")
        return False
    
    print(f"  ✅ Found {len(nc_files)} NetCDF files")
    print(f"  → First 3 files:")
    for f in nc_files[:3]:
        print(f"     - {f}")
    
    return True

def test_database_connection():
    """Test 3: Check database connection"""
    print_section("TEST 3: Database Connection")
    
    try:
        import psycopg2
    except ImportError:
        print("  ❌ psycopg2 not installed")
        print("  → Install: pip install psycopg2-binary")
        return False
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USERNAME', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            database='postgres'
        )
        print("  ✅ Database connection successful")
        conn.close()
        return True
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        print("  → Check your .env file and PostgreSQL is running")
        return False

def test_bgc_database():
    """Test 4: Check BGC database and schema"""
    print_section("TEST 4: BGC Database Schema")
    
    try:
        import psycopg2
        
        db_name = os.getenv('DB_NAME', 'argo_bgc')
        
        # Try to connect to BGC database
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5432)),
                user=os.getenv('DB_USERNAME', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                database=db_name
            )
            print(f"  ✅ Database '{db_name}' exists")
        except psycopg2.OperationalError:
            print(f"  ⚠️  Database '{db_name}' does not exist yet")
            print(f"  → It will be created when you run bgc_ingest.py")
            return False
        
        cur = conn.cursor()
        
        # Check if tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('argo_bgc_profiles', 'argo_bgc_measurements')
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        if 'argo_bgc_profiles' in tables:
            print("  ✅ Table 'argo_bgc_profiles' exists")
        else:
            print("  ⚠️  Table 'argo_bgc_profiles' does not exist yet")
        
        if 'argo_bgc_measurements' in tables:
            print("  ✅ Table 'argo_bgc_measurements' exists")
        else:
            print("  ⚠️  Table 'argo_bgc_measurements' does not exist yet")
        
        if not tables:
            print("  → Tables will be created when you run bgc_ingest.py")
            conn.close()
            return False
        
        # Check if bgc_parameters column exists
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'argo_bgc_measurements' 
            AND column_name = 'bgc_parameters'
        """)
        result = cur.fetchone()
        
        if result:
            print(f"  ✅ Column 'bgc_parameters' exists ({result[1]})")
        else:
            print("  ⚠️  Column 'bgc_parameters' does not exist")
            print("  → Run: python3 migrate_bgc_to_jsonb.py")
            conn.close()
            return False
        
        # Check if GIN index exists
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'argo_bgc_measurements' 
            AND indexname = 'idx_bgc_parameters_gin'
        """)
        result = cur.fetchone()
        
        if result:
            print(f"  ✅ GIN index exists")
        else:
            print("  ⚠️  GIN index does not exist")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_bgc_data():
    """Test 5: Check if BGC data exists"""
    print_section("TEST 5: BGC Data")
    
    try:
        import psycopg2
        import json
        
        db_name = os.getenv('DB_NAME', 'argo_bgc')
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USERNAME', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            database=db_name
        )
        
        cur = conn.cursor()
        
        # Count profiles
        cur.execute("SELECT COUNT(*) FROM argo_bgc_profiles")
        profile_count = cur.fetchone()[0]
        
        if profile_count > 0:
            print(f"  ✅ Profiles: {profile_count}")
        else:
            print(f"  ⚠️  No profiles found")
            print(f"  → Run: python3 bgc_ingest.py")
            conn.close()
            return False
        
        # Count measurements
        cur.execute("SELECT COUNT(*) FROM argo_bgc_measurements")
        measurement_count = cur.fetchone()[0]
        print(f"  ✅ Measurements: {measurement_count}")
        
        # Count BGC measurements
        cur.execute("SELECT COUNT(*) FROM argo_bgc_measurements WHERE bgc_parameters IS NOT NULL")
        bgc_count = cur.fetchone()[0]
        
        if bgc_count > 0:
            print(f"  ✅ Measurements with BGC data: {bgc_count}")
        else:
            print(f"  ⚠️  No BGC data found")
            print(f"  → Your NetCDF files may not have BGC parameters")
            conn.close()
            return False
        
        # List available parameters
        cur.execute("""
            SELECT DISTINCT jsonb_object_keys(bgc_parameters) as parameter
            FROM argo_bgc_measurements
            WHERE bgc_parameters IS NOT NULL
        """)
        params = [row[0] for row in cur.fetchall()]
        
        if params:
            print(f"  ✅ Available BGC parameters: {', '.join(params)}")
        
        # Show sample
        cur.execute("""
            SELECT 
                p.float_id,
                m.bgc_parameters
            FROM argo_bgc_profiles p
            JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
            WHERE m.bgc_parameters IS NOT NULL
            LIMIT 1
        """)
        result = cur.fetchone()
        
        if result:
            print(f"\n  ✅ Sample data:")
            print(f"     Float ID: {result[0]}")
            print(f"     BGC Parameters: {json.dumps(result[1], indent=8)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_bgc_query():
    """Test 6: Test a BGC query"""
    print_section("TEST 6: BGC Query Test")
    
    try:
        import psycopg2
        
        db_name = os.getenv('DB_NAME', 'argo_bgc')
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USERNAME', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            database=db_name
        )
        
        cur = conn.cursor()
        
        # Test: List floats with DOXY
        cur.execute("""
            SELECT DISTINCT p.float_id
            FROM argo_bgc_profiles p
            JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
            WHERE m.bgc_parameters ? 'DOXY'
            LIMIT 5
        """)
        
        floats = [row[0] for row in cur.fetchall()]
        
        if floats:
            print(f"  ✅ Query successful! Found floats with DOXY:")
            for f in floats:
                print(f"     - Float {f}")
        else:
            print(f"  ⚠️  No floats with DOXY found")
            print(f"  → Your data may not have DOXY parameter")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Query failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "BGC INTEGRATION QUICK TEST" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Environment", test_environment()))
    results.append(("BGC Files", test_bgc_files()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("BGC Schema", test_bgc_database()))
    results.append(("BGC Data", test_bgc_data()))
    results.append(("BGC Query", test_bgc_query()))
    
    # Summary
    print_section("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! BGC integration is working!")
        print("\n  Next steps:")
        print("  1. Try queries: python3 test_bgc_integration.py")
        print("  2. See examples: cat BGC_SQL_EXAMPLES.sql")
        print("  3. Read guide: cat BGC_QUICKSTART.md")
        return 0
    else:
        print("\n  ⚠️  Some tests failed. See above for details.")
        print("\n  Quick fixes:")
        print("  - Missing files? Check data/bgc_downloads/")
        print("  - No database? Run: python3 bgc_ingest.py")
        print("  - Connection error? Check .env file")
        print("\n  Full guide: cat TEST_BGC_NOW.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
