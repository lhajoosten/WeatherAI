import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Box, Text, useColorModeValue } from '@chakra-ui/react';
import { format } from 'date-fns';

interface DataPoint {
  timestamp: string;
  [key: string]: string | number | null;
}

interface TimeSeriesChartProps {
  data: DataPoint[];
  title: string;
  xAxisKey: string;
  yAxisKeys: {
    key: string;
    label: string;
    color: string;
    unit?: string;
  }[];
  height?: number;
  showLegend?: boolean;
}

const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  data,
  title,
  xAxisKey,
  yAxisKeys,
  height = 300,
  showLegend = true
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const gridColor = useColorModeValue('#f0f0f0', '#4a5568');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  const formatXAxisTick = (tickItem: string) => {
    try {
      const date = new Date(tickItem);
      return format(date, 'MMM dd HH:mm');
    } catch {
      return tickItem;
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          bg={bgColor}
          border="1px solid"
          borderColor="gray.200"
          borderRadius="md"
          p={3}
          shadow="lg"
        >
          <Text fontWeight="semibold" mb={2}>
            {format(new Date(label), 'MMM dd, yyyy HH:mm')}
          </Text>
          {payload.map((entry: any, index: number) => {
            const yAxisConfig = yAxisKeys.find(y => y.key === entry.dataKey);
            const unit = yAxisConfig?.unit || '';
            
            return (
              <Text key={index} color={entry.color} fontSize="sm">
                {entry.name}: {entry.value !== null ? `${entry.value}${unit}` : 'N/A'}
              </Text>
            );
          })}
        </Box>
      );
    }
    return null;
  };

  return (
    <Box>
      <Text fontSize="lg" fontWeight="semibold" mb={4} color={textColor}>
        {title}
      </Text>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
          <XAxis
            dataKey={xAxisKey}
            tickFormatter={formatXAxisTick}
            stroke={textColor}
            fontSize={12}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis stroke={textColor} fontSize={12} />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
          {yAxisKeys.map((yAxis) => (
            <Line
              key={yAxis.key}
              type="monotone"
              dataKey={yAxis.key}
              stroke={yAxis.color}
              strokeWidth={2}
              dot={false}
              name={yAxis.label}
              connectNulls={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default TimeSeriesChart;