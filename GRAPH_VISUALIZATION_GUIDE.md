# 📊 Graph Visualization Integration Guide

## Overview

This guide explains how graph visualization is integrated into FloatChat to display analysis results (temperature trends, T-S curves, etc.) as interactive charts instead of just tables.

---

## 🎯 Architecture

```
User Query: "Show temperature trend for float 1902482"
    ↓
Backend (FastAPI + MCP)
    ↓
Data Access Orchestrator
    ↓
Analysis Tools Wrapper
    ↓
Analysis Result (with measurements)
    ↓
MCP Query Agent (_extract_chart_data)
    ↓
Response with chart_data
    ↓
Frontend (React Native)
    ↓
ChatScreen receives message with chartData
    ↓
ChartRenderer component
    ↓
Victory Native renders chart
```

---

## 📦 Components

### **Backend Components**

#### 1. **Analysis Tools Wrapper** (`float_chat_mcp/data_access_tools/analysis_tools_wrapper.py`)
- Normalizes database columns (`profile_datetime` → `datetime`)
- Validates data has required columns
- Routes to appropriate analysis tool
- Returns structured analysis results

#### 2. **MCP Query Agent** (`mcp_query_agent.py`)
- Extracts chart data from analysis results
- Determines chart type based on analysis type
- Adds metadata (title, axis labels)
- Returns `chart_data` in response

**Key Method:**
```python
def _extract_chart_data(self, result: dict) -> dict:
    """Extract data for chart visualization"""
    if result.get('strategy') == 'analysis':
        analysis_type = result.get('analysis_type')
        measurements = result['analysis_result']['profiles'][0]['measurements']
        
        return {
            'type': analysis_type,  # 'temp_trend', 'ts_curve', etc.
            'data': measurements,    # Array of data points
            'title': 'Temperature Trend Over Time',
            'xLabel': 'Date',
            'yLabel': 'Temperature (°C)'
        }
```

#### 3. **FastAPI Server** (`app.py`)
- Receives query from frontend
- Invokes MCP agent
- Returns response with `chart_data` field

**Response Structure:**
```json
{
  "status": 201,
  "message": "I generated a temperature trend analysis...",
  "query_type": "analysis",
  "has_data": true,
  "table_data": {
    "columns": ["datetime", "temperature", "salinity"],
    "rows": [...]
  },
  "chart_data": {
    "type": "temp_trend",
    "data": [
      {"datetime": "2025-01-15T10:30:00", "temperature": 25.5},
      {"datetime": "2025-01-16T10:30:00", "temperature": 25.3}
    ],
    "title": "Temperature Trend Over Time",
    "xLabel": "Date",
    "yLabel": "Temperature (°C)"
  }
}
```

---

### **Frontend Components**

#### 1. **LineChart** (`mobile54/components/charts/LineChart.tsx`)
- Renders line charts with Victory Native
- Used for: temperature trends, salinity trends
- Features: grid lines, axis labels, data points

#### 2. **ScatterChart** (`mobile54/components/charts/ScatterChart.tsx`)
- Renders scatter plots with Victory Native
- Used for: T-S curves, T-D profiles
- Features: customizable colors, axis labels

#### 3. **ChartRenderer** (`mobile54/components/charts/ChartRenderer.tsx`)
- Smart component that determines which chart to render
- Transforms data based on chart type
- Handles edge cases (empty data, unsupported types)

**Data Transformation:**
```typescript
// Temperature Trend
data.map(point => ({
  x: new Date(point.datetime),
  y: parseFloat(point.temperature)
}))

// T-S Curve
data.map(point => ({
  x: parseFloat(point.temperature),
  y: parseFloat(point.salinity)
}))
```

#### 4. **ChatScreen** (`mobile54/src/screens/ChatScreen.js`)
- Updated to receive `chartData` from API
- Renders ChartRenderer when chart data is available
- Displays chart below the message text

---

## 🔄 Data Flow Example

### **Query: "Show temperature trend for float 1902482"**

**Step 1: Backend Processing**
```python
# 1. Query analyzed
intent = {
    "query_type": "analysis",
    "analysis_type": "temp_trend",
    "entities": {"float_ids": ["1902482"]}
}

# 2. Data fetched from database
data = [
    {"profile_datetime": "2025-01-15", "temperature": 25.5, "salinity": 35.2},
    {"profile_datetime": "2025-01-16", "temperature": 25.3, "salinity": 35.1}
]

# 3. Data normalized
normalized_data = [
    {"datetime": "2025-01-15", "temperature": 25.5, "salinity": 35.2},
    {"datetime": "2025-01-16", "temperature": 25.3, "salinity": 35.1}
]

# 4. Analysis executed
analysis_result = {
    "profiles": [{
        "measurements": normalized_data
    }]
}

# 5. Chart data extracted
chart_data = {
    "type": "temp_trend",
    "data": normalized_data,
    "title": "Temperature Trend Over Time",
    "xLabel": "Date",
    "yLabel": "Temperature (°C)"
}
```

