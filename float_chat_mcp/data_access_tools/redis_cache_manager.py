"""
Redis Cache Manager for FloatChat MCP Server
Provides caching capabilities for query results
Note: This is a stub implementation - Redis integration can be added later
"""

import logging
from typing import Dict, Any, List, Optional
import json
import hashlib
from datetime import datetime

class RedisCacheManager:
    """Cache manager for query results (stub implementation)"""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize cache manager
        
        Args:
            enabled: Whether caching is enabled (currently a no-op)
        """
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache as fallback (not persistent)
        self._memory_cache = {}
        self._query_history = []
        
        if enabled:
            self.logger.info("📦 Cache Manager initialized (in-memory mode)")
        else:
            self.logger.info("📦 Cache Manager initialized (disabled)")
    
    def get_cached_result(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a query
        
        Args:
            query: SQL query or search query
            params: Additional parameters
            
        Returns:
            Cached result if found, None otherwise
        """
        if not self.enabled:
            return None
        
        # Generate cache key
        cache_key = self._generate_cache_key(query, params)
        
        # Check in-memory cache
        if cache_key in self._memory_cache:
            cached_data = self._memory_cache[cache_key]
            self.logger.info(f"✅ Cache HIT for key: {cache_key[:16]}...")
            
            # Add cache_hit flag
            if isinstance(cached_data, dict):
                cached_data['cache_hit'] = True
            
            return cached_data
        
        self.logger.debug(f"❌ Cache MISS for key: {cache_key[:16]}...")
        return None
    
    def cache_result(self, query: str, result: Dict[str, Any], params: Dict[str, Any] = None, ttl: int = 3600):
        """
        Cache a query result
        
        Args:
            query: SQL query or search query
            result: Query result to cache
            params: Additional parameters
            ttl: Time to live in seconds (not implemented in memory cache)
        """
        if not self.enabled:
            return
        
        # Generate cache key
        cache_key = self._generate_cache_key(query, params)
        
        # Store in memory cache
        self._memory_cache[cache_key] = result
        
        # Add to query history
        self._query_history.append({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'cache_key': cache_key
        })
        
        # Keep only last 100 queries in history
        if len(self._query_history) > 100:
            self._query_history = self._query_history[-100:]
        
        self.logger.debug(f"💾 Cached result for key: {cache_key[:16]}...")
    
    def invalidate_cache(self, query: str = None, params: Dict[str, Any] = None):
        """
        Invalidate cache for a specific query or all cache
        
        Args:
            query: Specific query to invalidate (None = invalidate all)
            params: Additional parameters
        """
        if not self.enabled:
            return
        
        if query is None:
            # Clear all cache
            self._memory_cache.clear()
            self.logger.info("🗑️ Cleared all cache")
        else:
            # Clear specific query
            cache_key = self._generate_cache_key(query, params)
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                self.logger.info(f"🗑️ Invalidated cache for key: {cache_key[:16]}...")
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent queries from history
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of recent queries with metadata
        """
        return self._query_history[-limit:]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'enabled': self.enabled,
            'cache_type': 'in-memory',
            'cached_items': len(self._memory_cache),
            'query_history_size': len(self._query_history),
            'note': 'Using in-memory cache. For production, consider Redis integration.'
        }
    
    def _generate_cache_key(self, query: str, params: Dict[str, Any] = None) -> str:
        """
        Generate a cache key from query and parameters
        
        Args:
            query: Query string
            params: Additional parameters
            
        Returns:
            Cache key (hash)
        """
        # Combine query and params into a single string
        cache_string = query
        
        if params:
            # Sort params for consistent hashing
            sorted_params = json.dumps(params, sort_keys=True)
            cache_string += sorted_params
        
        # Generate SHA256 hash
        return hashlib.sha256(cache_string.encode()).hexdigest()


def test_cache_manager():
    """Test the cache manager"""
    print("🧪 Testing Redis Cache Manager (In-Memory Mode)\n")
    
    cache = RedisCacheManager(enabled=True)
    
    # Test 1: Cache miss
    print("1. Testing cache miss...")
    result = cache.get_cached_result("SELECT * FROM test", {"limit": 10})
    print(f"   Result: {result}")
    assert result is None, "Should be cache miss"
    
    # Test 2: Cache set
    print("\n2. Testing cache set...")
    test_data = {"status": "success", "data": [1, 2, 3]}
    cache.cache_result("SELECT * FROM test", test_data, {"limit": 10})
    print("   Cached successfully")
    
    # Test 3: Cache hit
    print("\n3. Testing cache hit...")
    result = cache.get_cached_result("SELECT * FROM test", {"limit": 10})
    print(f"   Result: {result}")
    assert result is not None, "Should be cache hit"
    assert result['cache_hit'] == True, "Should have cache_hit flag"
    
    # Test 4: Cache stats
    print("\n4. Testing cache stats...")
    stats = cache.get_cache_stats()
    print(f"   Stats: {stats}")
    
    # Test 5: Recent queries
    print("\n5. Testing recent queries...")
    queries = cache.get_recent_queries(limit=5)
    print(f"   Recent queries: {len(queries)}")
    
    # Test 6: Cache invalidation
    print("\n6. Testing cache invalidation...")
    cache.invalidate_cache("SELECT * FROM test", {"limit": 10})
    result = cache.get_cached_result("SELECT * FROM test", {"limit": 10})
    print(f"   Result after invalidation: {result}")
    assert result is None, "Should be cache miss after invalidation"
    
    print("\n✅ Cache Manager testing complete!")


if __name__ == "__main__":
    test_cache_manager()
