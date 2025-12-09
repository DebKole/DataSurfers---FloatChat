# Multi-Database & Quality Control System

## 🎯 Overview

The FloatChat system has been upgraded to support **multiple year-based databases (2015-2025)** with **quality-controlled data** and **intelligent database selection** by the LLM.

## 🚀 Quick Start

### For Users

Just specify the year in your queries:

```
"Show me temperature data from 2023 in the Arabian Sea"
"Get high-quality salinity profiles from 2020"
"Latest measurements" (uses 2025)
```

The system automatically:
- ✅ Selects the correct year database
- ✅ Filters for quality-controlled data
- ✅ Returns analyzed results

### For Developers

```python
from groq_sql_generator import GroqSQLGenerator

generator = GroqSQLGenerator()
result = generator.query_and_execute("Show me data from 2023")

print(f"Database: {result['database']}")  # argo_indian_ocean_23
print(f"Rows: {result['execution']['row_count']}")
print(f"Analysis: {result['analysis']}")
```

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[QUICK_START_MULTI_DATABASE.md](QUICK_START_MULTI_DATABASE.md)** | Quick reference guide | Everyone |
| **[MULTI_DATABASE_QC_GUIDE.md](MULTI_DATABASE_QC_GUIDE.md)** | Comprehensive guide | Users & Developers |
| **[MULTI_DATABASE_IMPLEMENTATION_SUMMARY.md](MULTI_DATABASE_IMPLEMENTATION_SUMMARY.md)** | Technical details | Developers |
| **[MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md)** | Migration steps | DevOps |

## 🗄️ Database Structure

### Year-Based Databases

```
argo_indian_ocean_15  (2015)
argo_indian_ocean_16  (2016)
...
argo_indian_ocean_25  (2025)
```

### Schema

**argo_profiles:** Profile metadata
- `global_profile_id`, `float_id`, `cycle_number`
- `datetime`, `latitude`, `longitude`
- `institution`, `data_mode`

**argo_measurements:** Quality-controlled measurements
- `pressure_adjusted`, `temperature_adjusted`, `salinity_adjusted`
- `pressure_adjusted_qc`, `temperature_adjusted_qc`, `salinity_adjusted_qc`
- QC flags: 1=best, 2=good, 3=acceptable

## 🎨 Key Features

### 1. Automatic Database Selection

The LLM extracts the year from your query and selects the appropriate database:

```
User: "Show me data from 2023"
LLM: Uses argo_indian_ocean_23
```

### 2. Quality Control Filtering

Measurements are automatically filtered by quality:

```sql
WHERE temperature_adjusted_qc <= 2  -- Good quality (default)
WHERE temperature_adjusted_qc = 1   -- Best quality only
WHERE temperature_adjusted_qc <= 3  -- All acceptable
```

### 3. Intelligent SQL Generation

The LLM generates SQL with:
- Database selection comment
- QC filters
- Adjusted column names
- Proper joins and indexes

Example:
```sql
-- DATABASE: argo_indian_ocean_23
SELECT ap.*, am.temperature_adjusted, am.temperature_adjusted_qc
FROM argo_profiles ap
JOIN argo_measurements am ON ap.global_profile_id = am.global_profile_id
WHERE ap.latitude BETWEEN 10 AND 20
  AND am.temperature_adjusted_qc <= 2
ORDER BY ap.datetime DESC;
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python3 test_multi_database_qc.py
```

Tests include:
- ✅ Database selection logic
- ✅ Year extraction from queries
- ✅ SQL generation with QC filters
- ✅ Database connectivity
- ✅ Quality control filtering
- ✅ Full workflow (query → SQL → execution)

## 📊 Quality Control (QC) Flags

| QC Value | Meaning | Use Case |
|----------|---------|----------|
| 1 | Best quality | High-precision analysis, publications |
| 2 | Good quality | Most applications (default) |
| 3 | Acceptable | General exploration |
| 4+ | Poor/Bad | Avoid or expert review |

## 🔧 Setup & Installation

### 1. Create Databases

```bash
for year in {15..25}; do
  psql -U postgres -c "CREATE DATABASE argo_indian_ocean_$year;"
done
```

### 2. Ingest Data

```bash
# Test with one year
python3 historical_data_ingestion_v2.py --year 2023

# Ingest all years (parallel processing)
python3 historical_data_ingestion_v2.py --parallel --workers 8
```

### 3. Run Tests

