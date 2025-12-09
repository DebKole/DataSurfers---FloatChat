
import sys
import os
from vector_db_manager import FloatChatVectorDB

def debug_metadata_search():
    print("🔍 Debugging Metadata Search...")
    
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
    float_id = "2902604"
    query = f"Who is the PI for float {float_id}?"
    print(f"\n🧪 Testing query: '{query}'")
    
    # 1. Check if float exists directly
    exists = db.check_float_exists(float_id)
    print(f"🧐 Float {float_id} exists in DB: {exists}")
    
    if exists:
        # Get the record to see what's in it
        try:
            record = coll.get(ids=[f"float_{float_id}"])
            print(f"\n📄 Record content for {float_id}:")
            print(f"   Document: {record['documents'][0]}")
            print(f"   Metadata: {record['metadatas'][0]}")
        except Exception as e:
            print(f"❌ Error retrieving record: {e}")

    # 2. Test search
    print(f"\n🔎 Running vector search for: '{query}'")
    results = db.search_float_metadata(query, n_results=3)
    
    print(f"found {len(results)} results")
    for i, res in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  ID: {res['id']}")
        print(f"  Distance: {res['distance']}")
        print(f"  Document: {res['document']}")
        print(f"  Metadata: {res['metadata']}")

if __name__ == "__main__":
    debug_metadata_search()
