# FloatChat - Argo Float Data Analysis System

A comprehensive system for querying, analyzing, and visualizing Argo oceanographic float data using natural language, powered by AI and PostgreSQL.

## 🌊 Overview

FloatChat enables researchers and oceanographers to interact with Argo float data using natural language queries. The system automatically translates questions into SQL, executes queries across multiple databases, performs statistical analysis, and generates visualizations.

## ✨ Key Features

- **Natural Language Queries**: Ask questions in plain English
- **Multi-Database Support**: Automatic routing to year-specific databases (2015-2025)
- **BGC Data Integration**: Support for biogeochemical parameters (DOXY, CHLA, NITRATE, etc.)
- **Quality Control**: Built-in QC filtering for data reliability
- **Statistical Analysis**: Automatic trend detection, anomaly identification, and statistical summaries
- **Visualizations**: T-S diagrams, time series, depth profiles, and spatial maps
- **Parallel Processing**: Fast data ingestion with multiprocessing support (10 workers)
- **MCP Integration**: Model Context Protocol for AI-powered analysis

## 🏗️ Architecture

```
User Query (Natural Language)
    ↓
MCP Query Agent (Intent Classification)
    ↓
Groq SQL Generator (SQL Generation)
    ↓
Database Executor (Multi-Database Query)
    ↓
Analysis Tools (Statistical Analysis)
    ↓
Visualization (Charts & Graphs)
    ↓
Natural Language Response
```

### Database Structure

- **Year-based databases**: `argo_indian_ocean_15` through `argo_indian_ocean_25`
- **BGC database**: `argo_bgc` with JSONB storage for flexible sensor data
- **Tables**: `argo_profiles` (metadata) and `argo_measurements` (data + QC flags)

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.11+
python3 --version

# PostgreSQL 14+
psql --version

# Node.js 18+ (for frontend)
node --version
```

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd DataSurfers---FloatChat
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file with:
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_password
DB_NAME=argo_bgc
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
```

4. **Initialize databases**
```bash
python3 setup_postgres_database.py
```

### Running the System

#### Backend (MCP Server)

```bash
python3 float_chat_mcp/floatchat_mcp_server.py
```

#### Frontend (Web Interface)

```bash
cd Landing_page
npm install
npm run dev
```

Access at: `http://localhost:3000`

#### Mobile App

```bash
cd mobile54
npm install
npx expo start
```

## 📊 Data Ingestion

### Core Argo Data

```bash
# Process NetCDF files
python3 process_netcdf_to_postgres.py
```

### BGC Data (Parallel Processing - Recommended)

```bash
# Test with 5 files
python3 bgc_ingest_parallel.py --workers 3 --max-files 5

# Process 100 files
python3 bgc_ingest_parallel.py --workers 10 --max-files 100

# Process all files (~13,876 files in 30-45 minutes)
python3 bgc_ingest_parallel.py --workers 10
```

**Features:**
- 10 workers by default (configurable)
- Automatic file management (moves to `data/ingested_bgc/`)
- Progress tracking and error handling
- ~4-5x faster than serial processing

### Historical Data

```bash
python3 historical_data_downloader.py
python3 historical_data_ingestion_v2.py
```

## 💬 Example Queries

### Spatial Queries
```
"Show me temperature data in the Arabian Sea"
"List floats near the equator"
"What's the salinity in the Bay of Bengal?"
```

### Temporal Queries
```
"Show temperature trends from 2020 to 2023"
"What was the temperature in January 2019?"
"Get the latest data from float 5906527"
```

### BGC Queries
```
"List floats with oxygen measurements"
"Show chlorophyll data in the Arabian Sea"
"Which floats have both DOXY and CHLA sensors?"
"Get high-quality pH measurements near the equator"
```

### Analysis Queries
```
"Show temperature statistics for the Arabian Sea"
"Detect anomalies in salinity data"
"Compare temperature between 2020 and 2023"
"Show me a T-S diagram for float 5906527"
```

## 🗄️ Database Schema

### Core Argo Tables

```sql
-- Profile metadata
argo_profiles (
    global_profile_id BIGINT PRIMARY KEY,
    float_id TEXT,
    cycle_number INTEGER,
    datetime TIMESTAMP,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
)

-- Measurement data
argo_measurements (
    id BIGSERIAL PRIMARY KEY,
    global_profile_id BIGINT,
    pressure_adjusted DOUBLE PRECISION,
    temperature_adjusted DOUBLE PRECISION,
    salinity_adjusted DOUBLE PRECISION,
    pressure_adjusted_qc INTEGER,
    temperature_adjusted_qc INTEGER,
    salinity_adjusted_qc INTEGER
)
```

### BGC Tables with JSONB

