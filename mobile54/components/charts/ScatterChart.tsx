import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { VictoryScatter, VictoryChart, VictoryAxis, VictoryTheme } from 'victory-native';
import { oceanTheme } from '../../constants/oceanTheme';

interface DataPoint {
  x: number;
  y: number;
  label?: string;
}

interface ScatterChartProps {
  data: DataPoint[];
  title?: string;
  xLabel?: string;
  yLabel?: string;
  color?: string;
}

export default function ScatterChart({ 
  data, 
  title, 
  xLabel = 'X', 
  yLabel = 'Y',
  color = oceanTheme.colors.coral 
}: ScatterChartProps) {
  const screenWidth = Dimensions.get('window').width;
  
  return (
    <View style={styles.container}>
      {title && <Text style={styles.title}>{title}</Text>}
      
      <VictoryChart
        width={screenWidth - 32}
        height={300}
        theme={VictoryTheme.material}
        padding={{ top: 20, bottom: 60, left: 60, right: 20 }}
      >
        <VictoryAxis
          label={xLabel}
          style={{
            axis: { stroke: oceanTheme.colors.border },
            axisLabel: { fill: oceanTheme.colors.lightWave, fontSize: 12, padding: 35 },
            tickLabels: { fill: oceanTheme.colors.mist, fontSize: 10 },
            grid: { stroke: oceanTheme.colors.border, strokeDasharray: '4,4' }
          }}
        />
        
        <VictoryAxis
          dependentAxis
          label={yLabel}
          style={{
            axis: { stroke: oceanTheme.colors.border },
            axisLabel: { fill: oceanTheme.colors.lightWave, fontSize: 12, padding: 45 },
            tickLabels: { fill: oceanTheme.colors.mist, fontSize: 10 },
            grid: { stroke: oceanTheme.colors.border, strokeDasharray: '4,4' }
          }}
        />
        
        <VictoryScatter
          data={data}
          size={4}
          style={{
            data: { fill: color, opacity: 0.7 }
          }}
        />
      </VictoryChart>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: oceanTheme.colors.midOcean,
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
  },
  title: {
    color: oceanTheme.colors.lightWave,
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
});
