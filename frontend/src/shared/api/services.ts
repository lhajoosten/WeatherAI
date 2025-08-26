// Comprehensive API service functions for all backend endpoints
import { httpClient } from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  // Location types
  LocationResponse,
  LocationCreate,
  LocationUpdate,
  ExplainResponse,
  
  // Location Group types
  LocationGroupResponse,
  LocationGroupCreate,
  LocationGroupBulkMembershipRequest,
  
  // User types
  UserMeResponse,
  UserProfileUpdate,
  UserPreferencesUpdate,
  
  // Analytics types
  ObservationResponse,
  AggregationResponse,
  TrendResponse,
  AccuracyResponse,
  AnalyticsSummaryRequest,
  AnalyticsSummaryResponse,
  DashboardResponse,
  
  // Digest types
  DigestResponse,
  
  // RAG types
  IngestRequest,
  IngestResponse,
  QueryRequest,
  QueryResponse,
  
  // Ingestion types
  AirQualityResponse,
  AstronomyResponse,
  IngestionRunResponse,
} from '../types/api';

// Helper function to build query strings
function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, v.toString()));
      } else {
        searchParams.append(key, value.toString());
      }
    }
  });
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

// Location Services
export const locationService = {
  async getAll(): Promise<LocationResponse[]> {
    return httpClient.get(API_ENDPOINTS.LOCATIONS.LIST);
  },

  async getById(id: number): Promise<LocationResponse> {
    return httpClient.get(API_ENDPOINTS.LOCATIONS.DETAIL(id.toString()));
  },

  async create(data: LocationCreate): Promise<LocationResponse> {
    return httpClient.post(API_ENDPOINTS.LOCATIONS.CREATE, data);
  },

  async update(id: number, data: LocationUpdate): Promise<LocationResponse> {
    return httpClient.put(API_ENDPOINTS.LOCATIONS.UPDATE(id.toString()), data);
  },

  async delete(id: number): Promise<void> {
    return httpClient.delete(API_ENDPOINTS.LOCATIONS.DELETE(id.toString()));
  },

  async explain(id: number, query?: string): Promise<ExplainResponse> {
    const params = query ? { query } : {};
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.LOCATIONS.EXPLAIN(id.toString())}${queryString}`);
  },
};

// Location Group Services
export const locationGroupService = {
  async getAll(): Promise<LocationGroupResponse[]> {
    return httpClient.get(API_ENDPOINTS.LOCATION_GROUPS.LIST);
  },

  async getById(id: number): Promise<LocationGroupResponse> {
    return httpClient.get(API_ENDPOINTS.LOCATION_GROUPS.DETAIL(id.toString()));
  },

  async create(data: LocationGroupCreate): Promise<LocationGroupResponse> {
    return httpClient.post(API_ENDPOINTS.LOCATION_GROUPS.CREATE, data);
  },

  async update(id: number, data: Partial<LocationGroupCreate>): Promise<LocationGroupResponse> {
    return httpClient.put(API_ENDPOINTS.LOCATION_GROUPS.UPDATE(id.toString()), data);
  },

  async delete(id: number): Promise<void> {
    return httpClient.delete(API_ENDPOINTS.LOCATION_GROUPS.DELETE(id.toString()));
  },

  async getMembers(id: number): Promise<LocationResponse[]> {
    return httpClient.get(API_ENDPOINTS.LOCATION_GROUPS.MEMBERS(id.toString()));
  },

  async bulkManageMembers(id: number, data: LocationGroupBulkMembershipRequest): Promise<void> {
    return httpClient.post(API_ENDPOINTS.LOCATION_GROUPS.BULK_MEMBERS(id.toString()), data);
  },
};

// User Services
export const userService = {
  async getMe(): Promise<UserMeResponse> {
    return httpClient.get(API_ENDPOINTS.USER.ME);
  },

  async updateProfile(data: UserProfileUpdate): Promise<void> {
    return httpClient.put(API_ENDPOINTS.USER.PROFILE, data);
  },

  async updatePreferences(data: UserPreferencesUpdate): Promise<void> {
    return httpClient.put(API_ENDPOINTS.USER.PREFERENCES, data);
  },

  async uploadAvatar(file: File): Promise<{ avatar_url: string }> {
    const formData = new FormData();
    formData.append('avatar', file);
    return httpClient.post(API_ENDPOINTS.USER.AVATAR_UPLOAD, formData);
  },
};

// Analytics Services
export const analyticsService = {
  async getObservations(params: {
    location_id: number;
    start?: string;
    end?: string;
    limit?: number;
  }): Promise<ObservationResponse[]> {
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.ANALYTICS.OBSERVATIONS}${queryString}`);
  },

  async getDailyAggregations(params: {
    location_id: number;
    start?: string;
    end?: string;
  }): Promise<AggregationResponse[]> {
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.ANALYTICS.AGGREGATIONS_DAILY}${queryString}`);
  },

  async getTrends(params: {
    location_id: number;
    period?: '7d' | '30d';
    metrics?: string[];
  }): Promise<TrendResponse[]> {
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.ANALYTICS.TRENDS}${queryString}`);
  },

  async getAccuracy(params: {
    location_id: number;
    start?: string;
    end?: string;
    variables?: string[];
  }): Promise<AccuracyResponse[]> {
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.ANALYTICS.ACCURACY}${queryString}`);
  },

  async generateSummary(data: AnalyticsSummaryRequest): Promise<AnalyticsSummaryResponse> {
    return httpClient.post(API_ENDPOINTS.ANALYTICS.SUMMARY, data);
  },

  async getDashboard(locationId: number, limit?: number): Promise<DashboardResponse> {
    const params = limit ? { limit } : {};
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.ANALYTICS.DASHBOARD(locationId.toString())}${queryString}`);
  },
};

