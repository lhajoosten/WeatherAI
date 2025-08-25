import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/shared/api';
import { RemoteData, remoteData } from '@/shared/types';

// Placeholder interface for weather data
interface WeatherData {
  temperature: number;
  condition: string;
  humidity: number;
  windSpeed: number;
  location: string;
}

/**
 * Placeholder hook for current weather data
 * Returns not implemented status until backend endpoint is available
 */
export const useCurrentWeather = (locationId: string): RemoteData<WeatherData> => {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.weather.current(locationId),
    queryFn: async () => {
      // Placeholder implementation - will be replaced when backend endpoint is ready
      throw new Error('Current weather endpoint not yet implemented');
    },
    enabled: false, // Disabled until endpoint is implemented
    retry: false,
  });

  if (isLoading) {
    return remoteData.loading();
  }

  if (error) {
    return remoteData.error({
      kind: 'unknown',
      message: 'Current weather feature not yet implemented',
    });
  }

  return data ? remoteData.success(data) : remoteData.idle();
};