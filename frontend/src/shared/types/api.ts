// API-related types that are shared across features, aligned with backend models

// Location types
export interface Location {
  id: number;
  name: string;
  lat: number;
  lon: number;
  timezone: string;
  user_id: number;
  created_at: string;
  updated_at?: string;
}

export interface LocationCreate {
  name: string;
  lat: number;
  lon: number;
  timezone: string;
}

export interface LocationUpdate {
  name?: string;
  timezone?: string;
}

export interface LocationResponse {
  id: number;
  name: string;
  lat: number;
  lon: number;
  timezone: string;
  created_at: string;
  updated_at?: string;
}

export interface ExplainResponse {
  summary: string;
  recommendations: string[];
  highlights: string[];
  model: string;
  tokens_in: number;
  tokens_out: number;
  generated_at: string;
}

// Backward compatibility for legacy location search
export interface LocationSearchResult {
  locations: Array<{
    id: string;
    name: string;
    country: string;
    latitude: number;
    longitude: number;
  }>;
  query: string;
  count: number;
}

// Location Groups
export interface LocationGroup {
  id: number;
  name: string;
  description?: string;
  user_id: number;
  created_at: string;
  updated_at?: string;
}

export interface LocationGroupCreate {
  name: string;
  description?: string;
}

export interface LocationGroupResponse {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  member_count?: number;
}

export interface LocationGroupBulkMembershipRequest {
  location_ids: number[];
  operation: 'add' | 'remove';
}

// User types  
export interface User {
  id: number;
  email: string;
  timezone: string;
  created_at: string;
}

export interface UserProfile {
  id: number;
  user_id: number;
  first_name?: string;
  last_name?: string;
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  website_url?: string;
  location?: string;
  created_at: string;
  updated_at?: string;
}

export interface UserPreferences {
  id: number;
  user_id: number;
  language: string;
  timezone: string;
  temperature_unit: 'celsius' | 'fahrenheit';
  wind_speed_unit: 'kph' | 'mph';
  pressure_unit: 'hPa' | 'inHg';
  distance_unit: 'km' | 'miles';
  date_format: 'ISO' | 'US' | 'EU';
  time_format: '12h' | '24h';
  morning_digest_enabled: boolean;
  morning_digest_time: string;
  email_notifications: boolean;
  push_notifications: boolean;
  theme_preference: 'light' | 'dark' | 'auto';
  created_at: string;
  updated_at?: string;
}

export interface UserMeResponse {
  id: number;
  email: string;
  timezone: string;
  created_at: string;
  profile?: UserProfile;
  preferences?: UserPreferences;
}

export interface UserProfileUpdate {
  first_name?: string;
  last_name?: string;
  display_name?: string;
  bio?: string;
  website_url?: string;
  location?: string;
}

export interface UserPreferencesUpdate {
  language?: string;
  timezone?: string;
  temperature_unit?: 'celsius' | 'fahrenheit';
  wind_speed_unit?: 'kph' | 'mph';
  pressure_unit?: 'hPa' | 'inHg';
  distance_unit?: 'km' | 'miles';
  date_format?: 'ISO' | 'US' | 'EU';
  time_format?: '12h' | '24h';
  morning_digest_enabled?: boolean;
  morning_digest_time?: string;
  email_notifications?: boolean;
  push_notifications?: boolean;
  theme_preference?: 'light' | 'dark' | 'auto';
}

// Backward compatibility for legacy weather types
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

// Analytics types
export interface ObservationResponse {
  id: number;
  location_id: number;
  observed_at: string;
  temp_c?: number;
  wind_kph?: number;
  precip_mm?: number;
  humidity_pct?: number;
  condition_code?: string;
  source: string;
}

export interface AggregationResponse {
  id: number;
  location_id: number;
  date: string;
  temp_min_c?: number;
  temp_max_c?: number;
  avg_temp_c?: number;
  total_precip_mm?: number;
  max_wind_kph?: number;
  heating_degree_days?: number;
  cooling_degree_days?: number;
  generated_at?: string;
}

export interface TrendResponse {
  id: number;
  location_id: number;
  metric: string;
  period: string;
  current_value?: number;
  previous_value?: number;
  delta?: number;
  pct_change?: number;
  generated_at?: string;
}

export interface AccuracyResponse {
  id: number;
  location_id: number;
  target_time: string;
  forecast_issue_time: string;
  variable: string;
  forecast_value?: number;
  observed_value?: number;
  abs_error?: number;
  pct_error?: number;
  created_at?: string;
}

export interface AnalyticsSummaryRequest {
  location_id: number;
  period: '7d' | '30d';
  metrics: string[];
}

export interface AnalyticsSummaryResponse {
  narrative?: string;
  model: string;
  tokens_in: number;
  tokens_out: number;
  prompt_version: string;
  generated_at: string;
  reason?: string;
}

export interface DashboardResponse {
  observations: ObservationResponse[];
  aggregations: AggregationResponse[];
  trends: Array<{
    metric: string;
    period: string;
    current_value?: number;
    previous_value?: number;
    delta?: number;
    pct_change?: number;
  }>;
  accuracy: Record<string, {
    sample_size: number;
    avg_absolute_error: number;
  }>;
  generated_at: string;
  cache_hit: boolean;
}

// Digest types
export interface DigestResponse {
  summary: string;
  recommendations: string[];
  highlights: string[];
  date: string;
  cache_meta: {
    hit: boolean;
    key: string;
    generated_at: string;
  };
  tokens_meta: {
    input_tokens: number;
    output_tokens: number;
    model: string;
  };
}

// RAG types
export interface IngestRequest {
  source_id: string;
  text: string;
  metadata?: Record<string, any>;
}

export interface IngestResponse {
  document_id: string;
  chunks: number;
  status: string;
}

export interface QueryRequest {
  query: string;
  max_sources?: number;
  min_similarity?: number;
}

export interface SourceDTO {
  source_id: string;
  score: number;
  content_preview?: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceDTO[];
  metadata: Record<string, any>;
}

export interface StreamQueryRequest {
  query: string;
}

// Backward compatibility RAG types
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

// Air Quality & Astronomy types
export interface AirQualityResponse {
  location_id: number;
  start: string;
  end: string;
  count: number;
  data: Array<{
    observed_at: string;
    pm10?: number;
    pm2_5?: number;
    ozone?: number;
    no2?: number;
    so2?: number;
    pollen_tree?: number;
    pollen_grass?: number;
    pollen_weed?: number;
    source: string;
  }>;
}

export interface AstronomyResponse {
  location_id: number;
  start: string;
  end: string;
  count: number;
  data: Array<{
    date: string;
    sunrise_utc?: string;
    sunset_utc?: string;
    daylight_minutes?: number;
    moon_phase?: string;
    civil_twilight_start_utc?: string;
    civil_twilight_end_utc?: string;
    generated_at: string;
  }>;
}

export interface IngestionRunResponse {
  count: number;
  data: Array<{
    id: number;
    provider: string;
    run_type: string;
    location_id?: number;
    started_at: string;
    completed_at?: string;
    status: string;
    records_ingested?: number;
    error_message?: string;
  }>;
}