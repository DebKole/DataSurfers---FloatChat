import os
import psycopg2
import pandas as pd
from vector_db_manager import FloatChatVectorDB
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USERNAME', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'database': 'argo_indian_ocean_25'  # Using the latest database
}

def get_all_floats_from_sql():
    """Get unique float metadata from SQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Query to get unique float info
        # We aggregate to get the most common project_name/institution for each float
        query = """
        SELECT 
            float_id,
            mode() WITHIN GROUP (ORDER BY project_name) as project_name,
            mode() WITHIN GROUP (ORDER BY institution) as institution,
            MIN(datetime) as first_seen,
            MAX(datetime) as last_seen,
            AVG(latitude) as avg_lat,
            AVG(longitude) as avg_lon
        FROM argo_profiles
        GROUP BY float_id
        """
        
        print(f"🔌 Connecting to {DB_CONFIG['database']}...")
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"✅ Retrieved {len(df)} unique floats from SQL database")
        return df
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return pd.DataFrame()

def populate_vector_metadata():
    """Populate vector DB with float metadata from SQL"""
    print("🚀 Starting Vector DB Metadata Population...")
    
    # Initialize vector DB
    vector_db = FloatChatVectorDB()
    
    # Get floats from SQL
    floats_df = get_all_floats_from_sql()
    
    if floats_df.empty:
        print("❌ No floats found in SQL database")
        return
    
    # Prepare metadata list
    metadata_list = []
    
    for _, row in floats_df.iterrows():
        # Check if float already exists (optional, but good for updates)
        # if vector_db.check_float_exists(str(row['float_id'])):
        #     continue
            
        meta = {
            'float_id': str(row['float_id']),
            'project_name': row['project_name'] if row['project_name'] else 'Unknown',
            'institution': row['institution'] if row['institution'] else 'Unknown',
            'launch_date': str(row['first_seen'].date()) if pd.notnull(row['first_seen']) else 'Unknown',
            'launch_lat': float(row['avg_lat']) if pd.notnull(row['avg_lat']) else None,
            'launch_lon': float(row['avg_lon']) if pd.notnull(row['avg_lon']) else None,
            # We don't have PI name or platform type in SQL, so we mark them as unknown
            'pi_name': 'Unknown',
            'platform_type': 'Argo Float'
        }
        
        # Create a rich document content
        # We override the default creation to include what we know
        document = f"Argo float {meta['float_id']}"
        if meta['project_name'] != 'Unknown':
            document += f" from project {meta['project_name']}"
        if meta['institution'] != 'Unknown':
            document += f", deployed by {meta['institution']}"
        if meta['launch_date'] != 'Unknown':
            document += f". Active since {meta['launch_date']}"
        if meta['launch_lat'] is not None:
            document += f". Operating around {meta['launch_lat']:.2f}°N, {meta['launch_lon']:.2f}°E"
        document += "."
        
        meta['document_content'] = document
        metadata_list.append(meta)
    
    # Add to vector DB
    print(f"📥 Adding {len(metadata_list)} floats to vector database...")
    count = vector_db.add_float_metadata_to_collection(metadata_list)
    
    print(f"✅ Successfully added {count} float records!")
    
    # Verify
    results = vector_db.search_float_metadata("Argo float", 5)
    print(f"\n🔍 Verification - Sample results:")
    for r in results:
        print(f"  - {r['document']}")

if __name__ == "__main__":
    populate_vector_metadata()
