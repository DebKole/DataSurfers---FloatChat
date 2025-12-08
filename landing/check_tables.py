import psycopg2

try:
    # Connect to the database
    conn = psycopg2.connect('postgresql://postgres:parv12345@localhost:5432/january_data')
    print("✅ Connected to database successfully!")
    
    # Create a cursor
    cur = conn.cursor()
    
    # List all tables
    print("\n📋 Listing all tables:")
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cur.fetchall()
    
    if not tables:
        print("No tables found in the database!")
    else:
        print("Found tables:")
        for table in tables:
            print(f"- {table[0]}")
    
    # Close the connection
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\nDone!")