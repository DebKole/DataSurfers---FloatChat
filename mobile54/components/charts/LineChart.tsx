import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { VictoryLine, VictoryChart, VictoryAxis, VictoryTheme, VictoryScatter } from 'victory-native';
import { oceanTheme } from '../../constants/oceanTheme';

interface DataPoint {
  x: number | string | Date;
  y: number;
}

interface LineChartProps {
  data: DataPoint[];
  title?: string;
  xLabel?: string;
  yLabel?: string;
  color?: string;
}

export default function LineChart({ 
  data, 
  title, 
  xLabel = 'X', 
  yLabel = 'Y',
  color = oceanTheme.colors.teal 
}: LineChartProps) {
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
        
        <VictoryLine
          data={data}
          style={{
            data: { stroke: color, strokeWidth: 2 }
          }}
        />
        
        <VictoryScatter
          data={data}
          size={3}
          style={{
            data: { fill: color }
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
