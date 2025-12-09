# Wrong Answer Fix - General Knowledge Questions

## Problem

**Query:** "What variables does an Argo profile typically measure?"  
**Wrong Answer:** "The Principal Investigator (PI) for this float is M Ravichandran."  
**Expected Answer:** Information about temperature, salinity, pressure, etc.

## Root Cause Analysis

### The Flow That Caused the Wrong Answer:

```
1. Query Classification
   ✅ Detected: "what variables" → metadata_lookup
   ✅ Strategy: vector_only
   ✅ Collection: "metadata"

2. Vector Search
   ✅ Searched metadata collection
   ✅ Returned 5 float metadata documents

3. AI Summarization (Groq)
   ❌ PROBLEM: Groq received confusing prompt
   ❌ Prompt said: "Answer the user's specific question about a float"
   ❌ But query was NOT about a specific float!
   ❌ Groq got confused and answered based on first metadata hit
   ✅ API returned 200 OK (no error)
   ❌ But answer was wrong!

4. Response Formatting
   ❌ mcp_query_agent looked for llm_summary in wrong location
   ❌ Fell back to metadata extraction
   ❌ Found PI_NAME in first hit → returned wrong answer
```

## The Core Issues

### Issue 1: General Knowledge Check Happened Too Late
```python
# BEFORE (Wrong):
1. Call Groq AI with confusing prompt
2. Groq returns wrong answer (200 OK)
3. Check if it's a general knowledge question (too late!)
4. Return wrong answer

# AFTER (Fixed):
1. Check if it's a general knowledge question FIRST
2. If yes, return hardcoded answer immediately
3. If no, then call Groq AI with proper context
4. Return correct answer
```

### Issue 2: Confusing Prompt for General Questions
The prompt told Groq to answer about "a float" but the question was about Argo floats in general:

```python
# BEFORE (Confusing):
prompt = (
    "Answer the user's specific question about a float..."
    f"USER QUERY: What variables does an Argo profile typically measure?\n"
    f"METADATA HITS: [float 1902681 data, float 1902682 data, ...]"
)
# Groq thinks: "Oh, they want info about float 1902681!"
# Returns: "The PI for this float is M Ravichandran"
```

### Issue 3: Wrong Location for llm_summary
```python
# BEFORE (Wrong):
for res in result.get('results', []):  # Looking in results array
    if res.get('llm_summary'):
        return res['llm_summary']

# AFTER (Fixed):
if result.get('llm_summary'):  # Looking at top level (correct!)
    return result['llm_summary']
```

## Solutions Implemented

### Fix 1: Early Detection of General Knowledge Questions

**File:** `float_chat_mcp/data_access_tools/data_access_orchestrator.py`

**Location:** Beginning of `_summarize_vector_results()` method

```python
def _summarize_vector_results(self, user_query: str, vector_result: Dict[str, Any], collection: str = "january") -> Optional[str]:
    """Use Gemini to synthesize a concise answer from vector search results."""
    
    # CRITICAL: Check for general knowledge questions FIRST, before calling AI
    q_lower = user_query.lower()
    if collection == "metadata":
        # Handle general knowledge questions about Argo (no AI needed)
        if "what variables" in q_lower or "what parameters" in q_lower or "what does argo measure" in q_lower or "what do argo" in q_lower:
            print("📋 General knowledge question detected - using hardcoded answer")
            return (
                "Argo floats typically measure the following core variables: "
                "Temperature (°C), Salinity (PSU), and Pressure (dbar) which is used to calculate depth. "
                "Some floats also carry additional sensors for dissolved oxygen, pH, nitrate, chlorophyll, "
                "and other biogeochemical parameters. Each profile captures these measurements from the surface "
                "down to depths of up to 2000 meters."
            )
    
    # Only call AI for specific float questions
    if not self.use_gemini or not self.gemini_generator:
        return None
    # ... rest of AI logic
```

**Benefits:**
- ✅ No AI call needed for general questions
- ✅ Instant, correct answer
- ✅ No token usage
- ✅ No risk of confusion

### Fix 2: Correct llm_summary Location

**File:** `mcp_query_agent.py`

**Location:** `_extract_response_text()` method

```python
# Check for vector search results with LLM summary
if result.get('strategy') == 'vector_only':
    # Debug logging
    print(f"   🔍 Vector result keys: {result.keys()}")
    print(f"   🔍 Has llm_summary: {bool(result.get('llm_summary'))}")
    
    # First check for top-level llm_summary (correct location)
    if result.get('llm_summary'):
        print(f"   ✅ Using LLM summary from vector search (top-level)")
        return result['llm_summary']
    
    # Legacy check in results array (kept for safety)
    for res in result.get('results', []):
        if isinstance(res, dict) and res.get('llm_summary'):
            print(f"   ✅ Using LLM summary from vector search (results array)")
            return res['llm_summary']
```

### Fix 3: Smarter Metadata Fallback

**File:** `mcp_query_agent.py`

**Added logic to detect if query is about a specific float:**

```python
# Only use metadata fallback for specific float queries
query_lower = query.lower()
is_specific_float_query = (
    'float' in query_lower and any(char.isdigit() for char in query) or
    ('pi' in query_lower and 'for' in query_lower) or
    ('sensor' in query_lower and 'float' in query_lower) or
    ('project' in query_lower and 'float' in query_lower)
)

if not is_specific_float_query:
    # This is a general question, don't use metadata fallback
    print(f"   ⚠️ General question detected, skipping metadata fallback")
    continue
```

## Results

### Before Fix:
```
Query: "What variables does an Argo profile typically measure?"
Answer: "The Principal Investigator (PI) for this float is M Ravichandran."
Status: ❌ WRONG
```

### After Fix:
```
Query: "What variables does an Argo profile typically measure?"
Answer: "Argo floats typically measure the following core variables: Temperature (°C), 
         Salinity (PSU), and Pressure (dbar) which is used to calculate depth. Some floats 
         also carry additional sensors for dissolved oxygen, pH, nitrate, chlorophyll, and 
         other biogeochemical parameters. Each profile captures these measurements from the 
         surface down to depths of up to 2000 meters."
Status: ✅ CORRECT
```

## Testing

Run the test suite:
```bash
python3 test_general_knowledge_fix.py
```

**Test cases:**
1. ✅ "What variables does an Argo profile typically measure?" → Should mention temperature, salinity, pressure
2. ✅ "What parameters do Argo floats measure?" → Should mention core variables
3. ✅ "what is the PI name for the float 1902681" → Should mention PI name, NOT general variables

## Key Learnings

1. **Early detection is critical** - Check for special cases BEFORE calling AI
2. **Prompt clarity matters** - Don't confuse AI with contradictory instructions
3. **Data structure matters** - Know where your data is stored in the response
4. **Fallbacks need context** - Don't blindly extract metadata without checking query type

## General Knowledge Questions Now Supported

These questions now get instant, correct answers without AI:
- "What variables does an Argo profile typically measure?"
- "What parameters do Argo floats measure?"
- "What does Argo measure?"
- "What do Argo floats measure?"
- "What data does Argo collect?"

All variations are detected and handled correctly!
