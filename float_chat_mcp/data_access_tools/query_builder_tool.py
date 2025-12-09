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
        
        # NEW: Try to resolve unknown locations if no coordinates found
        if not entities["coordinates"]["lat_bounds"] and not entities["regions"]:
            potential_locs = self._extract_potential_locations(query_text, entities)
            if potential_locs:
                # Try to resolve the first one
                resolved = self._resolve_location_with_gemini(potential_locs[0])
                if resolved:
                    self.logger.info(f"📍 Resolved location '{potential_locs[0]}' to {resolved}")
                    entities["coordinates"] = resolved
                    # Add a special flag so we know this was resolved
                    entities["resolved_location"] = potential_locs[0]
        
        # Determine query type
        query_type = self._classify_query_type(entities, query_lower)

        # Try LLM-based analysis classification first; if it decides analysis, lock it in
        analysis_llm = self._classify_analysis_llm(query_text, entities)
        analysis_type = None
        analysis_decider = "none"
        if analysis_llm and analysis_llm.get("analysis") is True and analysis_llm.get("type"):
            query_type = "analysis_query"
            analysis_type = analysis_llm.get("type")
            analysis_decider = "llm"
        elif query_type == "analysis_query":
            analysis_decider = "heuristic"

        # First try LLM-driven strategy selection (sql vs general/vector)
        llm_strategy = self._choose_strategy_llm(query_text, entities, query_type)

        # Fallback: rule-based strategy selection
        strategy = llm_strategy or self._choose_strategy(query_type, entities, query_lower)
        strategy_decider = "llm" if llm_strategy else "heuristic"
        
        result = {
            "query_text": query_text,
            "entities": entities,
            "query_type": query_type,
            "strategy": strategy,
            "confidence": self._calculate_confidence(entities, query_type),
            "strategy_decider": strategy_decider,
            "analysis_decider": analysis_decider
        }
        if analysis_type:
            result["analysis_type"] = analysis_type
        return result
    
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
        elif strategy == "analysis":  # NEW
            return self._build_analysis_plan(entities, intent)
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
        
        # Extract months
        months_map = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
        }
        for month, num in months_map.items():
            if month in query_lower:
                temporal_info["months"].append(num)
        
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

    def _extract_potential_locations(self, query_text: str, known_entities: Dict[str, Any]) -> List[str]:
        """Extract potential location names that aren't already known regions"""
        # Simple heuristic: look for "near X", "in X", "around X"
        # This is a basic extraction; for robust extraction, we might need NER or LLM
        potential_locs = []
        
        # Patterns to look for locations
        patterns = [
            r'\bnear\s+([a-zA-Z\s]+)',
            r'\baround\s+([a-zA-Z\s]+)',
            r'\boff\s+the\s+coast\s+of\s+([a-zA-Z\s]+)',
            r'\boff\s+([a-zA-Z\s]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)
            for match in matches:
                loc = match.strip()
                # Filter out known keywords to avoid false positives
                # Also filter out common stop words that might be matched
                stop_words = ["the", "a", "an", "me", "us", "it", "them", "data", "show", "get", "find"]
                
                # Stop capturing at common prepositions
                prepositions = ["from", "in", "during", "since", "to", "at", "for", "with"]
                
                # Clean up the match
                words = loc.split()
                clean_words = []
                for word in words:
                    if word.lower() in prepositions:
                        break
                    clean_words.append(word)
                
                loc = " ".join(clean_words)
                
                if loc and loc.lower() not in self.regions and loc.lower() not in stop_words:
                    potential_locs.append(loc)
                    
        return potential_locs

    def _resolve_location_with_gemini(self, location_name: str) -> Optional[Dict[str, List[float]]]:
        """Use Gemini to resolve a location name to a bounding box"""
        if not self.use_gemini or not self.gemini_generator:
            return None
            
        try:
            model = getattr(self.gemini_generator, "model", None)
            if model is None:
                return None
                
            prompt = (
                f"Identify the geographic bounding box and center point for the marine location: '{location_name}'. "
                "Return ONLY a JSON object with keys 'lat_bounds' ([min_lat, max_lat]), 'lng_bounds' ([min_lng, max_lng]), "
                "and 'center' ([lat, lng]). "
                "If the location is not a valid marine/coastal location, return null."
                "Example: {'lat_bounds': [18.0, 20.0], 'lng_bounds': [72.0, 73.5], 'center': [19.07, 72.87]}"
            )
            
            resp = model.generate_content(prompt)
            text = (resp.text or "").strip()
            
            # Clean and parse JSON
            cleaned = text.replace("```json", "").replace("```", "").strip()
            if not cleaned: 
                return None
                
            data = json.loads(cleaned)
            
            if data and 'lat_bounds' in data and 'lng_bounds' in data:
                result = {
                    "lat_bounds": data['lat_bounds'],
                    "lng_bounds": data['lng_bounds']
                }
                if 'center' in data:
                    result['center'] = data['center']
                return result
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to resolve location '{location_name}': {e}")
            return None
    
    def _classify_query_type(self, entities: Dict[str, Any], query_lower: str) -> str:
        """Classify the type of query based on entities"""
        
        # NEW: Check for analysis keywords first
        analysis_keywords = {
            'trend': ['trend', 'trending', 'time series', 'over time'],
            'curve': ['curve', 't-s', 'ts', 't-d', 'td', 'temperature-salinity', 'temperature-depth', 'vertical profile', 'chart', 'plot', 'graph'],
            'comparison': ['compare', 'comparison', 'versus', 'vs', 'difference between'],
            'statistics': ['statistics', 'stats', 'summary', 'summarize', 'average', 'mean']
        }
        
        for category, keywords in analysis_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return "analysis_query"
        
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
        if any(word in query_lower for word in ["analyze", "pattern", "anomaly"]):
            return "semantic_analysis"
        
        return "general_search"
    
    def _choose_strategy(self, query_type: str, entities: Dict[str, Any], query_lower: str) -> str:
        """Choose execution strategy based on query type and complexity"""
        
        # NEW: Route analysis queries to analysis strategy
        if query_type == "analysis_query":
            return "analysis"
        
        # Direct SQL for simple lookups
        if query_type == "float_lookup":
            return "sql_only"
        
        # Vector search for semantic queries
        if query_type == "semantic_analysis":
            return "vector_only"
        
        # Hybrid for complex spatial-temporal queries
        if query_type == "spatial_temporal":
            return "sql_only"  # Prefer SQL for specific region + time queries
        
        # SQL for simple spatial/temporal queries
        if query_type in ["spatial", "temporal"]:
            return "sql_only"
        
        # Vector for institution/parameter analysis
        if query_type in ["institution_analysis", "parameter_analysis"]:
            return "vector_only"
        
        # Default to hybrid for general searches
        return "hybrid"

    def _classify_analysis_llm(self, query_text: str, entities: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use Gemini to classify whether the query requests an analysis/graph and which type.

        Returns a dict like {analysis: bool, type: 'ts_curve'|'td_curve'|'temp_trend'|'sal_trend'|'comparison'|'statistics'}
        or None on failure/unavailable.
        """
        if not self.use_gemini or not self.gemini_generator:
            return None
        try:
            model = getattr(self.gemini_generator, "model", None)
            if model is None:
                return None
            guidance = (
                "Classify the user request for oceanographic analysis. Return JSON only with keys 'analysis' (true/false) "
                "and 'type' if analysis is true. Valid 'type' values: 'ts_curve', 'td_curve', 'temp_trend', 'sal_trend', "
                "'comparison', 'statistics'. Consider synonyms like graph/plot/chart/profile and temperature-salinity (TS), "
                "temperature-depth (TD), trend, compare."
            )
            hint = {
                "float_ids": entities.get("float_ids", []),
                "regions": entities.get("regions", []),
                "parameters": entities.get("parameters", []),
            }
            prompt = (
                f"{guidance}\n\nQUERY: {query_text}\nHINT: {json.dumps(hint)}\n"
                "Rules:\n- If the user asks for a graph/plot/chart/curve/profile, set analysis=true.\n"
                "- Map 'temperature salinity' to 'ts_curve', 'temperature depth' or 'vertical profile' to 'td_curve'.\n"
                "- If 'trend' with temperature/salinity, choose 'temp_trend' or 'sal_trend'. If 'compare', choose 'comparison'.\n"
                "- If unsure, set analysis=false. Return minimal JSON."
            )
            resp = model.generate_content(prompt)
            text = (resp.text or "").strip()
            try:
                parsed = json.loads(text)
            except Exception:
                cleaned = text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(cleaned) if cleaned.startswith("{") else {}
            if not isinstance(parsed, dict):
                return None
            # Normalize type
            t = parsed.get("type")
            if isinstance(t, str):
                t = t.strip().lower()
            if parsed.get("analysis") and t in {"ts_curve", "td_curve", "temp_trend", "sal_trend", "comparison", "statistics"}:
                return {"analysis": True, "type": t}
            return {"analysis": False}
        except Exception:
            return None

    def _choose_strategy_llm(self, query_text: str, entities: Dict[str, Any], query_type: str) -> Optional[str]:
        """Use Gemini to classify the query as SQL-based or General (vector).

        Returns one of: 'sql_only', 'vector_only', 'analysis' or None on failure.
        We keep analysis routing keyword-based to reduce LLM ambiguity; if the
        query_type already indicates analysis, prefer 'analysis'.
        """
        # If Gemini is not available, skip
        if not self.use_gemini or not self.gemini_generator:
            return None

        # Respect explicit analysis detection from heuristics
        if query_type == "analysis_query":
            return "analysis"

        try:
            # Reuse the already-configured Gemini model from the SQL generator
            model = getattr(self.gemini_generator, "model", None)
            if model is None:
                return None

            # Minimal, robust JSON classification prompt
            sys_prompt = (
                "You are a routing classifier. Decide if a user query should be answered "
                "by SQL over a relational database or by a general semantic/vector search.\n\n"
                "Return a compact JSON object with a single key 'route' whose value is one of: "
                "'sql' or 'general'. Do not add any extra text."
            )

            # Provide lightweight entity cues (best-effort; safe if missing)
            entities_hint = {
                "regions": entities.get("regions", []),
                "parameters": entities.get("parameters", []),
                "float_ids": entities.get("float_ids", []),
                "temporal": entities.get("temporal", {}),
            }

            prompt = (
                f"{sys_prompt}\n\n"
                f"QUERY: {query_text}\n"
                f"ENTITIES_HINT: {json.dumps(entities_hint)}\n"
                "Rules:\n"
                "- Prefer 'sql' when the user asks to show/get/find data, float IDs, profiles, measurements, specific regions or time windows.\n"
                "- Prefer 'general' when the user asks conceptual/overview questions or free-form discovery where structured SQL is unclear.\n"
                "- If unsure, choose 'general'.\n"
            )

            resp = model.generate_content(prompt)
            text = (resp.text or "").strip()

            # Attempt to parse JSON safely
            try:
                parsed = json.loads(text)
                route = str(parsed.get("route", "")).lower()
            except Exception:
                # Handle non-JSON outputs like ```json blocks
                cleaned = text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(cleaned) if cleaned.startswith("{") else {}
                route = str(parsed.get("route", "")).lower()

            if route == "sql":
                return "sql_only"
            if route == "general":
                return "vector_only"
        except Exception:
            # Swallow and fallback to heuristics
            return None

        return None
    
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
            "database": "argo_indian_ocean_25",  # Default to 2025 data
            "queries": [],
            "parameters": {},
            "gemini_powered": False,
            "fallback_reason": None
        }
        
        # Try Gemini AI first if available
        if self.use_gemini and self.gemini_generator:
            try:
                self.logger.info("🧠 Using Gemini AI to generate SQL query")
                
                # Prepare user query with context if available
                user_query_with_context = intent["query_text"]
                
                # Add location context for nearest neighbor search
                if intent["entities"].get("resolved_location") and intent["entities"].get("coordinates", {}).get("center"):
                    loc_name = intent["entities"]["resolved_location"]
                    center = intent["entities"]["coordinates"]["center"]
                    user_query_with_context += f" (Context: Location '{loc_name}' is at {center[0]}N, {center[1]}E. Use nearest neighbor search.)"
                
                # Use the full query_and_execute method to get SQL + analysis
                gemini_result = self.gemini_generator.query_and_execute(user_query_with_context)
                
                # Accept Gemini results if:
                # 1. Status is success
                # 2. SQL is safe (validation passed safety checks)
                # 3. We have either execution results OR analysis
                validation = gemini_result.get("validation", {})
                execution = gemini_result.get("execution", {})
                has_data = execution.get("status") == "success" and execution.get("row_count", 0) >= 0
                has_analysis = bool(gemini_result.get("analysis"))
                is_safe = validation.get("is_safe", False)
                
                # Use Gemini if it's safe and we have usable results
                if gemini_result.get("status") == "success" and is_safe and (has_data or has_analysis):
                    plan["queries"].append({
                        "type": "gemini_generated",
                        "method": "execute_query",
                        "params": {
                            "sql": gemini_result["generated_sql"],
                            "return_format": "dict",
                            "user_query": intent["query_text"], # Keep original query for display
                            "analysis": gemini_result.get("analysis", "")  # Pass Gemini analysis
                        },
                        "gemini_metadata": {
                            "validation": validation,
                            "ai_model": gemini_result.get("ai_model", "gemini-2.5-flash"),
                            "has_analysis": has_analysis
                        },
                        "precomputed_result": execution  # Pass the already-executed results
                    })
                    
                    plan["gemini_powered"] = True
                    self.logger.info(f"✅ Gemini generated SQL: {gemini_result['generated_sql'][:100]}...")
                    if has_analysis:
                        self.logger.info(f"✅ Gemini analysis: {gemini_result['analysis'][:80]}...")
                    
                    # Log warnings but don't fail
                    if validation.get("warnings"):
                        self.logger.info(f"ℹ️ Validation warnings (non-blocking): {validation['warnings']}")
                    
                    return plan
                else:
                    # Log the actual reason for fallback
                    fallback_reasons = []
                    if gemini_result.get("status") != "success":
                        fallback_reasons.append(f"status={gemini_result.get('status')}")
                    if not is_safe:
                        fallback_reasons.append("unsafe SQL")
                    if not has_data and not has_analysis:
                        fallback_reasons.append("no data or analysis")
                    
                    self.logger.warning(
                        "⚠️ Gemini result not usable, falling back. Reasons: %s. SQL=%s",
                        ", ".join(fallback_reasons),
                        gemini_result.get("generated_sql", "<none>")[:100]
                    )
                    plan["fallback_reason"] = {
                        "type": "gemini_unusable",
                        "reasons": fallback_reasons,
                        "validation": validation,
                        "generated_sql": gemini_result.get("generated_sql", "")
                    }
            except Exception as e:
                self.logger.error("❌ Gemini SQL generation failed: %s. Falling back to hardcoded patterns", e)
                plan["fallback_reason"] = {
                    "type": "gemini_exception",
                    "error": str(e)
                }
        
        # Fallback to hardcoded patterns
        self.logger.info("📋 Using hardcoded SQL patterns")
        
        # Float ID lookup
        if entities["float_ids"]:
            for float_id in entities["float_ids"]:
                q = {
                    "type": "float_lookup",
                    "method": "get_all_profiles_by_float_id",
                    "params": {"float_id": float_id, "include_measurements": True}
                }
                plan["queries"].append(q)
                self.logger.info("➡️ Fallback executing: %s params=%s", q["method"], q["params"])
        
        # Regional queries
        elif entities["regions"]:
            # Determine database based on year if present
            database = "argo_indian_ocean_25"  # Default
            start_date = None
            end_date = None
            
            if entities["temporal"]["years"]:
                year = entities["temporal"]["years"][0]
                if 2015 <= year <= 2025:
                    database = f"argo_indian_ocean_{year % 100:02d}"
                
                # If month is also present, calculate date range
                if entities["temporal"]["months"]:
                    month = entities["temporal"]["months"][0]
                    start_date = f"{year}-{month:02d}-01"
                    # Simple end date calculation (handle December)
                    if month == 12:
                        end_date = f"{year+1}-01-01"
                    else:
                        end_date = f"{year}-{month+1:02d}-01"
            
            # Update plan database
            plan["database"] = database
            
            for region in entities["regions"]:
                params = {"region": region, "limit": 50}
                if start_date:
                    params["start_date"] = start_date
                if end_date:
                    params["end_date"] = end_date
                    
                q = {
                    "type": "regional_search",
                    "method": "get_profiles_by_region", 
                    "params": params
                }
                plan["queries"].append(q)
                self.logger.info("➡️ Fallback executing: %s params=%s db=%s", q["method"], q["params"], database)
        
        # Temporal queries
        elif entities["temporal"]["relative_time"] == "recent":
            plan["database"] = "live"  # Use live data for recent queries
            q = {
                "type": "recent_data",
                "method": "get_database_stats",
                "params": {}
            }
            plan["queries"].append(q)
            self.logger.info("➡️ Fallback executing: %s", q["method"])
        
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
    
    def _build_analysis_plan(self, entities: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Build analysis execution plan"""
        
        query_lower = intent["query_text"].lower()
        
        # Determine specific analysis type
        # First check if LLM already determined the type
        analysis_type = intent.get("analysis_type")
        
        # If not, try to determine from keywords
        if not analysis_type:
            analysis_type = self._determine_analysis_type(query_lower, entities)
            
        # If still undetermined, default to statistics but log warning
        if not analysis_type:
            self.logger.warning("⚠️ Analysis type undetermined, defaulting to statistics")
            analysis_type = "statistics"
        
        # Extract analysis parameters
        parameters = self._extract_analysis_parameters(query_lower)
        
        # Determine data requirements
        data_requirements = {
            "float_ids": entities["float_ids"],
            "regions": entities["regions"],
            "parameters": entities["parameters"],
            "temporal": entities["temporal"]
        }
        
        # Determine database (main for historical, live for recent)
        database = "argo_indian_ocean_25"
        
        return {
            "strategy": "analysis",
            "analysis_type": analysis_type,
            "data_requirements": data_requirements,
            "analysis_parameters": parameters,
            "database": database
        }
    
    def _determine_analysis_type(self, query_lower: str, entities: Dict[str, Any]) -> Optional[str]:
        """Determine specific analysis type from query"""
        
        # Temperature trend
        if any(word in query_lower for word in ['temperature trend', 'temp trend', 'temperature over time']):
            return "temp_trend"
        
        # Salinity trend
        if any(word in query_lower for word in ['salinity trend', 'sal trend', 'salinity over time']):
            return "sal_trend"
        
        # Pressure trend
        if any(word in query_lower for word in ['pressure trend', 'depth trend']):
            return "pressure_trend"
        
        # T-S curve
        if any(word in query_lower for word in ['t-s', 'ts curve', 'temperature-salinity', 'temperature salinity']):
            return "ts_curve"
        
        # T-D curve (explicit or implied by temperature and depth)
        if any(word in query_lower for word in ['t-d', 'td curve', 'temperature-depth', 'vertical profile']):
            return "td_curve"
        if ('temperature' in query_lower or 'temp' in query_lower) and ('depth' in query_lower or 'pressure' in query_lower) and any(word in query_lower for word in ['chart', 'plot', 'graph', 'curve']):
            return "td_curve"
        
        # Comparison
        if any(word in query_lower for word in ['compare', 'comparison', 'versus', 'vs']):
            return "comparison"
        
        # Statistics
        if any(word in query_lower for word in ['statistics', 'stats', 'summary', 'summarize']):
            return "statistics"
        
        # Default: if "trend" is mentioned, assume temperature trend
        if 'trend' in query_lower:
            return "temp_trend"
            
        # Generic chart requests
        if any(word in query_lower for word in ['chart', 'plot', 'graph']):
            if 'salinity' in query_lower:
                return "sal_trend"
            if 'pressure' in query_lower:
                return "pressure_trend"
            # Default to temperature trend for generic charts
            return "temp_trend"
        
        # Return None if no specific analysis type is found
        return None
    
    def _extract_analysis_parameters(self, query_lower: str) -> Dict[str, Any]:
        """Extract analysis-specific parameters from query"""
        
        parameters = {}
        
        # Extract window size for trends
        window_match = re.search(r'window[=\s]+(\d+)', query_lower)
        if window_match:
            parameters['window'] = int(window_match.group(1))
        else:
            parameters['window'] = 20  # default
        
        # Extract axis variable for comparisons
        if 'by depth' in query_lower or 'vs depth' in query_lower:
            parameters['axis_var'] = 'depth'
        elif 'by time' in query_lower or 'over time' in query_lower:
            parameters['axis_var'] = 'datetime'
        elif 'by salinity' in query_lower:
            parameters['axis_var'] = 'salinity'
        elif 'by pressure' in query_lower:
            parameters['axis_var'] = 'pressure'
        
        return parameters
    
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
