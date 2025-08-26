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
  },

  // Weather (if/when added; stub paths)
  WEATHER: {
    CURRENT: (locationId: string) => `${API_VERSION}/weather/current/${locationId}`,
    FORECAST: (locationId: string) => `${API_VERSION}/weather/forecast/${locationId}`,
    HISTORY: (locationId: string) => `${API_VERSION}/weather/history/${locationId}`,
  },

  // User
  USER: {
    ME: `${API_VERSION}/user/me`,
    PROFILE: `${API_VERSION}/user/profile`, // backend currently uses /user/profile? (fallback)
    PREFERENCES: `${API_VERSION}/user/preferences`,
    SETTINGS: `${API_VERSION}/user/settings`,
  },

  // RAG (streaming endpoints)
  RAG: {
    ASK: `${API_VERSION}/rag/ask`,
    ASK_STREAM: `${API_VERSION}/rag/ask/stream`,
    SOURCES: `${API_VERSION}/rag/sources`,
  },

  // Streaming (if separate)
  STREAM: {
    EVENTS: `${API_VERSION}/stream/events`,
    RAG: (requestId: string) => `${API_VERSION}/stream/rag/${requestId}`,
  },
} as const;

export type ApiEndpoint = typeof API_ENDPOINTS;