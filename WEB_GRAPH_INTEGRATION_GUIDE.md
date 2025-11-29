# 📊 Web Frontend Graph Visualization Guide

## Overview

This guide explains how graph visualization is integrated into the **FloatChat web frontend** using **Plotly.js** to display analysis results as interactive charts.

---

## 🎯 Architecture

```
User Query: "Show temperature trend for float 1902482"
    ↓
Backend (FastAPI + MCP)
    ↓
Analysis Tools → chart_data extraction
    ↓
Response with chart_data
    ↓
Web Frontend (React)
    ↓
ChatContainer receives message with chartData
    ↓
ChartRenderer component
    ↓
Plotly.js renders interactive chart
```

---

## 📦 Components

### **Frontend Components**

#### 1. **ChartRenderer** (`src/components/ChartRenderer.js`)
Main component that renders charts using Plotly.js

**Features:**
- ✅ Automatic chart type detection
- ✅ Data transformation for different chart types
- ✅ Dark theme matching FloatChat design
- ✅ Interactive features (zoom, pan, hover)
- ✅ Responsive design

**Supported Chart Types:**
- `temp_trend` → Line chart (Temperature vs Time)
- `sal_trend` → Line chart (Salinity vs Time)
- `ts_curve` → Scatter plot (Temperature vs Salinity)
- `td_curve` → Line chart (Temperature vs Depth, inverted Y-axis)
- `comparison` → Multi-line chart
- Generic fallback for unknown types

#### 2. **ChatContainer** (`src/components/ChatContainer.js`)
Updated to:
- Store `chartData` in message objects
- Render `ChartRenderer` when chart data is available
- Pass chart data from API response to messages

---

## 🎨 Chart Styling

### **Color Scheme**
Matches FloatChat's ocean theme:
- **Temperature**: `#FF6B6B` (Coral red)
- **Salinity**: `#4ECDC4` (Teal)
- **Background**: `#1a2332` (Deep ocean blue)
- **Grid**: `#2a3f5f` (Mid ocean blue)
- **Text**: `#e0e0e0` (Light gray)

### **Interactive Features**
- **Hover**: Shows exact values on hover
- **Zoom**: Click and drag to zoom into specific regions
- **Pan**: Shift + drag to pan around
- **Reset**: Double-click to reset view
- **Download**: Built-in download as PNG

---

## 🔄 Data Flow Example

### **Query: "Show temperature trend for float 1902482"**

**Step 1: Backend Response**
```json
{
  "status": 201,
  "message": "I generated a temperature trend analysis...",
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

**Step 2: Frontend Processing**
```javascript
// ChatContainer stores message with chartData
const message = {
  type: 'bot',
  content: response.data.message,
  chartData: response.data.chart_data
};

// ChartRenderer transforms data
const plotData = [{
  x: ['2025-01-15T10:30:00', '2025-01-16T10:30:00'],
  y: [25.5, 25.3],
  type: 'scatter',
  mode: 'lines+markers',
  marker: { color: '#FF6B6B', size: 6 },
  line: { color: '#FF6B6B', width: 2 }
}];

// Plotly renders chart
<Plot data={plotData} layout={layout} />
```

---

## 📊 Chart Examples

### **1. Temperature Trend**
```javascript
{
  type: 'temp_trend',
  data: [
    { datetime: '2025-01-15', temperature: 25.5 },
    { datetime: '2025-01-16', temperature: 25.3 }
  ]
}
```
**Result:** Line chart with time on X-axis, temperature on Y-axis

### **2. T-S Curve**
```javascript
{
  type: 'ts_curve',
  data: [
    { temperature: 25.5, salinity: 35.2 },
    { temperature: 24.8, salinity: 35.1 }
  ]
}
```
**Result:** Scatter plot with temperature on X-axis, salinity on Y-axis

### **3. T-D Profile**
```javascript
{
  type: 'td_curve',
  data: [
    { temperature: 25.5, level: 0 },
    { temperature: 24.8, level: 10 }
  ]
}
```
**Result:** Line chart with temperature on X-axis, depth on Y-axis (inverted)

---

## 🚀 Installation & Setup

### **1. Dependencies Already Installed**
Your `package.json` already includes:
```json
{
  "plotly.js": "^3.3.0",
  "react-plotly.js": "^2.6.0"
}
```

### **2. Files Created**
- ✅ `src/components/ChartRenderer.js` - Main chart component
- ✅ `src/components/ChartRenderer.css` - Chart styling

### **3. Files Modified**
- ✅ `src/components/ChatContainer.js` - Added chart rendering
- ✅ `mcp_query_agent.py` - Added `_extract_chart_data()` method

### **4. Start the App**
```bash
# Start backend
python start_server.py

