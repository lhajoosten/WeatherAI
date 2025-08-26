// API endpoint definitions aligned with backend routers

// NOTE: Only health/monitoring endpoints are unversioned. All others require /v1 prefix.
const API_VERSION = '/v1';

export const API_ENDPOINTS = {
  // Health (unversioned)
  HEALTH: '/health',

  // Authentication
  AUTH: {
    LOGIN: `${API_VERSION}/auth/login`,
    LOGOUT: `${API_VERSION}/auth/logout`,
    REFRESH: `${API_VERSION}/auth/refresh`,
    REGISTER: `${API_VERSION}/auth/register`,
  },

  // Locations
  LOCATIONS: {
    SEARCH: `${API_VERSION}/locations/search`,
    DETAIL: (id: string) => `${API_VERSION}/locations/${id}`,
    LIST: `${API_VERSION}/locations`,
    CREATE: `${API_VERSION}/locations`,
    UPDATE: (id: string) => `${API_VERSION}/locations/${id}`,
    DELETE: (id: string) => `${API_VERSION}/locations/${id}`,
    EXPLAIN: (id: string) => `${API_VERSION}/locations/${id}/explain`,
  },

  // Location Groups
  LOCATION_GROUPS: {
    LIST: `${API_VERSION}/location-groups`,
    CREATE: `${API_VERSION}/location-groups`,
    DETAIL: (id: string) => `${API_VERSION}/location-groups/${id}`,
    UPDATE: (id: string) => `${API_VERSION}/location-groups/${id}`,
    DELETE: (id: string) => `${API_VERSION}/location-groups/${id}`,
    MEMBERS: (id: string) => `${API_VERSION}/location-groups/${id}/members`,
    BULK_MEMBERS: (id: string) => `${API_VERSION}/location-groups/${id}/bulk-members`,
  },

  // Analytics
  ANALYTICS: {
    OBSERVATIONS: `${API_VERSION}/analytics/observations`,
    AGGREGATIONS_DAILY: `${API_VERSION}/analytics/aggregations/daily`,
    TRENDS: `${API_VERSION}/analytics/trends`,
    ACCURACY: `${API_VERSION}/analytics/accuracy`,
    SUMMARY: `${API_VERSION}/analytics/summary`,
    DASHBOARD: (locationId: string) => `${API_VERSION}/analytics/${locationId}/dashboard`,
  },

  // Digest
  DIGEST: {
    MORNING: `${API_VERSION}/digest/morning`,
    MORNING_REGENERATE: `${API_VERSION}/digest/morning`,
    METRICS: `${API_VERSION}/digest/morning/metrics`,
  },

  // RAG
  RAG: {
    INGEST: `${API_VERSION}/rag/ingest`,
    QUERY: `${API_VERSION}/rag/query`,
    STREAM: `${API_VERSION}/rag/stream`,
    HEALTH: `${API_VERSION}/rag/health`,
  },

  // Ingestion (Air Quality, Astronomy)
  INGESTION: {
    AIR_QUALITY: `${API_VERSION}/air-quality`,
    ASTRONOMY_DAILY: `${API_VERSION}/astronomy/daily`,
    RUNS: `${API_VERSION}/ingest/runs`,
  },

  // User
  USER: {
    ME: `${API_VERSION}/user/me`,
    PROFILE: `${API_VERSION}/user/profile`,
    PREFERENCES: `${API_VERSION}/user/preferences`,
    AVATAR_UPLOAD: `${API_VERSION}/user/avatar`,
  },

  // Geo data
  GEO: {
    SEARCH: `${API_VERSION}/geo/search`,
    REVERSE: `${API_VERSION}/geo/reverse`,
  },

  // Meta endpoints
  META: {
    OPENAPI: `${API_VERSION}/meta/openapi`,
    VERSION: `${API_VERSION}/meta/version`,
  },
} as const;

export type ApiEndpoint = typeof API_ENDPOINTS;