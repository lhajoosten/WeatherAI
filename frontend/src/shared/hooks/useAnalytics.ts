import { useQuery, useMutation, UseQueryResult } from '@tanstack/react-query';
import { analyticsService } from '@/shared/api/services';
import type {
  ObservationResponse,
  AggregationResponse,
  TrendResponse,
  AccuracyResponse,
  AnalyticsSummaryRequest,
  AnalyticsSummaryResponse,
  DashboardResponse,
} from '@/shared/types/api';

// Re-export types for backward compatibility
export type ObservationData = ObservationResponse;
export type AggregationData = AggregationResponse;
export type TrendData = TrendResponse;
export type AccuracyData = AccuracyResponse;
export type AnalyticsSummaryData = AnalyticsSummaryResponse;

// Hooks for analytics API calls

export const useObservations = (
  locationId: number,
  startDate?: Date,
  endDate?: Date,
  enabled: boolean = true
): UseQueryResult<ObservationResponse[], Error> => {
  const start = startDate ? startDate.toISOString() : undefined;
  const end = endDate ? endDate.toISOString() : undefined;
  
  return useQuery({
    queryKey: ['observations', locationId, start, end],
    queryFn: () => analyticsService.getObservations({
      location_id: locationId,
      start,
      end,
      limit: 1000
    }),
    enabled: enabled && locationId > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
};

export const useAggregations = (
  locationId: number,
  startDate?: Date,
  endDate?: Date,
  enabled: boolean = true
): UseQueryResult<AggregationResponse[], Error> => {
  const start = startDate ? startDate.toISOString() : undefined;
  const end = endDate ? endDate.toISOString() : undefined;
  
  return useQuery({
    queryKey: ['aggregations', locationId, start, end],
    queryFn: () => analyticsService.getDailyAggregations({
      location_id: locationId,
      start,
      end
    }),
    enabled: enabled && locationId > 0,
    staleTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false
  });
};

export const useTrends = (
  locationId: number,
  period: '7d' | '30d' = '30d',
  metrics: string[] = ['avg_temp_c', 'total_precip_mm', 'max_wind_kph'],
  enabled: boolean = true
): UseQueryResult<TrendResponse[], Error> => {
  return useQuery({
    queryKey: ['trends', locationId, period, metrics],
    queryFn: () => analyticsService.getTrends({
      location_id: locationId,
      period,
      metrics
    }),
    enabled: enabled && locationId > 0,
    staleTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: false
  });
};

export const useAccuracy = (
  locationId: number,
  startDate?: Date,
  endDate?: Date,
  variables: string[] = ['temp_c', 'precipitation_probability_pct'],
  enabled: boolean = true
): UseQueryResult<AccuracyResponse[], Error> => {
  const start = startDate ? startDate.toISOString() : undefined;
  const end = endDate ? endDate.toISOString() : undefined;
  
  return useQuery({
    queryKey: ['accuracy', locationId, start, end, variables],
    queryFn: () => analyticsService.getAccuracy({
      location_id: locationId,
      start,
      end,
      variables
    }),
    enabled: enabled && locationId > 0,
    staleTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: false
  });
};

export const useAnalyticsSummary = () => {
  return useMutation<AnalyticsSummaryResponse, Error, AnalyticsSummaryRequest>({
    mutationFn: analyticsService.generateSummary
  });
};

export const useAnalyticsDashboard = (
  locationId: number,
  limit?: number,
  enabled: boolean = true
): UseQueryResult<DashboardResponse, Error> => {
  return useQuery({
    queryKey: ['analytics-dashboard', locationId, limit],
    queryFn: () => analyticsService.getDashboard(locationId, limit),
    enabled: enabled && locationId > 0,
    staleTime: 15 * 60 * 1000, // 15 minutes (matches backend cache TTL)
    refetchOnWindowFocus: false
  });
};