```bash
python3 test_multi_database_qc.py
```

## 📈 Performance

### Test Results (from test suite)

```
✅ Database Selection: 100% accurate
✅ Year Extraction: 100% accurate
✅ SQL Generation: QC filters present, adjusted columns used
✅ Database Connectivity: All databases accessible
✅ QC Filtering: 95.4% good quality, 92.8% best quality
✅ Full Workflow: Complete query execution successful
```

### Database Statistics (argo_indian_ocean_25)

```
Total measurements: 11,468,409
Good quality (QC ≤ 2): 10,942,566 (95.4%)
Best quality (QC = 1): 10,644,023 (92.8%)
```

## 🔄 Migration

Follow the [MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md) for step-by-step migration instructions.

**Estimated time:** 8-60 hours (mostly data ingestion)

## 🐛 Troubleshooting

### Common Issues

**Database doesn't exist:**
```bash
python3 historical_data_ingestion_v2.py --year 2023
```

**No data returned:**
- Check QC filters (try QC ≤ 3)
- Verify year has data
- Expand search bounds

**Wrong year selected:**
- Be more explicit: "Show me data from 2023"

## 📝 Example Queries

### User Queries

```
✅ "Show me temperature data from 2023 in the Arabian Sea"
✅ "Get high-quality salinity profiles from 2020"
✅ "Find float 1902482 data from 2019"
✅ "Latest measurements" (uses 2025)
✅ "Best quality data from Bay of Bengal in 2022"
```

### API Usage

```python
from groq_sql_generator import GroqSQLGenerator
from float_chat_mcp.data_access_tools.db_executor_tool import DatabaseExecutorTool

# SQL Generation
generator = GroqSQLGenerator()
result = generator.query_and_execute("Show me data from 2023")

# Direct Database Access
executor = DatabaseExecutorTool()
db = executor.get_database_for_year(2023)  # argo_indian_ocean_23
result = executor.execute_query(sql, database=db)

# Multi-Database Query
result = executor.execute_multi_database_query(
    sql, 
    start_year=2020, 
    end_year=2023
)
```

## 🎯 Success Metrics

- ✅ **11 databases** covering 2015-2025
- ✅ **95%+ data quality** (QC ≤ 2)
- ✅ **100% test pass rate**
- ✅ **Automatic year selection**
- ✅ **Backward compatible**

## 🔮 Future Enhancements

1. **Multi-year queries:** Automatic cross-database aggregation
2. **QC statistics:** Show quality distribution in results
3. **Regional expansion:** Atlantic and Pacific ocean databases
4. **Real-time data:** Integration with live data streams
5. **Advanced caching:** Redis cache for multi-database queries

## 📞 Support

- **Quick Reference:** [QUICK_START_MULTI_DATABASE.md](QUICK_START_MULTI_DATABASE.md)
- **Full Guide:** [MULTI_DATABASE_QC_GUIDE.md](MULTI_DATABASE_QC_GUIDE.md)
- **Technical Details:** [MULTI_DATABASE_IMPLEMENTATION_SUMMARY.md](MULTI_DATABASE_IMPLEMENTATION_SUMMARY.md)
- **Migration:** [MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md)
- **Test Suite:** `python3 test_multi_database_qc.py`

## 📄 Files Modified

### Core Files
- `groq_sql_generator.py` - Enhanced with year extraction and QC awareness (using Groq AI)
- `float_chat_mcp/data_access_tools/db_executor_tool.py` - Multi-database support
- `historical_data_ingestion_v2.py` - Year-based ingestion

### New Files
- `test_multi_database_qc.py` - Comprehensive test suite
- `MULTI_DATABASE_QC_GUIDE.md` - User guide
- `MULTI_DATABASE_IMPLEMENTATION_SUMMARY.md` - Technical documentation
- `QUICK_START_MULTI_DATABASE.md` - Quick reference
- `MIGRATION_CHECKLIST.md` - Migration guide
- `MULTI_DATABASE_README.md` - This file

## 🏆 Summary

The multi-database and quality control system provides:

✅ **Year-based organization** (2015-2025)  
✅ **Quality-controlled data** with QC flags  
✅ **Intelligent database selection** by LLM  
✅ **Backward compatibility** with legacy system  
✅ **Comprehensive testing** and documentation  
✅ **Performance optimization** with proper indexing  

**Just specify the year in your queries and the system handles the rest!**
