
from mcp_query_agent import MCPQueryAgent
import logging

# Mock result to simulate what Orchestrator returns for vector_only
# (based on code inspection)
mock_orchestrator_result = {
    'status': 'success',
    'strategy': 'vector_only',
    'data_sources': ['ChromaDB Vector Search'],
    'results': [
        {
            # This mimics the structure returned by VectorRetrievalTool wrapped in list
            "status": "success",
            "query": "What is the PI name of the float 1901514",
            "collection": "metadata",
            "total_results": 1,
            "results": [
                {
                    "profile_id": "float_1901514",
                    "relevance_score": 0.8,
                    "description": "Float 1901514 metadata...",
                    "metadata": {
                        "PI_NAME": "M Ravichandran",
                        "float_id": "1901514",
                        "PROJECT_NAME": "Argo INDIA"
                    }
                }
            ]
        }
    ],
    'query_metadata': {},
    # llm_summary is Missing or None, simulating the failure
    'llm_summary': None 
}

def test_fix():
    print("🧪 Testing MCP Agent Fix...")
    agent = MCPQueryAgent()
    
    # We want to test _format_response with our mock result
    # We can access the private method or just call a modified execute_query if we could inject the mock
    
    # Let's test _format_response directly
    response = agent._format_response(mock_orchestrator_result, "What is the PI name of the float 1901514")
    print(f"\nResponse:\n{response}")
    
    if "M Ravichandran" in response:
        print("\n✅ Fix verified: PI Name extracted from metadata fallback.")
    else:
        print("\n❌ Fix failed: PI Name not found in response.")

    # Also test table data extraction
    table_data = agent._extract_table_data(mock_orchestrator_result)
    print(f"\nTable Data Rows: {len(table_data['rows'])}")
    if table_data['rows'] and table_data['rows'][0].get('PI_NAME') == 'M Ravichandran':
         print("✅ Table data extraction verified.")
    else:
         print("❌ Table data extraction failed.")

if __name__ == "__main__":
    test_fix()
