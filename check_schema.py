import psycopg2

def check_schema():
    conn = psycopg2.connect(
        dbname="testing_2025",
        user="postgres",
        password="parv12345",
        host="localhost",
        port="5432"
    )
    
    # Get table columns
    cursor = conn.cursor()
    
    # Check argo_measurements table
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'argo_measurements';
    """)
    
    print("\nargo_measurements columns:")
    print("-" * 50)
    for col in cursor.fetchall():
        print(f"{col[0]} ({col[1]})")
    
    # Check argo_profiles table
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'argo_profiles';
    """)
    
    print("\nargo_profiles columns:")
    print("-" * 50)
    for col in cursor.fetchall():
        print(f"{col[0]} ({col[1]})")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_schema()
