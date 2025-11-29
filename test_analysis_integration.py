"""
Test script for analysis tools integration
Tests the complete flow from query to analysis result
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from mcp_query_agent import MCPQueryAgent


def test_analysis_integration():
    """Test the complete analysis integration"""
    print("🧪 Testing Analysis Tools Integration\n")
    print("=" * 60)
    
    agent = MCPQueryAgent()
    
    # Test queries for different analysis types
    test_queries = [
        "Show temperature trend for float 1902482",
        "Generate T-S curve for Arabian Sea",
        "Show statistics for float 1902482",
        "Compare temperature between float 1902482 and 2902746"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        print("-" * 60)
        
        try:
            # Check if it's detected as a data query
            is_data = agent.is_data_query(query)
            print(f"   Detected as data query: {is_data}")
            
            if is_data:
                # Execute the query
                result = agent.execute_query(query)
                
                print(f"   Status: {result['status']}")
                print(f"   Strategy: {result.get('query_type', 'unknown')}")
                
                if result['status'] == 'success':
                    print(f"   Response: {result['response'][:150]}...")
                    print(f"   Has table data: {len(result.get('table_data', {}).get('rows', [])) > 0}")
                else:
                    print(f"   Error: {result.get('response', 'Unknown error')}")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Analysis Integration Test Complete!")


if __name__ == "__main__":
    test_analysis_integration()
