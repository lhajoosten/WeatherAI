/**
 * Centralized query keys for React Query
 * Provides consistent and type-safe cache keys
 */

export const queryKeys = {
  // Health check
  health: () => ['health'] as const,
  
  // Locations
  locations: {
    all: () => ['locations'] as const,
    search: (query: string) => ['locations', 'search', query] as const,
  },
  
  // Weather
  weather: {
    all: () => ['weather'] as const,
    current: (locationId: string) => ['weather', 'current', locationId] as const,
    forecast: (locationId: string) => ['weather', 'forecast', locationId] as const,
  },
  
  // RAG
  rag: {
    all: () => ['rag'] as const,
    ask: (query: string) => ['rag', 'ask', query] as const,
  },
  
  // Meta
  meta: () => ['meta'] as const,
} as const;