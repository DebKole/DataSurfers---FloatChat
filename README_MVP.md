# FloatChat MVP - Argo Float Data Chatbot

## 🌊 Overview
FloatChat is an intelligent chatbot that can answer queries about oceanographic data from Argo floats. This MVP version can process natural language queries and provide data-driven responses using your local Argo float dataset.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the Data Processing (Optional)
```bash
python test_queries.py
```

### 3. Start the Backend Server
```bash
python start_server.py
```
Or alternatively:
```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### 4. Start the Frontend (in another terminal)
```bash
cd src
npm start
```

## 🤖 What FloatChat Can Do

### Data-Driven Queries (Uses Local Data)
- **Temperature queries**: "What's the surface temperature?", "Temperature at 100m depth"
- **Salinity queries**: "Show salinity profile", "Salinity at 50m depth"
- **Depth analysis**: "Conditions at 200m", "Data between 50 and 150m"
- **Profile analysis**: "Show profile summary", "Compare profiles"
- **Ocean structure**: "Find thermocline", "Temperature gradient"
- **Statistics**: "Dataset overview", "Basic statistics"
- **Surface conditions**: "Surface conditions", "Surface data"

### General Queries (Uses Gemini AI)
- General oceanography questions
- Explanations about marine science
- Help and guidance

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

## 🏗️ Architecture

### Backend Components
1. **FastAPI Server** (`app.py`) - Main API server
2. **LangGraph Agent** (`main.py`) - Query routing and processing
3. **Data Processor** (`data_processor.py`) - Argo data analysis
4. **Query Interpreter** (`query_interpreter.py`) - Natural language understanding

### Data Flow
1. User sends query via React frontend
2. FastAPI receives query
3. LangGraph agent determines if it's a data query or general query
4. Data queries → Local data processing → Structured response
5. General queries → Gemini AI → AI-generated response
6. Response sent back to frontend

## 📈 Features

### ✅ Implemented
- Natural language query processing
- Local Argo data analysis
- Temperature and salinity profiling
- Depth-based data retrieval
- Surface conditions analysis
- Thermocline detection
- Basic statistics and summaries
- Profile comparisons
- Intelligent query routing

### 🔄 Future Enhancements
- Map visualizations
- Real-time Argo data integration
- Advanced statistical analysis
- Export functionality
- Multi-region comparisons

## 🛠️ Technical Details

### Data Processing Capabilities
- **Depth Analysis**: Query data by depth ranges
- **Parameter Profiling**: Analyze temperature, salinity, pressure profiles
- **Statistical Analysis**: Mean, std, min, max by depth ranges
- **Gradient Analysis**: Find thermoclines and other gradients
- **Comparative Analysis**: Compare multiple profiles

### Query Understanding
- Regex-based pattern matching
- Parameter extraction (depths, ranges)
- Context-aware responses
- Fallback to AI for complex queries

## 🐛 Troubleshooting

### Common Issues
1. **"Module not found" errors**: Run `pip install -r requirements.txt`
2. **"CSV file not found"**: Ensure `argo_demo.csv` is in the root directory
3. **CORS errors**: Make sure frontend runs on `http://localhost:3000`
4. **Gemini API errors**: Check your `.env` file has `GEMINI_API_KEY`

### Testing
Run the test script to verify data processing:
```bash
python test_queries.py
```

## 📝 API Endpoints

- `GET /` - Server status
- `POST /` - Main chat endpoint
- `GET /dataset-info` - Dataset statistics

## 🎯 MVP Demonstration Points

1. **Data Integration**: Show how local Argo data is processed
2. **Natural Language Understanding**: Demonstrate various query types
3. **Intelligent Responses**: Show data-driven vs AI-generated responses
4. **Real-time Processing**: Fast query processing and response
5. **Extensibility**: Easy to add new query types and data sources

## 🔧 Customization

### Adding New Query Types
1. Add patterns to `query_interpreter.py`
2. Implement handler methods
3. Update data processor if needed

### Adding New Data Sources
1. Extend `ArgoDataProcessor` class
2. Add new analysis methods
3. Update query patterns

This MVP demonstrates the core functionality and can be extended for the full application!