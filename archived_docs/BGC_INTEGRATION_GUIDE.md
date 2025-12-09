# BGC-Argo Data Integration Guide

## Overview

This guide explains how BGC (Biogeochemical) Argo data is integrated into the FloatChat system using a flexible JSONB approach to handle variable sensor configurations.

## Architecture

### Problem
BGC-Argo floats have different sensor configurations:
- Some floats have only DOXY (dissolved oxygen)
- Some have CHLA (chlorophyll-a) + NITRATE
- Some have DOXY + CHLA + NITRATE + PH
- New sensors may be added in the future

### Solution: JSONB Storage

We store BGC parameters in a flexible JSONB column that can accommodate any combination of sensors without schema changes.

```sql
CREATE TABLE argo_bgc_measurements (
    id BIGSERIAL PRIMARY KEY,
    global_profile_id BIGINT,
    level INTEGER,
    pressure_adjusted DOUBLE PRECISION,
    temperature_adjusted DOUBLE PRECISION,
    salinity_adjusted DOUBLE PRECISION,
    pressure_adjusted_qc INTEGER,
    temperature_adjusted_qc INTEGER,
    salinity_adjusted_qc INTEGER,
    bgc_parameters JSONB,  -- ← Flexible BGC data storage
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    datetime TIMESTAMP WITH TIME ZONE
);

-- GIN index for fast JSONB queries
CREATE INDEX idx_bgc_parameters_gin ON argo_bgc_measurements USING GIN (bgc_parameters);
```

## Data Structure

### JSONB Format

```json
{
  "DOXY": {
    "value": 245.3,
    "qc": 1
  },
  "CHLA": {
    "value": 0.52,
    "qc": 2
  },
  "NITRATE": {
    "value": 5.2,
    "qc": 1
  }
}
```

### Supported BGC Parameters

- **DOXY**: Dissolved Oxygen (μmol/kg)
- **CHLA**: Chlorophyll-a (mg/m³)
- **NITRATE**: Nitrate (μmol/kg)
- **PH_IN_SITU_TOTAL**: pH (total scale)
- **BBP700**: Backscattering at 700nm (m⁻¹)
- **CDOM**: Colored Dissolved Organic Matter (ppb)

## Query Patterns

### 1. Check if Parameter Exists

```sql
-- List floats with DOXY measurements
SELECT DISTINCT p.float_id
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'DOXY';
```

### 2. Extract Parameter Value

```sql
-- Get DOXY values
SELECT 
    p.float_id,
    m.pressure_adjusted,
    (m.bgc_parameters->'DOXY'->>'value')::float as doxy_value,
    (m.bgc_parameters->'DOXY'->>'qc')::int as doxy_qc
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'DOXY';
```

### 3. Filter by QC Flag

```sql
-- Get high-quality DOXY measurements (QC <= 2)
SELECT *
FROM argo_bgc_measurements
WHERE m.bgc_parameters ? 'DOXY'
  AND (m.bgc_parameters->'DOXY'->>'qc')::int <= 2;
```

### 4. Multiple Parameters

```sql
-- Floats with both DOXY and CHLA
SELECT DISTINCT p.float_id
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ?& ARRAY['DOXY', 'CHLA'];
```

### 5. Any of Multiple Parameters

```sql
-- Floats with DOXY OR CHLA OR NITRATE
SELECT DISTINCT p.float_id
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ?| ARRAY['DOXY', 'CHLA', 'NITRATE'];
```

### 6. List Available Parameters

```sql
-- See what BGC parameters are available
SELECT DISTINCT jsonb_object_keys(bgc_parameters) as parameter
FROM argo_bgc_measurements
WHERE bgc_parameters IS NOT NULL;
```

### 7. Spatial + BGC Query

```sql
-- DOXY measurements in Arabian Sea
SELECT 
    p.float_id,
    p.latitude,
    p.longitude,
    (m.bgc_parameters->'DOXY'->>'value')::float as doxy
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'DOXY'
  AND p.latitude BETWEEN 10 AND 25
  AND p.longitude BETWEEN 50 AND 75
  AND (m.bgc_parameters->'DOXY'->>'qc')::int <= 2;
```

## Natural Language Query Examples

Users can ask questions like:

1. **"List floats with oxygen measurements in the Arabian Sea"**
   - System detects: spatial query + BGC parameter (DOXY)
   - Generates: `WHERE bgc_parameters ? 'DOXY' AND latitude BETWEEN ... AND longitude BETWEEN ...`

2. **"Show me chlorophyll data from 2023"**
   - System detects: temporal query + BGC parameter (CHLA)
   - Generates: `WHERE bgc_parameters ? 'CHLA' AND datetime BETWEEN '2023-01-01' AND '2023-12-31'`

3. **"Which floats have both oxygen and nitrate sensors?"**
   - System detects: list query + multiple BGC parameters
   - Generates: `WHERE bgc_parameters ?& ARRAY['DOXY', 'NITRATE']`

4. **"Get high-quality pH measurements near the equator"**
   - System detects: spatial + BGC + QC filtering
   - Generates: `WHERE bgc_parameters ? 'PH_IN_SITU_TOTAL' AND (bgc_parameters->'PH_IN_SITU_TOTAL'->>'qc')::int <= 2`

