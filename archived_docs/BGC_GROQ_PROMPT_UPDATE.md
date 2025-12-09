# BGC Data Support - Groq Model Prompt Update

## Overview
Updated the Groq model prompts in `main.py` and `groq_sql_generator.py` to support BGC (Biogeochemical) Argo float data queries.

## Changes Made

### 1. Main.py - Context Message Update

**Added BGC Capabilities:**
- Dissolved Oxygen (DOXY) - ocean oxygen content
- Chlorophyll-a (CHLA) - phytoplankton biomass indicator
- Nitrate - nutrient availability
- pH - ocean acidification indicator
- BBP700 - backscatter/particle concentration
- CDOM - colored dissolved organic matter

**Updated Example Queries:**
```
- "Get dissolved oxygen data from the Bay of Bengal"
- "What are the chlorophyll patterns in 2024?"
- "Show me nitrate levels near float 5906527"
- "Get pH measurements from the Arabian Sea"
```

### 2. Groq SQL Generator - Comprehensive BGC Support

#### Database Schema Information
Added BGC table relationships:
- `argo_bgc_profiles` - BGC float profile metadata
- `argo_bgc_measurements` - BGC measurements with biogeochemical parameters
- JSONB column `bgc_parameters` stores all BGC data

#### BGC Data Structure
```sql
-- BGC parameters stored as JSONB:
{
  "DOXY": {"value": 245.5, "qc": 1},
  "CHLA": {"value": 0.15, "qc": 2},
  "NITRATE": {"value": 5.2, "qc": 1}
}

-- Access BGC values:
(bgc_parameters->'DOXY'->>'value')::float

-- Access QC flags:
(bgc_parameters->'DOXY'->>'qc')::int

-- Check parameter exists:
WHERE bgc_parameters ? 'DOXY'

-- Check multiple parameters:
WHERE bgc_parameters ?| ARRAY['DOXY', 'CHLA']  -- any
WHERE bgc_parameters ?& ARRAY['DOXY', 'CHLA']  -- all
```

#### BGC-Specific Rules (Rules 11-16)

**Rule 11 - Detect BGC Queries:**
Keywords that trigger BGC table usage:
- oxygen, dissolved oxygen, DOXY
- chlorophyll, CHLA
- nitrate, NITRATE
- pH, PH_IN_SITU_TOTAL
- backscatter, BBP700
- CDOM

**Rule 12 - BGC Table Selection:**
- Use `argo_bgc_profiles` and `argo_bgc_measurements` for BGC queries
- BGC tables include core measurements (temp/sal/pressure) PLUS bgc_parameters

**Rule 13 - BGC Parameter Extraction:**
```sql
-- Extract value
(bgc_parameters->'DOXY'->>'value')::float AS doxy

-- Extract QC
(bgc_parameters->'DOXY'->>'qc')::int AS doxy_qc

-- Check existence
WHERE bgc_parameters ? 'DOXY'
```

**Rule 14 - BGC QC Filtering:**
- Always filter: `(bgc_parameters->'DOXY'->>'qc')::int <= 2`
- QC = 1: High quality
- QC <= 2: Good quality
- QC <= 3: Acceptable quality

**Rule 15 - BGC Parameter Names (case-sensitive):**
- `'DOXY'` - Dissolved Oxygen (μmol/kg)
- `'CHLA'` - Chlorophyll-a (mg/m³)
- `'NITRATE'` - Nitrate (μmol/kg)
- `'PH_IN_SITU_TOTAL'` - pH
- `'BBP700'` - Backscatter at 700nm
- `'CDOM'` - Colored Dissolved Organic Matter

**Rule 16 - Combined Queries:**
If user asks for both core and BGC parameters, use BGC tables (they include everything)

#### BGC Query Examples

**Example 1 - Get Dissolved Oxygen Data:**
```sql
-- DATABASE: argo_indian_ocean_25
SELECT 
    p.global_profile_id, p.float_id, p.latitude, p.longitude, p.datetime,
    m.pressure_adjusted AS pressure,
    (m.bgc_parameters->'DOXY'->>'value')::float AS doxy,
    (m.bgc_parameters->'DOXY'->>'qc')::int AS doxy_qc
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'DOXY'
  AND (m.bgc_parameters->'DOXY'->>'qc')::int <= 2
  AND p.datetime >= '2024-01-01'
ORDER BY p.datetime DESC
LIMIT 100;
```

