// Domain-oriented hooks for data fetching and mutations

import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/api/client';
import { queryKeys } from '@/state';

/**
 * Hook for searching locations
 */
export function useLocations(query: string) {
  return useQuery({
    queryKey: queryKeys.locations.search(query),
    queryFn: () => apiClient.searchLocations(query),
    enabled: query.length > 2, // Only search if query is meaningful
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook for getting a specific location
 */
export function useLocation(id: string) {
  return useQuery({
    queryKey: queryKeys.locations.detail(id),
    queryFn: () => apiClient.getLocation(id),
    enabled: !!id,
  });
}

/**
 * Hook for getting current weather
 */
export function useCurrentWeather(locationId: string) {
  return useQuery({
    queryKey: queryKeys.weather.current(locationId),
    queryFn: () => apiClient.getCurrentWeather(locationId),
    enabled: !!locationId,
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });
}

/**
 * Hook for getting weather forecast
 */
export function useWeatherForecast(locationId: string) {
  return useQuery({
    queryKey: queryKeys.weather.forecast(locationId),
    queryFn: () => apiClient.getWeatherForecast(locationId),
    enabled: !!locationId,
    staleTime: 30 * 60 * 1000, // 30 minutes - forecast doesn't change as often
  });
}

/**
 * Hook for health check
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: () => apiClient.healthCheck(),
    refetchInterval: 30000, // Check every 30 seconds
    retry: false, // Don't retry health checks
  });
}