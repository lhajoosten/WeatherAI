// API endpoint definitions aligned with backend routers

export const API_ENDPOINTS = {
  // Health
  HEALTH: '/health',
  
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    REGISTER: '/auth/register',
  },
  
  // Locations
  LOCATIONS: {
    SEARCH: '/locations/search',
    DETAIL: (id: string) => `/locations/${id}`,
    LIST: '/locations',
  },
  
  // Weather
  WEATHER: {
    CURRENT: (locationId: string) => `/weather/current/${locationId}`,
    FORECAST: (locationId: string) => `/weather/forecast/${locationId}`,
    HISTORY: (locationId: string) => `/weather/history/${locationId}`,
  },
  
  // User
  USER: {
    PROFILE: '/user/profile',
    PREFERENCES: '/user/preferences',
    SETTINGS: '/user/settings',
  },
  
  // RAG (streaming endpoints)
  RAG: {
    ASK: '/rag/ask',
    ASK_STREAM: '/rag/ask/stream',
    SOURCES: '/rag/sources',
  },
  
  // Streaming
  STREAM: {
    EVENTS: '/stream/events',
    RAG: (requestId: string) => `/stream/rag/${requestId}`,
  },
} as const;

export type ApiEndpoint = typeof API_ENDPOINTS;