**Step 2: Frontend Rendering**
```javascript
// 1. Message received
const aiMessage = {
  role: "assistant",
  content: "I generated a temperature trend analysis...",
  chartData: {
    type: "temp_trend",
    data: [...],
    title: "Temperature Trend Over Time"
  }
}

// 2. ChartRenderer determines chart type
<ChartRenderer chartData={msg.chartData} />

// 3. LineChart renders with Victory Native
<VictoryChart>
  <VictoryLine data={transformedData} />
  <VictoryScatter data={transformedData} />
</VictoryChart>
```

---

## 🎨 Supported Chart Types

| Analysis Type | Chart Type | X-Axis | Y-Axis | Component |
|--------------|------------|--------|--------|-----------|
| `temp_trend` | Line | Date | Temperature (°C) | LineChart |
| `sal_trend` | Line | Date | Salinity (PSU) | LineChart |
| `ts_curve` | Scatter | Temperature (°C) | Salinity (PSU) | ScatterChart |
| `td_curve` | Scatter | Temperature (°C) | Depth (m) | ScatterChart |
| `comparison` | Multiple Lines | Variable | Value | LineChart |
| `statistics` | Bar | Variable | Value | (Future) |

---

## 🚀 Installation

### **1. Install Dependencies**
```bash
cd mobile54
npm install victory-native react-native-svg
```

### **2. Files Created**
- `mobile54/components/charts/LineChart.tsx`
- `mobile54/components/charts/ScatterChart.tsx`
- `mobile54/components/charts/ChartRenderer.tsx`

### **3. Files Modified**
- `mobile54/src/screens/ChatScreen.js` - Added chart rendering
- `mcp_query_agent.py` - Added `_extract_chart_data()` method

---

## 🧪 Testing

### **Test Queries:**

1. **Temperature Trend**
   ```
   Show temperature trend for float 1902482
   ```
   Expected: Line chart with date vs temperature

2. **T-S Curve**
   ```
   Generate T-S curve for Arabian Sea
   ```
   Expected: Scatter plot with temperature vs salinity

3. **Salinity Trend**
   ```
   Show salinity trend for float 2902746
   ```
   Expected: Line chart with date vs salinity

---

## 🎨 Customization

### **Change Chart Colors**
Edit `mobile54/components/charts/ChartRenderer.tsx`:
```typescript
<LineChart
  data={transformedData}
  color={oceanTheme.colors.coral}  // Change this
/>
```

### **Adjust Chart Size**
Edit `LineChart.tsx` or `ScatterChart.tsx`:
```typescript
<VictoryChart
  width={screenWidth - 32}
  height={300}  // Change this
/>
```

### **Add New Chart Type**
1. Create new chart component (e.g., `BarChart.tsx`)
2. Add case in `ChartRenderer.tsx`:
```typescript
case 'statistics':
  return <BarChart data={transformedData} />;
```

---

## 🐛 Troubleshooting

### **Chart Not Showing**
1. Check if `chart_data` is in API response:
   ```javascript
   console.log('Response:', data);
   ```

2. Verify data structure:
   ```javascript
   console.log('Chart Data:', msg.chartData);
   ```

3. Check for errors in ChartRenderer:
   ```typescript
   if (!chartData || !chartData.data) {
     console.log('Invalid chart data');
   }
   ```

### **Victory Native Errors**
- Ensure `react-native-svg` is installed
- Run `npx expo install react-native-svg`
- Restart Metro bundler

### **Data Not Transforming Correctly**
- Check column names in backend response
- Verify normalization in `analysis_tools_wrapper.py`
- Add logging in `ChartRenderer.transformData()`

---

## 📈 Future Enhancements

1. **Interactive Charts**
   - Zoom/pan functionality
   - Tooltips on hover
   - Click to see details

2. **More Chart Types**
   - Bar charts for statistics
   - Multi-line charts for comparisons
   - Heatmaps for spatial data

3. **Export Functionality**
   - Save chart as image
   - Export data as CSV
   - Share chart via social media

4. **Animation**
   - Smooth transitions when data updates
   - Loading animations
   - Entry animations

---

## 📚 Resources

- [Victory Native Docs](https://commerce.nearform.com/open-source/victory-native/)
- [React Native SVG](https://github.com/software-mansion/react-native-svg)
- [Victory Chart Examples](https://formidable.com/open-source/victory/gallery)

---

## ✅ Summary

The graph visualization integration works by:

1. **Backend** extracts chart data from analysis results
2. **API** sends `chart_data` field in response
3. **Frontend** receives chart data in message
4. **ChartRenderer** determines chart type and transforms data
5. **Victory Native** renders the chart

This creates a seamless experience where users see beautiful, interactive charts alongside their analysis results!
