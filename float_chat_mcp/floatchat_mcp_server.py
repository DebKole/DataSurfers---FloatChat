"""
FloatChat MCP Server
Exposes data access tools to AI agents via Model Context Protocol
Using FastMCP for simplicity
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from fastmcp import FastMCP

# Import your enhanced data access tools
from float_chat_mcp.data_access_tools.data_access_orchestrator import DataAccessOrchestrator
from float_chat_mcp.data_access_tools.redis_cache_manager import RedisCacheManager

# Initialize tools
orchestrator = DataAccessOrchestrator(use_gemini=True, enable_cache=True)
cache_manager = RedisCacheManager(enabled=True)

# Create FastMCP server
mcp = FastMCP("FloatChat Data Access")

@mcp.tool()
def execute_query(query: str) -> dict:
    """
    Execute a natural language query about Argo float data.
    Uses Gemini AI to understand the query and generate SQL.
    Results are cached in Redis for faster repeated queries.
    
    Args:
        query: Natural language query (e.g., 'Show me temperature data from Arabian Sea')
    
    Returns:
        Query results with metadata
    """
    result = orchestrator.execute_query(query)
    return result

@mcp.tool()
def get_recent_queries(limit: int = 10) -> list:
    """
    Get list of recent queries executed by users.
    Useful for showing query history in dashboard.
    
    Args:
        limit: Maximum number of queries to return (default: 10)
    
    Returns:
        List of recent query information
    """
    recent = cache_manager.get_recent_queries(limit=limit)
    return recent

@mcp.tool()
def get_system_status() -> dict:
    """
    Get status of all system components.
    Includes Gemini AI, Redis cache, databases, and vector store status.
    
    Returns:
        System status information
    """
    status = orchestrator.get_system_status()
    return status

@mcp.tool()
def get_cache_stats() -> dict:
    """
    Get Redis cache statistics.
    Shows cached queries count, memory usage, and performance metrics.
    
    Returns:
        Cache statistics
    """
    stats = cache_manager.get_cache_stats()
    return stats

if __name__ == "__main__":
    print("🚀 Starting FloatChat MCP Server (FastMCP)")
    print("📊 Tools available:")
    print("   - execute_query (Gemini AI + Redis caching)")
    print("   - get_recent_queries")
    print("   - get_system_status")
    print("   - get_cache_stats")
    print("\n✅ Server ready for agent connections")
    
    # Run the server
    mcp.run()
