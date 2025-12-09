# List Query Fix - Wrong Classification as Analysis

## Problem

**Query:** "List the Argo floats that were active in the Arabian Sea in February 2019"  
**Wrong Answer:** "I've crunched the numbers! 🔢 Here are the statistical summaries..."  
**Expected Answer:** A list of float IDs with their locations and dates

## Root Cause

The query was being **misclassified as an analysis query** (specifically `statistics`) instead of a data retrieval query.

### Why This Happened:

1. **Missing "list" keyword** in data retrieval detection
   - The LLM classification prompt included: "show", "get", "find", "retrieve"
   - But NOT "list", "which floats", "float IDs"
   
2. **Groq AI misinterpreted the intent**
   - Without explicit guidance, Groq saw "Arabian Sea" + "February 2019"
   - Thought: "They want analysis of this data"
   - Classified as: `analysis=true, type='statistics'`

3. **Heuristic fallback didn't catch it**
   - The keyword-based classification also didn't have "list" in data retrieval keywords
   - So it couldn't override the LLM's wrong classification

## The Classification Flow

### Before Fix (Wrong):
```
Query: "List the Argo floats..."
    ↓
Heuristic Check: No "list" in data_retrieval_keywords
    ↓
LLM Classification (Groq): "Hmm, they want data from a region/time... probably analysis?"
    ↓
Result: analysis=true, type='statistics'
    ↓
Strategy: 'analysis'
    ↓
Response: "I've crunched the numbers! 🔢..."
```

### After Fix (Correct):
```
Query: "List the Argo floats..."
    ↓
Heuristic Check: "list" found in data_retrieval_keywords ✅
    ↓
Skip analysis classification (is_data_retrieval=true)
    ↓
Result: query_type='spatial_temporal'
    ↓
Strategy: 'sql_only'
    ↓
SQL Generation: SELECT DISTINCT float_id, latitude, longitude, datetime...
    ↓
Response: Table with float IDs and locations
```

## Solutions Implemented

### Fix 1: Comprehensive Data Retrieval Keywords

**File:** `float_chat_mcp/data_access_tools/query_builder_tool.py`

**Location:** `_classify_query_type()` method

```python
# BEFORE: Missing many common keywords
data_retrieval_keywords = ['show me', 'get me', 'give me', 'find', 'retrieve']

# AFTER: Comprehensive list including standalone verbs
data_retrieval_keywords = [
    'list', 'list the', 'list all',
    'show', 'show me', 'show all', 'show the',  # Added standalone 'show'
    'get', 'get me', 'get all', 'get the',      # Added standalone 'get'
    'give', 'give me', 'give all',              # Added standalone 'give'
    'which floats', 'what floats', 'float ids',
    'find', 'find me', 'find all',
    'retrieve', 'fetch', 'return'
]
is_data_retrieval = any(keyword in query_lower for keyword in data_retrieval_keywords)

# Only classify as analysis if NOT a data retrieval query
if not is_data_retrieval:
    for category, keywords in analysis_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            return "analysis_query"
```

**Key improvement:** Added standalone verbs like "show", "get", "give" without requiring "me" after them.

### Fix 2: Enhanced LLM Classification with Examples

**File:** `float_chat_mcp/data_access_tools/query_builder_tool.py`

**Location:** `_classify_analysis_llm()` method

```python
# BEFORE: Vague rules without examples
"- If the user asks to 'show', 'get', 'find', 'retrieve' data WITHOUT explicit analysis keywords..."

# AFTER: Explicit rules with concrete examples
prompt = (
    "Rules:\n"
    "- **CRITICAL DATA RETRIEVAL RULE**: If the user asks to 'list', 'show', 'get', 'find', 'retrieve', 'give', 'fetch', 'return' "
    "data/floats/profiles WITHOUT explicit analysis keywords (trend, plot, graph, chart, compare, statistics, mean, average, summarize), "
    "set analysis=false. These are DATA RETRIEVAL queries.\n"
    "- **EXAMPLES OF DATA RETRIEVAL** (analysis=false):\n"
    "  * 'Show floats in region X'\n"
    "  * 'List floats from time Y'\n"
    "  * 'Get profiles near location Z'\n"
    "  * 'Find floats within distance D'\n"
    "- **EXAMPLES OF ANALYSIS** (analysis=true):\n"
    "  * 'Plot temperature vs salinity' → ts_curve\n"
    "  * 'Show temperature trend' → temp_trend\n"
    "  * 'Calculate statistics' → statistics\n"
    "  * 'Compare two floats' → comparison\n"
    "- **DEFAULT**: If unsure, set analysis=false. Return minimal JSON."
)
```