```sql
-- BGC measurements with flexible JSONB storage
argo_bgc_measurements (
    id BIGSERIAL PRIMARY KEY,
    global_profile_id BIGINT,
    bgc_parameters JSONB,  -- Flexible BGC data
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    datetime TIMESTAMP
)

-- GIN index for fast JSONB queries
CREATE INDEX idx_bgc_parameters_gin 
ON argo_bgc_measurements USING GIN (bgc_parameters);
```

### BGC JSONB Format

```json
{
  "DOXY": {"value": 245.3, "qc": 1},
  "CHLA": {"value": 0.52, "qc": 2},
  "NITRATE": {"value": 5.2, "qc": 1}
}
```

## 🔍 BGC Query Examples (SQL)

```sql
-- Check if parameter exists
WHERE bgc_parameters ? 'DOXY'

-- Extract value
(bgc_parameters->'DOXY'->>'value')::float

-- Filter by QC
WHERE (bgc_parameters->'DOXY'->>'qc')::int <= 2

-- Multiple parameters (AND)
WHERE bgc_parameters ?& ARRAY['DOXY', 'CHLA']

-- Multiple parameters (OR)
WHERE bgc_parameters ?| ARRAY['DOXY', 'CHLA', 'NITRATE']
```

See `archived_docs/BGC_SQL_EXAMPLES.sql` for 50+ query examples.

## 📈 Analysis Tools

### Statistical Summary
- Mean, median, std dev, min, max
- Quartiles and percentiles
- Data quality metrics

### Trend Analysis
- Linear regression
- Seasonal decomposition
- Anomaly detection

### Visualizations
- T-S diagrams
- Time series plots
- Depth profiles
- Spatial maps

## 📁 Project Structure

```
DataSurfers---FloatChat/
├── float_chat_mcp/              # MCP server and tools
│   ├── floatchat_mcp_server.py  # Main MCP server
│   ├── mcp_query_agent.py       # Query orchestration
│   ├── data_access_tools/       # Database tools
│   └── analysis_tools/          # Statistical analysis
├── Landing_page/                # Web frontend (Next.js)
├── mobile54/                    # Mobile app (Expo)
├── data/                        # Data storage
│   ├── bgc_downloads/          # BGC NetCDF files
│   └── ingested_bgc/           # Processed BGC files
├── logs/                        # Application logs
├── archived_docs/              # Detailed documentation
├── bgc_ingest_parallel.py      # Parallel BGC ingestion
├── process_netcdf_to_postgres.py # NetCDF processor
├── groq_sql_generator.py       # SQL generation
└── requirements.txt            # Python dependencies
```

## 🧪 Testing

Quick verification:

```bash
# Test database connection
python3 -c "import psycopg2; print('✅ DB OK')"

# Test BGC integration
python3 quick_test_bgc.py

# Test parallel ingestion (3 files)
python3 bgc_ingest_parallel.py --workers 2 --max-files 3
```

## 📚 Documentation Archive

All detailed documentation is in `archived_docs/`:

- **BGC Integration**: `BGC_INTEGRATION_GUIDE.md`, `BGC_QUICKSTART.md`
- **System Architecture**: `SYSTEM_ARCHITECTURE.md`
- **API Documentation**: `API_DOCUMENTATION.md`
- **SQL Examples**: `BGC_SQL_EXAMPLES.sql` (50+ examples)
- **Parallel Ingestion**: `PARALLEL_INGESTION_GUIDE.md`
- **Implementation Summaries**: Various `*_SUMMARY.md` files

To access:
```bash
ls archived_docs/
cat archived_docs/BGC_INTEGRATION_GUIDE.md
```

## 🐛 Troubleshooting

### Database Connection
```bash
pg_isready
psql -U postgres -d argo_bgc -c "SELECT 1;"
```

### BGC Data
```bash
# Check files
ls data/bgc_downloads/ | wc -l

# Check database
psql -d argo_bgc -c "SELECT COUNT(*) FROM argo_bgc_measurements WHERE bgc_parameters IS NOT NULL;"
```

### Performance
- Reduce workers: `--workers 5`
- Smaller batches: `--max-files 100`
- Check indexes: `\di` in psql

## 🔧 Configuration

### Environment Variables

```bash
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_password
DB_NAME=argo_bgc
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### BGC Ingestion Config

Create `bgc_config.json`:
```json
{
  "download_dir": "./data/bgc_downloads/",
  "max_total_files": 1000,
  "skip_existing": true
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 👥 Team

DataSurfers Team

## 🙏 Acknowledgments

- Argo Program for oceanographic data
- IFREMER for BGC-Argo data
- Groq for AI inference
- Google Gemini for analysis

## 📞 Support

- Check `archived_docs/` for detailed documentation
- Review logs in `logs/` directory
- Open an issue on GitHub

---

**Version**: 1.0.0  
**Last Updated**: December 2024
