# BGC-Argo Integration Quick Start

## Overview

This guide will help you integrate BGC (Biogeochemical) Argo data into your FloatChat system using a flexible JSONB approach.

## What's Been Implemented

✅ **Flexible JSONB storage** for variable BGC sensor configurations  
✅ **Automatic BGC parameter extraction** from NetCDF files  
✅ **Quality control filtering** for BGC measurements  
✅ **GIN indexing** for fast JSONB queries  
✅ **Natural language query support** for BGC parameters  

## Quick Start (3 Steps)

### Step 1: Inspect Your BGC Files

First, see what BGC parameters are in your downloaded files:

```bash
python inspect_bgc_files.py
```

**Expected output:**
```
Found 150 NetCDF files

BGC Parameter Frequency:
  DOXY                : 120 files (80.0%)
  CHLA                :  95 files (63.3%)
  NITRATE             :  85 files (56.7%)
  BBP700              :  45 files (30.0%)

Parameter Combinations:
  DOXY, CHLA, NITRATE                           :  65 files
  DOXY, CHLA                                    :  30 files
  DOXY                                          :  25 files
```

### Step 2: Run Migration (if needed)

If you already have a BGC database, add the JSONB column:

```bash
python migrate_bgc_to_jsonb.py
```

Otherwise, skip to Step 3 (the ingestion script will create the schema).

### Step 3: Ingest BGC Data

Process all BGC NetCDF files and load into PostgreSQL:

```bash
python bgc_ingest.py
```

**What this does:**
- Creates `argo_bgc_profiles` and `argo_bgc_measurements` tables
- Extracts BGC parameters (DOXY, CHLA, NITRATE, etc.)
- Stores them in JSONB format: `{"DOXY": {"value": 245.3, "qc": 1}}`
- Creates GIN index for fast queries
- Handles variable sensor configurations automatically

## Verify Installation

```bash
python test_bgc_integration.py
```

**Expected output:**
```
Testing BGC Schema
✅ bgc_parameters column exists: jsonb
✅ GIN index exists: idx_bgc_parameters_gin

Testing BGC Query Patterns
Count floats with DOXY measurements: 42
Count floats with CHLA measurements: 38

Sample BGC Data Structure
Float ID: 5906527
BGC Parameters: {
  "DOXY": {"value": 245.3, "qc": 1},
  "CHLA": {"value": 0.52, "qc": 2}
}

✅ All tests completed!
```

## Example Queries

### Natural Language (via FloatChat)

Users can now ask:

1. **"List floats with oxygen measurements in the Arabian Sea"**
2. **"Show me chlorophyll data from 2023"**
3. **"Which floats have both oxygen and nitrate sensors?"**
4. **"Get high-quality pH measurements near the equator"**

### SQL (Direct Database)

```sql
-- List floats with DOXY
SELECT DISTINCT float_id
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'DOXY';

-- Get DOXY values with QC filtering
SELECT 
    p.float_id,
    (m.bgc_parameters->'DOXY'->>'value')::float as doxy_value,
    (m.bgc_parameters->'DOXY'->>'qc')::int as doxy_qc
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ? 'DOXY'
  AND (m.bgc_parameters->'DOXY'->>'qc')::int <= 2;

-- Floats with multiple sensors
SELECT DISTINCT p.float_id
FROM argo_bgc_profiles p
JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
WHERE m.bgc_parameters ?& ARRAY['DOXY', 'CHLA', 'NITRATE'];
```

See `BGC_SQL_EXAMPLES.sql` for 50+ query examples.

## File Reference

| File | Purpose |
|------|---------|
| `bgc_ingest.py` | Main ingestion script - downloads and processes BGC files |
| `process_netcdf_to_postgres.py` | NetCDF processor with BGC extraction |
| `inspect_bgc_files.py` | Inspect downloaded files to see available parameters |
| `migrate_bgc_to_jsonb.py` | Add JSONB column to existing database |
| `test_bgc_integration.py` | Test suite for BGC functionality |
| `BGC_INTEGRATION_GUIDE.md` | Complete documentation |
| `BGC_SQL_EXAMPLES.sql` | 50+ SQL query examples |
| `BGC_QUICKSTART.md` | This file |

## Data Structure

### Database Schema

```
argo_bgc_profiles
├── global_profile_id (PK)
├── float_id
├── datetime
├── latitude, longitude
└── ...

argo_bgc_measurements
├── id (PK)
├── global_profile_id (FK)
├── pressure_adjusted
├── temperature_adjusted
├── salinity_adjusted
├── bgc_parameters (JSONB) ← BGC data here
└── ...
```

### JSONB Structure

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

## Supported BGC Parameters

- **DOXY**: Dissolved Oxygen (μmol/kg)
- **CHLA**: Chlorophyll-a (mg/m³)
- **NITRATE**: Nitrate (μmol/kg)
- **PH_IN_SITU_TOTAL**: pH (total scale)
- **BBP700**: Backscattering at 700nm (m⁻¹)
- **CDOM**: Colored Dissolved Organic Matter (ppb)

## Configuration

### Environment Variables

Create `.env` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_password
DB_NAME=argo_bgc
```

### BGC Ingest Config

Edit `bgc_ingest.py` or create `bgc_config.json`:

```json
{
  "target_params": ["DOXY", "CHLA", "NITRATE", "PH"],
  "download_dir": "./data/bgc_downloads/",
  "max_total_files": 1000,
  "skip_existing": true
}
```

## Troubleshooting

### No BGC data appearing

```bash
# Check if files were downloaded
ls -lh data/bgc_downloads/

# Inspect files
python inspect_bgc_files.py

# Check logs
tail -f logs/bgc_ingest_*.log
```

### Query performance issues

```sql
-- Verify GIN index exists
SELECT indexname FROM pg_indexes 
WHERE tablename = 'argo_bgc_measurements';

-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM argo_bgc_measurements
WHERE bgc_parameters ? 'DOXY';
```

### Database connection errors

```bash
# Test connection
python test_bgc_integration.py

# Check environment variables
cat .env
```

## Performance Tips

✅ **Use GIN index**: Automatically created for fast JSONB queries  
✅ **Filter by QC**: `WHERE (bgc_parameters->'DOXY'->>'qc')::int <= 2`  
✅ **Existence checks**: `WHERE bgc_parameters ? 'DOXY'` (very fast)  
✅ **Batch inserts**: Default chunk size is 5000 rows  

## Next Steps

1. **Test queries**: Try the examples in `BGC_SQL_EXAMPLES.sql`
2. **Integrate with FloatChat**: BGC queries work automatically
3. **Add more parameters**: Edit `bgc_params` list in `process_netcdf_to_postgres.py`
4. **Monitor performance**: Use `EXPLAIN ANALYZE` on slow queries

## Why JSONB?

✅ Handles variable sensor configurations  
✅ No schema changes for new parameters  
✅ Fast queries with GIN indexes  
✅ Efficient storage (only stores what exists)  
✅ Clean, simple query patterns  
✅ Future-proof for new sensors  

## Support

For detailed documentation, see:
- `BGC_INTEGRATION_GUIDE.md` - Complete guide
- `BGC_SQL_EXAMPLES.sql` - Query examples
- `SYSTEM_ARCHITECTURE.md` - Overall system design

---

**Ready to go!** Run `python bgc_ingest.py` to start ingesting BGC data.
