#!/usr/bin/env python3
"""
Migration script to add bgc_parameters JSONB column to existing argo_bgc_measurements table
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    """Get database configuration from environment"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USERNAME", "postgres"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME", "argo_bgc")
    }

def check_table_exists(conn):
    """Check if argo_bgc_measurements table exists"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'argo_bgc_measurements'
            );
        """)
        return cur.fetchone()[0]

def check_column_exists(conn, column_name):
    """Check if a column exists in argo_bgc_measurements"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'argo_bgc_measurements' 
                AND column_name = %s
            );
        """, (column_name,))
        return cur.fetchone()[0]

def add_bgc_parameters_column(conn):
    """Add bgc_parameters JSONB column"""
    print("\n1. Adding bgc_parameters JSONB column...")
    
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE argo_bgc_measurements 
            ADD COLUMN IF NOT EXISTS bgc_parameters JSONB;
        """)
        conn.commit()
    
    print("   ✅ Column added successfully")

def create_gin_index(conn):
    """Create GIN index on bgc_parameters"""
    print("\n2. Creating GIN index on bgc_parameters...")
    
    with conn.cursor() as cur:
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_bgc_parameters_gin 
            ON argo_bgc_measurements USING GIN (bgc_parameters);
        """)
        conn.commit()
    
    print("   ✅ GIN index created successfully")

def migrate_existing_data(conn):
    """Migrate existing BGC data from separate columns to JSONB"""
    print("\n3. Checking for existing BGC data in separate columns...")
    
    # Check which BGC columns exist
    bgc_columns = ['doxy', 'chla', 'nitrate', 'ph_in_situ_total', 'bbp700', 'cdom']
    existing_columns = []
    
    for col in bgc_columns:
        adjusted_col = f"{col}_adjusted"
        if check_column_exists(conn, adjusted_col):
            existing_columns.append(col.upper())
    
    if not existing_columns:
        print("   ℹ️  No existing BGC columns found. Skipping migration.")
        return
    
    print(f"   Found existing columns: {', '.join(existing_columns)}")
    print("   Migrating data to JSONB format...")
    
    # Build migration query
    jsonb_parts = []
    for col in existing_columns:
        col_lower = col.lower()
        jsonb_parts.append(f"""
            CASE WHEN {col_lower}_adjusted IS NOT NULL THEN
                '{col}', jsonb_build_object(
                    'value', {col_lower}_adjusted,
                    'qc', {col_lower}_adjusted_qc
                )
            ELSE NULL END
        """)
    
    # Filter out NULLs and build object
    migration_query = f"""
        UPDATE argo_bgc_measurements
        SET bgc_parameters = (
            SELECT jsonb_object_agg(key, value)
            FROM (
                SELECT * FROM (VALUES
                    {', '.join([f'({part})' for part in jsonb_parts])}
                ) AS t(key, value)
                WHERE key IS NOT NULL
            ) AS filtered
        )
        WHERE bgc_parameters IS NULL
          AND ({' OR '.join([f'{col.lower()}_adjusted IS NOT NULL' for col in existing_columns])});
    """
    
    with conn.cursor() as cur:
        cur.execute(migration_query)
        rows_updated = cur.rowcount
        conn.commit()
    
    print(f"   ✅ Migrated {rows_updated} rows")

def verify_migration(conn):
    """Verify the migration was successful"""
    print("\n4. Verifying migration...")
    
    with conn.cursor() as cur:
        # Count rows with BGC data
        cur.execute("""
            SELECT COUNT(*) 
            FROM argo_bgc_measurements 
            WHERE bgc_parameters IS NOT NULL;
        """)
        count = cur.fetchone()[0]
        
        print(f"   ✅ Found {count} rows with BGC parameters")
        
        # Show sample data
        if count > 0:
            cur.execute("""
                SELECT 
                    global_profile_id,
                    bgc_parameters
                FROM argo_bgc_measurements 
                WHERE bgc_parameters IS NOT NULL
                LIMIT 3;
            """)
            
            print("\n   Sample data:")
            for row in cur.fetchall():
                print(f"   Profile {row[0]}: {row[1]}")
        
        # List available parameters
        cur.execute("""
            SELECT DISTINCT jsonb_object_keys(bgc_parameters) as parameter
            FROM argo_bgc_measurements
            WHERE bgc_parameters IS NOT NULL;
        """)
        
        params = [row[0] for row in cur.fetchall()]
        if params:
            print(f"\n   Available BGC parameters: {', '.join(params)}")

def main():
    """Main migration function"""
    print("=" * 80)
    print("BGC JSONB Migration Script")
    print("=" * 80)
    
    try:
        db_config = get_db_config()
        print(f"\nConnecting to database: {db_config['database']}")
        
        conn = psycopg2.connect(**db_config)
        
        # Check if table exists
        if not check_table_exists(conn):
            print("\n❌ Table argo_bgc_measurements does not exist.")
            print("   Run bgc_ingest.py first to create the table.")
            return 1
        
        print("✅ Table argo_bgc_measurements exists")
        
        # Check if column already exists
        if check_column_exists(conn, 'bgc_parameters'):
            print("✅ Column bgc_parameters already exists")
        else:
            # Add column
            add_bgc_parameters_column(conn)
        
        # Create index
        create_gin_index(conn)
        
        # Migrate existing data (if any)
        migrate_existing_data(conn)
        
        # Verify
        verify_migration(conn)
        
        print("\n" + "=" * 80)
        print("✅ Migration completed successfully!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Run: python test_bgc_integration.py")
        print("2. Run: python bgc_ingest.py (to ingest new BGC data)")
        print("3. Query example: 'List floats with oxygen measurements'")
        print("=" * 80)
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
