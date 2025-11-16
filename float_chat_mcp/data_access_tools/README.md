# FloatChat Data Access Tools

**Intelligent data retrieval system for Argo oceanographic data using Model Context Protocol (MCP)**

## 🎯 Overview

The Data Access Tools provide the **RAG (Retrieval-Augmented Generation) pipeline** for FloatChat, enabling natural language queries to be intelligently routed to the appropriate data sources and retrieval methods.

## 🏗️ Architecture

### Core Components

1. **`query_builder_tool.py`** - Intent analysis and query routing
2. **`vector_retrieval_tool.py`** - Semantic search using ChromaDB
3. **`db_executor_tool.py`** - SQL execution on PostgreSQL
4. **`data_access_orchestrator.py`** - Coordinates all tools

### Data Sources

- **PostgreSQL Main DB**: 2,434 January 2025 profiles with 1.6M measurements
- **PostgreSQL Live DB**: Real-time Argo data (224+ profiles)
- **ChromaDB Vector DB**: Semantic embeddings for 2,658+ profiles

## 🧠 Query Intelligence

### Query Types & Routing

| Query Type | Example | Strategy | Tools Used |
|------------|---------|----------|------------|
| **Float Lookup** | "Show data from float 1902482" | SQL Only | DB Executor |
| **Spatial** | "Profiles in Arabian Sea" | SQL Only | DB Executor |
| **Temporal** | "Winter 2025 data" | SQL Only | DB Executor |
| **Semantic** | "Deep water salinity patterns" | Vector Only | Vector Retrieval |
| **Spatial-Temporal** | "Arabian Sea winter profiles" | Hybrid | Vector + SQL |
| **Institution** | "INCOIS float deployments" | Vector Only | Vector Retrieval |

### Smart Routing Logic

```python
# The system automatically determines the best approach:
query = "Find INCOIS floats with high salinity in Arabian Sea"

# 1. Intent Analysis
entities = {
    "institutions": ["INCOIS"],
    "parameters": ["salinity"], 
    "regions": ["Arabian Sea"]
}

# 2. Strategy Selection
strategy = "hybrid"  # Complex query needs both vector + SQL

# 3. Execution Plan
plan = {
    "step_1": "Vector search for INCOIS + salinity + Arabian Sea",
    "step_2": "SQL refinement for detailed measurements"
}
```

## 🚀 Usage Examples

### Basic Usage

```python
from mcp.data_access_tools import DataAccessOrchestrator

orchestrator = DataAccessOrchestrator()

# Execute natural language query
result = orchestrator.execute_query("Show me temperature profiles in Arabian Sea")

print(f"Strategy: {result['strategy']}")
print(f"Results: {len(result['results'])} datasets found")
```

### Individual Tool Usage

```python
# Direct vector search
from mcp.data_access_tools import VectorRetrievalTool

vector_tool = VectorRetrievalTool()
results = vector_tool.search_profiles("deep ocean measurements", n_results=10)

# Direct SQL execution  
from mcp.data_access_tools import DatabaseExecutorTool

db_tool = DatabaseExecutorTool()
results = db_tool.get_profiles_by_region("Arabian Sea", limit=50)

# Query analysis
from mcp.data_access_tools import QueryBuilderTool

builder = QueryBuilderTool()
intent = builder.analyze_intent("Find winter temperature data")
plan = builder.build_execution_plan(intent)
```

## 📊 Supported Query Patterns

### Geographic Queries
- "Profiles in Arabian Sea"
- "Bay of Bengal measurements"
- "Data between 10°N-20°N and 60°E-75°E"
- "Floats near Mumbai"

### Temporal Queries
- "Winter 2025 data"
- "Latest measurements"
- "January profiles"
- "Recent oceanographic data"

### Parameter-Specific Queries
- "Temperature profiles"
- "Salinity measurements"
- "Deep water data"
- "Surface conditions"

### Institution Queries
- "INCOIS float deployments"
- "French research floats"
- "Data from specific institutions"

### Semantic Queries
- "High salinity regions"
- "Deep ocean patterns"
- "Unusual temperature readings"
- "Monsoon-influenced areas"

### Complex Hybrid Queries
- "Compare Arabian Sea vs Bay of Bengal salinity"
- "INCOIS floats in winter with deep measurements"
- "Temperature trends in tropical regions"

## 🎯 Government Demo Scenarios

### Scenario 1: Regional Analysis
```
Query: "Show me all data from Arabian Sea in January 2025"
→ Strategy: SQL Only
→ Result: 208 profiles with regional filtering
→ Demo Point: Geographic intelligence
```

### Scenario 2: Institution Tracking
```
Query: "Find all INCOIS deployed floats"
→ Strategy: Vector Search
→ Result: Semantic matching of institution data
→ Demo Point: Organizational data tracking
```

### Scenario 3: Complex Analysis
```
Query: "Compare deep water temperature between regions"
→ Strategy: Hybrid (Vector + SQL)
→ Result: Multi-step analysis with detailed measurements
→ Demo Point: Advanced analytical capabilities
```

## 🔧 Configuration

### Environment Variables
```bash
# Database connection
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_password

# Vector database path (optional)
CHROMA_DB_PATH=./chroma_db
```

### Database Requirements
- PostgreSQL with `floatchat_argo` and `floatchat_argo_live` databases
- ChromaDB vector store with embedded profiles
- Network access for live data updates

## 📈 Performance Metrics

### Query Response Times
- **Simple SQL queries**: < 0.5 seconds
- **Vector searches**: < 1 second  
- **Hybrid queries**: < 2 seconds
- **Complex analysis**: < 5 seconds

### Data Coverage
- **2,434 profiles** in main database
- **1,596,480 measurements** for detailed analysis
- **754 unique floats** across global oceans
- **2,658+ searchable profiles** in vector database

## 🏛️ Government Integration Features

### Transparency & Auditability
- Complete query execution logs
- Data source tracking
- Confidence scoring
- Methodology explanation

### Scalability
- Handles 1M+ measurements efficiently
- Optimized for government-scale deployments
- Regional data partitioning
- Automated performance monitoring

### Security
- SQL injection protection
- Read-only database access
- Query validation and sanitization
- Audit trail for all data access

## 🧪 Testing

```bash
# Test individual components
python mcp/data_access_tools/query_builder_tool.py
python mcp/data_access_tools/vector_retrieval_tool.py
python mcp/data_access_tools/db_executor_tool.py

# Test complete system
python mcp/data_access_tools/data_access_orchestrator.py
```

## 🎉 SIH 2025 Demo Ready

This system demonstrates:
- ✅ **RAG Pipeline**: Natural language → Intelligent data retrieval
- ✅ **Multi-modal Data Access**: Vector + SQL hybrid approach
- ✅ **Government-Ready**: Transparent, auditable, scalable
- ✅ **Real Data**: 2,434 profiles, 1.6M measurements
- ✅ **Production Quality**: Error handling, logging, monitoring

**Perfect for demonstrating how AI can make oceanographic data accessible to non-technical government officials while maintaining scientific rigor and transparency.**

---

**Built by Team DataSurfers for Smart India Hackathon 2025**