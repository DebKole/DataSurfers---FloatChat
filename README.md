# FloatChat - Advanced Oceanographic Data Platform

## 🌊 Overview
FloatChat is an intelligent oceanographic data platform that provides real-time analysis of Argo float data through natural language queries. Built for the Smart India Hackathon (SIH) 2025, it combines AI-powered query processing with live data automation to deliver comprehensive ocean insights.

## 🏆 SIH 2025 Innovation Features
- **🤖 AI-Powered Query Processing**: Natural language to oceanographic insights
- **📡 Live Data Automation**: Real-time Argo data ingestion and processing
- **🏭 Ocean Pollution Detection**: Advanced environmental monitoring
- **🐟 Marine Life Detection**: Mesopelagic organism identification
- **🌡️ Climate Change Analysis**: Ocean heat content and thermal analysis
- **🗺️ Interactive Visualizations**: Real-time oceanographic maps

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials and API keys
```

### 2. Database Setup
```bash
# Set up main development database (January 2025 data)
python setup_postgres_database.py

# Set up vector database with January data
python scripts/import_january_to_vector.py

# Set up live automation database (optional)
./scripts/setup_live_automation.sh
```

### 3. Start the Application
```bash
# Start backend server
python start_server.py
# Or: uvicorn app:app --reload --host 127.0.0.1 --port 8000

# Start frontend (in another terminal)
npm start
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🤖 What FloatChat Can Do

### 🌊 Core Oceanographic Queries
- **Temperature Analysis**: "What's the surface temperature?", "Temperature at 100m depth"
- **Salinity Profiling**: "Show salinity profile", "Salinity at 50m depth"
- **Depth Analysis**: "Conditions at 200m", "Data between 50 and 150m"
- **Profile Comparisons**: "Show profile summary", "Compare profiles"
- **Ocean Structure**: "Find thermocline", "Temperature gradient"
- **Statistical Analysis**: "Dataset overview", "Basic statistics"

### 🚀 Innovation Features
- **🏭 Pollution Detection**: "Analyze ocean pollution", "Show acidification levels"
- **🐟 Marine Life Detection**: "Detect organisms", "Show marine biomass"
- **🌡️ Climate Analysis**: "Ocean heat content", "Climate change impact"
- **🗺️ Interactive Maps**: "Show temperature map", "Visualize salinity distribution"
- **📡 Live Data**: "Latest oceanographic data", "Real-time conditions"

### 🧠 AI-Powered Insights
- Advanced oceanographic explanations
- Climate change impact analysis
- Marine ecosystem health assessment
- Data-driven environmental recommendations

## 📊 Sample Queries to Try

```
"What are the basic statistics?"
"What's the surface temperature?"
"Show me temperature at 100 meters depth"
"What's the salinity profile?"
"Find the thermocline"
"What are surface conditions?"
"Compare the profiles"
"Show temperature range"
```

## 🏗️ System Architecture

### 🖥️ Backend Components
1. **FastAPI Server** (`app.py`) - Main API server with CORS support
2. **LangGraph Agent** (`main.py`) - Intelligent query routing and processing
3. **Data Processor** (`data_processor.py`) - Advanced Argo data analysis
4. **Query Interpreter** (`query_interpreter.py`) - Natural language understanding
5. **Map Data Provider** (`map_data_provider.py`) - Geospatial visualization support

### 🗄️ Database Architecture
- **Development Database** (`floatchat_argo`): Stable January 2025 dataset (2,434 profiles)
- **Live Database** (`floatchat_argo_live`): Real-time automation with current data (224+ profiles)
- **Vector Database** (`ChromaDB`): Semantic search with 2,658+ searchable profiles
- **Dual-database + Vector approach** ensures development stability while enabling live features and AI-powered search

