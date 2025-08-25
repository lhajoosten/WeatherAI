import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { AuthProvider } from '@/core/auth/AuthContext';
import { ErrorBoundary } from '@/core/error/ErrorBoundary';
import theme from '@/theme';

// Create React Query client with default configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Composed application providers following the provider pattern.
 * Wraps the app with all necessary context providers in the correct order.
 */
const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <ErrorBoundary>
        <ChakraProvider theme={theme}>
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              <BrowserRouter>
                {children}
              </BrowserRouter>
            </AuthProvider>
          </QueryClientProvider>
        </ChakraProvider>
      </ErrorBoundary>
    </>
  );
};

export default AppProviders;