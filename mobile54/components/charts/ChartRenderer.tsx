import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import LineChart from './LineChart';
import ScatterChart from './ScatterChart';
import { oceanTheme } from '../../constants/oceanTheme';

interface ChartData {
  type: 'line' | 'scatter' | 'ts_curve' | 'td_curve' | 'temp_trend' | 'sal_trend';
  data: any[];
  title?: string;
  xLabel?: string;
  yLabel?: string;
}

interface ChartRendererProps {
  chartData: ChartData;
}

export default function ChartRenderer({ chartData }: ChartRendererProps) {
  if (!chartData || !chartData.data || chartData.data.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No chart data available</Text>
      </View>
    );
  }

  // Transform data based on chart type
  const transformData = () => {
    const { type, data } = chartData;

    switch (type) {
      case 'temp_trend':
      case 'sal_trend':
        // Temperature/Salinity trend: datetime vs value
        return data.map((point: any) => ({
          x: new Date(point.datetime || point.DATETIME),
          y: parseFloat(point.temperature || point.salinity || point.TEMP || point.SAL || 0)
        }));

      case 'ts_curve':
        // T-S Curve: temperature vs salinity
        return data.map((point: any) => ({
          x: parseFloat(point.temperature || point.TEMP || 0),
          y: parseFloat(point.salinity || point.SAL || 0)
        }));

      case 'td_curve':
        // T-D Profile: temperature vs depth/level
        return data.map((point: any) => ({
          x: parseFloat(point.temperature || point.TEMP || 0),
          y: parseFloat(point.level || point.LEVEL || point.depth || point.DEPTH || 0)
        }));

      case 'line':
        // Generic line chart
        return data.map((point: any) => ({
          x: point.x,
          y: parseFloat(point.y || 0)
        }));

      case 'scatter':
        // Generic scatter chart
        return data.map((point: any) => ({
          x: parseFloat(point.x || 0),
          y: parseFloat(point.y || 0)
        }));

      default:
        return data;
    }
  };

  const transformedData = transformData();

  // Determine chart component and labels
  const renderChart = () => {
    const { type, title } = chartData;

    switch (type) {
      case 'temp_trend':
        return (
          <LineChart
            data={transformedData}
            title={title || 'Temperature Trend'}
            xLabel="Date"
            yLabel="Temperature (°C)"
            color={oceanTheme.colors.coral}
          />
        );

      case 'sal_trend':
        return (
          <LineChart
            data={transformedData}
            title={title || 'Salinity Trend'}
            xLabel="Date"
            yLabel="Salinity (PSU)"
            color={oceanTheme.colors.teal}
          />
        );

      case 'ts_curve':
        return (
          <ScatterChart
            data={transformedData}
            title={title || 'T-S Curve'}
            xLabel="Temperature (°C)"
            yLabel="Salinity (PSU)"
            color={oceanTheme.colors.teal}
          />
        );

      case 'td_curve':
        return (
          <ScatterChart
            data={transformedData}
            title={title || 'T-D Profile'}
            xLabel="Temperature (°C)"
            yLabel="Depth (m)"
            color={oceanTheme.colors.coral}
          />
        );

      case 'line':
        return (
          <LineChart
            data={transformedData}
            title={title}
            xLabel={chartData.xLabel}
            yLabel={chartData.yLabel}
          />
        );

      case 'scatter':
        return (
          <ScatterChart
            data={transformedData}
            title={title}
            xLabel={chartData.xLabel}
            yLabel={chartData.yLabel}
          />
        );

      default:
        return (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>Unsupported chart type: {type}</Text>
          </View>
        );
    }
  };

  return <View style={styles.container}>{renderChart()}</View>;
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
  },
  emptyContainer: {
    backgroundColor: oceanTheme.colors.midOcean,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    color: oceanTheme.colors.mist,
    fontSize: 14,
  },
});
