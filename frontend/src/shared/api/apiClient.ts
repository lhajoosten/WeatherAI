// Enhanced API client with typed endpoints and error mapping

import { API_ENDPOINTS } from './endpoints';
import { mapToAppError } from '@/shared/api/errors';
import { httpClient } from '@/shared/api/client';
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
  return await httpClient.get(API_ENDPOINTS.HEALTH);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // Location endpoints
  async searchLocations(query: string): Promise<LocationSearchResult> {
    try {
  return await httpClient.get(`${API_ENDPOINTS.LOCATIONS.SEARCH}?q=${encodeURIComponent(query)}`);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async getLocation(id: string): Promise<Location> {
    try {
  return await httpClient.get(API_ENDPOINTS.LOCATIONS.DETAIL(id));
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // Weather endpoints
  async getCurrentWeather(locationId: string): Promise<CurrentWeather> {
    try {
  return await httpClient.get(API_ENDPOINTS.WEATHER.CURRENT(locationId));
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async getWeatherForecast(locationId: string): Promise<WeatherForecast> {
    try {
  return await httpClient.get(API_ENDPOINTS.WEATHER.FORECAST(locationId));
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // User endpoints
  async getCurrentUser(): Promise<User> {
    try {
  return await httpClient.get(API_ENDPOINTS.USER.ME);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // Auth endpoints (TokenResponse shape from legacy for now)
  async login(credentials: { email: string; password: string }) {
    try {
      return await httpClient.post(API_ENDPOINTS.AUTH.LOGIN, credentials);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async register(data: { email: string; password: string; timezone?: string }) {
    try {
      return await httpClient.post(API_ENDPOINTS.AUTH.REGISTER, data);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<User> {
    try {
  return await httpClient.patch(API_ENDPOINTS.USER.PREFERENCES, preferences);
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  // RAG endpoints (placeholder implementation)
  async askRag(request: RagAskRequest): Promise<RagResponse> {
    try {
  return await httpClient.post(API_ENDPOINTS.RAG.ASK, request);
    } catch (error) {
      throw mapToAppError(error);
    }
  }
}

// Singleton instance
export const apiClient = new ApiClient();