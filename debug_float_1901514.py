
import sys
import os
from vector_db_manager import FloatChatVectorDB

def debug_metadata_search():
    print("🔍 Debugging Metadata Search for Float 1901514...")
    
    # Initialize DB
    db = FloatChatVectorDB()
    
    # Check stats
    try:
        coll = db.metadata_collection
        count = coll.count()
        print(f"📊 Metadata collection count: {count}")
    except Exception as e:
        print(f"❌ Error accessing metadata collection: {e}")
        return

    # Test specific query
    float_id = "1901514"
    query = f"What is the PI name of the float {float_id}"
    print(f"\n🧪 Testing query: '{query}'")
    
    # 1. Check if float exists directly
    # check_float_exists looks for ID "float_{float_id}"
    try:
        record = coll.get(ids=[f"float_{float_id}"])
        if record and record['ids']:
             print(f"🧐 Float {float_id} exists in DB.")
             print(f"\n📄 Record content for {float_id}:")
             print(f"   Document: {record['documents'][0]}")
             print(f"   Metadata: {record['metadatas'][0]}")
        else:
             print(f"❌ Float {float_id} DOES NOT exist in DB (id='float_{float_id}').")
    except Exception as e:
        print(f"❌ Error checking existence: {e}")

    # 2. Test search
    print(f"\n🔎 Running vector search for: '{query}'")
    results = db.search_float_metadata(query, n_results=3)
    
    print(f"found {len(results)} results")
    for i, res in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  ID: {res['id']}")
        print(f"  Distance: {res['distance']}")
        print(f"  Metadata: {res['metadata']}")

if __name__ == "__main__":
    debug_metadata_search()
