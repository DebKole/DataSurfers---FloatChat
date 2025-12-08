import psycopg2
from psycopg2 import sql

# Database connection parameters
host = "localhost"
user = "postgres"
password = "1234"
port = "5432"

# Iterate over the databases argo_indian_ocean_15 to argo_indian_ocean_25
for i in range(15, 26):
    db_name = f"argo_indian_ocean_{i}"

    try:
        # Connect to the current database
        connection = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cursor = connection.cursor()

        # Define the query to find the count for a specific float_id
        query = sql.SQL("""
            SELECT COUNT(*) 
            FROM argo_profiles 
            WHERE float_id = %s
        """)

        # Execute the query with the specific float_id
        cursor.execute(query, ('1902296',))
        count = cursor.fetchone()[0]

        # If the count is not zero, print the database name and count
        if count != 0:
            print(f"Database {db_name} has {count} entries for float_id '1902296'.")

        # Close the cursor and connection
        cursor.close()
        connection.close()

    except Exception as e:
        # If an error occurs, print the error and move to the next database
        print(f"Error connecting to database {db_name}: {e}")
        continue
