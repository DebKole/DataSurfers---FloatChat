"""
Data Access Orchestrator for FloatChat MCP Server
Coordinates all data access tools to execute complex queries
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import time

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from float_chat_mcp.data_access_tools.query_builder_tool import QueryBuilderTool
from float_chat_mcp.data_access_tools.vector_retrieval_tool import VectorRetrievalTool
from float_chat_mcp.data_access_tools.db_executor_tool import DatabaseExecutorTool
from float_chat_mcp.data_access_tools.analysis_tools_wrapper import AnalysisToolsWrapper

class DataAccessOrchestrator:
    """Orchestrates all data access tools for intelligent query execution"""
    
    def __init__(self, use_gemini: bool = True, enable_cache: bool = True):
        """
        Initialize all data access tools
        
        Args:
            use_gemini: Whether to use Gemini AI for SQL generation
            enable_cache: Whether to enable caching
        """
        self.query_builder = QueryBuilderTool(use_gemini=use_gemini)
        self.vector_tool = VectorRetrievalTool()
        self.db_tool = DatabaseExecutorTool(enable_cache=enable_cache)
        self.analysis_wrapper = AnalysisToolsWrapper()
    
    def execute_query(self, user_query: str) -> Dict[str, Any]:
        """
        Execute a complete data access workflow
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Complete query results with metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Analyze intent and build execution plan
            print(f"🧠 Analyzing query: '{user_query}'")
            intent = self.query_builder.analyze_intent(user_query)
            plan = self.query_builder.build_execution_plan(intent)
            
            print(f"📋 Strategy: {plan['strategy']} (confidence: {intent['confidence']:.2f})")
            
            # Step 2: Execute based on strategy
            if plan["strategy"] == "sql_only":
                results = self._execute_sql_strategy(plan, intent)
            elif plan["strategy"] == "vector_only":
                results = self._execute_vector_strategy(plan, intent)
            elif plan["strategy"] == "hybrid":
                results = self._execute_hybrid_strategy(plan, intent)
            elif plan["strategy"] == "analysis":
                results = self._execute_analysis_strategy(plan, intent)
            else:
                results = self._execute_fallback_strategy(plan, intent)
            
            # Step 3: Add execution metadata
            execution_time = time.time() - start_time
            results.update({
                "query_metadata": {
                    "original_query": user_query,
                    "intent_analysis": intent,
                    "execution_plan": plan,
                    "execution_time": f"{execution_time:.2f}s",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
            
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "query": user_query,
                "execution_time": f"{time.time() - start_time:.2f}s"
            }
    
    def _execute_sql_strategy(self, plan: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL-only strategy"""
        print("🗄️ Executing SQL strategy...")
        
        results = {
            "status": "success",
            "strategy": "sql_only",
            "data_sources": [],
            "results": []
        }
        
        database = plan.get("database", "main")
        
        # Execute each query in the plan
        for query_spec in plan.get("queries", []):
            method_name = query_spec["method"]
            params = query_spec["params"]
            query_type = query_spec["type"]
            
            print(f"   📋 Executing: {method_name}")
            
            # Check if this is a Gemini-generated query with precomputed results
            if query_type == "gemini_generated" and "precomputed_result" in query_spec:
                print(f"   🧠 Gemini AI-powered query (precomputed)")
                
                # Use precomputed results (already executed by Gemini generator)
                result = query_spec["precomputed_result"]
                
                # Ensure analysis is in the result (check multiple locations)
                analysis = None
                if result.get("analysis"):
                    analysis = result["analysis"]
                elif params.get("analysis"):
                    analysis = params["analysis"]
                    result["analysis"] = analysis
                
                if analysis:
                    print(f"   🧠 Gemini Analysis: {analysis[:80]}...")
                else:
                    print(f"   ⚠️ No Gemini analysis found in result")
                
                if "gemini_metadata" in query_spec:
                    validation = query_spec['gemini_metadata']['validation']
                    print(f"   ✅ Validation: Safe={validation.get('is_safe')}, Warnings={len(validation.get('warnings', []))}")
                
                # Log result structure for debugging
                print(f"   📊 Result: {result.get('row_count', 0)} rows, status={result.get('status')}")
                
                results["results"].append({
                    "query_type": query_type,
                    "result": result,
                    "gemini_powered": True,
                    "params": params  # Include params for analysis extraction
                })
                results["data_sources"].append(f"PostgreSQL ({database}) + Gemini AI")
                
            elif hasattr(self.db_tool, method_name):
                # Execute normally for non-Gemini queries
                method = getattr(self.db_tool, method_name)
                result = method(database=database, **params)
                
                # Log the SQL query if available
                if isinstance(result, dict) and "sql" in result:
                    print(f"   🔍 SQL Query: {result['sql'][:100]}...")
                    if result.get("cache_hit"):
                        print(f"   💾 Cache HIT - Retrieved from Redis")
                    if result.get("analysis"):
                        print(f"   🧠 Gemini Analysis: {result['analysis'][:80]}...")
                
                results["results"].append({
                    "query_type": query_type,
                    "result": result,
                    "gemini_powered": query_type == "gemini_generated"
                })
                results["data_sources"].append(f"PostgreSQL ({database})")
        
        # If no specific queries, do a general search based on entities
        if not plan.get("queries"):
            entities = intent["entities"]
            
            if entities["regions"]:
                print(f"   📋 Fallback: Regional search for {entities['regions'][0]}")
                result = self.db_tool.get_profiles_by_region(
                    region=entities["regions"][0],
                    database=database
                )
                if isinstance(result, dict) and "sql" in result:
                    print(f"   🔍 SQL Query: {result['sql']}")
                
                results["results"].append({
                    "query_type": "regional_search",
                    "result": result
                })
                results["data_sources"].append(f"PostgreSQL ({database})")
            
            elif entities["float_ids"]:
                print(f"   📋 Fallback: Float search for {entities['float_ids'][0]}")
                result = self.db_tool.get_profiles_by_float_id(
                    float_id=entities["float_ids"][0],
                    database=database,
                    include_measurements=True
                )
                if isinstance(result, dict) and "sql" in result:
                    print(f"   🔍 SQL Query: {result['sql']}")
                
                results["results"].append({
                    "query_type": "float_lookup",
                    "result": result
                })
                results["data_sources"].append(f"PostgreSQL ({database})")
            
            elif entities["coordinates"]["lat_bounds"] or entities["coordinates"]["lng_bounds"]:
                # Handle coordinate-based queries (like "get float ids in region X to Y")
                print(f"   📋 Fallback: Coordinate-based search")
                lat_bounds = entities["coordinates"]["lat_bounds"]
                lng_bounds = entities["coordinates"]["lng_bounds"]
                
                # This is a spatial query - return empty result with helpful message
                result = {
                    "status": "success",
                    "message": f"Coordinate query detected but not handled by fallback. Try using more specific terms.",
                    "row_count": 0,
                    "data": [],
                    "columns": []
                }
                results["results"].append({
                    "query_type": "coordinate_search",
                    "result": result
                })
                results["data_sources"].append(f"PostgreSQL ({database})")
            
            else:
                print("   ⚠️ No specific entities found, returning empty result with helpful message")
                # Instead of database stats, return an empty result with a helpful message
                result = {
                    "status": "success",
                    "message": "No specific data found. Try being more specific about region, float ID, or time period.",
                    "row_count": 0,
                    "data": [],
                    "columns": []
                }
                results["results"].append({
                    "query_type": "no_results",
                    "result": result
                })
                results["data_sources"].append(f"PostgreSQL ({database})")
        
        return results
    
    def _execute_vector_strategy(self, plan: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute vector-only strategy"""
        print("🧠 Executing vector search strategy...")
        
        # Perform semantic search
        vector_result = self.vector_tool.search_profiles(
            query_text=plan["query"],
            collection=plan.get("collection", "january"),
            n_results=plan.get("n_results", 20),
            filters=plan.get("filters")
        )
        
        return {
            "status": "success",
            "strategy": "vector_only",
            "data_sources": ["ChromaDB Vector Search"],
            "results": [vector_result],
            "semantic_query": plan["query"]
        }
    
    def _execute_hybrid_strategy(self, plan: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hybrid strategy (vector + SQL)"""
        print("🔄 Executing hybrid strategy...")
        
        results = {
            "status": "success",
            "strategy": "hybrid",
            "data_sources": ["ChromaDB Vector Search", "PostgreSQL"],
            "results": [],
            "execution_steps": []
        }
        
        # Execute each step in the hybrid plan
        for step in plan["execution_steps"]:
            if step["type"] == "vector_search":
                print(f"   Step {step['step']}: Vector search...")
                vector_result = self.vector_tool.search_profiles(
                    query_text=step["query"],
                    n_results=step["n_results"]
                )
                
                results["execution_steps"].append({
                    "step": step["step"],
                    "type": "vector_search",
                    "result": vector_result
                })
                
                # Extract profile IDs for next step
                if vector_result["status"] == "success":
                    profile_ids = [
                        int(result["profile_id"]) 
                        for result in vector_result["results"]
                        if result["profile_id"].isdigit()
                    ]
                    
            elif step["type"] == "sql_refinement":
                print(f"   Step {step['step']}: SQL refinement...")
                if 'profile_ids' in locals() and profile_ids:
                    sql_result = self.db_tool.get_measurements_by_profile_ids(
                        profile_ids=profile_ids[:20],  # Limit to first 20
                        parameters=step["params"]["parameters"]
                    )
                    
                    results["execution_steps"].append({
                        "step": step["step"],
                        "type": "sql_refinement", 
                        "result": sql_result
                    })
        
        return results
    
    def _execute_fallback_strategy(self, plan: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fallback strategy for unclear queries"""
        print("❓ Executing fallback strategy...")
        
        # Try a general vector search
        vector_result = self.vector_tool.search_profiles(
            query_text=intent["query_text"],
            n_results=10
        )
        
        return {
            "status": "partial_success",
            "strategy": "fallback",
            "data_sources": ["ChromaDB Vector Search"],
            "results": [vector_result],
            "suggestion": plan.get("suggestion", "Please provide more specific query terms"),
            "message": "Query was unclear, showing general search results"
        }
    
    def _execute_analysis_strategy(self, plan: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis strategy (data fetch + analysis)"""
        print("📊 Executing analysis strategy...")
        
        results = {
            "status": "success",
            "strategy": "analysis",
            "analysis_type": plan["analysis_type"],
            "data_sources": [],
            "fetched_data": None,
            "analysis_result": None
        }
        
        try:
            # Step 1: Fetch data
            print(f"   Step 1: Fetching data for analysis...")
            data_result = self._fetch_data_for_analysis(plan, intent)
            
            if data_result["status"] != "success":
                return {
                    "status": "error",
                    "error": "Data fetch failed",
                    "details": data_result,
                    "step": "data_fetch"
                }
            
            results["fetched_data"] = data_result
            results["data_sources"] = data_result.get("data_sources", [])
            
            # Extract actual data from result
            data_list = self._extract_data_list(data_result)
            
            if not data_list:
                return {
                    "status": "error",
                    "error": "No data found for analysis",
                    "step": "data_fetch"
                }
            
            print(f"   ✅ Fetched {len(data_list)} data points")
            
            # Step 2: Handle comparison (multiple datasets)
            if plan["analysis_type"] == "comparison":
                results = self._execute_comparison_analysis(plan, intent, results)
            else:
                # Step 2: Run analysis on single dataset
                print(f"   Step 2: Running {plan['analysis_type']} analysis...")
                analysis_result = self.analysis_wrapper.execute_analysis(
                    analysis_type=plan["analysis_type"],
                    data=data_list,
                    parameters=plan.get("analysis_parameters", {})
                )
                
                if analysis_result.get("status") == "error":
                    return {
                        "status": "error",
                        "error": analysis_result.get("error", "Analysis failed"),
                        "step": "analysis"
                    }
                
                results["analysis_result"] = analysis_result
                print(f"   ✅ Analysis complete")
            
            return results
            
        except Exception as e:
            print(f"   ❌ Analysis strategy failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "strategy": "analysis",
                "step": "unknown"
            }
    
    def _fetch_data_for_analysis(self, plan: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data required for analysis using existing tools"""
        data_req = plan["data_requirements"]
        database = plan.get("database", "main")
        
        # Build a temporary SQL plan for data fetching
        temp_plan = {
            "strategy": "sql_only",
            "database": database,
            "queries": []
        }
        
        # Determine what data to fetch based on requirements
        if data_req["float_ids"]:
            # Fetch by float ID
            for float_id in data_req["float_ids"]:
                temp_plan["queries"].append({
                    "type": "float_lookup",
                    "method": "get_profiles_by_float_id",
                    "params": {
                        "float_id": float_id,
                        "include_measurements": True,
                        "limit": 500
                    }
                })
        elif data_req["regions"]:
            # Fetch by region
            for region in data_req["regions"]:
                temp_plan["queries"].append({
                    "type": "regional_search",
                    "method": "get_profiles_by_region",
                    "params": {
                        "region": region,
                        "limit": 200
                    }
                })
        else:
            # Fallback: general database query
            temp_plan["queries"].append({
                "type": "general_stats",
                "method": "get_database_stats",
                "params": {}
            })
        
        # Execute the data fetch
        return self._execute_sql_strategy(temp_plan, intent)
    
    def _extract_data_list(self, data_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract flat list of measurements from orchestrator result"""
        data_list = []
        
        for result in data_result.get("results", []):
            if isinstance(result, dict) and "result" in result:
                inner = result["result"]
                if isinstance(inner, dict) and "data" in inner:
                    data_list.extend(inner["data"])
        
        return data_list
    
    def _execute_comparison_analysis(self, plan: Dict[str, Any], intent: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comparison analysis for multiple datasets"""
        print(f"   Step 2: Running comparison analysis...")
        
        data_req = plan["data_requirements"]
        
        # Need multiple entities for comparison
        entities_to_compare = data_req["float_ids"] or data_req["regions"]
        
        if len(entities_to_compare) < 2:
            return {
                "status": "error",
                "error": "Comparison requires at least 2 floats or regions",
                "step": "analysis"
            }
        
        # Fetch data for each entity separately
        datasets = []
        labels = []
        
        for entity in entities_to_compare[:5]:  # Limit to 5 comparisons
            # Create temp plan for this entity
            temp_plan = {
                "strategy": "sql_only",
                "database": plan.get("database", "main"),
                "queries": []
            }
            
            if entity in data_req["float_ids"]:
                temp_plan["queries"].append({
                    "type": "float_lookup",
                    "method": "get_profiles_by_float_id",
                    "params": {"float_id": entity, "include_measurements": True, "limit": 200}
                })
                labels.append(f"Float {entity}")
            else:
                temp_plan["queries"].append({
                    "type": "regional_search",
                    "method": "get_profiles_by_region",
                    "params": {"region": entity, "limit": 200}
                })
                labels.append(entity)
            
            # Fetch data
            entity_result = self._execute_sql_strategy(temp_plan, intent)
            entity_data = self._extract_data_list(entity_result)
            
            if entity_data:
                datasets.append(entity_data)
        
        if len(datasets) < 2:
            return {
                "status": "error",
                "error": "Insufficient data for comparison (need at least 2 datasets with data)",
                "step": "analysis"
            }
        
        # Determine comparison variable
        variable = "temperature"  # default
        if data_req["parameters"]:
            variable = data_req["parameters"][0]
        
        # Run comparison
        analysis_result = self.analysis_wrapper.execute_analysis(
            analysis_type="comparison",
            data=[],  # Not used for comparison
            parameters={
                "datasets": datasets,
                "labels": labels,
                "variable": variable,
                "axis_var": plan.get("analysis_parameters", {}).get("axis_var")
            }
        )
        
        if analysis_result.get("status") == "error":
            return {
                "status": "error",
                "error": analysis_result.get("error", "Comparison failed"),
                "step": "analysis"
            }
        
        results["analysis_result"] = analysis_result
        print(f"   ✅ Comparison complete")
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all data access components"""
        print("📊 Checking system status...")
        
        # Check vector database
        vector_stats = self.vector_tool.get_collection_stats()
        
        # Check main database
        main_db_stats = self.db_tool.get_database_stats("main")
        
        # Check live database
        live_db_stats = self.db_tool.get_database_stats("live")
        
        return {
            "status": "operational",
            "components": {
                "vector_database": {
                    "status": "online" if vector_stats["status"] == "success" else "error",
                    "stats": vector_stats.get("stats", {})
                },
                "main_database": {
                    "status": "online" if main_db_stats["status"] == "success" else "error",
                    "stats": main_db_stats.get("data", [])
                },
                "live_database": {
                    "status": "online" if live_db_stats["status"] == "success" else "error", 
                    "stats": live_db_stats.get("data", [])
                }
            },
            "capabilities": [
                "Natural language query understanding",
                "Semantic search across 2,434+ profiles",
                "SQL execution on 1.6M+ measurements",
                "Hybrid vector + SQL workflows",
                "Regional and temporal filtering",
                "Float-specific data retrieval"
            ]
        }

def demo_data_access_system():
    """Demonstrate the complete data access system"""
    print("🚀 FloatChat Data Access System Demo")
    print("=" * 50)
    
    orchestrator = DataAccessOrchestrator()
    
    # Demo queries showcasing different strategies
    demo_queries = [
        "Show me data from float 1902482",  # SQL-only
        "Find INCOIS floats in the Arabian Sea",  # Vector-only
        "Compare temperature profiles from winter 2025",  # Hybrid
        "What's the latest oceanographic data?",  # Temporal
        "Show me deep water salinity measurements"  # Semantic
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n🔍 Demo Query {i}: '{query}'")
        print("-" * 40)
        
        result = orchestrator.execute_query(query)
        
        print(f"✅ Status: {result['status']}")
        print(f"📋 Strategy: {result.get('strategy', 'unknown')}")
        print(f"⏱️ Time: {result.get('query_metadata', {}).get('execution_time', 'N/A')}")
        
        if result["status"] == "success":
            data_count = 0
            for res in result.get("results", []):
                if isinstance(res, dict):
                    # Handle direct results
                    if "row_count" in res:
                        data_count += res["row_count"]
                    elif "total_results" in res:
                        data_count += res["total_results"]
                    # Handle nested results (from orchestrator)
                    elif "result" in res and isinstance(res["result"], dict):
                        inner_result = res["result"]
                        if "row_count" in inner_result:
                            data_count += inner_result["row_count"]
                        elif "total_results" in inner_result:
                            data_count += inner_result["total_results"]
            
            print(f"📊 Data points: {data_count}")
        
        print()
    
    # System status
    print("\n📊 System Status Check")
    print("-" * 30)
    status = orchestrator.get_system_status()
    print(f"Overall Status: {status['status'].upper()}")
    
    for component, info in status["components"].items():
        print(f"  {component}: {info['status'].upper()}")
    
    print(f"\n🎯 System Capabilities:")
    for capability in status["capabilities"]:
        print(f"  ✅ {capability}")
    
    print("\n🎉 Data Access System Demo Complete!")

if __name__ == "__main__":
    demo_data_access_system()