### 🔄 Data Processing Pipeline
1. **NetCDF Ingestion** → Raw Argo float data from IFREMER
2. **Data Processing** → Extract profiles, measurements, metadata
3. **PostgreSQL Storage** → Optimized schema with spatial indexes
4. **Vector Database** → ChromaDB with semantic embeddings for AI search
5. **Query Processing** → Natural language to SQL + vector search
6. **AI Enhancement** → Gemini AI + semantic search for complex analysis
7. **Response Generation** → Structured data + natural language + contextual insights

### 🤖 Live Automation System
- **Hourly monitoring** of IFREMER Argo database
- **Automatic download** and processing of new NetCDF files
- **Real-time database updates** with comprehensive logging
- **Error handling** and recovery mechanisms

## 📈 Features

### ✅ Core Features
- **🤖 Natural Language Processing**: Advanced query understanding and routing
- **🧠 Semantic Search**: AI-powered vector database for contextual profile discovery
- **🌊 Oceanographic Analysis**: Temperature, salinity, pressure profiling
- **📊 Statistical Analysis**: Comprehensive data summaries and comparisons
- **🗺️ Interactive Maps**: Real-time oceanographic visualizations
- **📡 Live Data Integration**: Automated Argo data ingestion and processing

### 🚀 Innovation Features
- **🏭 Ocean Pollution Detection**: pH analysis, acidification monitoring, contamination alerts
- **🐟 Mesopelagic Organism Detection**: Deep-sea life identification using fluorescence data
- **🌡️ Climate Change Analysis**: Ocean heat content, thermal expansion, warming trends
- **⚡ Real-time Automation**: Hourly data updates with comprehensive monitoring
- **🔍 Advanced Query System**: SQL generation from natural language

### 🎯 Production Features
- **🗄️ Dual Database Architecture**: Stable development + live production data
- **📈 Performance Optimization**: Spatial indexes, query optimization
- **🔧 Comprehensive Logging**: Automation tracking, error handling
- **⏰ Scheduled Automation**: Cron-based hourly data updates
- **📊 Monitoring Dashboard**: System health and data pipeline status

## 🛠️ Technical Implementation

### 🔬 Advanced Data Processing
- **NetCDF Processing**: Real-time ingestion from IFREMER Argo database
- **Global Profile Management**: Unique ID generation across multiple data sources
- **Spatial Analysis**: Geographic querying with optimized indexes
- **Temporal Analysis**: Time-series processing and trend analysis
- **Quality Control**: Data validation and error handling

### 🧠 AI & Machine Learning
- **LangGraph Integration**: Intelligent query routing and decision making
- **Gemini AI**: Advanced natural language understanding and generation
- **Pattern Recognition**: Automated detection of oceanographic phenomena
- **Predictive Analytics**: Climate trend analysis and environmental forecasting

### 🗄️ Database Design
- **PostgreSQL**: Optimized schema for oceanographic data with 2,658+ profiles
- **ChromaDB Vector Store**: Semantic embeddings for AI-powered search
- **Spatial Indexing**: Fast geographic queries with region detection
- **Composite Keys**: Efficient profile and measurement relationships
- **Global ID Management**: Conflict-free numbering across multiple databases
- **Automation Logging**: Comprehensive pipeline monitoring

### 🔄 Automation Pipeline
- **Cron Scheduling**: Hourly automated data updates
- **Error Recovery**: Robust handling of network and processing failures
- **Incremental Processing**: Only process new/changed files
- **Resource Management**: Automatic cleanup and disk space optimization

## � Liove Automation Setup

### Setting Up Real-time Data Pipeline
```bash
# Set up live automation system
./scripts/setup_live_automation.sh

# Test the live pipeline
./scripts/test_live_pipeline.sh

# Run production pipeline once
./scripts/run_live_production.sh

# Monitor system status
./scripts/monitor_live_pipeline.sh
```