// Digest Services
export const digestService = {
  async getMorningDigest(date?: string): Promise<DigestResponse> {
    const params = date ? { date } : {};
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.DIGEST.MORNING}${queryString}`);
  },

  async regenerateMorningDigest(force: boolean = true, date?: string): Promise<DigestResponse> {
    const params = { force, ...(date && { date }) };
    const queryString = buildQueryString(params);
    return httpClient.post(`${API_ENDPOINTS.DIGEST.MORNING_REGENERATE}${queryString}`);
  },

  async getMetrics(): Promise<any> {
    return httpClient.get(API_ENDPOINTS.DIGEST.METRICS);
  },
};

// RAG Services
export const ragService = {
  async ingestDocument(data: IngestRequest): Promise<IngestResponse> {
    return httpClient.post(API_ENDPOINTS.RAG.INGEST, data);
  },

  async queryDocuments(data: QueryRequest): Promise<QueryResponse> {
    return httpClient.post(API_ENDPOINTS.RAG.QUERY, data);
  },

  async healthCheck(): Promise<any> {
    return httpClient.get(API_ENDPOINTS.RAG.HEALTH);
  },

  // Streaming endpoint returns a different response type  
  getStreamEndpoint(): string {
    // Get base URL from httpClient configuration
    const baseUrl = (httpClient as any).baseURL || 'http://localhost:8000';
    return `${baseUrl}${API_ENDPOINTS.RAG.STREAM}`;
  },
};

// Ingestion Services
export const ingestionService = {
  async getAirQuality(params: {
    location_id: number;
    start?: string;
    end?: string;
    limit?: number;
  }): Promise<AirQualityResponse> {
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.INGESTION.AIR_QUALITY}${queryString}`);
  },

  async getAstronomyDaily(params: {
    location_id: number;
    start?: string;
    end?: string;
    limit?: number;
  }): Promise<AstronomyResponse> {
    const queryString = buildQueryString(params);
    return httpClient.get(`${API_ENDPOINTS.INGESTION.ASTRONOMY_DAILY}${queryString}`);
  },

  async getIngestionRuns(params?: {
    provider?: string;
    status?: 'SUCCESS' | 'FAILED' | 'RUNNING';
    limit?: number;
  }): Promise<IngestionRunResponse> {
    const queryString = buildQueryString(params || {});
    return httpClient.get(`${API_ENDPOINTS.INGESTION.RUNS}${queryString}`);
  },
};

// Health Service
export const healthService = {
  async check(): Promise<{ status: string; timestamp: string }> {
    return httpClient.get(API_ENDPOINTS.HEALTH);
  },
};