## Data Ingestion

### Running BGC Ingest

```bash
# Basic usage (uses environment variables for DB config)
python bgc_ingest.py

# With custom config
python bgc_ingest.py --config bgc_config.json --db-config db_config.json
```

### Configuration

Create `bgc_config.json`:

```json
{
  "index_url": "https://data-argo.ifremer.fr/argo_bio-profile_index.txt",
  "base_url": "https://data-argo.ifremer.fr/",
  "target_params": ["DOXY", "CHLA", "NITRATE", "PH"],
  "organization_prefix": "",
  "download_dir": "./data/bgc_downloads/",
  "log_dir": "./logs/",
  "max_total_files": 1000,
  "skip_existing": true
}
```

### Environment Variables

```bash
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_password
DB_NAME=argo_bgc
```

## Testing

### Run Integration Tests

```bash
python test_bgc_integration.py
```

This will test:
1. Schema setup (bgc_parameters column and GIN index)
2. Query patterns (existence checks, value extraction, QC filtering)
3. Sample data structure

### Expected Output

```
Testing BGC Schema
✅ bgc_parameters column exists: jsonb
✅ GIN index exists: idx_bgc_parameters_gin

Testing BGC Query Patterns
Count floats with DOXY measurements: 42
Count floats with CHLA measurements: 38
...

Sample BGC Data Structure
Float ID: 5906527
BGC Parameters: {
  "DOXY": {"value": 245.3, "qc": 1},
  "CHLA": {"value": 0.52, "qc": 2}
}
```

## Performance Considerations

### Indexing

The GIN index on `bgc_parameters` enables fast queries:
- Existence checks (`?` operator): O(log n)
- Multiple key checks (`?&`, `?|` operators): O(log n)
- Value extraction: O(1) after key lookup

### Query Optimization

**Good:**
```sql
WHERE bgc_parameters ? 'DOXY'  -- Uses GIN index
```

**Avoid:**
```sql
WHERE bgc_parameters::text LIKE '%DOXY%'  -- Full table scan
```

### Storage Efficiency

- Only stores parameters that exist for each measurement
- No NULL columns for missing sensors
- Typical JSONB overhead: ~20-30 bytes per measurement
- Much more efficient than separate columns with mostly NULL values

## Integration with Groq SQL Generator

The SQL generator automatically handles BGC queries:

```python
# User query: "List floats with oxygen in Arabian Sea"

# Groq generates:
SELECT DISTINCT p.float_id
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'DOXY'
  AND p.latitude BETWEEN 10 AND 25
  AND p.longitude BETWEEN 50 AND 75;
```

### Parameter Mapping

The system understands natural language terms:
- "oxygen" → DOXY
- "chlorophyll" → CHLA
- "nitrate" → NITRATE
- "pH" → PH_IN_SITU_TOTAL
- "backscatter" → BBP700

## Advantages of JSONB Approach

✅ **Flexibility**: Handle any sensor combination without schema changes
✅ **Extensibility**: New BGC parameters can be added without migration
✅ **Performance**: GIN indexes provide fast lookups
✅ **Storage**: Efficient - only stores what exists
✅ **Simplicity**: Clean query patterns that AI can generate
✅ **Consistency**: Matches existing QC filtering approach
✅ **Future-proof**: Ready for new sensor types

## Migration from Existing Data

If you have existing BGC data in separate columns:

```sql
-- Migrate from column-based to JSONB
UPDATE argo_bgc_measurements
SET bgc_parameters = jsonb_build_object(
    'DOXY', jsonb_build_object('value', doxy_adjusted, 'qc', doxy_adjusted_qc),
    'CHLA', jsonb_build_object('value', chla_adjusted, 'qc', chla_adjusted_qc)
)
WHERE doxy_adjusted IS NOT NULL OR chla_adjusted IS NOT NULL;
```

## Troubleshooting

### No BGC data appearing

1. Check if files were downloaded:
   ```bash
   ls -lh data/bgc_downloads/
   ```

2. Check ingestion logs:
   ```bash
   tail -f logs/bgc_ingest_*.log
   ```

3. Verify database connection:
   ```bash
   python test_bgc_integration.py
   ```

### Query performance issues

1. Ensure GIN index exists:
   ```sql
   SELECT indexname FROM pg_indexes 
   WHERE tablename = 'argo_bgc_measurements';
   ```

2. Analyze query plan:
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM argo_bgc_measurements
   WHERE bgc_parameters ? 'DOXY';
   ```

### QC filtering not working

Ensure QC values are integers:
```sql
-- Check QC data types
SELECT 
    bgc_parameters->'DOXY'->>'qc',
    pg_typeof(bgc_parameters->'DOXY'->>'qc')
FROM argo_bgc_measurements
LIMIT 5;
```

## Summary

The JSONB approach provides a flexible, performant, and future-proof solution for storing heterogeneous BGC sensor data. It integrates seamlessly with the existing FloatChat architecture and enables natural language queries for complex BGC data retrieval.
