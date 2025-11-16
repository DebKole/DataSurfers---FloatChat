"""
Query Builder Tool for FloatChat MCP Server
Intelligent query routing and SQL generation from natural language intent
Now powered by Google Gemini AI for dynamic SQL generation
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import Gemini SQL Generator
try:
    from gemini_sql_generator import GeminiSQLGenerator
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Gemini SQL Generator not available, falling back to hardcoded patterns")

class QueryBuilderTool:
    """Intelligent query builder and router for Argo data access"""
    
    def __init__(self, use_gemini: bool = True):
        """
        Initialize query builder with patterns and mappings
        
        Args:
            use_gemini: Whether to use Gemini AI for SQL generation (default: True)
        """
        self.logger = logging.getLogger(__name__)
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        
        # Initialize Gemini SQL Generator if available
        if self.use_gemini:
            try:
                self.gemini_generator = GeminiSQLGenerator()
                self.logger.info("✅ Gemini SQL Generator initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini: {e}. Falling back to hardcoded patterns")
                self.use_gemini = False
                self.gemini_generator = None
        else:
            self.gemini_generator = None
        
        # Geographic regions mapping
        self.regions = {
            "arabian sea": "Arabian Sea",
            "bay of bengal": "Bay of Bengal", 
            "southern indian ocean": "Southern Indian Ocean",
            "northern indian ocean": "Northern Indian Ocean",
            "indian ocean": "Indian Ocean"
        }
        
        # Temporal patterns
        self.temporal_patterns = {
            "winter": ["winter", "december", "january", "february"],
            "spring": ["spring", "march", "april", "may"],
            "summer": ["summer", "june", "july", "august"],
            "autumn": ["autumn", "fall", "september", "october", "november"]
        }
        
        # Parameter mappings
        self.parameters = {
            "temperature": ["temperature", "temp", "thermal", "heat"],
            "salinity": ["salinity", "salt", "saline", "psu"],
            "pressure": ["pressure", "depth", "deep", "shallow"]
        }
        
        # Institution patterns
        self.institutions = {
            "incois": ["incois", "indian national centre"],
            "csiro": ["csiro", "commonwealth scientific"],
            "ifremer": ["ifremer", "french research"]
        }
    
    def analyze_intent(self, query_text: str) -> Dict[str, Any]:
        """
        Analyze user query to extract intent and entities
        
        Args:
            query_text: Natural language query
            
        Returns:
            Intent analysis with extracted entities
        """
        query_lower = query_text.lower()
        
        # Extract entities
        entities = {
            "regions": self._extract_regions(query_lower),
            "temporal": self._extract_temporal(query_lower),
            "parameters": self._extract_parameters(query_lower),
            "float_ids": self._extract_float_ids(query_text),
            "institutions": self._extract_institutions(query_lower),
            "coordinates": self._extract_coordinates(query_text),
            "depth_terms": self._extract_depth_terms(query_lower)
        }
        
        # Determine query type
        query_type = self._classify_query_type(entities, query_lower)
        
        # Choose execution strategy
        strategy = self._choose_strategy(query_type, entities, query_lower)
        
        return {
            "query_text": query_text,
            "entities": entities,
            "query_type": query_type,
            "strategy": strategy,
            "confidence": self._calculate_confidence(entities, query_type)
        }
    
    def build_execution_plan(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build execution plan based on intent analysis
        
        Args:
            intent: Intent analysis from analyze_intent()
            
        Returns:
            Detailed execution plan with queries and parameters
        """
        strategy = intent["strategy"]
        entities = intent["entities"]
        
        if strategy == "sql_only":
            return self._build_sql_plan(entities, intent)
        elif strategy == "vector_only":
            return self._build_vector_plan(entities, intent)
        elif strategy == "hybrid":
            return self._build_hybrid_plan(entities, intent)
        else:
            return self._build_fallback_plan(intent)
    
    def _extract_regions(self, query_lower: str) -> List[str]:
        """Extract geographic regions from query"""
        found_regions = []
        for key, region in self.regions.items():
            if key in query_lower:
                found_regions.append(region)
        return found_regions
    
    def _extract_temporal(self, query_lower: str) -> Dict[str, Any]:
        """Extract temporal information from query"""
        temporal_info = {
            "seasons": [],
            "years": [],
            "months": [],
            "relative_time": None
        }
        
        # Extract seasons
        for season, keywords in self.temporal_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                temporal_info["seasons"].append(season)
        
        # Extract years
        year_matches = re.findall(r'\b(20\d{2})\b', query_lower)
        temporal_info["years"] = [int(year) for year in year_matches]
        
        # Extract relative time
        if any(word in query_lower for word in ["latest", "recent", "current", "now"]):
            temporal_info["relative_time"] = "recent"
        elif any(word in query_lower for word in ["last month", "past month"]):
            temporal_info["relative_time"] = "last_month"
        
        return temporal_info
    
    def _extract_parameters(self, query_lower: str) -> List[str]:
        """Extract oceanographic parameters from query"""
        found_params = []
        for param, keywords in self.parameters.items():
            if any(keyword in query_lower for keyword in keywords):
                found_params.append(param)
        return found_params
    
    def _extract_float_ids(self, query_text: str) -> List[str]:
        """Extract float IDs from query"""
        # Look for patterns like "float 1234567" or "1234567"
        float_patterns = [
            r'float\s+(\d{7})',
            r'\b(\d{7})\b'
        ]
        
        float_ids = []
        for pattern in float_patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)
            float_ids.extend(matches)
        
        return list(set(float_ids))  # Remove duplicates
    
    def _extract_institutions(self, query_lower: str) -> List[str]:
        """Extract institutions from query"""
        found_institutions = []
        for inst, keywords in self.institutions.items():
            if any(keyword in query_lower for keyword in keywords):
                found_institutions.append(inst.upper())
        return found_institutions
    
    def _extract_coordinates(self, query_text: str) -> Dict[str, Any]:
        """Extract coordinate information from query"""
        coords = {"lat_bounds": None, "lng_bounds": None}
        
        # Look for coordinate patterns
        lat_pattern = r'(\d+(?:\.\d+)?)[°]?[NS]'
        lng_pattern = r'(\d+(?:\.\d+)?)[°]?[EW]'
        
        lat_matches = re.findall(lat_pattern, query_text, re.IGNORECASE)
        lng_matches = re.findall(lng_pattern, query_text, re.IGNORECASE)
        
        if lat_matches:
            coords["lat_bounds"] = [float(lat) for lat in lat_matches]
        if lng_matches:
            coords["lng_bounds"] = [float(lng) for lng in lng_matches]
        
        return coords
    
    def _extract_depth_terms(self, query_lower: str) -> List[str]:
        """Extract depth-related terms"""
        depth_terms = []
        depth_keywords = {
            "surface": ["surface", "shallow", "top"],
            "deep": ["deep", "bottom", "abyssal"],
            "intermediate": ["intermediate", "mid", "middle"]
        }
        
        for category, keywords in depth_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                depth_terms.append(category)
        
        return depth_terms
    
    def _classify_query_type(self, entities: Dict[str, Any], query_lower: str) -> str:
        """Classify the type of query based on entities"""
        
        # Specific float lookup
        if entities["float_ids"]:
            return "float_lookup"
        
        # Spatial queries
        if entities["regions"] or entities["coordinates"]["lat_bounds"]:
            if entities["temporal"]["seasons"] or entities["temporal"]["years"]:
                return "spatial_temporal"
            return "spatial"
        
        # Temporal queries
        if entities["temporal"]["seasons"] or entities["temporal"]["years"] or entities["temporal"]["relative_time"]:
            return "temporal"
        
        # Parameter-specific queries
        if entities["parameters"]:
            return "parameter_analysis"
        
        # Institution queries
        if entities["institutions"]:
            return "institution_analysis"
        
        # Semantic/complex queries
        if any(word in query_lower for word in ["compare", "analyze", "pattern", "trend", "anomaly"]):
            return "semantic_analysis"
        
        return "general_search"
    
    def _choose_strategy(self, query_type: str, entities: Dict[str, Any], query_lower: str) -> str:
        """Choose execution strategy based on query type and complexity"""
        
        # Direct SQL for simple lookups
        if query_type == "float_lookup":
            return "sql_only"
        
        # Vector search for semantic queries
        if query_type == "semantic_analysis":
            return "vector_only"
        
        # Hybrid for complex spatial-temporal queries
        if query_type == "spatial_temporal":
            return "hybrid"
        
        # SQL for simple spatial/temporal queries
        if query_type in ["spatial", "temporal"]:
            return "sql_only"
        
        # Vector for institution/parameter analysis
        if query_type in ["institution_analysis", "parameter_analysis"]:
            return "vector_only"
        
        # Default to hybrid for general searches
        return "hybrid"
    
    def _calculate_confidence(self, entities: Dict[str, Any], query_type: str) -> float:
        """Calculate confidence score for the intent analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on extracted entities
        if entities["float_ids"]:
            confidence += 0.3
        if entities["regions"]:
            confidence += 0.2
        if entities["parameters"]:
            confidence += 0.1
        if entities["temporal"]["seasons"] or entities["temporal"]["years"]:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _build_sql_plan(self, entities: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Build SQL-only execution plan using Gemini AI or fallback to hardcoded patterns"""
        
        plan = {
            "strategy": "sql_only",
            "database": "main",  # Default to January data
            "queries": [],
            "parameters": {},
            "gemini_powered": False
        }
        
        # Try Gemini AI first if available
        if self.use_gemini and self.gemini_generator:
            try:
                self.logger.info("🧠 Using Gemini AI to generate SQL query")
                
                # Use the full query_and_execute method to get SQL + analysis
                gemini_result = self.gemini_generator.query_and_execute(intent["query_text"])
                
                if gemini_result["status"] == "success" and gemini_result["validation"]["is_safe"]:
                    # Extract execution results
                    execution = gemini_result.get("execution", {})
                    
                    plan["queries"].append({
                        "type": "gemini_generated",
                        "method": "execute_query",
                        "params": {
                            "sql": gemini_result["generated_sql"],
                            "return_format": "dict",
                            "user_query": intent["query_text"],
                            "analysis": gemini_result.get("analysis", "")  # Pass Gemini analysis
                        },
                        "gemini_metadata": {
                            "validation": gemini_result["validation"],
                            "ai_model": gemini_result.get("ai_model", "gemini-2.5-flash"),
                            "has_analysis": bool(gemini_result.get("analysis"))
                        },
                        "precomputed_result": execution  # Pass the already-executed results
                    })
                    
                    plan["gemini_powered"] = True
                    self.logger.info(f"✅ Gemini generated SQL: {gemini_result['generated_sql'][:100]}...")
                    if gemini_result.get("analysis"):
                        self.logger.info(f"✅ Gemini analysis: {gemini_result['analysis'][:80]}...")
                    return plan
                else:
                    self.logger.warning(f"⚠️ Gemini SQL validation failed, falling back to hardcoded patterns")
            except Exception as e:
                self.logger.error(f"❌ Gemini SQL generation failed: {e}, falling back to hardcoded patterns")
        
        # Fallback to hardcoded patterns
        self.logger.info("📋 Using hardcoded SQL patterns")
        
        # Float ID lookup
        if entities["float_ids"]:
            for float_id in entities["float_ids"]:
                plan["queries"].append({
                    "type": "float_lookup",
                    "method": "get_profiles_by_float_id",
                    "params": {"float_id": float_id, "include_measurements": True}
                })
        
        # Regional queries
        elif entities["regions"]:
            for region in entities["regions"]:
                plan["queries"].append({
                    "type": "regional_search",
                    "method": "get_profiles_by_region", 
                    "params": {"region": region, "limit": 50}
                })
        
        # Temporal queries
        elif entities["temporal"]["relative_time"] == "recent":
            plan["database"] = "live"  # Use live data for recent queries
            plan["queries"].append({
                "type": "recent_data",
                "method": "get_database_stats",
                "params": {}
            })
        
        return plan
    
    def _build_vector_plan(self, entities: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Build vector-only execution plan"""
        
        # Generate semantic query
        query_parts = []
        
        if entities["parameters"]:
            query_parts.extend(entities["parameters"])
        
        if entities["regions"]:
            query_parts.extend(entities["regions"])
        
        if entities["institutions"]:
            query_parts.extend([f"{inst} floats" for inst in entities["institutions"]])
        
        if entities["depth_terms"]:
            query_parts.extend([f"{term} water" for term in entities["depth_terms"]])
        
        semantic_query = " ".join(query_parts) if query_parts else intent["query_text"]
        
        return {
            "strategy": "vector_only",
            "collection": "january",
            "query": semantic_query,
            "n_results": 20,
            "filters": self._build_vector_filters(entities)
        }
    
    def _build_hybrid_plan(self, entities: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Build hybrid execution plan"""
        
        return {
            "strategy": "hybrid",
            "execution_steps": [
                {
                    "step": 1,
                    "type": "vector_search",
                    "query": self._build_vector_plan(entities, intent)["query"],
                    "n_results": 50
                },
                {
                    "step": 2, 
                    "type": "sql_refinement",
                    "method": "get_measurements_by_profile_ids",
                    "params": {"parameters": entities["parameters"] or ["temperature", "salinity"]}
                }
            ]
        }
    
    def _build_fallback_plan(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Build fallback plan for unclear queries"""
        
        return {
            "strategy": "fallback",
            "action": "general_search",
            "query": intent["query_text"],
            "suggestion": "Please be more specific about region, time period, or parameters"
        }
    
    def _build_vector_filters(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Build filters for vector search"""
        filters = {}
        
        if entities["regions"]:
            filters["region"] = entities["regions"][0]  # Use first region
        
        if entities["temporal"]["seasons"]:
            filters["season"] = entities["temporal"]["seasons"][0]  # Use first season
        
        if entities["institutions"]:
            filters["institution"] = entities["institutions"][0]  # Use first institution
        
        return filters


def test_query_builder():
    """Test the query builder tool"""
    print("🧪 Testing Query Builder Tool...")
    
    builder = QueryBuilderTool()
    
    test_queries = [
        "Show me data from float 1902482",
        "Find profiles in the Arabian Sea from winter 2025",
        "What's the latest temperature data?",
        "Compare salinity profiles from INCOIS floats",
        "Show me deep water measurements"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        
        # Analyze intent
        intent = builder.analyze_intent(query)
        print(f"   Type: {intent['query_type']}")
        print(f"   Strategy: {intent['strategy']}")
        print(f"   Confidence: {intent['confidence']:.2f}")
        
        # Build execution plan
        plan = builder.build_execution_plan(intent)
        print(f"   Plan: {plan['strategy']}")
    
    print("\n✅ Query Builder Tool testing complete!")


if __name__ == "__main__":
    test_query_builder()
