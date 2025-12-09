# Frontend Query Fix - Cross-Year Queries

## Problem
**User Query:** "give temperature data between november 2016 and february 2017"

**System Response:** "I can provide temperature data between November 2016 and February 2017. Please specify a region..."

**Issue:** System was asking for clarification instead of executing the query, even though FDW setup was successful.

## Root Causes

### 1. Gemini Being Too Cautious
The AI was being overly cautious and asking for region specification instead of generating SQL for all regions.

### 2. Missing "give" in Action Verbs
The word "give" wasn't explicitly in the action verbs list, though it should have been caught by "give me".

## Solutions Applied

### 1. Updated `groq_sql_generator.py`

**Added explicit rules (using Groq AI):**
```python
IMPORTANT RULES:
3. **NO REGION SPECIFIED = RETURN ALL DATA** for that date range (don't ask for clarification)
14. **GENERATE SQL, DON'T ASK FOR CLARIFICATION** - if region not specified, query all regions
```

**Added critical instructions:**
```
**CRITICAL INSTRUCTIONS:**
1. **ALWAYS GENERATE SQL** - Never respond with text asking for clarification
2. **NO REGION = ALL REGIONS** - If user doesn't specify region, query all data for that date range
```

**Added example:**
```sql
-- Example: "give temperature data between november 2016 and february 2017"
-- DATABASE: argo_indian_ocean_25
SELECT ap.*, am.temperature_adjusted, am.temperature_adjusted_qc
FROM all_years_argo_profiles ap
JOIN all_years_argo_measurements am ON ap.global_profile_id = am.global_profile_id
WHERE ap.datetime >= '2016-11-01' AND ap.datetime <= '2017-02-28'
  AND am.temperature_adjusted_qc <= 2
ORDER BY ap.datetime DESC
```

### 2. Updated `mcp_query_agent.py`

**Added "give" to action verbs:**
```python
action_verbs = [
    'show', 'get', 'find', 'list', 'display', 'retrieve',
    'fetch', 'give me', 'show me', 'get me', 'give'  # Added 'give'
]
```

**Added debug logging:**
```python
print(f"   ✅ Detected data query (action verb: {[v for v in action_verbs if v in query_lower]})")
```

## Expected Behavior Now

### Query 1: "give data between november 2016 and february 2017"
```
✅ Detected as data query (action verb: 'give')
✅ Detected as cross-year query (2016 → 2017)
✅ Database: argo_indian_ocean_25 (FDW)
✅ SQL: SELECT * FROM all_years_argo_profiles 
        WHERE datetime >= '2016-11-01' AND datetime <= '2017-02-28'
        ORDER BY datetime DESC
✅ Returns: All profiles from Nov 2016 - Feb 2017 across all regions
```

### Query 2: "give temperature data between november 2016 and february 2017"
```
✅ Detected as data query (action verb: 'give')
✅ Detected as cross-year query (2016 → 2017)
✅ Database: argo_indian_ocean_25 (FDW)
✅ SQL: SELECT ap.*, am.temperature_adjusted, am.temperature_adjusted_qc
        FROM all_years_argo_profiles ap
        JOIN all_years_argo_measurements am ON ap.global_profile_id = am.global_profile_id
        WHERE ap.datetime >= '2016-11-01' AND ap.datetime <= '2017-02-28'
          AND am.temperature_adjusted_qc <= 2
        ORDER BY ap.datetime DESC
✅ Returns: Temperature measurements from Nov 2016 - Feb 2017 with QC filtering
```

### Query 3: "give temperature data between november 2016 and february 2017 in Arabian Sea"
```
✅ Detected as data query (action verb: 'give')
✅ Detected as cross-year query (2016 → 2017)
✅ Database: argo_indian_ocean_25 (FDW)
✅ SQL: SELECT ap.*, am.temperature_adjusted, am.temperature_adjusted_qc
        FROM all_years_argo_profiles ap
        JOIN all_years_argo_measurements am ON ap.global_profile_id = am.global_profile_id
        WHERE ap.datetime >= '2016-11-01' AND ap.datetime <= '2017-02-28'
          AND ap.latitude BETWEEN 0 AND 30
          AND ap.longitude BETWEEN 50 AND 80
          AND am.temperature_adjusted_qc <= 2
        ORDER BY ap.datetime DESC
✅ Returns: Temperature measurements from Nov 2016 - Feb 2017 in Arabian Sea
```

## Testing

### Test Script
Run the test script to verify:
```bash
python test_cross_year_query.py
```

Expected output:
```
🧪 Testing Cross-Year Query Generation
============================================================

🔍 Test 1: 'give data between november 2016 and february 2017'
------------------------------------------------------------
Cross-year detected: True
✅ SQL Generated:
   Database: argo_indian_ocean_25
   SQL: SELECT * FROM all_years_argo_profiles WHERE datetime >= '2016-11-01' AND datetime <= '2017-02-28' ORDER BY datetime DESC
   ✅ Using FDW views (all_years_argo_*)
```

### Manual Testing
1. Start the application
2. Try these queries:
   - "give data between november 2016 and february 2017"
   - "give temperature data between november 2016 and february 2017"
   - "show me salinity from december 2019 to march 2020"

### Expected Results
- ✅ No "please specify region" messages
- ✅ SQL generated immediately
- ✅ Data returned from multiple years
- ✅ FDW views used for cross-year queries

## Key Changes Summary

| File | Change | Purpose |
|------|--------|---------|
| `groq_sql_generator.py` | Added "NO REGION = ALL DATA" rule | Prevent asking for clarification |
| `groq_sql_generator.py` | Added "ALWAYS GENERATE SQL" instruction | Force SQL generation |
| `groq_sql_generator.py` | Added cross-year temperature example | Show proper FDW usage |
| `groq_sql_generator.py` | Uses Groq AI instead of Gemini | Improved SQL generation |
| `mcp_query_agent.py` | Added "give" to action verbs | Detect "give data" queries |
| `mcp_query_agent.py` | Added debug logging | Help troubleshoot routing |

## Verification Checklist

- [x] FDW setup successful (test queries work in psql)
- [x] Cross-year detection working
- [x] Action verb detection includes "give"
- [x] Gemini prompt instructs to generate SQL without asking
- [x] Example queries added to prompt
- [x] Debug logging added for troubleshooting
- [ ] Test with frontend (restart application)
- [ ] Verify "give data between november 2016 and february 2017" works
- [ ] Verify "give temperature data..." works
- [ ] Verify data is returned from both 2016 and 2017

## Next Steps

1. **Restart the application** to load the updated code
2. **Test the queries** in the frontend
3. **Check logs** for debug output showing query detection
4. **Verify results** contain data from both years

## Troubleshooting

### If still asking for region:
1. Check if Gemini API key is valid
2. Verify the prompt is being used (check logs)
3. Try running `test_cross_year_query.py` to see SQL generation

### If no data returned:
1. Verify FDW setup: `psql -U postgres -d argo_indian_ocean_25 -c "SELECT COUNT(*) FROM all_years_argo_profiles WHERE datetime >= '2016-11-01' AND datetime <= '2017-02-28';"`
2. Check if databases have data for those years
3. Verify QC filters aren't too restrictive

### If routing to LLM instead of data query:
1. Check debug logs for "Detected data query" message
2. Verify "give" is in action_verbs list
3. Check if query matches informational patterns
