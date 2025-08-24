import React, { useState, useMemo } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Select,
  SimpleGrid,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  Divider
} from '@chakra-ui/react';
import { subDays, format } from 'date-fns';
import { useLocation } from '../context/LocationContext';
import {
  useObservations,
  useAggregations,
  useTrends,
  useAccuracy
} from '../hooks/useAnalytics';
import TimeSeriesChart from '../components/charts/TimeSeriesChart';
import TrendDeltaCard from '../components/charts/TrendDeltaCard';
import AnalyticsSummary from '../components/AnalyticsSummary';

const AnalyticsDashboard: React.FC = () => {
  const { selectedLocation, locations } = useLocation();
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d'>('7d');
  
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBgColor = useColorModeValue('white', 'gray.800');
  
  // Date ranges for data fetching
  const endDate = new Date();
  const startDate = selectedPeriod === '7d' ? subDays(endDate, 7) : subDays(endDate, 30);
  
  // Data fetching hooks
  const {
    data: observations,
    isLoading: observationsLoading,
    error: observationsError
  } = useObservations(selectedLocation?.id || 0, startDate, endDate, !!selectedLocation);
  
  const {
    data: aggregations,
    isLoading: aggregationsLoading,
    error: aggregationsError
  } = useAggregations(selectedLocation?.id || 0, startDate, endDate, !!selectedLocation);
  
  const {
    data: trends,
    isLoading: trendsLoading,
    error: trendsError
  } = useTrends(selectedLocation?.id || 0, selectedPeriod, ['avg_temp_c', 'total_precip_mm', 'max_wind_kph'], !!selectedLocation);
  
  const {
    data: accuracy,
    isLoading: accuracyLoading,
    error: accuracyError
  } = useAccuracy(selectedLocation?.id || 0, startDate, endDate, ['temp_c', 'precipitation_probability_pct'], !!selectedLocation);

  // Transform data for charts
  const observationChartData = useMemo(() => {
    if (!observations) return [];
    
    return observations.map(obs => ({
      timestamp: obs.observed_at,
      temp_c: obs.temp_c,
      wind_kph: obs.wind_kph,
      precip_mm: obs.precip_mm,
      humidity_pct: obs.humidity_pct
    }));
  }, [observations]);

  const aggregationChartData = useMemo(() => {
    if (!aggregations) return [];
    
    return aggregations.map(agg => ({
      timestamp: agg.date,
      temp_min_c: agg.temp_min_c,
      temp_max_c: agg.temp_max_c,
      avg_temp_c: agg.avg_temp_c,
      total_precip_mm: agg.total_precip_mm,
      max_wind_kph: agg.max_wind_kph
    }));
  }, [aggregations]);

  // Extract trend data by metric
  const getTrendByMetric = (metric: string) => {
    return trends?.find(t => t.metric === metric);
  };

  const isLoading = observationsLoading || aggregationsLoading || trendsLoading || accuracyLoading;
  const hasError = observationsError || aggregationsError || trendsError || accuracyError;
  
  // Check if all data is loaded but empty
  const isDataLoaded = !isLoading && !hasError;
  const hasData = (observations && observations.length > 0) || 
                  (aggregations && aggregations.length > 0) || 
                  (trends && trends.length > 0) || 
                  (accuracy && accuracy.length > 0);
  const showEmptyState = isDataLoaded && !hasData;

  if (!selectedLocation) {
    return (
      <Box p={8} textAlign="center">
        <Heading size="lg" mb={4}>Analytics Dashboard</Heading>
        <Text color="gray.500">
          {locations.length === 0 
            ? "No locations available. Add a location first."
            : "Select a location to view analytics."
          }
        </Text>
      </Box>
    );
  }

  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        {/* Header */}
        <Box bg={cardBgColor} p={6} borderRadius="lg" shadow="sm">
          <HStack justify="space-between" align="center" mb={4}>
            <VStack align="start" spacing={1}>
              <Heading size="lg">Analytics Dashboard</Heading>
              <Text color="gray.500">{selectedLocation.name}</Text>
            </VStack>
            
            <HStack spacing={4}>
              <Select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value as '7d' | '30d')}
                width="auto"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
              </Select>
            </HStack>
          </HStack>
          
          <Text fontSize="sm" color="gray.500">
            Period: {format(startDate, 'MMM dd, yyyy')} - {format(endDate, 'MMM dd, yyyy')}
          </Text>
        </Box>

        {/* Error display */}
        {hasError && (
          <Alert status="error" borderRadius="lg">
            <AlertIcon />
            Failed to load analytics data. Please try again.
          </Alert>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <Box textAlign="center" py={8}>
            <Spinner size="lg" color="blue.500" />
            <Text mt={4} color="gray.500">Loading analytics data...</Text>
          </Box>
        )}

        {/* Empty state */}
        {showEmptyState && (
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            <VStack align="start" spacing={2}>
              <Text fontWeight="semibold">No analytics data available</Text>
              <Text fontSize="sm">
                No data found for the selected period. This could be because:
              </Text>
              <VStack align="start" spacing={1} fontSize="sm" pl={4}>
                <Text>• The location is newly added</Text>
                <Text>• No weather data has been collected yet</Text>
                <Text>• Try selecting a different time period</Text>
              </VStack>
            </VStack>
          </Alert>
        )}

        {/* Content - only show when we have data */}
        {!showEmptyState && isDataLoaded && (
        <>
        {/* Trend cards */}
        {trends && trends.length > 0 && (
          <Box>
            <Heading size="md" mb={4}>Current Trends</Heading>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
              <TrendDeltaCard
                title="Average Temperature"
                currentValue={getTrendByMetric('avg_temp_c')?.current_value || null}
                previousValue={getTrendByMetric('avg_temp_c')?.previous_value || null}
                delta={getTrendByMetric('avg_temp_c')?.delta || null}
                pctChange={getTrendByMetric('avg_temp_c')?.pct_change || null}
                unit="°C"
                precision={1}
              />
              
              <TrendDeltaCard
                title="Total Precipitation"
                currentValue={getTrendByMetric('total_precip_mm')?.current_value || null}
                previousValue={getTrendByMetric('total_precip_mm')?.previous_value || null}
                delta={getTrendByMetric('total_precip_mm')?.delta || null}
                pctChange={getTrendByMetric('total_precip_mm')?.pct_change || null}
                unit="mm"
                precision={1}
              />
              
              <TrendDeltaCard
                title="Max Wind Speed"
                currentValue={getTrendByMetric('max_wind_kph')?.current_value || null}
                previousValue={getTrendByMetric('max_wind_kph')?.previous_value || null}
                delta={getTrendByMetric('max_wind_kph')?.delta || null}
                pctChange={getTrendByMetric('max_wind_kph')?.pct_change || null}
                unit=" km/h"
                precision={1}
              />
            </SimpleGrid>
          </Box>
        )}

        <Divider />

        {/* Charts */}
        <SimpleGrid columns={{ base: 1, xl: 2 }} spacing={6}>
          {/* Daily aggregates chart */}
          {aggregationChartData.length > 0 && (
            <Box bg={cardBgColor} p={6} borderRadius="lg" shadow="sm">
              <TimeSeriesChart
                data={aggregationChartData}
                title="Daily Temperature Range"
                xAxisKey="timestamp"
                yAxisKeys={[
                  { key: 'temp_min_c', label: 'Min Temp', color: '#3182ce', unit: '°C' },
                  { key: 'temp_max_c', label: 'Max Temp', color: '#e53e3e', unit: '°C' },
                  { key: 'avg_temp_c', label: 'Avg Temp', color: '#38a169', unit: '°C' }
                ]}
                height={300}
              />
            </Box>
          )}

          {/* Observations chart */}
          {observationChartData.length > 0 && (
            <Box bg={cardBgColor} p={6} borderRadius="lg" shadow="sm">
              <TimeSeriesChart
                data={observationChartData}
                title="Hourly Observations"
                xAxisKey="timestamp"
                yAxisKeys={[
                  { key: 'temp_c', label: 'Temperature', color: '#3182ce', unit: '°C' },
                  { key: 'wind_kph', label: 'Wind Speed', color: '#38a169', unit: ' km/h' }
                ]}
                height={300}
              />
            </Box>
          )}
        </SimpleGrid>

        {/* Forecast Accuracy Table */}
        {accuracy && accuracy.length > 0 && (
          <Box bg={cardBgColor} p={6} borderRadius="lg" shadow="sm">
            <Heading size="md" mb={4}>Recent Forecast Accuracy</Heading>
            <Text fontSize="sm" color="gray.500" mb={4}>
              Showing {accuracy.length} accuracy records from the last {selectedPeriod}
            </Text>
            
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              {['temp_c', 'precipitation_probability_pct'].map(variable => {
                const variableData = accuracy.filter(a => a.variable === variable);
                const avgError = variableData.reduce((sum, a) => sum + (a.abs_error || 0), 0) / variableData.length;
                
                return (
                  <Box key={variable} p={4} border="1px solid" borderColor="gray.200" borderRadius="md">
                    <Text fontWeight="semibold" mb={2}>
                      {variable === 'temp_c' ? 'Temperature' : 'Precipitation Probability'}
                    </Text>
                    <Text fontSize="sm" color="gray.500">
                      Avg Error: {avgError.toFixed(2)} {variable === 'temp_c' ? '°C' : '%'}
                    </Text>
                    <Text fontSize="sm" color="gray.500">
                      Samples: {variableData.length}
                    </Text>
                  </Box>
                );
              })}
            </SimpleGrid>
          </Box>
        )}
        </>
        )} {/* End of content wrapper */}

        {/* Analytics Summary - show even when no data, but disable if no underlying data */}
        <AnalyticsSummary
          locationId={selectedLocation.id}
          period={selectedPeriod}
          metrics={['avg_temp_c', 'total_precip_mm', 'max_wind_kph']}
          hasUnderlyingData={hasData}
        />
      </VStack>
    </Box>
  );
};

export default AnalyticsDashboard;