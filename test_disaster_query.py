
from gemini_sql_generator import GeminiSQLGenerator
import re

def test_disaster_query():
    generator = GeminiSQLGenerator()
    
    query = "What was the salinity in the Bay of Bengal during Cyclone Amphan?"
    print(f"Testing query: '{query}'")
    
    result = generator.generate_sql_query(query)
    
    if result['status'] == 'success':
        sql = result['sql']
        print(f"Generated SQL:\n{sql}")
        
        # Check for May 2020 dates
        if "2020-05" in sql:
            print("✅ PASSED: Found May 2020 dates in SQL.")
        else:
            print("❌ FAILED: Did not find May 2020 dates.")
            
        # Check for Bay of Bengal coordinates (approximate)
        if "latitude" in sql and "longitude" in sql:
             print("✅ PASSED: Found coordinate filters.")
        else:
             print("⚠️ WARNING: No coordinate filters found (might be relying on 'Bay of Bengal' text if supported, or just date).")

    else:
        print(f"❌ FAILED: Generation error: {result.get('error')}")

if __name__ == "__main__":
    test_disaster_query()
