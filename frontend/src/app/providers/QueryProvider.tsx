import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { ReactNode } from 'react';

// Enhanced React Query client with proper retry policies
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: any) => {
        // Don't retry client errors (4xx)
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        // Retry network errors and server errors (5xx) up to 2 times
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    },
    mutations: {
      retry: (failureCount, error: any) => {
        // Don't retry client errors (4xx)
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        // Retry network errors and server errors (5xx) up to 1 time
        return failureCount < 1;
      },
    },
  },
});

interface QueryProviderProps {
  children: ReactNode;
}

/**
 * Enhanced Query provider with sensible defaults and error handling
 */
export const QueryProvider: React.FC<QueryProviderProps> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};