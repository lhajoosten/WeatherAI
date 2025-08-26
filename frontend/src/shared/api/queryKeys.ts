/**
 * Centralized query keys for React Query
 * Provides consistent and type-safe cache keys
 */

export const queryKeys = {
  // Health
  health: () => ['health'] as const,
  
  // Locations
  locations: {
    all: () => ['locations'] as const,
    search: (query: string) => ['locations', 'search', query] as const,
    detail: (id: string) => ['locations', 'detail', id] as const,
  },
  
  // Weather
  weather: {
    all: () => ['weather'] as const,
    current: (locationId: string) => ['weather', 'current', locationId] as const,
    forecast: (locationId: string) => ['weather', 'forecast', locationId] as const,
    history: (locationId: string, range?: string) => {
      const key: (string | undefined)[] = ['weather', 'history', locationId];
      if (range) key.push(range);
      return key.filter(Boolean) as string[];
    },
  },
  
  // User
  user: {
    all: () => ['user'] as const,
    profile: () => ['user', 'profile'] as const,
    preferences: () => ['user', 'preferences'] as const,
    settings: () => ['user', 'settings'] as const,
  },
  
  // RAG
  rag: {
    all: () => ['rag'] as const,
    ask: (query: string, _context?: Record<string, unknown>) => {
      const key = ['rag', 'ask', query] as const;
      // Note: context is excluded from cache key for simplicity
      return key;
    },
    sources: (query: string) => ['rag', 'sources', query] as const,
  },
  
  // Meta
  meta: () => ['meta'] as const,
} as const;