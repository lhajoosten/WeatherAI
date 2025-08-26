import { useQuery } from '@tanstack/react-query';
import { ingestionService } from '@/shared/api/services';

// React Query keys for environmental data
export const environmentalQueryKeys = {
  airQuality: (locationId: number, start?: string, end?: string) => 
    ['environmental', 'air-quality', locationId, start, end],
  astronomy: (locationId: number, start?: string, end?: string) => 
    ['environmental', 'astronomy', locationId, start, end],
};

/**
 * Hook for fetching air quality data
 */
export const useAirQuality = (
  locationId: number,
  startDate?: Date,
  endDate?: Date,
  enabled: boolean = true
) => {
  const start = startDate ? startDate.toISOString() : undefined;
  const end = endDate ? endDate.toISOString() : undefined;
  
  return useQuery({
    queryKey: environmentalQueryKeys.airQuality(locationId, start, end),
    queryFn: () => ingestionService.getAirQuality({
      location_id: locationId,
      start,
      end,
      limit: 1000
    }),
    enabled: enabled && locationId > 0,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  });
};

/**
 * Hook for fetching astronomy data
 */
export const useAstronomy = (
  locationId: number,
  startDate?: Date,
  endDate?: Date,
  enabled: boolean = true
) => {
  const start = startDate ? startDate.toISOString() : undefined;
  const end = endDate ? endDate.toISOString() : undefined;
  
  return useQuery({
    queryKey: environmentalQueryKeys.astronomy(locationId, start, end),
    queryFn: () => ingestionService.getAstronomyDaily({
      location_id: locationId,
      start,
      end,
      limit: 100
    }),
    enabled: enabled && locationId > 0,
    staleTime: 60 * 60 * 1000, // 1 hour - astronomy data changes slowly
    retry: 2,
  });
};