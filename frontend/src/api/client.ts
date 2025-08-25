// Enhanced API client with typed endpoints and error mapping

import { httpClient } from '@/shared/api/client';
import { mapToAppError } from '@/shared/api/errors';

// Location types
export interface Location {
  id: string;
  name: string;
  country: string;
  latitude: number;
  longitude: number;
}

export interface LocationSearchResult {
  locations: Location[];
  query: string;
  count: number;
}

// User types  
export interface User {
  id: string;
  email: string;
  name: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  language: string;
  timezone: string;
  units: 'metric' | 'imperial';
}

// Weather types
export interface CurrentWeather {
  locationId: string;
  temperature: number;
  humidity: number;
  windSpeed: number;
  description: string;
  timestamp: string;
}

export interface WeatherForecast {
  locationId: string;
  days: DayForecast[];
}

export interface DayForecast {
  date: string;
  high: number;
  low: number;
  description: string;
  precipitation: number;
}

// RAG types
export interface RagAskRequest {
  query: string;
  locationId?: string;
  context?: Record<string, unknown>;
}

export interface RagResponse {
  answer: string;
  sources: RagSource[];
  requestId: string;
}

export interface RagSource {
  type: 'weather' | 'location' | 'general';
  title: string;
  excerpt: string;
  url?: string;
}

/**
 * Enhanced API client with typed endpoints
 */
export class ApiClient {
  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      return await httpClient.get('/health');
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // Location endpoints
  async searchLocations(query: string): Promise<LocationSearchResult> {
    try {
      return await httpClient.get(`/locations/search?q=${encodeURIComponent(query)}`);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async getLocation(id: string): Promise<Location> {
    try {
      return await httpClient.get(`/locations/${id}`);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // Weather endpoints
  async getCurrentWeather(locationId: string): Promise<CurrentWeather> {
    try {
      return await httpClient.get(`/weather/current/${locationId}`);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async getWeatherForecast(locationId: string): Promise<WeatherForecast> {
    try {
      return await httpClient.get(`/weather/forecast/${locationId}`);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // User endpoints
  async getCurrentUser(): Promise<User> {
    try {
      return await httpClient.get('/user/profile');
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<User> {
    try {
      return await httpClient.patch('/user/preferences', preferences);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // RAG endpoints (placeholder implementation)
  async askRag(request: RagAskRequest): Promise<RagResponse> {
    try {
      return await httpClient.post('/rag/ask', request);
    } catch (error) {
      throw mapToAppError(error);
    }
  }
}

// Singleton instance
export const apiClient = new ApiClient();