### Configuring Hourly Automation
```bash
# Set up cron job for hourly updates
crontab -e
# Add: 0 * * * * /path/to/scripts/run_live_pipeline.sh

# Or use systemd (production)
sudo cp scripts/floatchat-live.* /etc/systemd/system/
sudo systemctl enable floatchat-live.timer
sudo systemctl start floatchat-live.timer
```

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Ensure PostgreSQL is running and credentials are correct in `.env`
2. **Missing Dependencies**: Run `pip install -r requirements.txt` and `npm install`
3. **API Errors**: Check `GEMINI_API_KEY` in `.env` file
4. **Automation Issues**: Verify cron service is running: `systemctl status cron`
5. **Network Issues**: Check internet connection for IFREMER data downloads

### System Monitoring
```bash
# Check live pipeline status
./scripts/monitor_live_pipeline.sh

# View recent logs
tail -f logs/live_argo_pipeline_*.log

# Check database status
psql -h localhost -U postgres -d floatchat_argo_live -c "SELECT COUNT(*) FROM argo_profiles;"
```

## 📝 API Endpoints

### Core Endpoints
- `GET /` - Server status and health check
- `POST /` - Main chat endpoint for natural language queries
- `GET /dataset-info` - Dataset statistics and metadata

### Response Format
```json
{
  "status": 201,
  "message": "Natural language response",
  "query_type": "temperature_analysis",
  "has_data": true,
  "show_map": false,
  "structured_data": {...}
}
```

## 📊 Sample Queries

### Basic Oceanographic Queries
```
"What's the surface temperature?"
"Show me temperature at 100 meters depth"
"What's the salinity profile?"
"Find the thermocline"
"Compare the profiles"
"Show INCOIS floats in Arabian Sea"
"Find deep water profiles from winter"
```

### Innovation Feature Queries
```
"Analyze ocean pollution levels"
"Detect marine organisms at 500m depth"
"Show climate change impact on ocean heat"
"Display temperature map of the region"
"What are the latest oceanographic conditions?"
```

## 🏆 SIH 2025 Demonstration Points

### 🎯 Technical Excellence
1. **Production-Ready System**: Real automation with live data processing
2. **Advanced AI Integration**: LangGraph + Gemini AI for intelligent responses
3. **Scalable Architecture**: Dual-database design for stability and growth
4. **Innovation Features**: Pollution detection, marine life analysis, climate monitoring
5. **Real-time Capabilities**: Hourly automated data updates

### 🌊 Oceanographic Impact
1. **Environmental Monitoring**: Real-time pollution and acidification detection
2. **Climate Research**: Ocean heat content analysis for climate change studies
3. **Marine Conservation**: Deep-sea organism detection and biomass estimation
4. **Operational Oceanography**: Live data integration for current conditions
5. **Educational Tool**: Natural language interface for ocean science learning

## 🚀 Deployment & Scaling

### Production Deployment
- **Cloud Infrastructure**: AWS/Azure/GCP compatible
- **Container Support**: Docker containerization ready
- **Load Balancing**: Horizontal scaling capabilities
- **Monitoring**: Comprehensive logging and alerting
- **Security**: Environment-based configuration management

### Performance Metrics
- **Query Response Time**: < 2 seconds for complex analyses
- **Data Processing**: 10+ NetCDF files per hour
- **Database Performance**: Optimized for 1M+ measurements
- **Automation Reliability**: 99%+ uptime with error recovery

## 🤝 Contributing

This project was developed for Smart India Hackathon 2025 by Team DataSurfers. The system demonstrates advanced oceanographic data processing with real-time automation capabilities.

### Key Technologies
- **Backend**: Python, FastAPI, LangGraph, PostgreSQL, ChromaDB
- **Frontend**: React, JavaScript, Leaflet Maps
- **AI/ML**: Google Gemini AI, Vector Embeddings, Semantic Search
- **Data**: NetCDF, Argo Float Network, IFREMER Database
- **Automation**: Cron, Systemd, Shell Scripting
- **Vector DB**: ChromaDB with all-MiniLM-L6-v2 embeddings

---

**🌊 FloatChat - Transforming Ocean Data into Actionable Insights**