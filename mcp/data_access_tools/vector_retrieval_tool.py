"""
Vector Retrieval Tool for FloatChat MCP Server
Performs semantic search on Argo float profiles using ChromaDB
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from vector_db_manager import FloatChatVectorDB

class VectorRetrievalTool:
    """Semantic search tool for Argo float profiles"""
    
    def __init__(self):
        """Initialize vector database connection"""
        self.vector_db = FloatChatVectorDB()
        
    def search_profiles(
        self, 
        query_text: str, 
        collection: str = "january",
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search on Argo profiles
        
        Args:
            query_text: Natural language query
            collection: "january" or "live" 
            n_results: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            Structured search results with metadata
        """
        try:
            # Perform vector search
            results = self.vector_db.search_profiles(
                query=query_text,
                collection_name=collection,
                n_results=n_results,
                filters=filters
            )
            
            # Format results for MCP
            formatted_results = {
                "status": "success",
                "query": query_text,
                "collection": collection,
                "total_results": len(results),
                "results": []
            }
            
            for result in results:
                formatted_result = {
                    "profile_id": result.get('id', '').replace('profile_', ''),
                    "relevance_score": 1 - result.get('distance', 1),  # Convert distance to relevance
                    "description": result.get('document', ''),
                    "metadata": result.get('metadata', {}),
                    "region": result.get('metadata', {}).get('region', 'unknown'),
                    "float_id": result.get('metadata', {}).get('float_id', 'unknown'),
                    "institution": result.get('metadata', {}).get('institution', 'unknown')
                }
                formatted_results["results"].append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "query": query_text,
                "results": []
            }
    
    def search_by_region(
        self, 
        region: str, 
        collection: str = "january",
        n_results: int = 20
    ) -> Dict[str, Any]:
        """Search profiles by specific region"""
        
        region_queries = {
            "arabian_sea": "Arabian Sea oceanographic profiles temperature salinity",
            "bay_of_bengal": "Bay of Bengal monsoon influenced salinity profiles",
            "southern_indian_ocean": "Southern Indian Ocean deep water profiles",
            "northern_indian_ocean": "Northern Indian Ocean tropical profiles"
        }
        
        query = region_queries.get(region.lower().replace(" ", "_"), f"{region} oceanographic profiles")
        
        return self.search_profiles(
            query_text=query,
            collection=collection,
            n_results=n_results,
            filters={"region": region} if region != "unknown" else None
        )
    
    def search_by_depth_category(
        self, 
        depth_category: str,
        collection: str = "january", 
        n_results: int = 15
    ) -> Dict[str, Any]:
        """Search profiles by depth category"""
        
        depth_queries = {
            "surface": "surface water profiles shallow measurements temperature",
            "shallow": "shallow water profiles upper ocean structure",
            "intermediate": "intermediate depth profiles thermocline measurements", 
            "deep": "deep water profiles full depth ocean profiling"
        }
        
        query = depth_queries.get(depth_category.lower(), f"{depth_category} depth profiles")
        
        return self.search_profiles(
            query_text=query,
            collection=collection,
            n_results=n_results,
            filters={"depth_category": depth_category}
        )
    
    def search_by_institution(
        self, 
        institution: str,
        collection: str = "january",
        n_results: int = 15
    ) -> Dict[str, Any]:
        """Search profiles by deploying institution"""
        
        query = f"{institution} deployed floats oceanographic profiles research"
        
        return self.search_profiles(
            query_text=query,
            collection=collection, 
            n_results=n_results,
            filters={"institution": institution}
        )
    
    def search_seasonal_patterns(
        self, 
        season: str,
        collection: str = "january",
        n_results: int = 20
    ) -> Dict[str, Any]:
        """Search profiles by seasonal patterns"""
        
        seasonal_queries = {
            "winter": "winter oceanographic measurements cold season profiles",
            "spring": "spring seasonal transition ocean profiles",
            "summer": "summer warm season oceanographic data",
            "autumn": "autumn seasonal patterns ocean measurements"
        }
        
        query = seasonal_queries.get(season.lower(), f"{season} seasonal oceanographic profiles")
        
        return self.search_profiles(
            query_text=query,
            collection=collection,
            n_results=n_results,
            filters={"season": season}
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about available collections"""
        try:
            stats = self.vector_db.get_collection_stats()
            return {
                "status": "success",
                "stats": stats
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }

def test_vector_retrieval():
    """Test the vector retrieval tool"""
    print("🧪 Testing Vector Retrieval Tool...")
    
    tool = VectorRetrievalTool()
    
    # Test 1: Basic semantic search
    print("\n1. Testing semantic search...")
    results = tool.search_profiles("INCOIS floats in Arabian Sea", n_results=3)
    print(f"   Found {results['total_results']} results")
    if results['results']:
        print(f"   Best match: {results['results'][0]['description'][:80]}...")
    
    # Test 2: Regional search
    print("\n2. Testing regional search...")
    results = tool.search_by_region("Arabian Sea", n_results=3)
    print(f"   Found {results['total_results']} Arabian Sea profiles")
    
    # Test 3: Depth category search
    print("\n3. Testing depth category search...")
    results = tool.search_by_depth_category("deep", n_results=3)
    print(f"   Found {results['total_results']} deep water profiles")
    
    # Test 4: Collection stats
    print("\n4. Testing collection stats...")
    stats = tool.get_collection_stats()
    print(f"   Stats: {stats}")
    
    print("\n✅ Vector Retrieval Tool testing complete!")

if __name__ == "__main__":
    test_vector_retrieval()