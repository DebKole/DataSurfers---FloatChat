# System Architecture: Multi-Database & Quality Control

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                               │
│  "Show me temperature data from 2023 in the Arabian Sea"        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GEMINI SQL GENERATOR                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Extract Year: "2023" → 23                             │  │
│  │ 2. Select Database: argo_indian_ocean_23                 │  │
│  │ 3. Generate SQL with QC filters                          │  │
│  │ 4. Add database comment: -- DATABASE: argo_indian_ocean_23│ │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE EXECUTOR TOOL                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Parse database from SQL comment                       │  │
│  │ 2. Connect to argo_indian_ocean_23                       │  │
│  │ 3. Execute SQL query                                     │  │
│  │ 4. Return results with metadata                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASES                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ argo_indian_ │  │ argo_indian_ │  │ argo_indian_ │  ...    │
│  │  ocean_15    │  │  ocean_20    │  │  ocean_23    │         │
│  │   (2015)     │  │   (2020)     │  │   (2023)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  Each database contains:                                        │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ argo_profiles (metadata)                               │   │
│  │ argo_measurements (data + QC flags)                    │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Query
    │
    ├─→ Year Extraction
    │       │
    │       ├─→ "2023" found → year = 2023
    │       ├─→ "January 2020" → year = 2020
    │       └─→ "latest" → year = 2025 (default)
    │
    ├─→ Database Selection
    │       │
    │       └─→ year_databases[year % 100]
    │           └─→ argo_indian_ocean_23
    │
    ├─→ SQL Generation
    │       │
    │       ├─→ Add database comment
    │       ├─→ Use adjusted columns
    │       ├─→ Add QC filters (default: QC ≤ 2)
    │       └─→ Generate complete SQL
    │
    ├─→ Query Execution
    │       │
    │       ├─→ Connect to selected database
    │       ├─→ Execute SQL
    │       └─→ Return results
    │
    └─→ Analysis & Response
            │
            ├─→ Gemini analyzes results
            ├─→ Generate natural language summary
            └─→ Return to user
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP QUERY AGENT                             │
│  (Orchestrates the entire workflow)                              │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─→ is_data_query() → Determine if query needs data
             │
             ├─→ execute_query() → Main execution flow
             │       │
             │       ├─→ DataAccessOrchestrator
             │       │       │
             │       │       ├─→ QueryBuilderTool (analyze intent)
             │       │       │
             │       │       ├─→ GroqSQLGenerator (generate SQL using Groq AI)
             │       │       │       │
             │       │       │       ├─→ _extract_year_from_query()
             │       │       │       ├─→ generate_sql_query()
             │       │       │       └─→ _extract_database_from_sql()
             │       │       │
             │       │       └─→ DatabaseExecutorTool (execute)
             │       │               │
             │       │               ├─→ get_database_for_year()
             │       │               ├─→ execute_query()
             │       │               └─→ execute_multi_database_query()
             │       │
             │       └─→ Format response
             │
             └─→ Return structured result
```

## Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                    argo_indian_ocean_XX                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ argo_profiles                                          │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ global_profile_id (PK)                                 │    │
│  │ float_id                                               │    │
│  │ cycle_number                                           │    │
│  │ datetime                                               │    │
│  │ latitude, longitude                                    │    │
│  │ min_pressure, max_pressure                             │    │
│  │ measurement_count                                      │    │
│  │ institution, project_name, data_mode                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          │ 1:N                                   │
│                          ▼                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ argo_measurements                                      │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ id (PK)                                                │    │
│  │ global_profile_id (FK)                                 │    │
│  │ level                                                  │    │
│  │ pressure_adjusted          ┐                           │    │
│  │ temperature_adjusted       │ Quality-Controlled        │    │
│  │ salinity_adjusted          ┘ Values                    │    │
│  │ pressure_adjusted_qc       ┐                           │    │
│  │ temperature_adjusted_qc    │ QC Flags                  │    │
│  │ salinity_adjusted_qc       ┘ (1-9)                     │    │
│  │ latitude, longitude, datetime                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Year-to-Database Mapping

```
┌──────────┬─────────────────────────┬──────────────────┐
│   Year   │     Database Name       │   Year Suffix    │
├──────────┼─────────────────────────┼──────────────────┤
│   2015   │ argo_indian_ocean_15    │       15         │
│   2016   │ argo_indian_ocean_16    │       16         │
│   2017   │ argo_indian_ocean_17    │       17         │
│   2018   │ argo_indian_ocean_18    │       18         │
│   2019   │ argo_indian_ocean_19    │       19         │
│   2020   │ argo_indian_ocean_20    │       20         │
│   2021   │ argo_indian_ocean_21    │       21         │
│   2022   │ argo_indian_ocean_22    │       22         │
│   2023   │ argo_indian_ocean_23    │       23         │
│   2024   │ argo_indian_ocean_24    │       24         │
│   2025   │ argo_indian_ocean_25    │       25         │
└──────────┴─────────────────────────┴──────────────────┘