**Key improvement:** Added concrete examples so the LLM can pattern-match correctly.

### Fix 3: LLM Can Override Heuristics

**File:** `float_chat_mcp/data_access_tools/query_builder_tool.py`

**Location:** `analyze_intent()` method

```python
# NEW: Allow LLM to explicitly override heuristic classification
if analysis_llm and analysis_llm.get("analysis") is False:
    # LLM explicitly said this is NOT analysis - trust it and override heuristics
    if query_type == "analysis_query":
        self.logger.info(f"🔄 LLM overriding heuristic: NOT analysis")
        query_type = "spatial_temporal" if entities["regions"] and entities["temporal"]["years"] else "spatial"
```

**Key improvement:** When the LLM says `analysis=false`, it can now override incorrect heuristic classifications.

### Fix 4: Improve SQL Generation for List Queries

**File:** `groq_sql_generator.py`

**Location:** IMPORTANT RULES section

```python
# Added specific guidance for list queries
8. **SELECT ONLY RELEVANT COLUMNS** (Strict Column Rule):
   - **ALWAYS INCLUDE**: global_profile_id, float_id, latitude, longitude, datetime
   - **IF USER ASKS FOR "LIST" or "WHICH FLOATS"**: Return DISTINCT float_id, latitude, longitude, datetime (one row per float)
   - **IF USER ASKS FOR PARAMETER** (e.g., temperature): Include the parameter AND its QC column
   - **DO NOT** use SELECT * unless explicitly asked.
9. **FOR "LIST" QUERIES**: Use SELECT DISTINCT float_id to avoid duplicates, and include location/date for context
```

## Expected SQL for List Query

For: "List the Argo floats that were active in the Arabian Sea in February 2019"

```sql
-- DATABASE: argo_indian_ocean_19
SELECT DISTINCT 
    ap.float_id,
    ap.latitude,
    ap.longitude,
    ap.datetime
FROM argo_profiles ap
WHERE ap.latitude BETWEEN 0 AND 30
  AND ap.longitude BETWEEN 50 AND 80
  AND ap.datetime BETWEEN '2019-02-01' AND '2019-02-28'
ORDER BY ap.float_id, ap.datetime DESC
LIMIT 100;
```

## Testing

Run the test suite:
```bash
python3 test_list_query_fix.py
```

**Test cases:**
1. ✅ "List the Argo floats that were active in the Arabian Sea in February 2019" → sql_only
2. ✅ "Which floats were in the Bay of Bengal in 2020?" → sql_only
3. ✅ "Show me the float IDs in Arabian Sea" → sql_only
4. ✅ "Get me all floats from January 2019" → sql_only
5. ✅ "Show temperature statistics for Arabian Sea" → analysis (correct!)

## Data Retrieval vs Analysis

### Data Retrieval Queries (sql_only):
- "List the floats..."
- "Which floats..."
- "Show me float IDs..."
- "Get me floats..."
- "Find floats..."
- "Give me data..."

### Analysis Queries (analysis strategy):
- "Show temperature statistics..."
- "Plot temperature vs salinity..."
- "Compare floats..."
- "Calculate average temperature..."
- "Show trend over time..."

## Key Learnings

1. **Keywords matter** - "list" is a common data retrieval verb that was missing
2. **Heuristics first** - Check simple patterns before calling expensive LLM
3. **Explicit guidance** - LLMs need very explicit instructions about edge cases
4. **Test edge cases** - "list" queries are common but were not tested

## Impact

### Before Fix:
- ❌ List queries → Wrong analysis response
- ❌ Users confused by statistical summaries
- ❌ No actual float IDs returned

### After Fix:
- ✅ List queries → Correct SQL query
- ✅ Returns actual float IDs with locations
- ✅ Clear, expected results

## Related Queries Now Fixed

All these queries will now work correctly:
- "List all floats in [region]"
- "Which floats were active in [time period]"
- "Show me float IDs for [conditions]"
- "Get me all floats from [location/time]"
- "Find floats that [criteria]"
- "Give me the floats in [region]"
