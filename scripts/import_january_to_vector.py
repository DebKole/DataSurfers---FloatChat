"""
Import January 2025 Argo data to Vector Database
One-time setup script to populate the development vector collection
"""

import sys
import os
from pathlib import Path
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from vector_db_manager import FloatChatVectorDB

# Load environment variables
load_dotenv()

# Main database configuration (January data)
MAIN_DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USERNAME', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'database': 'floatchat_argo'  # Main database with January data
}

def get_january_profiles():
    """Get all profiles from the main January database"""
    try:
        conn = psycopg2.connect(**MAIN_DB_CONFIG)
        
        query = """
        SELECT 
            global_profile_id,
            source_file,
            local_profile_id,
            float_id,
            cycle_number,
            datetime,
            latitude,
            longitude,
            min_pressure,
            max_pressure,
            measurement_count,
            project_name,
            institution,
            data_mode,
            created_at
        FROM argo_profiles
        ORDER BY global_profile_id
        """
        
        profiles_df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"📊 Retrieved {len(profiles_df)} profiles from January database")
        return profiles_df
        
    except Exception as e:
        print(f"❌ Error connecting to January database: {e}")
        return pd.DataFrame()

def import_january_data():
    """Import January profiles to vector database"""
    print("🚀 Starting January data import to Vector Database...")
    print("=" * 60)
    
    # Initialize vector database
    print("🧠 Initializing Vector Database...")
    vector_db = FloatChatVectorDB()
    
    # Get current stats
    stats_before = vector_db.get_collection_stats()
    print(f"📊 Current Vector DB Stats: {stats_before}")
    
    # Get January profiles
    print("📥 Fetching January profiles from PostgreSQL...")
    profiles_df = get_january_profiles()
    
    if profiles_df.empty:
        print("❌ No profiles found in January database")
        return False
    
    # Clear existing January collection (fresh start)
    print("🧹 Clearing existing January collection...")
    vector_db.clear_collection("january")
    
    # Process profiles in batches for better performance
    batch_size = 100
    total_added = 0
    
    print(f"🔄 Processing {len(profiles_df)} profiles in batches of {batch_size}...")
    
    for i in range(0, len(profiles_df), batch_size):
        batch = profiles_df.iloc[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(profiles_df) + batch_size - 1) // batch_size
        
        print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} profiles)...")
        
        added_count = vector_db.add_profiles_to_collection(batch, "january")
        total_added += added_count
        
        if added_count != len(batch):
            print(f"⚠️  Warning: Only {added_count}/{len(batch)} profiles added in this batch")
    
    # Get final stats
    stats_after = vector_db.get_collection_stats()
    
    print("\n" + "=" * 60)
    print("✅ JANUARY DATA IMPORT COMPLETE!")
    print("=" * 60)
    print(f"📊 Profiles processed: {len(profiles_df)}")
    print(f"📊 Profiles added to vector DB: {total_added}")
    print(f"📊 Final vector DB stats: {stats_after}")
    
    # Test search functionality
    print("\n🔍 Testing search functionality...")
    test_queries = [
        "INCOIS floats",
        "Arabian Sea deployments", 
        "deep water profiles",
        "winter measurements"
    ]
    
    for query in test_queries:
        results = vector_db.search_profiles(query, "january", 3)
        print(f"  Query: '{query}' → {len(results)} results")
        if results:
            print(f"    Best match: {results[0]['document'][:80]}...")
    
    return True

def main():
    """Main import function"""
    try:
        success = import_january_data()
        
        if success:
            print("\n🎉 January data successfully imported to Vector Database!")
            print("🔍 You can now perform semantic searches on your January Argo data")
            print("🚀 Ready for integration with query agents!")
        else:
            print("\n❌ Import failed. Please check the error messages above.")
            
    except Exception as e:
        print(f"\n❌ Unexpected error during import: {e}")

if __name__ == "__main__":
    main()