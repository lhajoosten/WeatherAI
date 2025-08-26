// API-related types that are shared across features

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