Conversion: database_name = f"argo_indian_ocean_{year % 100:02d}"
```

## Quality Control Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEASUREMENT QUALITY                           │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Raw Data (from NetCDF)                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PRES, TEMP, PSAL (raw values)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Quality Control Processing                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Apply calibration corrections                         │  │
│  │ 2. Detect outliers                                       │  │
│  │ 3. Validate against climatology                          │  │
│  │ 4. Assign QC flags (1-9)                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Adjusted Data (stored in database)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ pressure_adjusted, temperature_adjusted, salinity_adjusted│ │
│  │ pressure_adjusted_qc, temperature_adjusted_qc, ...       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Query Filtering                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ WHERE temperature_adjusted_qc <= 2  (good quality)       │  │
│  │ WHERE temperature_adjusted_qc = 1   (best quality)       │  │
│  │ WHERE temperature_adjusted_qc <= 3  (acceptable)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## QC Flag Decision Tree

```
                    Measurement Value
                           │
                           ▼
                    ┌──────────────┐
                    │ Valid Range? │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
             Yes                       No
              │                         │
              ▼                         ▼
    ┌─────────────────┐         ┌──────────┐
    │ Climatology OK? │         │ QC = 4   │
    └────────┬────────┘         │ (Bad)    │
             │                   └──────────┘
    ┌────────┴────────┐
    │                 │
   Yes               No
    │                 │
    ▼                 ▼
┌─────────┐      ┌─────────┐
│ Sensor  │      │ QC = 3  │
│ Drift?  │      │ (Prob.  │
└────┬────┘      │ Good)   │
     │           └─────────┘
┌────┴────┐
│         │
No       Yes
│         │
▼         ▼
┌────┐  ┌────┐
│QC=1│  │QC=2│
│Best│  │Good│
└────┘  └────┘
```

## Request/Response Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER REQUEST                                                  │
│    "Show me temperature data from 2023 in the Arabian Sea"      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. YEAR EXTRACTION                                               │
│    year = 2023                                                   │
│    database = "argo_indian_ocean_23"                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. SQL GENERATION                                                │
│    -- DATABASE: argo_indian_ocean_23                             │
│    SELECT ap.*, am.temperature_adjusted, am.temperature_adjusted_qc│
│    FROM argo_profiles ap                                         │
│    JOIN argo_measurements am ON ...                              │
│    WHERE ap.latitude BETWEEN 0 AND 30                            │
│      AND ap.longitude BETWEEN 50 AND 80                          │
│      AND am.temperature_adjusted_qc <= 2                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. QUERY EXECUTION                                               │
│    Connect to: argo_indian_ocean_23                              │
│    Execute SQL                                                   │
│    Return: 1,234 rows                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. GEMINI ANALYSIS                                               │
│    "Found 1,234 temperature measurements from 2023 in the        │
│     Arabian Sea. Data shows typical seasonal patterns with       │
│     temperatures ranging from 24.5°C to 29.8°C..."              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. RESPONSE TO USER                                              │
│    {                                                             │
│      "status": "success",                                        │
│      "database": "argo_indian_ocean_23",                         │
│      "row_count": 1234,                                          │
│      "analysis": "Found 1,234 temperature measurements...",      │
│      "data": [...]                                               │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
```

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLOATCHAT SYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Frontend (Web UI)                                      │    │
│  │ - User query input                                     │    │
│  │ - Results display                                      │    │
│  │ - Data visualization                                   │    │
│  └────────────────────────┬───────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ MCP Server (floatchat_mcp_server.py)                  │    │
│  │ - Request routing                                      │    │
│  │ - Session management                                   │    │
│  │ - Response formatting                                  │    │
│  └────────────────────────┬───────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ MCP Query Agent (mcp_query_agent.py)                  │    │
│  │ - Query classification                                 │    │
│  │ - Workflow orchestration                               │    │
│  │ - Response formatting                                  │    │
│  └────────────────────────┬───────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Data Access Orchestrator                               │    │
│  │ - Intent analysis                                      │    │
│  │ - Strategy selection                                   │    │
│  │ - Tool coordination                                    │    │
│  └────────────────────────┬───────────────────────────────┘    │
│                           │                                     │
│              ┌────────────┴────────────┐                        │
│              ▼                         ▼                        │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │ GroqSQLGenerator     │  │ DatabaseExecutorTool │           │
│  │ - Year extraction    │  │ - DB selection       │           │
│  │ - SQL generation     │  │ - Query execution    │           │
│  │ - Uses Groq AI       │  │ - Multi-database     │           │
│  │ - QC awareness       │  │ - Multi-DB support   │           │
│  └──────────────────────┘  └──────────────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Summary

This architecture provides:

✅ **Modular design** - Clear separation of concerns
✅ **Intelligent routing** - Automatic database selection
✅ **Quality awareness** - Built-in QC filtering
✅ **Scalability** - Easy to add more years/regions
✅ **Maintainability** - Well-documented components
✅ **Performance** - Optimized with indexes and caching
