// React Query setup and configuration

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { ReactNode } from 'react';

/**
 * Create a new QueryClient instance with sensible defaults
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes (renamed from cacheTime)
        retry: (failureCount, error) => {
          // Don't retry on 4xx errors
          if (error && typeof error === 'object' && 'status' in error) {
            const status = error.status as number;
            if (status >= 400 && status < 500) {
              return false;
            }
          }
          return failureCount < 3;
        },
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// Query key factory with strong typing
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
} as const;

/**
 * Query client provider with error boundary integration
 */
interface QueryProviderProps {
  children: ReactNode;
  client?: QueryClient;
}

export function QueryProvider({ children, client }: QueryProviderProps): React.JSX.Element {
  const queryClient = client || createQueryClient();
  
  return React.createElement(QueryClientProvider, { client: queryClient }, children);
}