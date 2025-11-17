"""
Simple test script for FloatChat MCP Server
Tests the server by calling tools directly
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import the data access tools directly for testing
from data_access_tools.data_access_orchestrator import DataAccessOrchestrator
from data_access_tools.redis_cache_manager import RedisCacheManager

# Initialize tools
orchestrator = DataAccessOrchestrator(use_gemini=True, enable_cache=True)
cache_manager = RedisCacheManager(enabled=True)

# Wrapper functions (same as MCP server)
def execute_query(query: str):
    return orchestrator.execute_query(query)

def get_recent_queries(limit: int = 10):
    return cache_manager.get_recent_queries(limit=limit)

def get_system_status():
    return orchestrator.get_system_status()

def get_cache_stats():
    return cache_manager.get_cache_stats()

def test_mcp_tools():
    """Test all MCP tools"""
    
    print("🧪 Testing FloatChat MCP Server Tools\n")
    print("=" * 60)
    
    # Test 1: Execute Query
    print("\n📋 Test 1: Execute Natural Language Query")
    print("-" * 60)
    query = "Show me data from float 1902482"
    print(f"Query: '{query}'")
    
    try:
        result = execute_query(query)
        print(f"✅ Status: {result.get('status', 'unknown')}")
        print(f"📊 Strategy: {result.get('strategy', 'unknown')}")
        if 'results' in result:
            print(f"📈 Results: {len(result['results'])} datasets")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get Recent Queries
    print("\n📋 Test 2: Get Recent Queries")
    print("-" * 60)
    
    try:
        recent = get_recent_queries(limit=5)
        print(f"✅ Found {len(recent)} recent queries")
        for i, q in enumerate(recent[:3], 1):
            print(f"   {i}. {q.get('query', 'N/A')[:50]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get System Status
    print("\n📋 Test 3: Get System Status")
    print("-" * 60)
    
    try:
        status = get_system_status()
        print(f"✅ Overall Status: {status.get('status', 'unknown').upper()}")
        
        components = status.get('components', {})
        for component, info in components.items():
            comp_status = info.get('status', 'unknown')
            print(f"   {component}: {comp_status.upper()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get Cache Stats
    print("\n📋 Test 4: Get Cache Statistics")
    print("-" * 60)
    
    try:
        stats = get_cache_stats()
        print(f"✅ Cache Status: {stats.get('status', 'unknown')}")
        if stats.get('enabled'):
            print(f"   Cached queries: {stats.get('cached_queries', 0)}")
            print(f"   Memory used: {stats.get('memory_used', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests complete!")
    print("\n💡 To run as MCP server: python mcp/floatchat_mcp_server.py")

if __name__ == "__main__":
    test_mcp_tools()
