// Enhanced API client with typed endpoints and error mapping

import { httpClient } from '@/shared/api/client';
import { mapToAppError } from '@/shared/api/errors';
import {
  Location,
  LocationSearchResult,
  User,
  UserPreferences,
  CurrentWeather,
  WeatherForecast,
  RagAskRequest,
  RagResponse,
} from '@/shared/types/api';

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