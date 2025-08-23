import { useQuery, useMutation, UseQueryResult } from '@tanstack/react-query';
import { format } from 'date-fns';
import apiClient from '../services/apiClient';

// Types for analytics data
export interface ObservationData {
  id: number;
  location_id: number;
  observed_at: string;
  temp_c: number | null;
  wind_kph: number | null;
  precip_mm: number | null;
  humidity_pct: number | null;
  condition_code: string | null;
  source: string;
}

export interface AggregationData {
  id: number;
  location_id: number;
  date: string;
  temp_min_c: number | null;
  temp_max_c: number | null;
  avg_temp_c: number | null;
  total_precip_mm: number | null;
  max_wind_kph: number | null;
  heating_degree_days: number | null;
  cooling_degree_days: number | null;
  generated_at: string | null;
}

export interface TrendData {
  id: number;
  location_id: number;
  metric: string;
  period: string;
  current_value: number | null;
  previous_value: number | null;
  delta: number | null;
  pct_change: number | null;
  generated_at: string | null;
}

export interface AccuracyData {
  id: number;
  location_id: number;
  target_time: string;
  forecast_issue_time: string;
  variable: string;
  forecast_value: number | null;
  observed_value: number | null;
  abs_error: number | null;
  pct_error: number | null;
  created_at: string | null;
}

export interface AnalyticsSummaryData {
  narrative: string;
  model: string;
  tokens_in: number;
  tokens_out: number;
  prompt_version: string;
  generated_at: string;
}

export interface AnalyticsSummaryRequest {
  location_id: number;
  period: '7d' | '30d';
  metrics: string[];
}

// Hooks for analytics API calls

export const useObservations = (
  locationId: number,
  startDate?: Date,
  endDate?: Date,
  enabled: boolean = true
): UseQueryResult<ObservationData[], Error> => {
  const start = startDate ? startDate.toISOString() : undefined;
  const end = endDate ? endDate.toISOString() : undefined;
  
  return useQuery({
    queryKey: ['observations', locationId, start, end],
    queryFn: async () => {
      const params = new URLSearchParams({
        location_id: locationId.toString(),
        limit: '1000'
      });
      
      if (start) params.append('start', start);
      if (end) params.append('end', end);
      
      const response = await apiClient.get(`/v1/analytics/observations?${params}`);
      return response.data;
    },
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
): UseQueryResult<AggregationData[], Error> => {
  const start = startDate ? startDate.toISOString() : undefined;
  const end = endDate ? endDate.toISOString() : undefined;
  
  return useQuery({
    queryKey: ['aggregations', locationId, start, end],
    queryFn: async () => {
      const params = new URLSearchParams({
        location_id: locationId.toString()
      });
      
      if (start) params.append('start', start);
      if (end) params.append('end', end);
      
      const response = await apiClient.get(`/v1/analytics/aggregations/daily?${params}`);
      return response.data;
    },
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
): UseQueryResult<TrendData[], Error> => {
  return useQuery({
    queryKey: ['trends', locationId, period, metrics],
    queryFn: async () => {
      const params = new URLSearchParams({
        location_id: locationId.toString(),
        period: period
      });
      
      metrics.forEach(metric => params.append('metrics', metric));
      
      const response = await apiClient.get(`/v1/analytics/trends?${params}`);
      return response.data;
    },
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
): UseQueryResult<AccuracyData[], Error> => {
  const start = startDate ? startDate.toISOString() : undefined;
  const end = endDate ? endDate.toISOString() : undefined;
  
  return useQuery({
    queryKey: ['accuracy', locationId, start, end, variables],
    queryFn: async () => {
      const params = new URLSearchParams({
        location_id: locationId.toString()
      });
      
      if (start) params.append('start', start);
      if (end) params.append('end', end);
      variables.forEach(variable => params.append('variables', variable));
      
      const response = await apiClient.get(`/v1/analytics/accuracy?${params}`);
      return response.data;
    },
    enabled: enabled && locationId > 0,
    staleTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: false
  });
};

export const useAnalyticsSummary = () => {
  return useMutation<AnalyticsSummaryData, Error, AnalyticsSummaryRequest>({
    mutationFn: async (request: AnalyticsSummaryRequest) => {
      const response = await apiClient.post('/v1/analytics/summary', request);
      return response.data;
    }
  });
};