# Start frontend (in another terminal)
npm start
```

---

## 🧪 Testing

### **Test Queries:**

1. **Temperature Trend**
   ```
   Show temperature trend for float 1902482
   ```
   ✅ Expected: Interactive line chart with date vs temperature

2. **T-S Curve**
   ```
   Generate T-S curve for Arabian Sea
   ```
   ✅ Expected: Scatter plot with temperature vs salinity

3. **Salinity Trend**
   ```
   Show salinity trend for float 2902746
   ```
   ✅ Expected: Line chart with date vs salinity

4. **T-D Profile**
   ```
   Show temperature depth profile for float 1902482
   ```
   ✅ Expected: Line chart with temperature vs depth (inverted Y)

---

## 🎨 Customization

### **Change Chart Colors**
Edit `src/components/ChartRenderer.js`:
```javascript
marker: { 
  color: '#FF6B6B',  // Change this
  size: 6
}
```

### **Adjust Chart Height**
Edit `src/components/ChartRenderer.js`:
```javascript
style={{ width: '100%', height: '400px' }}  // Change height
```

### **Modify Theme**
Edit `src/components/ChartRenderer.js`:
```javascript
layout: {
  paper_bgcolor: '#1a2332',  // Background color
  plot_bgcolor: '#1a2332',   // Plot area color
  font: { color: '#e0e0e0' } // Text color
}
```

### **Add New Chart Type**
1. Add case in `transformData()` function:
```javascript
case 'my_new_chart':
  return {
    data: [{
      x: data.map(p => p.x),
      y: data.map(p => p.y),
      type: 'bar'  // or 'scatter', 'line', etc.
    }],
    layout: { ... }
  };
```

---

## 🐛 Troubleshooting

### **Chart Not Showing**

1. **Check API Response:**
   ```javascript
   console.log('Response:', response.data);
   console.log('Chart Data:', response.data.chart_data);
   ```

2. **Verify Data Structure:**
   ```javascript
   // In ChatContainer.js
   console.log('Message:', message);
   console.log('Has Chart Data:', !!message.chartData);
   ```

3. **Check Browser Console:**
   - Open DevTools (F12)
   - Look for errors in Console tab
   - Check Network tab for API response

### **Plotly Errors**

**Error: "Plotly is not defined"**
```bash
npm install plotly.js react-plotly.js
```

**Error: "Cannot read property 'data' of undefined"**
- Check that `chartData` exists before rendering
- Verify backend is sending `chart_data` in response

### **Styling Issues**

**Chart too small:**
```css
/* In ChartRenderer.css */
.chart-container .js-plotly-plot {
  height: 500px !important;  /* Increase height */
}
```

**Chart not responsive:**
```javascript
// In ChartRenderer.js
layout={{
  ...layout,
  autosize: true  // Ensure this is set
}}
```

---

## 📈 Advanced Features

### **1. Multiple Charts in One Message**
```javascript
// Backend can send array of charts
chart_data: [
  { type: 'temp_trend', data: [...] },
  { type: 'sal_trend', data: [...] }
]

// Frontend renders multiple charts
{message.chartData && Array.isArray(message.chartData) ? (
  message.chartData.map((chart, idx) => (
    <ChartRenderer key={idx} chartData={chart} />
  ))
) : (
  <ChartRenderer chartData={message.chartData} />
)}
```

### **2. Export Chart as Image**
Plotly has built-in export:
- Click camera icon in chart toolbar
- Downloads as PNG automatically

### **3. Custom Hover Templates**
```javascript
data: [{
  ...
  hovertemplate: '<b>Date</b>: %{x}<br>' +
                 '<b>Temp</b>: %{y}°C<br>' +
                 '<extra></extra>'
}]
```

### **4. Animation**
```javascript
layout: {
  ...
  transition: {
    duration: 500,
    easing: 'cubic-in-out'
  }
}
```

---

## 🔗 Comparison: Web vs Mobile

| Feature | Web (Plotly.js) | Mobile (Victory Native) |
|---------|----------------|------------------------|
| **Library** | Plotly.js | Victory Native |
| **Interactivity** | ✅ High (zoom, pan, hover) | ⚠️ Limited |
| **Performance** | ✅ Excellent | ✅ Good |
| **File Size** | ⚠️ Larger (~3MB) | ✅ Smaller (~500KB) |
| **Customization** | ✅ Extensive | ✅ Good |
| **3D Charts** | ✅ Yes | ❌ No |
| **Export** | ✅ Built-in PNG export | ⚠️ Manual |

---

## 📚 Resources

- [Plotly.js Documentation](https://plotly.com/javascript/)
- [React-Plotly.js GitHub](https://github.com/plotly/react-plotly.js)
- [Plotly Chart Types](https://plotly.com/javascript/basic-charts/)
- [Plotly Styling Guide](https://plotly.com/javascript/styling-figures/)

---

## ✅ Summary

The web graph visualization integration provides:

1. **Interactive Charts** - Zoom, pan, hover for detailed exploration
2. **Automatic Rendering** - Charts appear automatically with analysis results
3. **Beautiful Design** - Matches FloatChat's ocean theme
4. **Responsive** - Works on desktop, tablet, and mobile browsers
5. **Export Ready** - Built-in PNG export functionality

Users can now see their oceanographic data come to life with professional, interactive visualizations! 🌊📊
