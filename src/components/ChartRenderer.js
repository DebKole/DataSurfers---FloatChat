import React from 'react';
import Plot from 'react-plotly.js';
import './ChartRenderer.css';

const ChartRenderer = ({ chartData }) => {
  if (!chartData || !chartData.data || chartData.data.length === 0) {
    return null; // Don't show anything if no chart data
  }

  const transformData = () => {
    const { type, data } = chartData;

    switch (type) {
      case 'temp_trend':
      case 'sal_trend':
        // Time series: datetime vs value
        const dates = data.map(point => point.datetime || point.DATETIME);
        const values = data.map(point => 
          parseFloat(point.temperature || point.salinity || point.TEMP || point.SAL || 0)
        );
        
        return {
          data: [{
            x: dates,
            y: values,
            type: 'scatter',
            mode: 'lines+markers',
            marker: { 
              color: type === 'temp_trend' ? '#FF6B6B' : '#4ECDC4',
              size: 6
            },
            line: { 
              color: type === 'temp_trend' ? '#FF6B6B' : '#4ECDC4',
              width: 2
            },
            name: type === 'temp_trend' ? 'Temperature' : 'Salinity'
          }],
          layout: {
            title: chartData.title || (type === 'temp_trend' ? 'Temperature Trend' : 'Salinity Trend'),
            xaxis: { 
              title: chartData.xLabel || 'Date',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            yaxis: { 
              title: chartData.yLabel || (type === 'temp_trend' ? 'Temperature (°C)' : 'Salinity (PSU)'),
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            paper_bgcolor: '#1a2332',
            plot_bgcolor: '#1a2332',
            font: { color: '#e0e0e0' },
            hovermode: 'closest',
            showlegend: true,
            legend: {
              bgcolor: '#2a3f5f',
              bordercolor: '#4ECDC4',
              borderwidth: 1
            }
          }
        };

      case 'ts_curve':
        // T-S Curve: temperature vs salinity
        const temps = data.map(point => parseFloat(point.temperature || point.TEMP || 0));
        const sals = data.map(point => parseFloat(point.salinity || point.SAL || 0));
        
        return {
          data: [{
            x: temps,
            y: sals,
            type: 'scatter',
            mode: 'markers',
            marker: { 
              color: '#4ECDC4',
              size: 8,
              opacity: 0.7
            },
            name: 'T-S Data'
          }],
          layout: {
            title: chartData.title || 'Temperature-Salinity Curve',
            xaxis: { 
              title: chartData.xLabel || 'Temperature (°C)',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            yaxis: { 
              title: chartData.yLabel || 'Salinity (PSU)',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            paper_bgcolor: '#1a2332',
            plot_bgcolor: '#1a2332',
            font: { color: '#e0e0e0' },
            hovermode: 'closest'
          }
        };

      case 'td_curve':
        // T-D Profile: temperature vs depth
        const tempsTD = data.map(point => parseFloat(point.temperature || point.TEMP || 0));
        const depths = data.map(point => parseFloat(point.level || point.LEVEL || point.depth || point.DEPTH || 0));
        
        return {
          data: [{
            x: tempsTD,
            y: depths,
            type: 'scatter',
            mode: 'lines+markers',
            marker: { 
              color: '#FF6B6B',
              size: 6
            },
            line: {
              color: '#FF6B6B',
              width: 2
            },
            name: 'Temperature Profile'
          }],
          layout: {
            title: chartData.title || 'Temperature-Depth Profile',
            xaxis: { 
              title: chartData.xLabel || 'Temperature (°C)',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            yaxis: { 
              title: chartData.yLabel || 'Depth (m)',
              autorange: 'reversed', // Depth increases downward
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            paper_bgcolor: '#1a2332',
            plot_bgcolor: '#1a2332',
            font: { color: '#e0e0e0' },
            hovermode: 'closest'
          }
        };

      case 'comparison':
        // Multiple datasets comparison
        // Assuming data is already structured for comparison
        return {
          data: data.map((dataset, idx) => ({
            x: dataset.x || dataset.dates,
            y: dataset.y || dataset.values,
            type: 'scatter',
            mode: 'lines+markers',
            name: dataset.label || `Dataset ${idx + 1}`,
            marker: { size: 6 },
            line: { width: 2 }
          })),
          layout: {
            title: chartData.title || 'Data Comparison',
            xaxis: { 
              title: chartData.xLabel || 'X',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            yaxis: { 
              title: chartData.yLabel || 'Y',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            paper_bgcolor: '#1a2332',
            plot_bgcolor: '#1a2332',
            font: { color: '#e0e0e0' },
            hovermode: 'closest',
            showlegend: true,
            legend: {
              bgcolor: '#2a3f5f',
              bordercolor: '#4ECDC4',
              borderwidth: 1
            }
          }
        };

      case 'three_axis_line':
        // Three-axis line chart with multiple Y-axes
        const xData = data.x || [];
        const y1Data = data.y1 || [];
        const y2Data = data.y2 || [];
        const y3Data = data.y3 || [];
        
        const series = [{
          x: xData,
          y: y1Data,
          type: 'scatter',
          mode: 'lines+markers',
          name: chartData.y1Label || 'Series 1',
          marker: { 
            color: '#FF6B6B',
            size: 6
          },
          line: { 
            color: '#FF6B6B',
            width: 2
          }
        }];

        if (y2Data.length > 0) {
          series.push({
            x: xData,
            y: y2Data,
            type: 'scatter',
            mode: 'lines+markers',
            name: chartData.y2Label || 'Series 2',
            yaxis: 'y2',
            marker: { 
              color: '#4ECDC4',
              size: 6
            },
            line: { 
              color: '#4ECDC4',
              width: 2
            }
          });
        }

        if (y3Data.length > 0) {
          series.push({
            x: xData,
            y: y3Data,
            type: 'scatter',
            mode: 'lines+markers',
            name: chartData.y3Label || 'Series 3',
            yaxis: 'y3',
            marker: { 
              color: '#FFD166',
              size: 6
            },
            line: { 
              color: '#FFD166',
              width: 2
            }
          });
        }

        return {
          data: series,
          layout: {
            title: chartData.title || 'Multi-Axis Line Chart',
            xaxis: { 
              title: chartData.xLabel || 'X-Axis',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            yaxis: { 
              title: chartData.y1Label || 'Y1-Axis',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            yaxis2: chartData.y2Label ? {
              title: chartData.y2Label,
              overlaying: 'y',
              side: 'right',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            } : undefined,
            yaxis3: chartData.y3Label ? {
              title: chartData.y3Label,
              overlaying: 'y',
              side: 'right',
              position: 1,
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            } : undefined,
            paper_bgcolor: '#1a2332',
            plot_bgcolor: '#1a2332',
            font: { color: '#e0e0e0' },
            showlegend: true,
            legend: {
              bgcolor: '#2a3f5f',
              bordercolor: '#4ECDC4',
              borderwidth: 1
            }
          }
        };

      default:
        // Generic chart
        return {
          data: [{
            x: data.map((_, idx) => idx),
            y: data.map(point => point.y || point.value || 0),
            type: 'scatter',
            mode: 'lines+markers',
            marker: { color: '#4ECDC4', size: 6 },
            line: { color: '#4ECDC4', width: 2 }
          }],
          layout: {
            title: chartData.title || 'Data Visualization',
            xaxis: { 
              title: chartData.xLabel || 'X',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            yaxis: { 
              title: chartData.yLabel || 'Y',
              gridcolor: '#2a3f5f',
              color: '#e0e0e0'
            },
            paper_bgcolor: '#1a2332',
            plot_bgcolor: '#1a2332',
            font: { color: '#e0e0e0' },
            hovermode: 'closest'
          }
        };
    }
  };

  const { data: plotData, layout } = transformData();

  return (
    <div className="chart-container">
      <Plot
        data={plotData}
        layout={{
          ...layout,
          autosize: true,
          margin: { l: 60, r: 30, t: 50, b: 60 }
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
        }}
        style={{ width: '100%', height: '400px' }}
      />
    </div>
  );
};

export default ChartRenderer;