**Example 2 - Get Chlorophyll in Arabian Sea:**
```sql
-- DATABASE: argo_indian_ocean_25
SELECT 
    p.global_profile_id, p.float_id, p.latitude, p.longitude, p.datetime,
    m.pressure_adjusted AS pressure,
    (m.bgc_parameters->'CHLA'->>'value')::float AS chla,
    (m.bgc_parameters->'CHLA'->>'qc')::int AS chla_qc
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'CHLA'
  AND (m.bgc_parameters->'CHLA'->>'qc')::int <= 2
  AND p.latitude BETWEEN 10 AND 25
  AND p.longitude BETWEEN 50 AND 80
ORDER BY p.datetime DESC
LIMIT 100;
```

**Example 3 - List Floats with Oxygen Sensors:**
```sql
-- DATABASE: argo_indian_ocean_25
SELECT DISTINCT p.float_id, p.latitude, p.longitude, MAX(p.datetime) as latest_date
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'DOXY'
GROUP BY p.float_id, p.latitude, p.longitude
ORDER BY latest_date DESC
LIMIT 50;
```

**Example 4 - Combined Core and BGC Parameters:**
```sql
-- DATABASE: argo_indian_ocean_25
SELECT 
    p.global_profile_id, p.float_id, p.latitude, p.longitude, p.datetime,
    m.pressure_adjusted AS pressure,
    m.temperature_adjusted AS temperature,
    m.salinity_adjusted AS salinity,
    (m.bgc_parameters->'DOXY'->>'value')::float AS doxy,
    (m.bgc_parameters->'CHLA'->>'value')::float AS chla
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ?& ARRAY['DOXY', 'CHLA']
  AND (m.bgc_parameters->'DOXY'->>'qc')::int <= 2
  AND (m.bgc_parameters->'CHLA'->>'qc')::int <= 2
  AND m.temperature_adjusted_qc <= 2
ORDER BY p.datetime DESC
LIMIT 100;
```

## Testing BGC Queries

### Test Queries to Try:

1. **Basic Oxygen Query:**
   ```
   "Show me dissolved oxygen data from 2024"
   ```

2. **Chlorophyll in Region:**
   ```
   "Get chlorophyll measurements in the Arabian Sea"
   ```

3. **List BGC Floats:**
   ```
   "Which floats have oxygen sensors?"
   ```

4. **Combined Parameters:**
   ```
   "Show me temperature, salinity, and dissolved oxygen in the Bay of Bengal"
   ```

5. **Specific Float:**
   ```
   "Get all BGC parameters from float 5906527"
   ```

6. **Nitrate Query:**
   ```
   "Show me nitrate levels in 2024"
   ```

7. **pH Query:**
   ```
   "Get pH measurements from the Indian Ocean"
   ```

## BGC Data Availability

Based on your database:
- BGC tables: `argo_bgc_profiles`, `argo_bgc_measurements`
- Parameters stored in JSONB: `bgc_parameters`
- Available parameters: DOXY, CHLA, NITRATE, PH_IN_SITU_TOTAL, BBP700, CDOM
- QC flags included for quality control

## Benefits

1. **Comprehensive Coverage** - Supports all BGC parameters
2. **Quality Control** - Automatic QC filtering for reliable data
3. **Flexible Queries** - Can query single or multiple BGC parameters
4. **Combined Analysis** - Can mix core (temp/sal) and BGC parameters
5. **Natural Language** - Users can ask in plain English about BGC data

## Implementation Notes

- BGC detection is keyword-based (oxygen, chlorophyll, nitrate, pH, etc.)
- JSONB operators used for efficient parameter extraction
- QC filtering applied by default (QC <= 2 for good quality)
- BGC tables include core measurements, so no need for complex joins
- All examples follow PostgreSQL JSONB best practices

## Future Enhancements

1. **BGC Visualizations** - Add charts for oxygen profiles, chlorophyll distributions
2. **BGC Statistics** - Aggregate functions for BGC parameters
3. **BGC Trends** - Time series analysis of biogeochemical parameters
4. **BGC Correlations** - Analyze relationships between BGC and physical parameters
5. **BGC Quality Reports** - Detailed QC flag analysis and reporting
